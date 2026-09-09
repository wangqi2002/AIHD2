import json


class PalletIntentProcessor:
    def __init__(self):
        pass

    def process(self, intent_result_str: str) -> str:
        """
        处理码垛task_pallet意图，输入LLM输出的intent json字符串，输出业务结果json字符串
        :param intent_result_str: LLM输出JSON字符串，例：{"intent_list":[{"intent":"task_pallet","entities":{"pallet_row":3,"pallet_col":2,"row_offset":120,"col_offset":150}}]}
        :return: json字符串
            示例1（全部参数）：{"function":["ur_robot.task_pallet()"], "response":"好的，设置码垛参数：行数3，列数2，行偏移120mm，列偏移150mm", "pallet_row":3, "pallet_col":2, "row_offset":120, "col_offset":150}
            示例2（部分参数）：{"function":["ur_robot.task_pallet()"], "response":"好的，设置码垛参数：行数4，列数3", "pallet_row":4, "pallet_col":3, "row_offset":null, "col_offset":null}
            示例3（无有效参数）：{"function": [], "response":"未获取到有效的码垛参数，请指定行数、列数或偏移距离"}
        """
        function_list = []
        response_list = []
        out_row = None
        out_col = None
        out_row_offset = None
        out_col_offset = None

        try:
            intent_data = json.loads(intent_result_str.strip())
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
            return json.dumps({
                "function": [],
                "response": "指令解析失败"
            }, ensure_ascii=False)

        if not intent_items:
            return json.dumps({
                "function": [],
                "response": "无有效码垛指令"
            }, ensure_ascii=False)

        for item in intent_items:
            intent_name = item.get("intent", "")
            entities = item.get("entities", {})
            if intent_name != "task_pallet":
                response_list.append("非码垛任务")
                continue

            pallet_row = entities.get("pallet_row")
            pallet_col = entities.get("pallet_col")
            row_offset = entities.get("row_offset")
            col_offset = entities.get("col_offset")

            out_row = pallet_row
            out_col = pallet_col
            out_row_offset = row_offset
            out_col_offset = col_offset

            # 拼接回复文本
            msg_parts = []
            if pallet_row is not None:
                msg_parts.append(f"行数{pallet_row}")
            if pallet_col is not None:
                msg_parts.append(f"列数{pallet_col}")
            if row_offset is not None:
                msg_parts.append(f"行偏移{row_offset}mm")
            if col_offset is not None:
                msg_parts.append(f"列偏移{col_offset}mm")

            if msg_parts:
                function_list.append("ur_robot.task_pallet()")
                response_list.append(f"好的，设置码垛参数：{','.join(msg_parts)}")
            else:
                response_list.append("未获取到有效的码垛参数，请指定行数、列数或偏移距离")

        final = {
            "function": function_list,
            "response": "；".join(response_list)
        }
        # 有任意一个码垛实体不为null则输出实体字段
        if any(x is not None for x in [out_row, out_col, out_row_offset, out_col_offset]):
            final["pallet_row"] = out_row
            final["pallet_col"] = out_col
            final["row_offset"] = out_row_offset
            final["col_offset"] = out_col_offset

        return json.dumps(final, ensure_ascii=False)


if __name__ == "__main__":
    proc = PalletIntentProcessor()
    # 测试用例1：完整参数
    print(proc.process('{"intent_list":[{"intent":"task_pallet","entities":{"pallet_row":3,"pallet_col":2,"row_offset":120,"col_offset":150}}]}'))
    # 测试用例2：仅行列
    print(proc.process('{"intent_list":[{"intent":"task_pallet","entities":{"pallet_row":4,"pallet_col":3,"row_offset":null,"col_offset":null}}]}'))
    # 测试用例3：仅行偏移
    print(proc.process('{"intent_list":[{"intent":"task_pallet","entities":{"pallet_row":null,"pallet_col":null,"row_offset":80,"col_offset":null}}]}'))
    # 测试用例4：无关指令
    print(proc.process('{"intent_list":[]}'))
