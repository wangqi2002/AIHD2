""" UR机器人运动控制交互函数 """
import rtde_control
import rtde_receive
from pyModbusTCP.client import ModbusClient

import numpy as np
import math
from .zhixing_gripper import ZhixingGripper

class UR_Robot():
    """ UR机器人控制类 """
    def __init__(self, robot_ip="192.168.1.30"):

        try:
            self.rtde_c = rtde_control.RTDEControlInterface(robot_ip)
            self.rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip)
            print("UR机器人控制接口已连接")
        except Exception as e:
            print(f"UR机器人控制接口连接失败: {e}")
            self.rtde_c = None
            self.rtde_r = None

        self.gripper = ZhixingGripper()
        self.gripper.connect()

        self.acc = 0.5
        self.speed = 0.1

        self.home_joint_config = [(45 / 360.0) * 2 * np.pi, 
                                  -(90 / 360.0) * 2 * np.pi,
                                  -(90 / 360.0) * 2 * np.pi, 
                                  -(90 / 360.0) * 2 * np.pi,
                                  (90 / 360.0) * 2 * np.pi, 
                                  (90 / 360.0) * 2 * np.pi
                                  ]
        self.home_task_drink = [(52.45 / 360.0) * 2 * np.pi, 
                                -(77.89 / 360.0) * 2 * np.pi,
                                -(68.30 / 360.0) * 2 * np.pi, 
                                -(124.19 / 360.0) * 2 * np.pi,
                                (90.75 / 360.0) * 2 * np.pi, 
                                (98.17 / 360.0) * 2 * np.pi
                                ]
        self.base_rotation_angle = np.radians(45)   # 绕Z轴旋转角度（度）
        self.base_rotation_axis = 'z'   # 默认绕Z轴

    def go_home(self, task_type=None):
        """ 快速回零 """
        # if task_type == 'voice_teach':
        #     self.rtde_c.moveL(self.home_joint_config, self.speed, self.acc, False)
        # elif task_type == 'drink':
        #     self.rtde_c.moveJ(self.home_task_drink, self.speed, self.acc, False)
        self.rtde_c.moveJ(self.home_task_drink, self.speed, self.acc, False)

    def _transform(self, dx, dy, dz):
        """将相对于原始基坐标系的移动向量变换到当前基坐标系下"""
        angle = self.base_rotation_angle
        axis = self.base_rotation_axis
        c = math.cos(angle)
        s = math.sin(angle)

        if axis == 'z':
            # 绕Z轴旋转
            new_dx = dx * c + dy * s
            new_dy = -dx * s + dy * c
            new_dz = dz
        elif axis == 'x':
            new_dx = dx
            new_dy = dy * c - dz * s
            new_dz = dy * s + dz * c
        elif axis == 'y':
            new_dx = dx * c + dz * s
            new_dy = dy
            new_dz = -dx * s + dz * c
        else:
            raise ValueError("axis must be 'x', 'y', or 'z'")
        return new_dx, new_dy, new_dz

    def move_direction(self, x, y, z):
        """ 在笛卡尔空间中基于方向移动 """ 
        x, y, z = x / 1000, y / 1000, z / 1000
        x, y, z = self._transform(x, y, z)
        current_pose = np.array(self.rtde_r.getActualTCPPose())
        target_pose = current_pose + np.array([x, y, z, 0, 0, 0])
        self.rtde_c.moveL(target_pose, self.speed, self.acc, False)

    def move_l(self, target_pose):
        """ 在笛卡尔空间中直线运动 """
        target_pose = np.array(target_pose)
        self.rtde_c.moveL(target_pose, self.speed, self.acc, False)

    def move_l_sequence(self, target_poses):
        """ 在笛卡尔空间中执行一系列直线运动 """
        for pose in target_poses:
            self.move_l(pose)

    def move_j(self, a, b, c, d, e, f):
        """ 移动到指定关节角度 """
        current_pose = np.array(self.rtde_r.getActualQ())
        target_pose = current_pose + np.radians([a, b, c, d, e, f])
        # print(f"当前关节角度: {current_pose}")
        # print(f"目标关节角度: {target_pose}")
        self.rtde_c.moveJ(target_pose, self.speed, self.acc, False)

    # def gripper(self, b):
    #     """ 控制爪手开合 """
    #     if b:
    #         self.rtde_c.setStandardDigitalOut(0, True)  # 关闭爪手
    #     else:
    #         self.rtde_c.setStandardDigitalOut(0, False) # 打开爪手

    def get_current_tcp(self):
        current_pose = np.array(self.rtde_r.getActualTCPPose())
        print(f"当前TCP位置: {current_pose}")
        

if __name__ == "__main__":
    ur_robot = UR_Robot()
    ur_robot.get_current_tcp()
    # ur_robot.go_home()
    # ur_robot.move_direction(200, 0, 0)
    # ur_robot.move_direction(0, 100, 0)
    # ur_robot.move_direction(0, 0, 100)
    # ur_robot.move_j(5, 0, 0, 0, 0, 0)