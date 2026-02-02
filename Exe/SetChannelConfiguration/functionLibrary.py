"""
Wwise 对象分析器函数库

执行顺序：
1. 调用 analyze_custom_objects() 入口函数
2. 内部创建 WwiseObjectAnalyzer 实例
3. 调用 analyze_by_ids() 进行多线程分析
4. 返回分析结果数据

主要功能：
- 多线程并行遍历 Wwise 对象层次结构
- 支持按对象类型执行不同的处理逻辑
- 提供统计信息和层次结构显示
- 支持对象类型过滤

作者: Assistant
版本: 1.0
"""

from waapi import WaapiClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time


class ObjectTypeProcessor:
    """
    对象类型处理器 - 针对不同类型的对象执行不同的处理函数
    
    每个处理函数负责特定类型对象的显示和逻辑处理
    可以扩展此类来添加新的对象类型处理
    """
    
    def process_audiofilesource(self, obj, client=None):
        """处理 AudioFileSource 对象 - 音频文件源"""
        print(f"🎵 音频文件源: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 路径: {obj.get('path', 'N/A')}")
        if 'ChannelConfigOverride' in obj:
            print(f"   - 声道配置: {obj['ChannelConfigOverride']}")
        
        # 设置ChannelConfigOverride属性
        if client:
            source_id = obj.get('id')
            try:
                result = client.call("ak.wwise.core.object.setProperty", {
                    "object": source_id,
                    "property": "ChannelConfigOverride",
                    "value": 49410
                })
                print(f"   ✅ 成功设置声道配置为 49410")
            except Exception as e:
                print(f"   ❌ 设置声道配置失败: {e}")
        print()

    def process_sound(self, obj, client=None):
        """处理 Sound 对象 - 声音对象"""
        print(f"🔊 Sound对象: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 类型: {obj.get('type', 'N/A')}")
        print()

    def process_workunit(self, obj, client=None):
        """处理 WorkUnit 对象 - 工作单元"""
        print(f"📁 工作单元: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 路径: {obj.get('path', 'N/A')}")
        print()

    def process_actormixer(self, obj, client=None):
        """处理 ActorMixer 对象 - 角色混音器"""
        print(f"🎭 角色混音器: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 类ID: {obj.get('classId', 'N/A')}")
        print()

    def process_randomsequencecontainer(self, obj, client=None):
        """处理 Random/Sequence Container 对象 - 随机/序列容器"""
        container_type = obj.get('type', 'Container')
        icon = "🎲" if "Random" in container_type else "📊"
        print(f"{icon} 容器对象: {obj.get('name', 'Unnamed')} [{container_type}]")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 路径: {obj.get('path', 'N/A')}")
        print()

    def process_blendcontainer(self, obj, client=None):
        """处理 Blend Container 对象 - 混合容器"""
        print(f"🎛️ 混合容器: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 类ID: {obj.get('classId', 'N/A')}")
        print()

    def process_default(self, obj, client=None):
        """默认处理函数 - 处理未知类型的对象"""
        obj_type = obj.get('type', 'Unknown')
        obj_name = obj.get('name', 'Unnamed')
        print(f"📄 {obj_type}: {obj_name}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 路径: {obj.get('path', 'N/A')}")
        print()


