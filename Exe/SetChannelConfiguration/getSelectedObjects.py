#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
from Json.json_handler import save_wwise_objects_to_json, JSONHandler
from functionLibrary import WwiseObjectAnalyzer

def main():
    """获取Wwise选中的对象并保存到JSON，然后使用多线程分析功能"""
    try:
        with WaapiClient() as client:
            result = client.call(
                "ak.wwise.ui.getSelectedObjects",
                options ={"return": ['id',"type", "name"]}
            )
            pprint(result["objects"])

            if result["objects"]:
                id = result["objects"][0]['id']
                pprint('=========================================')
                pprint('=========================================')
                pprint(id)
                
                # 使用封装的函数保存Wwise对象
                if save_wwise_objects_to_json(result["objects"], "wwise_selected_objects.json"):
                    print("Wwise对象保存成功！")
                    
                    # 创建JSONHandler实例来获取对象ID
                    handler = JSONHandler("wwise_selected_objects.json")
                    
                    # 获取所有对象ID
                    selected_ids = handler.get_object_ids()
                    print(f"\n所有对象ID: {selected_ids}")
                    
                    # 创建Wwise对象分析器并执行多线程分析
                    print("\n=== 开始多线程分析Wwise对象 ===")
                    analyzer = WwiseObjectAnalyzer(client)
                    analysis_results = analyzer.analyze_by_ids(selected_ids)
                    
                    # 保存分析结果到JSON
                    if analysis_results:
                        analysis_handler = JSONHandler("wwise_analysis_results.json")
                        if analysis_handler.write_to_json({"analysis_results": analysis_results}):
                            print("\n分析结果已保存到 wwise_analysis_results.json")
                        
                        print(f"\n=== 分析完成 ===")
                        print(f"共分析 {len(analysis_results)} 个对象")
                        print("详细分析信息已在上方显示")
                    else:
                        print("\n分析失败，未获得有效结果")
                        
                else:
                    print("Wwise对象保存失败！")
            else:
                print("没有选中任何对象！")

    except CannotConnectToWaapiException:
        print(
            "Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?"
        )

if __name__ == "__main__":
    main()
