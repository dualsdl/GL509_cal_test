#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import time
from datetime import datetime
import util_yy

import pysoslab_etel_stage as py_stage_etel
import pysoslab_core
import pysoslab_user
import pysoslab_developer
import pysoslab_area

# stage_lib을 import하기 위해 프로젝트 루트를 sys.path에 추가
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage_lib.ETEL import test_stage, search_home, get_current_position
from stage_lib.DPIN import DpinStageHandler as DPIN

# from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use("TkAgg")  # 예: TkAgg 백엔드 사용
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0

from scipy.ndimage import minimum_filter, maximum_filter, median_filter
from scipy.ndimage import gaussian_filter
from scipy.interpolate import CubicSpline


# #############  parameter start ###############
default_parameters = {
    "SERIAL_NAME": "COM4",
    "SERIAL_BAUDRATE": 921600,  # 921600, 115200
    "UDP_SENSOR_IP": "10.110.1.2",
    "UDP_SENSOR_PORT": 2000,
    "UDP_PC_IP": "10.110.1.3",
    "UDP_PC_PORT": 3000,
    "etel_stage_IP_addr": "10.110.1.200",
    "speed_mmps": 400.0,
    "target_angle": 90,  # OHT는 DG4090
    # "target_angle": -90,  # OBS는 92%
    "device_rotation_speed": 30.0,
    "LINEAR_STAGE_OFFSET": -43,
    # "LINEAR_STAGE_OFFSET_retro40": -43 + 188
    "test_cond": {
        'spot_jig': {
            'target_angle': 180.0,
            'measurements': {
                '0.0': {'dist': [1200.0, 150.0], 'moving_speed': 100.0, 'selected_area': 1},
            },
            'plt_color': 'darkslategrey'
        },
    },
    "ROI_width": 0.2,
    # "test_area_file_path": "./OHT_filtering_validataion_area.json",
    "empty_area_file_path": "./empty_area.json",
    # "log_path": "./log/spot_jig_lut_gen",
    "log_path": "./log/spot_jig_lut_gen",
}
# #############  parameter end ###############


def data_acquisition(input: dict, parameters: dict) -> dict:
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

    success, areas = GL5_area.getAllAreaFromFile(parameters["empty_area_file_path"])
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

    success = GL5_developer.setLUTMode(GL5_core, 1)  # walk error 모드
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

    for target_name, target_cond in parameters["test_cond"].items():
        output[target_name] = dict()
        # print(f'{target_name}_data acquisition start')

        stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, target_cond['target_angle'], 30.0)
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
            time.sleep(0.2)

        for device_angle, params in target_cond['measurements'].items():            
            # print('2')
            output[target_name][device_angle] = dict()

            logging_datas = []
            dist_list = params['dist']
            speed = params['moving_speed']

            # 초기 위치로 이동
            stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 1000, 400.0)
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                time.sleep(0.2)

            stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, float(device_angle), parameters["device_rotation_speed"])
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
                time.sleep(0.2)

            print(f'{target_name}_GlAngle_{float(device_angle):.1f}_data acquisition start')

            for i in range(len(dist_list)):
                # print('1')
                # 현재 위치로 이동
                stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, dist_list[i], speed)
                print(f'dist_list[{i}]:', dist_list[i])
                # time.sleep(0.1)
                while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                    success, frame_data = GL5_user.getLidarData(GL5_core, False)
                    if not success:
                        print("Failed to get a LiDAR data")
                    else:
                        logging_datas.append({
                            'frame_data': frame_data,
                            'test_test': get_current_position(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET)
                            })
                        # print(get_current_position(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET))

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

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 0.0, parameters["device_rotation_speed"])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)

    return output


