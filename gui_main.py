import flet as ft
from functions.beam_size import default_parameters as beam_size_default_parameters
from functions.beam_size import run as beam_size_run
from functions.gl507_walkerror_auto import default_params as walk_error_default_parameters
from functions.gl507_walkerror_auto import run as walk_error_run
from functions.gl507_walkerror import run as walk_error_analysis
from functions.tx_level_test import default_parameters as tx_level_default_parameters
from functions.tx_level_test import run as tx_level_run
from functions.home_position import default_params as home_position_default_parameters
from functions.home_position import run as home_position_run
from functions.distance_offset_and_test_v2 import default_parameters as distance_performance_default_parameters
from functions.distance_offset_and_test_v2 import run as distance_performance_run
from functions.OHT_filtering_table_generation import default_params as OHT_filtering_table_generation_default_parameters
from functions.OHT_filtering_table_generation import run as OHT_filtering_table_generation_run
from functions.OHT_filtering_validation import default_parameter as OHT_filtering_validation_default_parameter
from functions.OHT_filtering_validation import run as OHT_filtering_validation_run
from functions.rear_cover_test import default_params as rear_cover_detection_default_parameters
from functions.rear_cover_test import run as rear_cover_detection_run
from functions.max_dist import default_params as max_distance_default_parameters
from functions.max_dist import run as max_distance_run


import json
import os
import time
import cv2
import threading
import numpy as np
# --- 장비 Connect/Disconnect 함수 템플릿 ---
import pysoslab_etel_stage as py_stage_etel
import pysoslab_core
import pysoslab_user
import pysoslab_developer
from stage_lib import DPIN, ETEL
from pypylon import pylon
import pysoslab_area
from functions.KDC101 import KDC101
from functions.util_yy import parse_dict_from_string
from functions import util_yy
import matplotlib.pyplot as plt

# 연결 정보 파라미터
connection_parameters = {
    'UDP_SENSOR_IP': beam_size_default_parameters['UDP_SENSOR_IP'],
    'UDP_SENSOR_PORT': beam_size_default_parameters['UDP_SENSOR_PORT'],
    'UDP_PC_IP': beam_size_default_parameters['UDP_PC_IP'],
    'UDP_PC_PORT': beam_size_default_parameters['UDP_PC_PORT'],
    'etel_stage_IP_addr': beam_size_default_parameters['etel_stage_IP_addr'],
    'DPIN_gonio_IP_addr': beam_size_default_parameters['DPIN_gonio_IP_addr'],
    'DPIN_gonio_port': beam_size_default_parameters['DPIN_gonio_port'],
    'etel_stage_offset': -43  # ETEL 스테이지 오프셋 기본값 추가
}

# 검사별 파라미터
beam_size_parameters = {
    'camera_FPS': beam_size_default_parameters['camera_FPS'],
    'camera_acqusition_num': beam_size_default_parameters['camera_acqusition_num'],
    'OHT_camera_exposure': beam_size_default_parameters['OHT_camera_exposure'],
    'OBS_camera_exposure': beam_size_default_parameters['OBS_camera_exposure'],
    'OHT_target_angle': beam_size_default_parameters['OHT_target_angle'],
    'OBS_target_angle': beam_size_default_parameters['OBS_target_angle'],
    'test_dist': beam_size_default_parameters['test_dist'],
    'beamsize_pass_criteria': beam_size_default_parameters['beamsize_pass_criteria'],
    'threshold_std': beam_size_default_parameters['threshold_std'],
    'image_ROI_x': beam_size_default_parameters['image_ROI_x'],
    'image_ROI_y': beam_size_default_parameters['image_ROI_y'],
    'origin': beam_size_default_parameters['origin'],
    'px2mm_conversion_gain': beam_size_default_parameters['px2mm_conversion_gain']
}

walk_error_parameters = {
    'walk_error_stage_dist': walk_error_default_parameters['walk_error_stage_dist'],
    'speed_conditions': walk_error_default_parameters['speed_conditions'],
    'OHT_ld_high_voltage': walk_error_default_parameters['OHT_ld_high_voltage'],
    'OHT_pd_high_voltage': walk_error_default_parameters['OHT_pd_high_voltage'],
    'OHT_BR_intensity': walk_error_default_parameters['OHT_BR_intensity'],
    'OBS_ld_high_voltage': walk_error_default_parameters['OBS_ld_high_voltage'],
    'OBS_pd_high_voltage': walk_error_default_parameters['OBS_pd_high_voltage'],
    'OBS_BR_intensity': walk_error_default_parameters['OBS_BR_intensity']
}

# 수평도 검사 파라미터 추가
tx_level_parameters = {
    'LD_HV': tx_level_default_parameters['LD_HV'],
    'OBS_camera_exposure': tx_level_default_parameters['OBS_camera_exposure'],
    'OHT_camera_exposure': tx_level_default_parameters['OHT_camera_exposure'],
    'camera_FPS': tx_level_default_parameters['camera_FPS'],
    'camera_acqusition_num': tx_level_default_parameters['camera_acqusition_num'],
    'OBS_target_angle': tx_level_default_parameters['OBS_target_angle'],
    'OHT_target_angle': tx_level_default_parameters['OHT_target_angle'],
    'linear_distance': tx_level_default_parameters['linear_distance'],
    'scan_angles': tx_level_default_parameters['scan_angles'],
    'image_ROI_y': tx_level_default_parameters['image_ROI_y'],
    'image_ROI_x': tx_level_default_parameters['image_ROI_x'],
    'binary_threshold': tx_level_default_parameters['binary_threshold'],
    'tx_level_origin_px': tx_level_default_parameters['tx_level_origin_px'],
    'px2mm_conversion_gain': tx_level_default_parameters['px2mm_conversion_gain'],
    'pass_criteria': tx_level_default_parameters['pass_criteria']
}

home_position_parameters = {
    'OHT_target_angle': home_position_default_parameters['OHT_target_angle'],
    'OBS_target_angle': home_position_default_parameters['OBS_target_angle'],
    'device_rotation_speed': home_position_default_parameters['device_rotation_speed'],
    'test_distance': home_position_default_parameters['test_distance'],
    'device_angle': home_position_default_parameters['device_angle'],
    'logging_frame_num': home_position_default_parameters['logging_frame_num'],
    'frame_size': home_position_default_parameters['frame_size'],
    'home_position_pass_criteria': home_position_default_parameters['home_position_pass_criteria']
}

distance_performance_parameters = {
    'OHT_target_angle': distance_performance_default_parameters['OHT_target_angle'],
    'OBS_target_angle': distance_performance_default_parameters['OBS_target_angle'],
    'device_rotation_speed': distance_performance_default_parameters['device_rotation_speed'],
    'LINEAR_STAGE_OFFSET': distance_performance_default_parameters['LINEAR_STAGE_OFFSET'],
    'oht_cal_dist_points': distance_performance_default_parameters['oht_cal_dist_points'],
    'obs_cal_dist_points': distance_performance_default_parameters['obs_cal_dist_points'],
    'oht_test_dist_points': distance_performance_default_parameters['oht_test_dist_points'],
    'obs_test_dist_points': distance_performance_default_parameters['obs_test_dist_points'],
    'logging_frame_num': distance_performance_default_parameters['logging_frame_num'],
    'ROI_width': distance_performance_default_parameters['ROI_width'],
    'precision_pass_criteria': distance_performance_default_parameters['precision_pass_criteria'],
    'accuracy_pass_criteria': distance_performance_default_parameters['accuracy_pass_criteria']
}

OHT_filtering_table_generation_parameters = {
    'ROI_width': OHT_filtering_table_generation_default_parameters['ROI_width'],
    'EXTRAPOLATION_POINTS': OHT_filtering_table_generation_default_parameters['EXTRAPOLATION_POINTS'],
    'measurement_cond': OHT_filtering_table_generation_default_parameters['measurement_cond']
}

OHT_filtering_validation_parameters = {
    'validation_cond': OHT_filtering_validation_default_parameter['validation_cond'],
    'validation_area_path': OHT_filtering_validation_default_parameter['validation_area_path'],
    'empty_area_path': OHT_filtering_validation_default_parameter['empty_area_path']
}

rear_cover_detection_parameters = {
    'test_cond': rear_cover_detection_default_parameters['test_cond'],
    'test_area_path': rear_cover_detection_default_parameters['test_area_path'],
    'empty_area_path': rear_cover_detection_default_parameters['empty_area_path'],
    # 'speed_mmps': rear_cover_detection_default_parameters['speed_mmps'],
    'target_angle': rear_cover_detection_default_parameters['target_angle'],
    # 'device_rotation_speed': rear_cover_detection_default_parameters['device_rotation_speed'],
    # 'LINEAR_STAGE_OFFSET': rear_cover_detection_default_parameters['LINEAR_STAGE_OFFSET']
}

max_distance_parameters = {
    'test_angle': max_distance_default_parameters['test_angle'],
    'ROI_width': max_distance_default_parameters['ROI_width'],
    'logging_frame_num': max_distance_default_parameters['logging_frame_num'],
    'detection_ratio_criteria': max_distance_default_parameters['detection_ratio_criteria'],
    # 'device_rotation_speed': max_distance_default_parameters['device_rotation_speed']
}

# --- 장비 연결 객체 전역 변수 선언 ---
stage_etel = py_stage_etel.stage_etel()
GL5_core = pysoslab_core.core()
GL5_user = pysoslab_user.user()
GL5_developer = pysoslab_developer.developer()
GL5_area = pysoslab_area.area()
dpin = DPIN.DpinStageHandler()
kdc101 = None  # KDC101 스테이지 객체를 None으로 초기화
camera = None  # 카메라는 장치 연결 시점에만 초기화 필요

global devices
devices = dict()
devices['stage_etel'] = stage_etel
devices['GL5_core'] = GL5_core
devices['GL5_user'] = GL5_user
devices['GL5_developer'] = GL5_developer
devices['GL5_area'] = GL5_area
devices['dpin'] = dpin

# main 함수 시작 부분에 추가
global global_beam_size_result
global_beam_size_result = None
global global_walk_error_result  
global_walk_error_result = None
global global_tx_level_result
global_tx_level_result = None
global global_home_position_result
global_home_position_result = None
global global_distance_performance_result
global_distance_performance_result = None
global global_oht_filtering_lut_result
global_oht_filtering_lut_result = None
global global_oht_filtering_validation_result
global_oht_filtering_validation_result = None
global global_rear_cover_detection_result
global_rear_cover_detection_result = None
global global_max_distance_result
global_max_distance_result = None

