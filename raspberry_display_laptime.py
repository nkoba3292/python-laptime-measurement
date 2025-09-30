#!/usr/bin/env python3
"""
🖥️ Raspberry Pi 5 フルスクリーン表示版ラップタイム計測システム
PyGame使用・モニター直接表示・キーボード操作対応
"""

import pygame
import cv2
import time
import numpy as np
import json
import threading
from datetime import datetime
import os
import sys

# PyGame 初期化
pygame.init()

class RaspberryDisplayLaptimeSystem:
    def __init__(self):
        # ディスプレイ設定
        self.screen_width = 1920
        self.screen_height = 1080
        
        # フルスクリーン設定を試行、失敗時はウィンドウモード
        try:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
            self.fullscreen = True
        except:
            self.screen = pygame.display.set_mode((1280, 720))
            self.fullscreen = False
            self.screen_width = 1280
            self.screen_height = 720
            
        pygame.display.set_caption("🏁 Raspberry Pi 5 Lap Timer System")
        
        # 色定義
        self.colors = {
            'background': (20, 20, 30),
            'text_white': (255, 255, 255),
            'text_green': (0, 255, 0),
            'text_yellow': (255, 255, 0),
            'text_red': (255, 0, 0),
            'text_cyan': (0, 255, 255),
            'panel_bg': (50, 50, 70),
            'border': (100, 100, 120)
        }
        
        # フォント設定
        try:
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 36)
            self.font_tiny = pygame.font.Font(None, 24)
        except:
            self.font_large = pygame.font.SysFont('arial', 72)
            self.font_medium = pygame.font.SysFont('arial', 48)
            self.font_small = pygame.font.SysFont('arial', 36)
            self.font_tiny = pygame.font.SysFont('arial', 24)
        
        # カメラ設定
        self.camera_overview = None
        self.camera_start_line = None
        self.bg_subtractor = None
        
        # レース状態
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        self.last_detection_time = 0
        self.detection_cooldown = 2.0
        
        # システム状態
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 30
        
        # フレームバッファ
        self.current_overview_frame = None
        self.current_startline_frame = None
        self.last_motion_pixels = 0
        
        # 設定読み込み
        self.load_config()
        
        # カメラスレッド用ロック
        self.frame_lock = threading.Lock()
        
    def load_config(self):
        """設定ファイル読み込み"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # デフォルト設定
            self.config = {
                "camera_settings": {
                    "overview_camera_index": 0,
                    "startline_camera_index": 2,
                    "frame_width": 640,
                    "frame_height": 480
                },
                "detection_settings": {
                    "motion_pixels_threshold": 500
                },
                "race_settings": {
                    "max_laps": 10,
                    "detection_cooldown": 2.0
                }
            }
            print("⚠️ config.json not found, using default settings")
            
    def initialize_cameras(self):
        """カメラ初期化"""
        print("📹 Raspberry Pi 5 カメラシステム初期化中...")
        
        # Overview カメラ
        overview_idx = self.config['camera_settings']['overview_camera_index']
        self.camera_overview = cv2.VideoCapture(overview_idx)
        if not self.camera_overview.isOpened():
            print(f"❌ Overview camera (index {overview_idx}) failed to open")
            return False
            
        # StartLine カメラ
        startline_idx = self.config['camera_settings']['startline_camera_index']
        self.camera_start_line = cv2.VideoCapture(startline_idx)
        if not self.camera_start_line.isOpened():
            print(f"❌ Start line camera (index {startline_idx}) failed to open")
            return False
            
        # カメラ設定最適化
        for camera in [self.camera_overview, self.camera_start_line]:
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            camera.set(cv2.CAP_PROP_FPS, 30)
        
        # 背景差分初期化
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()
        
        print("✅ カメラ初期化成功")
        return True
        
    def camera_thread(self):
        """カメラフレーム取得スレッド"""
        while self.running:
            try:
                ret_ov, frame_ov = self.camera_overview.read()
                ret_sl, frame_sl = self.camera_start_line.read()
                
                if ret_ov and ret_sl:
                    with self.frame_lock:
                        self.current_overview_frame = frame_ov.copy()
                        self.current_startline_frame = frame_sl.copy()
                        
                    # 車両検知
                    detected, motion_pixels = self.detect_vehicle_crossing(frame_sl)
                    self.last_motion_pixels = motion_pixels
                    
                    if detected:
                        self.handle_vehicle_detection(motion_pixels)
                        
            except Exception as e:
                print(f"カメラスレッドエラー: {e}")
                
            time.sleep(1/30)  # 30fps
            
    def detect_vehicle_crossing(self, frame):
        """車両通過検知"""
        if not self.bg_subtractor:
            return False, 0
            
        fg_mask = self.bg_subtractor.apply(frame)
        motion_pixels = cv2.countNonZero(fg_mask)
        
        motion_threshold = self.config['detection_settings']['motion_pixels_threshold']
        current_time = time.time()
        
        if (motion_pixels > motion_threshold and 
            current_time - self.last_detection_time > self.detection_cooldown):
            self.last_detection_time = current_time
            return True, motion_pixels
            
        return False, motion_pixels
        
    def handle_vehicle_detection(self, motion_pixels):
        """車両検知時の処理"""
        current_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if not self.race_active:
            # レース開始
            self.race_active = True
            self.start_time = current_time
            self.lap_count = 0
            print(f"🏁 レース開始! {timestamp}")
            
        else:
            # ラップ記録
            lap_time = current_time - self.start_time
            self.lap_count += 1
            self.lap_times.append(lap_time)
            
            print(f"🏁 LAP {self.lap_count} 完了! タイム: {lap_time:.3f}秒")
            
            # 最大ラップ数チェック
            max_laps = self.config['race_settings']['max_laps']
            if self.lap_count >= max_laps:
                self.finish_race()
                
    def finish_race(self):
        """レース終了処理"""
        if self.lap_times:
            best_lap = min(self.lap_times)
            total_time = sum(self.lap_times)
            
            print("🏆 レース終了!")
            print(f"📊 ベストラップ: {best_lap:.3f}秒")
            
            self.save_race_result()
            
        self.race_active = False
        
    def save_race_result(self):
        """レース結果保存"""
        if not os.path.exists('data'):
            os.makedirs('data')
            
        result = {
            'timestamp': datetime.now().isoformat(),
            'lap_count': self.lap_count,
            'lap_times': self.lap_times,
            'best_lap': min(self.lap_times) if self.lap_times else 0,
            'total_time': sum(self.lap_times) if self.lap_times else 0
        }
        
        filename = f"data/race_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
            
        print(f"💾 結果保存: {filename}")
        
    def opencv_to_pygame(self, cv_image):
        """OpenCV画像をPygame用に変換"""
        if cv_image is None:
            return None
            
        # BGR to RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        # 回転（OpenCVとPygameの座標系違い）
        rgb_image = np.rot90(rgb_image)
        rgb_image = np.fliplr(rgb_image)
        # Pygame Surface作成
        return pygame.surfarray.make_surface(rgb_image)
        
    def draw_camera_feeds(self):
        """カメラ映像描画"""
        with self.frame_lock:
            overview_frame = self.current_overview_frame
            startline_frame = self.current_startline_frame
            
        if overview_frame is not None and startline_frame is not None:
            # Overview camera (メイン表示)
            overview_surface = self.opencv_to_pygame(overview_frame)
            if overview_surface:
                # スケーリング
                overview_scaled = pygame.transform.scale(overview_surface, (1200, 600))
                self.screen.blit(overview_scaled, (50, 50))
                
            # StartLine camera (サブ表示)
            startline_surface = self.opencv_to_pygame(startline_frame)
            if startline_surface:
                # スケーリング
                startline_scaled = pygame.transform.scale(startline_surface, (400, 300))
                self.screen.blit(startline_scaled, (1300, 50))
                
        # カメララベル描画
        overview_label = self.font_medium.render("Overview Camera", True, self.colors['text_white'])
        self.screen.blit(overview_label, (50, 10))
        
        startline_label = self.font_small.render("Start Line", True, self.colors['text_white'])
        self.screen.blit(startline_label, (1300, 10))
        
    def draw_race_info(self):
        """レース情報描画"""
        # 情報パネル背景
        info_rect = pygame.Rect(50, 700, 1200, 300)
        pygame.draw.rect(self.screen, self.colors['panel_bg'], info_rect)
        pygame.draw.rect(self.screen, self.colors['border'], info_rect, 3)
        
        y_offset = 720
        
        # レース状態
        if self.race_active:
            status_text = f"🏁 RACING - LAP {self.lap_count}"
            status_color = self.colors['text_green']
            
            if self.start_time:
                current_time = time.time() - self.start_time
                time_text = f"TIME: {current_time:.2f}s"
            else:
                time_text = "TIME: 0.00s"
        else:
            status_text = "🎯 WAITING FOR START"
            status_color = self.colors['text_yellow']
            time_text = "Ready to Race"
            
        status_surface = self.font_large.render(status_text, True, status_color)
        self.screen.blit(status_surface, (70, y_offset))
        
        time_surface = self.font_medium.render(time_text, True, self.colors['text_white'])
        self.screen.blit(time_surface, (70, y_offset + 80))
        
        # ラップタイム表示
        if self.lap_times:
            best_lap = min(self.lap_times)
            last_lap = self.lap_times[-1]
            total_time = sum(self.lap_times)
            avg_lap = total_time / len(self.lap_times)
            
            lap_info = [
                f"🏆 BEST LAP: {best_lap:.3f}s",
                f"⏱️ LAST LAP: {last_lap:.3f}s",
                f"📊 AVG LAP: {avg_lap:.3f}s",
                f"🏁 TOTAL LAPS: {len(self.lap_times)}"
            ]
            
            for i, info in enumerate(lap_info):
                lap_surface = self.font_small.render(info, True, self.colors['text_cyan'])
                self.screen.blit(lap_surface, (700, y_offset + 20 + i * 40))
                
        # システム情報
        system_info = [
            f"Motion Pixels: {self.last_motion_pixels}",
            f"FPS: {int(self.clock.get_fps())}",
            f"Resolution: {self.screen_width}x{self.screen_height}"
        ]
        
        for i, info in enumerate(system_info):
            system_surface = self.font_tiny.render(info, True, self.colors['text_white'])
            self.screen.blit(system_surface, (70, y_offset + 140 + i * 25))
            
    def draw_controls_info(self):
        """操作方法表示"""
        controls_rect = pygame.Rect(1300, 400, 400, 250)
        pygame.draw.rect(self.screen, self.colors['panel_bg'], controls_rect)
        pygame.draw.rect(self.screen, self.colors['border'], controls_rect, 2)
        
        controls = [
            "🎮 CONTROLS",
            "",
            "R - Reset Race",
            "Q - Quit System",
            "F - Toggle Fullscreen",
            "S - Save Screenshot",
            "",
            "ESC - Exit"
        ]
        
        for i, control in enumerate(controls):
            if control == "🎮 CONTROLS":
                color = self.colors['text_yellow']
                font = self.font_small
            elif control == "":
                continue
            else:
                color = self.colors['text_white']
                font = self.font_tiny
                
            control_surface = font.render(control, True, color)
            self.screen.blit(control_surface, (1320, 420 + i * 25))
            
    def handle_keypress(self, key):
        """キー入力処理"""
        if key == pygame.K_r:
            # レースリセット
            self.reset_race()
        elif key == pygame.K_q or key == pygame.K_ESCAPE:
            # システム終了
            self.running = False
        elif key == pygame.K_f:
            # フルスクリーン切り替え
            self.toggle_fullscreen()
        elif key == pygame.K_s:
            # スクリーンショット保存
            self.save_screenshot()
            
    def reset_race(self):
        """レースリセット"""
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        print("🔄 レースリセット完了")
        
    def toggle_fullscreen(self):
        """フルスクリーン切り替え"""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
            self.screen_width = 1920
            self.screen_height = 1080
        else:
            self.screen = pygame.display.set_mode((1280, 720))
            self.screen_width = 1280
            self.screen_height = 720
            
    def save_screenshot(self):
        """スクリーンショット保存"""
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
            
        filename = f"screenshots/laptime_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pygame.image.save(self.screen, filename)
        print(f"📸 スクリーンショット保存: {filename}")
        
    def run(self):
        """メイン実行ループ"""
        print("🖥️ Raspberry Pi 5 フルスクリーン表示版ラップタイム計測システム起動")
        print("🎮 キーボード操作: R=リセット, Q/ESC=終了, F=フルスクリーン, S=スクリーンショット")
        
        if not self.initialize_cameras():
            print("❌ カメラ初期化失敗")
            return False
            
        # カメラスレッド開始
        camera_thread = threading.Thread(target=self.camera_thread, daemon=True)
        camera_thread.start()
        
        # メインループ
        while self.running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keypress(event.key)
                    
            # 画面描画
            self.screen.fill(self.colors['background'])
            
            self.draw_camera_feeds()
            self.draw_race_info()
            self.draw_controls_info()
            
            # 画面更新
            pygame.display.flip()
            self.clock.tick(self.fps)
            
        self.cleanup()
        return True
        
    def cleanup(self):
        """リソース解放"""
        self.running = False
        
        if self.camera_overview:
            self.camera_overview.release()
        if self.camera_start_line:
            self.camera_start_line.release()
            
        pygame.quit()
        print("🔧 システム終了")

def main():
    print("🖥️ Raspberry Pi 5 フルスクリーン ラップタイム計測システム")
    print("=" * 60)
    
    try:
        system = RaspberryDisplayLaptimeSystem()
        success = system.run()
        
        if success:
            print("✅ システム正常終了")
        else:
            print("❌ システムエラー終了")
            
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()