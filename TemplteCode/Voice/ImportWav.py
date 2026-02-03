import shutil
from pathlib import Path
from pprint import pprint
from collections import deque

# =========================
# WAAPI 初始化
# =========================
try:
    from waapi import WaapiClient, CannotConnectToWaapiException
except Exception:  # pragma: no cover
    WaapiClient = None  # type: ignore[assignment]

    class CannotConnectToWaapiException(Exception):
        pass

TARGET_TYPE = "Sound"
WAAPI_URL = "ws://127.0.0.1:8080/waapi"

# 支持的语言
SUPPORTED_LANGS = ['en_US', 'ja_JP', 'ko_KR', 'zh_CN']

# =========================
# 广度优先搜索目录下所有语言文件夹
# =========================
def bfs_find_language_dirs(base_path: Path) -> dict[str, Path]:
    found = {}
    queue = deque([base_path])
    while queue:
        current = queue.popleft()
        for child in current.iterdir():
            if child.is_dir():
                if child.name in SUPPORTED_LANGS:
                    found[child.name] = child
                else:
                    queue.append(child)
    return found

# =========================
# 构建目标路径
# =========================
def build_target_path(source_path: Path, target_lang_root: Path, language: str) -> Path:
    source_parts = list(source_path.parts)
    try:
        lang_index = source_parts.index(language)
        relative_parts = source_parts[lang_index + 1:]
    except ValueError:
        relative_parts = [source_path.name]

    target_path = target_lang_root
    for part in relative_parts:
        target_path /= part
    return target_path

# =========================
# 导入文件/目录
# =========================
def import_path(source_path: Path, target_path: Path) -> bool:
    try:
        if source_path.is_file():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            print(f"✅ 已复制文件到: {target_path}")
        else:
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(source_path, target_path)
            file_count = sum(1 for p in target_path.rglob('*') if p.is_file())
            print(f"✅ 已复制目录到: {target_path} 共 {file_count} 个文件")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

# =========================
# 主流程
# =========================
if __name__ == "__main__":
    print("="*60)
    print("音频文件导入工具 - 自动多语言批量导入")
    print("="*60)

    # 0️⃣ 获取 Wwise 平台和语言
    try:
        if WaapiClient is None:
            print("❌ 未安装 waapi 包，无法连接到 Wwise。")
            wwise_languages = SUPPORTED_LANGS
        else:
            with WaapiClient(url=WAAPI_URL) as client:
                languages_result = client.call("ak.wwise.core.object.get", {
                    "waql": "from type language"
                }, options={"return": ["id", "name"]})
                wwise_languages = [l['name'] for l in languages_result['return']
                                   if l['name'] not in ['Mixed', 'External', 'SFX']]
    except CannotConnectToWaapiException:
        print("❌ 无法连接到 Wwise，使用默认语言列表")
        wwise_languages = SUPPORTED_LANGS
    except Exception as e:
        print(f"❌ 获取 Wwise 语言异常: {e}")
        wwise_languages = SUPPORTED_LANGS

    print("✅ Wwise 语言:")
    pprint(wwise_languages)

    # 1️⃣ 本地语言文件夹管理
    base_local_path = Path.cwd().parent.parent.parent / "Originals" / "Voices"
    base_local_path.mkdir(parents=True, exist_ok=True)
    local_folders = {f.name: f for f in base_local_path.iterdir() if f.is_dir()}

    print(f"✅ 本地已有语言文件夹 ({len(local_folders)} 个):")
    for lang, path in local_folders.items():
        print(f"  - {lang}: {path}")

    # 2️⃣ 对比 Wwise 语言，缺少的就创建
    for lang in wwise_languages:
        if lang not in local_folders:
            folder_path = base_local_path / lang
            folder_path.mkdir(exist_ok=True)
            local_folders[lang] = folder_path
            print(f"🟢 创建缺失本地语言文件夹: {folder_path}")

    # 3️⃣ 获取源路径
    source_path_input = input(
        "请输入源路径（如：D:/Temp/zh_CN/Voice_Part1-1/Dialog-1）:\n> "
    ).strip()
    if not source_path_input:
        print("❌ 未输入路径")
        input("\n按 Enter 键退出...")
        exit()
    source_path = Path(source_path_input)
    if not source_path.exists():
        print(f"❌ 源路径不存在: {source_path}")
        input("\n按 Enter 键退出...")
        exit()

    # 4️⃣ 广度优先搜索源路径下所有语言文件夹
    found_dirs = bfs_find_language_dirs(source_path)
    if not found_dirs:
        print("❌ 源路径下未找到任何语言文件夹")
        input("\n按 Enter 键退出...")
        exit()

    print(f"✅ 在源路径下发现语言文件夹: {list(found_dirs.keys())}")

    # 5️⃣ 遍历每个语言文件夹导入
    for lang, lang_source_path in found_dirs.items():
        if lang not in local_folders:
            print(f"⚠ 本地未找到语言文件夹 {lang}, 自动创建")
            target_lang_root = base_local_path / lang
            target_lang_root.mkdir(exist_ok=True)
            local_folders[lang] = target_lang_root

        target_path = build_target_path(lang_source_path, local_folders[lang], lang)
        print("\n导入设置:")
        print(f"  源路径: {lang_source_path}")
        print(f"  目标语言: {lang}")
        print(f"  目标路径: {target_path}")

        import_path(lang_source_path, target_path)

    print("\n✅ 所有语言导入完成")
    input("\n按 Enter 键退出...")