def analysis(input: dict, parameters: dict) -> dict:    
    output = dict()

    spot_jig_dist = np.array([])
    spot_jig_intensity = np.array([])
    for target_name in input.keys():
        if target_name == 'GL_serial' or target_name == 'test_time':
            pass
        else:
            for device_angle_str in input[target_name].keys():
                device_angle = float(device_angle_str)
                center_idx = np.round((device_angle / 0.18)+(1500/2))
                center_idx = np.clip(center_idx, 0, 1499)
                center_idx = np.int64(center_idx)

                ROI_dist = []
                ROI_intensity = []
                for data in input[target_name][device_angle_str]['logging_datas']:
                    dist = data['frame_data']['distance']
                    intensity = data['frame_data']['pulse_width']

                    # Select the relevant slice around center_idx
                    selected_slice = np.array(dist[center_idx-3:center_idx+3])

                    # Exclude zeros and NaN values from the calculation
                    filtered_slice = selected_slice[(selected_slice != 0) & (~np.isnan(selected_slice))]

                    # Calculate the mean excluding zeros and NaN values
                    test_dist = np.nanmean(filtered_slice)

                    if test_dist == 0:
                        break
                    ROI_angle_width = np.degrees(np.arctan(parameters['ROI_width'] / 2 / test_dist))

                    idx_range = np.array([-np.floor((ROI_angle_width) / 0.18), np.floor((ROI_angle_width) / 0.18)])

                    idx = np.array(center_idx + idx_range, dtype=np.int64)
                    idx = np.clip(idx, 0, 1499)  # 0 미만과 1499 초과인 값 제거

                    ROI_dist.append(dist[idx[0]:idx[1]])
                    ROI_intensity.append(intensity[idx[0]:idx[1]])

                flattened_ROI_dist = []
                for sublist in ROI_dist:
                    for item in sublist:
                        flattened_ROI_dist.append(item)
                ROI_dist = np.array(flattened_ROI_dist, dtype=np.float64)
                ROI_dist = np.array(ROI_dist, dtype=np.float64)
                # ROI_intensity = [item for sublist in ROI_intensity for item in sublist]
                flattened_ROI_intensity = []
                for sublist in ROI_intensity:
                    for item in sublist:
                        flattened_ROI_intensity.append(item)
                ROI_intensity = np.array(flattened_ROI_intensity, dtype=np.float64)
                ROI_intensity = np.array(ROI_intensity, dtype=np.float64)

                idx = np.logical_or((ROI_intensity == 0), (ROI_intensity > 5000))
                idx = np.logical_or(idx, (ROI_dist == 0))
                ROI_dist = ROI_dist[~idx]
                ROI_intensity = ROI_intensity[~idx]

                # if (target_name == 'profile') or (target_name == 'semes_white'):
                # plt.figure()
                plt.scatter(ROI_dist, ROI_intensity,
                            c=input[target_name][device_angle_str]['plt_color'],
                            label=target_name,
                            alpha=0.3,)

                spot_jig_dist = np.hstack((spot_jig_dist, ROI_dist))
                spot_jig_intensity = np.hstack((spot_jig_intensity, ROI_intensity))

    dist_unique, _ = np.unique(spot_jig_dist, return_index=True)
    # minima_y = np.zeros_like(dist_unique)
    # maxima_y = np.zeros_like(dist_unique)
    # print('dist_unique:', maxima_y.shape)

    d_table = np.linspace(0, 25, 2501)
    minima_y = np.zeros_like(d_table)
    maxima_y = np.zeros_like(d_table)

    for i, ux in enumerate(dist_unique):
        # 각 unique_x에 대해 윈도우 내의 최소값 및 최대값 계산
        minima_y[i] = np.max(spot_jig_intensity[spot_jig_dist == ux])
        maxima_y[i] = 5000

    for i, ux in enumerate(d_table):
        # 조건에 맞는 인덱스 배열을 얻기 위해 mask[0] 사용
        mask = np.where(int(ux * 100.0) == np.array(dist_unique * 100.0, dtype=np.int64))[0]
        if mask.size > 0:
            # 조건에 맞는 값 중 첫번째 값을 선택
            current_dist = dist_unique[mask][0]
            filtered = spot_jig_intensity[spot_jig_dist == current_dist]
            if filtered.size > 0:
                minima_y[i] = np.max(filtered)
            else:
                minima_y[i] = 0
        else:
            minima_y[i] = 0
        maxima_y[i] = 5000

    # plt.figure(2)
    # plt.plot(d_table, minima_y, label='min1')
    # plt.plot(d_table, maxima_y, label='max1')
    minima_y = median_filter(minima_y, 5)
    # plt.plot(dist_unique, minima_y, label='min_1.median_filter')
    # plt.plot(dist_unique, maxima_y, label='max_1.median_filter')
    minima_y = maximum_filter(minima_y, 8)
    # plt.plot(dist_unique, minima_y, label='min_2.min_filter')
    # plt.plot(dist_unique, maxima_y, label='max_2.max_filter')
    minima_y = gaussian_filter(minima_y, sigma=1)
    # plt.plot(d_table, minima_y, label='min_3.gaussian_filter')
    # plt.plot(d_table, maxima_y, label='max_3.gaussian_filter')

    intensity_min = minima_y + 15  # 최적화 필요
    intensity_max = maxima_y

    # Cubic Spline 보간을 통한 min/max model 획득
    minima_model = CubicSpline(d_table, intensity_min)
    maxima_model = CubicSpline(d_table, intensity_max)
    min_table = minima_model(d_table)
    max_table = maxima_model(d_table)

    close_idx = d_table < 0.15
    min_table[close_idx] = 0
    # plt.plot(d_table, min_table, label='min3')
    # plt.plot(d_table, max_table, label='max3')

    far_idx = d_table > 1.13
    min_table[far_idx] = 0

    max_table[:] = 5000

    idx = d_table > 0.15
    min_table[idx] = gaussian_filter(min_table[idx], sigma=3)
    min_table = gaussian_filter(min_table, sigma=1)

    np.clip(min_table, 0, 5000, out=min_table)
    np.clip(max_table, 0, 5000, out=max_table)

    data = np.column_stack((min_table, max_table)) / 10
    # filename = f"./log/OHT_table/{base_filename}_OHT_filtering_table.csv"
    # np.savetxt(filename, data, delimiter=",", comments='', fmt='%d')
    output['min_table'] = np.array(min_table / 10, dtype=np.uint16)
    output['max_table'] = np.array(max_table / 10, dtype=np.uint16)

    plt.plot(d_table, output['min_table']*10, 'g-', label='lower_threshold')
    plt.plot(d_table, output['max_table']*10, 'm-', label='upper_threshold')
    plt.xlabel('Distance (m)')
    plt.ylabel('Intensity (0.1ns)')
    plt.title('Spot Jig LUT Generation')

    # 중복된 레전드 항목을 제거하는 방법
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='black')
    plt.minorticks_on()
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    # plt.show()
    plt.xlim(0, 1)
    plt.ylim(0, 100)
    plt.savefig(f"{parameters['log_path']}/{input['GL_serial']}_{input['test_time']}_1m.png", dpi=300)
    plt.xlim(0, 5)
    plt.savefig(f"{parameters['log_path']}/{input['GL_serial']}_{input['test_time']}_5m.png", dpi=300)
    plt.show()

    output['data'] = data

    return output


