from waapi import WaapiClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time


class ObjectTypeProcessor:
    """针对不同类型的对象执行不同的处理函数"""

    @staticmethod
    def process_audiofilesource(obj):
        """处理 AudioFileSource 对象"""
        print(f"🎵 音频文件源: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 路径: {obj.get('path', 'N/A')}")
        if 'ChannelConfigOverride' in obj:
            print(f"   - 声道配置: {obj['ChannelConfigOverride']}")
        print()

    @staticmethod
    def process_sound(obj):
        """处理 Sound 对象"""
        print(f"🔊 Sound对象: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 类型: {obj.get('type', 'N/A')}")
        print()

    @staticmethod
    def process_workunit(obj):
        """处理 WorkUnit 对象"""
        print(f"📁 工作单元: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 路径: {obj.get('path', 'N/A')}")
        print()

    @staticmethod
    def process_actormixer(obj):
        """处理 ActorMixer 对象"""
        print(f"🎭 角色混音器: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 类ID: {obj.get('classId', 'N/A')}")
        print()

    @staticmethod
    def process_randomsequencecontainer(obj):
        """处理 Random/Sequence Container 对象"""
        container_type = obj.get('type', 'Container')
        icon = "🎲" if "Random" in container_type else "📊"
        print(f"{icon} 容器对象: {obj.get('name', 'Unnamed')} [{container_type}]")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 路径: {obj.get('path', 'N/A')}")
        print()

    @staticmethod
    def process_blendcontainer(obj):
        """处理 Blend Container 对象"""
        print(f"🎛️ 混合容器: {obj.get('name', 'Unnamed')}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 类ID: {obj.get('classId', 'N/A')}")
        print()

    @staticmethod
    def process_default(obj):
        """默认处理函数"""
        obj_type = obj.get('type', 'Unknown')
        obj_name = obj.get('name', 'Unnamed')
        print(f"📄 {obj_type}: {obj_name}")
        print(f"   - ID: {obj.get('id', 'N/A')}")
        print(f"   - 路径: {obj.get('path', 'N/A')}")
        print()


