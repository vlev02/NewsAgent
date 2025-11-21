# encoding:UTF-8
import json
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import re

# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
XUNFEI_APPID = os.getenv('XUNFEI_APPID')
XUNFEI_APISecret = os.getenv('XUNFEI_APISecret')
XUNFEI_APIKey = os.getenv('XUNFEI_APIKey')

# Configure API settings
api_key = f"Bearer {XUNFEI_APIKey}"
url = "https://spark-api-open.xf-yun.com/v1/chat/completions"

def create_tech_news_prompt():
    """创建专业的技术资讯搜索prompt"""
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""你是一个专业的技术资讯分析师。今天是{current_date}，请使用联网搜索功能获取以下技术领域的最新动态：

搜索领域：自动驾驶、具身智能、大模型、人工智能
重点关注：特斯拉FSD、人形机器人、AI大模型突破、行业重要动态

请严格按照以下JSON格式返回数据，不要有任何额外的解释或文本：

{{
  "search_date": "{current_date}",
  "summary": "今日技术领域总体趋势的简要描述",
  "news_items": [
    {{
      "id": 1,
      "category": "技术领域分类",
      "title": "新闻标题",
      "content": "详细内容摘要(150-200字)",
      "key_entities": ["相关公司", "相关人物", "技术名称"],
      "source_type": "信息来源平台",
      "significance": "高/中/低",
      "timestamp": "信息发布时间或发现时间"
    }}
  ]
}}

具体要求：
1. 每个技术领域提供2-3条最重要的最新信息
2. 按重要性排序，最重要的信息在前
3. 确保信息准确且是最新的（24小时内）
4. 关键实体要准确识别
5. significance评估基于技术突破性、行业影响力
6. source_type注明如：微博、公众号、科技媒体、学术平台等

现在开始搜索并返回JSON数据："""

    return prompt

def get_structured_news():
    """获取结构化的技术新闻"""
    
    # 创建专业prompt
    prompt = create_tech_news_prompt()
    
    headers = {
        'Authorization': api_key,
        'content-type': "application/json"
    }
    
    body = {
        "model": "4.0Ultra",
        "user": "tech_news_agent",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,  # 改为非流式，便于获取完整JSON
        "temperature": 0.3,  # 较低温度保证输出稳定性
        "max_tokens": 4000,
        "tools": [
            {
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_mode": "deep"
                }
            }
        ]
    }
    print(json.dumps(dict(url=url, json=body, headers=headers, ), ensure_ascii=False, indent=2))
    return({})
    try:
        response = requests.post(url=url, json=body, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        full_response = data['choices'][0]['message']['content']
        
        # 尝试从响应中提取JSON
        json_data = extract_json_from_response(full_response)
        return json_data
        
    except Exception as e:
        print(f"API调用错误: {e}")
        return None

def extract_json_from_response(response_text):
    """从响应文本中提取JSON数据"""
    
    # 方法1: 直接查找JSON结构
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            json_str = json_match.group()
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # 方法2: 如果直接提取失败，尝试清理文本后解析
    try:
        # 移除可能的多余文本
        clean_text = response_text.strip()
        if clean_text.startswith('```json'):
            clean_text = clean_text[7:]
        if clean_text.endswith('```'):
            clean_text = clean_text[:-3]
        
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"原始响应: {response_text}")
        return {"error": "Failed to parse JSON", "raw_response": response_text}

def save_news_to_file(news_data, filename=None):
    """保存新闻数据到文件"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"tech_news_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到: {filename}")
    return filename

def display_news_summary(news_data):
    """以友好格式显示新闻摘要"""
    if not news_data or "error" in news_data:
        print("无法获取有效数据")
        return
    
    print(f"\n{'='*60}")
    print(f"技术动态简报 - {news_data.get('search_date', 'N/A')}")
    print(f"{'='*60}")
    print(f"总体趋势: {news_data.get('summary', 'N/A')}")
    print(f"{'='*60}")
    
    news_items = news_data.get('news_items', [])
    for i, item in enumerate(news_items, 1):
        print(f"\n{i}. [{item.get('category', 'N/A')}] {item.get('title', 'N/A')}")
        print(f"   内容: {item.get('content', 'N/A')}")
        print(f"   关键实体: {', '.join(item.get('key_entities', []))}")
        print(f"   来源: {item.get('source_type', 'N/A')}")
        print(f"   重要性: {item.get('significance', 'N/A')}")
        print(f"   时间: {item.get('timestamp', 'N/A')}")
        print("-" * 60)

# 主程序入口
if __name__ == '__main__':
    print("开始获取最新技术动态...")
    
    # 获取结构化新闻数据
    news_data = get_structured_news()
    
    if news_data:
        # 显示摘要
        display_news_summary(news_data)
        
        # 保存到文件
        filename = save_news_to_file(news_data)
        
        print(f"\n获取完成! 共找到 {len(news_data.get('news_items', []))} 条信息")
    else:
        print("获取技术动态失败")