def main(page: ft.Page):
    page.title = "GL-509 calibration and test"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_resizable = True
    # page.window_width = 1600
    # page.window_height = 1200
    # page.full_screen = True
    page.update()

    # 1. settings.json에서 값 읽기 시도, 없으면 기본값 사용
    loaded_connection = connection_parameters.copy()
    loaded_beam_size = beam_size_parameters.copy()
    loaded_walk_error = walk_error_parameters.copy()
    loaded_tx_level = tx_level_parameters.copy()
    loaded_home_position = home_position_parameters.copy()
    loaded_distance_performance = distance_performance_parameters.copy()
    loaded_OHT_filtering_table_generation = OHT_filtering_table_generation_parameters.copy()
    loaded_OHT_filtering_validation = OHT_filtering_validation_parameters.copy()
    loaded_rear_cover_detection = rear_cover_detection_parameters.copy()
    loaded_max_distance = max_distance_parameters.copy()

    if os.path.exists("settings.json"):
        with open("settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        # 연결
        loaded_connection['UDP_SENSOR_IP'] = data.get('connection', {}).get('UDP_SENSOR_IP', beam_size_default_parameters['UDP_SENSOR_IP'])
        loaded_connection['UDP_SENSOR_PORT'] = data.get('connection', {}).get('UDP_SENSOR_PORT', beam_size_default_parameters['UDP_SENSOR_PORT'])
        loaded_connection['UDP_PC_IP'] = data.get('connection', {}).get('UDP_PC_IP', beam_size_default_parameters['UDP_PC_IP'])
        loaded_connection['UDP_PC_PORT'] = data.get('connection', {}).get('UDP_PC_PORT', beam_size_default_parameters['UDP_PC_PORT'])
        loaded_connection['etel_stage_IP_addr'] = data.get('connection', {}).get('etel_stage_IP_addr', beam_size_default_parameters['etel_stage_IP_addr'])
        loaded_connection['DPIN_gonio_IP_addr'] = data.get('connection', {}).get('DPIN_gonio_IP_addr', beam_size_default_parameters['DPIN_gonio_IP_addr'])
        loaded_connection['DPIN_gonio_port'] = data.get('connection', {}).get('DPIN_gonio_port', beam_size_default_parameters['DPIN_gonio_port'])
        loaded_connection['etel_stage_offset'] = data.get('connection', {}).get('etel_stage_offset', -43)  # ETEL 스테이지 오프셋 로드

        # 빔 사이즈
        loaded_beam_size['camera_FPS'] = data.get('beam_size', {}).get('camera_FPS', beam_size_default_parameters['camera_FPS'])
        loaded_beam_size['camera_acqusition_num'] = data.get('beam_size', {}).get('camera_acqusition_num', beam_size_default_parameters['camera_acqusition_num'])
        loaded_beam_size['OHT_camera_exposure'] = data.get('beam_size', {}).get('OHT_camera_exposure', beam_size_default_parameters['OHT_camera_exposure'])
        loaded_beam_size['OBS_camera_exposure'] = data.get('beam_size', {}).get('OBS_camera_exposure', beam_size_default_parameters['OBS_camera_exposure'])
        loaded_beam_size['OHT_target_angle'] = data.get('beam_size', {}).get('OHT_target_angle', beam_size_default_parameters['OHT_target_angle'])
        loaded_beam_size['OBS_target_angle'] = data.get('beam_size', {}).get('OBS_target_angle', beam_size_default_parameters['OBS_target_angle'])
        loaded_beam_size['test_dist'] = data.get('beam_size', {}).get('test_dist', beam_size_default_parameters['test_dist'])
        loaded_beam_size['beamsize_pass_criteria'] = data.get('beam_size', {}).get('beamsize_pass_criteria', beam_size_default_parameters['beamsize_pass_criteria'])
        loaded_beam_size['threshold_std'] = data.get('beam_size', {}).get('threshold_std', beam_size_default_parameters['threshold_std'])

        # Walk Error LUT settings (이미 처리된 상태 유지)
        loaded_walk_error['walk_error_stage_dist'] = data.get('walk_error_lut', {}).get('walk_error_stage_dist', loaded_walk_error['walk_error_stage_dist'])
        loaded_walk_error['speed_conditions'] = data.get('walk_error_lut', {}).get('speed_conditions', loaded_walk_error['speed_conditions'])
        loaded_walk_error['OHT_ld_high_voltage'] = data.get('walk_error_lut', {}).get('OHT_ld_high_voltage', loaded_walk_error['OHT_ld_high_voltage'])
        loaded_walk_error['OHT_pd_high_voltage'] = data.get('walk_error_lut', {}).get('OHT_pd_high_voltage', loaded_walk_error['OHT_pd_high_voltage'])
        loaded_walk_error['OHT_BR_intensity'] = data.get('walk_error_lut', {}).get('OHT_BR_intensity', loaded_walk_error['OHT_BR_intensity'])
        loaded_walk_error['OBS_ld_high_voltage'] = data.get('walk_error_lut', {}).get('OBS_ld_high_voltage', loaded_walk_error['OBS_ld_high_voltage'])
        loaded_walk_error['OBS_pd_high_voltage'] = data.get('walk_error_lut', {}).get('OBS_pd_high_voltage', loaded_walk_error['OBS_pd_high_voltage'])
        loaded_walk_error['OBS_BR_intensity'] = data.get('walk_error_lut', {}).get('OBS_BR_intensity', loaded_walk_error['OBS_BR_intensity'])

        # 수평도 검사
        loaded_tx_level['LD_HV'] = data.get('tx_level', {}).get('LD_HV', loaded_tx_level['LD_HV'])
        loaded_tx_level['OBS_camera_exposure'] = data.get('tx_level', {}).get('OBS_camera_exposure', loaded_tx_level['OBS_camera_exposure'])
        loaded_tx_level['OHT_camera_exposure'] = data.get('tx_level', {}).get('OHT_camera_exposure', loaded_tx_level['OHT_camera_exposure'])
        loaded_tx_level['camera_FPS'] = data.get('tx_level', {}).get('camera_FPS', loaded_tx_level['camera_FPS'])
        loaded_tx_level['camera_acqusition_num'] = data.get('tx_level', {}).get('camera_acqusition_num', loaded_tx_level['camera_acqusition_num'])
        loaded_tx_level['OBS_target_angle'] = data.get('tx_level', {}).get('OBS_target_angle', loaded_tx_level['OBS_target_angle'])
        loaded_tx_level['OHT_target_angle'] = data.get('tx_level', {}).get('OHT_target_angle', loaded_tx_level['OHT_target_angle'])
        loaded_tx_level['linear_distance'] = data.get('tx_level', {}).get('linear_distance', loaded_tx_level['linear_distance'])
        loaded_tx_level['scan_angles'] = data.get('tx_level', {}).get('scan_angles', loaded_tx_level['scan_angles'])
        loaded_tx_level['image_ROI_y'] = data.get('tx_level', {}).get('image_ROI_y', loaded_tx_level['image_ROI_y'])
        loaded_tx_level['image_ROI_x'] = data.get('tx_level', {}).get('image_ROI_x', loaded_tx_level['image_ROI_x'])
        loaded_tx_level['binary_threshold'] = data.get('tx_level', {}).get('binary_threshold', loaded_tx_level['binary_threshold'])
        loaded_tx_level['tx_level_origin_px'] = data.get('tx_level', {}).get('tx_level_origin_px', loaded_tx_level['tx_level_origin_px'])
        loaded_tx_level['px2mm_conversion_gain'] = data.get('tx_level', {}).get('px2mm_conversion_gain', loaded_tx_level['px2mm_conversion_gain'])
        loaded_tx_level['pass_criteria'] = data.get('tx_level', {}).get('pass_criteria', loaded_tx_level['pass_criteria'])
        
        # 홈 포지션
        loaded_home_position['OHT_target_angle'] = data.get('home_position', {}).get('OHT_target_angle', loaded_home_position['OHT_target_angle'])
        loaded_home_position['OBS_target_angle'] = data.get('home_position', {}).get('OBS_target_angle', loaded_home_position['OBS_target_angle'])
        loaded_home_position['device_rotation_speed'] = data.get('home_position', {}).get('device_rotation_speed', loaded_home_position['device_rotation_speed'])
        loaded_home_position['test_distance'] = data.get('home_position', {}).get('test_distance', loaded_home_position['test_distance'])
        loaded_home_position['device_angle'] = data.get('home_position', {}).get('device_angle', loaded_home_position['device_angle'])
        loaded_home_position['logging_frame_num'] = data.get('home_position', {}).get('logging_frame_num', loaded_home_position['logging_frame_num'])
        loaded_home_position['frame_size'] = data.get('home_position', {}).get('frame_size', loaded_home_position['frame_size'])
        loaded_home_position['home_position_pass_criteria'] = data.get('home_position', {}).get('home_position_pass_criteria', loaded_home_position['home_position_pass_criteria'])
        
        # 거리 성능
        loaded_distance_performance['OHT_target_angle'] = float(data.get('distance_performance', {}).get('OHT_target_angle', loaded_distance_performance['OHT_target_angle']))
        loaded_distance_performance['OBS_target_angle'] = float(data.get('distance_performance', {}).get('OBS_target_angle', loaded_distance_performance['OBS_target_angle']))
        loaded_distance_performance['device_rotation_speed'] = float(data.get('distance_performance', {}).get('device_rotation_speed', loaded_distance_performance['device_rotation_speed']))
        loaded_distance_performance['LINEAR_STAGE_OFFSET'] = float(data.get('distance_performance', {}).get('LINEAR_STAGE_OFFSET', loaded_distance_performance['LINEAR_STAGE_OFFSET']))
        
        # 복잡한 데이터 구조 처리 (리스트와 딕셔너리를 포함하는 구조)
        loaded_distance_performance['oht_cal_dist_points'] = data.get('distance_performance', {}).get('oht_cal_dist_points', loaded_distance_performance['oht_cal_dist_points'])
        loaded_distance_performance['obs_cal_dist_points'] = data.get('distance_performance', {}).get('obs_cal_dist_points', loaded_distance_performance['obs_cal_dist_points'])
        loaded_distance_performance['oht_test_dist_points'] = data.get('distance_performance', {}).get('oht_test_dist_points', loaded_distance_performance['oht_test_dist_points'])
        loaded_distance_performance['obs_test_dist_points'] = data.get('distance_performance', {}).get('obs_test_dist_points', loaded_distance_performance['obs_test_dist_points'])
        
        loaded_distance_performance['logging_frame_num'] = int(data.get('distance_performance', {}).get('logging_frame_num', loaded_distance_performance['logging_frame_num']))
        loaded_distance_performance['ROI_width'] = float(data.get('distance_performance', {}).get('ROI_width', loaded_distance_performance['ROI_width']))
        loaded_distance_performance['precision_pass_criteria'] = float(data.get('distance_performance', {}).get('precision_pass_criteria', loaded_distance_performance['precision_pass_criteria']))
        loaded_distance_performance['accuracy_pass_criteria'] = float(data.get('distance_performance', {}).get('accuracy_pass_criteria', loaded_distance_performance['accuracy_pass_criteria']))

        # OHT 필터링 테이블 생성
        loaded_OHT_filtering_table_generation['ROI_width'] = float(data.get('OHT_filtering_table_generation', {}).get('ROI_width', loaded_OHT_filtering_table_generation['ROI_width']))
        loaded_OHT_filtering_table_generation['EXTRAPOLATION_POINTS'] = int(data.get('OHT_filtering_table_generation', {}).get('EXTRAPOLATION_POINTS', loaded_OHT_filtering_table_generation['EXTRAPOLATION_POINTS']))
        loaded_OHT_filtering_table_generation['measurement_cond'] = data.get('OHT_filtering_table_generation', {}).get('measurement_cond', loaded_OHT_filtering_table_generation['measurement_cond'])

        # OHT 필터링 검증
        loaded_OHT_filtering_validation['validation_cond'] = data.get('OHT_filtering_validation', {}).get('validation_cond', loaded_OHT_filtering_validation['validation_cond'])
        loaded_OHT_filtering_validation['validation_area_path'] = data.get('OHT_filtering_validation', {}).get('validation_area_path', loaded_OHT_filtering_validation['validation_area_path'])
        loaded_OHT_filtering_validation['empty_area_path'] = data.get('OHT_filtering_validation', {}).get('empty_area_path', loaded_OHT_filtering_validation['empty_area_path'])

        # 후방 커버 검사
        loaded_rear_cover_detection['test_cond'] = data.get('rear_cover_detection', {}).get('test_cond', loaded_rear_cover_detection['test_cond'])
        loaded_rear_cover_detection['test_area_path'] = data.get('rear_cover_detection', {}).get('test_area_path', loaded_rear_cover_detection['test_area_path'])
        loaded_rear_cover_detection['empty_area_path'] = data.get('rear_cover_detection', {}).get('empty_area_path', loaded_rear_cover_detection['empty_area_path'])

        # 최대 거리 검사
        loaded_max_distance['test_angle'] = data.get('max_distance', {}).get('test_angle', loaded_max_distance['test_angle'])
        loaded_max_distance['ROI_width'] = data.get('max_distance', {}).get('ROI_width', loaded_max_distance['ROI_width'])
        loaded_max_distance['logging_frame_num'] = data.get('max_distance', {}).get('logging_frame_num', loaded_max_distance['logging_frame_num'])
        loaded_max_distance['detection_ratio_criteria'] = data.get('max_distance', {}).get('detection_ratio_criteria', loaded_max_distance['detection_ratio_criteria'])

    # 2. 입력 필드 컨트롤 생성 시 loaded_* 값 사용
    sensor_ip_field = ft.TextField(label="GL5 IP 주소", width=600, value=loaded_connection['UDP_SENSOR_IP'])
    sensor_port_field = ft.TextField(label="GL5 포트", width=600, value=str(loaded_connection['UDP_SENSOR_PORT']))
    pc_ip_field = ft.TextField(label="PC IP 주소", width=600, value=loaded_connection['UDP_PC_IP'])
    pc_port_field = ft.TextField(label="PC 포트", width=600, value=str(loaded_connection['UDP_PC_PORT']))
    etel_ip_field = ft.TextField(label="ETEL 스테이지 IP", width=600, value=loaded_connection['etel_stage_IP_addr'])
    dpin_ip_field = ft.TextField(label="DPIN 고니오 IP", width=600, value=loaded_connection['DPIN_gonio_IP_addr'])
    dpin_port_field = ft.TextField(label="DPIN 고니오 포트", width=600, value=str(loaded_connection['DPIN_gonio_port']))
    etel_stage_offset_field = ft.TextField(label="ETEL 스테이지 오프셋", width=600, value=str(loaded_connection['etel_stage_offset']))

    camera_fps_field = ft.TextField(label="카메라 FPS", width=600, value=str(loaded_beam_size['camera_FPS']))
    camera_acq_field = ft.TextField(label="카메라 획득 프레임 수", width=600, value=str(loaded_beam_size['camera_acqusition_num']))
    oht_exp_field = ft.TextField(label="OHT 카메라 노출시간", width=600, value=str(loaded_beam_size['OHT_camera_exposure']))
    obs_exp_field = ft.TextField(label="OBS 카메라 노출시간", width=600, value=str(loaded_beam_size['OBS_camera_exposure']))
    oht_angle_field = ft.TextField(label="OHT 타겟 각도", width=600, value=str(loaded_beam_size['OHT_target_angle']))
    obs_angle_field = ft.TextField(label="OBS 타겟 각도", width=600, value=str(loaded_beam_size['OBS_target_angle']))
    test_dist_field = ft.TextField(label="테스트 거리 (mm)", width=600, value=str(loaded_beam_size['test_dist']))
    pass_criteria_field = ft.TextField(label="빔 사이즈 합격 기준 (mm)", width=600, value=str(loaded_beam_size['beamsize_pass_criteria']))
    threshold_dropdown = ft.Dropdown(
        label="임계값 기준",
        width=600,
        options=[
            ft.dropdown.Option("1/e^2"),
            ft.dropdown.Option("FWHM")
        ],
        value=loaded_beam_size['threshold_std']
    )
    
    # Update walk error settings to match gl507_walkerror_auto.py
    walk_error_stage_dist_field = ft.TextField(label="Walk Error Stage Distance", width=600, value=loaded_walk_error['walk_error_stage_dist'])
    speed_conditions_field = ft.TextField(label="Speed Conditions (e.g., [{'speed': 0.7, 'max_pulse_width': 2500}, ...])", width=600, height=600, multiline=True, value=json.dumps(loaded_walk_error['speed_conditions'], indent=4))
    OHT_ld_high_voltage_field = ft.TextField(label="OHT LD HV (V)", width=600, value=str(loaded_walk_error['OHT_ld_high_voltage']))
    OHT_pd_high_voltage_field = ft.TextField(label="OHT PD HV (V)", width=600, value=str(loaded_walk_error['OHT_pd_high_voltage']))
    OHT_BR_intensity_field = ft.TextField(label="OHT BR Intensity (0.1ns)", width=600, value=str(loaded_walk_error['OHT_BR_intensity']))
    OBS_ld_high_voltage_field = ft.TextField(label="OBS LD HV (V)", width=600, value=str(loaded_walk_error['OBS_ld_high_voltage']))
    OBS_pd_high_voltage_field = ft.TextField(label="OBS PD HV (V)", width=600, value=str(loaded_walk_error['OBS_pd_high_voltage']))
    OBS_BR_intensity_field = ft.TextField(label="OBS BR Intensity (0.1ns)", width=600, value=str(loaded_walk_error['OBS_BR_intensity']))

    # 수평도 검사 설정 필드 추가
    tx_level_ld_hv_field = ft.TextField(label="LD HV", width=600, value=str(loaded_tx_level['LD_HV']))
    tx_level_oht_exp_field = ft.TextField(label="OHT 카메라 노출시간", width=600, value=str(loaded_tx_level['OHT_camera_exposure']))
    tx_level_obs_exp_field = ft.TextField(label="OBS 카메라 노출시간", width=600, value=str(loaded_tx_level['OBS_camera_exposure']))
    tx_level_camera_fps_field = ft.TextField(label="카메라 FPS", width=600, value=str(loaded_tx_level['camera_FPS']))
    tx_level_camera_acq_field = ft.TextField(label="카메라 획득 프레임 수", width=600, value=str(loaded_tx_level['camera_acqusition_num']))
    tx_level_oht_angle_field = ft.TextField(label="OHT 타겟 각도", width=600, value=str(loaded_tx_level['OHT_target_angle']))
    tx_level_obs_angle_field = ft.TextField(label="OBS 타겟 각도", width=600, value=str(loaded_tx_level['OBS_target_angle']))
    tx_level_linear_dist_field = ft.TextField(label="검사 거리 (mm)", width=600, value=str(loaded_tx_level['linear_distance']))
    tx_level_scan_angles_field = ft.TextField(label="스캔 각도", width=600, value=str(loaded_tx_level['scan_angles']))
    tx_level_roi_x_field = ft.TextField(label="이미지 ROI X", width=600, value=str(loaded_tx_level['image_ROI_x']))
    tx_level_roi_y_field = ft.TextField(label="이미지 ROI Y", width=600, value=str(loaded_tx_level['image_ROI_y']))
    tx_level_binary_threshold_field = ft.TextField(label="이진화 임계값", width=600, value=str(loaded_tx_level['binary_threshold']))
    tx_level_origin_px_field = ft.TextField(label="수평도 원점 픽셀", width=600, value=str(loaded_tx_level['tx_level_origin_px']))
    tx_level_px2mm_gain_field = ft.TextField(label="픽셀-밀리미터 변환 계수", width=600, value=str(loaded_tx_level['px2mm_conversion_gain']))
    tx_level_pass_criteria_field = ft.TextField(label="합격 기준 (도)", width=600, value=str(loaded_tx_level['pass_criteria']))

    # 홈 포지션 설정 필드 추가
    home_position_oht_angle_field = ft.TextField(label="OHT 타겟 각도", width=600, value=str(loaded_home_position['OHT_target_angle']))
    home_position_obs_angle_field = ft.TextField(label="OBS 타겟 각도", width=600, value=str(loaded_home_position['OBS_target_angle']))
    # home_position_device_rotation_speed_field = ft.TextField(label="GL5 회전 속도", width=600, value=str(loaded_home_position['device_rotation_speed']))
    home_position_test_distance_field = ft.TextField(label="테스트 거리 (mm)", width=600, value=str(loaded_home_position['test_distance']))
    # home_position_device_angle_field = ft.TextField(label="GL5 스캔 각도", width=600, value=str(loaded_home_position['device_angle']))
    home_position_logging_frame_num_field = ft.TextField(label="로깅 프레임 수", width=600, value=str(loaded_home_position['logging_frame_num']))
    # home_position_frame_size_field = ft.TextField(label="프레임 크기", width=600, value=str(loaded_home_position['frame_size']))
    home_position_pass_criteria_field = ft.TextField(label="합격 기준", width=600, value=str(loaded_home_position['home_position_pass_criteria']))
    
    # 거리 성능 설정 필드 추가
    distance_performance_oht_target_angle_field = ft.TextField(label="OHT 타겟 각도", width=600, value=str(loaded_distance_performance['OHT_target_angle']))
    distance_performance_obs_target_angle_field = ft.TextField(label="OBS 타겟 각도", width=600, value=str(loaded_distance_performance['OBS_target_angle']))
    # distance_performance_device_rotation_speed_field = ft.TextField(label="GL5 회전 속도", width=600, value=str(loaded_distance_performance['device_rotation_speed']))
    # distance_performance_linear_stage_offset_field = ft.TextField(label="ETEL 스테이지 오프셋", width=600, value=str(loaded_distance_performance['LINEAR_STAGE_OFFSET']))
    # 복잡한 데이터 구조 처리 (리스트와 딕셔너리를 포함하는 구조)
    distance_performance_oht_cal_dist_points_field = ft.TextField(label="OHT offset 보정 포인트", width=600, height=600, multiline=True, value=json.dumps(loaded_distance_performance['oht_cal_dist_points'], indent=4))
    distance_performance_obs_cal_dist_points_field = ft.TextField(label="OBS offset 보정 포인트", width=600, height=600, multiline=True, value=json.dumps(loaded_distance_performance['obs_cal_dist_points'], indent=4))
    distance_performance_oht_test_dist_points_field = ft.TextField(label="OHT 검사 거리 포인트", width=600, height=600, multiline=True, value=json.dumps(loaded_distance_performance['oht_test_dist_points'], indent=4))
    distance_performance_obs_test_dist_points_field = ft.TextField(label="OBS 검사 거리 포인트", width=600, height=600, multiline=True, value=json.dumps(loaded_distance_performance['obs_test_dist_points'], indent=4))
    distance_performance_logging_frame_num_field = ft.TextField(label="로깅 프레임 수", width=600, value=str(loaded_distance_performance['logging_frame_num']))
    distance_performance_roi_width_field = ft.TextField(label="ROI 너비 (mm)", width=600, value=str(loaded_distance_performance['ROI_width']))
    distance_performance_precision_pass_criteria_field = ft.TextField(label="정밀도 합격 기준 (mm)", width=600, value=str(loaded_distance_performance['precision_pass_criteria']))
    distance_performance_accuracy_pass_criteria_field = ft.TextField(label="정확도 합격 기준 (mm)", width=600, value=str(loaded_distance_performance['accuracy_pass_criteria']))

    # OHT 필터링 테이블 생성 설정 필드 추가
    OHT_filtering_table_generation_roi_width_field = ft.TextField(label="ROI 너비 (mm)", width=600, value=str(loaded_OHT_filtering_table_generation['ROI_width']))
    OHT_filtering_table_generation_extrapolation_points_field = ft.TextField(label="외삽 포인트", width=600, value=str(loaded_OHT_filtering_table_generation['EXTRAPOLATION_POINTS']))
    OHT_filtering_table_generation_measurement_cond_field = ft.TextField(label="측정 조건", width=600, height=600, multiline=True, value=json.dumps(loaded_OHT_filtering_table_generation['measurement_cond'], indent=4))

    # OHT 필터링 검증 설정 필드 추가
    OHT_filtering_validation_validation_cond_field = ft.TextField(label="검증 조건", width=600, height=600, multiline=True, value=json.dumps(loaded_OHT_filtering_validation['validation_cond'], indent=4))
    OHT_filtering_validation_validation_area_path_field = ft.TextField(label="검증 영역 경로", width=600, value=str(loaded_OHT_filtering_validation['validation_area_path']))
    OHT_filtering_validation_empty_area_path_field = ft.TextField(label="빈 영역 경로", width=600, value=str(loaded_OHT_filtering_validation['empty_area_path']))

    # 후방 커버 검사 설정 필드 추가
    rear_cover_detection_test_cond_field = ft.TextField(label="검사 조건", width=600, height=600, multiline=True, value=json.dumps(loaded_rear_cover_detection['test_cond'], indent=4))
    rear_cover_detection_test_area_path_field = ft.TextField(label="검사 영역 경로", width=600, value=str(loaded_rear_cover_detection['test_area_path']))
    rear_cover_detection_empty_area_path_field = ft.TextField(label="빈 영역 경로", width=600, value=str(loaded_rear_cover_detection['empty_area_path']))

    # 최대 거리 검사 설정 필드 추가
    max_distance_test_angle_field = ft.TextField(label="검사 각도", width=600, multiline=True, value=str(loaded_max_distance['test_angle']))
    max_distance_roi_width_field = ft.TextField(label="ROI 너비 (mm)", width=600, value=str(loaded_max_distance['ROI_width']))
    max_distance_logging_frame_num_field = ft.TextField(label="로깅 프레임 수", width=600, value=str(loaded_max_distance['logging_frame_num']))
    max_distance_detection_ratio_criteria_field = ft.TextField(label="검출 비율 기준", width=600, value=str(loaded_max_distance['detection_ratio_criteria']))

    # Define a global variable to track the current text field
    current_text_field = None

    # Define the function to handle file selection
    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal current_text_field
        if e.files and current_text_field:
            # Set the selected file path to the text field
            current_text_field.value = e.files[0].path
            page.update()

    # Create a single FilePicker instance
    file_picker = ft.FilePicker(on_result=on_file_picked)

    # Add the FilePicker to the page
    page.overlay.append(file_picker)
    page.update()

    # Function to set current text field and pick files
    def pick_file_for(e, text_field):
        nonlocal current_text_field
        current_text_field = text_field
        file_picker.pick_files()

    def save_settings_to_json(e=None):
        data = {
            'connection': {
                'UDP_SENSOR_IP': sensor_ip_field.value,
                'UDP_SENSOR_PORT': int(sensor_port_field.value),
                'UDP_PC_IP': pc_ip_field.value,
                'UDP_PC_PORT': int(pc_port_field.value),
                'etel_stage_IP_addr': etel_ip_field.value,
                'DPIN_gonio_IP_addr': dpin_ip_field.value,
                'DPIN_gonio_port': int(dpin_port_field.value),
                'etel_stage_offset': float(etel_stage_offset_field.value),  # Changed from int to float
            },
            'walk_error_lut': {
                'walk_error_stage_dist': parse_dict_from_string(walk_error_stage_dist_field.value),
                'speed_conditions': parse_dict_from_string(speed_conditions_field.value),
                'OHT_ld_high_voltage': float(OHT_ld_high_voltage_field.value),
                'OHT_pd_high_voltage': float(OHT_pd_high_voltage_field.value),
                'OHT_BR_intensity': float(OHT_BR_intensity_field.value),
                'OBS_ld_high_voltage': float(OBS_ld_high_voltage_field.value),
                'OBS_pd_high_voltage': float(OBS_pd_high_voltage_field.value),
                'OBS_BR_intensity': float(OBS_BR_intensity_field.value)
            },
            'beam_size': {
                'camera_FPS': float(camera_fps_field.value),
                'camera_acqusition_num': int(camera_acq_field.value),
                'OHT_camera_exposure': int(oht_exp_field.value),
                'OBS_camera_exposure': int(obs_exp_field.value),
                'OHT_target_angle': float(oht_angle_field.value),
                'OBS_target_angle': float(obs_angle_field.value),
                'test_dist': float(test_dist_field.value),
                'beamsize_pass_criteria': float(pass_criteria_field.value),
                'threshold_std': threshold_dropdown.value
            },
            'tx_level': {
                'LD_HV': float(tx_level_ld_hv_field.value),
                'OBS_camera_exposure': int(tx_level_obs_exp_field.value),
                'OHT_camera_exposure': int(tx_level_oht_exp_field.value),
                'camera_FPS': float(tx_level_camera_fps_field.value),
                'camera_acqusition_num': int(tx_level_camera_acq_field.value),
                'OBS_target_angle': float(tx_level_obs_angle_field.value),
                'OHT_target_angle': float(tx_level_oht_angle_field.value),
                'linear_distance': float(tx_level_linear_dist_field.value),
                'scan_angles': parse_dict_from_string(tx_level_scan_angles_field.value),
                'image_ROI_y': parse_dict_from_string(tx_level_roi_y_field.value),
                'image_ROI_x': parse_dict_from_string(tx_level_roi_x_field.value),
                'binary_threshold': int(tx_level_binary_threshold_field.value),
                'tx_level_origin_px': int(tx_level_origin_px_field.value),
                'px2mm_conversion_gain': float(tx_level_px2mm_gain_field.value),
                'pass_criteria': float(tx_level_pass_criteria_field.value)
            },
            'home_position': {
                'OHT_target_angle': float(home_position_oht_angle_field.value),
                'OBS_target_angle': float(home_position_obs_angle_field.value),
                # 'device_rotation_speed': float(home_position_device_rotation_speed_field.value),
                'test_distance': float(home_position_test_distance_field.value),
                # 'device_angle': float(home_position_device_angle_field.value),
                'logging_frame_num': int(home_position_logging_frame_num_field.value),
                # 'frame_size': int(home_position_frame_size_field.value),
                'home_position_pass_criteria': float(home_position_pass_criteria_field.value)
            },
            'distance_performance': {
                'OHT_target_angle': float(distance_performance_oht_target_angle_field.value),
                'OBS_target_angle': float(distance_performance_obs_target_angle_field.value),
                # 'device_rotation_speed': float(loaded_distance_performance['device_rotation_speed']),
                # 'LINEAR_STAGE_OFFSET': float(loaded_distance_performance['LINEAR_STAGE_OFFSET']),
                'oht_cal_dist_points': parse_dict_from_string(distance_performance_oht_cal_dist_points_field.value),
                'obs_cal_dist_points': parse_dict_from_string(distance_performance_obs_cal_dist_points_field.value),
                'oht_test_dist_points': parse_dict_from_string(distance_performance_oht_test_dist_points_field.value),
                'obs_test_dist_points': parse_dict_from_string(distance_performance_obs_test_dist_points_field.value),
                'logging_frame_num': int(distance_performance_logging_frame_num_field.value),
                'ROI_width': float(distance_performance_roi_width_field.value),
                'precision_pass_criteria': float(distance_performance_precision_pass_criteria_field.value),
                'accuracy_pass_criteria': float(distance_performance_accuracy_pass_criteria_field.value)
            },
            'OHT_filtering_table_generation': {
                'ROI_width': float(loaded_OHT_filtering_table_generation['ROI_width']),
                'EXTRAPOLATION_POINTS': int(loaded_OHT_filtering_table_generation['EXTRAPOLATION_POINTS']),
                'measurement_cond': parse_dict_from_string(loaded_OHT_filtering_table_generation['measurement_cond'])
            },
            'OHT_filtering_validation': {
                'validation_cond': parse_dict_from_string(OHT_filtering_validation_validation_cond_field.value),
                'validation_area_path': OHT_filtering_validation_validation_area_path_field.value,
                'empty_area_path': OHT_filtering_validation_empty_area_path_field.value
            },
            'rear_cover_detection': {
                'test_cond': parse_dict_from_string(rear_cover_detection_test_cond_field.value),
                'test_area_path': rear_cover_detection_test_area_path_field.value,
                'empty_area_path': rear_cover_detection_empty_area_path_field.value
            },
            'max_distance': {
                'test_angle': parse_dict_from_string(max_distance_test_angle_field.value),
                'ROI_width': float(max_distance_roi_width_field.value),
                'logging_frame_num': int(max_distance_logging_frame_num_field.value),
                'detection_ratio_criteria': float(max_distance_detection_ratio_criteria_field.value)
            }
        }
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        page.snack_bar = ft.SnackBar(content=ft.Text("설정이 settings.json에 저장되었습니다."))
        page.update()

        # 연결 파라미터 업데이트
        loaded_connection['UDP_SENSOR_IP'] = sensor_ip_field.value
        loaded_connection['UDP_SENSOR_PORT'] = int(sensor_port_field.value)
        loaded_connection['UDP_PC_IP'] = pc_ip_field.value
        loaded_connection['UDP_PC_PORT'] = int(pc_port_field.value)
        loaded_connection['etel_stage_IP_addr'] = etel_ip_field.value
        loaded_connection['DPIN_gonio_IP_addr'] = dpin_ip_field.value
        loaded_connection['DPIN_gonio_port'] = int(dpin_port_field.value)
        loaded_connection['etel_stage_offset'] = float(etel_stage_offset_field.value)

        # loaded_beam_size 업데이트
        loaded_beam_size['camera_FPS'] = float(camera_fps_field.value)
        loaded_beam_size['camera_acqusition_num'] = int(camera_acq_field.value)
        loaded_beam_size['OHT_camera_exposure'] = int(oht_exp_field.value)
        loaded_beam_size['OBS_camera_exposure'] = int(obs_exp_field.value)
        loaded_beam_size['OHT_target_angle'] = float(oht_angle_field.value)
        loaded_beam_size['OBS_target_angle'] = float(obs_angle_field.value)
        loaded_beam_size['test_dist'] = float(test_dist_field.value)
        loaded_beam_size['beamsize_pass_criteria'] = float(pass_criteria_field.value)
        loaded_beam_size['threshold_std'] = threshold_dropdown.value

        # loaded_walk_error 업데이트
        loaded_walk_error['walk_error_stage_dist'] = parse_dict_from_string(walk_error_stage_dist_field.value)
        loaded_walk_error['speed_conditions'] = parse_dict_from_string(speed_conditions_field.value)
        loaded_walk_error['OHT_ld_high_voltage'] = float(OHT_ld_high_voltage_field.value)
        loaded_walk_error['OHT_pd_high_voltage'] = float(OHT_pd_high_voltage_field.value)
        loaded_walk_error['OHT_BR_intensity'] = float(OHT_BR_intensity_field.value)
        loaded_walk_error['OBS_ld_high_voltage'] = float(OBS_ld_high_voltage_field.value)
        loaded_walk_error['OBS_pd_high_voltage'] = float(OBS_pd_high_voltage_field.value)
        loaded_walk_error['OBS_BR_intensity'] = float(OBS_BR_intensity_field.value)

        # tx_level_parameters 업데이트
        loaded_tx_level['LD_HV'] = float(tx_level_ld_hv_field.value)
        loaded_tx_level['OBS_camera_exposure'] = int(tx_level_obs_exp_field.value)
        loaded_tx_level['OHT_camera_exposure'] = int(tx_level_oht_exp_field.value)
        loaded_tx_level['camera_FPS'] = float(tx_level_camera_fps_field.value)
        loaded_tx_level['camera_acqusition_num'] = int(tx_level_camera_acq_field.value)
        loaded_tx_level['OBS_target_angle'] = float(tx_level_obs_angle_field.value)
        loaded_tx_level['OHT_target_angle'] = float(tx_level_oht_angle_field.value)
        loaded_tx_level['linear_distance'] = float(tx_level_linear_dist_field.value)
        loaded_tx_level['scan_angles'] = parse_dict_from_string(tx_level_scan_angles_field.value)
        loaded_tx_level['image_ROI_y'] = parse_dict_from_string(tx_level_roi_y_field.value)
        loaded_tx_level['image_ROI_x'] = parse_dict_from_string(tx_level_roi_x_field.value)
        loaded_tx_level['binary_threshold'] = int(tx_level_binary_threshold_field.value)
        loaded_tx_level['tx_level_origin_px'] = int(tx_level_origin_px_field.value)
        loaded_tx_level['px2mm_conversion_gain'] = float(tx_level_px2mm_gain_field.value)
        loaded_tx_level['pass_criteria'] = float(tx_level_pass_criteria_field.value)

        # home_position_parameters 업데이트
        loaded_home_position['OHT_target_angle'] = float(home_position_oht_angle_field.value)
        loaded_home_position['OBS_target_angle'] = float(home_position_obs_angle_field.value)
        # loaded_home_position['device_rotation_speed'] = float(home_position_device_rotation_speed_field.value)
        loaded_home_position['test_distance'] = float(home_position_test_distance_field.value)
        # loaded_home_position['device_angle'] = float(home_position_device_angle_field.value)
        loaded_home_position['logging_frame_num'] = int(home_position_logging_frame_num_field.value)
        # loaded_home_position['frame_size'] = int(home_position_frame_size_field.value)
        loaded_home_position['home_position_pass_criteria'] = float(home_position_pass_criteria_field.value)

        # distance_performance_parameters 업데이트
        loaded_distance_performance['OHT_target_angle'] = float(distance_performance_oht_target_angle_field.value)
        loaded_distance_performance['OBS_target_angle'] = float(distance_performance_obs_target_angle_field.value)
        # loaded_distance_peevice_rotation_speed'] = float(distance_performance_device_rotation_speed_field.value)
        # loaded_distance_performance['Lrformance['dINEAR_STAGE_OFFSET'] = float(distance_performance_linear_stage_offset_field.value)
        loaded_distance_performance['oht_cal_dist_points'] = parse_dict_from_string(distance_performance_oht_cal_dist_points_field.value)
        loaded_distance_performance['obs_cal_dist_points'] = parse_dict_from_string(distance_performance_obs_cal_dist_points_field.value)
        loaded_distance_performance['oht_test_dist_points'] = parse_dict_from_string(distance_performance_oht_test_dist_points_field.value)
        loaded_distance_performance['obs_test_dist_points'] = parse_dict_from_string(distance_performance_obs_test_dist_points_field.value)
        loaded_distance_performance['logging_frame_num'] = int(distance_performance_logging_frame_num_field.value)
        loaded_distance_performance['ROI_width'] = float(distance_performance_roi_width_field.value)
        loaded_distance_performance['precision_pass_criteria'] = float(distance_performance_precision_pass_criteria_field.value)
        loaded_distance_performance['accuracy_pass_criteria'] = float(distance_performance_accuracy_pass_criteria_field.value)
        
        # OHT 필터링 테이블 생성 설정 업데이트
        loaded_OHT_filtering_table_generation['ROI_width'] = float(OHT_filtering_table_generation_roi_width_field.value)
        loaded_OHT_filtering_table_generation['EXTRAPOLATION_POINTS'] = int(OHT_filtering_table_generation_extrapolation_points_field.value)
        loaded_OHT_filtering_table_generation['measurement_cond'] = parse_dict_from_string(OHT_filtering_table_generation_measurement_cond_field.value)

        # OHT 필터링 검증 설정 업데이트
        loaded_OHT_filtering_validation['validation_cond'] = parse_dict_from_string(OHT_filtering_validation_validation_cond_field.value)
        loaded_OHT_filtering_validation['validation_area_path'] = OHT_filtering_validation_validation_area_path_field.value
        loaded_OHT_filtering_validation['empty_area_path'] = OHT_filtering_validation_empty_area_path_field.value

        # 후방 커버 검사 설정 업데이트
        loaded_rear_cover_detection['test_cond'] = parse_dict_from_string(rear_cover_detection_test_cond_field.value)
        loaded_rear_cover_detection['test_area_path'] = rear_cover_detection_test_area_path_field.value
        loaded_rear_cover_detection['empty_area_path'] = rear_cover_detection_empty_area_path_field.value

        # 최대 거리 검사 설정 업데이트
        loaded_max_distance['test_angle'] = parse_dict_from_string(max_distance_test_angle_field.value)
        loaded_max_distance['ROI_width'] = float(max_distance_roi_width_field.value)
        loaded_max_distance['logging_frame_num'] = int(max_distance_logging_frame_num_field.value)
        loaded_max_distance['detection_ratio_criteria'] = float(max_distance_detection_ratio_criteria_field.value)

    def load_settings_from_json(e=None):
        if not os.path.exists("settings.json"):
            page.snack_bar = ft.SnackBar(content=ft.Text("settings.json 파일이 없습니다."))
            page.update()
            return
        with open("settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        # 연결
        sensor_ip_field.value = data['connection'].get('UDP_SENSOR_IP', beam_size_default_parameters['UDP_SENSOR_IP'])
        sensor_port_field.value = str(data['connection'].get('UDP_SENSOR_PORT', beam_size_default_parameters['UDP_SENSOR_PORT']))
        pc_ip_field.value = data['connection'].get('UDP_PC_IP', beam_size_default_parameters['UDP_PC_IP'])
        pc_port_field.value = str(data['connection'].get('UDP_PC_PORT', beam_size_default_parameters['UDP_PC_PORT']))
        etel_ip_field.value = data['connection'].get('etel_stage_IP_addr', beam_size_default_parameters['etel_stage_IP_addr'])
        dpin_ip_field.value = data['connection'].get('DPIN_gonio_IP_addr', beam_size_default_parameters['DPIN_gonio_IP_addr'])
        dpin_port_field.value = str(data['connection'].get('DPIN_gonio_port', beam_size_default_parameters['DPIN_gonio_port']))
        etel_stage_offset_field.value = str(data['connection'].get('etel_stage_offset', -43))

        # 빔 사이즈
        camera_fps_field.value = str(data['beam_size'].get('camera_FPS', beam_size_default_parameters['camera_FPS']))
        camera_acq_field.value = str(data['beam_size'].get('camera_acqusition_num', beam_size_default_parameters['camera_acqusition_num']))
        oht_exp_field.value = str(data['beam_size'].get('OHT_camera_exposure', beam_size_default_parameters['OHT_camera_exposure']))
        obs_exp_field.value = str(data['beam_size'].get('OBS_camera_exposure', beam_size_default_parameters['OBS_camera_exposure']))
        oht_angle_field.value = str(data['beam_size'].get('OHT_target_angle', beam_size_default_parameters['OHT_target_angle']))
        obs_angle_field.value = str(data['beam_size'].get('OBS_target_angle', beam_size_default_parameters['OBS_target_angle']))
        test_dist_field.value = str(data['beam_size'].get('test_dist', beam_size_default_parameters['test_dist']))
        pass_criteria_field.value = str(data['beam_size'].get('beamsize_pass_criteria', beam_size_default_parameters['beamsize_pass_criteria']))
        threshold_dropdown.value = data['beam_size'].get('threshold_std', beam_size_default_parameters['threshold_std'])

        # Walk Error LUT settings
        walk_error_stage_dist_field.value = str(data.get('walk_error_lut', {}).get('walk_error_stage_dist', walk_error_default_parameters['walk_error_stage_dist']))
        speed_conditions_field.value = json.dumps(data.get('walk_error_lut', {}).get('speed_conditions', walk_error_default_parameters['speed_conditions']), indent=4)
        OHT_ld_high_voltage_field.value = str(data.get('walk_error_lut', {}).get('OHT_ld_high_voltage', walk_error_default_parameters['OHT_ld_high_voltage']))
        OHT_pd_high_voltage_field.value = str(data.get('walk_error_lut', {}).get('OHT_pd_high_voltage', walk_error_default_parameters['OHT_pd_high_voltage']))
        OHT_BR_intensity_field.value = str(data.get('walk_error_lut', {}).get('OHT_BR_intensity', walk_error_default_parameters['OHT_BR_intensity']))
        OBS_ld_high_voltage_field.value = str(data.get('walk_error_lut', {}).get('OBS_ld_high_voltage', walk_error_default_parameters['OBS_ld_high_voltage']))
        OBS_pd_high_voltage_field.value = str(data.get('walk_error_lut', {}).get('OBS_pd_high_voltage', walk_error_default_parameters['OBS_pd_high_voltage']))
        OBS_BR_intensity_field.value = str(data.get('walk_error_lut', {}).get('OBS_BR_intensity', walk_error_default_parameters['OBS_BR_intensity']))

        # 수평도 검사 설정
        tx_level_ld_hv_field.value = str(data.get('tx_level', {}).get('LD_HV', loaded_tx_level['LD_HV']))
        tx_level_obs_exp_field.value = str(data.get('tx_level', {}).get('OBS_camera_exposure', loaded_tx_level['OBS_camera_exposure']))
        tx_level_oht_exp_field.value = str(data.get('tx_level', {}).get('OHT_camera_exposure', loaded_tx_level['OHT_camera_exposure']))
        tx_level_camera_fps_field.value = str(data.get('tx_level', {}).get('camera_FPS', loaded_tx_level['camera_FPS']))
        tx_level_camera_acq_field.value = str(data.get('tx_level', {}).get('camera_acqusition_num', loaded_tx_level['camera_acqusition_num']))
        tx_level_obs_angle_field.value = str(data.get('tx_level', {}).get('OBS_target_angle', loaded_tx_level['OBS_target_angle']))
        tx_level_oht_angle_field.value = str(data.get('tx_level', {}).get('OHT_target_angle', loaded_tx_level['OHT_target_angle']))
        tx_level_linear_dist_field.value = str(data.get('tx_level', {}).get('linear_distance', loaded_tx_level['linear_distance']))
        tx_level_scan_angles_field.value = str(data.get('tx_level', {}).get('scan_angles', loaded_tx_level['scan_angles']))
        tx_level_roi_y_field.value = str(data.get('tx_level', {}).get('image_ROI_y', loaded_tx_level['image_ROI_y']))
        tx_level_roi_x_field.value = str(data.get('tx_level', {}).get('image_ROI_x', loaded_tx_level['image_ROI_x']))
        tx_level_binary_threshold_field.value = str(data.get('tx_level', {}).get('binary_threshold', loaded_tx_level['binary_threshold']))
        tx_level_origin_px_field.value = str(data.get('tx_level', {}).get('tx_level_origin_px', loaded_tx_level['tx_level_origin_px']))
        tx_level_px2mm_gain_field.value = str(data.get('tx_level', {}).get('px2mm_conversion_gain', loaded_tx_level['px2mm_conversion_gain']))
        tx_level_pass_criteria_field.value = str(data.get('tx_level', {}).get('pass_criteria', loaded_tx_level['pass_criteria']))

        # 홈 포지션 설정
        home_position_oht_angle_field.value = str(data.get('home_position', {}).get('OHT_target_angle', loaded_home_position['OHT_target_angle']))
        home_position_obs_angle_field.value = str(data.get('home_position', {}).get('OBS_target_angle', loaded_home_position['OBS_target_angle']))
        # home_position_device_rotation_speed_field.value = str(data.get('home_position', {}).get('device_rotation_speed', loaded_home_position['device_rotation_speed']))
        home_position_test_distance_field.value = str(data.get('home_position', {}).get('test_distance', loaded_home_position['test_distance']))
        # home_position_device_angle_field.value = str(data.get('home_position', {}).get('device_angle', loaded_home_position['device_angle']))
        home_position_logging_frame_num_field.value = str(data.get('home_position', {}).get('logging_frame_num', loaded_home_position['logging_frame_num']))
        # home_position_frame_size_field.value = str(data.get('home_position', {}).get('frame_size', loaded_home_position['frame_size']))
        home_position_pass_criteria_field.value = str(data.get('home_position', {}).get('home_position_pass_criteria', loaded_home_position['home_position_pass_criteria']))

        # 거리 성능
        distance_performance_oht_target_angle_field.value = str(data.get('distance_performance', {}).get('OHT_target_angle', loaded_distance_performance['OHT_target_angle']))
        distance_performance_obs_target_angle_field.value = str(data.get('distance_performance', {}).get('OBS_target_angle', loaded_distance_performance['OBS_target_angle']))
        # distance_performance_device_rotation_speed_field.value = str(data.get('distance_performance', {}).get('device_rotation_speed', loaded_distance_performance['device_rotation_speed']))
        # distance_performance_linear_stage_offset_field.value = str(data.get('distance_performance', {}).get('LINEAR_STAGE_OFFSET', loaded_distance_performance['LINEAR_STAGE_OFFSET']))
        distance_performance_oht_cal_dist_points_field.value = json.dumps(data.get('distance_performance', {}).get('oht_cal_dist_points', loaded_distance_performance['oht_cal_dist_points']), indent=4)
        distance_performance_obs_cal_dist_points_field.value = json.dumps(data.get('distance_performance', {}).get('obs_cal_dist_points', loaded_distance_performance['obs_cal_dist_points']), indent=4)
        distance_performance_oht_test_dist_points_field.value = json.dumps(data.get('distance_performance', {}).get('oht_test_dist_points', loaded_distance_performance['oht_test_dist_points']), indent=4)
        distance_performance_obs_test_dist_points_field.value = json.dumps(data.get('distance_performance', {}).get('obs_test_dist_points', loaded_distance_performance['obs_test_dist_points']), indent=4)
        distance_performance_logging_frame_num_field.value = str(data.get('distance_performance', {}).get('logging_frame_num', loaded_distance_performance['logging_frame_num']))
        distance_performance_roi_width_field.value = str(data.get('distance_performance', {}).get('ROI_width', loaded_distance_performance['ROI_width']))
        distance_performance_precision_pass_criteria_field.value = str(data.get('distance_performance', {}).get('precision_pass_criteria', loaded_distance_performance['precision_pass_criteria']))
        distance_performance_accuracy_pass_criteria_field.value = str(data.get('distance_performance', {}).get('accuracy_pass_criteria', loaded_distance_performance['accuracy_pass_criteria']))
            
        # OHT 필터링 테이블 생성 설정 업데이트
        OHT_filtering_table_generation_roi_width_field.value = str(data.get('OHT_filtering_table_generation', {}).get('ROI_width', loaded_OHT_filtering_table_generation['ROI_width']))
        OHT_filtering_table_generation_extrapolation_points_field.value = str(data.get('OHT_filtering_table_generation', {}).get('EXTRAPOLATION_POINTS', loaded_OHT_filtering_table_generation['EXTRAPOLATION_POINTS']))
        OHT_filtering_table_generation_measurement_cond_field.value = json.dumps(data.get('OHT_filtering_table_generation', {}).get('measurement_cond', loaded_OHT_filtering_table_generation['measurement_cond']), indent=4)

        # OHT 필터링 검증 설정 업데이트
        OHT_filtering_validation_validation_cond_field.value = json.dumps(data.get('OHT_filtering_validation', {}).get('validation_cond', loaded_OHT_filtering_validation['validation_cond']), indent=4)
        OHT_filtering_validation_validation_area_path_field.value = str(data.get('OHT_filtering_validation', {}).get('validation_area_path', loaded_OHT_filtering_validation['validation_area_path']))
        OHT_filtering_validation_empty_area_path_field.value = str(data.get('OHT_filtering_validation', {}).get('empty_area_path', loaded_OHT_filtering_validation['empty_area_path']))

        # 후방 커버 검사 설정 업데이트
        rear_cover_detection_test_cond_field.value = json.dumps(data.get('rear_cover_detection', {}).get('test_cond', loaded_rear_cover_detection['test_cond']), indent=4)
        rear_cover_detection_test_area_path_field.value = str(data.get('rear_cover_detection', {}).get('test_area_path', loaded_rear_cover_detection['test_area_path']))
        rear_cover_detection_empty_area_path_field.value = str(data.get('rear_cover_detection', {}).get('empty_area_path', loaded_rear_cover_detection['empty_area_path']))

        # 최대 거리 검사 설정 업데이트
        max_distance_test_angle_field.value = json.dumps(data.get('max_distance', {}).get('test_angle', loaded_max_distance['test_angle']), indent=4)
        max_distance_roi_width_field.value = str(data.get('max_distance', {}).get('ROI_width', loaded_max_distance['ROI_width']))
        max_distance_logging_frame_num_field.value = str(data.get('max_distance', {}).get('logging_frame_num', loaded_max_distance['logging_frame_num']))
        max_distance_detection_ratio_criteria_field.value = str(data.get('max_distance', {}).get('detection_ratio_criteria', loaded_max_distance['detection_ratio_criteria']))

        update_status("설정이 settings.json에서 불러와졌습니다.")
        page.update()

    # 연결 상태 변수
    is_all_connected = False
    is_gl5_connected = False
    is_etel_connected = False
    is_camera_connected = False
    is_dpin_connected = False
    is_kdc101_connected = False  # KDC101 연결 상태 변수 추가

    # 연결 함수 템플릿 (Connect/Disconnect)
    def connect_all(e=None):
        nonlocal is_all_connected
        is_all_connected = True
        connect_gl5(e)
        connect_etel(e)
        connect_camera(e)
        connect_dpin(e)
        connect_kdc101(e)  # KDC101 연결 추가
        connection_tab.content = get_connection_content()
        update_status("전체 Connect 시도")
    def disconnect_all(e=None):
        nonlocal is_all_connected
        is_all_connected = False
        disconnect_gl5(e)
        disconnect_etel(e)
        disconnect_camera(e)
        disconnect_dpin(e)
        disconnect_kdc101(e)  # KDC101 연결 해제 추가
        connection_tab.content = get_connection_content()
        update_status("전체 Disconnect 시도")
    def connect_etel(e=None):
        global stage_etel
        nonlocal is_etel_connected
        status = stage_etel.connect(etel_ip_field.value, 3)
        if status:
            time.sleep(0.1)  # 연결 후 잠시 대기
            try:
                # 연결 성공 시 초기화 및 홈서치 수행
                ETEL.init_stage(stage_etel, offset=loaded_connection['etel_stage_offset'])
                update_status("ETEL stage 연결 및 초기화 성공")
                is_etel_connected = True
            except Exception as ex:
                update_status(f"ETEL stage 초기화 실패: {ex}")
                is_etel_connected = False
        else:
            update_status("ETEL stage 연결 실패")
            is_etel_connected = False
        connection_tab.content = get_connection_content()
        page.update()
    def disconnect_etel(e=None):
        global stage_etel
        nonlocal is_etel_connected
        try:
            ETEL.disconnect_stage(stage_etel)
            update_status("ETEL stage 연결 해제 성공")
        except Exception as ex:
            update_status(f"ETEL stage 연결 해제 실패: {ex}")
        is_etel_connected = False
        connection_tab.content = get_connection_content()
        page.update()
    def connect_gl5(e=None):
        global GL5_core, GL5_user, GL5_developer, GL5_area
        nonlocal is_gl5_connected
        if GL5_core.connectUDP(sensor_ip_field.value, int(sensor_port_field.value), pc_ip_field.value, int(pc_port_field.value)):
            success, serial = GL5_user.getSerialNum(GL5_core)
            if success:
                update_status(f"GL5 연결 성공 (Serial: {serial})")
                is_gl5_connected = True
            else:
                update_status("GL5 연결은 되었으나 Serial 확인 실패")
                is_gl5_connected = False
        else:
            update_status("GL5 UDP 연결 실패")
            is_gl5_connected = False
        connection_tab.content = get_connection_content()
        page.update()
    def disconnect_gl5(e=None):
        global GL5_core
        nonlocal is_gl5_connected
        if GL5_core is not None:
            GL5_core.disconnect()
            if hasattr(GL5_core, 'isConnected') and not GL5_core.isConnected():
                update_status("GL5 연결 해제 성공")
                is_gl5_connected = False
            else:
                update_status("GL5 연결 해제 실패")
                is_gl5_connected = True
        else:
            update_status("GL5 객체 없음")
            is_gl5_connected = False
        connection_tab.content = get_connection_content()
        page.update()
    def connect_dpin(e=None):
        global dpin
        nonlocal is_dpin_connected
        try:
            dpin.connect(dpin_ip_field.value, int(dpin_port_field.value))
            dpin.searching_home()
            update_status("DPIN 연결 및 홈서치 성공")
            is_dpin_connected = True
        except Exception as ex:
            update_status(f"DPIN 연결 실패: {ex}")
            is_dpin_connected = False
        connection_tab.content = get_connection_content()
        page.update()
    def disconnect_dpin(e=None):
        global dpin
        nonlocal is_dpin_connected
        try:
            dpin.disconnect()
            update_status("DPIN 연결 해제 성공")
        except Exception as ex:
            update_status(f"DPIN 연결 해제 실패: {ex}")
        is_dpin_connected = False
        connection_tab.content = get_connection_content()
        page.update()
    def connect_camera(e=None):
        global camera
        nonlocal is_camera_connected
        try:
            camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
            camera.Open()
            camera.Close()  # 빔 사이즈 run에서 다시 open으로 개발해놔서 여기서는 확인만 해줌
            update_status("카메라 연결 확인")
            is_camera_connected = True
        except Exception as ex:
            update_status(f"카메라 연결 실패: {ex}")
            is_camera_connected = False
        connection_tab.content = get_connection_content()
        page.update()
    def disconnect_camera(e=None):
        global camera
        nonlocal is_camera_connected
        if camera is not None and camera.IsOpen():
            camera.Close()
            update_status("카메라 연결 해제")
        camera = None
        is_camera_connected = False
        connection_tab.content = get_connection_content()
        page.update()
    def connect_kdc101(e=None):
        global kdc101
        nonlocal is_kdc101_connected
        try:
            if kdc101 is None:
                kdc101 = KDC101()  # 연결 시도 시점에 객체 생성
            if kdc101.is_homed():
                update_status("KDC101 스테이지 연결 및 홈 상태 확인")
                is_kdc101_connected = True
            else:
                kdc101.home_search()
                update_status("KDC101 스테이지 연결 및 홈서치 완료")
                is_kdc101_connected = True
        except Exception as ex:
            update_status(f"KDC101 스테이지 연결 실패: {ex}")
            is_kdc101_connected = False
            kdc101 = None  # 연결 실패 시 객체 초기화
        connection_tab.content = get_connection_content()
        page.update()

    def disconnect_kdc101(e=None):
        global kdc101
        nonlocal is_kdc101_connected
        try:
            if kdc101 is not None:
                kdc101.close()
                update_status("KDC101 스테이지 연결 해제 성공")
        except Exception as ex:
            update_status(f"KDC101 스테이지 연결 해제 실패: {ex}")
        is_kdc101_connected = False
        kdc101 = None  # 연결 해제 시 객체 초기화
        connection_tab.content = get_connection_content()
        page.update()

    # Connection Tab Content 생성 함수
    def get_connection_content():
        return ft.Container(
            content=ft.Column([
                ft.Text("연결 제어", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton("전체 Connect", width=140, on_click=connect_all, bgcolor="green" if is_all_connected else "grey"),
                    ft.ElevatedButton("전체 Disconnect", width=140, on_click=disconnect_all, bgcolor="red" if not is_all_connected else "grey"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                ft.Row([
                    ft.ElevatedButton("GL5 Connect", width=140, on_click=connect_gl5, bgcolor="green" if is_gl5_connected else "grey"),
                    ft.ElevatedButton("GL5 Disconnect", width=140, on_click=disconnect_gl5, bgcolor="red" if not is_gl5_connected else "grey"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                ft.Row([
                    ft.ElevatedButton("ETEL stage Connect", width=140, on_click=connect_etel, bgcolor="green" if is_etel_connected else "grey"),
                    ft.ElevatedButton("ETEL stage Disconnect", width=140, on_click=disconnect_etel, bgcolor="red" if not is_etel_connected else "grey"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                ft.Row([
                    ft.ElevatedButton("카메라 Connect", width=140, on_click=connect_camera, bgcolor="green" if is_camera_connected else "grey"),
                    ft.ElevatedButton("카메라 Disconnect", width=140, on_click=disconnect_camera, bgcolor="red" if not is_camera_connected else "grey"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                ft.Row([
                    ft.ElevatedButton("DPIN Connect", width=140, on_click=connect_dpin, bgcolor="green" if is_dpin_connected else "grey"),
                    ft.ElevatedButton("DPIN Disconnect", width=140, on_click=disconnect_dpin, bgcolor="red" if not is_dpin_connected else "grey"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                ft.Row([
                    ft.ElevatedButton("KDC101 Connect", width=140, on_click=connect_kdc101, bgcolor="green" if is_kdc101_connected else "grey"),
                    ft.ElevatedButton("KDC101 Disconnect", width=140, on_click=disconnect_kdc101, bgcolor="red" if not is_kdc101_connected else "grey"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            padding=20
        )

    # connection_tab을 전역 Tab 객체로 생성
    connection_tab = ft.Tab(
        text="연결",
        content=get_connection_content()
    )

    # 검사 결과 표시용 컨테이너(동적으로 내용 변경)
    result_area = ft.Container(
        content=ft.Column(
            [ft.Text("검사 결과가 여기에 표시됩니다.")],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            alignment=ft.MainAxisAlignment.START,  # 왼쪽 위 정렬
            horizontal_alignment=ft.CrossAxisAlignment.START  # 왼쪽 정렬
        ),
        expand=True,
        padding=20
    )

    def on_test_type_change(e):
        selected = test_type_dropdown.value
        # 검사 종류에 따라 검사 항목 필터링
        if selected == "1차 보정검사(공통)":
            inspection_type_dropdown.options = [
                ft.dropdown.Option("빔 사이즈 측정"),
                ft.dropdown.Option("Walk Error 보정(LUT 생성)")
            ]
        elif selected == "2차 보정검사(OHT)":
            inspection_type_dropdown.options = [
                ft.dropdown.Option("수평도 검사"),
                ft.dropdown.Option("홈포지선 검사"),
                ft.dropdown.Option("거리성능 검사"),
                ft.dropdown.Option("OHT filtering LUT 생성"),
                ft.dropdown.Option("OHT filtering 검사"),
                ft.dropdown.Option("Rear cover 감지 검사"),
                ft.dropdown.Option("최대거리 검사")
            ]
        elif selected == "2차 보정검사(OBS)":
            inspection_type_dropdown.options = [
                ft.dropdown.Option("수평도 검사"),
                ft.dropdown.Option("홈포지선 검사"),
                ft.dropdown.Option("거리성능 검사"),
                ft.dropdown.Option("최대거리 검사")
            ]
        inspection_type_dropdown.value = None
        page.update()

    # 검사 함수 템플릿: 검사명 -> (실행 함수, 결과 생성 함수)
    def beam_size_test():
        global global_beam_size_result
        if global_beam_size_result is None:
            return {
                'title': '빔 사이즈 결과',
                'widgets': [ft.Text("빔 사이즈 검사를 실행해주세요.")]
            }
        return {
            'title': '빔 사이즈 결과',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_beam_size_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_beam_size_result.get('test_time', 'N/A')}"),
                ft.Text(f"빔 사이즈: {global_beam_size_result.get('major_axis_length', 'N/A'):.2f} x {global_beam_size_result.get('minor_axis_length', 'N/A'):.2f} mm"),
                ft.Text(f"편심: {global_beam_size_result.get('decenter_horizontal_deg', 'N/A'):.2f}° (수평), {global_beam_size_result.get('decenter_vertical_deg', 'N/A'):.2f}° (수직)"),
                ft.Image(src=global_beam_size_result['output_img_path'], width=600, height=400, fit=ft.ImageFit.CONTAIN)
            ]
        }
    def walk_error_lut_test():
        global global_walk_error_result
        if global_walk_error_result is None:
            return {
                'title': 'Walk Error LUT Results',
                'widgets': [
                    ft.Text("Walk Error LUT 검사를 실행해주세요.")
                ]
            }
        
        def format_table(table_data):
            import numpy as np
            if isinstance(table_data, np.ndarray):
                if table_data.ndim == 1:
                    lines = []
                    for i in range(0, len(table_data), 10):
                        line = ", ".join(f"{int(x):04d}" for x in table_data[i:i+10])
                        lines.append(f"{i:04d}: {line}")
                    return "\n".join(lines)
                elif table_data.ndim == 2:
                    lines = []
                    for idx, row in enumerate(table_data):
                        line = ", ".join(f"{int(x):04d}" for x in row)
                        lines.append(f"[{idx}]: {line}")
                    return "\n".join(lines)
                else:
                    return str(table_data)
            elif isinstance(table_data, list):
                return format_table(np.array(table_data))
            else:
                return str(table_data)
        
        formatted_table = format_table(global_walk_error_result['walk_error_table'])
        
        return {
            'title': 'Walk Error LUT Results',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_walk_error_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_walk_error_result.get('test_time', 'N/A')}"),
                ft.Text("Walk Error Graph", size=16, weight=ft.FontWeight.BOLD),
                ft.Image(src=global_walk_error_result['walk_error_graph_filename'], width=800, height=600, fit=ft.ImageFit.CONTAIN),
                ft.Text("Walk Error Table", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        [ft.Text(formatted_table)],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    border=ft.border.all(1, "grey"),
                    border_radius=8,
                    padding=10,
                    height=200
                )
            ]
        }


    # 검사 함수 템플릿
    def tx_level_test():
        global global_tx_level_result
        if global_tx_level_result is None:
            return {
                'title': '수평도 검사 결과',
                'widgets': [ft.Text("수평도 검사를 실행해주세요.")]
            }
        return {
            'title': '수평도 검사 결과',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_tx_level_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_tx_level_result.get('test_time', 'N/A')}"),
                # 빔 수평도 pass/fail 결과 표시
                ft.Text(f"빔 수평도 Pass/Fail: {global_tx_level_result['tx_level_Pass/Fail']}"),
                # 스캔앵글 별로 수평도 측정 결과 표시
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("스캔 각도")),
                        *[ft.DataColumn(ft.Text(f"{angle}°")) for angle in tx_level_parameters['scan_angles']]
                    ],
                    rows=[
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text("수평도 (deg)")),
                            *[ft.DataCell(ft.Text(f"{global_tx_level_result[angle]['tx_level_in_deg']:.3f}")) for angle in tx_level_parameters['scan_angles']]
                        ])
                    ]
                ),
                ft.Image(src=global_tx_level_result['tx_level_image_path'], width=1200, height=300, fit=ft.ImageFit.CONTAIN)
            ] 
        }

    def home_position_test():
        global global_home_position_result
        if global_home_position_result is None:
            return {
                'title': '홈포지션 검사 결과',
                'widgets': [ft.Text("홈포지션 검사를 실행해주세요.")]
            }
        return {
            'title': '홈포지션 검사 결과',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_home_position_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_home_position_result.get('test_time', 'N/A')}"),
                ft.Text(f"홈포지션 검사 결과: {global_home_position_result['home_position_test_result']}"),
                ft.Text(f"홈포지션 오차: {global_home_position_result['home_position_error']:.3f}[idx]")
            ]
        }

    def distance_performance_test():
        global global_distance_performance_result
        if global_distance_performance_result is None:
            return {
                'title': '거리성능 검사 결과',
                'widgets': [ft.Text("거리성능 검사를 실행해주세요.")]
            }
        
        return {
            'title': '거리성능 검사 결과',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_distance_performance_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_distance_performance_result.get('test_time', 'N/A')}"),
                # 정확도 패스?
                ft.Text(f"정확도 패스: {global_distance_performance_result['accuracy_pass']}"),
                # 정밀도 패스?
                ft.Text(f"정밀도 패스: {global_distance_performance_result['precision_pass']}"),
                # 정밀도 검사 결과 표, 행:스캔각도, 열:검사거리, 값: 정밀도 평가값
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("스캔각도")),
                        ft.DataColumn(ft.Text("검사거리")),
                        ft.DataColumn(ft.Text("정밀도")),
                        ft.DataColumn(ft.Text("정밀도 PASS/FAIL")),
                        ft.DataColumn(ft.Text("정확도")),
                        ft.DataColumn(ft.Text("정확도 PASS/FAIL"))

                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(f"{result['device_angle']}°")),
                                ft.DataCell(ft.Text(f"{result['test_dist']:.3f} m")),
                                ft.DataCell(ft.Text(f"{result['precision']:.3f} m")),
                                ft.DataCell(
                                    ft.Text(
                                        result['precision_pass'],
                                        bgcolor='#f1c40f' if result['precision_pass'] == 'FAIL' else '#ffffff'
                                    )
                                ),
                                ft.DataCell(ft.Text(f"{result['accuracy']:.3f} m")),
                                ft.DataCell(
                                    ft.Text(
                                        result['accuracy_pass'],
                                        bgcolor='#f1c40f' if result['accuracy_pass'] == 'FAIL' else '#ffffff'
                                    )
                                ),
                            ]
                        ) for result in global_distance_performance_result['results']
                    ]
                ),          
            ]
        }
        
    def oht_filtering_lut_generation():
        global global_oht_filtering_lut_result
        if global_oht_filtering_lut_result is None:
            return {
                'title': 'OHT filtering LUT 생성 결과',
                'widgets': [ft.Text("OHT filtering LUT 생성을 실행해주세요.")]
            }
        
        def format_table(table_data):
            import numpy as np
            if isinstance(table_data, np.ndarray):
                if table_data.ndim == 1:
                    lines = []
                    for i in range(0, len(table_data), 10):
                        line = ", ".join(f"{int(x):04d}" for x in table_data[i:i+10])
                        lines.append(f"{i:04d}: {line}")
                    return "\n".join(lines)
                elif table_data.ndim == 2:
                    lines = []
                    for idx, row in enumerate(table_data):
                        line = ", ".join(f"{int(x):04d}" for x in row)
                        lines.append(f"[{idx}]: {line}")
                    return "\n".join(lines)
                else:
                    return str(table_data)
            elif isinstance(table_data, list):
                return format_table(np.array(table_data))
            else:
                return str(table_data)
        
        min_table = format_table(global_oht_filtering_lut_result.get('min_table', []))
        max_table = format_table(global_oht_filtering_lut_result.get('max_table', []))
        
        return {
            'title': 'OHT filtering LUT 생성 결과',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_oht_filtering_lut_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_oht_filtering_lut_result.get('test_time', 'N/A')}"),
                ft.Text("1m 거리 이미지", size=16, weight=ft.FontWeight.BOLD),
                ft.Image(src=global_oht_filtering_lut_result['img_1m_path'], width=1200, height=600, fit=ft.ImageFit.CONTAIN),
                ft.Text("OHT Filtering Table [MIN]", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        [ft.Text(min_table)],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    border=ft.border.all(1, "grey"),
                    border_radius=8,
                    padding=10,
                    width=800,
                    height=200
                ),
                ft.Text("OHT Filtering Table [MAX]", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        [ft.Text(max_table)],
                        scroll=ft.ScrollMode.AUTO
                    ),
                    border=ft.border.all(1, "grey"),
                    border_radius=8,
                    padding=10,
                    width=800,
                    height=200
                )
            ]
        }

    def oht_filtering_test():
        global global_oht_filtering_validation_result
        if global_oht_filtering_validation_result is None:
            return {
                'title': 'OHT filtering 검사 결과',
                'widgets': [ft.Text("OHT filtering 검사를 실행해주세요.")]
            }
        
        max_rows = 20
        return {
            'title': 'OHT filtering 검사 결과',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_oht_filtering_validation_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_oht_filtering_validation_result.get('test_time', 'N/A')}"),
                # 요약 결과
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("타겟 이름")),
                        ft.DataColumn(ft.Text("결과"))
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(target_name)),
                                ft.DataCell(ft.Text('PASS' if target_data['is_passed'] else 'FAIL'))
                            ]
                        ) for target_name, target_data in global_oht_filtering_validation_result.items()
                        if target_name not in ['GL_serial', 'test_time', 'report_path']
                    ]
                ),
                # 상세 결과
                ft.Text("\n미감지 포인트 표", size=20, weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Target")),
                        ft.DataColumn(ft.Text("Distance")),
                        ft.DataColumn(ft.Text("Device Angle")),
                        ft.DataColumn(ft.Text("Pass/Fail"))
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(data['Target'])),
                                ft.DataCell(ft.Text(str(data['Distance']))),
                                ft.DataCell(ft.Text(str(data['Device Angle']))),
                                ft.DataCell(ft.Text(data['Pass/Fail'],
                                                    bgcolor='#f1c40f' if data['Pass/Fail'] == 'FAIL' else '#ffffff'))
                            ]
                        ) for data in [
                            {
                                'Target': target_name,
                                'Distance': data['dist'],
                                'Device Angle': data['device_angle'],
                                'Pass/Fail': 'FAIL'
                            }
                            for target_name, target_data in global_oht_filtering_validation_result.items()
                            if target_name not in ['GL_serial', 'test_time', 'report_path']
                            if isinstance(target_data, dict)
                            for data in target_data.get('data', [])
                            if not data.get('is_passed', False)
                        ][:max_rows]
                    ] + ([ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("이하 생략")),
                            ft.DataCell(ft.Text("상세 데이터")),
                            ft.DataCell(ft.Text("리포트 참조")),
                            ft.DataCell(ft.Text("..."))
                        ]
                    )] if len([data for target_name, target_data in global_oht_filtering_validation_result.items()
                            if target_name not in ['GL_serial', 'test_time', 'report_path']
                            if isinstance(target_data, dict)
                            for data in target_data.get('data', [])
                            if not data.get('is_passed', False)]) > max_rows else [])
                )
            ]
        }

    def rear_cover_detection_test():
        global global_rear_cover_detection_result
        if global_rear_cover_detection_result is None:
            return {
                'title': 'Rear cover 감지 검사 결과',
                'widgets': [ft.Text("Rear cover 감지 검사를 실행해주세요.")]
            }
        
        max_rows = 20
        return {
            'title': 'Rear cover 감지 검사 결과',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_rear_cover_detection_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_rear_cover_detection_result.get('test_time', 'N/A')}"),
                ft.Text(f"Rear cover 평가결과: {global_rear_cover_detection_result.get('result', 'N/A')}"),
                
                # 상세 결과 테이블
                ft.Text("\n미감지 포인트 표", size=20, weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Distance (mm)")),
                        ft.DataColumn(ft.Text("Target Angle (deg)")),
                        ft.DataColumn(ft.Text("Device Angle (deg)")),
                        ft.DataColumn(ft.Text("Status"))
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(f"{float(data.get('test_dist', 'N/A')):.1f}" if data.get('test_dist') != 'N/A' else 'N/A')),
                                ft.DataCell(ft.Text(f"{float(data.get('test_angle', 'N/A')):.1f}" if data.get('test_angle') != 'N/A' else 'N/A')),
                                ft.DataCell(ft.Text(f"{float(data.get('test_device_angle', 'N/A')):.1f}" if data.get('test_device_angle') != 'N/A' else 'N/A')),
                                ft.DataCell(ft.Text('Fail (미감지)'))
                            ]
                        ) for data in global_rear_cover_detection_result.get('fail_datas', [])[:max_rows]
                    ] + ([ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("이하 생략")),
                            ft.DataCell(ft.Text("상세 데이터")),
                            ft.DataCell(ft.Text("리포트 참조")),
                            ft.DataCell(ft.Text("..."))
                        ]
                    )] if len(global_rear_cover_detection_result.get('fail_datas', [])) > max_rows else [])
                )
            ]
        }

    def max_distance_test():
        global global_max_distance_result
        if global_max_distance_result is None:
            return {
                'title': '최대거리 검사 결과',
                'widgets': [ft.Text("최대거리 검사를 실행해주세요.")]
            }
        return {
            'title': '최대거리 검사 결과',
            'widgets': [
                ft.Text(f"GL 시리얼: {global_max_distance_result.get('GL_serial', 'N/A')}"),
                ft.Text(f"테스트 시간: {global_max_distance_result.get('test_time', 'N/A')}"),
                ft.Text(f"최대거리 검사 결과: {global_max_distance_result.get('is_passed', 'N/A')}"),
                
                # 상세 결과 테이블
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("센서각도")),
                        ft.DataColumn(ft.Text("검사 결과")),
                        ft.DataColumn(ft.Text("감지율")),
                        ft.DataColumn(ft.Text("감지 포인트 수")),
                        ft.DataColumn(ft.Text("전체 포인트 수"))
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(str(angle))),
                                ft.DataCell(ft.Text('PASS' if data.get('is_passed', False) else 'FAIL', color='#000000' if data.get('is_passed', False) else '#FF0000')),
                                ft.DataCell(ft.Text(str(data.get('detection_ratio', 'N/A')))),
                                ft.DataCell(ft.Text(str(data.get('cnt', 'N/A')))),
                                ft.DataCell(ft.Text(str(data.get('max_cnt', 'N/A'))))
                            ]
                        ) for angle, data in global_max_distance_result.items()
                        if angle not in ['GL_serial', 'test_time', 'is_passed', 'report_path']
                    ]
                )
            ]
        }

    test_functions = {
        "빔 사이즈 측정": beam_size_test,
        "Walk Error 보정(LUT 생성)": walk_error_lut_test,
        "수평도 검사": tx_level_test,
        "홈포지선 검사": home_position_test,
        "거리성능 검사": distance_performance_test,
        "OHT filtering LUT 생성": oht_filtering_lut_generation,
        "OHT filtering 검사": oht_filtering_test,
        "Rear cover 감지 검사": rear_cover_detection_test,
        "최대거리 검사": max_distance_test
    }

    # 검사 결과 표시 함수
    def update_result_area(test_name):
        if test_name in test_functions:
            result = test_functions[test_name]()
            result_area.content = ft.Column(
                [
                    ft.Text(result['title'], size=18, weight=ft.FontWeight.BOLD),
                    *result['widgets']
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                alignment=ft.MainAxisAlignment.START,  # 왼쪽 위 정렬
                horizontal_alignment=ft.CrossAxisAlignment.START  # 왼쪽 정렬
            )
        else:
            result_area.content = ft.Column(
                [ft.Text("알 수 없는 검사 유형")],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                alignment=ft.MainAxisAlignment.START,  # 왼쪽 위 정렬
                horizontal_alignment=ft.CrossAxisAlignment.START  # 왼쪽 정렬
            )
        page.update()

    # 검사 항목 드롭다운 on_change 이벤트
    def on_inspection_type_change(e):
        selected = inspection_type_dropdown.value
        update_result_area(selected)

    # 왼쪽: 검사 선택/버튼 영역 (드롭다운 컨트롤 분리)
    test_type_dropdown = ft.Dropdown(
        label="검사 종류",
        width=230,
        options=[
            ft.dropdown.Option("1차 보정검사(공통)"),
            ft.dropdown.Option("2차 보정검사(OHT)"),
            ft.dropdown.Option("2차 보정검사(OBS)")
        ],
        on_change=lambda e: on_test_type_change(e)
    )

    inspection_type_dropdown = ft.Dropdown(
        label="검사 항목",
        width=230,
        options=[
            # 검사 종류가 선택되지 않았을경우 검사 항목 목록 비활성화
            # ft.dropdown.Option("빔 사이즈 측정"),
            # ft.dropdown.Option("Walk Error 보정(LUT 생성)"),
            # ft.dropdown.Option("기타 검사")
        ],
        on_change=on_inspection_type_change
    )

    inspection_tab_left = ft.Container( 
        content=ft.Column([
            ft.Text("검사 설정", size=20, weight=ft.FontWeight.BOLD),
            test_type_dropdown,
            inspection_type_dropdown,
            ft.ElevatedButton(
                "검사 시작",
                width=230,
                on_click=lambda e: start_inspection(e)
            ),
        ], spacing=20),
        width=250,
        padding=20
    )

    # 검사 진행 중 상태를 표시하는 함수 추가
    def show_in_progress(test_name):
        loading_message = f"{test_name} 검사가 진행 중입니다..."
        result_area.content = ft.Column(
            [
                ft.Text(loading_message, size=18, weight=ft.FontWeight.BOLD, color="blue"),
                ft.ProgressRing(width=40, height=40),
                ft.Text("잠시만 기다려주세요...", color="blue")
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        page.update()

    # 검사 시작 함수 수정
    def start_inspection(e):
        inspection_type = inspection_type_dropdown.value
        if not inspection_type:
            page.snack_bar = ft.SnackBar(content=ft.Text("검사 항목을 선택해주세요."))
            page.update()
            return

        # 검사 진행 중 표시
        show_in_progress(inspection_type)

        if inspection_type == "빔 사이즈 측정":
            run_beam_size_test()
        elif inspection_type == "Walk Error 보정(LUT 생성)":
            run_walk_error_lut_generation()
        elif inspection_type == "수평도 검사":
            run_tx_level_test()
        elif inspection_type == "홈포지선 검사":
            run_home_position_test()
        elif inspection_type == "거리성능 검사":
            run_distance_performance_test()
        elif inspection_type == "OHT filtering LUT 생성":
            run_oht_filtering_lut_generation()
        elif inspection_type == "OHT filtering 검사":
            run_oht_filtering_test()
        elif inspection_type == "Rear cover 감지 검사":
            run_rear_cover_detection_test()
        elif inspection_type == "최대거리 검사":
            run_max_distance_test()

        update_result_area(inspection_type)

    # 검사탭: 좌우 분할 구조
    inspection_tab = ft.Tab(
        text="검사",
        content=ft.Container(
            content=ft.Row([
                inspection_tab_left,
                result_area
            ]),
            padding=0
        )
    )

    # 최초 진입 시 기본 검사 결과 표시
    update_result_area(inspection_type_dropdown.value or "빔 사이즈 측정")

    # Results Tab
    # 1차 보정검사(공통) 컨테이너
    beam_size_field = ft.TextField(
        label="빔 사이즈 측정 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    walk_error_field = ft.TextField(
        label="Walk Error LUT 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    first_cal_common_container = ft.Column([
        ft.Text("빔 사이즈 측정", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            beam_size_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, beam_size_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("Walk Error 보정(LUT 생성)", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            walk_error_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, walk_error_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
    ], spacing=10)

    # 2차 보정검사(OHT) 컨테이너
    tx_level_field = ft.TextField(
        label="수평도 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    home_position_field = ft.TextField(
        label="홈포지션 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    distance_performance_field = ft.TextField(
        label="거리성능 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    oht_filtering_lut_field = ft.TextField(
        label="OHT filtering LUT 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    oht_filtering_field = ft.TextField(
        label="OHT filtering 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    rear_cover_detection_field = ft.TextField(
        label="Rear cover 감지 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    max_distance_field = ft.TextField(
        label="최대거리 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    second_cal_oht_container = ft.Column([
        ft.Text("수평도 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            tx_level_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, tx_level_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("홈포지션 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            home_position_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, home_position_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("거리성능 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            distance_performance_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, distance_performance_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("OHT filtering LUT 생성", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            oht_filtering_lut_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, oht_filtering_lut_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("OHT filtering 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            oht_filtering_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, oht_filtering_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("Rear cover 감지 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            rear_cover_detection_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, rear_cover_detection_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("최대거리 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            max_distance_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, max_distance_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
    ], spacing=10)

    # 2차 보정검사(OBS) 컨테이너
    tx_level_obs_field = ft.TextField(
        label="수평도 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    home_position_obs_field = ft.TextField(
        label="홈포지션 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    distance_performance_obs_field = ft.TextField(
        label="거리성능 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    max_distance_obs_field = ft.TextField(
        label="최대거리 검사 결과 경로",
        width=350,
        read_only=True,
        value=""
    )
    second_cal_obs_container = ft.Column([
        ft.Text("수평도 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            tx_level_obs_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, tx_level_obs_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("홈포지션 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            home_position_obs_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, home_position_obs_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("거리성능 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            distance_performance_obs_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, distance_performance_obs_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Text("최대거리 검사", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([
            max_distance_obs_field,
            ft.ElevatedButton(
                "파일 열기",
                width=100,
                on_click=lambda e: pick_file_for(e, max_distance_obs_field)
            ),
        ], alignment=ft.MainAxisAlignment.START),
    ], spacing=10)

    # 컨테이너를 담을 전역 변수
    report_content_container = ft.Container(
        content=first_cal_common_container,  # 기본값으로 1차 보정검사 표시
        padding=20
    )

    # 리포트 종류 선택 드롭다운
    report_type_dropdown = ft.Dropdown(
        label="검사 종류",
        width=230,
        options=[
            ft.dropdown.Option("1차 보정검사(공통)"),
            ft.dropdown.Option("2차 보정검사(OHT)"),
            ft.dropdown.Option("2차 보정검사(OBS)")
        ],
        value="1차 보정검사(공통)",  # 기본값 설정
        on_change=lambda e: update_report_content(e)
    )

    # 검사 종류에 따라 내용 업데이트하는 함수
    def update_report_content(e):
        selected = e.control.value
        if selected == "1차 보정검사(공통)":
            report_content_container.content = first_cal_common_container
        elif selected == "2차 보정검사(OHT)":
            report_content_container.content = second_cal_oht_container
        elif selected == "2차 보정검사(OBS)":
            report_content_container.content = second_cal_obs_container
        page.update()

    # 리포트 생성 버튼
    report_generate_button = ft.ElevatedButton(
        "리포트 생성",
        width=140,
        on_click=lambda e: generate_report(e)
    )

    # 리포트 생성 함수
    def generate_report(e):
        report_type = report_type_dropdown.value
        update_status(f"{report_type} 리포트 생성")


        file_path_list = {}
        if report_type == "1차 보정검사(공통)":
            file_path_list['beam_size_result_fname'] = beam_size_field.value
            file_path_list['walkerror_result_fname'] = walk_error_field.value

            from functions.report_1st_cal_and_test import run as generate_report_1st_cal_common            
            save_parameters = {
                'save_path': './log/1st_cal_and_test/',
            }
            generate_report_1st_cal_common(file_path_list, save_parameters)

        elif report_type == "2차 보정검사(OHT)":
            file_path_list['tx_level_result_fname'] = tx_level_field.value
            file_path_list['home_position_result_fname'] = home_position_field.value
            file_path_list['distance_test_result_fname'] = distance_performance_field.value
            file_path_list['oht_filtering_table_result_fname'] = oht_filtering_lut_field.value
            file_path_list['oht_filtering_validation_result_fname'] = oht_filtering_field.value
            file_path_list['rear_cover_result_fname'] = rear_cover_detection_field.value
            file_path_list['max_dist_result_fname'] = max_distance_field.value

            from functions.report_2nd_cal_and_test_OHT import run as generate_report_2nd_cal_oht
            save_parameters = {
                'save_path': './log/2nd_cal_and_test_OHT/',
            }
            generate_report_2nd_cal_oht(file_path_list, save_parameters)

        elif report_type == "2차 보정검사(OBS)":
            file_path_list['tx_level_result_fname'] = tx_level_obs_field.value
            file_path_list['home_position_result_fname'] = home_position_obs_field.value
            file_path_list['distance_test_result_fname'] = distance_performance_obs_field.value
            file_path_list['max_dist_result_fname'] = max_distance_obs_field.value

            from functions.report_2nd_cal_and_test_OBS import run as generate_report_2nd_cal_obs
            save_parameters = {
                'save_path': './log/2nd_cal_and_test_OBS/',
            }
            generate_report_2nd_cal_obs(file_path_list, save_parameters)

        update_status(f"{report_type} 리포트 생성 완료")
        page.update()

    # Results Tab 구성
    results_tab = ft.Tab(
        text="리포트",
        content=ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("검사 설정", size=20, weight=ft.FontWeight.BOLD),
                        report_type_dropdown,
                    ], spacing=20),
                    width=250,
                    padding=20
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("검사 항목 경로", size=20, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Column([
                                report_content_container,
                            ],
                            scroll=ft.ScrollMode.AUTO
                            ),
                            height=500,
                            expand=True,
                            border=ft.border.all(1, "#E0E0E0"),
                            border_radius=8,
                            padding=10,
                        ),
                        report_generate_button
                    ], spacing=20),
                    padding=20,
                    expand=True
                )
            ]),
            padding=20
        )
    )

    # 상태 메시지용 Text 컨트롤 생성 (하단 상태창)
    status_text = ft.Text("", size=14, color="blue")
    status_history = []  # 상태 메시지 히스토리를 저장할 리스트

    def update_status(message):
        nonlocal status_history
        status_history.append(message)
        if len(status_history) > 500:  # 최대 500개 메시지 유지
            status_history.pop(0)
        status_text.value = "\n".join(status_history)
        # 스크롤을 맨 아래로 이동
        status_container.content.scroll_to(offset=1000, duration=100)
        page.update()

    # --- ETEL Stage Section ---
    linear_target_field = ft.TextField(label="Linear target (mm)", width=150, value="0")
    linear_target_speed_field = ft.TextField(label="Linear target speed (mm/s)", width=150, value="400")
    rotate_target_field = ft.TextField(label="Rotate target (deg)", width=150, value="0")
    rotate_target_speed_field = ft.TextField(label="Rotate target speed (deg/s)", width=150, value="50")
    rotate_device_field = ft.TextField(label="Rotate device (deg)", width=150, value="0")
    rotate_device_speed_field = ft.TextField(label="Rotate device speed (deg/s)", width=150, value="30")

    def move_linear_target(e):
        if not is_etel_connected:
            update_status("ETEL stage가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            value = float(linear_target_field.value)
            speed = float(linear_target_speed_field.value)
            
            if value < 0:
                value = 0
                linear_target_field.value = "0"
                update_status("0mm 미만은 0mm로 자동 보정되었습니다.")
            elif value > 5000:
                value = 5000
                linear_target_field.value = "5000"
                update_status("5000mm 초과는 5000mm로 자동 보정되었습니다.")
                
            if speed < 0:
                speed = 0
                linear_target_speed_field.value = "0"
                update_status("속도 0mm/s 미만은 0mm/s로 자동 보정되었습니다.")
            elif speed > 400:
                speed = 400
                linear_target_speed_field.value = "400"
                update_status("속도 400mm/s 초과는 400mm/s로 자동 보정되었습니다.")
            
            stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, value, speed)
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                time.sleep(0.2)
            update_status(f"Linear target {value}mm 이동 완료 (속도: {speed}mm/s)")
        except Exception as ex:
            update_status(f"Linear target 이동 실패: {ex}")
        page.update()

    def home_linear_target(e):
        if not is_etel_connected:
            update_status("ETEL stage가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            if ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
                update_status("Linear target 홈서치 성공")
            else:
                update_status("Linear target 홈서치 실패")
        except Exception as ex:
            update_status(f"Linear target 홈서치 실패: {ex}")
        page.update()

    def move_rotate_target(e):
        if not is_etel_connected:
            update_status("ETEL stage가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            value = float(rotate_target_field.value)
            speed = float(rotate_target_speed_field.value)
            
            if value < -360:
                value = -360
                rotate_target_field.value = "-360"
                update_status("-360deg 미만은 -360deg로 자동 보정되었습니다.")
            elif value > 360:
                value = 360
                rotate_target_field.value = "360"
                update_status("360deg 초과는 360deg로 자동 보정되었습니다.")
                
            if speed < 0:
                speed = 0
                rotate_target_speed_field.value = "0"
                update_status("속도 0deg/s 미만은 0deg/s로 자동 보정되었습니다.")
            elif speed > 100:
                speed = 100
                rotate_target_speed_field.value = "100"
                update_status("속도 100deg/s 초과는 100deg/s로 자동 보정되었습니다.")
            
            stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, value, speed)
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
                time.sleep(0.2)
            update_status(f"Rotate target {value}deg 이동 완료 (속도: {speed}deg/s)")
        except Exception as ex:
            update_status(f"Rotate target 이동 실패: {ex}")
        page.update()

    def home_rotate_target(e):
        if not is_etel_connected:
            update_status("ETEL stage가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            if ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
                update_status("Rotate target 홈서치 성공")
            else:
                update_status("Rotate target 홈서치 실패")
        except Exception as ex:
            update_status(f"Rotate target 홈서치 실패: {ex}")
        page.update()

    def move_rotate_device(e):
        if not is_etel_connected:
            update_status("ETEL stage가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            value = float(rotate_device_field.value)
            speed = float(rotate_device_speed_field.value)
            
            if value < -135:
                value = -135
                rotate_device_field.value = "-135"
                update_status("-135deg 미만은 -135deg로 자동 보정되었습니다.")
            elif value > 135:
                value = 135
                rotate_device_field.value = "135"
                update_status("135deg 초과는 135deg로 자동 보정되었습니다.")
                
            if speed < 0:
                speed = 0
                rotate_device_speed_field.value = "0"
                update_status("속도 0deg/s 미만은 0deg/s로 자동 보정되었습니다.")
            elif speed > 30:
                speed = 30
                rotate_device_speed_field.value = "30"
                update_status("속도 30deg/s 초과는 30deg/s로 자동 보정되었습니다.")
            
            stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, value, speed)
            while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
                time.sleep(0.2)
            update_status(f"Rotate device {value}deg 이동 완료 (속도: {speed}deg/s)")
        except Exception as ex:
            update_status(f"Rotate device 이동 실패: {ex}")
        page.update()

    def home_rotate_device(e):
        if not is_etel_connected:
            update_status("ETEL stage가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            if ETEL.search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
                update_status("Rotate device 홈서치 성공")
            else:
                update_status("Rotate device 홈서치 실패")
        except Exception as ex:
            update_status(f"Rotate device 홈서치 실패: {ex}")
        page.update()

    etel_section = ft.Container(
        content=ft.Column([
            ft.Text("ETEL Stage", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                linear_target_field,
                linear_target_speed_field,
                ft.ElevatedButton("Move", on_click=move_linear_target),
                ft.ElevatedButton("Home", on_click=home_linear_target)
            ], spacing=10),
            ft.Row([
                rotate_target_field,
                rotate_target_speed_field,
                ft.ElevatedButton("Move", on_click=move_rotate_target),
                ft.ElevatedButton("Home", on_click=home_rotate_target)
            ], spacing=10),
            ft.Row([
                rotate_device_field,
                rotate_device_speed_field,
                ft.ElevatedButton("Move", on_click=move_rotate_device),
                ft.ElevatedButton("Home", on_click=home_rotate_device)
            ], spacing=10),
        ], spacing=10),
        padding=10,
        border=ft.border.all(1, "grey"),
        border_radius=8
    )

    # --- DPIN Gonio Stage Section ---
    tilt_device_field = ft.TextField(label="Tilt device (deg)", width=150, value="0")

    def move_tilt_device(e):
        if not is_dpin_connected:
            update_status("DPIN stage가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            value = float(tilt_device_field.value)
            if value < -15:
                value = -15
                tilt_device_field.value = "-15"
                update_status("-15deg 미만은 -15deg로 자동 보정되었습니다.")
            elif value > 15:
                value = 15
                tilt_device_field.value = "15"
                update_status("15deg 초과는 15deg로 자동 보정되었습니다.")
            
            dpin.move_to_angle(value)
            while dpin.is_moving():
                time.sleep(0.1)
            current_angle = dpin.read_cur_deg()
            update_status(f"Tilt device {value}deg 이동 완료 (현재: {current_angle:.2f}deg)")
        except Exception as ex:
            update_status(f"Tilt device 이동 실패: {ex}")
        page.update()

    def home_tilt_device(e):
        if not is_dpin_connected:
            update_status("DPIN stage가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            dpin.searching_home()
            current_angle = dpin.read_cur_deg()
            update_status(f"Tilt device 홈서치 완료 (현재: {current_angle:.2f}deg)")
        except Exception as ex:
            update_status(f"Tilt device 홈서치 실패: {ex}")
        page.update()

    dpin_section = ft.Container(
        content=ft.Column([
            ft.Text("DPIN Gonio Stage", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                tilt_device_field,
                ft.ElevatedButton("Move", on_click=move_tilt_device),
                ft.ElevatedButton("Home", on_click=home_tilt_device)
            ], spacing=10),
        ], spacing=10),
        padding=10,
        border=ft.border.all(1, "grey"),
        border_radius=8
    )

    # --- KDC101 Stage Section ---
    kdc101_position_field = ft.TextField(label="Position (mm)", width=150, value="0")
    kdc101_speed_field = ft.TextField(label="Speed (mm/s)", width=150, value="2.4")

    def move_kdc101(e):
        if not is_kdc101_connected:
            update_status("KDC101 스테이지가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            position = float(kdc101_position_field.value)
            speed = float(kdc101_speed_field.value)
            
            # 속도 범위 체크 및 보정
            if speed < 0:
                speed = 0
                kdc101_speed_field.value = "0"
                update_status("속도 0mm/s 미만은 0mm/s로 자동 보정되었습니다.")
            elif speed > 2.4:
                speed = 2.4
                kdc101_speed_field.value = "2.4"
                update_status("속도 2.4mm/s 초과는 2.4mm/s로 자동 보정되었습니다.")
            
            kdc101.set_velocity(spd_mmps=speed)
            kdc101.move(position)
            while kdc101.is_moving():
                time.sleep(0.1)
            update_status(f"KDC101 스테이지 {position}mm 이동 완료 (속도: {speed}mm/s)")
        except Exception as ex:
            update_status(f"KDC101 스테이지 이동 실패: {ex}")
        page.update()

    def home_kdc101(e):
        if not is_kdc101_connected:
            update_status("KDC101 스테이지가 연결되어 있지 않습니다.")
            page.update()
            return
            
        try:
            kdc101.home_search()
            update_status("KDC101 스테이지 홈서치 완료")
        except Exception as ex:
            update_status(f"KDC101 스테이지 홈서치 실패: {ex}")
        page.update()

    kdc101_section = ft.Container(
        content=ft.Column([
            ft.Text("KDC101 Stage", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                kdc101_position_field,
                kdc101_speed_field,
                ft.ElevatedButton("Move", on_click=move_kdc101),
                ft.ElevatedButton("Home", on_click=home_kdc101)
            ], spacing=10),
        ], spacing=10),
        padding=10,
        border=ft.border.all(1, "grey"),
        border_radius=8
    )

    # 수동 조작 탭: 세 section을 세로로 배치
    manual_tab = ft.Tab(
        text="수동 조작",
        content=ft.Container(
            content=ft.Column([
                etel_section,
                dpin_section,
                kdc101_section  # KDC101 섹션 추가
            ], spacing=20),
            padding=20
        )
    )

    # Settings Tab
    settings_tab = ft.Tab(
        text="설정",
        content=ft.Container(
            content=ft.Column([
                ft.ExpansionTile(
                    title=ft.Text("연결 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                sensor_ip_field,
                                sensor_port_field,
                                pc_ip_field,
                                pc_port_field,
                                etel_ip_field,
                                dpin_ip_field,
                                dpin_port_field,
                                etel_stage_offset_field,
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("빔 사이즈 측정 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                camera_fps_field,
                                camera_acq_field,
                                oht_exp_field,
                                obs_exp_field,
                                oht_angle_field,
                                obs_angle_field,
                                test_dist_field,
                                pass_criteria_field,
                                threshold_dropdown,
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("Walk Error 보정 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                walk_error_stage_dist_field,
                                speed_conditions_field,
                                OHT_ld_high_voltage_field,
                                OHT_pd_high_voltage_field,
                                OHT_BR_intensity_field,
                                OBS_ld_high_voltage_field,
                                OBS_pd_high_voltage_field,
                                OBS_BR_intensity_field
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("수평도 검사 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                tx_level_ld_hv_field,
                                tx_level_obs_exp_field,
                                tx_level_oht_exp_field,
                                tx_level_camera_fps_field,
                                tx_level_camera_acq_field,
                                tx_level_obs_angle_field,
                                tx_level_oht_angle_field,
                                tx_level_linear_dist_field,
                                tx_level_scan_angles_field,
                                tx_level_roi_y_field,
                                tx_level_roi_x_field,
                                tx_level_binary_threshold_field,
                                tx_level_origin_px_field,
                                tx_level_px2mm_gain_field,
                                tx_level_pass_criteria_field
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("홈 포지션 검사 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                home_position_oht_angle_field,
                                home_position_obs_angle_field,
                                # home_position_device_rotation_speed_field,
                                home_position_test_distance_field,
                                # home_position_device_angle_field,
                                home_position_logging_frame_num_field,
                                # home_position_frame_size_field,
                                home_position_pass_criteria_field
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("거리 성능 검사 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                distance_performance_oht_target_angle_field,
                                distance_performance_obs_target_angle_field,
                                # distance_performance_device_rotation_speed_field,
                                # distance_performance_linear_stage_offset_field,
                                distance_performance_oht_cal_dist_points_field,
                                distance_performance_obs_cal_dist_points_field,
                                distance_performance_oht_test_dist_points_field,
                                distance_performance_obs_test_dist_points_field,
                                distance_performance_logging_frame_num_field,
                                distance_performance_roi_width_field,
                                distance_performance_precision_pass_criteria_field,
                                distance_performance_accuracy_pass_criteria_field
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("OHT Filtering LUT 생성 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                OHT_filtering_table_generation_roi_width_field,
                                OHT_filtering_table_generation_extrapolation_points_field,
                                OHT_filtering_table_generation_measurement_cond_field
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("OHT filtering 검사 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                OHT_filtering_validation_validation_cond_field,
                                OHT_filtering_validation_validation_area_path_field,
                                OHT_filtering_validation_empty_area_path_field
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("Rear Cover 감지 검사 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                rear_cover_detection_test_cond_field,
                                rear_cover_detection_test_area_path_field,
                                rear_cover_detection_empty_area_path_field
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.ExpansionTile(
                    title=ft.Text("최대 거리 검사 설정", size=16, weight=ft.FontWeight.BOLD),
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                max_distance_test_angle_field,
                                max_distance_roi_width_field,
                                max_distance_logging_frame_num_field,
                                max_distance_detection_ratio_criteria_field
                            ], spacing=10),
                            padding=10
                        )
                    ]
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "설정 저장",
                        width=140,
                        on_click=save_settings_to_json
                    ),
                    ft.ElevatedButton(
                        "설정 불러오기",
                        width=140,
                        on_click=load_settings_from_json
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            height=600
            ),
            padding=20
        )
    )

    # 페이지에 추가할 때 스크롤 가능한 컨테이너로 감싸기
    status_container = ft.Container(
        content=ft.Column([
            status_text
        ], scroll=ft.ScrollMode.AUTO),
        height=80,  # 5줄 정도의 높이로 조정
        border=ft.border.all(1, "grey"),
        border_radius=8,
        padding=5,  # 패딩도 줄임
        alignment=ft.alignment.center_left  # 텍스트를 왼쪽 정렬
    )

    # Create the Tabs object once and add it to the page at the end
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[settings_tab, connection_tab, inspection_tab, results_tab, manual_tab],
        expand=1
    )
    page.add(tabs)
    page.add(status_container)

    # main 함수 내에서 start_inspection 함수 바로 이전에 다음 함수들을 추가합니다.

    # 빔 사이즈 테스트 함수 수정
    def run_beam_size_test():
        # GL5, ETEL, DPIN, camera 연결 이후에만 시행하도록 조건 추가
        if not is_gl5_connected or not is_etel_connected or not is_dpin_connected or not is_camera_connected:
            update_status("GL5, ETEL, DPIN, camera 연결 이후에 시행해주세요.")
            page.update()
            return
        
        update_status("빔 사이즈 측정 검사를 시작합니다...")

        raw_data, result = beam_size_run(devices, loaded_beam_size)
        test_name = 'beam_size_test'
        path = f"./log/{test_name}"
        filename = f"{raw_data['GL_serial']}_" + f'{raw_data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(raw_data, path, filename)

        filename = f"{raw_data['GL_serial']}_" + f'{raw_data["test_time"]}' + f'{test_name}_procdata'
        util_yy.save_pickle_to_zip(result, path, filename)
        result['report_path'] = os.path.join(path, f"{filename}.zip")
        # 리포트탭 경로 자동 할당
        beam_size_field.value = result['report_path']
        page.update()
        
        # save image    
        filename = f"{raw_data['GL_serial']}_" + f'{raw_data["test_time"]}' + f'{test_name}'  # 확장자 없이
        filename = f"{path}/{filename}_beam_size.png"
        cv2.imwrite(filename, result['ellipse_img'])

        result['output_img_path'] = filename

        global global_beam_size_result
        global_beam_size_result = result
        update_status("Beam Size Test 완료")

    # Walk Error LUT 생성 함수 수정
    def run_walk_error_lut_generation():
        # KDC101 및 GL5 연결 이후에만 시행하도록 조건 추가
        if not is_kdc101_connected or not is_gl5_connected:
            update_status("KDC101 및 GL5 연결 이후에 시행해주세요.")
            page.update()
            return
        
        update_status("Walk Error LUT 생성을 시작합니다...")
        
        devices['walk_error_stage'] = kdc101
        walk_error_rawdata = walk_error_run(devices, loaded_walk_error)
        
        test_name = 'walk_error'
        path = f"./log/{test_name}"
        save_filename = f"{walk_error_rawdata['GL_serial']}_" + f'{walk_error_rawdata["test_time"]}' + f'_{test_name}_rawdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(walk_error_rawdata, path, save_filename)

        base_filename = f"{walk_error_rawdata['GL_serial']}_" + f'{walk_error_rawdata["test_time"]}'
        graph_filename = f'{path}/{base_filename}.png'
        walk_error_table_filename = f'{path}/{base_filename}.csv'
        walk_error_proc_filename = f"{path}/{base_filename}_walkerror_proc_data.zip"

        save_path = f'{path}/{save_filename}.zip'
        walk_error_result = walk_error_analysis(save_path, walk_error_table_filename, graph_filename, walk_error_proc_filename, 400)

        kdc101.set_velocity(spd_mmps=4.0)
        kdc101.move(target_pos=0.0)

        success, walk_error_lut = GL5_developer.getWalkErrorLUTFromFile(
            walk_error_table_filename
        )
        if success:
            update_status("Successfully loaded the walk_error_lut from file")
        else:
            update_status("Unable to load the walk_error_lut from file")
        page.update()

        success = GL5_developer.setWalkErrorLUTToSensor(GL5_core, walk_error_lut)
        if success:
            update_status("Successfully set the walk_error_lut to sensor")
        else:
            update_status("Unable to set the walk_error_lut to sensor")
        page.update()
        
        walk_error_result['report_path'] = walk_error_proc_filename

        global global_walk_error_result
        global_walk_error_result = walk_error_result
        update_status("Walk Error LUT 생성 완료 및 결과 전역 변수 저장")

        # 리포트탭 경로 자동 할당
        walk_error_field.value = walk_error_result['report_path']
        page.update()

    def run_tx_level_test():
        # GL5, ETEL, DPIN, camera 연결 이후에만 시행하도록 조건 추가
        if not is_gl5_connected or not is_etel_connected or not is_dpin_connected or not is_camera_connected:
            update_status("GL5, ETEL, DPIN, camera 연결 이후에 시행해주세요.")
            page.update()
            return
        
        update_status("수평도 검사를 시작합니다...")

        rawdata, tx_level_result = tx_level_run(devices, loaded_tx_level)

        base_filename = f"{rawdata['GL_serial']}_" + f'{rawdata["test_time"]}'
        path = "./log/tx_level"
        tx_level_image_path = f"{path}/{base_filename}.png"  # 저장할 이미지 경로
        rawdata_name = f"{base_filename}_raw"
        processed_data_name = f"{base_filename}_processed"

        # ZIP 파일에 pickle 데이터 압축하여 저장하기
        util_yy.save_pickle_to_zip(rawdata, path, rawdata_name)
        util_yy.save_pickle_to_zip(tx_level_result, path, processed_data_name)

        cv2.imwrite(tx_level_image_path, tx_level_result['line_image'])
        
        result_path = os.path.join(path, f"{processed_data_name}.zip")
        tx_level_result['report_path'] = result_path
        tx_level_result['tx_level_image_path'] = tx_level_image_path

        global global_tx_level_result
        global_tx_level_result = tx_level_result

        # 검사 종류에 따라 결과 필드 업데이트
        if test_type_dropdown.value == "2차 보정검사(OHT)":
            tx_level_field.value = result_path
        elif test_type_dropdown.value == "2차 보정검사(OBS)":
            tx_level_obs_field.value = result_path
        page.update()
        update_status("수평도 검사 완료 및 결과 경로 자동 할당")

    def run_home_position_test():
        # GL5, ETEL, DPIN 연결 이후에만 시행하도록 조건 추가
        if not is_gl5_connected or not is_etel_connected or not is_dpin_connected:
            update_status("GL5, ETEL, DPIN 연결 이후에 시행해주세요.")
            page.update()
            return
        
        update_status("홈포지션 검사를 시작합니다...")

        data, result = home_position_run(devices, loaded_home_position)
        
        test_name = 'home_position'
        path = f"./log/{test_name}"
        filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(data, path, filename)

        filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(result, path, filename)
        result['report_path'] = f'{path}/{filename}.zip'

        filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_report.txt'  # 확장자 없이
        np.savetxt(f'{path}/{filename}', [f'homepositon result is {result["home_position_error"]:.3f}[idx]'], fmt ='%s')

        # 리포트탭 경로 자동 할당
        if test_type_dropdown.value == "2차 보정검사(OHT)":
            home_position_field.value = result['report_path']
        elif test_type_dropdown.value == "2차 보정검사(OBS)":
            home_position_obs_field.value = result['report_path']
        page.update()

        global global_home_position_result
        global_home_position_result = result

        update_status(f"홈포지션 검사 완료: {result['home_position_test_result']} (홈포지션 오차: {result['home_position_error']:.3f}[idx])")

    def run_distance_performance_test():
        # GL5, ETEL, DPIN 연결 이후에만 시행하도록 조건 추가
        if not is_gl5_connected or not is_etel_connected or not is_dpin_connected:
            update_status("GL5, ETEL, DPIN 연결 이후에 시행해주세요.")
            page.update()
            return     
        
        success, GL_serial = GL5_user.getSerialNum(GL5_core)
        if success:
            print(f"Serial_num = {GL_serial}")
        else:
            print("Unable to get a serial number")

        model_name = GL_serial[4:6]
        print(f"Model name: {model_name}")
        if (model_name == '1W' or
                model_name == '1V'):
            test_cond = loaded_distance_performance['oht_cal_dist_points']
        elif (model_name == '1N' or
                model_name == '1M' or
                model_name == '1R' or
                model_name == '2N'):
            test_cond = loaded_distance_performance['obs_cal_dist_points']
        else:
            raise ValueError('Unknown sensor type')
        
        devices['test_dist'] = test_cond
        _, outputs = distance_performance_run(devices, loaded_distance_performance)
            
        success, back_reflector_distance_target = GL5_developer.getBackReflectorDistanceTarget(GL5_core)
        if success:
            print(f"old back_reflector_distance_target = {back_reflector_distance_target}")
            print(f"distance_offset_compensation = {outputs['distance_offset_compensation']}")
            back_reflector_distance_target = int(back_reflector_distance_target -
                                                outputs['distance_offset_compensation'])
            print('new back_reflector_distance_target =', back_reflector_distance_target)
            success = GL5_developer.setBackReflectorDistanceTarget(GL5_core,
                                                                   back_reflector_distance_target)
            if success:
                print(f"Successfully set the back_reflector_distance_target({int(back_reflector_distance_target)})")
            else:
                print("Unable to set the back_reflector_distance_target")
        else:
            print("Unable to get the back_reflector_distance_target")
        
        if (model_name == '1W' or
            model_name == '1V'):
            test_cond = loaded_distance_performance['oht_test_dist_points']
        elif (model_name == '1N' or
                model_name == '1M' or
                model_name == '1R' or
                model_name == '2N'):
            test_cond = loaded_distance_performance['obs_test_dist_points']
        else:
            raise ValueError('Unknown sensor type')
        
        devices['test_dist'] = test_cond
        raw_data, outputs = distance_performance_run(devices, loaded_distance_performance)
        
        test_name = 'distance_test'
        path = f"./log/{test_name}"
        filename = f"{raw_data['GL_serial']}_" + f'{raw_data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(raw_data, path, filename)

        filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(outputs, path, filename)        
        outputs['report_path'] = f'{path}/{filename}.zip'

        filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_report'  # 확장자 없이
        distance_result_path = f"{path}/{filename}.xlsx"

        from functions.distance_offset_and_test_v2 import save_to_excel
        save_to_excel(outputs, distance_result_path)

        # 전체 결과에 대한 accuracy_pass와 precision_pass 계산
        accuracy_pass_values = [result['accuracy_pass'] for result in outputs['results'] if 'accuracy_pass' in result]
        outputs['accuracy_pass'] = 'PASS' if all(p == 'PASS' for p in accuracy_pass_values) else 'FAIL'
        
        precision_pass_values = [result['precision_pass'] for result in outputs['results'] if 'precision_pass' in result]
        outputs['precision_pass'] = 'PASS' if all(p == 'PASS' for p in precision_pass_values) else 'FAIL'

        global global_distance_performance_result
        global_distance_performance_result = outputs
        
        # 검사 종류에 따라 결과 필드 업데이트
        if test_type_dropdown.value == "2차 보정검사(OHT)":
            distance_performance_field.value = outputs['report_path']
        elif test_type_dropdown.value == "2차 보정검사(OBS)":
            distance_performance_obs_field.value = outputs['report_path']
        page.update()
        update_status("거리성능 검사 완료 및 결과 경로 자동 할당")

    def run_oht_filtering_lut_generation():
        # GL5, ETEL, DPIN 연결 이후에만 시행하도록 조건 추가
        if not is_gl5_connected or not is_etel_connected or not is_dpin_connected:
            update_status("GL5, ETEL, DPIN 연결 이후에 시행해주세요.")
            page.update()
            return    
        
        update_status("OHT filtering LUT 생성을 시작합니다...")
        data, result = OHT_filtering_table_generation_run(devices, loaded_OHT_filtering_table_generation)
        test_name = 'OHT_filtering_table'
        path = f"./log/{test_name}"
        filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(data, path, filename)

        filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(result, path, filename)
        result['report_path'] = f'{path}/{filename}.zip'

        # 1m, 5m 이미지 저장
        filename = f"{data['GL_serial']}_" + f'{data["test_time"]}' + f'{test_name}_1m.png'
        plt.imsave(f'{path}/{filename}', result['img_1m'])
        result['img_1m_path'] = f'{path}/{filename}'
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
                update_status("Successfully set the min/max_pulse_width_lut to sensor")
            else:
                update_status("Unable to set the min/max_pulse_width_lut to sensor")
        else:
            update_status("Unable to load the min/max_pulse_width_lut from file")

        global global_oht_filtering_lut_result
        global_oht_filtering_lut_result = result
        oht_filtering_lut_field.value = result['report_path']
        page.update()
        update_status("OHT filtering LUT 생성 완료 및 결과 경로 자동 할당")

    def run_oht_filtering_test():
        # GL5, ETEL, DPIN 연결 이후에만 시행하도록 조건 추가
        if not is_gl5_connected or not is_etel_connected or not is_dpin_connected:
            update_status("GL5, ETEL, DPIN 연결 이후에 시행해주세요.")
            page.update()
            return
        
        update_status("OHT filtering 검사를 시작합니다...")
        
        raw_data, outputs = OHT_filtering_validation_run(devices, loaded_OHT_filtering_validation)

        test_name = 'oht_filtering_validation'
        path = f"./log/{test_name}"
        filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(raw_data, path, filename)

        filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(outputs, path, filename)
        outputs['report_path'] = f'{path}/{filename}.zip'

        filename = f"{outputs['GL_serial']}_" + f'{outputs["test_time"]}' + '_OHT_filtering_valid_report'
        from functions.OHT_filtering_validation import create_fail_report as create_fail_report_oht_filtering_validation
        create_fail_report_oht_filtering_validation(outputs, f"{path}/{filename}.xlsx")
        
        global global_oht_filtering_validation_result
        global_oht_filtering_validation_result = outputs
        oht_filtering_field.value = outputs['report_path']
        page.update()
        update_status("OHT filtering 검사 완료 및 결과 경로 자동 할당")

    def run_rear_cover_detection_test():
        # GL5, ETEL, DPIN 연결 이후에만 시행하도록 조건 추가
        if not is_gl5_connected or not is_etel_connected or not is_dpin_connected:
            update_status("GL5, ETEL, DPIN 연결 이후에 시행해주세요.")
            page.update()
            return
        
        update_status("Rear cover 감지 검사를 시작합니다...")

        results = rear_cover_detection_run(devices, loaded_rear_cover_detection)
        
        test_name = 'rear_cover_test'
        path = f"./log/{test_name}"
        filename = f"{results['GL_serial']}_" + f'{results["test_time"]}' + f'{test_name}_data'  # 확장자 없이
        util_yy.save_pickle_to_zip(results, path, filename)
        results['report_path'] = f'{path}/{filename}.zip'

        filename = f"{results['GL_serial']}_" + f'{results["test_time"]}' + f'{test_name}_report'  # 확장자 없이
        from functions.rear_cover_test import create_fail_report as create_fail_report_rear_cover_test
        create_fail_report_rear_cover_test(results, f"{path}/{filename}.xlsx")

        global global_rear_cover_detection_result
        global_rear_cover_detection_result = results
        rear_cover_detection_field.value = results['report_path']
        page.update()
        update_status("Rear cover 감지 검사 완료 및 결과 경로 자동 할당")

    def run_max_distance_test():
        # GL5, ETEL, DPIN 연결 이후에만 시행하도록 조건 추가
        if not is_gl5_connected or not is_etel_connected or not is_dpin_connected:
            update_status("GL5, ETEL, DPIN 연결 이후에 시행해주세요.")
            page.update()
            return
        
        update_status("최대거리 검사를 시작합니다...")

        raw_data, results = max_distance_run(devices, loaded_max_distance)
        
        test_name = 'max_dist'
        path = f"./log/{test_name}"
        filename = f"{raw_data['GL_serial']}_" + f'{raw_data["test_time"]}' + f'{test_name}_rawdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(raw_data, path, filename)

        filename = f"{raw_data['GL_serial']}_" + f'{raw_data["test_time"]}' + f'{test_name}_procdata'  # 확장자 없이
        util_yy.save_pickle_to_zip(results, path, filename)
        results['report_path'] = f'{path}/{filename}.zip'

        from functions.max_dist import make_report as make_report_max_distance
        make_report_max_distance(raw_data, results, save_dir=path)
        
        global global_max_distance_result
        global_max_distance_result = results
        
        # 검사 종류에 따라 결과 필드 업데이트
        if test_type_dropdown.value == "2차 보정검사(OHT)":
            max_distance_field.value = results['report_path']
        elif test_type_dropdown.value == "2차 보정검사(OBS)":
            max_distance_obs_field.value = results['report_path']
        page.update()
        update_status("최대거리 검사 완료 및 결과 경로 자동 할당")

if __name__ == "__main__":
    ft.app(main)