class ParallelWwiseTraverser:
    """并行遍历 Wwise 对象的类"""

    def __init__(self, client, max_workers=8):
        self.client = client
        self.max_workers = max_workers
        self.lock = threading.Lock()

    def get_children_ids(self, object_id):
        """广度优先：获取直接子对象的ID"""
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
        """获取单个对象的详细信息"""
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
        """并行深度优先遍历主函数 - 支持多个根对象"""
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
        """遍历单个子树（递归深度优先）"""
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
        """获取多个对象的详细信息"""
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
    """Wwise 对象分析器"""

    def __init__(self, client, max_workers=8):
        self.client = client
        self.traverser = ParallelWwiseTraverser(client, max_workers)
        self.processor = ObjectTypeProcessor()

    def analyze_by_ids(self, object_ids, object_type_filter=None):
        """
        入口函数：根据ID数组分析对象

        Args:
            object_ids: Wwise对象ID列表
            object_type_filter: 可选的对象类型过滤器
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

    def analyze_selected_object(self):
        """分析当前选中的对象（保持原有功能）"""
        # 获取选中的对象
        selected = self.client.call("ak.wwise.ui.getSelectedObjects", {})

        if not selected["objects"]:
            print("❌ 没有选中任何对象")
            return

        sound_obj = selected["objects"][0]
        sound_id = sound_obj["id"]

        # 使用新的入口函数
        return self.analyze_by_ids([sound_id])

    def _process_objects_by_type(self, objects):
        """根据对象类型执行不同的处理函数"""
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
            handler(obj)
            processed_count += 1

        print(f"✅ 已完成 {processed_count} 个对象的处理")

    def _show_statistics(self, objects, elapsed_time, root_count):
        """显示统计信息"""
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
        """显示层次结构"""
        print("\n" + "=" * 60)
        print("🌳 完整的层次结构:")

        def print_subtree(sub_root_id, indent=0, is_root=True):
            try:
                result = self.client.call("ak.wwise.core.object.get", {
                    "from": {"id": [sub_root_id]},
                    "transform": [{"select": ["children"]}],
                    "options": {"return": ["id", "name", "type"]}
                })

                if "return" in result and result["return"]:
                    for obj in result["return"]:
                        prefix = "  " * indent + "└── " if indent > 0 else ""
                        obj_type = obj.get('type', 'Unknown')
                        obj_name = obj.get('name', 'Unnamed')

                        # 根对象特殊标记
                        if is_root and indent == 0:
                            print(f"🎯 {obj_name} [{obj_type}]")
                        else:
                            print(f"{prefix}{obj_name} [{obj_type}]")

                        print_subtree(obj["id"], indent + 1, False)
            except Exception as e:
                print(f"获取层次结构时出错 {sub_root_id}: {e}")

        # 为每个根对象显示层次结构
        for i, obj_id in enumerate(object_ids, 1):
            root_obj = next((obj for obj in root_objects if obj.get('id') == obj_id), None)
            if root_obj:
                obj_name = root_obj.get('name', 'Unnamed')
                obj_type = root_obj.get('type', 'Unknown')
                print(f"\n📁 层次结构 {i}: {obj_name} [{obj_type}]")
                print("-" * 40)
                print_subtree(obj_id, 0, True)


def main():
    """主函数 - 使用示例"""
    try:
        with WaapiClient() as client:
            print("🚀 Wwise 对象分析器启动")
            print("=" * 60)

            # 创建分析器实例
            analyzer = WwiseObjectAnalyzer(client, max_workers=6)

            # 使用方式1：分析当前选中的对象
            print("使用方法1: 分析当前选中的对象")
            analyzer.analyze_selected_object()

            print("\n" + "=" * 80)
            print("使用方法2: 传入ID数组进行分析")
            print("=" * 80)

            # 使用方式2：传入ID数组进行分析
            # 这里可以替换为您自己的ID数组
            example_ids = [
                # "您的对象ID1",
                # "您的对象ID2",
                # "您的对象ID3"
            ]

            if example_ids:
                result = analyzer.analyze_by_ids(example_ids)
                # result 包含所有分析到的对象数据，可以进一步处理
            else:
                print("💡 提示: 请在 example_ids 中添加要分析的Wwise对象ID")

            print("\n" + "=" * 60)
            print("✅ 分析完成！")

    except Exception as e:
        print(f"❌ 程序执行出错: {e}")


# 在其他地方调用的示例函数
def analyze_custom_objects(object_ids, max_workers=6, object_type_filter=None):
    """
    在其他地方调用的入口函数

    Args:
        object_ids: Wwise对象ID列表
        max_workers: 最大线程数
        object_type_filter: 对象类型过滤器

    Returns:
        list: 所有分析到的对象数据
    """
    try:
        with WaapiClient() as client:
            analyzer = WwiseObjectAnalyzer(client, max_workers)
            return analyzer.analyze_by_ids(object_ids, object_type_filter)
    except Exception as e:
        print(f"❌ 分析自定义对象时出错: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    # 方式1: 直接运行主函数
    main()

    # 方式2: 在其他Python文件中这样调用:
    """
    from your_script_name import analyze_custom_objects

    # 定义要分析的ID数组
    my_object_ids = [
        "{Your-Object-ID-1}",
        "{Your-Object-ID-2}", 
        "{Your-Object-ID-3}"
    ]

    # 调用分析函数
    result = analyze_custom_objects(
        object_ids=my_object_ids,
        max_workers=8,
        object_type_filter="AudioFileSource"  # 可选：只分析特定类型
    )

    # 处理结果
    if result:
        print(f"分析完成，共找到 {len(result)} 个对象")
    """