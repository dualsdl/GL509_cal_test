#!/usr/bin/env python3
#-*- coding : utf-8 -*-

from . import KDC101
from . import gl507_walkerror
from datetime import datetime
import pickle
import numpy as np
import time

import pysoslab_core
import pysoslab_user
import pysoslab_logger
import pysoslab_developer
import os
import sys

# 현재 디렉토리를 저장
original_directory = os.getcwd()
try:
    # 작업할 디렉토리로 변경 (상위 폴더로 이동)
    os.chdir("./..")  # 상위 폴더로 이동
    # print("현재 디렉토리:", os.getcwd())
    # 상위 폴더를 sys.path에 추가
    sys.path.append(os.getcwd())  # 상위 폴더를 경로
    # 모듈을 import
    from . import util_yy  # 예: util_yy.py를 상위 폴더에서 import
    # print("모듈을 정상적으로 import 했습니다.")
finally:
    # 작업이 끝난 후 원래 디렉토리로 돌아가기
    os.chdir(original_directory)
    # print("원래 디렉토리로 돌아왔습니다:", os.getcwd())

##############  parameter start ###############
default_params = {
    "walk_error_stage_dist": [0.0, 12.5],
    "speed_conditions": [
        {"speed": 0.7, "max_pulse_width": 2500},
        {"speed": 0.3, "max_pulse_width": 2000},
        # {"speed": 0.7, "max_pulse_width": 1700},
        {"speed": 0.2, "max_pulse_width": 1300},
        {"speed": 0.15, "max_pulse_width": 1000},
        {"speed": 0.1, "max_pulse_width": 400},
        {"speed": 0.03, "max_pulse_width": 100},
        {"speed": 0.01, "max_pulse_width": 75},
        {"speed": 0.004, "max_pulse_width": 50},
        {"speed": 0.001, "max_pulse_width": 1},
    ],
    "OHT_ld_high_voltage": 11,  # [0.1V]
    "OHT_pd_high_voltage": 100,  # [V]
    "OHT_BR_intensity": 190,  # [0.1ns]

    "OBS_ld_high_voltage": 16,  # [0.1V]
    "OBS_pd_high_voltage": 160,  # [V]
    "OBS_BR_intensity": 420,  # [0.1ns]

    "comparator": 2.20,  # [V]

    "SERIAL_NAME": "COM12",
    "SERIAL_BAUDRATE": 921600,  # 921600, 115200
    "UDP_SENSOR_IP": "10.110.1.2",
    "UDP_SENSOR_PORT": 2000,
    "UDP_PC_IP": "10.110.1.3",
    "UDP_PC_PORT": 3000,
    
    "obs_empty_lut": "./obs_lut.csv",
    "interstitial_param": 0.03,
}
##############  parameter end ###############


