import json

# 定义递归函数
def extract_values(json_obj, keys_to_find):
    results = {}  # 用于存储找到的键值对
    
    if isinstance(json_obj, dict):  # 如果是字典
        for key, value in json_obj.items():
            if key in keys_to_find:  # 如果键匹配
                results[key] = value
            if isinstance(value, (dict, list)):  # 如果值是嵌套字典或列表，继续递归
                results.update(extract_values(value, keys_to_find))
    
    elif isinstance(json_obj, list):  # 如果是列表
        for item in json_obj:
            results.update(extract_values(item, keys_to_find))
    
    return results

# 示例 JSON 数据
json_data = '''
{
    "name": "example",
    "website": "https://example.com",
    "socials": {
        "twitter": "@example",
        "other": {
            "telegram": "example_chat"
        }
    },
    "tags": ["news", "blog"]
}
'''

# 加载 JSON 数据
data = json.loads(json_data)

# 需要查找的字段
keys = {"website", "twitter", "telegram"}

# 提取值
found_values = extract_values(data, keys)

# 输出结果
print(found_values)
