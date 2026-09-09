import json


class DrinkIntentProcessor:
    def __init__(self):
        self.drink_name_map = {
            "cola": "可乐",
            "sprite": "雪碧",
            "fenda": "芬达"
        }

    def process(self, intent_result_str: str) -> str:
        """
        处理饮品task_drink意图，输入LLM输出的intent json字符串，输出业务结果json字符串
        :param intent_result_str: LLM输出JSON字符串，例：{"intent_list":[{"intent":"task_drink","entities":{"drink_type":"none"}}]}
        :return: json字符串，对齐需求示例
            口渴未指定：{"function": [], "response": "好的，这里有可乐、雪碧和芬达，您想要哪款？"}
            指定芬达：{"function":["ur_robot.task_drink()"], "response":"好的，马上为您提供芬达", "type":"fenda"}
        """
        function_list = []
        response_list = []
        out_type = None

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
                "response": "无有效饮品指令"
            }, ensure_ascii=False)

        for item in intent_items:
            intent_name = item.get("intent", "")
            entities = item.get("entities", {})

            if intent_name != "task_drink":
                response_list.append("非饮品任务")
                continue

            drink_type = entities.get("drink_type", "none")
            if drink_type == "none":
                response_list.append("好的，这里有可乐、雪碧和芬达，您想要哪款？")
            elif drink_type in self.drink_name_map:
                drink_cn = self.drink_name_map[drink_type]
                function_list.append("ur_robot.task_drink()")
                response_list.append(f"好的，马上为您提供{drink_cn}")
                out_type = drink_type
            else:
                response_list.append(f"暂不支持该饮品：{drink_type}")

        final = {
            "function": function_list,
            "response": "；".join(response_list)
        }
        if out_type is not None:
            final["type"] = out_type

        return json.dumps(final, ensure_ascii=False)


if __name__ == "__main__":
    proc = DrinkIntentProcessor()
    print(proc.process('{"intent_list":[{"intent":"task_drink","entities":{"drink_type":"none"}}]}'))
    print(proc.process('{"intent_list":[{"intent":"task_drink","entities":{"drink_type":"fenda"}}]}'))
    print(proc.process('{"intent_list":[{"intent":"task_drink","entities":{"drink_type":"cola"}}]}'))
    print(proc.process('{"intent_list":[{"intent":"task_drink","entities":{"drink_type":"sprite"}}]}'))
