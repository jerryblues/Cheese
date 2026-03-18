
import sys
from pathlib import Path
import json
import os

# 将脚本所在目录添加到 sys.path 以便导入 get_daily
script_dir = Path("d:/Code/Cheese/Get_to_Feishu")
sys.path.append(str(script_dir))

import get_daily

def mock_today_title_prefix():
    # 强制返回指定的测试日期
    return "26.0317"

# 替换原始函数
get_daily.today_title_prefix = mock_today_title_prefix

if __name__ == "__main__":
    print("--- 启动同步跳过逻辑测试 (模拟日期: 26.0317) ---")
    
    # 1. 确保缓存文件中有该日期
    cache_file = script_dir / "notebook_list.json"
    if cache_file.exists():
        content = cache_file.read_text(encoding="utf-8")
        data = json.loads(content)
        synced_dates = data.get("syncedDates", [])
        if "26.0317" not in synced_dates:
            print("正在向缓存添加 26.0317 以触发跳过逻辑...")
            synced_dates.append("26.0317")
            data["syncedDates"] = synced_dates
            cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            print("缓存中已存在 26.0317")
    
    # 2. 运行主函数
    # 由于 main() 内部会重新加载缓存，我们通过直接调用 main 验证是否打印 skip 消息
    try:
        # 切换工作目录到脚本所在目录，以确保 Path(__file__) 逻辑正确
        os.chdir(str(script_dir))
        get_daily.main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"运行出错: {e}")

    print("--- 测试完成 ---")
