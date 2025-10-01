# main_laptime_system_debug.py
# -*- coding: utf-8 -*-
"""
自動運転ミニカー予選タイム計測システム（デバッグ版）
- カメラなしでも動作するシミュレーションモード
- コンソールベースでのラップタイム測定
"""
import time
import pygame
import json
from datetime import datetime
from pathlib import Path

class LapTimeSystemDebug:
    def __init__(self):
        # ラップタイム管理
        self.lap_times = []
        self.start_time = None
        self.current_lap = 0
        self.max_laps = 3
        self.race_started = False
        self.race_finished = False
        
        # 表示制御
        self.show_timer = True  # 3周目半周で非表示
        self.timer_hidden_at = None
        
        # 音響システム
        pygame.mixer.init()
        self.sound_start = None
        self.sound_finish = None
        
        # データ保存
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 初期化
        self.load_sounds()
    
    def load_sounds(self):
        """効果音ファイルの読み込み"""
        try:
            # サンプル音を作成（実際の音ファイルがない場合）
            self.create_sample_sounds()
            self.sound_start = pygame.mixer.Sound("sounds/start.wav")
            self.sound_finish = pygame.mixer.Sound("sounds/finish.wav")
            print("✅ Sound files loaded successfully")
        except Exception as e:
            print(f"⚠️ Sound loading error: {e}")
            print("📝 Running without sound effects")
    
    def create_sample_sounds(self):
        """サンプル効果音の生成（実際の音ファイルがない場合）"""
        import numpy as np
        import wave
        
        sounds_dir = Path("sounds")
        sounds_dir.mkdir(exist_ok=True)
        
        # 簡単なビープ音を生成
        sample_rate = 44100
        duration = 0.5
        
        # スタート音（高音）
        start_freq = 880  # A5
        start_samples = np.sin(2 * np.pi * start_freq * np.linspace(0, duration, int(sample_rate * duration)))
        start_audio = (start_samples * 32767).astype(np.int16)
        
        # フィニッシュ音（低音→高音）
        finish_samples = np.concatenate([
            np.sin(2 * np.pi * 440 * np.linspace(0, duration/2, int(sample_rate * duration/2))),
            np.sin(2 * np.pi * 880 * np.linspace(0, duration/2, int(sample_rate * duration/2)))
        ])
        finish_audio = (finish_samples * 32767).astype(np.int16)
        
        # WAVファイルとして保存（簡易版）
        
        # スタート音
        with wave.open("sounds/start.wav", 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(start_audio.tobytes())
        
        # フィニッシュ音
        with wave.open("sounds/finish.wav", 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(finish_audio.tobytes())

    def handle_start_line_crossing(self):
        """スタートライン通過時の処理"""
        current_time = time.time()
        
        if not self.race_started:
            # レース開始
            self.race_started = True
            self.start_time = current_time
            self.current_lap = 1
            
            print("🚀 RACE STARTED!")
            print(f"🏁 LAP {self.current_lap}/{self.max_laps}")
            
            # スタート音再生
            if self.sound_start:
                self.sound_start.play()
                
        elif self.race_started and not self.race_finished:
            # ラップタイム記録
            lap_time = current_time - self.start_time
            self.lap_times.append(lap_time)
            
            print(f"⏱️ LAP {self.current_lap} COMPLETED: {lap_time:.2f}s")
            
            # 次のラップへ
            self.current_lap += 1
            self.start_time = current_time
            
            if self.current_lap <= self.max_laps:
                print(f"🏁 LAP {self.current_lap}/{self.max_laps}")
                
                # 3周目の半分でタイマー非表示
                if self.current_lap == 3:
                    # 簡易的に3周目開始時に非表示
                    self.hide_timer()
            else:
                # レース終了
                self.race_finished = True
                total_time = sum(self.lap_times)
                avg_time = total_time / len(self.lap_times)
                best_lap = min(self.lap_times)
                
                print("🏆 RACE FINISHED!")
                print("=" * 40)
                print(f"📊 RACE RESULTS:")
                for i, lap_time in enumerate(self.lap_times, 1):
                    print(f"   Lap {i}: {lap_time:.2f}s")
                print(f"📈 Total Time: {total_time:.2f}s")
                print(f"📊 Average Lap: {avg_time:.2f}s")
                print(f"🏃 Best Lap: {best_lap:.2f}s")
                print("=" * 40)
                
                # フィニッシュ音再生
                if self.sound_finish:
                    self.sound_finish.play()
                
                # データ保存
                self.save_race_data()
    
    def hide_timer(self):
        """タイマー表示を非表示にする"""
        self.show_timer = False
        self.timer_hidden_at = time.time()
        print("🙈 Timer display hidden (3rd lap)")
    
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
        except Exception as e:
            print(f"❌ Save error: {e}")
    
    def run(self):
        """メインループ（デバッグモード）"""
        print("🏁 Lap Timer System Starting (DEBUG MODE)")
        print("=" * 50)
        print("🔧 DEBUG MODE: No cameras required")
        print("🎯 Keyboard simulation mode:")
        print("   's' = Start/Next lap")
        print("   'r' = Reset race")
        print("   'q' = Quit")
        print("=" * 50)
        
        try:
            while True:
                # 現在の状態表示
                print(f"\n📊 Current Status:")
                print(f"   Race Started: {self.race_started}")
                print(f"   Current Lap: {self.current_lap}/{self.max_laps}")
                
                if self.lap_times:
                    print(f"   Completed Laps: {[f'{t:.2f}s' for t in self.lap_times]}")
                
                if self.race_started and not self.race_finished:
                    elapsed = time.time() - self.start_time
                    if self.show_timer:
                        print(f"   Current Time: {elapsed:.1f}s")
                    else:
                        print(f"   Current Time: [HIDDEN] (3rd lap mode)")
                
                if self.race_finished:
                    print("🏆 Race completed! Enter 'r' to reset or 'q' to quit.")
                
                print("\nEnter command (s/r/q): ", end="")
                try:
                    key = input().lower().strip()
                except KeyboardInterrupt:
                    break
                
                if key == 'q':
                    break
                elif key == 'r':
                    self.reset_race()
                elif key == 's':
                    print("🚗 Simulating start line crossing...")
                    self.handle_start_line_crossing()
                else:
                    print("⚠️ Invalid command. Use 's', 'r', or 'q'")
        
        except KeyboardInterrupt:
            print("\n🛑 System interrupted by user")
        
        finally:
            self.cleanup()
    
    def reset_race(self):
        """レースのリセット"""
        self.lap_times.clear()
        self.start_time = None
        self.current_lap = 0
        self.race_started = False
        self.race_finished = False
        self.show_timer = True
        self.timer_hidden_at = None
        print("🔄 Race reset - Ready for new race")
    
    def cleanup(self):
        """リソースの解放"""
        pygame.mixer.quit()
        print("🧹 System cleanup completed")

def main():
    """メイン実行"""
    print("🏁 Autonomous Car Lap Timer System (DEBUG VERSION)")
    print("=" * 60)
    
    system = LapTimeSystemDebug()
    system.run()

if __name__ == "__main__":
    main()