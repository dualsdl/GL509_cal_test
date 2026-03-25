#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import time
from datetime import datetime
from functions import util_yy

try:
    from stage_lib import ETEL
    import pysoslab_etel_stage as py_stage_etel
except ImportError:
    pass
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
default_parameter = {
    'gl5_serial': {
        'name': "COM4",
        'baudrate': 921600  # 921600, 115200
    },
    'gl5_udp': {
        'sensor_ip': "10.110.1.2",
        'sensor_port': 2000,
        'pc_ip': "10.110.1.3", 
        'pc_port': 3000
    },
    'etel_stage': {
        'ip_addr': "10.110.1.200",
        'speed_mmps': 400.0,
        'device_rotation_speed': 30.0,
        'linear_stage_offset': -43
    },
    'validation_area_path': './OHT_filtering_validataion_area.json',
    'empty_area_path': './empty_area.json',
    'validation_cond': {
        'retro0': {
            'target_angle': 0.0,
            'dist_offset': 0.0,
            'measurements': {
                # dist[0]은 초기위치(항상 5000.0)로 사용
                "-130.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 2},
                "-90.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 3},
                "-45.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 4},
                "0.0": {'dist': [5000.0, 1000.0, 50.0], 'moving_speed': [400.0, 250.0], 'selected_area': 1},
                "45.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 5},
                "90.0": {'dist': [5000.0, 1000.0, 120.0], 'moving_speed': [400.0, 250.0], 'selected_area': 6},
                "130.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 7}
            },
            'plt_color': 'royalblue'
        },
        'retro42': {
            'target_angle': -90,
            'dist_offset': 131.0,
            'measurements': {
                "-130.0": {'dist': [5000.0, 1000.0, 150.0], 'moving_speed': [400.0, 250.0], 'selected_area': 2},
                "-90.0": {'dist': [5000.0, 1000.0, 170.0], 'moving_speed': [400.0, 250.0], 'selected_area': 3},
                "-45.0": {'dist': [5000.0, 1000.0, 150.0], 'moving_speed': [400.0, 250.0], 'selected_area': 4},
                "0.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 1},
                "45.0": {'dist': [5000.0, 1000.0, 150.0], 'moving_speed': [400.0, 250.0], 'selected_area': 5},
                "90.0": {'dist': [5000.0, 1000.0, 170.0], 'moving_speed': [400.0, 250.0], 'selected_area': 6},
                "130.0": {'dist': [5000.0, 1000.0, 150.0], 'moving_speed': [400.0, 250.0], 'selected_area': 7}
            },
            'plt_color': 'cornflowerblue'
        },
        'profile': {
            'target_angle': 180.0,
            'dist_offset': 80.0,
            'measurements': {
                "-130.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 2},
                "-90.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 3},
                "-45.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 4},
                "0.0": {'dist': [5000.0, 1000.0, 50.0], 'moving_speed': [400.0, 250.0], 'selected_area': 1},
                "45.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 5},
                "90.0": {'dist': [5000.0, 1000.0, 120.0], 'moving_speed': [400.0, 250.0], 'selected_area': 6},
                "130.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 7}
            },
            'plt_color': 'darkviolet'
        },
        'semes_white': {
            'target_angle': 90.0,
            'dist_offset': 0.0,
            'measurements': {
                "-130.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 2},
                "-90.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 3},
                "-45.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 4},
                "0.0": {'dist': [5000.0, 1000.0, 50.0], 'moving_speed': [400.0, 250.0], 'selected_area': 1},
                "45.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 5},
                "90.0": {'dist': [5000.0, 1000.0, 120.0], 'moving_speed': [400.0, 250.0], 'selected_area': 6},
                "130.0": {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 250.0], 'selected_area': 7}
            },
            'plt_color': 'silver'
        }
    }
}
# #############  parameter end ###############