def run(input, params: dict = None):
    # 기본 파라미터를 복사하고 전달된 파라미터로 덮어씀
    params_merged = default_params.copy()
    if params is not None:
        params_merged.update(params)
    params = params_merged    
    output = dict()
    print(params)

    output['test_time'] = f"{datetime.now().year}" + \
                    f".{datetime.now().month}" + \
                    f".{datetime.now().day}" + \
                    f'_{datetime.now().strftime("%H.%M.%S")}'

    # LiDAR Serial number read
    success, serial_num = input["GL5_user"].getSerialNum(input["GL5_core"])
    if success:
        print(f"Serial_num = {serial_num}")
        output["GL_serial"] = serial_num
    else:
        print("Unable to get a serial number")
    
    # LiDAR set to Set-up(One-Point) mode
    success = input["GL5_developer"].setOperationMode(input["GL5_core"], 1)
    if success:
        print("Successfully set the Setup Mode")
    else:
        print("Unable to set the Setup Mode")
    
    success = input['GL5_developer'].setCompensation(input["GL5_core"], 0)
    if success:
        print("Successfully set the compensation")
    else:
        print("Unable to set the compensation")
    
    success = input['GL5_developer'].setLUTMode(input["GL5_core"], 0)
    if success:
        print("Successfully set the lut_mode")
    else:
        print("Unable to set the lut_mode")
    
    success = input['GL5_developer'].setComparatorParam(input["GL5_core"], params['comparator'])
    if success:
        print("Successfully set the comparator")
    else:
        print("Unable to set the comparator")

    success = input['GL5_developer'].setInterstitialPointsParam(input["GL5_core"], params['interstitial_param'])
    if success:
        print("[Success] setInterstitialPointsParam")
    else:
        print("[Fail] setInterstitialPointsParam")

    success, min_pulse_width_lut, max_pulse_width_lut = (
        input['GL5_developer'].getMinMaxPulseWidthLUTFromFile(params['obs_empty_lut'])
    )
    if success:
        success = input['GL5_developer'].setMinMaxPulseWidthLUTToSensor(
            input["GL5_core"], min_pulse_width_lut, max_pulse_width_lut
        )
        if success:
            print("Successfully set the min/max_pulse_width_lut to sensor")
        else:
            print("Unable to set the min/max_pulse_width_lut to sensor")
    else:
        print("Unable to load the min/max_pulse_width_lut from file")

    external_output_format = [0, 0, 0]
    external_output_format[0] = 0  # Non invert
    external_output_format[1] = 1  # Gray
    external_output_format[2] = 0  # Near High

    if input['GL5_developer'].setExternalOutputFormat(input["GL5_core"], external_output_format):
        print("Successfully set the external_output_format")
    else:
        print("Unable to set the external_output_format")
    
    # 만약 Gl_serial의 4~5문자가 1W라면 OHT 센서, 1N이라면 OBS 센서
    model_name = serial_num[4:6]
    print(f"Model name: {model_name}")
    if (model_name == '1W' or
            model_name == '1V'):
        ld_hv = params['OHT_ld_high_voltage']
        pd_hv = params['OHT_pd_high_voltage']
        BR_intensity = params['OHT_BR_intensity']
    elif (model_name == '1N' or
            model_name == '1M' or
            model_name == '1R' or
            model_name == '2N'):
        ld_hv = params['OBS_ld_high_voltage']
        pd_hv = params['OBS_pd_high_voltage']
        BR_intensity = params['OBS_BR_intensity']
    else:
        raise ValueError('Unknown sensor type')
    # GL LD HV 셋
    success = input['GL5_developer'].setLDHighVoltage(input["GL5_core"], ld_hv)
    if success:
        print("Successfully set the ld_high_voltage")
    else:
        print("Unable to set the ld_high_voltage")
    success, ld_high_voltage = input['GL5_developer'].getLDHighVoltage(input["GL5_core"])
    if success:
        print(f"ld_high_voltage = {ld_high_voltage}")
    else:
        print("Unable to get the ld_high_voltage")

    # GL PD HV 셋
    success = input['GL5_developer'].setPDHighVoltage(input["GL5_core"], pd_hv)
    if success:
        print("Successfully set the pd_high_voltage")
    else:
        print("Unable to set the pd_high_voltage")
    success, pd_high_voltage = input['GL5_developer'].getPDHighVoltage(input["GL5_core"])
    if success:
        print(f"pd_high_voltage = {pd_high_voltage}")
    else:
        print("Unable to get the pd_high_voltage")

    success = input['GL5_developer'].setBackReflectorPulseWidthTarget(
        input["GL5_core"], int(BR_intensity)
    )
    if success:
        print("Successfully set the back_reflector_pulse_width_target")
    else:
        print("Unable to set the back_reflector_pulse_width_target")

    # walk error stage move to initial position (opening aperture of Receiving lens)
    input['walk_error_stage'].move(target_pos=params['walk_error_stage_dist'][0])
    while input['walk_error_stage'].is_moving():
        pass

    # LiDAR streaming start
    success = input["GL5_user"].setStreamEnable(input["GL5_core"], True)
    if success:
        print("Successfully enable data streaming")
    else:
        print("Failed to enable data streaming")
    
    # delay = 5.0
    # time.sleep(delay)

    # walk error stage move to destination (closing aperture of Receiving lens)
    input['walk_error_stage'].set_velocity(spd_mmps=params['speed_conditions'][0]["speed"])
    input['walk_error_stage'].move(target_pos=params['walk_error_stage_dist'][1])

    # LiDAR streaming logging while walk error stage is moving
    frame_datas = []
    current_speed_index = 0
    start_time = time.time()
    iteration_count = 0
    total_time = 0
    while input['walk_error_stage'].is_moving():
        success, frame_data = input["GL5_user"].getLidarData(input["GL5_core"], False)
        if not success:
            print("Failed to get a LiDAR data")
        
        else:
            current_pulse_width = np.max(np.array(frame_data['pulse_width']).flatten())
            
            # 속도 변경 조건 확인
            if current_pulse_width > 0 and current_speed_index < len(params['speed_conditions']) - 1:
                next_speed_condition = params['speed_conditions'][current_speed_index + 1]
                if current_pulse_width < next_speed_condition["max_pulse_width"]:
                    print("current_pulse_width: ", current_pulse_width)
                    input['walk_error_stage'].stop()
                    input['walk_error_stage'].set_velocity(spd_mmps=next_speed_condition["speed"])
                    input['walk_error_stage'].move(target_pos=params['walk_error_stage_dist'][1])
                    current_speed_index += 1
            else:
                input['walk_error_stage'].stop()

            end_time = time.time()
            iteration_time = end_time - start_time
            start_time = end_time
            total_time += iteration_time
            iteration_count += 1

            # 10번에 한 번씩 실행 주기를 출력
            if iteration_count % 10 == 0:
                avg_time = total_time / iteration_count
                frequency_hz = 1 / avg_time
                print(f"Iteration: {iteration_count}, Average Frequency: {frequency_hz:.2f} Hz, pulse_width: {current_pulse_width}")

            frame_datas.append(frame_data)

    output['frame_datas'] = frame_datas

    return output


