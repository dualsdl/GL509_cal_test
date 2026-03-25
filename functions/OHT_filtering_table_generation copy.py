#!/usr/bin/env python3
#-*- coding : utf-8 -*-

import numpy as np
import time
from datetime import datetime
import zipfile

import matplotlib as mpl
# mpl.use("TkAgg")  # 예: TkAgg 백엔드 사용
mpl.use("Agg")  # Non-interactive backend 사용
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
# Interactive mode 끄기
mpl.rcParams['interactive'] = False

try:
    from stage_lib import ETEL
    import pysoslab_etel_stage as py_stage_etel
    import pysoslab_core
    import pysoslab_user
    import pysoslab_developer
except ImportError:
    pass

import matplotlib.pyplot as plt
# Interactive mode 끄기
plt.ioff()
import pickle
from sklearn.linear_model import LinearRegression

from scipy.ndimage import minimum_filter, maximum_filter, median_filter
from scipy.ndimage import gaussian_filter
from scipy.interpolate import CubicSpline
try:
    # 패키지로 실행될 때
    from . import util_yy
except ImportError:
    # 스크립트 단독 실행 시 부모 디렉토리를 경로에 추가하여 절대 임포트로 폴백
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from functions import util_yy


# #############  parameter start ###############
default_params = {
    'SERIAL_NAME': "COM4",
    'SERIAL_BAUDRATE': 921600,  # 921600, 115200
    'UDP_SENSOR_IP': "10.110.1.2",
    'UDP_SENSOR_PORT': 2000,
    'UDP_PC_IP': "10.110.1.3", 
    'UDP_PC_PORT': 3000,

    'etel_stage_IP_addr': "10.110.1.200",
    'device_rotation_speed': 30.0,
    'LINEAR_STAGE_OFFSET': -44,

    'ROI_width': 0.07,
    'EXTRAPOLATION_POINTS': 150,  # 경사를 추정할 때 사용할 마지막 데이터 포인트의 개수
    'measurement_cond': {
        'retro0': {
            'target_angle': 0.0,
            'dist_offset': 0.0,
            'measurements': {
                # dist[0]은 초기위치(항상 5000.0)로 사용
                # -130.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                -90.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                # -45.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                0.0: {'dist': [5000.0, 1000.0, 50.0], 'moving_speed': [400.0, 100.0]},
                # 45.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                # 90.0: {'dist': [5000.0, 1000.0, 120.0], 'moving_speed': [400.0, 100.0]},
                # 130.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]}
            },
            'plt_color': 'royalblue'
        },
        'retro42': {
            'target_angle': -90,
            'dist_offset': 131.0,
            'measurements': {
                # -130.0: {'dist': [5000.0, 1000.0, 130.0], 'moving_speed': [400.0, 100.0]},
                -90.0: {'dist': [5000.0, 1000.0, 110.0], 'moving_speed': [400.0, 100.0]},
                # -45.0: {'dist': [5000.0, 1000.0, 120.0], 'moving_speed': [400.0, 100.0]},
                0.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                # 45.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                # 90.0: {'dist': [5000.0, 1000.0, 130.0], 'moving_speed': [400.0, 100.0]},
                # 130.0: {'dist': [5000.0, 1000.0, 140.0], 'moving_speed': [400.0, 100.0]}
            },
            'plt_color': 'cornflowerblue'
        },
        'profile': {
            'target_angle': 180.0,
            'dist_offset': 80.0,
            'measurements': {
                # -130.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                -90.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                # -45.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                0.0: {'dist': [5000.0, 1000.0, 50.0], 'moving_speed': [400.0, 100.0]},
                # 45.0: {'dist': [1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                # 90.0: {'dist': [1000.0, 120.0], 'moving_speed': [400.0, 100.0]},
                # 130.0: {'dist': [1000.0, 100.0], 'moving_speed': [400.0, 100.0]}
            },
            'plt_color': 'darkviolet'
        },
        'semes_white': {
            'target_angle': 90.0,
            'dist_offset': 0.0,
            'measurements': {
                # -130.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                -90.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                # -45.0: {'dist': [5000.0, 1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                0.0: {'dist': [5000.0, 1000.0, 50.0], 'moving_speed': [400.0, 100.0]},
                # 45.0: {'dist': [1000.0, 100.0], 'moving_speed': [400.0, 100.0]},
                # 90.0: {'dist': [1000.0, 120.0], 'moving_speed': [400.0, 100.0]},
                # 130.0: {'dist': [1000.0, 100.0], 'moving_speed': [400.0, 100.0]}
            },
            'plt_color': 'silver'
        }
    }
}
# #############  parameter end ###############