class ParallelWwiseTraverser:
    """
    并行 Wwise 对象遍历器
    
    采用广度优先+深度优先的多线程遍历策略：
    1. 广度优先获取第一层子对象
    2. 为每个子树开启独立线程进行深度优先遍历
    3. 合并所有线程的结果
    """

    def __init__(self, client, max_workers=8):
        """
        初始化遍历器
        
        Args:
            client: WAAPI 客户端实例
            max_workers: 最大线程数，默认8个
        """
        self.client = client
        self.max_workers = max_workers
        self.lock = threading.Lock()

    def get_children_ids(self, object_id):
        """
        广度优先：获取对象的直接子对象ID
        
        Args:
            object_id: 父对象ID
            
        Returns:
            list: 子对象ID和类型的元组列表 [(id, type), ...]
        """
        try:
            result = self.client.call("ak.wwise.core.object.get", {
                "from": {"id": [object_id]},
                "transform": [{"select": ["children"]}],
                "options": {"return": ["id", "name", "type"]}
            })

            if "return" in result and result["return"]:
                return [(obj["id"], obj.get("type", "Unknown")) for obj in result["return"]]
            return []
        except Exception as e:
            print(f"获取子对象ID时出错 {object_id}: {e}")
            return []

    def get_object_details(self, object_id, object_type_filter=None):
        """
        获取单个对象的详细信息
        
        Args:
            object_id: 对象ID
            object_type_filter: 对象类型过滤器
            
        Returns:
            list: 符合条件的对象信息列表
        """
        try:
            result = self.client.call("ak.wwise.core.object.get", {
                "from": {"id": [object_id]},
                "options": {
                    "return": ["id", "name", "type", "path", "classId", "ChannelConfigOverride"]
                }
            })

            objects = []
            if "return" in result and result["return"]:
                current_obj = result["return"][0]
                if object_type_filter is None or current_obj.get("type") == object_type_filter:
                    objects.append(current_obj)

            return objects
        except Exception as e:
            print(f"获取对象详情时出错 {object_id}: {e}")
            return []

    def parallel_deep_traverse(self, root_ids, object_type_filter=None):
        """
        并行深度优先遍历主函数
        
        Args:
            root_ids: 根对象ID列表
            object_type_filter: 对象类型过滤器
            
        Returns:
            list: 所有遍历到的对象信息列表
        """
        all_objects = []
        
        # 第一步：为每个根对象广度优先获取第一层子对象
        all_first_level_children = []
        root_info = []
        
        for root_id in root_ids:
            first_level_children = self.get_children_ids(root_id)
            all_first_level_children.extend(first_level_children)
            root_info.append((root_id, len(first_level_children)))
        
        total_children = len(all_first_level_children)
        print(f"🎯 找到 {len(root_ids)} 个根对象")
        for root_id, child_count in root_info:
            print(f"   - 对象 {root_id}: {child_count} 个直接子对象")
        print(f"🚀 总共 {total_children} 个子树，启动 {min(self.max_workers, total_children)} 个线程进行并行处理...")
        
        # 第二步：使用线程池并行处理每个子树
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有子树的任务
            future_to_child = {
                executor.submit(self._traverse_subtree, child_id, object_type_filter): child_id 
                for child_id, child_type in all_first_level_children
            }
            
            # 收集结果
            completed_count = 0
            for future in as_completed(future_to_child):
                child_id = future_to_child[future]
                completed_count += 1
                try:
                    subtree_objects = future.result()
                    with self.lock:
                        all_objects.extend(subtree_objects)
                    print(f"✅ 完成子树 {completed_count}/{total_children}")
                except Exception as e:
                    print(f"❌ 处理子对象 {child_id} 时出错: {e}")
        
        return all_objects

    def _traverse_subtree(self, root_id, object_type_filter=None):
        """
        遍历单个子树（递归深度优先）
        
        Args:
            root_id: 子树根节点ID
            object_type_filter: 对象类型过滤器
            
        Returns:
            list: 子树中的所有对象信息
        """
        objects = []

        # 获取当前对象的详细信息
        current_objects = self.get_object_details(root_id, object_type_filter)
        objects.extend(current_objects)

        # 递归获取子对象
        children = self.get_children_ids(root_id)
        for child_id, child_type in children:
            child_objects = self._traverse_subtree(child_id, object_type_filter)
            objects.extend(child_objects)

        return objects

    def get_objects_details(self, object_ids):
        """
        获取多个对象的详细信息
        
        Args:
            object_ids: 对象ID列表
            
        Returns:
            list: 对象详细信息列表
        """
        try:
            result = self.client.call("ak.wwise.core.object.get", {
                "from": {"id": object_ids},
                "options": {
                    "return": ["id", "name", "type", "path", "classId"]
                }
            })
            
            return result.get("return", [])
        except Exception as e:
            print(f"获取对象详情时出错: {e}")
            return []


