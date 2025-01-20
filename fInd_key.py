import json

# 定义递归函数
def extract_values(json_obj, keys_to_find):
    results = {key: None for key in keys_to_find}  # 初始化所有键为 None
    
    def _recursive_search(obj):
        if isinstance(obj, dict):  # 如果是字典
            for key, value in obj.items():
                if key in keys_to_find:  # 如果键匹配
                    results[key] = value
                if isinstance(value, (dict, list)):  # 如果值是嵌套字典或列表，继续递归
                    _recursive_search(value)
        elif isinstance(obj, list):  # 如果是列表
            for item in obj:
                _recursive_search(item)
    
    _recursive_search(json_obj)  # 开始递归
    return results

# 示例 JSON 数据（没有目标字段）
json_data = '''
{
    "name": "example",
    "description": "This is a test case.",
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
