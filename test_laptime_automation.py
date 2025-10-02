# test_laptime_automation.py
# ラップタイムシステムの自動テストスクリプト

import subprocess
import time
import sys

def test_laptime_system():
    """ラップタイムシステムの自動テスト"""
    print("🧪 Automated Laptime System Test")
    print("=" * 40)
    
    # テストシナリオ
    commands = [
        ("s", "Start race"),
        ("s", "Complete lap 1"),
        ("s", "Complete lap 2"), 
        ("s", "Complete lap 3 (finish race)"),
        ("r", "Reset race"),
        ("s", "Start new race"),
        ("q", "Quit system")
    ]
    
    try:
        # プロセス開始
        process = subprocess.Popen(
            [sys.executable, "main_laptime_system_debug.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="C:/Users/DELL/20250928_Python_LAPTIME_WEBCAM"
        )
        
        # コマンド実行
        for cmd, description in commands:
            print(f"📝 {description} (command: '{cmd}')")
            process.stdin.write(cmd + "\n")
            process.stdin.flush()
            time.sleep(1)  # 1秒待機
        
        # プロセス終了待機
        stdout, stderr = process.communicate(timeout=10)
        
        print("✅ Test completed")
        print("\n📊 Output:")
        print(stdout)
        
        if stderr:
            print("\n⚠️ Errors:")
            print(stderr)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    test_laptime_system()