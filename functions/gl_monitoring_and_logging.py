import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pprint import pprint
import pickle
# import time
import matplotlib as mpl

import pysoslab_core
import pysoslab_user
import pysoslab_logger

import keyboard

np.set_printoptions(threshold=10)
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0

##############################################
SERIAL_NAME = "COM4"
SERIAL_BAUDRATE = 921600  # 921600, 115200
logging_frames = 40


UDP_SENSOR_IP = "10.110.1.2"
UDP_SENSOR_PORT = 2000
UDP_PC_IP = "10.110.1.3"
UDP_PC_PORT = 3000
##############################################


def data_acqusition(inputs: dict):
    output = dict()
    logging_flag = 0

    success, serial_num = inputs["gl_user"].getSerialNum(inputs["gl_core"])
    if success:
        print(f"Serial_num = {serial_num}")
        output["serial_num"] = serial_num
    else:
        print("Unable to get a serial number")

    success = inputs["gl_user"].setStreamEnable(inputs["gl_core"], True)
    if success:
        print("Successfully enable data streaming")
    else:
        print("Failed to enable data streaming")

    i = 0
    j = 0
    frame_datas = []
    while True:
        # key = keyboard.is_pressed('q')
        if keyboard.is_pressed('q') or keyboard.is_pressed('Q'):
            break

        if keyboard.is_pressed('l') or keyboard.is_pressed('L'):
            logging_flag = 1
            print("logging start")

        success, frame_data = inputs["gl_user"].getLidarData(
            inputs["gl_core"], False
            )
        if not success:
            print("Failed to get a LiDAR data")

        if logging_flag:
            frame_datas.append(frame_data)
            j = j + 1
            if j >= logging_frames:
                plt.close()
                break

        i = i + 1
        # if i % 10 == 0:
        if True:
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

        if i % 3 == 0:
            print(f'pulsewidth@idx 750:{frame_data["pulse_width"][750]/10:2f}')

    output["raw_data"] = frame_datas
    return output


def analysis():
    pass


def unittest():
    gl_core = pysoslab_core.core()
    gl_user = pysoslab_user.user()
    gl_logger = pysoslab_logger.logger()

    inputs = dict()
    inputs["gl_core"] = gl_core
    inputs["gl_user"] = gl_user
    inputs["gl_logger"] = gl_logger
    # gl_core.connectSerial(SERIAL_NAME, SERIAL_BAUDRATE)
    gl_core.connectUDP(UDP_SENSOR_IP, UDP_SENSOR_PORT, UDP_PC_IP, UDP_PC_PORT)


    raw_data = data_acqusition(inputs)

    inputs["gl_core"].disconnect()

    # 변수값을 직접 보고싶을때 활성화
    # with open('logging_data_test.yaml', 'w') as f:
    #     yaml.dump(raw_data, f,
    #               default_flow_style=False,
    #               allow_unicode=True,
    #               sort_keys=False)

    with open(
        file=f'./log/gl_monitoring_and_logging/{raw_data["serial_num"]}'
        + f"_{datetime.now().year}"
        + f".{datetime.now().month}"
        + f".{datetime.now().day}"
        + f'_{datetime.now().strftime("%H.%M.%S")}'
        + f'_device-130,retro50,9m.pickle',
        mode="wb",
    ) as f:
        pickle.dump(raw_data, f)


if __name__ == "__main__":
    unittest()