def run(input: dict, parameters: dict) -> dict:
    stage_etel = input['stage_etel']

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, 90.0, 30.0)  # 재귀반사판 설정
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
        time.sleep(0.2)

    import tx_level_test
    tx_level_test_parameter = {
        "scan_angles": ['0.0'],
        "OBS_target_angle": 90.0,  # retro target angle on ETEL stage
        "OHT_target_angle": 90.0,  # 임시 테스트 용
    }
    tx_level_rawdata, tx_level_output = tx_level_test.run(input, tx_level_test_parameter)
    tx_level = tx_level_output[f'{tx_level_test_parameter["scan_angles"][0]}']['tx_level_in_deg']
    input['dpin'].move_to_angle(tx_level)
    print('tx_level:', tx_level)

    default_parameters.update(parameters)

    raw_data = data_acquisition(input, default_parameters)
    util_yy.save_pickle_to_zip(
        data=raw_data,
        path=default_parameters['log_path'],
        filename=f"{raw_data['GL_serial']}{raw_data['test_time']}_raw_data"
        )

    result = analysis(raw_data, default_parameters)
    util_yy.save_pickle_to_zip(
        data=result,
        path=default_parameters['log_path'],
        filename=f"{raw_data['GL_serial']}{raw_data['test_time']}_result"
        )

    np.savetxt(
        f"{default_parameters['log_path']}/{raw_data['GL_serial']}{raw_data['test_time']}_OBS_filtering_table.csv",
        result['data'],
        delimiter=",",
        comments='',
        fmt='%d'
        )

    return raw_data, result


def unittest():
    stage_etel = py_stage_etel.stage_etel()

    # GL connect
    GL5_core = pysoslab_core.core()
    GL5_user = pysoslab_user.user()
    GL5_area = pysoslab_area.area()
    GL5_developer = pysoslab_developer.developer()
    # GL5_core.connectSerial(SERIAL_NAME, SERIAL_BAUDRATE)
    GL5_core.connectUDP(
        default_parameters["UDP_SENSOR_IP"],
        default_parameters["UDP_SENSOR_PORT"],
        default_parameters["UDP_PC_IP"],
        default_parameters["UDP_PC_PORT"]
        )

    input = {
        'stage_etel': stage_etel,
        'GL5_core': GL5_core,
        'GL5_user': GL5_user,
        'GL5_developer': GL5_developer,
        'GL5_area': GL5_area
    }

    dpin = DPIN()
    dpin.connect("10.110.1.201", 184)
    dpin.searching_home()

    input['dpin'] = dpin

    # ETEL stage connect
    status = stage_etel.connect(default_parameters["etel_stage_IP_addr"], 3)
    if status:
        pass
    else:
        raise Exception('ETEL stage initialing FAIL')

    time.sleep(0.5)
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE)
    print('ROTARY_DEVICE home search done')
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET)
    print('LINEAR_TARGET home search done')
    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET)
    print('ROTARY_TARGET home search done')

    stage_etel.setOffset(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, default_parameters["LINEAR_STAGE_OFFSET"]
    )
    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)

    raw_data, result = run(input, default_parameters)


def analysis_test():
    raw_data = util_yy.load_pickle_from_zip(
        zip_path="H:/gui_test/log/spot_jig_lut_gen/G5091W2258042__2025.11.18_15.26.07_raw_data.zip"
        )
    result = analysis(raw_data, default_parameters)
    util_yy.save_pickle_to_zip(
        data=result,
        path=default_parameters['log_path'],
        filename=f"{raw_data['GL_serial']}_{raw_data['test_time']}_result"
        )

    np.savetxt(
        f"{default_parameters['log_path']}/{raw_data['GL_serial']}_{raw_data['test_time']}_OBS_filtering_table.csv",
        result['data'],
        delimiter=",",
        comments='',
        fmt='%d'
        )


if __name__ == "__main__":
    unittest()
    # analysis_test()
