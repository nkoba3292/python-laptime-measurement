#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v7 - 超高感度版)
- v6よりさらに感度を大幅向上：motion_pixels_threshold 300, min_contour_area 200
- 検知条件を2/6以上に緩和して超敏感に反応
- わずかな動きでも確実に検知する最高感度設定
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

pygame.init()

class TeamsSimpleLaptimeSystemFixedV7:
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🏁 Lap Timer - Teams View (v7 - Ultra Sensitivity)")
        self.colors = {
            'background': (15, 15, 25),
            'text_white': (255, 255, 255),
            'text_green': (0, 255, 100),
            'text_yellow': (255, 255, 50),
            'text_red': (255, 80, 80),
            'panel_bg': (40, 40, 60),
            'border': (80, 80, 100)
        }
        try:
            self.font_huge = pygame.font.Font(None, 120)
            self.font_large = pygame.font.Font(None, 80)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
        except:
            self.font_huge = pygame.font.SysFont('arial', 120, bold=True)
            self.font_large = pygame.font.SysFont('arial', 80, bold=True)
            self.font_medium = pygame.font.SysFont('arial', 48)
            self.font_small = pygame.font.SysFont('arial', 32)
        self.camera_overview = None
        self.camera_start_line = None
        self.bg_subtractor = None
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        self.last_detection_time = 0
        self.detection_cooldown = 2.5  # v6:3.0→2.5秒（より早い連続検知）
        self.hide_time_after_lap = 3
        self.time_visible = True
        self.last_time_update = 0
        self.display_time = 0.0
        self.time_update_interval = 0.1
        self.last_motion_pixels = 0
        self.motion_history = []
        self.stable_frame_count = 0
        self.motion_area_ratio = 0.0
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.current_overview_frame = None
        self.current_startline_frame = None
        self.available_cameras = []
        self.load_config()
        self.frame_lock = threading.Lock()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # v7: 超高感度版の設定
            self.config = {
                "camera_settings": {
                    "overview_camera_index": 0,
                    "startline_camera_index": 2,
                    "frame_width": 640,
                    "frame_height": 480
                },
                "detection_settings": {
                    "motion_pixels_threshold": 300,      # v6:600→300 (超高感度)
                    "min_contour_area": 200,             # v6:500→200 (超小物体検知)
                    "motion_area_ratio_min": 0.008,      # v6:0.015→0.008 (極小面積比)
                    "motion_area_ratio_max": 0.9,        # 範囲拡大
                    "stable_frames_required": 2,         # v6:3→2 (より早い反応)
                    "motion_consistency_check": False    # 一貫性チェック無効化（超敏感）
                },
                "race_settings": {
                    "max_laps": 10,
                    "detection_cooldown": 2.5  # v6:3.0→2.5秒
                }
            }
            print("⚠️ config.json not found, using v7 ultra sensitivity settings")

    def find_available_cameras(self):
        print("🔍 利用可能なカメラを検索中...")
        self.available_cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.available_cameras.append(i)
                    print(f"✅ カメラ {i}: 利用可能")
                cap.release()
        print(f"📹 検出されたカメラ: {self.available_cameras}")
        return len(self.available_cameras) >= 1

    def initialize_cameras(self):
        print("📹 Teams用シンプル表示カメラシステム初期化中...")
        if not self.find_available_cameras():
            print("❌ 利用可能なカメラが見つかりません")
            return False
        if len(self.available_cameras) >= 1:
            overview_idx = self.available_cameras[0]
        else:
            overview_idx = 0
        self.camera_overview = cv2.VideoCapture(overview_idx)
        if not self.camera_overview.isOpened():
            print(f"❌ Overview camera (index {overview_idx}) failed to open")
            return False
        if len(self.available_cameras) >= 2:
            startline_idx = self.available_cameras[1]
        else:
            startline_idx = self.available_cameras[0] if self.available_cameras else 0
        self.camera_start_line = cv2.VideoCapture(startline_idx)
        if not self.camera_start_line.isOpened():
            print(f"❌ Start line camera (index {startline_idx}) failed to open")
            return False
        for camera in [self.camera_overview, self.camera_start_line]:
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            camera.set(cv2.CAP_PROP_FPS, 30)
        # v7: より敏感な背景差分設定
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=300,           # v6:500→300 (短い履歴でより敏感)
            varThreshold=25,       # v6:50→25 (より低い分散閾値)
            detectShadows=False
        )
        print("✅ カメラ初期化完了 (v7 - 超高感度版)")
        return True

    def camera_thread(self):
        while self.running:
            try:
                ret_ov, frame_ov = self.camera_overview.read()
                ret_sl, frame_sl = self.camera_start_line.read()
                if ret_ov and ret_sl:
                    frame_ov_flipped = cv2.flip(frame_ov, 1)
                    frame_sl_flipped = cv2.flip(frame_sl, 1)
                    with self.frame_lock:
                        self.current_overview_frame = frame_ov_flipped.copy()
                        self.current_startline_frame = frame_sl_flipped.copy()
                    detected, motion_data = self.detect_vehicle_crossing_ultra(frame_sl_flipped)
                    self.last_motion_pixels = motion_data['motion_pixels']
                    self.motion_area_ratio = motion_data['area_ratio']
                    if detected:
                        self.handle_vehicle_detection(motion_data)
            except Exception as e:
                print(f"カメラスレッドエラー: {e}")
            time.sleep(1/30)

    def detect_vehicle_crossing_ultra(self, frame):
        if not self.bg_subtractor:
            return False, {'motion_pixels': 0, 'area_ratio': 0.0, 'contour_count': 0, 'largest_contour_area': 0}
        fg_mask = self.bg_subtractor.apply(frame)
        # v7: より軽いノイズ除去（感度を保つため）
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))  # v6:(5,5)→(3,3)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        # Gaussian Blurを軽減
        fg_mask = cv2.GaussianBlur(fg_mask, (3, 3), 0)  # v6:(5,5)→(3,3)
        _, fg_mask = cv2.threshold(fg_mask, 100, 255, cv2.THRESH_BINARY)  # v6:127→100
        motion_pixels = cv2.countNonZero(fg_mask)
        total_pixels = frame.shape[0] * frame.shape[1]
        area_ratio = motion_pixels / total_pixels if total_pixels > 0 else 0
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_contours = []
        min_contour_area = self.config['detection_settings']['min_contour_area']
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_contour_area:
                valid_contours.append(contour)
        largest_contour_area = max([cv2.contourArea(c) for c in valid_contours]) if valid_contours else 0
        motion_data = {
            'motion_pixels': motion_pixels,
            'area_ratio': area_ratio,
            'contour_count': len(valid_contours),
            'largest_contour_area': largest_contour_area
        }
        detection_result = self.evaluate_detection_ultra(motion_data)
        return detection_result, motion_data

    def evaluate_detection_ultra(self, motion_data):
        current_time = time.time()
        detection_settings = self.config['detection_settings']
        motion_threshold = detection_settings['motion_pixels_threshold']
        min_area_ratio = detection_settings['motion_area_ratio_min']
        max_area_ratio = detection_settings['motion_area_ratio_max']
        condition1 = motion_data['motion_pixels'] > motion_threshold
        condition2 = (min_area_ratio <= motion_data['area_ratio'] <= max_area_ratio)
        condition3 = motion_data['contour_count'] > 0
        condition4 = (current_time - self.last_detection_time) > self.detection_cooldown
        condition5 = motion_data['largest_contour_area'] > detection_settings['min_contour_area']
        self.motion_history.append(motion_data['motion_pixels'])
        if len(self.motion_history) > 5:  # v6:10→5 (短い履歴)
            self.motion_history.pop(0)
        # v7: 一貫性チェックを無効化または大幅緩和
        condition6 = True
        if (len(self.motion_history) >= 2 and 
            detection_settings.get('motion_consistency_check', False)):
            recent_motion = self.motion_history[-2:]  # v6:3→2
            motion_std = np.std(recent_motion)
            motion_mean = np.mean(recent_motion)
            if motion_mean > 0:
                cv_motion = motion_std / motion_mean
                condition6 = cv_motion < 5.0  # v6:2.0→5.0 (大幅緩和)
        all_conditions = [condition1, condition2, condition3, condition4, condition5, condition6]
        conditions_met = sum(all_conditions)
        # v7: より詳細なデバッグ情報
        if motion_data['motion_pixels'] > 50:  # v6:100→50
            debug_info = f"v7検知: {conditions_met}/6 | 動き:{motion_data['motion_pixels']} | 面積:{motion_data['area_ratio']:.4f} | 輪郭:{motion_data['contour_count']} | 最大輪郭:{motion_data['largest_contour_area']}"
            print(debug_info)
        # v7: 2条件以上で検知（超高感度）
        if conditions_met >= 2:
            self.last_detection_time = current_time
            print(f"🎯 車両検知成功: 条件クリア ({conditions_met}/6) - 超高感度検知")
            return True
        return False

    def handle_vehicle_detection(self, motion_data):
        current_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if not self.race_active:
            self.race_active = True
            self.start_time = current_time
            self.lap_count = 0
            self.time_visible = True
            print(f"🏁 レース開始: {timestamp}")
            print(f"   v7検知データ: 動き={motion_data['motion_pixels']}, 面積比={motion_data['area_ratio']:.4f}")
        else:
            lap_time = current_time - self.start_time
            self.lap_count += 1
            self.lap_times.append(lap_time)
            print(f"🏁 LAP {self.lap_count} 完了: タイム: {lap_time:.3f}秒")
            print(f"   v7検知データ: 動き={motion_data['motion_pixels']}, 面積比={motion_data['area_ratio']:.4f}")
            if self.lap_count >= self.hide_time_after_lap:
                self.time_visible = False
            max_laps = self.config['race_settings']['max_laps']
            if self.lap_count >= max_laps:
                self.finish_race()

    def finish_race(self):
        if self.lap_times:
            best_lap = min(self.lap_times)
            total_time = sum(self.lap_times)
            print("🏁 レース終了")
            print(f"🏆 ベストラップ: {best_lap:.3f}秒")
            self.save_race_result()
        self.race_active = False
        self.time_visible = True

    def save_race_result(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        result = {
            'timestamp': datetime.now().isoformat(),
            'lap_count': self.lap_count,
            'lap_times': self.lap_times,
            'best_lap': min(self.lap_times) if self.lap_times else 0,
            'total_time': sum(self.lap_times) if self.lap_times else 0,
            'detection_settings': self.config['detection_settings'],
            'version': 'v7_ultra_sensitivity'
        }
        filename = f"data/race_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 結果保存: {filename}")

    def update_display_time(self):
        current_time = time.time()
        if current_time - self.last_time_update >= self.time_update_interval:
            if self.race_active and self.start_time:
                self.display_time = current_time - self.start_time
            else:
                self.display_time = 0.0
            self.last_time_update = current_time

    def opencv_to_pygame(self, cv_image):
        if cv_image is None:
            return None
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        rgb_image = np.transpose(rgb_image, (1, 0, 2))
        rgb_image = np.flipud(rgb_image)
        return pygame.surfarray.make_surface(rgb_image)

    def draw_camera_feeds(self):
        with self.frame_lock:
            overview_frame = self.current_overview_frame
            startline_frame = self.current_startline_frame
        if overview_frame is not None:
            overview_surface = self.opencv_to_pygame(overview_frame)
            if overview_surface:
                overview_scaled = pygame.transform.scale(overview_surface, (800, 400))
                self.screen.blit(overview_scaled, (50, 50))
        if startline_frame is not None:
            startline_surface = self.opencv_to_pygame(startline_frame)
            if startline_surface:
                startline_scaled = pygame.transform.scale(startline_surface, (400, 300))
                self.screen.blit(startline_scaled, (880, 50))
                detection_rect = pygame.Rect(880 + 100, 50 + 100, 200, 100)
                pygame.draw.rect(self.screen, self.colors['text_red'], detection_rect, 2)
                if hasattr(self, 'last_motion_pixels') and self.last_motion_pixels > 0:
                    motion_text = f"Motion: {self.last_motion_pixels}"
                    motion_surface = self.font_small.render(motion_text, True, self.colors['text_green'])
                    self.screen.blit(motion_surface, (880, 360))
                    ratio_text = f"Area: {self.motion_area_ratio:.4f}"  # v7: 4桁表示
                    ratio_surface = self.font_small.render(ratio_text, True, self.colors['text_yellow'])
                    self.screen.blit(ratio_surface, (880, 380))
        if len(self.available_cameras) < 2:
            if startline_frame is not None and overview_frame is not None:
                gray_frame = cv2.cvtColor(startline_frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray_frame, 50, 150)
                edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                edges_surface = self.opencv_to_pygame(edges_colored)
                if edges_surface:
                    edges_scaled = pygame.transform.scale(edges_surface, (400, 300))
                    self.screen.blit(edges_scaled, (880, 50))
            warning_text = self.font_small.render("⚠️ Single camera: Edge detection view", True, self.colors['text_yellow'])
            self.screen.blit(warning_text, (200, 5))
        overview_label = self.font_medium.render("Overview Camera (Fixed)", True, self.colors['text_white'])
        self.screen.blit(overview_label, (50, 10))
        startline_label = self.font_medium.render("StartLine (Ultra Sensitivity)", True, self.colors['text_white'])
        self.screen.blit(startline_label, (880, 10))

    def draw_simple_race_info(self):
        self.update_display_time()
        info_rect = pygame.Rect(50, 480, 1180, 220)
        pygame.draw.rect(self.screen, self.colors['panel_bg'], info_rect)
        pygame.draw.rect(self.screen, self.colors['border'], info_rect, 2)
        if self.race_active:
            lap_text = f"LAP {self.lap_count}"
            lap_color = self.colors['text_green']
            if self.time_visible:
                time_text = f"{self.display_time:.1f}s"
                time_color = self.colors['text_white']
            else:
                time_text = "--- HIDDEN ---"
                time_color = self.colors['text_red']
        else:
            lap_text = "READY"
            lap_color = self.colors['text_yellow']
            time_text = "00.0s"
            time_color = self.colors['text_white']
        lap_surface = self.font_huge.render(lap_text, True, lap_color)
        self.screen.blit(lap_surface, (80, 520))
        time_surface = self.font_large.render(time_text, True, time_color)
        time_rect = time_surface.get_rect()
        self.screen.blit(time_surface, (1050 - time_rect.width, 540))
        if self.lap_times:
            best_lap = min(self.lap_times)
            if self.time_visible:
                best_text = f"BEST: {best_lap:.3f}s"
            else:
                best_text = "BEST: ---"
            best_surface = self.font_small.render(best_text, True, self.colors['text_white'])
            best_rect = best_surface.get_rect()
            self.screen.blit(best_surface, (1050 - best_rect.width, 620))
        if not self.time_visible and self.race_active:
            hide_info = self.font_small.render("⚠️ TIME HIDDEN", True, self.colors['text_red'])
            hide_rect = hide_info.get_rect()
            self.screen.blit(hide_info, (640 - hide_rect.width // 2, 650))
        fps_text = f"FPS: {int(self.clock.get_fps())}"
        fps_surface = self.font_small.render(fps_text, True, self.colors['text_white'])
        self.screen.blit(fps_surface, (80, 670))
        version_text = "v7 - Ultra Sensitivity"
        version_surface = self.font_small.render(version_text, True, self.colors['text_red'])  # 赤色で強調
        self.screen.blit(version_surface, (850, 670))

    def handle_keypress(self, key):
        if key == pygame.K_r:
            self.reset_race()
        elif key == pygame.K_q or key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_t:
            self.time_visible = not self.time_visible
            print(f"タイム表示: {'ON' if self.time_visible else 'OFF'}")
        elif key == pygame.K_s:
            self.save_screenshot()
        elif key == pygame.K_c:
            self.show_camera_info()
        elif key == pygame.K_d:
            self.show_detection_settings()

    def show_camera_info(self):
        print("📹 カメラ情報:")
        print(f"利用可能なカメラ: {self.available_cameras}")
        print(f"Overview カメラ稼働中: {self.camera_overview.isOpened() if self.camera_overview else 'None'}")
        print(f"StartLine カメラ稼働中: {self.camera_start_line.isOpened() if self.camera_start_line else 'None'}")
        print("🔄 左右反転修正: 有効 (cv2.flip適用)")

    def show_detection_settings(self):
        print("🎯 検知設定 (v7 超高感度版):")
        ds = self.config['detection_settings']
        print(f"  動きピクセル閾値: {ds['motion_pixels_threshold']} (超高感度)")
        print(f"  最小輪郭面積: {ds['min_contour_area']} (超高感度)")
        print(f"  面積比範囲: {ds['motion_area_ratio_min']:.4f} - {ds['motion_area_ratio_max']:.1f} (超高感度)")
        print(f"  検知条件: 2/6以上 (超高感度)")
        print(f"  クールダウン: {self.detection_cooldown}秒 (短縮)")
        print(f"  一貫性チェック: {'無効' if not ds.get('motion_consistency_check', True) else '緩和'}")
        print(f"  直近動きピクセル: {self.last_motion_pixels}")
        print(f"  直近面積比: {self.motion_area_ratio:.4f}")

    def reset_race(self):
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        self.time_visible = True
        self.display_time = 0.0
        self.motion_history = []
        print("🔄 レースリセット完了")

    def save_screenshot(self):
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
        filename = f"screenshots/teams_view_v7_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pygame.image.save(self.screen, filename)
        print(f"📸 スクリーンショット保存: {filename}")

    def run(self):
        print("🏁 Teams共有用シンプル表示タイム計測システム起動 (v7 - 物体検知超高感度版)")
        print("🎮 操作: R=リセット, Q/ESC=終了, T=タイム表示切替, S=スクリーンショット, C=カメラ情報, D=検知設定")
        print("⚠️  v7特徴: わずかな動きでも確実に検知する超高感度設定（誤検知の可能性も高い）")
        if not self.initialize_cameras():
            print("❌ カメラ初期化失敗")
            return False
        camera_thread = threading.Thread(target=self.camera_thread, daemon=True)
        camera_thread.start()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keypress(event.key)
            self.screen.fill(self.colors['background'])
            self.draw_camera_feeds()
            self.draw_simple_race_info()
            pygame.display.flip()
            self.clock.tick(self.fps)
        self.cleanup()
        return True

    def cleanup(self):
        self.running = False
        if self.camera_overview:
            self.camera_overview.release()
        if self.camera_start_line:
            self.camera_start_line.release()
        pygame.quit()
        print("🏁 システム終了")

def main():
    print("🏁 Teams共有用シンプル表示タイム計測システム (v7 - 物体検知超高感度版)")
    print("=" * 70)
    print("⚠️  注意: 超高感度設定のため誤検知が発生する可能性があります")
    try:
        system = TeamsSimpleLaptimeSystemFixedV7()
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