def unittest(parameter: dict = default_parameter) -> None:
    # ETEL stage connect
    stage_etel = py_stage_etel.stage_etel()
    status = stage_etel.connect(parameter['etel_stage']['ip_addr'], 3)
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
    GL5_core.connectUDP(parameter['gl5_udp']['sensor_ip'], 
                        parameter['gl5_udp']['sensor_port'], 
                        parameter['gl5_udp']['pc_ip'], 
                        parameter['gl5_udp']['pc_port'])

    input = dict()
    input['stage_etel'] = stage_etel
    input['GL5_core'] = GL5_core
    input['GL5_user'] = GL5_user
    input['GL5_developer'] = GL5_developer
    input['GL5_area'] = GL5_area

    stage_etel.setOffset(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, parameter['etel_stage']['linear_stage_offset']
    )

    raw_data, outputs = run(input, parameter)
    
    test_name = 'oht_filtering_validation'
    path = f"./log/{test_name}"
    filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(raw_data, path, filename)

    filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(outputs, path, filename)

    filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + '_OHT_filtering_valid_report'
    create_fail_report(outputs, f"{path}/{filename}.xlsx")


def data_acquisition(input: dict, parameter: dict) -> dict:
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

    success, areas = GL5_area.getAllAreaFromFile(parameter['validation_area_path'])
    print(areas)
    if success:
        success = GL5_area.setAllAreaToSensor(GL5_core, GL5_user, areas)
        if success:
            print("Successfully set the areas")
        else:
            print("Unable to set the areas")
    else:
        print("Unable to read the areas from file")
            
    success = GL5_developer.setCompensation(GL5_core, 15)
    if success:
        print("Successfully set the compensation")
    else:
        print("Unable to set the compensation")
    
    success = GL5_developer.setLUTMode(GL5_core, 2)
    if success:
        print("Successfully set the lut_mode")
    else:
        print("Unable to set the lut_mode")

    send_str = f'area console setting'
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

    for target_name, target_cond in parameter['validation_cond'].items():
        output[target_name] = dict()
        # print(f'{target_name}_data acquisition start')

        # 초기 위치로 이동
        stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 1000.0, 400.0)
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
            time.sleep(0.2)

        stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, target_cond['target_angle'], 30.0)
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
            time.sleep(0.2)
        
        dist_offset = target_cond['dist_offset']

        for device_angle, params in target_cond['measurements'].items():
            output[target_name][f'{device_angle}'] = dict()
            
            # 초기 위치로 이동
            dist_list = params['dist']
            speed_list = params['moving_speed']

            # dist_list[0]은 초기위치 (항상 5000.0)
            stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, dist_list[0], 400.0)
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                time.sleep(0.2)

            stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, float(device_angle), parameter['etel_stage']['device_rotation_speed'])
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
            # 거리 이동은 dist_list[i+1]로 수행 (dist_list[0]은 초기위치)
            move_cnt = min(len(speed_list), len(dist_list) - 1)
            for i in range(move_cnt):
                # 현재 위치로 이동
                stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 
                                  dist_list[i + 1] + dist_offset, 
                                  speed_list[i])
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

            output[target_name][f'{device_angle}']['logging_datas'] = logging_datas
            output[target_name][f'{device_angle}']['plt_color'] = target_cond['plt_color']

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 0.0, parameter['etel_stage']['device_rotation_speed'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)

    success, areas = GL5_area.getAllAreaFromFile(parameter['empty_area_path'])
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


def analysis(input: dict, parameter: dict) -> dict:
    output = dict()
    output['GL_serial'] = input['GL_serial']
    output['test_time'] = input['test_time']

    for target_name in input.keys():
        if target_name == 'GL_serial' or target_name == 'test_time':
            pass
        else:        
            output[target_name] = {}
            output[target_name]['data'] = []
            for device_angle_str in input[target_name].keys():
                for data in input[target_name][device_angle_str]['logging_datas']:
                    # print(frame_data.keys())
                    # input_area = frame_data['input_area']
                    output_level = data['frame_data']['output_level']

                    if target_name[:5] == 'retro':
                        is_passed = output_level != 0
                    else:
                        is_passed = output_level == 0

                    output[target_name]['data'].append({
                        'dist': data['test_test'],  # 5m stage dist read
                        'device_angle': device_angle_str,
                        'is_passed': is_passed,
                        })
    
    output[target_name]['is_passed'] = True
    for target_name in input.keys():
        if target_name == 'GL_serial' or target_name == 'test_time':
            pass
        else:        
            output[target_name]['is_passed'] = True
            for device_angle_str in input[target_name].keys():
                for data in output[target_name]['data']:
                    if data['is_passed'] == False:
                        output[target_name]['is_passed'] = False
                        break
    
    return output


