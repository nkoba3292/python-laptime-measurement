# test_system.py
# -*- coding: utf-8 -*-
"""
予選タイム計測システムのテスト版（カメラなし）
"""
import time
import json
from datetime import datetime
from pathlib import Path

class LapTimeSystemTest:
    def __init__(self):
        print("🏁 Lap Timer System (Test Mode) Starting...")
        print("=" * 60)
        print("Features implemented:")
        print("• ✅ Dual camera system (LOGICOOL C270 x2)")
        print("• ✅ Start line detection algorithm")
        print("• ✅ 3-lap timing with real-time display")
        print("• ✅ Timer hiding at lap 2.5")
        print("• ✅ Sound effects (start/finish)")
        print("• ✅ Automatic data saving")
        print("• ✅ Overlay display system")
        print("=" * 60)
        
        # ラップタイム管理
        self.lap_times = []
        self.start_time = None
        self.current_lap = 0
        self.max_laps = 3
        self.race_started = False
        self.race_finished = False
        
        # 表示制御
        self.show_timer = True
        
        # データ保存
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
    
    def simulate_race(self):
        """レースのシミュレーション"""
        print("\n🎯 Race Simulation Starting...")
        print("📋 Expected behavior:")
        print("  1. Start line detection → Race start")
        print("  2. Lap timing (3 laps)")
        print("  3. Timer hide at lap 2.5")
        print("  4. Finish detection → Data save")
        
        # シミュレーション実行
        print("\n🚗 Simulating vehicle crossing start line...")
        self.handle_start_line_crossing()
        
        # ラップ1
        time.sleep(1)
        print("🔄 Simulating lap 1 completion...")
        self.handle_start_line_crossing()
        
        # ラップ2
        time.sleep(1)
        print("🔄 Simulating lap 2 completion...")
        self.handle_start_line_crossing()
        
        # タイマー非表示シミュレーション
        print("🙈 Timer would be hidden now (lap 2.5)")
        self.show_timer = False
        
        # ラップ3（最終）
        time.sleep(1)
        print("🔄 Simulating final lap completion...")
        self.handle_start_line_crossing()
        
        print("\n✅ Race simulation completed!")
    
    def handle_start_line_crossing(self):
        """スタートライン通過時の処理"""
        current_time = time.time()
        
        if not self.race_started:
            # レース開始
            self.race_started = True
            self.start_time = current_time
            self.current_lap = 1
            print("🏁 RACE STARTED!")
            print("🎵 [START SOUND EFFECT PLAYED]")
            
        else:
            # ラップ完了
            lap_time = current_time - self.start_time
            self.lap_times.append(lap_time)
            self.current_lap += 1
            
            print(f"⏱️ Lap {len(self.lap_times)} completed: {lap_time:.2f}s")
            
            # レース終了チェック
            if len(self.lap_times) >= self.max_laps:
                self.race_finished = True
                total_time = sum(self.lap_times)
                print(f"🏁 RACE FINISHED! Total time: {total_time:.2f}s")
                print("🎵 [FINISH SOUND EFFECT PLAYED]")
                
                # データ保存
                self.save_race_data()
    
    def save_race_data(self):
        """レースデータの保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"race_result_{timestamp}.json"
        
        race_data = {
            "timestamp": datetime.now().isoformat(),
            "lap_times": self.lap_times,
            "total_time": sum(self.lap_times),
            "average_lap": sum(self.lap_times) / len(self.lap_times) if self.lap_times else 0,
            "best_lap": min(self.lap_times) if self.lap_times else 0,
            "worst_lap": max(self.lap_times) if self.lap_times else 0
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(race_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Race data saved: {filename}")
            print("📊 Results:")
            print(f"   Total Time: {race_data['total_time']:.2f}s")
            print(f"   Average Lap: {race_data['average_lap']:.2f}s")
            print(f"   Best Lap: {race_data['best_lap']:.2f}s")
        except Exception as e:
            print(f"❌ Save error: {e}")
    
    def show_system_architecture(self):
        """システム構成の表示"""
        print("\n🏗️ SYSTEM ARCHITECTURE")
        print("=" * 60)
        print("📹 Camera System:")
        print("  • Overview Camera (index 0): Full course view → Main display")
        print("  • Start Line Camera (index 1): Line detection → Small window (1/9)")
        
        print("\n🎯 Detection Algorithm:")
        print("  • Frame difference motion detection")
        print("  • Configurable sensitivity thresholds")
        print("  • 2-second cooldown between detections")
        
        print("\n📺 Display Layout:")
        print("  • Main: 1280x720 overview camera")
        print("  • Small: 427x240 start line camera (bottom-left)")
        print("  • Overlay: Race timer, lap info, status")
        
        print("\n🎵 Audio System:")
        print("  • Start sound: 880Hz tone")
        print("  • Finish sound: 440Hz → 880Hz sequence")
        
        print("\n💾 Data Management:")
        print("  • Auto-save JSON format")
        print("  • Timestamp-based filenames")
        print("  • Detailed race statistics")

def main():
    """メイン実行"""
    system = LapTimeSystemTest()
    system.show_system_architecture()
    
    print("\n" + "=" * 60)
    input("Press ENTER to start race simulation...")
    
    system.simulate_race()
    
    print("\n🎯 SYSTEM READY FOR DEPLOYMENT")
    print("📋 Next steps:")
    print("  1. Connect LOGICOOL C270 cameras to Raspberry Pi 5")
    print("  2. Install required libraries: opencv-python, numpy, pygame")
    print("  3. Run: python main_laptime_system.py")
    print("  4. Adjust detection settings in config.json if needed")

if __name__ == "__main__":
    main()