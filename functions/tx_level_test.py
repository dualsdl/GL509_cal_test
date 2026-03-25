#!/usr/bin/env python3
#-*- coding : utf-8 -*-

import numpy as np
import cv2
from pypylon import pylon
import time
from datetime import datetime

# stage_lib을 import하기 위해 프로젝트 루트를 sys.path에 추가
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage_lib.DPIN import DpinStageHandler
from stage_lib.ETEL import init_stage, search_home, disconnect_stage
import pysoslab_etel_stage as py_stage_etel

import pysoslab_core
import pysoslab_user
import pysoslab_developer
from functions.util_yy import save_pickle_to_zip
# #############  parameter start ###############
default_parameters = {
    "SERIAL_NAME": "COM4",
    "SERIAL_BAUDRATE": 921600,  # 921600, 115200
    "UDP_SENSOR_IP": "10.110.1.2",
    "UDP_SENSOR_PORT": 2000,
    "UDP_PC_IP": "10.110.1.3",
    "UDP_PC_PORT": 3000,
    "DPIN_gonio_IP_addr": "10.110.1.201",
    "DPIN_gonio_port": 184,
    "etel_stage_IP_addr": "10.110.1.200",
    "LINEAR_STAGE_OFFSET": -43,
    "OBS_camera_exposure": 5000,
    "OHT_camera_exposure": 5000,
    "LD_HV": 20.0,
    "camera_FPS": 49.5,
    "camera_acqusition_num": 100,
    "OBS_target_angle": 90.0,  # retro target angle on ETEL stage
    "OHT_target_angle": 0.0,  # retro target angle on ETEL stage
    "linear_distance": 5000.0,
    "scan_angles": ['-135.0', '-90.0', '-45.0', '0.0', '45.0', '90.0', '135.0'],
    # "scan_angles": [0.0],
    "image_ROI_y": [879, 1135],
    "image_ROI_x": [865, 1290],
    "binary_threshold": 20,
    "tx_level_origin_px": 1090,
    # "px2mm_conversion_gain": 200/(1173-1002),  # d/px로 계산, 실제 측정한 거리d가 몇 픽셀px로 나오는가? 300/(1141-878)
    "px2mm_conversion_gain": 1.14068,  # d/px로 계산, 실제 측정한 거리d가 몇 픽셀px로 나오는가?
    "pass_criteria": 1
}
# #############  parameter end ###############


def data_acquisition(input: dict, parameters: dict) -> dict:
    outputs = dict()
    GL5_core = input['GL5_core']
    GL5_user = input['GL5_user']
    GL5_developer = input['GL5_developer']
        
    success, GL_serial = GL5_user.getSerialNum(GL5_core)
    if success:
        print(f"Serial_num = {GL_serial}")
    else:
        print("Unable to get a serial number")
    
    outputs['GL_serial'] = GL_serial
    
    # 현재 LD_HV값 저장
    success, prev_ld_high_voltage = GL5_developer.getLDHighVoltage(GL5_core)
    if not success:
        print("Unable to get the current ld_high_voltage")
        
    # 테스트용 LD_HV값 설정
    # success = GL5_developer.setLDHighVoltage(GL5_core, parameters["LD_HV"])
    # if success:
    #     print("Successfully set the ld_high_voltage")
    # else:
    #     print("Unable to set the ld_high_voltage")
    success, ld_high_voltage = GL5_developer.getLDHighVoltage(GL5_core)
    if success:
        print(f"ld_high_voltage = {ld_high_voltage}")
    else:
        print("Unable to get the ld_high_voltage")

    model_name = GL_serial[4:6]
    print(f"Model name: {model_name}")
    if (model_name == '1W' or
            model_name == '1V'):
        target_angle = parameters["OHT_target_angle"]
        camera_exposure = parameters["OHT_camera_exposure"]
    elif (model_name == '1N' or
            model_name == '1M' or
            model_name == '1R' or
            model_name == '2N'):
        target_angle = parameters["OBS_target_angle"]
        camera_exposure = parameters["OBS_camera_exposure"]
    else:
        raise ValueError('Unknown sensor type')

    outputs['test_time'] = f"{datetime.now().year}" + \
                    f".{datetime.now().month}" + \
                    f".{datetime.now().day}" + \
                    f'_{datetime.now().strftime("%H.%M.%S")}'
    # print(f'test time = {outputs["test_time"]}')
    stage_etel = input['stage_etel']

    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()
    print("Using device ", camera.GetDeviceInfo().GetModelName())
    camera.ExposureTime = camera_exposure
    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate = parameters["camera_FPS"]
    # camera.Gain = 1
    fps = camera.ResultingFrameRate.GetValue()
    print(f'camera FPS is {fps:.3f}')

    # Grabing Continusely (video) with minimal delay
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    converter = pylon.ImageFormatConverter()
    # converting to opencv bgr format
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, 5000.0, 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)
    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET, target_angle, 30.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET):
        time.sleep(0.2)

    for scan_angle in parameters["scan_angles"]:
        outputs[scan_angle] = dict()

        stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, float(scan_angle), 30.0)
        while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
            time.sleep(0.2)

        frame_cnt = 0
        imgs = []
        while camera.IsGrabbing():
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                # Access the image data
                image = converter.Convert(grabResult)
                img = image.GetArray()
                img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                imgs.append(img)

            frame_cnt = frame_cnt + 1
            if frame_cnt >= parameters["camera_acqusition_num"]:
                min_img = np.min(imgs, axis=0)  # back ground image without laser
                max_img = np.max(imgs, axis=0)  # image with laser
                var_img = max_img - min_img
                outputs[scan_angle]['variation_img'] = var_img
                outputs[scan_angle]['max_img'] = max_img
                outputs[scan_angle]['min_img'] = min_img
                break

    stage_etel.rotateTo(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE, 0.0, 30.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE):
        time.sleep(0.2)
        
    # 이전 LD_HV값으로 복원
    # success = GL5_developer.setLDHighVoltage(GL5_core, prev_ld_high_voltage)
    # if success:
    #     print("Successfully restored the previous ld_high_voltage")
    # else:
    #     print("Unable to restore the previous ld_high_voltage")

    return outputs


