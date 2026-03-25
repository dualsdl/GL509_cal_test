#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import time
from datetime import datetime
import pickle
import zipfile
import os

try:
    from stage_lib import ETEL
except ImportError:
    print("stage_lib not found")

import pysoslab_etel_stage as py_stage_etel
import pysoslab_core
import pysoslab_user
import pysoslab_developer
# import pysoslab_area

from functions import util_yy
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use("TkAgg")  # 예: TkAgg 백엔드 사용
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0

# #############  parameter start ###############
default_params = {
    "SERIAL_NAME": "COM4",
    "SERIAL_BAUDRATE": 921600,  # 921600, 115200
    "UDP_SENSOR_IP": "10.110.1.2",
    "UDP_SENSOR_PORT": 2000,
    "UDP_PC_IP": "10.110.1.3",
    "UDP_PC_PORT": 3000,
    "etel_stage_IP_addr": "10.110.1.200",
    "device_rotation_speed": 30.0,
    "ROI_width": 0.10,
    "test_angle": ['-130.0', '-90.0', '-45.0', '0.0', '45.0', '90.0', '130.0'],
    "logging_frame_num": 100,
    "detection_ratio_criteria": 0.997,
    "obs_empty_lut": "./obs_lut.csv",
}
# #############  parameter end ###############


def make_report(data: dict, result: dict, save_dir="./report") -> None:
    """
    data, result를 받아서 엑셀 형태로 리포트를 생성합니다.
    리포트에는 다음 정보가 들어갑니다.
        1) GL_serial
        2) 센서각도 (device_angle)
        3) is_passed (검사 통과 여부)
        4) 감지율 (detection_ratio)
        5) 감지수 (cnt)
        6) 감지모수 (max_cnt)
        7) 검사시간 (inspection_time)
    """
    # 저장할 폴더가 없으면 생성
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # GL 시리얼 번호가 존재하는지 확인
    if "GL_serial" not in data:
        raise ValueError("data dictionary에 'GL_serial' 정보가 없습니다.")

    # 검사시간이 없을 경우를 대비하여 get() 사용 (없으면 None)
    inspection_time = data.get("test_time", None)
    
    # result 내부에 각 센서각도별로 정보가 저장되어 있다고 가정 (예: result["-130.0"] = {...} )
    angles = list(result.keys())  # 예: ['-130.0', '-90.0', ...]
    print(f'{angles}')
    
    # 데이터프레임 구성
    rows = []
    for angle in angles:
        if angle == 'GL_serial' or angle == 'test_time' or angle == 'is_passed' or 'report_path':
            pass
        else:
            row_dict = {
                "GL_serial": data["GL_serial"],
                "검사시간(초)": inspection_time,  # 모든 행 동일
                "센서각도": angle,
                "검사 결과": result[angle]["is_passed"],
                "감지율": result[angle]["detection_ratio"],
                "감지수": result[angle]["cnt"],
                "감지모수": result[angle]["max_cnt"]
            }
            rows.append(row_dict)

    df_report = pd.DataFrame(rows)

    # 엑셀 파일 이름 지정 (예시)
    excel_filename = f"{data['GL_serial']}_{inspection_time}_maxdist_report.xlsx"
    save_path = os.path.join(save_dir, excel_filename)

    # 엑셀로 저장
    df_report.to_excel(save_path, index=False)
    print(f"리포트가 생성되었습니다: {save_path}")


