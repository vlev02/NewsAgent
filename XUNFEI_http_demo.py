# encoding:UTF-8
'''
https://www.xfyun.cn/doc/spark/HTTP%E8%B0%83%E7%94%A8%E6%96%87%E6%A1%A3.html#_3-%E8%AF%B7%E6%B1%82%E8%AF%B4%E6%98%8E
'''
import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
XUNFEI_APPID = os.getenv('XUNFEI_APPID')
XUNFEI_APISecret = os.getenv('XUNFEI_APISecret')
XUNFEI_APIKey = os.getenv('XUNFEI_APIKey')
XUNFEI_APIPassword = os.getenv('XUNFEI_APIPassword')

# Configure API settings
url = "https://spark-api-open.xf-yun.com/v1/chat/completions"

# 请求模型，并将结果输出
def get_answer(message):
    # 初始化请求头
    headers = {
        'Authorization': f'Bearer {XUNFEI_APIPassword}',
        'Content-Type': 'application/json'
    }
    body = {
        "model": "4.0Ultra",
        "user": "user_id",
        "messages": message,
        # 下面是可选参数
        "stream": True,
        "tools": [
            {
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_mode":"deep"
                }
            }
        ]
    }
    full_response = ""  # 存储返回结果
    isFirstContent = True  # 首帧标识

    response = requests.post(url=url, json=body, headers=headers, stream=True)

    # 检查响应状态
    if response.status_code != 200:
        print(f"\nError: API返回状态码 {response.status_code}")
        print(f"响应: {response.text}")
        return ""

    # 处理流式响应
    for chunks in response.iter_lines():
        # 跳过空行
        if not chunks:
            continue

        # 检查是否为完成标记
        if b'[DONE]' in chunks:
            break

        try:
            # SSE格式数据以"data: "开头
            if chunks.startswith(b'data: '):
                data_org = chunks[6:]  # 去除"data: "前缀
            else:
                continue

            # 跳过空数据
            if not data_org.strip():
                continue

            # 解析JSON
            chunk = json.loads(data_org)

            # 检查是否包含choices
            if 'choices' not in chunk or len(chunk['choices']) == 0:
                continue

            # 获取delta内容
            delta = chunk['choices'][0].get('delta', {})

            # 判断最终结果状态并输出
            if 'content' in delta and delta['content']:
                content = delta['content']
                if isFirstContent:
                    isFirstContent = False
                print(content, end="")
                full_response += content

        except json.JSONDecodeError as e:
            # JSON解析错误，跳过该chunk
            continue
        except Exception as e:
            print(f"\n处理响应时出错: {e}")
            continue

    return full_response


# 管理对话历史，按序编为列表
def getText(text,role, content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text

# 获取对话中的所有角色的content长度
def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

# 判断长度是否超长，当前限制8K tokens
def checklen(text):
    while (getlength(text) > 11000):
        del text[0]
    return text


#主程序入口
if __name__ =='__main__':

    #对话历史存储列表
    chatHistory = []
    #循环对话轮次
    while (1):
        # 等待控制台输入
        Input = input("\n" + "我:")
        if Input in ["exit","quit"]:
            print("退出对话")
            break   
        question = checklen(getText(chatHistory,"user", Input))
        # 开始输出模型内容
        print("星火:", end="")
        getText(chatHistory,"assistant", get_answer(question))