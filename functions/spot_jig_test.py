#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import time
from datetime import datetime
import util_yy

# stage_lib을 import하기 위해 프로젝트 루트를 sys.path에 추가
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage_lib import ETEL
import pysoslab_etel_stage as py_stage_etel
from stage_lib.DPIN import DpinStageHandler as DPIN

import pysoslab_core
import pysoslab_user
import pysoslab_developer
import pysoslab_area

# from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter
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
    "speed_mmps": 400.0,
    # "target_angle": 90,  # OHT는 DG4090
    "target_angle": -90,  # OBS는 92%
    "device_rotation_speed": 30.0,
    "LINEAR_STAGE_OFFSET": -43,
    # "LINEAR_STAGE_OFFSET_retro40": -43 + 188
    "test_area_path": "./OHT_filtering_validataion_area.json",
    # "test_area_path": "./empty_area.json",
    "empty_area_path": "./empty_area.json",

    "test_cond": {
        'spot_jig': {
            'target_angle': 180.0,  # TBD
            'measurements': {
                '0.0': {'dist': [1080.0, 330.0], # 80mm정도 스팟지그가 튀어나와있어서 1000~250검사한것과 같음
                        'moving_speed': 100.0,
                        'selected_area': 10},
            },
            'plt_color': 'darkslategrey'
        },
    },
}

# #############  parameter end ###############


def unittest() -> None:
    params = default_params
    # ETEL stage connect
    stage_etel = py_stage_etel.stage_etel()
    status = stage_etel.connect(params['etel_stage_IP_addr'], 3)
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
    GL5_area = pysoslab_area.area()
    GL5_developer = pysoslab_developer.developer()
    # GL5_core.connectSerial(SERIAL_NAME, SERIAL_BAUDRATE)
    GL5_core.connectUDP(
        params['UDP_SENSOR_IP'],
        params['UDP_SENSOR_PORT'],
        params['UDP_PC_IP'],
        params['UDP_PC_PORT'],
        )

    input = dict()
    input['stage_etel'] = stage_etel
    input['GL5_core'] = GL5_core
    input['GL5_user'] = GL5_user
    input['GL5_developer'] = GL5_developer
    input['GL5_area'] = GL5_area

    stage_etel.setOffset(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET,
        params['LINEAR_STAGE_OFFSET'],
    )
    
    dpin = DPIN()
    dpin.connect("10.110.1.201", 184)
    dpin.searching_home()

    input['dpin'] = dpin

    data, result = run(input, params)

    test_name = 'spot_jig_test'
    path = f"./log/{test_name}"
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(data, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(result, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_report'  # 확장자 없이
    create_fail_report(result, f"{path}/{filename}.xlsx")


def data_acquisition(input: dict, params: dict = None) -> dict:
    output = dict()
    output['test_time'] = f"{datetime.now().year}" + \
                          f".{datetime.now().month}" + \
                          f".{datetime.now().day}" + \
                          f'_{datetime.now().strftime("%H.%M.%S")}'
    stage_etel = input['stage_etel']
    GL5_core = input['GL5_core']
    GL5_user = input['GL5_user']
    GL5_developer = input['GL5_developer']
    GL5_area = input['GL5_area']

    success, GL_serial = GL5_user.getSerialNum(GL5_core)
    if success:
        print(f"Serial_num = {GL_serial}")
    else:
        print("Unable to get a serial number")
    output['GL_serial'] = GL_serial

    success, areas = GL5_area.getAllAreaFromFile(params['test_area_path'])
    print(areas)
    if success:
        success = GL5_area.setAllAreaToSensor(GL5_core, GL5_user, areas)
        if success:
            print("Successfully set the areas")
        else:
            print("Unable to set the areas")
    else:
        print("Unable to read the areas from file")

    success = GL5_developer.setCompensation(GL5_core, 3)
    if success:
        print("Successfully set the compensation")
    else:
        print("Unable to set the compensation")

    success = GL5_developer.setLUTMode(GL5_core, 2)
    if success:
        print("Successfully set the lut_mode")
    else:
        print("Unable to set the lut_mode")

    send_str = 'area console setting'
    success, recv_str = GL5_developer.sendConsole(GL5_core, send_str)
    if success:
        print(f"send_str = {send_str}")
        print(f"recv_str = {recv_str}")
    else:
        print("Not responding to console messages")

    # LiDAR streaming start
    success = GL5_user.setStreamEnable(GL5_core, True)
    if success:
        print("Successfully enable data streaming")
    else:
        print("Failed to enable data streaming")

    # print('debug 2')
    for target_name, target_cond in params['test_cond'].items():
        output[target_name] = dict()
        # print(f'{target_name}_data acquisition start')

        # 초기 위치로 이동
        stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
            time.sleep(0.2)

        stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, target_cond['target_angle'], 30.0)
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
            time.sleep(0.2)

        # print('debug 1')
        for device_angle, item_value in target_cond['measurements'].items():
            output[target_name][device_angle] = dict()
            
            dist_list = item_value['dist']
            speed_list = item_value['moving_speed']

            # 초기 위치로 이동
            stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, dist_list[0], 400.0)
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                time.sleep(0.2)

            stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, float(device_angle), params['device_rotation_speed'])
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
                time.sleep(0.2)

            send_str = f'area set {target_cond["measurements"][device_angle]["selected_area"]}'
            success, recv_str = GL5_developer.sendConsole(GL5_core, send_str)
            if success:
                print(f"send_str = {send_str}")
                print(f"recv_str = {recv_str}")
            else:
                print("Not responding to console messages")

            print(f'{target_name}_GL{device_angle}_data acquisition start')

            logging_datas = []
            for i in range(len(dist_list)):
                # 현재 위치로 이동
                stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, dist_list[i], speed_list)
                while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                    success, frame_data = GL5_user.getLidarData(GL5_core, False)
                    if not success:
                        print("Failed to get a LiDAR data")
                    else:
                        logging_datas.append({
                            'frame_data': frame_data,
                            'test_test': ETEL.get_current_position(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET)
                            })

                    # plt.figure(1, figsize=(12, 9))
                    # plt.clf()
                    # plt.scatter(frame_data["x"], frame_data["y"], 
                    #             c=np.array(frame_data["pulse_width"]) / 10.0,
                    #             vmin=0, vmax=100)
                    # plt.colorbar()    
                    # plt.xlim([-5.5, 5.5])  # X_ROI
                    # plt.xlabel("X (mm)")
                    # plt.ylim([-5.5, 5.5])  # Y_ROI
                    # plt.ylabel("Y (mm)")
                    # plt.draw()
                    # plt.pause(0.001)

            output[target_name][device_angle]['logging_datas'] = logging_datas
            output[target_name][device_angle]['plt_color'] = target_cond['plt_color']

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 0.0, params['device_rotation_speed'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)

    success, areas = GL5_area.getAllAreaFromFile(params['empty_area_path'])
    print(areas)
    if success:
        success = GL5_area.setAllAreaToSensor(GL5_core, GL5_user, areas)
        if success:
            print("Successfully set the areas")
        else:
            print("Unable to set the areas")
    else:
        print("Unable to read the areas from file")

    return output


