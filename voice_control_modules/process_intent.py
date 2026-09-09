import time
import os
import json

class ProcessIntent:
    def __init__(self):

         # ========== 新增：后处理映射规则 ==========
        # 笛卡尔移动方向 -> (x系数, y系数, z系数)，对齐示例：左+x、前+y、上+z
        self.direction_axis_map = {
            "前": (0, 1, 0),
            "后": (0, -1, 0),
            "左": (1, 0, 0),
            "右": (-1, 0, 0),
            "上": (0, 0, 1),
            "下": (0, 0, -1)
        }
        # 长度单位 -> 毫米换算系数
        self.linear_unit_coeff = {
            "毫米": 1,
            "厘米": 10,
            "米": 1000
        }

        # ========== 新增：饮品类型映射 ==========
        self.drink_name_map = {
        "cola": "可乐",
        "sprite": "雪碧",
        "fenda": "芬达"}
    
    # ========== 新增：意图结果转机器人函数调用 后处理方法 ==========
    def intent_to_function(self, intent_result_str):
        """
        将模型输出的意图识别JSON，转换为UR机器人函数调用格式
        :param intent_result_str: 模型原始输出的意图JSON字符串
        :return: 最终输出的JSON字符串，包含function和response
        """
        function_list = []
        response_list = []

        # 1. 解析JSON，兼容模型的格式漂移
        try:
            intent_data = json.loads(intent_result_str.strip())
            # 兼容两种输出格式：intent_list 数组 / intent 单字段
            if "intent_list" in intent_data:
                intent_items = intent_data["intent_list"]
            elif "intent" in intent_data:
                intent_items = [{
                    "intent": intent_data["intent"],
                    "entities": intent_data.get("entities", {})
                }]
            else:
                intent_items = []
        except json.JSONDecodeError:
            # JSON解析失败兜底
            return json.dumps({
                "function": [],
                "response": "指令解析失败，请输入有效的机器人控制指令"
            }, ensure_ascii=False)

        # 2. 空意图/无效指令兜底
        if not intent_items:
            return json.dumps({
                "function": [],
                "response": "无法识别该指令，请输入有效的机器人控制指令"
            }, ensure_ascii=False)

        # 3. 遍历处理每个意图
        for item in intent_items:
            intent_name = item.get("intent", "")
            entities = item.get("entities", {})

            # 3.1 回原点
            if intent_name == "go_home":
                function_list.append("self.ur_robot.go_home()")
                response_list.append("好的，我正在返回原点")

            # 3.2 笛卡尔直线移动
            elif intent_name == "move_direction":
                direction = entities.get("direction", "none")
                distance = entities.get("distance", "none")
                unit = entities.get("unit", "none")
                passing_params = []
                
                # 参数完整性判断
                # if direction == "none":
                #     passing_params.append("运动方向")
                # if distance == "none":
                #     passing_params.append("距离")  
                # if unit == "none":
                #     passing_params.append("单位")

                # if len(passing_params) > 0:  # 参数不完整
                #     response_list.append(f"参数缺失：未获取到{passing_params}，无法执行移动指令")
                #     continue

                if direction == "none" or distance == "none" or unit == "none":
                    response_list.append("未同时提供方向、距离、单位信息，无法执行指令")
                    continue

                # 方向非法则跳过
                if direction not in self.direction_axis_map:
                    response_list.append(f"无法识别移动方向：{direction}")
                    continue

                # 单位统一转换为毫米，对齐示例参数
                coeff = self.linear_unit_coeff.get(unit, 1)
                dist_mm = int(distance * coeff)
                dx, dy, dz = self.direction_axis_map[direction]
                x = dx * dist_mm
                y = dy * dist_mm
                z = dz * dist_mm

                function_list.append(f"self.ur_robot.move_direction({x},{y},{z})")
                response_list.append(f"好的，我朝着{direction}方移动{distance}{unit}")

            # 3.3 关节空间旋转
            elif intent_name == "move_joint":
                joint_no = entities.get("joint_no", 0)
                rotate_dir = entities.get("rotate_dir", "正")
                angle = entities.get("angle", 0)
                unit = entities.get("unit", "度")

                # 关节编号非法则跳过
                if not (1 <= joint_no <= 6):
                    response_list.append(f"无效的关节编号：{joint_no}")
                    continue

                if joint_no == "none" or rotate_dir == "none" or angle == "none" or unit == "none":
                    response_list.append("未同时提供关节编号、方向、角度、单位信息，无法执行指令")
                    continue

                # 正转取正值，反转取负值
                angle_val = angle if rotate_dir == "正" else -angle
                # 初始化6个关节角度，对应位置赋值
                joints = [0, 0, 0, 0, 0, 0]
                joints[joint_no - 1] = angle_val

                func_str = f"self.ur_robot.move_j({joints[0]},{joints[1]},{joints[2]},{joints[3]},{joints[4]},{joints[5]})"
                function_list.append(func_str)
                response_list.append(f"好的，关节{joint_no}{rotate_dir}向旋转{angle}{unit}")

            # 3.4 夹爪控制
            elif intent_name == "gripper_control":
                status = entities.get("gripper_status", "")
                if status == "闭合":
                    flag = "True"
                    resp_text = "夹爪闭合"
                elif status == "张开":
                    flag = "False"
                    resp_text = "夹爪张开"
                else:
                    response_list.append(f"无法识别夹爪状态：{status}")
                    continue

                function_list.append(f"self.ur_robot.gripper_close({flag})")
                response_list.append(resp_text)

            # 未知意图兜底
            else:
                response_list.append(f"未知指令：{intent_name}")

        

        # 4. 组装最终结果
        final_result = {
            "function": function_list,
            "response": "；".join(response_list)
        }
        return json.dumps(final_result, ensure_ascii=False)
    # def chat_loop(self):
    #     """
    #     启动交互式对话循环
    #     """
    #     print("开始对话，输入 'quit' 或 'exit' 退出程序，输入 'clear' 清空历史记录")
        
    #     while True:
    #         user_input = input("\n请输入您的问题: ")
            
    #         if user_input.lower().strip() in ['quit', 'exit', '退出']:
    #             print("程序已退出")
    #             break
            
    #         if user_input.lower().strip() == 'clear':
    #             self.clear_history()
    #             print("历史记录已清空")
    #             continue
            
    #         if not user_input.strip():
    #             print("输入不能为空，请重新输入")
    #             continue
            
    #         thinking_content, intent_content, inference_time = self.generate_response(
    #             user_input, system_prompt=self.system_prompt
    #         )
    #         # 调用后处理，转换为函数调用格式
    #         final_output = self.intent_to_function(intent_content)

    #         print("thinking content:", thinking_content)
    #         print("原始意图识别结果:", intent_content)
    #         print("最终输出:", final_output)
    #         print("inference time:", inference_time)
            
    #         if "好的，我正在返回原点" in final_output:
    #             self.clear_history()
    #             print("已为您完成任务，聊天历史已清空")

    

# 使用示例
if __name__ == "__main__":
    # 创建模型实例
    pass