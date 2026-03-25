# zip파일에서 dict 추출, util_yy의 라이브러리 활용

import util_yy
from PySide6.QtWidgets import QApplication, QFileDialog
import sys
import matplotlib.pyplot as plt
import numpy as np

params = {}
params['ROI_width'] = 0.05

if __name__ == '__main__':
    app = QApplication(sys.argv)

    fname, _ = QFileDialog.getOpenFileName(
        None,                          # 부모 위젯 없음
        "Beam Size Result 파일 열기",                     # 대화상자 제목
        "./GL507_A_ver_test_SW/log/oht_filtering_table",             # 초기 디렉토리
        "ZIP 파일 (*.zip);;모든 파일 (*)"  # 파일 필터 (zip 우선)
    )
    input = util_yy.load_pickle_from_zip(fname)

    retro_dist = np.array([])
    retro_intensity = np.array([])
    for target_name in input.keys():
        if target_name == 'GL_serial' or target_name == 'test_time' or target_name == 'GL_setting':
            pass
        else:
            for device_angle_str in input[target_name].keys():
                device_angle = float(device_angle_str)
                center_idx = np.round((device_angle / 0.18)+(1500/2))
                center_idx = np.clip(center_idx, 0, 1499)
                center_idx = np.int64(center_idx)

                ROI_dist = []
                ROI_intensity = []
                for frame_data in input[target_name][device_angle_str]['logging_datas']:
                    dist = frame_data['distance']
                    intensity = frame_data['pulse_width']

                    selected_slice = np.array(dist[center_idx-3:center_idx+3])

                    filtered_slice = selected_slice[(selected_slice != 0) & (~np.isnan(selected_slice))]

                    test_dist = np.nanmean(filtered_slice)

                    if test_dist == 0:
                        break
                    ROI_angle_width = np.degrees(np.arctan(params['ROI_width'] / 2 / test_dist))
                    idx_range = np.array([-np.floor((ROI_angle_width) / 0.18), np.floor((ROI_angle_width) / 0.18)])
                    idx = np.array(center_idx + idx_range, dtype=np.int64)
                    idx = np.clip(idx, 0, 1499)  # 0 미만과 1499 초과인 값 제거

                    dist_slice = np.array(dist[idx[0]:idx[1]])
                    intensity_slice = np.array(intensity[idx[0]:idx[1]])

                    filtered_idx = np.abs(test_dist - dist_slice) < 0.15
                    dist_slice = dist_slice[filtered_idx]
                    intensity_slice = intensity_slice[filtered_idx]
                    ROI_dist.append(dist_slice)
                    ROI_intensity.append(intensity_slice)

                    # if target_name == "retro0":
                    #     plt.figure(1)
                    #     plt.plot(dist_slice, intensity_slice)
                    #     plt.draw()
                    #     plt.pause(0.01)

                ROI_dist = [item for sublist in ROI_dist for item in sublist]
                ROI_dist = np.array(ROI_dist, dtype=np.float64)
                ROI_intensity = [item for sublist in ROI_intensity for item in sublist]
                ROI_intensity = np.array(ROI_intensity, dtype=np.float64)

                idx = np.logical_or((ROI_intensity == 0), (ROI_intensity > 5000))
                idx = np.logical_or(idx, (ROI_dist == 0))
                ROI_dist = ROI_dist[~idx]
                ROI_intensity = ROI_intensity[~idx]

                plt.figure(target_name)
                
                plt.scatter(ROI_dist, ROI_intensity,
                            # c=input[target_name][device_angle_str]['plt_color'], 
                            label=f"{target_name}_{device_angle_str}",
                            alpha=0.3)

                if target_name[:5] == "retro":  # 뒤에서 LUT 테이블 만들때 사용
                    retro_dist = np.hstack((retro_dist, ROI_dist))
                    retro_intensity = np.hstack((retro_intensity, ROI_intensity))

        # 중복된 레전드 항목을 제거하는 방법
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())
        plt.grid(which='major', linestyle='-', linewidth='0.5', color='black')
        plt.minorticks_on()
        plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
        # plt.show()
        plt.xlim(0,1)
        # 이미지를 array로 메모리에 저장
        fig = plt.gcf()
        fig.canvas.draw()
        img_1m = np.array(fig.canvas.renderer.buffer_rgba())
        plt.xlim(0,5)
        fig.canvas.draw() 
        img_5m = np.array(fig.canvas.renderer.buffer_rgba())
    
    plt.show()