def create_fail_report(output_data: dict, filename: str = 'fail_report.xlsx'):
    """
    1) 타겟별 요약 정보 (PASS/FAIL)를 '요약' 시트에 기록
    2) Fail 항목의 상세 내역을 '상세' 시트에 기록
    """
    
    # 1) 요약 정보 작성
    summary_rows = []
    for target_name, target_data in output_data.items():
        if target_name in ['GL_serial', 'test_time', 'report_path']:
            continue
        if not isinstance(target_data, dict):
            print(f"경고: {target_name}의 데이터가 dict가 아님: {target_data}")
            continue
        summary_rows.append({
            '타겟 이름': target_name,
            '결과': 'PASS' if target_data.get('is_passed', False) else 'FAIL'
        })
    
    df_summary = pd.DataFrame(summary_rows)

    for k, v in output_data.items():
        print(f"{k}: {type(v)}")
        
    # 2) 상세 정보 작성 (Fail 항목만)
    detail_rows = []
    for target_name, target_data in output_data.items():
        # GL_serial과 test_time은 건너뛰기
        if target_name in ['GL_serial', 'test_time', 'report_path']:
            continue
        
        if not isinstance(target_data, dict):
            print(f"경고: {target_name}의 데이터가 dict가 아님: {target_data}")
            continue

        # print(f"target_data: {target_data}")
        
        for data in target_data['data']:
            if not data['is_passed']:
                detail_rows.append({
                    # 'No.': len(detail_rows) + 1,
                    'Target': target_name,
                    'Distance': data['dist'],
                    'Device Angle': data['device_angle'],
                    'Pass/Fail': 'FAIL'
                })
    
    df_details = pd.DataFrame(detail_rows)

    # 3) Excel 파일로 저장 (두 개의 시트)
    with pd.ExcelWriter(filename) as writer:
        df_summary.to_excel(writer, sheet_name='요약', index=False)
        df_details.to_excel(writer, sheet_name='상세', index=False)

    print(f"리포트가 '{filename}' 파일로 저장되었습니다.")



def run(input: dict, parameter: dict) -> dict:
    if parameter is None:
        parameter = {}
    default_parameter.update(parameter)
    print('default_parameter:', default_parameter)
    data = data_acquisition(input, default_parameter)

    result = analysis(data, default_parameter)        

    return data, result


def analysis_test():
    import sys
    from PySide6.QtWidgets import QApplication, QFileDialog

    app = QApplication(sys.argv)

    oht_validation_result_fname, _ = QFileDialog.getOpenFileName(
        None,                          # 부모 위젯 없음
        "OHT Validation 결과 파일 선택",   # 대화상자 제목
        "",             # 초기 디렉토리
        "ZIP 파일 (*.zip);;모든 파일 (*)"  # 파일 필터 (zip 우선)
    )
    data = util_yy.load_pickle_from_zip(oht_validation_result_fname)
    outputs = analysis(data, default_parameter)

    # 타겟별 결과 출력
    for target_name, target_data in outputs.items():
        if target_name in ['GL_serial', 'test_time']:
            continue
        print(f'{target_name} 결과: {target_data["is_passed"]}')

    test_name = 'oht_filtering_validation'
    path = f"./log/{test_name}"
    filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(outputs, path, filename)

    filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + '_OHT_filtering_valid_report'
    create_fail_report(outputs, f"{path}/{filename}.xlsx")

if __name__ == "__main__":
    unittest()
    # analysis_test()
