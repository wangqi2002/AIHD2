"""
主程序
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from modelscope import AutoModelForCausalLM, AutoTokenizer
from funasr import AutoModel
import time

# 添加模块路径
sys.path.append(str(Path(__file__).parent))
from congfig import RAGConfig, DEFAULT_CONFIG
from utils.ur5e import UR_Robot

# 语音控制
from voice_control_modules import process_intent

# 饮品抓取
from drink_grab_modules import post_process_drink

# 继电器码垛
from pallet_modules import post_process_pallet

from dotenv import load_dotenv

# 配置日志等级、格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class RobotAgentSystem:
    """机器人助手"""

    def __init__(self, config: RAGConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.voice_control_module = None
        self.drink_grab_module = None
        self.initialize_system()

        # # 检查API密钥
        # if not os.getenv("MOONSHOT_API_KEY"):
        #     raise ValueError("请设置 MOONSHOT_API_KEY 环境变量")
    
    def initialize_system(self):
        """初始化所有模块"""
        self._initialize_system_asr()
        print("✅ asr初始化完成！")
        self._initialize_system_llm()
        print("✅ llm初始化完成！")

        """初始化UR5e"""
        # self.ur_robot = UR_Robot()

        """初始化语音控制模块"""
        self.process_intent = process_intent.ProcessIntent()

        """初始化饮品抓取模块"""
        self.process_intent_drink = post_process_drink.DrinkIntentProcessor()

        """初始化继电器码垛模块"""
        self.process_intent_pallet = post_process_pallet.PalletIntentProcessor()

    def _initialize_system_asr(self):
        self.asr_model = AutoModel(
        model="/home/win/.cache/modelscope/hub/FunAudioLLM/Fun-ASR-Nano-2512",
        trust_remote_code=True,
        remote_code="/home/win/Project/P03/Fun-ASR//model.py",
        device="cuda:0",
    )   

    def _initialize_system_llm(self):
        """
        初始化Qwen模型
        """
        model_name = self.config.local_model
        # 加载tokenizer和模型
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        
    def audio_to_text(self, audio_path: str) -> str:
        res = self.asr_model.generate(
        input=[audio_path],
        cache={},
        batch_size=1,
        hotwords=["拿一杯", "可乐", "芬达", "雪碧", "码垛", "继电器"],
        language="中文",
        itn=True, # or False
    )
        text = res[0]["text"]
        print(text)
        return text

    def router_query(self,user_input):
        """
        根据输入的prompt生成回复
        """
        prompt_file = Path(self.config.prompt_path) / "router_prompt.txt"
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception as e:
            logger.error(f"加载router_prompt失败 {prompt_file}: {e}")

        thinking_content, intent_content, inference_time = self._generate_response(
            user_input, system_prompt, max_new_tokens=20, temperature=0, flag_do_sample=False
        )
        return intent_content
    
    def voice_control(self, user_input):
        """
        根据输入的prompt生成回复
        """
        prompt_file = Path(self.config.prompt_path) / "voice_control.txt"
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception as e:
            logger.error(f"加载router_prompt失败 {prompt_file}: {e}")

        thinking_content, intent_content, inference_time = self._generate_response(
            user_input, system_prompt, max_new_tokens=50, temperature=0, flag_do_sample=False
        )
        return intent_content
    
    def drink_grab(self, user_input):
        """
        根据输入的prompt生成回复
        """
        prompt_file = Path(self.config.prompt_path) / "drink_grab.txt"
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception as e:
            logger.error(f"加载router_prompt失败 {prompt_file}: {e}")

        thinking_content, intent_content, inference_time = self._generate_response(
            user_input, system_prompt, max_new_tokens=50, temperature=0, flag_do_sample=False
        )
        return intent_content
    
    def pallet(self, user_input):
        """
        根据输入的prompt生成回复
        """
        prompt_file = Path(self.config.prompt_path) / "pallet.txt"
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception as e:
            logger.error(f"加载router_prompt失败 {prompt_file}: {e}")

        thinking_content, intent_content, inference_time = self._generate_response(
            user_input, system_prompt, max_new_tokens=50, temperature=0, flag_do_sample=False
        )
        return intent_content
    
    def excute_code(self, router_type, control_code):
        for each in control_code['function']: # 运行智能体规划编排的每个函数
            print('\n开始执行动作', each)
            eval(each)

    def _generate_response(self, prompt, system_prompt, max_new_tokens=100, temperature=0, flag_do_sample = False):

        # 准备模型输入
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": prompt})
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False  # 在思考模式和非思考模式之间切换，默认为True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        start_time = time.time()

        # 执行文本生成
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            temperature= temperature,
            do_sample=False
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

        # 解析思考内容
        try:
            # rindex查找151668 (</think>)
            index = len(output_ids) - output_ids[::-1].index(151668) - 1
        except ValueError:
            index = 0

        thinking_content = self.tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
        content = self.tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

        end_time = time.time()
        inference_time = end_time - start_time

        return thinking_content, content, inference_time
    
    # 测试用
    def chat_loop(self):
        """
        启动交互式对话循环
        """
        print("开始对话，输入 'quit' 或 'exit' 退出程序，输入 'clear' 清空历史记录")
        
        while True:
            user_input = input("\n请输入您的问题: ")
            
            if user_input.lower().strip() in ['quit', 'exit', '退出']:
                print("程序已退出")
                break
            
            if not user_input.strip():
                print("输入不能为空，请重新输入")
                continue
            
            router_type = self.router_query(user_input)
            print("意图识别结果:", router_type)

            if router_type == 'voice_control':
                control_intent = self.voice_control(user_input)    
                print("意图识别结果:", control_intent)
                control_code = self.process_intent.intent_to_function(control_intent)
                print("控制指令:", control_code)
                
            elif router_type == 'drink_grab':
                control_intent = self.drink_grab(user_input)
                print("意图识别结果:", control_intent)
                control_code = self.process_intent_drink.process(control_intent)
                print("控制指令:", control_code)

            elif router_type == 'pallet':
                control_intent = self.pallet(user_input)
                print("意图识别结果:", control_intent)
                control_code = self.process_intent_pallet.process(control_intent)
                print("控制指令:", control_code)

            else:
                print("无法识别意图，请重新输入")

    # 对接语音识别文本
    def chat(self, user_input):

        router_type = self.router_query(user_input)
        print("意图识别结果:", router_type)

        if router_type == 'voice_control':
            control_intent = self.voice_control(user_input)    
            print("意图识别结果:", control_intent)
            control_code = self.process_intent.intent_to_function(control_intent)
            print("控制指令:", control_code)
            
        elif router_type == 'drink_grab':
            control_intent = self.drink_grab(user_input)
            print("意图识别结果:", control_intent)
            control_code = self.process_intent_drink.process(control_intent)
            print("控制指令:", control_code)

        elif router_type == 'pallet':
            control_intent = self.pallet(user_input)
            print("意图识别结果:", control_intent)
            control_code = self.process_intent_pallet.process(control_intent)
            print("控制指令:", control_code)

        else:
            print("无法识别意图，请重新输入")
            return {"router":router_type,"intent": "无法识别意图，请重新输入"}

        return {"router":router_type,"intent": control_intent, "code": control_code}

             
def main():
    """主函数"""
    try:
        # 创建RAG系统
        robot_system = RobotAgentSystem()
        
        # 运行交互式问答
        robot_system.chat_loop()
        
    except Exception as e:
        logger.error(f"系统运行出错: {e}")
        print(f"系统错误: {e}")

if __name__ == "__main__":
    main()