def analysis(input: dict, parameters: dict) -> dict:
    output = dict()
    output['test_time'] = input['test_time']
    output['GL_serial'] = input['GL_serial']

    for scan_angle in parameters["scan_angles"]:
        cropped_img = input[scan_angle]['variation_img'][parameters["image_ROI_x"][0]:parameters["image_ROI_x"][1],
                                                         parameters["image_ROI_y"][0]:parameters["image_ROI_y"][1]]
        max_img = input[scan_angle]['max_img'][parameters["image_ROI_x"][0]:parameters["image_ROI_x"][1],
                                               parameters["image_ROI_y"][0]:parameters["image_ROI_y"][1]]
        processed_data = dict()
        processed_data['1.cropped_image'] = cropped_img

        # cv2.imshow('Image Window', cropped_img)
        # cv2.waitKey(0)

        k_size = 5
        filtered_img = cv2.bilateralFilter(cropped_img, k_size, 20, 20)
        processed_data['2.filtered_image'] = filtered_img

        back_ground_intensity = np.median(filtered_img.flatten())

        _, binary_img = cv2.threshold(filtered_img, back_ground_intensity + parameters['binary_threshold'], 255, cv2.THRESH_BINARY)
        # _, binary_img = cv2.threshold(filtered_img, back_ground_intensity + np.max(filtered_img.flatten()) - parameters["binary_threshold"], 255, cv2.THRESH_BINARY)
        processed_data['3.binary_image'] = binary_img

        # cv2.imshow('Image Window', binary_img)
        # cv2.waitKey(0)

        # Opning이 맞나? Closing이 맞나??
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
        # opening_img = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, k)
        opening_img = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, k)
        processed_data['4.opening_image'] = opening_img

        # cv2.imshow('Image Window', opening_img)
        # cv2.waitKey(0)

        _, labels, stats, _ = cv2.connectedComponentsWithStats(opening_img)
        s = stats[:, 4].argsort()[::-1]
        labels[np.where(labels != s[1])] = 0
        labels[np.where(labels == s[1])] = 255
        labels = np.uint8(labels)
        processed_data['5.lebeling_image'] = labels

        idx = np.where(labels == 255)
        tx_level = np.mean(idx[0])  # in pixel, origin is top point
        # print(tx_level)

        line_img = cv2.cvtColor(max_img, cv2.COLOR_GRAY2RGB)
        pt1 = np.array((0, tx_level), dtype=np.int64)
        pt2 = np.array((max_img.shape[1], tx_level), dtype=np.int64)
        cv2.line(line_img, pt1, pt2, (255, 0, 255), thickness=2)

        tx_level = tx_level - (parameters["tx_level_origin_px"] - parameters["image_ROI_x"][0])
        # print(tx_level)
        # in pixel, parameters['beam_height_origin'] indicate origin
        processed_data['tx_level_in_pixels'] = tx_level
        tx_level = tx_level * parameters["px2mm_conversion_gain"]
        processed_data['tx_level_in_mm'] = tx_level
        tx_level = np.degrees(np.arctan(tx_level / parameters["linear_distance"]))
        processed_data['tx_level_in_deg'] = tx_level

        org = (10, 30)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f'tx_level = {tx_level:.3f}deg'
        cv2.putText(line_img, text, org, font, 0.5, (0, 255, 0), 1)
        processed_data['6.line_image'] = line_img

        output[scan_angle] = processed_data

    output['tx_level_Pass/Fail'] = True

    # 절대값 +- 1도 이내인지 검사
    for scan_angle in parameters["scan_angles"]:
        if abs(output[scan_angle]['tx_level_in_deg']) > parameters["pass_criteria"]:
        # if output[scan_angle]['tx_level_in_deg'] < -parameters["pass_criteria"] or \
        #    output[scan_angle]['tx_level_in_deg'] > parameters["pass_criteria"]:
            output['tx_level_Pass/Fail'] = False
    
    line_img = []
    for scan_angle in parameters["scan_angles"]:
        line_img.append(output[scan_angle]['6.line_image'])
        # print(f'{scan_angle}deg tx level[deg] = {output[scan_angle]["tx_level_in_deg"]:.3f}')
        # print(f'{scan_angle}deg tx level[px] = {output[scan_angle]["tx_level_in_pixels"]:.3f}')

    line_img = np.hstack(line_img)
    output['line_image'] = line_img

    return output


