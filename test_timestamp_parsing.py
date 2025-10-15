#!/usr/bin/env python3
"""
測試 PTT 時間戳解析功能
"""

import re
from datetime import datetime

def test_ptt_timestamp_parsing():
    """測試 PTT 時間戳解析"""
    
    # 測試用例
    test_cases = [
        "Wed Oct 15 13:16:00 2025",
        "Mon Jan 1 00:00:00 2024", 
        "Fri Dec 31 23:59:59 2023",
        "2025年10月15日",
        "10/15/2025",
        "2025-10-15"
    ]
    
    for test_text in test_cases:
        print(f"\n測試文本: {test_text}")
        
        # 嘗試解析 PTT 完整時間戳格式
        ptt_timestamp_match = re.search(r'(\w{3})\s+(\w{3})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})\s+(\d{4})', test_text)
        if ptt_timestamp_match:
            try:
                day_name, month_name, day, hour, minute, second, year = ptt_timestamp_match.groups()
                month_map = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                month = month_map.get(month_name, 1)
                parsed_time = datetime(int(year), month, int(day), int(hour), int(minute), int(second))
                print(f"✅ PTT 時間戳解析成功: {parsed_time}")
                print(f"   格式化輸出: {parsed_time.strftime('%Y-%m-%d-%a-%H:%M:%S')}")
                continue
            except (ValueError, KeyError) as e:
                print(f"❌ PTT 時間戳解析失敗: {e}")
        
        # 嘗試解析中文日期格式
        if '年' in test_text and '月' in test_text and '日' in test_text:
            time_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', test_text)
            if time_match:
                year, month, day = time_match.groups()
                parsed_time = datetime(int(year), int(month), int(day))
                print(f"✅ 中文日期解析成功: {parsed_time}")
                continue
        
        # 嘗試解析英文日期格式
        elif '/' in test_text and len(test_text.split('/')) == 3:
            try:
                parts = test_text.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    if len(year) == 2:
                        year = '20' + year
                    parsed_time = datetime(int(year), int(month), int(day))
                    print(f"✅ 英文日期解析成功: {parsed_time}")
                    continue
            except ValueError:
                pass
        
        # 嘗試解析 ISO 格式
        elif re.match(r'\d{4}-\d{1,2}-\d{1,2}', test_text):
            try:
                parsed_time = datetime.fromisoformat(test_text)
                print(f"✅ ISO 日期解析成功: {parsed_time}")
                continue
            except ValueError:
                pass
        
        print(f"❌ 無法解析: {test_text}")

if __name__ == "__main__":
    test_ptt_timestamp_parsing()