class WwiseObjectAnalyzer:
    """
    Wwise 对象分析器主类
    
    协调整个分析流程，包括：
    - 对象遍历
    - 类型处理
    - 统计显示
    - 层次结构展示
    """

    def __init__(self, client, max_workers=8):
        """
        初始化分析器
        
        Args:
            client: WAAPI 客户端实例
            max_workers: 最大线程数
        """
        self.client = client
        self.traverser = ParallelWwiseTraverser(client, max_workers)
        self.processor = ObjectTypeProcessor()

    def analyze_by_ids(self, object_ids, object_type_filter=None):
        """
        核心分析函数：根据ID数组分析对象
        
        Args:
            object_ids: Wwise对象ID列表
            object_type_filter: 可选的对象类型过滤器
            
        Returns:
            list: 所有分析到的对象数据，包含ID、名称、类型等信息
        """
        if not object_ids:
            print("❌ 对象ID列表为空")
            return None

        print(f"🎯 开始分析 {len(object_ids)} 个对象:")
        print("=" * 60)
        
        # 获取根对象的详细信息
        root_objects = self.traverser.get_objects_details(object_ids)
        
        for i, obj in enumerate(root_objects, 1):
            obj_name = obj.get('name', 'Unnamed')
            obj_type = obj.get('type', 'Unknown')
            obj_id = obj.get('id', 'N/A')
            print(f"{i}. {obj_name} [{obj_type}] (ID: {obj_id})")
        
        print("=" * 60)
        
        # 并行遍历所有对象及其子对象
        print("\n🔍 开始并行遍历所有对象及其子对象...")
        start_time = time.time()
        all_objects = self.traverser.parallel_deep_traverse(object_ids, object_type_filter)
        elapsed_time = time.time() - start_time
        
        # 将根对象也加入到结果中
        root_objects_in_result = []
        for root_obj in root_objects:
            # 检查是否已经在结果中（避免重复）
            if not any(obj.get('id') == root_obj.get('id') for obj in all_objects):
                root_objects_in_result.append(root_obj)
        
        all_objects.extend(root_objects_in_result)
        
        # 按类型处理对象
        self._process_objects_by_type(all_objects)
        
        # 显示统计信息
        self._show_statistics(all_objects, elapsed_time, len(object_ids))
        
        # 显示层次结构
        self._show_hierarchies(object_ids, root_objects)
        
        return all_objects

    def _process_objects_by_type(self, objects):
        """
        根据对象类型执行不同的处理函数
        
        Args:
            objects: 对象信息列表
        """
        # 类型到处理函数的映射
        type_handlers = {
            'AudioFileSource': self.processor.process_audiofilesource,
            'Sound': self.processor.process_sound,
            'WorkUnit': self.processor.process_workunit,
            'ActorMixer': self.processor.process_actormixer,
            'RandomContainer': self.processor.process_randomsequencecontainer,
            'SequenceContainer': self.processor.process_randomsequencecontainer,
            'BlendContainer': self.processor.process_blendcontainer,
            'SwitchContainer': self.processor.process_randomsequencecontainer,
        }

        print("\n🔄 开始按类型处理对象...")
        print("=" * 60)

        processed_count = 0
        for obj in objects:
            obj_type = obj.get('type', 'Unknown')
            handler = type_handlers.get(obj_type, self.processor.process_default)
            handler(obj, self.client)  # 传递client参数
            processed_count += 1

        print(f"✅ 已完成 {processed_count} 个对象的处理")

    def _show_statistics(self, objects, elapsed_time, root_count):
        """
        显示统计信息
        
        Args:
            objects: 对象信息列表
            elapsed_time: 耗时
            root_count: 根对象数量
        """
        type_count = {}
        for obj in objects:
            obj_type = obj.get('type', 'Unknown')
            type_count[obj_type] = type_count.get(obj_type, 0) + 1

        print("\n" + "=" * 60)
        print("📊 对象类型统计:")
        print("-" * 30)

        type_icons = {
            'AudioFileSource': '🎵',
            'Sound': '🔊',
            'WorkUnit': '📁',
            'ActorMixer': '🎭',
            'RandomContainer': '🎲',
            'SequenceContainer': '📊',
            'BlendContainer': '🎛️',
            'SwitchContainer': '🔀',
        }

        total_count = 0
        for obj_type, count in sorted(type_count.items()):
            icon = type_icons.get(obj_type, '📄')
            print(f"  {icon} {obj_type}: {count} 个")
            total_count += count

        print("-" * 30)
        print(f"🎯 根对象数: {root_count} 个")
        print(f"📦 处理对象总数: {total_count} 个")
        print(f"⏱️  总耗时: {elapsed_time:.2f} 秒")

    def _show_hierarchies(self, object_ids, root_objects):
        """
        显示层次结构
        
        Args:
            object_ids: 对象ID列表
            root_objects: 根对象信息列表
        """
        print("\n" + "=" * 60)
        print("🌳 完整的层次结构:")

        def print_subtree(sub_root_id, indent=0, is_root=True):
            try:
                result = self.client.call("ak.wwise.core.object.get", {
                    "from": {"id": [sub_root_id]},
                    "transform": [{"select": ["children"]}],
                    "options": {"return": ["id", "name", "type"]}
                })

                # if "return" in result and result["return"]:
                #     for obj in result["return"]:
                #         prefix = "  " * indent + "└── " if indent > 0 else ""
                #         obj_type = obj.get('type', 'Unknown')
                #         obj_name = obj.get('name', 'Unnamed')
                        
                #         # 根对象特殊标记
                #         if is_root and indent == 0:
                #             print(f"🎯 {obj_name} [{obj_type}]")
                #         else:
                #             print(f"{prefix}{obj_name} [{obj_type}]")
                        
                #         print_subtree(obj["id"], indent + 1, False)
            except Exception as e:
                print(f"获取层次结构时出错 {sub_root_id}: {e}")

        # 为每个根对象显示层次结构
        # for i, obj_id in enumerate(object_ids, 1):
        #     root_obj = next((obj for obj in root_objects if obj.get('id') == obj_id), None)
        #     if root_obj:
        #         obj_name = root_obj.get('name', 'Unnamed')
        #         obj_type = root_obj.get('type', 'Unknown')
        #         print(f"\n📁 层次结构 {i}: {obj_name} [{obj_type}]")
        #         print("-" * 40)
        #         print_subtree(obj_id, 0, True)