def data_acquisition(input: dict, params: dict) -> dict:
    output = dict()
    output['test_time'] = f"{datetime.now().year}" + \
                        f".{datetime.now().month}" + \
                        f".{datetime.now().day}" + \
                        f'_{datetime.now().strftime("%H.%M.%S")}'

    stage_etel = input['stage_etel']
    GL5_core = input['GL5_core']
    GL5_user = input['GL5_user']
    GL5_developer = input['GL5_developer']

    success, GL_serial = GL5_user.getSerialNum(GL5_core)
    if success:
        print(f"Serial_num = {GL_serial}")
    else:
        print("Unable to get a serial number")
    output['GL_serial'] = GL_serial
    
    model_name = GL_serial[4:6]
    print(f"Model name: {model_name}")
    if (model_name == '1W' or
            model_name == '1V'):
        compensation = 15
        LUT_mode = 2
    elif (model_name == '1N' or
            model_name == '1M' or
            model_name == '1R' or
            model_name == '2N'):
        compensation = 3
        LUT_mode = 2
        
        # success, min_pulse_width_lut, max_pulse_width_lut = (
        #     GL5_developer.getMinMaxPulseWidthLUTFromFile(params['obs_empty_lut'])
        # )
        # if success:
        #     success = GL5_developer.setMinMaxPulseWidthLUTToSensor(
        #         GL5_core, min_pulse_width_lut, max_pulse_width_lut
        #     )
        #     if success:
        #         print("Successfully set the min/max_pulse_width_lut to sensor")
        #     else:
        #         print("Unable to set the min/max_pulse_width_lut to sensor")
        # else:
        #     print("Unable to load the min/max_pulse_width_lut from file")
    else:
        raise ValueError('Unknown sensor type')
    success = GL5_developer.setCompensation(GL5_core, compensation)
    if success:
        print("Successfully set the compensation")
    else:
        print("Unable to set the compensation")

    success = GL5_developer.setLUTMode(GL5_core, LUT_mode)
    if success:
        print("Successfully set the lut_mode")
    else:
        print("Unable to set the lut_mode")

    # LiDAR streaming start
    success = GL5_user.setStreamEnable(GL5_core, True)
    if success:
        print("Successfully enable data streaming")
    else:
        print("Failed to enable data streaming")

    output['raw_data'] = []
    for device_angle in params['test_angle']:
        # 각 각도별로 프레임 버퍼를 초기화해야 누적 집계가 발생하지 않음
        logging_datas = []
        temp = dict()
        stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, float(device_angle), params['device_rotation_speed'])
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
            time.sleep(0.2)

        cnt = 0
        while (cnt < params['logging_frame_num']):
            success, frame_data = GL5_user.getLidarData(GL5_core, False)
            if not success:
                print("Failed to get a LiDAR data")
            else:
                logging_datas.append(frame_data)
                cnt += 1

                # if cnt % 5 == 0:
                # if True:
                if False:
                    # print(j)
                    # print(frame_data.keys())
                    # print(frame_data['angle'][999])
                    plt.figure(0)
                    plt.clf()
                    plt.scatter(frame_data["x"], frame_data["y"], 
                                c=np.array(frame_data["pulse_width"]) / 10.0,
                                vmin=0, vmax=100)
                    plt.colorbar()
                    plt.xlim([-11.5, 11.5])  # X_ROI
                    plt.xlabel("X (mm)")
                    plt.ylim([-11.5, 11.5])  # _ROI
                    plt.ylabel("Y (mm)")
                    plt.draw()
                    plt.pause(0.001)

        temp['frame_datas'] = logging_datas
        temp['device_angle'] = device_angle
        output['raw_data'].append(temp)
        
    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, float(0.0), params['device_rotation_speed'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)

    return output


def analysis(input: dict, params: dict) -> dict:
    output = dict()
    output['GL_serial'] = input['GL_serial']
    output['test_time'] = input['test_time']

    output['is_passed'] = True

    for data in input['raw_data']:
        output[data['device_angle']] = dict()
        device_angle = float(data['device_angle'])
        frame_datas = data['frame_datas']

        test_dist = 9.0

        ROI_angle_width = np.degrees(np.arctan(params['ROI_width'] / 2 / test_dist))
        # print(f"ROI_angle_width = {ROI_angle_width}")
        idx_center = device_angle / 0.18 + 749.5
        idx_range = np.array([-np.floor(ROI_angle_width / 0.18), np.floor(ROI_angle_width / 0.18)], dtype=np.int64)
        idx = np.array(np.array(idx_center, dtype=np.int64) + idx_range)
        idx = np.clip(idx, 0, 1499)  # 0 미만과 1499 초과인 값 제거

        x_array = []
        y_array = []
        for frame_data in frame_datas:
            x = np.array(frame_data['x'][idx[0]:idx[1]])
            y = np.array(frame_data['y'][idx[0]:idx[1]])
            # x = np.array(frame_data['x'])
            # y = np.array(frame_data['y'])

            x_rotated, y_rotated = util_yy.rotate_points(x, y, device_angle)  # 인덱싱된 포인트 회전변환하여 정면에 타겟이 있게
            # idx = x_rotated < params['ROI_width'] / 2
            # idx = np.logical_and(idx, x_rotated > -params['ROI_width'] / 2)
            # idx = np.logical_and(idx, x_rotated != 0)
            x_array.append(x_rotated)
            y_array.append(y_rotated)

        x_array = np.concatenate(x_array)
        y_array = np.concatenate(y_array)

        cnt_idx = (y_array > 8)
        cnt_idx = np.logical_and(cnt_idx, y_array < 10)
        cnt = np.sum(cnt_idx)
        output[data['device_angle']]['cnt'] = cnt

        max_cnt = (idx[1] - idx[0]) * params['logging_frame_num']
        output[data['device_angle']]['max_cnt'] = max_cnt
        detection_ratio = cnt / max_cnt
        output[data['device_angle']]['detection_ratio'] = detection_ratio

        if detection_ratio > params['detection_ratio_criteria']:
            output[data['device_angle']]['is_passed'] = True
        else:
            output[data['device_angle']]['is_passed'] = False
            output['is_passed'] = False

    return output


