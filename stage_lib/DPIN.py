#!/usr/bin/env python3
# -*- coding : utf-8 -*-

import time
import socket
import ctypes


class DpinStageHandler(object):
    def __init__(self) -> None:
        self.dpin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dpin_socket.settimeout(3.0)

    def send_msg(self, send_msg: str) -> str:
        self.dpin_socket.sendall(send_msg.encode(encoding="utf-8"))
        data = self.dpin_socket.recv(1000)
        recv_msg = data.decode()
        return recv_msg

    def connect(self, ip: str, port: int) -> None:
        self.dpin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dpin_socket.settimeout(3.0)
        self.dpin_socket.connect((ip, port))
        print("dpin_connected")
        msg = "GONIO,X"
        self.send_msg(msg)

        self.set_rpm(100, 500, 100, 100)

    def disconnect(self) -> None:
        self.dpin_socket.close()

    def searching_home(self) -> None:
        self.gonio_cw_move(10)
        while self.is_moving():
            time.sleep(0.01)

        msg = "HOME,X"
        self.send_msg(msg)
        print("Start searching origin...")
        while not self.read_status()["Home_Checked"]:
            time.sleep(0.1)
        print("Origin Search Success!")
        time.sleep(0.1)

    def gonio_cw_move(self, goal_deg: float) -> None:
        goal_deg = goal_deg * 25600 / 1.6
        msg = f"JM_CW,X,{goal_deg:f}"
        self.send_msg(msg)
        time.sleep(0.1)

    def gonio_ccw_move(self, goal_deg: float) -> None:
        goal_deg = goal_deg * 25600 / 1.6
        msg = f"JM_CCW,X,{goal_deg:f}"
        self.send_msg(msg)
        time.sleep(0.1)

    def read_status(self) -> dict:
        msg = "STATUS,X"
        recv_msg = self.send_msg(msg)
        status = dict()
        status["is_moving"] = bool(recv_msg[14] == "1")
        status["Home_Checked"] = bool(recv_msg[15] == "4")
        status["Limit_CCW_Checked"] = bool(recv_msg[15] == "2")
        status["Limit_CW_Checked"] = bool(recv_msg[15] == "1")
        return status

    def is_moving(self) -> bool:
        status = self.read_status()
        return status["is_moving"]

    def read_cur_deg(self) -> float:
        msg = "R_POS,X"
        recv_msg = self.send_msg(msg)
        msg = recv_msg.split()
        val = int(msg[1][2:], 16)
        int_val = ctypes.c_int32(val).value
        angle_deg = int_val / 25600 * 1.6
        return angle_deg

    def move_to_angle(self, target_angle: float) -> None:
        current_angle = self.read_cur_deg()
        relative_angle = target_angle - current_angle

        if relative_angle > 0:
            self.gonio_cw_move(relative_angle)
        else:
            relative_angle = -relative_angle
            self.gonio_ccw_move(relative_angle)

    def set_rpm(
        self, start_speed: int, run_speed: int, dec_time: int, acc_time: int
    ) -> None:
        msg = f"SET_RPM,X,{start_speed},{run_speed},{dec_time},{acc_time}"
        self.send_msg(msg)


def unittest():
    dpin = DpinStageHandler()
    dpin.connect("192.168.0.50", 10)
    dpin.searching_home()

    dpin.move_to_angle(2)
    print(f"cur_deg = {dpin.read_cur_deg()}")

    dpin.move_to_angle(4)
    print(f"cur_deg = {dpin.read_cur_deg()}")

    dpin.move_to_angle(2)
    print(f"cur_deg = {dpin.read_cur_deg()}")

    dpin.disconnect()


if __name__ == "__main__":
    unittest()
