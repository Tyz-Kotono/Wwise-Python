# !/usr/bin/env python
# -*- coding: utf-8 -*-
import pprint
import sys
import os
import pyperclip

# 设置虚拟环境
# def setup_environment():
#     # 方法1: 使用绝对路径
#     venv_path = r"D:\Code\env313"
#     site_packages = os.path.join(venv_path, "Lib", "site-packages")

#     if os.path.exists(site_packages):
#         sys.path.insert(0, site_packages)
#         return True
#     return False

def get_selected_guid():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return None


def get_selected_guids_list():
    return sys.argv[1:]


# # 初始化环境
# if setup_environment():
#     print("虚拟环境已加载")
# else:
#     print("使用系统 Python 环境")


guids = get_selected_guids_list()
pyperclip.copy(' '.join(guids))
pprint.pprint(guids)




