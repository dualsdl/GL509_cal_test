import io
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, BaggingRegressor
import matplotlib.image as mpimg
import pickle
from scipy.signal import savgol_filter
from sklearn.linear_model import LinearRegression
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import os
import sys

try:
    from . import util_yy
except ImportError:
    # 스크립트 직접 실행 시: 프로젝트 루트를 path에 넣고 패키지 절대 import
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    from functions import util_yy

mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0

SAVGOL_WINDOW_SIZES = [6, 15, 141, 331, 501]  # Savitzky-Golay 필터 구간별 윈도우 크기 (홀수여야 함)
POLY_ORDER = 5  # Savitzky-Golay 필터 다항식 차수
split_points = [50, 100, 350, 700]  # 구간을 나누는 지점


def extrapolate_initial_data(intensity, dist, num_points=3, extra_points=1):
    """초반 데이터를 외삽하여 데이터 포인트를 추가"""
    # intensity 값을 기준으로 대표값 계산 (동일한 intensity 값이 있을 경우 평균 사용)
    unique_intensity = np.unique(intensity)
    representative_intensity = []
    representative_dist = []

    for value in unique_intensity:
        mask = (intensity == value)
        representative_intensity.append(value)
        representative_dist.append(np.mean(dist[mask]))

    representative_intensity = np.array(representative_intensity)
    representative_dist = np.array(representative_dist)

    # intensity를 기준으로 정렬하여 가장 작은 5개의 값 선택
    sorted_indices = np.argsort(np.abs(representative_intensity))
    selected_intensity = representative_intensity[sorted_indices][:num_points]
    selected_dist = representative_dist[sorted_indices][:num_points]

    # 선형 회귀를 사용하여 초기 구간의 경향성을 파악
    model = LinearRegression()
    model.fit(selected_intensity.reshape(-1, 1), selected_dist)
    
    # 기울기와 절편을 기반으로 외삽
    extrapolated_intensity = np.linspace(selected_intensity[0] - extra_points * (selected_intensity[1] - selected_intensity[0]), 
                                         selected_intensity[0], num=extra_points)
    extrapolated_dist = model.predict(extrapolated_intensity.reshape(-1, 1))

    return extrapolated_intensity, extrapolated_dist


