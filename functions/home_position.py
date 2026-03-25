#!/usr/bin/env python3
#-*- coding : utf-8 -*-

import numpy as np
import time
from datetime import datetime

import sys
import os
try:
    from stage_lib import ETEL
except:
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   from stage_lib import ETEL

import pysoslab_etel_stage as py_stage_etel

import pysoslab_core
import pysoslab_user
import pysoslab_developer

from functions.util_yy import save_pickle_to_zip, load_pickle_from_zip

# #############  parameter start ###############
default_params = {
    "SERIAL_NAME": "COM4",
    "SERIAL_BAUDRATE": 921600,  # 921600, 115200
    "UDP_SENSOR_IP": "10.110.1.2",
    "UDP_SENSOR_PORT": 2000,
    "UDP_PC_IP": "10.110.1.3",
    "UDP_PC_PORT": 3000,
    "etel_stage_IP_addr": "10.110.1.200",
    "LINEAR_STAGE_OFFSET": -43,
    "speed_mmps": 400.0,
    "OHT_target_angle": 0,  # OBS는 92%
    "OBS_target_angle": -90,  # OHT는 DG4090
    "device_rotation_speed": 30.0,
    "test_distance": 5000.0,
    "device_angle": 0,
    "logging_frame_num": 200,
    "frame_size": 1500,
    "home_position_pass_criteria": 3
}
# #############  parameter end ###############


def data_acquisition(input: dict, params: dict) -> dict:
    output = dict()
    output['test_time'] = f"{datetime.now().year}" + \
                        f".{datetime.now().month}" + \
                        f".{datetime.now().day}" + \
                        f'_{datetime.now().strftime("%H.%M.%S")}'

    stage_etel = input['stage_etel']
    GL5_core = input['GL5_core']
    GL5_user = input['GL5_user']
    
    success, home_position = input['GL5_developer'].getHomePosition(input['GL5_core'])
    if success:
        output['prev_home_position'] = home_position
    else:
        print("Unable to get the home position")

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
        target_angle = params["OHT_target_angle"]
    elif (model_name == '1N' or
            model_name == '1M' or
            model_name == '1R' or
            model_name == '2N'):
        target_angle = params["OBS_target_angle"]
    else:
        raise ValueError('Unknown sensor type')

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, params['test_distance'], params['speed_mmps'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, params['device_angle'], params['device_rotation_speed'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)

    # 시리얼 규칙으로 조건문 만들어서 할것, OHT는 DG4090, OBS는 92%
    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, target_angle, 30.0)
    print('ROTARY_TARGET move to {}'.format(target_angle))
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
        time.sleep(0.2)

    success = input['GL5_developer'].setCompensation(input["GL5_core"], 2)
    if success:
        print("Successfully set the compensation")
    else:
        print("Unable to set the compensation")
    
    success = input['GL5_developer'].setLUTMode(input["GL5_core"], 1)
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

    logging_datas = []
    cnt = 0

    while (cnt < params['logging_frame_num']):
        success, frame_data = GL5_user.getLidarData(GL5_core, False)
        if not success:
            print("Failed to get a LiDAR data")      
        else:
            logging_datas.append(frame_data)
            cnt += 1
            # print(f"frame {cnt} is acquired")
    output['raw_data'] = logging_datas

    return output