def unittest(params: dict = default_params):
    default_params.update(params)
    input = dict()

    walk_error_stage = KDC101.KDC101()
    walk_error_stage.set_velocity(spd_mmps=2.4)
    if walk_error_stage.is_homed():
        pass
        print(f"{walk_error_stage.devices} is homed already")
    else:
        walk_error_stage.home_search()

    GL5_core = pysoslab_core.core()
    GL5_user = pysoslab_user.user()
    GL5_logger = pysoslab_logger.logger()
    GL5_developer = pysoslab_developer.developer()

    # GL5_core.connectSerial(SERIAL_NAME, SERIAL_BAUDRATE)
    GL5_core.connectUDP(
        default_params['UDP_SENSOR_IP'],
        default_params['UDP_SENSOR_PORT'],
        default_params['UDP_PC_IP'],
        default_params['UDP_PC_PORT']
        )

    input['GL5_core'] = GL5_core
    input['GL5_user'] = GL5_user
    input['GL5_logger'] = GL5_logger
    input['GL5_developer'] = GL5_developer
    input['walk_error_stage'] = walk_error_stage

    output = run(input, default_params)

    test_name = 'walk_error'
    path = f"./log/{test_name}"
    save_filename = f"{output['GL_serial']}_" + f'{output["test_time"]}' + f'_{test_name}_rawdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(output, path, save_filename)

    base_filename = f"{output['GL_serial']}_" + f'{output["test_time"]}'
    graph_filename = f'{path}/{base_filename}.png'
    walk_error_table_filename = f'{path}/{base_filename}.csv'
    walk_error_proc_filename = f"{path}/{base_filename}_walkerror_proc_data.zip"

    save_path = f'{path}/{save_filename}.zip'
    gl507_walkerror.run(save_path, walk_error_table_filename, graph_filename, walk_error_proc_filename, 400)

    walk_error_stage.set_velocity(spd_mmps=4.0)
    walk_error_stage.move(target_pos=0.0)
    walk_error_stage.close()

    success, walk_error_lut = GL5_developer.getWalkErrorLUTFromFile(
        walk_error_table_filename
    )
    if success:
        # print("walk_error_lut from file:")
        # for i, value in enumerate(walk_error_lut):
        #     end = ",\n" if i % 30 == 29 else ", "
            # print(f"{value:4}", end=end)
        print()
    else:
        print("Unable to load the walk_error_lut from file")
    
    success = GL5_developer.setWalkErrorLUTToSensor(GL5_core, walk_error_lut)
    if success:
        print("Successfully set the walk_error_lut to sensor")
    else:
        print("Unable to set the walk_error_lut to sensor")

    GL5_core.disconnect()


if __name__ == "__main__":
    unittest()
