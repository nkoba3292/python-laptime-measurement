# main_laptime_system.py
# -*- coding: utf-8 -*-
"""
自動運転ミニカー予選タイム計測システム
- LOGICOOL C270 x2台でリアルタイム映像
- スタートライン検出による自動タイム計測
- 3周分のラップタイム測定と表示
"""
import cv2
import numpy as np
import time
import pygame
import json
import threading
from datetime import datetime
from pathlib import Path

class LapTimeSystem:
    def __init__(self, debug_mode=False):
        # デバッグモード設定
        self.debug_mode = debug_mode
        
        # カメラ設定
        self.camera_start_line = None  # スタートライン用カメラ
        self.camera_overview = None    # 俯瞰用カメラ
        
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
        
        # スタートライン検出
        self.line_detection_enabled = True
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # 2秒のクールダウン
        
        # 音響システム
        pygame.mixer.init()
        self.sound_start = None
        self.sound_finish = None
        
        # データ保存
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 画面設定
        self.window_name = "Autonomous Car Lap Timer"
        self.frame_width = 1280
        self.frame_height = 720
        
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
        import wave
        
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
    
    def initialize_cameras(self):
        """カメラの初期化"""
        if self.debug_mode:
            print("🔧 DEBUG MODE: Running without real cameras")
            return True
            
        try:
            # カメラ0: 俯瞰用（メイン表示）
            self.camera_overview = cv2.VideoCapture(0)
            if not self.camera_overview.isOpened():
                print("❌ Overview camera (index 0) failed to open")
                print("💡 Switching to debug mode...")
                self.debug_mode = True
                return True
            
            # カメラ1: スタートライン用
            self.camera_start_line = cv2.VideoCapture(1)
            if not self.camera_start_line.isOpened():
                print("❌ Start line camera (index 1) failed to open")
                print("💡 Switching to debug mode...")
                self.debug_mode = True
                if self.camera_overview:
                    self.camera_overview.release()
                return True
            
            # カメラ設定
            self.camera_overview.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera_overview.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera_start_line.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera_start_line.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            print("✅ Both cameras initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Camera initialization error: {e}")
            return False
    
    def detect_start_line_crossing(self, frame):
        """スタートライン通過の検出（画像処理ベース）"""
        if not self.line_detection_enabled:
            return False
        
        # クールダウンチェック
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            return False
        
        # 簡易的な動体検出（実際の実装では車両の特徴検出を使用）
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # スタートライン領域の設定（画面中央部）
        h, w = gray.shape
        line_region = gray[int(h*0.4):int(h*0.6), :]
        
        # 動きの検出（フレーム差分法）
        if hasattr(self, 'prev_frame'):
            diff = cv2.absdiff(line_region, self.prev_frame)
            motion_pixels = np.sum(diff > 30)  # 閾値は調整可能
            
            # 動きが一定以上あった場合、車両通過と判定
            if motion_pixels > 1000:  # 閾値は調整可能
                self.prev_frame = line_region
                self.last_detection_time = current_time
                return True
        
        self.prev_frame = line_region
        return False
    
    def handle_start_line_crossing(self):
        """スタートライン通過時の処理"""
        current_time = time.time()
        
        if not self.race_started:
            # レース開始
            self.race_started = True
            self.start_time = current_time
            self.current_lap = 1
            print("🏁 RACE STARTED!")
            
            # スタート音再生
            if self.sound_start:
                self.sound_start.play()
            
        else:
            # ラップ完了
            lap_time = current_time - self.start_time
            self.lap_times.append(lap_time)
            self.current_lap += 1
            
            print(f"⏱️ Lap {len(self.lap_times)} completed: {lap_time:.2f}s")
            
            # 3周目の半周で表示を非表示
            if self.current_lap == 3 and len(self.lap_times) == 2:
                # 次のラップの半分程度で非表示にする予約
                threading.Timer(lap_time / 2, self.hide_timer).start()
            
            # レース終了チェック
            if len(self.lap_times) >= self.max_laps:
                self.race_finished = True
                total_time = sum(self.lap_times)
                print(f"🏁 RACE FINISHED! Total time: {total_time:.2f}s")
                
                # フィニッシュ音再生
                if self.sound_finish:
                    self.sound_finish.play()
                
                # データ保存
                self.save_race_data()
    
    def hide_timer(self):
        """タイマー表示を非表示にする"""
        self.show_timer = False
        self.timer_hidden_at = time.time()
        print("🙈 Timer display hidden (3rd lap, halfway)")
    
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
    
    def draw_overlay(self, frame):
        """画面オーバーレイの描画"""
        h, w = frame.shape[:2]
        
        # 背景パネル
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
        cv2.addWeighted(frame, 0.7, overlay, 0.3, 0, frame)
        
        # タイトル
        cv2.putText(frame, "Autonomous Car Lap Timer", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # レース状態
        if not self.race_started:
            status = "Waiting for START..."
            color = (0, 255, 255)  # Yellow
        elif self.race_finished:
            status = "RACE FINISHED!"
            color = (0, 255, 0)  # Green
        else:
            status = f"LAP {self.current_lap}/{self.max_laps}"
            color = (0, 0, 255)  # Red
        
        cv2.putText(frame, status, (20, 65), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # タイマー表示（非表示設定時は表示しない）
        if self.show_timer and self.race_started and not self.race_finished:
            current_time = time.time() - self.start_time
            timer_text = f"Time: {current_time:.1f}s"
            cv2.putText(frame, timer_text, (20, 95), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # ラップタイム履歴
        for i, lap_time in enumerate(self.lap_times):
            lap_text = f"Lap {i+1}: {lap_time:.2f}s"
            cv2.putText(frame, lap_text, (20, 125 + i*25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    def combine_camera_feeds(self, overview_frame, startline_frame):
        """カメラ映像の合成（俯瞰メイン + スタートライン小窓）"""
        # 俯瞰カメラをメイン表示にリサイズ
        main_frame = cv2.resize(overview_frame, (self.frame_width, self.frame_height))
        
        # スタートラインカメラを小窓サイズにリサイズ（左下1/9）
        small_width = self.frame_width // 3
        small_height = self.frame_height // 3
        small_frame = cv2.resize(startline_frame, (small_width, small_height))
        
        # 小窓を左下に配置
        y_offset = self.frame_height - small_height - 10
        x_offset = 10
        
        # 小窓の境界線
        cv2.rectangle(main_frame, (x_offset-2, y_offset-2), 
                     (x_offset + small_width + 2, y_offset + small_height + 2), 
                     (255, 255, 255), 2)
        
        # 小窓を合成
        main_frame[y_offset:y_offset + small_height, 
                  x_offset:x_offset + small_width] = small_frame
        
        # スタートラインカメラのラベル
        cv2.putText(main_frame, "START LINE CAM", (x_offset, y_offset - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return main_frame
    
    def run(self):
        """メインループ"""
        print("🏁 Lap Timer System Starting...")
        
        if not self.initialize_cameras():
            print("❌ Camera initialization failed")
            return
        
        print("📹 Cameras ready")
        print("🎯 Waiting for vehicle to cross start line...")
        print("🔧 Controls: 'r' = reset, 'q' = quit")
        
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.frame_width, self.frame_height)
        
        try:
            while True:
                # フレーム取得
                ret1, overview_frame = self.camera_overview.read()
                ret2, startline_frame = self.camera_start_line.read()
                
                if not ret1 or not ret2:
                    print("❌ Failed to capture frames")
                    break
                
                # スタートライン検出（スタートラインカメラで）
                if self.detect_start_line_crossing(startline_frame):
                    self.handle_start_line_crossing()
                
                # 映像合成
                combined_frame = self.combine_camera_feeds(overview_frame, startline_frame)
                
                # オーバーレイ描画
                self.draw_overlay(combined_frame)
                
                # 表示
                cv2.imshow(self.window_name, combined_frame)
                
                # キー入力処理
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.reset_race()
                
                # レース終了後の自動終了（オプション）
                if self.race_finished and time.time() - self.start_time > 10:
                    print("🎯 Auto-closing after race completion...")
                    break
        
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
        if self.camera_overview:
            self.camera_overview.release()
        if self.camera_start_line:
            self.camera_start_line.release()
        cv2.destroyAllWindows()
        pygame.mixer.quit()
        print("🧹 System cleanup completed")

def main():
    """メイン実行"""
    print("🏁 Autonomous Car Lap Timer System")
    print("=" * 50)
    
    system = LapTimeSystem()
    system.run()

if __name__ == "__main__":
    main()