# 데이터가 없는 구간을 점진적으로 떨어지게 하기
def extrapolate_trend(x, y, start_idx, EXTRAPOLATION_POINTS):
    extrapolated_y = np.copy(y)
    # 마지막 데이터 포인트의 개수를 사용하여 선형 회귀를 적용하여 경사 추정
    x_for_slope = x[start_idx - EXTRAPOLATION_POINTS:start_idx].reshape(-1, 1)
    y_for_slope = y[start_idx - EXTRAPOLATION_POINTS:start_idx]

    model = LinearRegression()
    model.fit(x_for_slope, y_for_slope)

    trend_slope = model.coef_[0]

    for i in range(start_idx, len(x)):
        extrapolated_y[i] = extrapolated_y[i-1] + trend_slope * (x[i] - x[i-1])

    return extrapolated_y


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

    success, GL_serial = GL5_user.getSerialNum(GL5_core)
    if success:
        print(f"Serial_num = {GL_serial}")
    else:
        print("Unable to get a serial number")
    output['GL_serial'] = GL_serial
        
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
    
    output['GL_setting'] = dict()
    success, back_reflector_pulse_width_target = (
        input['GL5_developer'].getBackReflectorPulseWidthTarget(input["GL5_core"])
    )
    if success:
        print(f"back_reflector_pulse_width_target = {back_reflector_pulse_width_target}")
    else:
        print("Unable to get the back_reflector_pulse_width_target")
    output['GL_setting']['back_reflector_pulse_width_target'] = back_reflector_pulse_width_target

    success, pd_high_voltage = input['GL5_developer'].getPDHighVoltage(input["GL5_core"])
    if success:
        print(f"pd_high_voltage = {pd_high_voltage}")
    else:
        print("Unable to get the pd_high_voltage")
    output['GL_setting']['pd_high_voltage'] = pd_high_voltage

    success, ld_high_voltage = input['GL5_developer'].getLDHighVoltage(input["GL5_core"])
    if success:
        print(f"ld_high_voltage = {ld_high_voltage}")
    else:
        print("Unable to get the ld_high_voltage")
    output['GL_setting']['ld_high_voltage'] = ld_high_voltage

    # LiDAR streaming start
    success = GL5_user.setStreamEnable(GL5_core, True)
    if success:
        print("Successfully enable data streaming")
    else:
        print("Failed to enable data streaming")

    for target_name, target_cond in parameter['measurement_cond'].items():
        output[target_name] = dict()
        # print(f'{target_name}_data acquisition start')
                
        # 초기 위치로 이동
        stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
            time.sleep(0.2)

        stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, target_cond['target_angle'], 30.0)
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
            time.sleep(0.2)

        for device_angle, params in target_cond['measurements'].items():
            # output[target_name][f'{device_angle:.1f}'] = dict()
            output[target_name][f'{device_angle}'] = dict()
            
            # 초기 위치로 이동
            dist_list = params['dist']
            speed_list = params['moving_speed']

            # dist_list[0]은 초기위치 (항상 5000.0)
            stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, dist_list[0], 400.0)
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                time.sleep(0.2)

            stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, float(device_angle), parameter['device_rotation_speed'])
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
                time.sleep(0.2)

            print(f'{target_name}_GL{device_angle}_data acquisition start')

            logging_datas = []
            # 거리 이동은 dist_list[i+1]로 수행 (dist_list[0]은 초기위치)
            move_cnt = min(len(speed_list), len(dist_list) - 1)
            for i in range(move_cnt):
                # 현재 위치로 이동
                stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 
                                  dist_list[i + 1] + target_cond['dist_offset'], 
                                  speed_list[i])
                while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                    success, frame_data = GL5_user.getLidarData(GL5_core, False)
                    if not success:
                        print("Failed to get a LiDAR data")
                    else:
                        logging_datas.append(frame_data)
                    
                    # plt.figure(1, figsize=(8, 6))
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
        
    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 0.0, parameter['device_rotation_speed'])
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)

    return output


