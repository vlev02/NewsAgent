import requests
import json
import os

# Disable proxy for direct API calls
# This removes any system proxy configuration that might block requests
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

request_args =json.loads(r"""
{
  "url": "https://api.hunyuan.cloud.tencent.com/v1/chat/completions",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer sk-cj5AcQjaGzUzcwOO4IyXgZcYqmMgpstb9BlFH7KJ67fvU72S",
    "Content-Type": "application/json"
  },
  "json": {
    "model": "hunyuan-turbo",
    "stream": false,
    "temperature": 0.3,
    "enable_enhancement": true,
    "search_info": true,
    "messages": [
      {
        "role": "user",
        "content": "你是一个专业的技术资讯分析师。今天是2025-11-21，请使用联网搜索功能获取以下技术领域的最新动态：\n\n## 搜索范围\n\n**主要领域：**\n\n- 自动驾驶\n\n- 具身智能\n\n- 大模型\n\n- 人工智能\n\n\n**重点关注：**\n\n- 特斯拉FSD\n\n- 人形机器人\n\n- AI大模型突破\n\n- 行业重要动态\n\n\n## 搜索参数\n- 时间范围：最近一周\n- 语言：中文\n- 启用自动分类：True\n\n## 输出要求\n\n请严格按照以下JSON格式返回数据，不要有任何额外的解释或文本：\n\n```json\n{\n  \"search_date\": \"2025-11-21\",\n  \"summary\": \"今日技术领域总体趋势分析（2-3句话）\",\n  \"news_items\": [\n    {\n      \"id\": 1,\n      \"category\": \"技术领域分类（由AI自动分类）\",\n      \"title\": \"新闻标题\",\n      \"content\": \"详细内容摘要(150-200字)\",\n      \"key_entities\": [\"相关公司\", \"相关人物\", \"技术名称\"],\n      \"source_type\": \"信息来源平台\",\n      \"source_link\": \"信息源URL\",\n      \"significance\": \"高/中/低\",\n      \"timestamp\": \"信息发布时间（YYYY-MM-DD HH:MM格式）\"\n    }\n  ]\n}\n```\n\n## 具体要求\n\n1. **结果数量：** 共8-10条最重要的信息\n2. **排序：** 按重要性排序\n3. **自动分类：** AI应基于内容自动分类各条信息\n4. **时效性：** 最近一周内的信息\n5. **关键实体识别：** 准确识别公司、人物、技术名称\n6. **重要性评估：** 基于技术突破性和行业影响力\n\n现在开始执行搜索："
      }
    ]
  }
}
"""
)

# Add proxies={}  to disable any proxies that might be set
# This ensures direct connection to the API
request_args['proxies'] = {}

print(request_args)
print("=" * 30)
response = requests.request(**request_args)
print(response)
print(response.json())