def analysis(input: dict, params: dict) -> dict:
    output = dict()
    output['test_time'] = input['test_time']
    output['GL_serial'] = input['GL_serial']

    center_idx = []
    for frame_data in input['raw_data']:
        x = np.array(frame_data['x'])
        y = np.array(frame_data['y'])
        r = np.array(frame_data['distance'])

        # idx searching
        idx = r > 3.00
        # print(np.where(idx))
        idx = np.bitwise_and(idx, r < 7.00)
        # print(np.where(idx))
        idx = np.bitwise_and(idx, x < 0.500)
        # print(np.where(idx))
        idx = np.bitwise_and(idx, x > -0.500)
        # print(np.where(idx))
        idx = np.bitwise_and(idx, y < 6.00)  # 2차 보정 장치 ROI 내 HP_UNDERLIMIT2
        # print(np.where(idx))
        idx = np.bitwise_and(idx, y > 4.00)  # 2차 보정 장치 ROI 내 HP_UPPERLIMIT2
        # print(np.where(idx))

        if np.any(idx):
            first = np.min(np.where(idx))
            last = np.max(np.where(idx))
            center_idx.append((first + last) / 2.0)
            # print(f"first = {first}, last = {last}")
            # print(f"center_idx = {center_idx}")
        else:
            print("No valid indices found in this frame.")
            # center_idx.append((frame_size - 1) / 2)  # 기본값으로 중앙 인덱스를 사용

        # center_idx.append((first_idx + last_idx) / 2)
    print(f"center_idx = {center_idx}")
    # print(f"first_idx = {first_idx}")
    # print(f"last_idx = {last_idx}")

    output['home_position_error'] = np.median(center_idx) - (params['frame_size']-1)/2.0
    # output['home_position_error'] = np.mean(center_idx) - (params['frame_size']-1)/2.0
    print(f"home_position_error = {output['home_position_error']}")
    output['prev_home_position'] = input.get('prev_home_position', np.nan)
    output['proposed_home_position'] = np.clip(np.round(output['prev_home_position'] + output['home_position_error']), 0, 99)
    if abs(output['home_position_error']) < params['home_position_pass_criteria']:
        output['home_position_test_result'] = 'PASS'
    else:
        output['home_position_test_result'] = 'FAIL'
    return output


def run(input: dict, params: dict = None) -> dict:
    if params is None:
        params = {}
    default_params.update(params)
    print('default_params:', default_params)

    success = input['GL5_developer'].setBackReflectorDistanceTarget(input['GL5_core'], # temperary code 250823s
                                                                    1100)
    if success:
        print(f"Successfully set the back_reflector_distance_target(1100) : temperary code 250823")
    else:
        print("Unable to set the back_reflector_distance_target")

    data = data_acquisition(input, default_params)
    result = analysis(data, default_params)

    success = input['GL5_developer'].setHomePosition(input['GL5_core'], int(result['proposed_home_position']))
    if success:
        print(f"Successfully set the home position: {int(result['proposed_home_position'])}")
    else:
        print("Unable to set the home position")

    data = data_acquisition(input, default_params)
    result = analysis(data, default_params)

    
    #result의 홈포지션 에러값을 출력
    print(f"home_position_error = {result['home_position_error']}")

    return data, result


def unittest():
    # ETEL stage connect
    stage_etel = py_stage_etel.stage_etel()
    status = stage_etel.connect(default_params['etel_stage_IP_addr'], 3)
    if status:
        pass
    else:
        raise Exception('ETEL stage initialing FAIL')

    stage_etel.setOffset(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, default_params['LINEAR_STAGE_OFFSET']
    )

    time.sleep(0.5)
    ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE)
    print('ROTARY_DEVICE home search done')

    ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET)
    print('LINEAR_TARGET home search done')
    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, default_params['test_distance'], default_params['speed_mmps'])
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

    data, result = run(input, None)
    # print(result)

    test_name = 'home_position'
    path = f"./log/{test_name}"
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
    save_pickle_to_zip(data, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    save_pickle_to_zip(result, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_report.txt'  # 확장자 없이
    np.savetxt(f'{path}/{filename}', [f'homepositon result is {result["home_position_error"]:.3f}[idx]'], fmt ='%s')


def analysis_test():
    path = 'I:\\gui_test\\log\\home_position'
    filename = 'G5091W3053002_2025.6.10_16.26.33home_position_rawdata.zip'
    data = load_pickle_from_zip(f'{path}/{filename}')
    
    result = analysis(data, default_params)
    # print(result)

    test_name = 'home_position'
    path = f"./log/{test_name}"
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    save_pickle_to_zip(result, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_report.txt'  # 확장자 없이
    np.savetxt(f'{path}/{filename}', [f'homepositon result is {result["home_position_error"]:.3f}[idx]'], fmt ='%s')


if __name__ == "__main__":
    # unittest()
    analysis_test()
    print('done')
