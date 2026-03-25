#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import time
from datetime import datetime
import pickle
import math
import zipfile

from stage_lib import ETEL
import pysoslab_etel_stage as py_stage_etel
import pysoslab_core
import pysoslab_user
import pysoslab_developer

# from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter
import pandas as pd
from functions import util_yy

# #############  parameter start ###############
default_parameters = {
    'SERIAL_NAME': "COM4",
    'SERIAL_BAUDRATE': 921600,  # 921600, 115200
    'UDP_SENSOR_IP': "10.110.1.2", 
    'UDP_SENSOR_PORT': 2000,
    'UDP_PC_IP': "10.110.1.3",
    'UDP_PC_PORT': 3000,

    'etel_stage_IP_addr': "10.110.1.200",
    'speed_mmps': 400.0,
    'OHT_target_angle': 0.0,  # OHT는 DG4090
    'OBS_target_angle': -90.0,  # OBS는 92%
    'device_rotation_speed': 30.0,
    'LINEAR_STAGE_OFFSET': -43,

    'oht_cal_dist_points': [
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': -130.0, 
            'distance': [5000.0, 4000.0, 3000.0],
        },
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': -90.0, 
            'distance': [5000.0, 4000.0, 3000.0],
        },
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': -45.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },        
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': 0.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },        
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': 45.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },        
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': 90.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },        
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': 130.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },
    ],
    'obs_cal_dist_points': [
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': -130.0, 
            'distance': [5000.0, 4000.0, 3000.0],
        },
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': -90.0, 
            'distance': [5000.0, 4000.0, 3000.0],
        },
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': -45.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },        
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': 0.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },        
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': 45.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },        
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': 90.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },        
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': 130.0, 
            'distance': [5000.0, 4000.0, 3000.0]
        },
    ],

    'oht_test_dist_points': [
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': -130.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 100.0]
        },        
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': -90.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 100.0]
        },
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': -45.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 100.0]
        },
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': 0.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 50.0]
        },
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': 45.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 100.0]
        },
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': 90.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 100.0]
        },
        {
            'target_angle': 0.0, 'target_name': 'retro', # DG4090
            'device_angle': 130.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 100.0]
        },
    ],
    'obs_test_dist_points': [
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': -130.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },        
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': -90.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': -45.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': 0.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 50.0]
        },
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': 45.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': 90.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': -90.0, 'target_name': '92%', # 10%
            'device_angle': 130.0, 
            'distance': [5000.0, 4000.0, 3000.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': 0.0, 'target_name': '10%', # 10%
            'device_angle': -130.0, 
            'distance': [2500.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },        
        {
            'target_angle': 0.0, 'target_name': '10%', # 10%
            'device_angle': -90.0, 
            'distance': [2500.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': 0.0, 'target_name': '10%', # 10%
            'device_angle': -45.0, 
            'distance': [2500.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': 0.0, 'target_name': '10%', # 10%
            'device_angle': 0.0, 
            'distance': [2500.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 50.0]
        },
        {
            'target_angle': 0.0, 'target_name': '10%', # 10%
            'device_angle': 45.0, 
            'distance': [2500.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': 0.0, 'target_name': '10%', # 10%
            'device_angle': 90.0, 
            'distance': [2500.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
        {
            'target_angle': 0.0, 'target_name': '10%', # 10%
            'device_angle': 130.0, 
            'distance': [2500.0, 2000.0, 1000.0, 500.0, 300.0, 250.0, 200.0, 170.0, 150.0, 120.0, 115.0]
        },
    ],

    'logging_frame_num': 40,
    'ROI_width': 0.150,  # 150mm

    'precision_pass_criteria': 0.03,  # 30mm
    'accuracy_pass_criteria': 0.03  # 30mm
}
# #############  parameter end ###############


def save_to_excel(data: dict, filename: str):
    df = pd.DataFrame(data['results'])

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Analysis Results')

        # Formatting the Excel sheet
        workbook = writer.book
        worksheet = writer.sheets['Analysis Results']

        # Setting column widths
        for column in worksheet.columns:
            max_length = 0
            column_name = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except TypeError:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_name].width = adjusted_width

        # Setting header styles
        header_font = Font(bold=True)
        for cell in worksheet["1:1"]:
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')


def data_acquisition(input: dict, params: dict) -> dict:
    output = dict()

    output['test_time'] = f"{datetime.now().year}" + \
                    f".{datetime.now().month}" + \
                    f".{datetime.now().day}" + \
                    f'_{datetime.now().strftime("%H.%M.%S")}'
    
    stage_etel = input['stage_etel']
    GL5_user = input['GL5_user']
    GL5_core = input['GL5_core']
    GL5_developer = input['GL5_developer']

    # print()
    # print(input['test_dist'])
    # print()
    
    success, back_reflector_distance_target = GL5_developer.getBackReflectorDistanceTarget(GL5_core)
    if success:
        output['back_reflector_distance_target'] = back_reflector_distance_target
        print(f"back_reflector_distance_target = {back_reflector_distance_target}")
    else:
        print("Unable to get the back_reflector_distance_target")

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, params['speed_mmps'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)

    success, GL_serial = GL5_user.getSerialNum(GL5_core)
    if success:
        print(f"Serial_num = {GL_serial}")
    else:
        print("Unable to get a serial number")
    output['GL_serial'] = GL_serial

    # LiDAR streaming start
    success = input["GL5_user"].setStreamEnable(input["GL5_core"], True)
    if success:
        print("Successfully enable data streaming")
    else:
        print("Failed to enable data streaming")

    output['raw_data'] = []
    for test_cond in input['test_dist']:
        for test_dist in test_cond['distance']:
            raw_data = dict()
            raw_data['device_angle'] = test_cond['device_angle']
            raw_data['test_distance'] = test_dist
            raw_data['target_name'] = test_cond['target_name']
            # raw_data['target_angle'] = test_cond['target_angle']

            stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET,
                              test_dist, params['speed_mmps'])
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                time.sleep(0.2)
            print(f'LINEAR_5000 stopped at {test_dist}mm')

            stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, test_cond['target_angle'], params['device_rotation_speed'])
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
                time.sleep(0.2)
            
            stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE,
                                raw_data['device_angle'], params['device_rotation_speed'])
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
                time.sleep(0.2)
            print(f'Device stopped at {raw_data["device_angle"]}deg')

            logging_datas = []
            cnt = 0
            while (cnt < params['logging_frame_num']):
                success, frame_data = input["GL5_user"].getLidarData(input["GL5_core"], False)
                if not success:
                    print("Failed to get a LiDAR data")
                else:
                    logging_datas.append(frame_data)
                    cnt += 1
            raw_data['frame_datas'] = logging_datas
            output['raw_data'].append(raw_data)

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, params['speed_mmps'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, -90.0, 50.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
        time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 0.0, params['device_rotation_speed'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)

    return output


def analysis(input: dict, params: dict) -> dict:
    output = dict()
    output['GL_serial'] = input.get('GL_serial', None)
    output['test_time'] = input.get('test_time', None)
    output['back_reflector_distance_target'] = input.get('back_reflector_distance_target', np.nan)

    angle_dist_outputs = []    
    accuracy_array = []
    for data in input['raw_data']:
        device_angle = data['device_angle']
        target_name = data['target_name']
        # target_angle = data['target_angle']
        test_dist = data['test_distance'] / 1000.0
        print(f"device_angle = {device_angle}, test_dist = {test_dist}")
        frame_datas = data['frame_datas']

        ROI_angle_width = np.degrees(np.arctan(params['ROI_width'] / 2 / test_dist))
        print(f"ROI_angle_width = {ROI_angle_width}")
        idx_center = device_angle / 0.18 + 749.5
        idx_range = np.array([-np.floor(ROI_angle_width / 0.18), np.floor(ROI_angle_width / 0.18)], dtype=np.int64)
        idx = np.array(np.array(idx_center, dtype=np.int64) + idx_range)
        idx = np.clip(idx, 0, 1499)  # 0 미만과 1499 초과인 값 제거

        x_array = []
        y_array = []
        intensity_array = []
        r_array = []
        for framedata in frame_datas:
            x = framedata['x'][idx[0]:idx[1]]  # indexing
            y = framedata['y'][idx[0]:idx[1]]  # indexing
            pulse_width = framedata['pulse_width'][idx[0]:idx[1]]  # indexing
            r = framedata['distance'][idx[0]:idx[1]]  # indexing

            x_rotated, y_rotated = util_yy.rotate_points(x, y, device_angle)  # 인덱싱된 포인트 회전변환하여 정면에 타겟이 있게

            x_array.append(x_rotated)
            y_array.append(y_rotated)
            intensity_array.append(pulse_width)
            r_array.append(r)

        x_array = np.array(x_array).flatten()
        y_array = np.array(y_array).flatten()
        intensity_array = np.array(intensity_array).flatten()
        r_array = np.array(r_array).flatten()

        idx = (r_array > 0)
        idx = np.logical_and(idx, r_array < 20)
        idx = np.logical_and(idx, y_array > 0)
        idx = np.logical_and(idx, x_array < 0.5)
        idx = np.logical_and(idx, x_array > -0.5)
        x_array = x_array[idx]
        y_array = y_array[idx]
        intensity_array = intensity_array[idx]

        angle_dist_output = dict()
        angle_dist_output["device_angle"] = device_angle        
        angle_dist_output['target_name'] = target_name
        # angle_dist_output['target_angle'] = target_angle
        angle_dist_output["test_dist"] = test_dist
        if np.all(np.isnan(y_array)):
            angle_dist_output["precision"] = np.nan
            angle_dist_output["accuracy"] = np.nan
            angle_dist_output["precision_pass"] = 'FAIL'
            angle_dist_output["accuracy_pass"] = 'FAIL'
        else:
            angle_dist_output["precision"] = np.nanstd(y_array)
            angle_dist_output["accuracy"] = np.nanmean(y_array) - test_dist
            accuracy_array.append(angle_dist_output["accuracy"])

            if np.abs(angle_dist_output["precision"]) < params['precision_pass_criteria']:
                angle_dist_output["precision_pass"] = 'PASS'
            else:
                angle_dist_output["precision_pass"] = 'FAIL'

            if np.abs(angle_dist_output["accuracy"]) < params['accuracy_pass_criteria']:
                angle_dist_output["accuracy_pass"] = 'PASS'
            else:
                angle_dist_output["accuracy_pass"] = 'FAIL'

        angle_dist_outputs.append(angle_dist_output)

    output['results'] = angle_dist_outputs
    output['distance_offset_compensation'] = np.nanmean(accuracy_array) * 1000.0
    print(f'accuracy_array = {accuracy_array}')

    return output


def run(input: dict, params: dict = None) -> dict:
    if params is None:
        params = {}
    default_parameters.update(params)
    # print('default_params:', default_parameters)
    raw_data = data_acquisition(input, default_parameters)

    outputs = analysis(raw_data, default_parameters)

    return raw_data, outputs


def unittest(params: dict = default_parameters):
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
    stage_etel.moveTo(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, params['speed_mmps']
        )
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)
    ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET)
    print('ROTARY_TARGET home search done')

    # GL connect
    GL5_core = pysoslab_core.core()
    GL5_user = pysoslab_user.user()
    GL5_developer = pysoslab_developer.developer()
    GL5_core.connectUDP(params['UDP_SENSOR_IP'], params['UDP_SENSOR_PORT'], params['UDP_PC_IP'], params['UDP_PC_PORT'])
    
    success, GL_serial = GL5_user.getSerialNum(GL5_core)
    if success:
        print(f"Serial_num = {GL_serial}")
    else:
        print("Unable to get a serial number")

    input = dict()

    model_name = GL_serial[4:6]
    print(f"Model name: {model_name}")
    if (model_name == '1W' or
            model_name == '1V'):
        test_cond = params['oht_cal_dist_points']
    elif (model_name == '1N' or
            model_name == '1M' or
            model_name == '1R' or
            model_name == '2N'):
        test_cond = params['obs_cal_dist_points']
    else:
        raise ValueError('Unknown sensor type')
    input['test_dist'] = test_cond
    # print(parameter['test_dist'])
    
    input['stage_etel'] = stage_etel
    input['GL5_core'] = GL5_core
    input['GL5_user'] = GL5_user
    input['GL5_developer'] = GL5_developer
    input['test_dist'] = test_cond

    stage_etel.setOffset(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, params['LINEAR_STAGE_OFFSET']
    )

    raw_data, outputs = run(input, params)

    test_name = 'distance_offset'
    path = f"./log/{test_name}"
    filename = f"{raw_data['GL_serial']}_" + f'{raw_data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(raw_data, path, filename)

    filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(outputs, path, filename)

    success, back_reflector_distance_target = input['GL5_developer'].getBackReflectorDistanceTarget(input['GL5_core'])
    if success:
        print(f"old back_reflector_distance_target = {back_reflector_distance_target}")
        print(f"distance_offset_compensation = {outputs['distance_offset_compensation']}")
        back_reflector_distance_target = int(back_reflector_distance_target -
                                             outputs['distance_offset_compensation'])
        print('new back_reflector_distance_target =', back_reflector_distance_target)
        success = input['GL5_developer'].setBackReflectorDistanceTarget(input['GL5_core'],
                                                                        back_reflector_distance_target)
        if success:
            print(f"Successfully set the back_reflector_distance_target({int(back_reflector_distance_target)})")
        else:
            print("Unable to set the back_reflector_distance_target")
    else:
        print("Unable to get the back_reflector_distance_target")

    model_name = GL_serial[4:6]
    print(f"Model name: {model_name}")
    if (model_name == '1W' or
            model_name == '1V'):
        test_cond = params['oht_test_dist_points']
    elif (model_name == '1N' or
            model_name == '1M' or
            model_name == '1R' or
            model_name == '2N'):
        test_cond = params['obs_test_dist_points']
    else:
        raise ValueError('Unknown sensor type')
    input['test_dist'] = test_cond
    # print(parameter['test_dist'])
    raw_data, outputs = run(input, params)

    test_name = 'distance_test'
    path = f"./log/{test_name}"
    filename = f"{raw_data['GL_serial']}_" + f'{raw_data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(raw_data, path, filename)

    filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(outputs, path, filename)

    filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_report'  # 확장자 없이
    distance_result_path = f"{path}/{filename}.xlsx"

    save_to_excel(outputs, distance_result_path)


def analysis_test():
    import sys
    from PySide6.QtWidgets import QApplication, QFileDialog

    app = QApplication(sys.argv)

    distance_test_result_fname, _ = QFileDialog.getOpenFileName(
        None,                          # 부모 위젯 없음
        "Distance Test 결과 파일 선택",   # 대화상자 제목
        "",             # 초기 디렉토리
        "ZIP 파일 (*.zip);;모든 파일 (*)"  # 파일 필터 (zip 우선)
    )
    data = util_yy.load_pickle_from_zip(distance_test_result_fname)
    
    result = analysis(data, default_parameters)
    print(result['GL_serial'])

    test_name = 'distance_test'
    path = f"./log/{test_name}"
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(result, path, filename)
    filename = f"{result['GL_serial']}_" + f'{result["test_time"]}' + f'{test_name}_report'  # 확장자 없이
    distance_result_path = f"{path}/{filename}.xlsx"

    save_to_excel(result, distance_result_path)

if __name__ == "__main__":
    unittest()
    # analysis_test()
    print('done')
