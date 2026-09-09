"""
Time:2026.1.14
Coder:Wang
修改Robotiq代码，适配知行夹爪
"""

"""Module to control Robotiq's grippers - tested with HAND-E.

Taken from https://github.com/githubuser0xFFFF/py_robotiq_gripper/blob/master/src/robotiq_gripper.py
"""

import socket
from pyModbusTCP.client import ModbusClient
import threading
import time
from enum import Enum
from typing import OrderedDict, Tuple, Union


class ZhixingGripper:
    def __init__(self):
        """Constructor."""
        self.zxhand_client = None
        self._lock = threading.Lock()
        self._min_position = 25
        self._max_position = 100
        self._min_speed = 0
        self._max_speed = 1000
        self._min_force = 0
        self._max_force = 400
        
        self.add_mode = 0
        self.add_position = 10
        self.add_strength = 11
        self.add_speed = 12
        self.add_acc = 13
        self.add_position_real = 14
        self.add_tongbu = 42
        self.add_running = 43
        self.add_pos_ok = 44

    def connect(self, hostname: str = "192.168.1.20", port: int = 502) -> None:
        """Connects to a gripper at the given address.

        :param hostname: Hostname or ip.
        :param port: Port.
        :param socket_timeout: Timeout for blocking socket operations.
        """

        try:
            self.zxhand_client = ModbusClient(host=hostname, port=port, auto_open=True, auto_close=True)
            self.zxhand_client.write_single_register(self.add_mode, 1)
            self.zxhand_client.write_single_register(self.add_tongbu, 1)
            print("ZXHand 夹爪初始化成功")
        except Exception as e:
            print(f"ZXHand 夹爪初始化失败: {e}")
            self.zxhand_client = None

    def disconnect(self) -> None:
        """Closes the connection with the gripper."""
        """断开与知行夹爪的Modbus TCP连接，并清理资源"""
        # 先判断客户端实例是否存在（避免空指针报错）
        if self.zxhand_client is not None:
            try:
                # 1. 可选：断开前向夹爪写入"禁用"指令（比如模式寄存器写0）
                # 若需要夹爪断开连接前恢复初始状态，可取消下面注释
                self.zxhand_client.write_single_register(self.add_mode, 0)
                self.zxhand_client.write_single_register(self.add_tongbu, 0)
                
                # 2. 关闭Modbus TCP连接
                self.zxhand_client.close()
                print("ZXHand 夹爪连接已断开")
            except Exception as e:
                print(f"断开ZXHand 夹爪连接时出错: {e}")
            finally:
                # 3. 置空客户端实例，避免后续误操作
                self.zxhand_client = None
        else:
            # 客户端实例为空时的提示（非报错，仅友好提示）
            print("ZXHand 夹爪未建立连接，无需断开")


    # 写入寄存器的值
    def _write_register(self, register_address, value) -> bool:
        with self._lock:
            return self.zxhand_client.write_single_register(register_address, value)    

    # 读取寄存器的值
    def _read_register(self, register_address=None):
        with self._lock:
            return self.zxhand_client.read_input_registers(register_address, 1)
        
    def get_current_position(self) -> int:
        """
        读取夹爪当前实际位置
        :return: 夹爪当前位置 [min_position, max_position]
        """
        pos = self._read_register(self.add_position_real)
        if pos:
            return pos[0]
        else:
            raise RuntimeError("Failed to read current position from gripper.")

    def is_running(self) -> bool:
        return bool(self._read_register(self.add_running))

    def pos_reached(self) -> bool:
        return bool(self._read_register(self.add_pos_ok))

    def move(self, position: int, speed: int, force: int) -> Tuple[bool, int]:
        """
        发送指令控制夹爪移动到目标位置（非阻塞）
        :param position: 目标位置 [min_position, max_position]
        :param speed: 运动速度 [min_speed, max_speed]
        :param force: 夹持力度 [min_force, max_force]
        :return: (是否发送成功, 裁剪后的实际目标位置)
        """
        # 类型转换+范围裁剪（防止参数越界）
        position = int(position)
        speed = int(speed)
        force = int(force)

        def clip_val(min_val, val, max_val):
            return max(min_val, min(val, max_val))

        clip_pos = clip_val(self._min_position, position, self._max_position)
        clip_spe = clip_val(self._min_speed, speed, self._max_speed)
        clip_for = clip_val(self._min_force, force, self._max_force)

        # 向知行夹爪寄存器写入参数
        # 1. 写入速度
        speed_ok = self._write_register(self.add_speed, clip_spe)
        # 2. 写入力度
        force_ok = self._write_register(self.add_strength, clip_for)
        # 3. 写入目标位置
        pos_ok = self._write_register(self.add_position, clip_pos)
        # 所有寄存器写入成功才算指令发送成功
        succ = all([speed_ok, force_ok, pos_ok])
        # time.sleep(0.008)  # 保留原延迟，适配硬件响应
        # print(f"夹爪移动指令发送 {'成功' if succ else '失败'}，目标位置: {clip_pos}, 速度: {clip_spe}, 力度: {clip_for}")
        return succ, clip_pos

    def move_and_wait_for_pos(self, position: int, speed: int, force: int):
        """
        控制夹爪移动到目标位置并等待完成（阻塞）
        :param position: 目标位置 [min_position, max_position]
        :param speed: 运动速度 [min_speed, max_speed]
        :param force: 夹持力度 [min_force, max_force]
        :return: (最终位置, 状态码) 
                状态码对应：0=空闲,1=运动中,2=到位,3=夹取到物体（可根据手册调整）
        """
        position = int(position)
        speed = int(speed)
        force = int(force)

        def clip_val(min_val, val, max_val):
            return max(min_val, min(val, max_val))
        
        clip_pos = clip_val(self._min_position, position, self._max_position)
        # 发送移动指令
        set_ok = self.move(position, speed, force)
        if not set_ok:
            raise RuntimeError("Failed to set variables for move.")

        start_time = time.time()
        timeout = 5
        tolerance = 3
        # 等待夹爪确认目标位置（回显寄存器匹配）
        # 循环读取目标位置回显寄存器，直到和下发的cmd_pos一致
        while time.time() - start_time < timeout:
            # 读取夹爪实际位置
            current_pos = self._read_register(self.add_position_real)
            # 判断是否到达目标位置
            if abs(current_pos[0] - clip_pos) <= tolerance:
                print(f"夹爪已到达实际位置: {current_pos}")
                break
            else:
                print("无法读取夹爪实际位置")
            time.sleep(0.1)  # 短暂延时避免频繁查询
            print(f"夹爪未在 {timeout} 秒内到达实际位置 {clip_pos}")

        # 等待夹爪停止运动（状态寄存器不为1）
        cur_status = self._read_register(self.add_running)
        print(cur_status)
        while cur_status == 1:  # 1=运动中
            time.sleep(0.001)
            cur_status = self._read_register(self.add_running)

        # 获取最终位置和状态
        final_pos = self._read_register(self.add_position_real)
        final_status = cur_status
        print(f"夹爪移动完成，最终位置: {final_pos}, 状态码: {final_status}")
        return final_pos, final_status
   