def analysis(input: dict, params: dict) -> dict:
    output = dict()
    output['GL_setting'] = input['GL_setting']
    output['test_time'] = input['test_time']
    output['GL_serial'] = input['GL_serial']
    output['GL_setting'] = input['GL_setting']
    
    # 기존 figure가 있으면 클리어하고 새로 생성
    plt.clf()
    fig = plt.figure(figsize=(16, 8))

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

                    # Select the relevant slice around center_idx
                    selected_slice = np.array(dist[center_idx-3:center_idx+3])

                    # Exclude zeros and NaN values from the calculation
                    filtered_slice = selected_slice[(selected_slice != 0) & (~np.isnan(selected_slice))]

                    # Calculate the mean excluding zeros and NaN values
                    # 빈 배열 체크 추가
                    if len(filtered_slice) == 0:
                        break
                    test_dist = np.nanmean(filtered_slice)
                    if np.isnan(test_dist) or test_dist == 0:
                        break
                    ROI_angle_width = np.degrees(np.arctan(params['ROI_width'] / 2 / test_dist))
                    temp = 0

                    idx_range = np.array([-np.floor((ROI_angle_width) / 0.18), np.floor((ROI_angle_width) / 0.18)])
                    # NaN/Inf 체크 후 유효한 값만 사용
                    idx_range = np.nan_to_num(idx_range, nan=0.0, posinf=0.0, neginf=0.0)

                    idx = center_idx + idx_range
                    # NaN/Inf 체크 후 int64로 변환
                    idx = np.nan_to_num(idx, nan=0.0, posinf=0.0, neginf=0.0)
                    idx = np.array(idx, dtype=np.int64)
                    idx = np.clip(idx, 0, 1499)  # 0 미만과 1499 초과인 값 제거

                    dist_slice = np.array(dist[idx[0]:idx[1]])
                    intensity_slice = np.array(intensity[idx[0]:idx[1]])
                    filtered_idx = np.abs(test_dist - dist_slice) < 0.15
                    dist_slice = dist_slice[filtered_idx]
                    intensity_slice = intensity_slice[filtered_idx]

                    ROI_dist.append(dist_slice)
                    ROI_intensity.append(intensity_slice)

                ROI_dist = [item for sublist in ROI_dist for item in sublist]
                ROI_dist = np.array(ROI_dist, dtype=np.float64)
                ROI_intensity = [item for sublist in ROI_intensity for item in sublist]
                ROI_intensity = np.array(ROI_intensity, dtype=np.float64)

                idx = np.logical_or((ROI_intensity == 0), (ROI_intensity > 5000))
                idx = np.logical_or(idx, (ROI_dist == 0))
                ROI_dist = ROI_dist[~idx]
                ROI_intensity = ROI_intensity[~idx]

                # if (target_name == 'profile') or (target_name == 'semes_white'):
                # plt.figure()
                if target_name[:5] == "retro":
                    zorder_val = 2  # retro 데이터는 위에 표시
                else:
                    zorder_val = 1  # 다른 데이터는 아래에 표시
                    
                plt.scatter(ROI_dist, ROI_intensity, 
                            c=input[target_name][device_angle_str]['plt_color'],
                            label=target_name,
                            alpha=0.3,
                            zorder=zorder_val)

                if target_name[:5] == "retro":  # 뒤에서 LUT 테이블 만들때 사용
                    retro_dist = np.hstack((retro_dist, ROI_dist))
                    retro_intensity = np.hstack((retro_intensity, ROI_intensity))

    dist_unique, indices = np.unique(retro_dist, return_index=True)
    minima_y = np.zeros_like(dist_unique)
    maxima_y = np.zeros_like(dist_unique)

    for i, ux in enumerate(dist_unique):
        # 각 unique_x에 대해 윈도우 내의 최소값 및 최대값 계산
        minima_y[i] = np.min(retro_intensity[retro_dist == ux])
        maxima_y[i] = np.max(retro_intensity[retro_dist == ux])

    # plt.figure(2)
    # plt.plot(dist_unique, minima_y, label='min1')
    # plt.plot(dist_unique, maxima_y, label='max1')
    minima_y = median_filter(minima_y, 7)
    maxima_y = median_filter(maxima_y, 5)
    # plt.plot(dist_unique, minima_y, label='min_1.median_filter')
    # plt.plot(dist_unique, maxima_y, label='max_1.median_filter')
    minima_y = minimum_filter(minima_y, 15)
    idx = dist_unique > 0.5
    minima_y[idx] = minimum_filter(minima_y[idx], 51)
    maxima_y = maximum_filter(maxima_y, 51)
    # plt.plot(dist_unique, minima_y, label='min_2.min_filter')
    # plt.plot(dist_unique, maxima_y, label='max_2.max_filter')
    minima_y = gaussian_filter(minima_y, sigma=20)
    maxima_y = gaussian_filter(maxima_y, sigma=20)
    # plt.plot(dist_unique, minima_y, label='min_3.gaussian_filter')
    # plt.plot(dist_unique, maxima_y, label='max_3.gaussian_filter')

    close_idx = dist_unique < 0.13  # 근거리 데이터에 대해 오감지발생되더라도 재귀반사판 인식을 우선적으로
    try:
        minima_y[close_idx] = np.nanmin(minima_y[close_idx])
    except:
        pass
    close_idx = dist_unique < 0.15  # 근거리 데이터에 대해 오감지발생되더라도 재귀반사판 인식을 우선적으로
    try:
        maxima_y[close_idx] = np.nanmax(maxima_y[close_idx])
    except:
        pass

    idx_far = dist_unique > 3
    maxima_y[idx_far] = maximum_filter(maxima_y[idx_far], 200)
    # plt.plot(dist_unique, minima_y, label='min_pre_process')
    # plt.plot(dist_unique, maxima_y, label='max_pre_process')

    intensity_max = maxima_y
    intensity_min = minima_y
    intensity_max = intensity_max + 10
    
    # Cubic Spline 보간을 통한 min/max model 획득
    minima_model = CubicSpline(dist_unique, intensity_min)
    maxima_model = CubicSpline(dist_unique, intensity_max)

    # 데이터 등간격 보간
    d_table = np.linspace(0, 25, 2501)
    min_table = minima_model(d_table)
    max_table = maxima_model(d_table)

    close_idx = d_table < 0.15
    max_table[close_idx] = np.nanmax(max_table[close_idx])    
    close_idx = d_table < 0.1
    min_table[close_idx] = np.nanmin(min_table[close_idx])
    # min_table[close_idx] = min_table[close_idx] - 25
    min_table[close_idx] = min_table[close_idx] + 10
    # plt.plot(d_table, min_table, label='min3')
    # plt.plot(d_table, max_table, label='max3')

    # 데이터가 있는 마지막 인덱스 찾기
    last_data_idx = np.searchsorted(d_table, dist_unique.max(), side='right') - 1
    
    # 데이터 없는 구간에 대해 점진적으로 떨어지는 경향 추가
    min_table = extrapolate_trend(d_table, min_table, last_data_idx, params['EXTRAPOLATION_POINTS'])
    max_table = extrapolate_trend(d_table, max_table, last_data_idx, params['EXTRAPOLATION_POINTS'])

    # min_table = min_table - 30

    idx = d_table > 0.12
    min_table[idx] = min_table[idx] - 10

    idx = d_table > 0.15
    max_table[idx] = max_table[idx] + 30
    min_table[idx] = min_table[idx] - 20

    # idx = d_table > 0.15
    # idx = np.logical_and(idx, d_table < 0.22)
    # # min_table[idx] = min_table[idx] + 80
    # min_table[idx] = min_table[idx] - 00

    # idx = d_table > 0.16
    # idx = np.logical_and(idx, d_table < 0.18)
    # min_table[idx] = min_table[idx] - 10

    idx = d_table > 0.17
    idx = np.logical_and(idx, d_table < 0.3)
    # min_table[idx] = min_table[idx] - 30

    idx = d_table > 0.22
    max_table[idx] = max_table[idx] + 80
    min_table[idx] = min_table[idx] - 70

    idx = d_table > 0.3
    min_table[idx] = min_table[idx] - 70
    min_table[idx] = min_table[idx] - 40

    idx = d_table > 0.5
    max_table[idx] = max_table[idx] + 150
    min_table[idx] = min_table[idx] - 70

    idx = d_table > 0.8
    min_table[idx] = min_table[idx] - 40
    idx = d_table > 1.1
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 1.3
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 1.5
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 1.7
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 2
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 2.2
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 2.4
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 2.6
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 2.8
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 3.2
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 3.6
    min_table[idx] = min_table[idx] + 10
    idx = d_table > 4
    min_table[idx] = min_table[idx] - 60
    idx = d_table > 4.5
    min_table[idx] = min_table[idx] - 20
    idx = d_table > 5
    min_table[idx] = min_table[idx] - 20
    
    idx = d_table > 4
    idx = np.logical_and(idx, d_table < 4.5)
    far_dist_min_val = np.min(min_table[idx])
    idx = d_table > 4.5
    max_table[idx] = 5000  # UPPER limit 해제
    min_table[idx] = far_dist_min_val  # Lower limit 해제

    intensity_min = 70
    idx = d_table > 1.0
    idx = np.logical_and(idx, min_table < intensity_min)
    min_table[idx] = intensity_min

    idx = d_table > 6.0
    min_table[idx] = intensity_min

    idx = d_table > 7.0
    min_table[idx] = intensity_min -10

    idx = d_table > 8.0
    min_table[idx] = intensity_min -20
    # plt.plot(d_table, min_table, 'r-', label='lower_threshold_mod')
    # plt.show()
    max_table = gaussian_filter(max_table, sigma=5)
    idx = d_table > 5
    min_table[idx] = gaussian_filter(min_table[idx], sigma=60)
    idx = d_table > 1
    min_table[idx] = gaussian_filter(min_table[idx], sigma=30)
    idx = d_table > 0.15
    min_table[idx] = gaussian_filter(min_table[idx], sigma=3)
    min_table = gaussian_filter(min_table, sigma=1)

    min_table = np.clip(min_table, 0, 5000)
    max_table = np.clip(max_table, 0, 5000)

    idx = d_table < 0.15
    max_table[idx] = 5000  # UPPER limit 해제
    
    plt.plot(d_table, min_table, 'g-', label='lower_threshold')
    plt.plot(d_table, max_table, 'm-', label='upper_threshold')
    # 중복된 레전드 항목을 제거하는 방법
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='black')
    plt.minorticks_on()
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')
    # plt.show()
    plt.xlabel('Distance (m)')
    plt.ylabel('Intensity (0.1ns)')
    plt.title('OHT Filtering Table')
    # 이미지를 array로 메모리에 저장
    fig = plt.gcf()
    # Agg backend를 직접 사용하여 tkinter 오류 방지
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    # 기존 canvas가 있으면 제거하고 새로 생성
    if hasattr(fig, '_cachedRenderer'):
        delattr(fig, '_cachedRenderer')
    canvas = FigureCanvasAgg(fig)
    
    # 1m 이미지
    plt.xlim(0,1)
    plt.ylim(0,1200)
    canvas.draw()
    img_1m = np.array(canvas.renderer.buffer_rgba())
    output['img_1m'] = img_1m[:,:,:3]  # RGB만 추출
    
    # 0.5m 이미지 추가
    plt.xlim(0,0.5)
    plt.ylim(0,1200)
    canvas.draw()
    img_05m = np.array(canvas.renderer.buffer_rgba())
    output['img_0.5m'] = img_05m[:,:,:3]  # RGB만 추출
    
    # 9m 이미지 추가
    plt.xlim(0,9)
    plt.ylim(0,1200)
    canvas.draw()
    img_5m = np.array(canvas.renderer.buffer_rgba())
    output['img_5m'] = img_5m[:,:,:3]  # RGB만 추출
    
    # plt.xlim(0,12)
    # plt.ylim(0,2500)
    # plt.show()
    plt.clf()

    data = np.column_stack((min_table, max_table)) / 10
    # filename = f"./log/OHT_table/{base_filename}_OHT_filtering_table.csv"
    # np.savetxt(filename, data, delimiter=",", comments='', fmt='%d')
    output['min_table'] = min_table[1::] / 10
    output['max_table'] = max_table[1::] / 10
    output['oht_table'] = data[1:, :]

    return output


