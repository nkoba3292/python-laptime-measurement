# quick_test.py
# ラップタイムシステムの簡単なテスト

from main_laptime_system_debug import LapTimeSystemDebug
import time

def quick_test():
    """ラップタイムシステムの簡単なテスト"""
    print("🧪 Quick Laptime System Test")
    print("=" * 40)
    
    # システム初期化
    system = LapTimeSystemDebug()
    
    print("✅ System initialized")
    
    # レース開始
    print("🚀 Starting race...")
    system.handle_start_line_crossing()
    time.sleep(2)
    
    # ラップ1完了
    print("🏁 Completing lap 1...")
    system.handle_start_line_crossing()
    time.sleep(2)
    
    # ラップ2完了
    print("🏁 Completing lap 2...")
    system.handle_start_line_crossing()
    time.sleep(2)
    
    # ラップ3完了（レース終了）
    print("🏁 Completing lap 3 (finish)...")
    system.handle_start_line_crossing()
    
    print("✅ Test completed successfully!")
    
    # データ確認
    print(f"\n📊 Final Results:")
    print(f"   Lap Times: {system.lap_times}")
    print(f"   Race Finished: {system.race_finished}")
    print(f"   Total Laps: {len(system.lap_times)}")
    
    # クリーンアップ
    system.cleanup()

if __name__ == "__main__":
    quick_test()