def analysis(input: dict, params: dict = None) -> dict:
    output = dict()
    for target_name in input.keys():
        if target_name == 'GL_serial' or target_name == 'test_time':
            pass
        else:        
            output[target_name] = []
            for device_angle_str in input[target_name].keys():
                for data in input[target_name][device_angle_str]['logging_datas']:
                    # print(frame_data.keys())
                    # input_area = frame_data['input_area']
                    output_level = data['frame_data']['output_level']

                    if target_name[:5] == 'retro':
                        is_passed = output_level != 0
                    else:
                        is_passed = output_level == 0

                    output[target_name].append({
                            'dist': data['test_test'],  # 5m stage dist read
                            'device_angle': device_angle_str,
                            'is_passed': is_passed,
                        })

    return output


def create_fail_report(output_data: dict, filename: str = 'fail_report.xlsx'):
    """
    1) 타겟별 요약 정보 (PASS/FAIL)를 '요약' 시트에 기록
    2) Fail 항목의 상세 내역을 '상세' 시트에 기록
    """

    # 1) 요약 정보 작성
    summary_rows = []
    for target_name, result_list in output_data.items():
        # 'is_passed'가 False인 항목이 하나라도 있으면 FAIL
        fail_count = sum(1 for entry in result_list if entry['is_passed'] == False)
        if fail_count > 0:
            pass_fail_status = 'FAIL'
        else:
            pass_fail_status = 'PASS'

        summary_rows.append({
            '타겟 이름': target_name,
            '결과': pass_fail_status
        })

    df_summary = pd.DataFrame(summary_rows)

    # 2) 상세 정보 작성 (Fail 항목만)
    detail_rows = []
    for target_name, result_list in output_data.items():
        for entry in result_list:
            if entry['is_passed'] == False:
                detail_rows.append({
                    'Target': target_name,
                    'Distance': entry.get('dist', None),
                    # 'Device Angle': entry.get('device_angle', None),
                    'Pass/Fail': 'Fail'
                })

    df_details = pd.DataFrame(detail_rows)

    # 3) Excel 파일로 저장 (두 개의 시트)
    with pd.ExcelWriter(filename) as writer:
        df_summary.to_excel(writer, sheet_name='요약', index=False)
        df_details.to_excel(writer, sheet_name='상세', index=False)

    print(f"리포트가 '{filename}' 파일로 저장되었습니다.")


def run(input: dict, params: dict = None) -> dict:
    stage_etel = input['stage_etel']

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, 90.0, 30.0)  # 재귀반사판 설정
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
        time.sleep(0.2)

    import tx_level_test
    tx_level_test_parameter = {
        "scan_angles": ['0.0']
    }
    tx_level_rawdata, tx_level_output = tx_level_test.run(input, tx_level_test_parameter)
    tx_level = tx_level_output[f'{tx_level_test_parameter["scan_angles"][0]}']['tx_level_in_deg']
    input['dpin'].move_to_angle(tx_level)
    print('tx_level:', tx_level)

    if params is None:
        params = {}
    default_params.update(params)

    data = data_acquisition(input, default_params)

    result = analysis(data, default_params)

    return data, result


def analysis_test():
    data = util_yy.load_pickle_from_zip(f"./log/OHT_validation/G507VxxYY-T1_2025.3.4_15.19.34_OHT_table_valid_rawdata.zip")
    result = analysis(data)

    test_name = 'spot_jig_test'
    path = f"./log/{test_name}"
    # filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
    # util_yy.save_pickle_to_zip(data, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(result, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_report'  # 확장자 없이
    create_fail_report(result, f"{path}/{filename}.xlsx")


if __name__ == "__main__":
    unittest()
    # analysis_test()