def run(open_filename='C:/yy/OneDrive/gl5_test_sw/log/walk_error/G5091N2z5C012_2026.3.25_09.47.48_walk_error_rawdata.zip',
        walk_error_table_filename='./walk_error_table.csv',
        walk_error_graph_filename='./walk_error_graph.png',
        output_filename='./output_data.zip',
        ref_dist=1000,
        dist_sample_size=20000,  # 잔차 서브샘플 크기
        residue_sample_size=1000,  # 잔차 서브샘플 크기
        std_dev_threshold=30,  # 표준 편차 임계값
        avg_residue_threshold=15,
        sub_sample=10,  # 평균 잔차 임계값
        show_plot=False):
    """show_plot=False: matplotlib.pyplot를 쓰지 않음(다른 모듈/GUI에서 호출 시 plt 상태 유지).
    show_plot=True: 스크립트 직접 실행처럼 창에 그래프 표시(plt.subplots + plt.show)."""

    # pickle 파일에서 데이터 로드
    # with open(file=open_filename, mode='rb') as f:
    #     datas = pickle.load(f)
    datas = util_yy.load_pickle_from_zip(open_filename)

    # 거리와 intensity 데이터를 추출
    dist = []
    intensity = []
    for frame_data in datas['frame_datas']:
        dist.append(frame_data['distance'])
        intensity.append(frame_data['pulse_width'])

    # numpy 배열로 변환 및 평탄화
    dist = np.array(dist).flatten() * 1000  # mm 단위로 변환
    intensity = np.array(intensity).flatten()

    # intensity가 0인 데이터 제거
    idx = np.logical_or((intensity == 0), (intensity > 5000))
    dist = dist[~idx]
    intensity = intensity[~idx]

    # dist = dist[::sub_sample]
    # intensity = intensity[::sub_sample]

    # # 초반 데이터 외삽 처리 (초반 50개의 포인트와 추가 50개의 외삽 포인트)
    # extrapolated_intensity, extrapolated_dist = extrapolate_initial_data(intensity, dist, num_points=50, extra_points=50)

    # # 외삽된 데이터를 기존 데이터에 추가
    # intensity = np.concatenate((extrapolated_intensity, intensity))
    # dist = np.concatenate((extrapolated_dist, dist))

    # 호출: Figure만 사용 / 직접 실행(show_plot=True) 시에만 pyplot으로 창 표시
    if show_plot:
        import matplotlib.pyplot as plt
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12))
    else:
        fig = Figure(figsize=(16, 12))
        ax1, ax2, ax3 = fig.subplots(3, 1)

    # 첫 번째 서브플롯: 측정된 데이터와 모델 피팅 결과 플로팅
    # 서브샘플링
    # if len(dist) > dist_sample_size:
    #     indices = np.random.choice(len(dist), residue_sample_size, replace=False)
    #     sample_intensity = intensity[indices]
    #     sample_dist = dist[indices]
    # else:
    #     sample_intensity = intensity
    #     sample_dist = dist
    # ax1.scatter(sample_intensity, sample_dist, label='Measured Data', alpha=0.5)
    ax1.scatter(intensity[::sub_sample], dist[::sub_sample], label='Measured Data', alpha=0.5, s=5)

    # Bagging Regressor 모델 설정 및 학습
    bagging_model = BaggingRegressor(estimator=RandomForestRegressor(n_estimators=15, n_jobs=-1),
                                     n_estimators=5, random_state=0)
    bagging_model.fit(intensity.reshape(-1, 1), dist)

    # 예측 범위 설정 및 모델로 피팅
    walk_error_table_intensity = np.array(list(range(5000)))
    y_fit = bagging_model.predict(walk_error_table_intensity.reshape(-1, 1))

    idx = walk_error_table_intensity > 1500
    y_fit[idx] = y_fit[1500]

    # 구간별로 다른 Savitzky-Golay 윈도우 크기 적용
    smoothed_y_fit = np.empty_like(y_fit)
    start = 0

    for i, end in enumerate(split_points + [len(y_fit)]):
        window_size = SAVGOL_WINDOW_SIZES[i]  # 각 구간에 대한 윈도우 크기 설정
        smoothed_y_fit[start:end] = savgol_filter(y_fit[start:end], window_size, POLY_ORDER)
        start = end
    smoothed_y_fit = savgol_filter(smoothed_y_fit, 25, POLY_ORDER)

    from scipy.ndimage import gaussian_filter
    smoothed_y_fit = gaussian_filter(smoothed_y_fit, sigma=1)

    # Walk Error Table 저장
    walk_error_table = np.round(smoothed_y_fit - np.min(smoothed_y_fit))

    np.savetxt(walk_error_table_filename, walk_error_table, fmt="%s", delimiter='\n')
    
    # 첫 번째 서브플롯에 피팅된 모델 결과 플로팅
    ax1.plot(walk_error_table_intensity, smoothed_y_fit, color='y', label='Walk Error Table')
    ax1.set_xlabel('Pulse Width [0.1ns]')
    ax1.set_ylabel('Distance [mm]')
    ax1.set_xlim((0, 2000))
    ax1.set_ylim((np.nanmin(smoothed_y_fit)-50, np.nanmax(smoothed_y_fit)+50))
    ax1.legend(loc='upper right')
    ax1.grid()

    # 거리 오프셋 계산 및 출력
    distance_offset = np.min(smoothed_y_fit) - ref_dist
    print(f'Distance offset is {distance_offset}')

    # 전체 데이터에 대한 예측 및 잔차 계산
    y_fit = bagging_model.predict(intensity.reshape(-1, 1))
    residue = dist - y_fit

    # 잔차 서브샘플링
    if len(residue) > residue_sample_size:
        indices = np.random.choice(len(residue), residue_sample_size, replace=False)
        sample_intensity = intensity[indices]
        sample_residue = residue[indices]
    else:
        sample_intensity = intensity
        sample_residue = residue

    # 두 번째 서브플롯: 잔차와 표준 편차 플로팅
    ax2.scatter(sample_intensity, sample_residue, color='green', label='Residue', alpha=0.5, s=5)  # 점 크기 조정

    # 표준 편차 계산
    intensity_df = pd.DataFrame({'intensity': intensity, 'residue': residue})
    grouped = intensity_df.groupby('intensity')['residue']
    std_dev = grouped.std().reset_index(name='std_dev')

    # 표준 편차 범위 플로팅
    ax2.fill_between(std_dev['intensity'], -std_dev['std_dev'], std_dev['std_dev'], color='blue', alpha=0.5, label='Standard Deviation')
    
    # 표준 편차가 임계값을 초과하는 영역 플로팅
    exceed_std_threshold = std_dev['std_dev'] > std_dev_threshold
    ax2.fill_between(std_dev['intensity'], 
                     -std_dev['std_dev'],
                     std_dev['std_dev'], 
                     where=exceed_std_threshold, 
                     color='red', alpha=0.5, label=f'Std Deviation > {std_dev_threshold} mm')

    # 표준 편차 임계값 선 추가
    threshold_line1 = ax2.axhline(y=std_dev_threshold, color='orange', linestyle='--', label=f'Threshold: {std_dev_threshold} mm')
    threshold_line2 = ax2.axhline(y=-std_dev_threshold, color='orange', linestyle='--')
    
    ax2.set_xlabel('Pulse Width [0.1ns]')
    ax2.set_ylabel('Distance [mm]')
    ax2.set_xlim((0, 2000))
    ax2.set_title('Residuals and Standard Deviation')
    ax2.grid()
    ax2.legend(loc='upper right')

    # 각 intensity에 대한 평균 잔차 계산
    avg_residue = intensity_df.groupby('intensity')['residue'].mean().reset_index(name='avg_residue')
    
    # 세 번째 서브플롯: 잔차 플로팅
    scatter_handle = ax3.scatter(sample_intensity, sample_residue, color='green', label='Residue', alpha=0.5, s=5)

    # 평균 잔차 바 플로팅
    bar_width = 1  # 막대 폭 설정
    bars = ax3.bar(avg_residue['intensity'], avg_residue['avg_residue'], color=['orange' if abs(val) > avg_residue_threshold else 'purple' for val in avg_residue['avg_residue']], width=bar_width, align='center')
    
    # 레전드용 바 추가
    purple_bar = Line2D([0], [0], color='purple', lw=4, label='Within Threshold')
    orange_bar = Line2D([0], [0], color='orange', lw=4, label='Exceeds Threshold')

    # 평균 잔차가 임계값을 초과할 때 레이블 추가
    ax3.set_xlim((0, 2000))
    xlim_min, xlim_max = ax3.get_xlim()
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if abs(avg_residue['avg_residue'][i]) > avg_residue_threshold:
            x_pos = bar.get_x() + bar.get_width() / 2
            if xlim_min <= x_pos < xlim_max:
                ax3.text(x_pos, height, f'{height:.2f}', 
                         ha='center', va='bottom' if height > 0 else 'top', color='black')
            bar.set_edgecolor('red')
            bar.set_linewidth(1.5)

    # 기준값 선 추가
    threshold_line1 = ax3.axhline(y=avg_residue_threshold, color='orange', linestyle='--', label=f'Threshold: +{avg_residue_threshold} mm')
    threshold_line2 = ax3.axhline(y=-avg_residue_threshold, color='orange', linestyle='--', label=f'Threshold: -{avg_residue_threshold} mm')

    ax3.set_xlabel('Pulse Width [0.1ns]')
    ax3.set_ylabel('Distance [mm]')
    ax3.set_title('Average Residue and Threshold with Residues')
    ax3.grid()

    # 레전드 설정
    handles, labels = ax3.get_legend_handles_labels()
    custom_handles = [scatter_handle, purple_bar, orange_bar, threshold_line1, threshold_line2]
    ax3.legend(handles=custom_handles, loc='upper right')

    # 평균 잔차가 임계값을 초과하는 intensity 출력
    fail_avg_residue = avg_residue[abs(avg_residue['avg_residue']) > avg_residue_threshold]
    if not fail_avg_residue.empty:
        print(f"Intensity where average residue exceeds ±{avg_residue_threshold} mm:")
        for _, row in fail_avg_residue.iterrows():
            print(f"Intensity: {row['intensity']}, Avg Residue: {row['avg_residue']}")

    # PNG 한 번 렌더 → 파일 저장과 동일한 픽셀로 numpy(BGR) 생성 (캔버스 buffer_rgba / plt 불필요)
    _png_buf = io.BytesIO()
    fig.savefig(_png_buf, format='png', dpi=300, bbox_inches='tight')
    png_bytes = _png_buf.getvalue()
    with open(walk_error_graph_filename, 'wb') as _f:
        _f.write(png_bytes)
    _png_buf.seek(0)
    _rgba = mpimg.imread(_png_buf)
    if _rgba.dtype == np.float32 or _rgba.dtype == np.float64:
        _rgb = np.clip(_rgba[:, :, :3] * 255.0, 0, 255).astype(np.uint8)
    else:
        _rgb = _rgba[:, :, :3].astype(np.uint8)
    walk_error_graph = _rgb[:, :, ::-1]  # RGB → BGR

    if show_plot:
        plt.show(block=True)
        plt.close(fig)

    # 결과를 dict 형태로 구성
    result_dict = {
        'distance_offset': distance_offset,
        'std_residue_exceeds_threshold': exceed_std_threshold.any(),
        'avg_residue_exceeds_threshold': not fail_avg_residue.empty,
        'walk_error_table_filename': walk_error_table_filename,  # 파일 경로 추가
        'walk_error_graph_filename': walk_error_graph_filename,  # 파일 경로 추가
        'walk_error_table': walk_error_table.tolist(),  # 리스트로 변환
        'GL_serial': datas['GL_serial'],
        'walk_error_graph': walk_error_graph,
        'test_time': datas['test_time']
    }

    # pickle 파일로 결과 저장
    # with open(file=pickle_output_filename, mode='wb') as f:
    #     pickle.dump(result_dict, f)

    import zipfile
    # ZIP 파일에 pickle 데이터 압축하여 저장하기
    with zipfile.ZipFile(
        output_filename, 
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=7
        ) as zf:
        with zf.open(f"{datas['GL_serial']}_walk_error_proc_data.pickle", "w") as f:
            pickle.dump(result_dict, f)  # Pickle 데이터를 바로 씁니다.

    return result_dict


if __name__ == "__main__":
    result = run(show_plot=True)
    print(f"Run result: {result}")