# =============================================================================
# 入口函数 - 主要调用接口
# =============================================================================

def analyze_custom_objects(object_ids, max_workers=6, object_type_filter=None):
    """
    🎯 主要入口函数 - 在其他地方调用此函数进行分析
    
    执行流程：
    1. 创建 WAAPI 客户端连接
    2. 初始化分析器
    3. 执行多线程对象遍历
    4. 返回分析结果
    
    Args:
        object_ids (list): Wwise对象ID列表，例如 ["{id1}", "{id2}"]
        max_workers (int, optional): 最大线程数，默认6个. 
        object_type_filter (str, optional): 对象类型过滤器，例如 "AudioFileSource"
        
    Returns:
        list: 包含所有分析到的对象数据的列表，每个对象包含id、name、type、path等信息
              如果分析失败返回None
        
    Example:
         from wwise_analyzer import analyze_custom_objects
         
         # 定义要分析的ID数组
         my_object_ids = [
             "{Your-Object-ID-1}",
             "{Your-Object-ID-2}"
         ]
         
         # 调用分析函数
         result = analyze_custom_objects(
             object_ids=my_object_ids,
             max_workers=8,
             object_type_filter="AudioFileSource"
         )
         
         # 处理结果
         if result:
             print(f"分析完成，共找到 {len(result)} 个对象")
             for obj in result:
                 print(f"对象: {obj['name']} [{obj['type']}]")
    """
    try:
        with WaapiClient() as client:
            analyzer = WwiseObjectAnalyzer(client, max_workers)
            return analyzer.analyze_by_ids(object_ids, object_type_filter)
    except Exception as e:
        print(f"❌ 分析自定义对象时出错: {e}")
        return None


def analyze_selected_objects():
    """
    辅助入口函数 - 分析当前在Wwise中选中的对象
    
    适用于交互式使用场景
    
    Returns:
        list: 分析结果对象列表，失败返回None
    """
    try:
        with WaapiClient() as client:
            # 获取选中的对象
            selected = client.call("ak.wwise.ui.getSelectedObjects", {})
            
            if not selected["objects"]:
                print("❌ 没有选中任何对象")
                return None
            
            selected_ids = [obj["id"] for obj in selected["objects"]]
            
            print(f"🎯 检测到 {len(selected_ids)} 个选中对象")
            analyzer = WwiseObjectAnalyzer(client)
            return analyzer.analyze_by_ids(selected_ids)
            
    except Exception as e:
        print(f"❌ 分析选中对象时出错: {e}")
        return None


# =============================================================================
# 使用示例和测试代码
# =============================================================================

if __name__ == "__main__":
    """
    直接运行此文件时的示例代码
    """
    
    print("🚀 Wwise 对象分析器函数库")
    print("=" * 60)
    print("使用方法:")
    print("1. 在其他文件中导入: from wwise_analyzer import analyze_custom_objects")
    print("2. 调用 analyze_custom_objects() 函数并传入对象ID列表")
    print("=" * 60)
    
    # 示例：分析当前选中的对象
    result = analyze_selected_objects()
    
    if result:
        print(f"\n✅ 分析完成，共处理 {len(result)} 个对象")
    else:
        print("\n💡 提示: 请在Wwise中选中对象后运行，或使用 analyze_custom_objects() 函数")