def run(input: dict, params: dict = None) -> dict:
    if params is None:
        params = {}
    
    default_params.update(params)

    data = data_acquisition(input, default_params)

    result = analysis(data, default_params)

    return data, result


def unittest(params: dict = default_params):
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
    GL5_developer = pysoslab_developer.developer()
    # GL5_core.connectSerial(SERIAL_NAME, SERIAL_BAUDRATE)
    GL5_core.connectUDP(params['UDP_SENSOR_IP'], params['UDP_SENSOR_PORT'], params['UDP_PC_IP'], params['UDP_PC_PORT'])

    input = dict()
    input['stage_etel'] = stage_etel
    input['GL5_core'] = GL5_core
    input['GL5_user'] = GL5_user
    input['GL5_developer'] = GL5_developer

    stage_etel.setOffset(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, params['LINEAR_STAGE_OFFSET']
    )

    data, result = run(input, params)
    
    test_name = 'OHT_filtering_table'
    path = f"./log/{test_name}"
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(data, path, filename)

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(result, path, filename)


    # 1m, 5m 이미지 저장
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_1m.png'
    plt.imsave(f'{path}/{filename}', result['img_1m'])
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_5m.png'
    plt.imsave(f'{path}/{filename}', result['img_5m'])
    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_0.5m.png'
    plt.imsave(f'{path}/{filename}', result['img_0.5m'])

    filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}.csv'
    np.savetxt(f'{path}/{filename}', result['oht_table'], delimiter=",", comments='', fmt='%d')

    success, min_pulse_width_lut, max_pulse_width_lut = (
        GL5_developer.getMinMaxPulseWidthLUTFromFile(f'{path}/{filename}')
    )
    if success:
        success = GL5_developer.setMinMaxPulseWidthLUTToSensor(
            GL5_core, min_pulse_width_lut, max_pulse_width_lut
        )
        if success:
            print("Successfully set the min/max_pulse_width_lut to sensor")
        else:
            print("Unable to set the min/max_pulse_width_lut to sensor")
    else:
        print("Unable to load the min/max_pulse_width_lut from file")

    GL5_core.disconnect()


