import json
import os
from typing import Any, Dict, Union


class JSONHandler:
    """
    JSON文件读写处理器
    支持多种数据类型的读写，自动处理文件创建
    """
    
    def __init__(self, filename: str = "config.json"):
        """
        初始化JSON处理器
        
        Args:
            filename: JSON文件名
        """
        self.filename = filename
    
    def write_to_json(self, data: Dict[str, Any]) -> bool:
        """
        将数据写入JSON文件
        
        Args:
            data: 要写入的数据字典
            
        Returns:
            bool: 写入是否成功
        """
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"写入JSON文件时出错: {e}")
            return False
    
    def read_from_json(self, default_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        从JSON文件读取数据
        
        Args:
            default_data: 如果文件不存在，返回的默认数据
            
        Returns:
            Dict[str, Any]: 读取到的数据字典
        """
        if not os.path.exists(self.filename):
            print(f"文件 {self.filename} 不存在，返回默认数据")
            return default_data or {}
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return default_data or {}
        except Exception as e:
            print(f"读取JSON文件时出错: {e}")
            return default_data or {}
    
    def update_json(self, key: str, value: Any) -> bool:
        """
        更新JSON文件中的特定键值
        
        Args:
            key: 要更新的键
            value: 新的值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 读取现有数据
            existing_data = self.read_from_json({})
            
            # 更新数据
            existing_data[key] = value
            
            # 写回文件
            return self.write_to_json(existing_data)
        except Exception as e:
            print(f"更新JSON文件时出错: {e}")
            return False
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        获取JSON文件中特定键的值
        
        Args:
            key: 要获取的键
            default: 如果键不存在，返回的默认值
            
        Returns:
            Any: 键对应的值或默认值
        """
        data = self.read_from_json()
        return data.get(key, default)
    
    def add_multiple(self, data_dict: Dict[str, Any]) -> bool:
        """
        批量添加多个键值对到JSON文件
        
        Args:
            data_dict: 要添加的键值对字典
            
        Returns:
            bool: 添加是否成功
        """
        try:
            # 读取现有数据
            existing_data = self.read_from_json({})
            
            # 更新数据（新数据会覆盖同名键）
            existing_data.update(data_dict)
            
            # 写回文件
            return self.write_to_json(existing_data)
        except Exception as e:
            print(f"批量添加数据时出错: {e}")
            return False
    
    def delete_multiple(self, keys: list) -> bool:
        """
        批量删除多个键
        
        Args:
            keys: 要删除的键列表
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 读取现有数据
            existing_data = self.read_from_json({})
            
            # 删除指定的键
            for key in keys:
                existing_data.pop(key, None)
            
            # 写回文件
            return self.write_to_json(existing_data)
        except Exception as e:
            print(f"批量删除数据时出错: {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        清空JSON文件中的所有数据
        
        Returns:
            bool: 清空是否成功
        """
        try:
            # 写入空字典
            return self.write_to_json({})
        except Exception as e:
            print(f"清空JSON文件时出错: {e}")
            return False
    
    def traverse_objects(self, fields: list = None) -> list:
        """
        遍历JSON中的所有对象，返回指定字段组合的数据列表
        
        Args:
            fields: 要返回的字段列表，如果为None则返回所有字段
            
        Returns:
            list: 包含所有对象信息的列表，每个元素是一个字典
        """
        data = self.read_from_json()
        result = []
        
        for obj_id, obj_data in data.items():
            if fields is None:
                # 返回所有字段
                result.append({
                    "id": obj_id,
                    **obj_data
                })
            else:
                # 只返回指定字段
                filtered_obj = {"id": obj_id}
                for field in fields:
                    if field in obj_data:
                        filtered_obj[field] = obj_data[field]
                    elif field == "id_path":
                        # 特殊处理：生成ID路径组合
                        filtered_obj["id_path"] = f"{obj_id}/{obj_data.get('name', 'unknown')}"
                    else:
                        filtered_obj[field] = None
                result.append(filtered_obj)
        
        return result
    
    def get_object_ids(self) -> list:
        """
        获取JSON中所有对象的ID列表
        
        Returns:
            list: 包含所有对象ID的列表
        """
        data = self.read_from_json()
        return list(data.keys())
    
    def get_objects_by_type(self, object_type: str) -> list:
        """
        根据类型筛选对象
        
        Args:
            object_type: 对象类型（如"Sound", "Event"等）
            
        Returns:
            list: 符合指定类型的对象列表
        """
        all_objects = self.traverse_objects()
        return [obj for obj in all_objects if obj.get('type') == object_type]
    
    def get_object_by_id(self, obj_id: str) -> dict:
        """
        根据ID获取特定对象
        
        Args:
            obj_id: 对象ID
            
        Returns:
            dict: 对象信息字典，如果不存在则返回空字典
        """
        data = self.read_from_json()
        return data.get(obj_id, {})


def save_wwise_objects_to_json(objects: list, filename: str = "test_config.json") -> bool:
    """
    将Wwise对象列表保存到JSON文件
    
    Args:
        objects: Wwise对象列表，每个对象应包含id、name、type等字段
        filename: JSON文件名
        
    Returns:
        bool: 保存是否成功
    """
    handler = JSONHandler(filename)
    
    # 创建字典，以ID为键存储对象信息
    data_dict = {}
    for obj in objects:
        data_dict[obj['id']] = obj
    
    return handler.add_multiple(data_dict)


# 使用示例和测试函数
def main():
    """使用示例"""
    handler = JSONHandler("test_config.json")
    
    print("=== 清空JSON文件 ===")
    if handler.clear_all():
        print("清空成功！")
    
    # 示例1: 写入各种数据类型
    sample_data = {
        "integer_value": 42,
        "string_value": "Hello, World!",
        "float_value": 3.14159,
        "boolean_value": True,
        "list_value": [1, 2, 3, "four", 5.0],
        "dict_value": {
            "nested_int": 100,
            "nested_str": "嵌套字符串"
        }
    }
    
    print("\n=== 写入数据到JSON ===")
    if handler.write_to_json(sample_data):
        print("数据写入成功！")
    
    print("\n=== 从JSON读取数据 ===")
    read_data = handler.read_from_json()
    print(f"读取到的数据: {read_data}")
    
    print("\n=== 获取特定值 ===")
    int_value = handler.get_value("integer_value")
    str_value = handler.get_value("string_value")
    print(f"integer_value: {int_value} (类型: {type(int_value)})")
    print(f"string_value: {str_value} (类型: {type(str_value)})")
    
    print("\n=== 更新特定键值 ===")
    if handler.update_json("integer_value", 999):
        print("更新成功！")
    
    print("\n=== 验证更新结果 ===")
    updated_data = handler.read_from_json()
    print(f"更新后的数据: {updated_data}")
    
    print("\n=== 批量添加数据 ===")
    new_data = {
        "new_int": 123,
        "new_str": "新字符串",
        "new_list": ["a", "b", "c"]
    }
    if handler.add_multiple(new_data):
        print("批量添加成功！")
    
    print("\n=== 验证批量添加结果 ===")
    after_add_data = handler.read_from_json()
    print(f"批量添加后的数据: {after_add_data}")
    
    print("\n=== 批量删除数据 ===")
    keys_to_delete = ["integer_value", "new_str"]
    if handler.delete_multiple(keys_to_delete):
        print("批量删除成功！")
    
    print("\n=== 验证批量删除结果 ===")
    after_delete_data = handler.read_from_json()
    print(f"批量删除后的数据: {after_delete_data}")
    
    print("\n=== 测试Wwise对象保存函数 ===")
    # 模拟Wwise对象数据
    wwise_objects = [
        {
            "id": "{AE8F5D36-4F73-426A-9222-39D756105309}",
            "name": "Bang_R",
            "type": "Sound"
        },
        {
            "id": "{B1234567-8910-1112-1314-151617181920}",
            "name": "Explosion",
            "type": "Sound"
        }
    ]
    
    if save_wwise_objects_to_json(wwise_objects, "wwise_objects.json"):
        print("Wwise对象保存成功！")
    
    # 读取验证
    wwise_handler = JSONHandler("wwise_objects.json")
    wwise_data = wwise_handler.read_from_json()
    print(f"Wwise对象数据: {wwise_data}")
    
    print("\n=== 测试JSON遍历功能 ===")
    
    print("\n--- 获取所有对象ID ---")
    object_ids = wwise_handler.get_object_ids()
    print(f"所有对象ID: {object_ids}")
    
    print("\n--- 遍历所有字段 ---")
    all_objects = wwise_handler.traverse_objects()
    for obj in all_objects:
        print(f"对象: {obj}")
    
    print("\n--- 遍历指定字段 (id, name, type) ---")
    filtered_objects = wwise_handler.traverse_objects(fields=["id", "name", "type"])
    for obj in filtered_objects:
        print(f"对象: {obj}")
    
    print("\n--- 遍历包含ID路径的字段 ---")
    objects_with_path = wwise_handler.traverse_objects(fields=["id", "name", "type", "id_path"])
    for obj in objects_with_path:
        print(f"对象: {obj}")
    
    print("\n--- 根据类型筛选对象 ---")
    sound_objects = wwise_handler.get_objects_by_type("Sound")
    print(f"Sound类型对象: {sound_objects}")
    
    print("\n--- 根据ID获取特定对象 ---")
    specific_object = wwise_handler.get_object_by_id("{AE8F5D36-4F73-426A-9222-39D756105309}")
    print(f"特定对象: {specific_object}")


if __name__ == "__main__":
    main()
