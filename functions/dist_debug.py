# zip파일에서 dict 추출, util_yy의 라이브러리 활용

import util_yy
from PySide6.QtWidgets import QApplication, QFileDialog
import sys
import matplotlib.pyplot as plt
import numpy as np

if __name__ == '__main__':
    app = QApplication(sys.argv)

    fname, _ = QFileDialog.getOpenFileName(
        None,                          # 부모 위젯 없음
        "Beam Size Result 파일 열기",                     # 대화상자 제목
        "I:/GL507_A_ver_test_SW/log/distance_test",             # 초기 디렉토리
        "ZIP 파일 (*.zip);;모든 파일 (*)"  # 파일 필터 (zip 우선)
    )
    raw_data = util_yy.load_pickle_from_zip(fname)

    # print(raw_data['raw_data'])
    #raw_data['raw_data'] list of dict 안에서 key값이 device_angle이 130.0인 데이터 추출
    device_angle_data = [data for data in raw_data['raw_data'] if data['device_angle'] == 130.0]
    print(device_angle_data)

    #device_angle_data 안에 있는 데이터 중에서 test_distance가 500.0인 데이터 추출
    test_distance_data = [data for data in device_angle_data if data['test_distance'] == 500.0]
    print(test_distance_data)

    data = test_distance_data[0]['frame_datas']
    # data는 list of dict로 x, y 값을 가짐
    x_all = []
    y_all = []
    r_all = []

    device_angle = 130.0
    test_dist = 500 / 1000.0
    print(f"device_angle = {device_angle}, test_dist = {test_dist}")

    ROI_angle_width = np.degrees(np.arctan(0.15 / 2 / test_dist))
    print(f"ROI_angle_width = {ROI_angle_width}")
    idx_center = device_angle / 0.18 + 749.5
    print(f"idx_center = {idx_center}")
    idx_range = np.array([-np.floor(ROI_angle_width / 0.18), np.floor(ROI_angle_width / 0.18)], dtype=np.int64)
    print(f"idx_range = {idx_range}")
    idx = np.array(np.array(idx_center, dtype=np.int64) + idx_range)
    idx = np.clip(idx, 0, 1499)  # 0 미만과 1499 초과인 값 제거
    print(f"idx = {idx}")
    
    for frame in data:
        x_all.extend(frame['x'][idx[0]:idx[1]])
        y_all.extend(frame['y'][idx[0]:idx[1]])
        r_all.extend(frame['distance'][idx[0]:idx[1]])
    
    # 누적된 x, y 값을 이용하여 그래프 그리기 
    # plt.scatter(x_all, y_all)
    # plt.xlim(-1.5, 1.5)
    # plt.ylim(-1.5, 1.5)
    # plt.grid(True)
    # plt.show()

    # device_angle만큼 xy 회전변환 util_yy의 rotate_points 함수 활용
    x_all = np.array(x_all)
    y_all = np.array(y_all)
    r_array = np.array(r_all)
    x_array, y_array = util_yy.rotate_points(x_all, y_all, device_angle_data[0]['device_angle'])
    # plt.scatter(x_all, y_all)
    # plt.xlim(-1.5, 1.5)
    # plt.ylim(-1.5, 1.5)
    # plt.grid(True)
    # plt.show()

    idx = (r_array > 0)
    idx = np.logical_and(idx, r_array < 20)
    idx = np.logical_and(idx, y_array > 0)
    # idx = np.logical_and(idx, x_array < 0.5)
    # idx = np.logical_and(idx, x_array > -0.5)
    x_array = x_array[idx]
    y_array = y_array[idx]

    print(f'std y = {np.std(y_array)}')
    # array 전부 다 출력, 중간에 ... 없도록, numpy print 옵션 조정
    # np.set_printoptions(threshold=np.inf)
    print(y_array)

    plt.scatter(x_array, y_array)
    plt.xlim(-10.5, 10.5)
    plt.ylim(-10.5, 10.5)
    plt.grid(True)
    plt.show()