def analysis_test():
    from PySide6.QtWidgets import QFileDialog, QApplication
    import sys

    # QApplication 인스턴스 생성
    app = QApplication(sys.argv)

    fname, _ = QFileDialog.getOpenFileName(
        None,                          # 부모 위젯 없음
        "Beam Size Result 파일 열기",                     # 대화상자 제목
        "./log/OHT_filtering_table",             # 초기 디렉토리
        "ZIP 파일 (*.zip);;모든 파일 (*)"  # 파일 필터 (zip 우선)
    )
    loaded_data = util_yy.load_pickle_from_zip(fname)
            
    outputs = analysis(loaded_data, default_params)    
    test_name = 'OHT_filtering_table'
    path = f"./log/{test_name}"
    filename = f"{loaded_data['GL_serial']}_" + f'{loaded_data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
    util_yy.save_pickle_to_zip(outputs, path, filename)

    # 1m, 5m 이미지 저장
    filename = f"{loaded_data['GL_serial']}_" + f'{loaded_data["test_time"]}' + f'{test_name}_1m.png'
    plt.imsave(f'{path}/{filename}', outputs['img_1m'])
    filename = f"{loaded_data['GL_serial']}_" + f'{loaded_data["test_time"]}' + f'{test_name}_5m.png'
    plt.imsave(f'{path}/{filename}', outputs['img_5m'])
    filename = f"{loaded_data['GL_serial']}_" + f'{loaded_data["test_time"]}' + f'{test_name}_0.5m.png'
    plt.imsave(f'{path}/{filename}', outputs['img_0.5m'])

    filename = f"{loaded_data['GL_serial']}_" + f'{loaded_data["test_time"]}' + f'{test_name}.csv'
    np.savetxt(f'{path}/{filename}', outputs['oht_table'], delimiter=",", comments='', fmt='%d')
    
    # # GL connect
    # GL5_core = pysoslab_core.core()
    # GL5_user = pysoslab_user.user()
    # GL5_developer = pysoslab_developer.developer()
    # # GL5_core.connectSerial(SERIAL_NAME, SERIAL_BAUDRATE)
    # GL5_core.connectUDP(default_params['UDP_SENSOR_IP'], 
    #                     default_params['UDP_SENSOR_PORT'], 
    #                     default_params['UDP_PC_IP'], 
    #                     default_params['UDP_PC_PORT'])

    # success, min_pulse_width_lut, max_pulse_width_lut = (
    #     GL5_developer.getMinMaxPulseWidthLUTFromFile(f'{path}/{filename}')
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
    
    # GL5_core.disconnect()
    

if __name__ == "__main__":
    # unittest()
    analysis_test()
    print('done')