def test_write_read():
    # test open and closing the gripper
    gripper = ZhixingGripper()
    gripper.connect(hostname="192.168.1.20", port=502)
    # set speed and force
    gripper._write_register(gripper.add_speed, 100)
    gripper._write_register(gripper.add_strength, 100)
    # read speed and force
    speed = gripper._read_register(gripper.add_speed)
    force = gripper._read_register(gripper.add_strength)
    pos_real = gripper._read_register(gripper.add_position_real)
    print(f"Speed: {speed}, Force: {force}, Real Position: {pos_real}")

def test_read_pos():
    gripper = ZhixingGripper()
    gripper.connect(hostname="192.168.1.20", port=502)
    pos_real = gripper._read_register(gripper.add_position_real)
    print(f"Real Position: {pos_real}")

def test_move():
    gripper = ZhixingGripper()
    gripper.connect(hostname="192.168.1.20", port=502)
    gripper.move(0, 100, 100)
    gripper.disconnect()

def test_move_and_wait():
    gripper = ZhixingGripper()
    gripper.connect(hostname="192.168.1.20", port=502)
    gripper.move_and_wait_for_pos(0, 200, 150)
    gripper.disconnect()

if __name__ == "__main__":
    # test_write_read()
    # test_move()
    test_move_and_wait()
    # test_read_pos()
