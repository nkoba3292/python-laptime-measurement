#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v10 - オプティカルフロー版)
- Lucas-Kanadeオプティカルフローによる動き検出
- 特徴点の追跡で精密な動き検出
- より安定したモーション検出アルゴリズム
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

class TeamsSimpleLaptimeSystemFixedV10:
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🏁 Lap Timer - Teams View (v10 - Optical Flow)")
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
        
        # v10: オプティカルフロー用変数
        self.previous_gray = None
        self.feature_points = None
        self.lk_params = dict(winSize=(15, 15),
                             maxLevel=2,
                             criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
        self.feature_params = dict(maxCorners=100,
                                  qualityLevel=0.3,
                                  minDistance=7,
                                  blockSize=7)
        
        self.race_active = False
        self.lap_count = 0
        self.current_lap_start = None
        self.last_lap_time = 0.0
        self.best_lap_time = float('inf')
        self.total_time = 0.0
        self.race_start_time = None
        self.clock = pygame.time.Clock()
        self.running = True
        self.detection_cooldown = 0
        self.last_detection_time = 0
        self.motion_detected_recently = False
        self.detection_threshold_time = 1.0
        
        # v10: オプティカルフロー設定
        self.min_feature_points = 20  # 最小特徴点数
        self.motion_threshold = 2.0   # 動きの閾値
        self.min_moving_points = 10   # 動いている点の最小数
        self.max_flow_magnitude = 50  # 最大フロー大きさ（ノイズ除去）
        
        self.last_feature_count = 0
        self.last_moving_points = 0
        self.last_avg_motion = 0.0
        
        print(f"[v10 OPTICAL_FLOW] min_feature_points: {self.min_feature_points}")
        print(f"[v10 OPTICAL_FLOW] motion_threshold: {self.motion_threshold}")
        print(f"[v10 OPTICAL_FLOW] min_moving_points: {self.min_moving_points}")
        print("[v10 OPTICAL_FLOW] Lucas-Kanade optical flow detection")

    def load_config(self):
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.camera_overview_id = config.get('camera_overview_id', 0)
                self.camera_start_line_id = config.get('camera_start_line_id', 1)
                print(f"✅ 設定読み込み完了: Overview={self.camera_overview_id}, StartLine={self.camera_start_line_id}")
            except Exception as e:
                print(f"⚠️ 設定ファイル読み込みエラー: {e}")
                self.set_default_config()
        else:
            print("📁 設定ファイルが見つかりません。デフォルト設定を使用します。")
            self.set_default_config()

    def set_default_config(self):
        self.camera_overview_id = 0
        self.camera_start_line_id = 1

    def init_cameras(self):
        try:
            print("📷 カメラを初期化中...")
            self.camera_overview = cv2.VideoCapture(self.camera_overview_id)
            self.camera_start_line = cv2.VideoCapture(self.camera_start_line_id)
            
            if not self.camera_overview.isOpened():
                print(f"⚠️ オーバービューカメラ (ID: {self.camera_overview_id}) を開けませんでした")
                return False
            if not self.camera_start_line.isOpened():
                print(f"⚠️ スタートラインカメラ (ID: {self.camera_start_line_id}) を開けませんでした")
                return False
            
            self.camera_overview.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera_overview.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera_overview.set(cv2.CAP_PROP_FPS, 30)
            
            self.camera_start_line.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera_start_line.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera_start_line.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ カメラ初期化完了")
            return True
        except Exception as e:
            print(f"❌ カメラ初期化エラー: {e}")
            return False

    def start_race(self):
        if not self.race_active:
            self.race_active = True
            self.lap_count = 0
            self.current_lap_start = time.time()
            self.race_start_time = time.time()
            self.last_lap_time = 0.0
            self.best_lap_time = float('inf')
            self.total_time = 0.0
            self.detection_cooldown = 0
            self.last_detection_time = 0
            # オプティカルフロー初期化
            self.previous_gray = None
            self.feature_points = None
            print("🏁 レース開始 (v10 - Optical Flow)")

    def stop_race(self):
        if self.race_active:
            self.race_active = False
            self.previous_gray = None
            self.feature_points = None
            print("🏁 レース終了")

    def detect_motion_optical_flow(self, frame):
        """v10: オプティカルフローによる動き検出"""
        try:
            current_time = time.time()
            
            # クールダウン期間チェック
            if current_time - self.last_detection_time < 2.5:
                return False
            
            # グレースケール変換
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 初回フレームの場合
            if self.previous_gray is None:
                self.previous_gray = gray.copy()
                # 特徴点検出
                self.feature_points = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
                return False
            
            # 特徴点が少なくなったら再検出
            if self.feature_points is None or len(self.feature_points) < self.min_feature_points:
                self.feature_points = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
                if self.feature_points is None:
                    self.previous_gray = gray.copy()
                    return False
            
            # オプティカルフロー計算
            new_points, status, error = cv2.calcOpticalFlowPyrLK(
                self.previous_gray, gray, self.feature_points, None, **self.lk_params)
            
            # 有効な点のみを選択
            good_new = new_points[status == 1]
            good_old = self.feature_points[status == 1]
            
            if len(good_new) < self.min_feature_points:
                # 特徴点を再検出
                self.feature_points = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
                self.previous_gray = gray.copy()
                return False
            
            # 動きベクトルを計算
            motion_vectors = good_new - good_old
            motion_magnitudes = np.sqrt(motion_vectors[:, 0]**2 + motion_vectors[:, 1]**2)
            
            # ノイズフィルタリング（極端に大きな動きを除去）
            valid_motion = motion_magnitudes < self.max_flow_magnitude
            filtered_magnitudes = motion_magnitudes[valid_motion]
            
            if len(filtered_magnitudes) == 0:
                self.previous_gray = gray.copy()
                self.feature_points = good_new.reshape(-1, 1, 2)
                return False
            
            # 動き統計
            avg_motion = np.mean(filtered_magnitudes)
            moving_points = np.sum(filtered_magnitudes > self.motion_threshold)
            
            # 状態保存
            self.last_feature_count = len(good_new)
            self.last_moving_points = moving_points
            self.last_avg_motion = avg_motion
            
            # 動き検出判定
            motion_detected = (moving_points >= self.min_moving_points and 
                             avg_motion > self.motion_threshold)
            
            # 次フレーム用に更新
            self.previous_gray = gray.copy()
            self.feature_points = good_new.reshape(-1, 1, 2)
            
            if motion_detected:
                print(f"🔥 [v10 OPTICAL_FLOW] Motion detected!")
                print(f"   - Moving points: {moving_points}/{len(good_new)} (threshold: {self.min_moving_points})")
                print(f"   - Average motion: {avg_motion:.2f} (threshold: {self.motion_threshold})")
                print(f"   - Total features: {len(good_new)}")
                self.last_detection_time = current_time
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ オプティカルフロー検出エラー: {e}")
            return False

    def process_detection(self):
        """検出処理とラップ計測"""
        if self.race_active:
            current_time = time.time()
            if self.current_lap_start is not None:
                lap_time = current_time - self.current_lap_start
                self.lap_count += 1
                self.last_lap_time = lap_time
                
                if lap_time < self.best_lap_time:
                    self.best_lap_time = lap_time
                    print(f"🏆 新記録！ Lap {self.lap_count}: {lap_time:.3f}秒")
                else:
                    print(f"⏱️ Lap {self.lap_count}: {lap_time:.3f}秒")
                
                self.current_lap_start = current_time
                self.total_time = current_time - self.race_start_time

    def format_time(self, seconds):
        """時間フォーマット"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:06.3f}"

    def draw_camera_view(self, frame, x, y, width, height, title):
        """カメラ映像を描画（左右反転付き）"""
        if frame is not None:
            # 左右反転を適用
            frame_flipped = cv2.flip(frame, 1)
            
            frame_rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (width, height))
            frame_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
            
            # 背景パネル
            panel_rect = pygame.Rect(x-10, y-40, width+20, height+60)
            pygame.draw.rect(self.screen, self.colors['panel_bg'], panel_rect)
            pygame.draw.rect(self.screen, self.colors['border'], panel_rect, 2)
            
            # タイトル
            title_surface = self.font_small.render(title, True, self.colors['text_white'])
            title_rect = title_surface.get_rect(centerx=x + width//2, y=y-35)
            self.screen.blit(title_surface, title_rect)
            
            # カメラ映像
            self.screen.blit(frame_surface, (x, y))
            
            return frame_flipped
        else:
            # カメラなしの場合
            panel_rect = pygame.Rect(x-10, y-40, width+20, height+60)
            pygame.draw.rect(self.screen, (60, 60, 60), panel_rect)
            pygame.draw.rect(self.screen, self.colors['border'], panel_rect, 2)
            
            # タイトル
            title_surface = self.font_small.render(title, True, self.colors['text_white'])
            title_rect = title_surface.get_rect(centerx=x + width//2, y=y-35)
            self.screen.blit(title_surface, title_rect)
            
            # "カメラなし" メッセージ
            no_camera_surface = self.font_medium.render("カメラなし", True, self.colors['text_red'])
            no_camera_rect = no_camera_surface.get_rect(center=(x + width//2, y + height//2))
            self.screen.blit(no_camera_surface, no_camera_rect)
            
            return None

    def draw_status_info(self):
        """v10状態表示"""
        status_y = 650
        
        # v10検出方式表示
        method_text = f"v10 OPTICAL_FLOW - Lucas-Kanade特徴点追跡"
        method_surface = self.font_small.render(method_text, True, self.colors['text_green'])
        self.screen.blit(method_surface, (20, status_y))
        
        # 検出パラメータ表示
        params_text = f"motion_threshold: {self.motion_threshold}, min_moving_points: {self.min_moving_points}"
        params_surface = self.font_small.render(params_text, True, self.colors['text_yellow'])
        self.screen.blit(params_surface, (20, status_y + 25))
        
        # 最新検出状態
        if hasattr(self, 'last_feature_count'):
            detection_text = f"最新: features={self.last_feature_count}, moving={self.last_moving_points}, avg_motion={self.last_avg_motion:.2f}"
            detection_surface = self.font_small.render(detection_text, True, self.colors['text_white'])
            self.screen.blit(detection_surface, (450, status_y))

    def draw_lap_info(self):
        """ラップ情報表示"""
        info_x = 850
        info_y = 50
        
        # 背景パネル
        panel_rect = pygame.Rect(info_x-20, info_y-20, 400, 300)
        pygame.draw.rect(self.screen, self.colors['panel_bg'], panel_rect)
        pygame.draw.rect(self.screen, self.colors['border'], panel_rect, 3)
        
        # タイトル
        title = self.font_large.render("🏁 LAP INFO", True, self.colors['text_white'])
        self.screen.blit(title, (info_x, info_y))
        
        # レース状態
        status_color = self.colors['text_green'] if self.race_active else self.colors['text_red']
        status_text = "レース中" if self.race_active else "待機中"
        status = self.font_medium.render(f"状態: {status_text}", True, status_color)
        self.screen.blit(status, (info_x, info_y + 60))
        
        # ラップ数
        lap_text = self.font_medium.render(f"ラップ: {self.lap_count}", True, self.colors['text_white'])
        self.screen.blit(lap_text, (info_x, info_y + 100))
        
        # 最新ラップタイム
        if self.last_lap_time > 0:
            last_lap = self.font_medium.render(f"前回: {self.format_time(self.last_lap_time)}", True, self.colors['text_yellow'])
            self.screen.blit(last_lap, (info_x, info_y + 140))
        
        # ベストラップタイム
        if self.best_lap_time < float('inf'):
            best_lap = self.font_medium.render(f"最高: {self.format_time(self.best_lap_time)}", True, self.colors['text_green'])
            self.screen.blit(best_lap, (info_x, info_y + 180))
        
        # 総時間
        if self.race_active and self.race_start_time:
            total = time.time() - self.race_start_time
            total_time = self.font_medium.render(f"総時間: {self.format_time(total)}", True, self.colors['text_white'])
            self.screen.blit(total_time, (info_x, info_y + 220))

    def draw_controls(self):
        """操作方法表示"""
        controls_y = 550
        controls = [
            "S: レース開始",
            "Q: レース停止", 
            "ESC: 終了",
            "v10: オプティカルフロー版"
        ]
        
        for i, control in enumerate(controls):
            color = self.colors['text_green'] if i < 3 else self.colors['text_green']
            control_surface = self.font_small.render(control, True, color)
            self.screen.blit(control_surface, (20, controls_y + i * 25))

    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_s:
                    self.start_race()
                elif event.key == pygame.K_q:
                    self.stop_race()

    def run(self):
        """メインループ"""
        self.load_config()
        
        if not self.init_cameras():
            print("❌ カメラの初期化に失敗しました")
            return
        
        print("🚀 システム開始 - v10 オプティカルフロー版")
        print("📋 操作: S=開始, Q=停止, ESC=終了")
        
        try:
            while self.running:
                self.handle_events()
                
                # 画面クリア
                self.screen.fill(self.colors['background'])
                
                # カメラフレーム取得
                frame_ov = None
                frame_sl = None
                
                if self.camera_overview and self.camera_overview.isOpened():
                    ret, frame_ov = self.camera_overview.read()
                    if not ret:
                        frame_ov = None
                
                if self.camera_start_line and self.camera_start_line.isOpened():
                    ret, frame_sl = self.camera_start_line.read()
                    if not ret:
                        frame_sl = None
                
                # カメラ映像描画
                processed_ov = self.draw_camera_view(frame_ov, 30, 80, 400, 300, "📹 Overview Camera")
                processed_sl = self.draw_camera_view(frame_sl, 450, 80, 350, 260, "🏁 Start Line Camera")
                
                # 動き検出（スタートラインカメラで）
                if self.race_active and processed_sl is not None:
                    if self.detect_motion_optical_flow(processed_sl):
                        self.process_detection()
                
                # UI描画
                self.draw_lap_info()
                self.draw_controls()
                self.draw_status_info()
                
                # 画面更新
                pygame.display.flip()
                self.clock.tick(30)
                
        except KeyboardInterrupt:
            print("\n⏹️ システム停止")
        except Exception as e:
            print(f"❌ エラー: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """リソース解放"""
        if self.camera_overview:
            self.camera_overview.release()
        if self.camera_start_line:
            self.camera_start_line.release()
        cv2.destroyAllWindows()
        pygame.quit()

def main():
    system = TeamsSimpleLaptimeSystemFixedV10()
    system.run()

if __name__ == "__main__":
    main()