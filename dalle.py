# encoding:utf-8
# 指定文件编码为 UTF-8，这对于处理非英文字符很重要

import plugins  # 用于处理插件相关功能的基类和装饰器
from plugins import *  # 导入 plugins 模块的所有公开内容，提供最大的灵活性
from bridge.context import ContextType  # 用于定义事件处理时的上下文类型
from bridge.reply import Reply, ReplyType  # 用于创建和管理回复消息的类型
from channel.chat_message import ChatMessage  # 用于处理聊天消息数据结构
from common.log import logger  # 用于记录日志
from config import conf  # 用于加载和管理配置文件
import json  # 用于处理 JSON 数据，可能用于配置文件的加载和解析
import os  # 用于处理文件和目录路径

# 根据插件的具体需求，后续可能还需要导入其他特定的库
@plugins.register(
    name="dalle", 
    desire_priority=1, 
    hidden=True, 
    desc="一个可以调用第三方画图API的插件", 
    version="1.0", 
    author="Pi"
)

class DallePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.model = self.config.get('dalle_model', 'dalle-mini')  # 默认使用 "dalle-mini" 模型

    def load_config(self):
        # 加载配置文件
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.error("配置文件不存在，请确保 config.json 文件在正确的路径下")
            return {}

    def on_handle_context(self, e_context):
        content = e_context["context"]["msg"].content.strip()
        if content.startswith("$ht "):
            prompt = content[4:]
            self.handle_dalle_request(prompt, e_context)
        elif content.startswith("$setmodel "):
            new_model = content[10:]
            self.model = new_model
            self.config['dalle_model'] = new_model  # 更新内存中的配置
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = f"模型已更改为: {new_model}"
            e_context["reply"] = reply

    def handle_dalle_request(self, prompt, e_context):
        image_url = self.call_dalle_api(prompt)
        reply = Reply()
        if image_url:
            reply.type = ReplyType.IMAGE
            reply.content = image_url
        else:
            reply.type = ReplyType.TEXT
            reply.content = "我累了，请休息一会再试吧。"
        e_context["reply"] = reply

    def call_dalle_api(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.config.get('openai_api_key')}",
            "Content-Type": "application/json"
        }
        data = {
            "prompt": prompt,
            "n": 1,  # 生成一张图片
            "model": self.model  # 使用配置中的模型
        }
        response = requests.post(self.config.get('dalle_base_url'), headers=headers, json=data)
        if response.status_code == 200:
            image_data = response.json()
            return image_data['data'][0]['url']
        else:
            logger.error(f"Failed to call DALL-E API: {response.status_code} {response.text}")
            return None