def run(input: dict, params: dict = None) -> dict:
    if params is None:
        params = {}
    default_params.update(params)
    print('default_params:', default_params)

    data = data_acquisition(input, default_params)

    result = analysis(data, default_params)

    return data, result


def unittest() -> None:
    # ETEL stage connect
    stage_etel = py_stage_etel.stage_etel()
    status = stage_etel.connect(default_params['etel_stage_IP_addr'], 3)
    if status:
        pass
    else:
        raise Exception('ETEL stage initialing FAIL')

    time.sleep(0.5)
    ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE)
    print('ROTARY_DEVICE home search done')
    ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET)
    print('LINEAR_TARGET home search done')
    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)
    ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET)
    print('ROTARY_TARGET home search done')

    # GL connect
    GL5_core = pysoslab_core.core()
    GL5_user = pysoslab_user.user()
    GL5_developer = pysoslab_developer.developer()
    # GL5_core.connectSerial(SERIAL_NAME, SERIAL_BAUDRATE)
    GL5_core.connectUDP(
        default_params['UDP_SENSOR_IP'],
        default_params['UDP_SENSOR_PORT'],
        default_params['UDP_PC_IP'],
        default_params['UDP_PC_PORT']
    )

    input = dict()
    input['stage_etel'] = stage_etel
    input['GL5_core'] = GL5_core
    input['GL5_user'] = GL5_user
    input['GL5_developer'] = GL5_developer

    data, results = run(input, None)

    stage_etel = input['stage_etel']
    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 0.0, default_params['device_rotation_speed'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)

    test_name = 'max_dist'
    path = f"./log/{test_name}"
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(data, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(results, path, filename)

    make_report(data, results, save_dir=path)


def unittest_analysis_rawdata(raw_zip_filepath: str) -> dict:
    """
    ZIP 내부의 '_maxdist_rawdata.pickle'을 읽어와서 analysis() 함수를 실행해 보는 테스트 함수입니다.
    raw_zip_filepath 인자는 예: './log/max_dist/GL5_..._maxdist_rawdata.zip' 형태.
    """
    
    # ZIP 파일 오픈
    with zipfile.ZipFile(raw_zip_filepath, 'r') as zf:
        # ZIP 내부 파일 목록 가져오기
        zip_files = zf.namelist()

        # 특정 pickle 파일명을 찾기 (예: ...maxdist_rawdata.pickle)
        pickle_filename = None
        for fname in zip_files:
            if fname.endswith('max_dist_rawdata.pickle'):
                pickle_filename = fname
                break

        if pickle_filename is None:
            raise FileNotFoundError("ZIP 내부에 'max_dist_rawdata.pickle' 파일을 찾을 수 없습니다.")

        # pickle 파일을 읽어서 data를 복원
        with zf.open(pickle_filename, 'r') as f:
            data = pickle.load(f)

    # 여기서 analysis()는 질문에서 이미 정의된 함수를 그대로 사용
    result = analysis(data)

    # 분석 결과를 반환하거나, 필요시 print할 수 있음
    print("\n===== Analysis Result =====")
    for angle_key, angle_result in result.items():
        print(f"Angle: {angle_key}")
        print(f"  detection_ratio: {angle_result['detection_ratio']}")
        print(f"  cnt: {angle_result['cnt']}, max_cnt: {angle_result['max_cnt']}")
        print(f"  is_passed: {angle_result['is_passed']}")

    return result


if __name__ == "__main__":
    # unittest()
    unittest_analysis_rawdata('H:/gui_test/log/max_dist/G5091N2258011_2025.8.27_19.53.54max_dist_rawdata.zip')