def run(input: dict, parameters: dict) -> dict:
    default_parameters.update(parameters)

    data = data_acquisition(input, default_parameters)
    outputs = analysis(data, default_parameters)

    return data, outputs


def unittest(parameters: dict = default_parameters):
    # LiDAR Serial number read    
    GL5_core = pysoslab_core.core()
    GL5_user = pysoslab_user.user()    
    GL5_developer = pysoslab_developer.developer()
    # GL5_core.connectSerial(parameters["SERIAL_NAME"], parameters["SERIAL_BAUDRATE"])
    GL5_core.connectUDP(
        parameters["UDP_SENSOR_IP"],
        parameters["UDP_SENSOR_PORT"],
        parameters["UDP_PC_IP"],
        parameters["UDP_PC_PORT"]
        )

    # DPIN stage connect
    # stage_dpin = DpinStageHandler()
    # stage_dpin.connect(parameters["DPIN_gonio_IP_addr"], parameters["DPIN_gonio_port"])
    # stage_dpin.searching_home()
    # stage_dpin.move_to_angle(0.0)

    # ETEL stage connect
    stage_etel = py_stage_etel.stage_etel()
    status = stage_etel.connect(parameters["etel_stage_IP_addr"], 3)
    if status:
        pass
    else:
        raise Exception('ETEL stage initialing FAIL')

    time.sleep(0.5)
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_DEVICE)
    print('ROTARY_DEVICE home search done')
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET)
    print('LINEAR_TARGET home search done')
    stage_etel.moveTo(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, parameters["linear_distance"], 400.0)
    while stage_etel.isMoving(py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET):
        time.sleep(0.2)
    search_home(stage_etel, py_stage_etel.STAGE_AXIS_INDEX.ROTARY_TARGET)
    print('ROTARY_TARGET home search done')

    input = dict()
    input['stage_etel'] = stage_etel

    stage_etel.setOffset(
        py_stage_etel.STAGE_AXIS_INDEX.LINEAR_TARGET, parameters["LINEAR_STAGE_OFFSET"]
    )
    
    dpin = DpinStageHandler()
    dpin.connect("10.110.1.201", 184)
    dpin.searching_home()

    input['dpin'] = dpin
    input['GL5_core'] = GL5_core
    input['GL5_user'] = GL5_user
    input['GL5_developer'] = GL5_developer

    rawdata, output = run(input, parameters)

    base_filename = f"{rawdata['GL_serial']}_" + f'{rawdata["test_time"]}'
    path = "./log/tx_level"
    tx_level_image_path = f"{path}/{base_filename}.png"  # 저장vvvv할 이미지 경로
    rawdata_name = f"{base_filename}_raw"
    processed_data_name = f"{base_filename}_processed"

    # ZIP 파일에 pickle 데이터 압축하여 저장하기
    save_pickle_to_zip(rawdata, path, rawdata_name)
    save_pickle_to_zip(output, path, processed_data_name)

    cv2.imwrite(tx_level_image_path, output['line_image'])

    disconnect_stage(stage_etel)
    # stage_dpin.disconnect()


if __name__ == "__main__":
    unittest()