#!/usr/bin/env python3
"""
📱 Teams共有用シンプル表示版ラップタイム計測システム
- メイン映像2個のみ
- 周回数・タイムのみ表示
- 3周目後半でタイム非表示機能付き
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

class TeamsSimpleLaptimeSystem:
    def __init__(self):
        # ディスプレイ設定（Teams共有最適化）
        self.screen_width = 1280
        self.screen_height = 720
        
        # ウィンドウモード（Teams共有用）
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🏁 Lap Timer - Teams View")
        
        # シンプル色定義
        self.colors = {
            'background': (15, 15, 25),      # ダークブルー
            'text_white': (255, 255, 255),   # 白
            'text_green': (0, 255, 100),     # 明るい緑
            'text_yellow': (255, 255, 50),   # 明るい黄
            'text_red': (255, 80, 80),       # 明るい赤
            'panel_bg': (40, 40, 60),        # パネル背景
            'border': (80, 80, 100)          # 境界線
        }
        
        # シンプルフォント設定
        try:
            self.font_huge = pygame.font.Font(None, 120)     # 周回数用
            self.font_large = pygame.font.Font(None, 80)     # タイム用
            self.font_medium = pygame.font.Font(None, 48)    # ラベル用
            self.font_small = pygame.font.Font(None, 32)     # 状態用
        except:
            self.font_huge = pygame.font.SysFont('arial', 120, bold=True)
            self.font_large = pygame.font.SysFont('arial', 80, bold=True)
            self.font_medium = pygame.font.SysFont('arial', 48)
            self.font_small = pygame.font.SysFont('arial', 32)
        
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
        
        # タイム表示制御
        self.hide_time_after_lap = 3        # 3周目以降でタイム非表示
        self.time_visible = True
        
        # システム状態
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 30
        
        # フレームバッファ
        self.current_overview_frame = None
        self.current_startline_frame = None
        
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
        print("📹 Teams用シンプル表示カメラシステム初期化中...")
        
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
            self.time_visible = True
            print(f"🏁 レース開始! {timestamp}")
            
        else:
            # ラップ記録
            lap_time = current_time - self.start_time
            self.lap_count += 1
            self.lap_times.append(lap_time)
            
            print(f"🏁 LAP {self.lap_count} 完了! タイム: {lap_time:.3f}秒")
            
            # タイム表示制御（3周目以降で非表示）
            if self.lap_count >= self.hide_time_after_lap:
                self.time_visible = False
            
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
        self.time_visible = True  # レース終了時にタイム表示復活
        
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
        """シンプルカメラ映像描画"""
        with self.frame_lock:
            overview_frame = self.current_overview_frame
            startline_frame = self.current_startline_frame
            
        if overview_frame is not None and startline_frame is not None:
            # Overview camera (左半分)
            overview_surface = self.opencv_to_pygame(overview_frame)
            if overview_surface:
                overview_scaled = pygame.transform.scale(overview_surface, (620, 400))
                self.screen.blit(overview_scaled, (20, 20))
                
            # StartLine camera (右半分)
            startline_surface = self.opencv_to_pygame(startline_frame)
            if startline_surface:
                startline_scaled = pygame.transform.scale(startline_surface, (620, 400))
                self.screen.blit(startline_scaled, (640, 20))
                
        # シンプルラベル
        overview_label = self.font_medium.render("Overview", True, self.colors['text_white'])
        self.screen.blit(overview_label, (20, 430))
        
        startline_label = self.font_medium.render("Start Line", True, self.colors['text_white'])
        self.screen.blit(startline_label, (640, 430))
        
    def draw_simple_race_info(self):
        """シンプルレース情報描画"""
        # 下部情報エリア背景
        info_rect = pygame.Rect(20, 480, 1240, 220)
        pygame.draw.rect(self.screen, self.colors['panel_bg'], info_rect)
        pygame.draw.rect(self.screen, self.colors['border'], info_rect, 2)
        
        # レース状態とラップ数（左側・大きく表示）
        if self.race_active:
            # 周回数を超大きく表示
            lap_text = f"LAP {self.lap_count}"
            lap_color = self.colors['text_green']
            
            # 現在タイム表示制御
            if self.time_visible and self.start_time:
                current_time = time.time() - self.start_time
                time_text = f"{current_time:.1f}s"
                time_color = self.colors['text_white']
            else:
                time_text = "--- HIDDEN ---"
                time_color = self.colors['text_red']
        else:
            lap_text = "READY"
            lap_color = self.colors['text_yellow']
            time_text = "00.0s"
            time_color = self.colors['text_white']
            
        # ラップ数表示（左側）
        lap_surface = self.font_huge.render(lap_text, True, lap_color)
        self.screen.blit(lap_surface, (50, 520))
        
        # タイム表示（右側）
        time_surface = self.font_large.render(time_text, True, time_color)
        time_rect = time_surface.get_rect()
        self.screen.blit(time_surface, (1100 - time_rect.width, 540))
        
        # ベストラップ表示（右下）
        if self.lap_times:
            best_lap = min(self.lap_times)
            if self.time_visible:
                best_text = f"BEST: {best_lap:.3f}s"
            else:
                best_text = "BEST: ---"
            best_surface = self.font_small.render(best_text, True, self.colors['text_white'])
            best_rect = best_surface.get_rect()
            self.screen.blit(best_surface, (1100 - best_rect.width, 620))
            
        # 状態表示（中央下）
        if not self.time_visible and self.race_active:
            hide_info = self.font_small.render("⚠️ TIME HIDDEN", True, self.colors['text_red'])
            hide_rect = hide_info.get_rect()
            self.screen.blit(hide_info, (640 - hide_rect.width // 2, 650))
        
    def handle_keypress(self, key):
        """キー入力処理"""
        if key == pygame.K_r:
            # レースリセット
            self.reset_race()
        elif key == pygame.K_q or key == pygame.K_ESCAPE:
            # システム終了
            self.running = False
        elif key == pygame.K_t:
            # タイム表示切り替え（手動制御）
            self.time_visible = not self.time_visible
            print(f"タイム表示: {'ON' if self.time_visible else 'OFF'}")
        elif key == pygame.K_s:
            # スクリーンショット保存
            self.save_screenshot()
            
    def reset_race(self):
        """レースリセット"""
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        self.time_visible = True
        print("🔄 レースリセット完了")
        
    def save_screenshot(self):
        """スクリーンショット保存"""
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
            
        filename = f"screenshots/teams_view_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pygame.image.save(self.screen, filename)
        print(f"📸 スクリーンショット保存: {filename}")
        
    def run(self):
        """メイン実行ループ"""
        print("📱 Teams共有用シンプル表示版ラップタイム計測システム起動")
        print("🎮 操作: R=リセット, Q/ESC=終了, T=タイム表示切替, S=スクリーンショット")
        
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
            self.draw_simple_race_info()
            
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
    print("📱 Teams共有用シンプル表示版ラップタイム計測システム")
    print("=" * 60)
    
    try:
        system = TeamsSimpleLaptimeSystem()
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