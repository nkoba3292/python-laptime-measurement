# virtual_test_system.py
# -*- coding: utf-8 -*-
"""
予選タイム計測システムの仮想テスト版
カメラなしで手動トリガーによる動作確認
"""
import time
import json
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from pathlib import Path
import pygame

class VirtualLapTimeSystem:
    def __init__(self):
        # ラップタイム管理
        self.lap_times = []
        self.start_time = None
        self.current_lap = 0
        self.max_laps = 3
        self.race_started = False
        self.race_finished = False
        
        # 表示制御
        self.show_timer = True
        self.timer_hidden_at = None
        
        # スタートライン検出
        self.last_detection_time = 0
        self.detection_cooldown = 2.0
        
        # データ保存
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # GUI要素
        self.root = None
        self.status_var = None
        self.timer_var = None
        self.lap_info_var = None
        
        # 音響システム
        pygame.mixer.init()
        self.load_sounds()
        
        # 自動更新スレッド
        self.update_thread = None
        self.running = True
    
    def load_sounds(self):
        """効果音の読み込み"""
        try:
            sounds_dir = Path("sounds")
            if not sounds_dir.exists():
                sounds_dir.mkdir(exist_ok=True)
                self.create_sample_sounds()
            
            self.sound_start = pygame.mixer.Sound("sounds/start.wav")
            self.sound_finish = pygame.mixer.Sound("sounds/finish.wav")
            print("✅ Sound system loaded")
        except Exception as e:
            print(f"⚠️ Sound loading error: {e}")
    
    def create_sample_sounds(self):
        """サンプル効果音の生成"""
        import numpy as np
        import wave
        
        sample_rate = 44100
        duration = 0.5
        
        # スタート音（高音）
        start_freq = 880
        start_samples = np.sin(2 * np.pi * start_freq * np.linspace(0, duration, int(sample_rate * duration)))
        start_audio = (start_samples * 32767).astype(np.int16)
        
        # フィニッシュ音（低音→高音）
        finish_samples = np.concatenate([
            np.sin(2 * np.pi * 440 * np.linspace(0, duration/2, int(sample_rate * duration/2))),
            np.sin(2 * np.pi * 880 * np.linspace(0, duration/2, int(sample_rate * duration/2)))
        ])
        finish_audio = (finish_samples * 32767).astype(np.int16)
        
        # WAVファイル保存
        with wave.open("sounds/start.wav", 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(start_audio.tobytes())
        
        with wave.open("sounds/finish.wav", 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(finish_audio.tobytes())
    
    def create_gui(self):
        """GUI作成"""
        self.root = tk.Tk()
        self.root.title("🏁 Virtual Lap Timer System")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = tk.Label(main_frame, text="🏁 自動運転ミニカー予選タイム計測システム", 
                              font=('Arial', 18, 'bold'), bg='#2b2b2b', fg='white')
        title_label.pack(pady=(0, 20))
        
        # ステータス表示
        self.status_var = tk.StringVar(value="待機中 - スタートボタンを押してください")
        status_label = tk.Label(main_frame, textvariable=self.status_var,
                               font=('Arial', 14), bg='#2b2b2b', fg='yellow')
        status_label.pack(pady=10)
        
        # タイマー表示
        self.timer_var = tk.StringVar(value="タイム: --:--")
        timer_label = tk.Label(main_frame, textvariable=self.timer_var,
                              font=('Arial', 24, 'bold'), bg='#2b2b2b', fg='red')
        timer_label.pack(pady=20)
        
        # ラップ情報表示
        self.lap_info_var = tk.StringVar(value="ラップ情報が表示されます")
        lap_info_label = tk.Label(main_frame, textvariable=self.lap_info_var,
                                 font=('Arial', 12), bg='#2b2b2b', fg='lightblue',
                                 justify=tk.LEFT)
        lap_info_label.pack(pady=10)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=30)
        
        # スタートライン通過ボタン
        self.start_button = tk.Button(button_frame, text="🚗 スタートライン通過",
                                     command=self.trigger_start_line,
                                     font=('Arial', 14, 'bold'),
                                     bg='green', fg='white',
                                     width=20, height=2)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # リセットボタン
        reset_button = tk.Button(button_frame, text="🔄 レースリセット",
                               command=self.reset_race,
                               font=('Arial', 14, 'bold'),
                               bg='orange', fg='white',
                               width=15, height=2)
        reset_button.pack(side=tk.LEFT, padx=10)
        
        # 終了ボタン
        quit_button = tk.Button(button_frame, text="❌ 終了",
                              command=self.quit_system,
                              font=('Arial', 14, 'bold'),
                              bg='red', fg='white',
                              width=10, height=2)
        quit_button.pack(side=tk.LEFT, padx=10)
        
        # コントロール説明
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=20)
        
        control_label = tk.Label(control_frame, 
                               text="💡 使用方法:\n"
                                   "• 'スタートライン通過'ボタンでレース開始\n"
                                   "• 各ラップ完了時に再度ボタンを押す\n"
                                   "• 3周完了で自動終了・データ保存\n"
                                   "• SPACEキーでもトリガー可能",
                               font=('Arial', 10), bg='#2b2b2b', fg='lightgray',
                               justify=tk.LEFT)
        control_label.pack()
        
        # カメラシミュレーション表示
        camera_frame = ttk.Frame(main_frame)
        camera_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # メインカメラエリア
        main_camera_label = tk.Label(camera_frame, text="📹 俯瞰カメラ (1280x720)\n[実際にはコース全体を表示]",
                                   font=('Arial', 12), bg='#404040', fg='white',
                                   width=60, height=8, relief=tk.SUNKEN)
        main_camera_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # サブカメラエリア
        sub_camera_label = tk.Label(camera_frame, text="📹 スタートライン\nカメラ (427x240)\n[車両検出用]",
                                  font=('Arial', 10), bg='#606060', fg='white',
                                  width=25, height=8, relief=tk.SUNKEN)
        sub_camera_label.pack(side=tk.LEFT)
        
        # キーボードイベント
        self.root.bind('<KeyPress-space>', lambda e: self.trigger_start_line())
        self.root.focus_set()
    
    def trigger_start_line(self):
        """スタートライン通過トリガー"""
        current_time = time.time()
        
        # クールダウンチェック
        if current_time - self.last_detection_time < self.detection_cooldown:
            remaining = self.detection_cooldown - (current_time - self.last_detection_time)
            self.status_var.set(f"クールダウン中: {remaining:.1f}秒待機")
            return
        
        self.last_detection_time = current_time
        self.handle_start_line_crossing()
    
    def handle_start_line_crossing(self):
        """スタートライン通過時の処理"""
        current_time = time.time()
        
        if not self.race_started:
            # レース開始
            self.race_started = True
            self.start_time = current_time
            self.current_lap = 1
            
            self.status_var.set("🏁 レース開始！")
            self.start_button.config(text="🚗 ラップ完了", bg='blue')
            
            # スタート音再生
            if hasattr(self, 'sound_start'):
                self.sound_start.play()
            
            print("🏁 RACE STARTED!")
            
        else:
            # ラップ完了
            lap_time = current_time - self.start_time
            self.lap_times.append(lap_time)
            self.current_lap += 1
            
            print(f"⏱️ Lap {len(self.lap_times)} completed: {lap_time:.2f}s")
            
            # 3周目の半周で表示を非表示
            if self.current_lap == 3 and len(self.lap_times) == 2:
                threading.Timer(lap_time / 2, self.hide_timer).start()
            
            # レース終了チェック
            if len(self.lap_times) >= self.max_laps:
                self.race_finished = True
                total_time = sum(self.lap_times)
                
                self.status_var.set(f"🏁 レース完了! 総時間: {total_time:.2f}秒")
                self.start_button.config(text="✅ 完了", bg='gray', state='disabled')
                
                # フィニッシュ音再生
                if hasattr(self, 'sound_finish'):
                    self.sound_finish.play()
                
                print(f"🏁 RACE FINISHED! Total time: {total_time:.2f}s")
                
                # データ保存
                self.save_race_data()
            else:
                self.status_var.set(f"ラップ {len(self.lap_times)} 完了 - 次のラップへ")
        
        self.update_display()
    
    def hide_timer(self):
        """タイマー表示を非表示にする"""
        self.show_timer = False
        self.timer_hidden_at = time.time()
        self.timer_var.set("🙈 タイマー非表示中")
        print("🙈 Timer display hidden (3rd lap, halfway)")
    
    def update_display(self):
        """表示の更新"""
        # ラップ情報更新
        lap_info = "ラップタイム履歴:\n"
        for i, lap_time in enumerate(self.lap_times):
            lap_info += f"Lap {i+1}: {lap_time:.2f}秒\n"
        
        if self.lap_times:
            avg_time = sum(self.lap_times) / len(self.lap_times)
            best_time = min(self.lap_times)
            lap_info += f"\n平均: {avg_time:.2f}秒\nベスト: {best_time:.2f}秒"
        
        self.lap_info_var.set(lap_info)
    
    def auto_update_timer(self):
        """タイマーの自動更新"""
        while self.running:
            if self.race_started and not self.race_finished:
                current_time = time.time() - self.start_time
                if self.show_timer:
                    minutes = int(current_time // 60)
                    seconds = current_time % 60
                    self.timer_var.set(f"タイム: {minutes:02d}:{seconds:05.2f}")
            
            time.sleep(0.1)
    
    def save_race_data(self):
        """レースデータの保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"virtual_race_result_{timestamp}.json"
        
        race_data = {
            "timestamp": datetime.now().isoformat(),
            "test_mode": "virtual",
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
            
            # 結果をGUIに表示
            result_window = tk.Toplevel(self.root)
            result_window.title("🏆 レース結果")
            result_window.geometry("400x300")
            result_window.configure(bg='#2b2b2b')
            
            result_text = f"""
🏆 レース結果

📊 統計情報:
総時間: {race_data['total_time']:.2f}秒
平均ラップ: {race_data['average_lap']:.2f}秒
ベストラップ: {race_data['best_lap']:.2f}秒
ワーストラップ: {race_data['worst_lap']:.2f}秒

📁 ファイル: {filename.name}
"""
            
            result_label = tk.Label(result_window, text=result_text,
                                  font=('Arial', 12), bg='#2b2b2b', fg='white',
                                  justify=tk.LEFT)
            result_label.pack(padx=20, pady=20)
            
        except Exception as e:
            print(f"❌ Save error: {e}")
    
    def reset_race(self):
        """レースのリセット"""
        self.lap_times.clear()
        self.start_time = None
        self.current_lap = 0
        self.race_started = False
        self.race_finished = False
        self.show_timer = True
        self.timer_hidden_at = None
        
        self.status_var.set("リセット完了 - スタートボタンを押してください")
        self.timer_var.set("タイム: --:--")
        self.lap_info_var.set("ラップ情報が表示されます")
        
        self.start_button.config(text="🚗 スタートライン通過", bg='green', state='normal')
        
        print("🔄 Race reset - Ready for new race")
    
    def quit_system(self):
        """システム終了"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join()
        pygame.mixer.quit()
        self.root.destroy()
    
    def run(self):
        """メインループ"""
        print("🏁 Virtual Lap Timer System Starting...")
        print("🎮 GUI mode with manual triggers")
        
        self.create_gui()
        
        # タイマー更新スレッド開始
        self.update_thread = threading.Thread(target=self.auto_update_timer, daemon=True)
        self.update_thread.start()
        
        # GUI開始
        self.root.mainloop()

def main():
    """メイン実行"""
    print("🎮 Virtual Lap Timer System")
    print("=" * 50)
    print("Features:")
    print("• 🖱️ GUI操作によるマニュアルトリガー")
    print("• ⏱️ リアルタイムタイマー表示")
    print("• 🎵 効果音再生")
    print("• 📊 結果表示・保存")
    print("• 🔄 リセット・終了機能")
    print("=" * 50)
    
    system = VirtualLapTimeSystem()
    system.run()

if __name__ == "__main__":
    main()