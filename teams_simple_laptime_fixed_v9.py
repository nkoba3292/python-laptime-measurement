#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v9 - フレーム差分版)
- 背景差分ではなくフレーム間差分による動き検出
- 前フレームとの直接比較でリアルタイム性向上
- シンプルな差分検出で高速且つ敏感な反応
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

class TeamsSimpleLaptimeSystemFixedV9:
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🏁 Lap Timer - Teams View (v9 - Frame Difference)")
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
        self.previous_frame = None  # v9: 前フレーム保存用
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
        
        # v9: フレーム差分設定
        self.frame_diff_threshold = 30  # フレーム差分の閾値
        self.motion_pixels_threshold = 200  # 変化ピクセル数の閾値
        self.min_contour_area = 100  # 最小輪郭面積
        self.blur_kernel_size = 5  # ガウシアンブラーのカーネルサイズ
        
        self.last_motion_pixels = 0
        self.last_max_contour_area = 0
        self.last_motion_ratio = 0.0
        
        print(f"[v9 FRAME_DIFF] frame_diff_threshold: {self.frame_diff_threshold}")
        print(f"[v9 FRAME_DIFF] motion_pixels_threshold: {self.motion_pixels_threshold}")
        print(f"[v9 FRAME_DIFF] min_contour_area: {self.min_contour_area}")
        print("[v9 FRAME_DIFF] Frame difference detection - HIGH SPEED")

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
            self.previous_frame = None  # フレーム履歴リセット
            print("🏁 レース開始 (v9 - Frame Difference)")

    def stop_race(self):
        if self.race_active:
            self.race_active = False
            self.previous_frame = None
            print("🏁 レース終了")

    def detect_motion_frame_diff(self, frame):
        """v9: フレーム差分による動き検出"""
        try:
            current_time = time.time()
            
            # クールダウン期間チェック
            if current_time - self.last_detection_time < 2.5:
                return False
            
            # グレースケール変換
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # ガウシアンブラーでノイズ除去
            gray = cv2.GaussianBlur(gray, (self.blur_kernel_size, self.blur_kernel_size), 0)
            
            # 初回フレームの場合は保存して終了
            if self.previous_frame is None:
                self.previous_frame = gray.copy()
                return False
            
            # フレーム差分計算
            frame_diff = cv2.absdiff(self.previous_frame, gray)
            
            # 閾値処理
            _, thresh = cv2.threshold(frame_diff, self.frame_diff_threshold, 255, cv2.THRESH_BINARY)
            
            # ノイズ除去
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # 動きピクセル数をカウント
            motion_pixels = cv2.countNonZero(thresh)
            frame_area = frame.shape[0] * frame.shape[1]
            motion_ratio = motion_pixels / frame_area
            
            # 輪郭検出
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 検出条件チェック
            motion_detected = False
            max_contour_area = 0
            
            if contours:
                max_contour_area = max(cv2.contourArea(c) for c in contours)
            
            # v9: フレーム差分の検出条件
            if (motion_pixels > self.motion_pixels_threshold and 
                max_contour_area > self.min_contour_area and 
                len(contours) >= 3):
                motion_detected = True
            
            # 状態保存
            self.last_motion_pixels = motion_pixels
            self.last_max_contour_area = max_contour_area
            self.last_motion_ratio = motion_ratio
            
            # 前フレーム更新
            self.previous_frame = gray.copy()
            
            if motion_detected:
                print(f"🔥 [v9 FRAME_DIFF] Motion detected!")
                print(f"   - Motion pixels: {motion_pixels} (threshold: {self.motion_pixels_threshold})")
                print(f"   - Max contour: {max_contour_area} (threshold: {self.min_contour_area})")
                print(f"   - Contours: {len(contours)}")
                print(f"   - Motion ratio: {motion_ratio:.4f}")
                self.last_detection_time = current_time
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ フレーム差分検出エラー: {e}")
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
        """v9状態表示"""
        status_y = 650
        
        # v9検出方式表示
        method_text = f"v9 FRAME_DIFF - フレーム差分検出"
        method_surface = self.font_small.render(method_text, True, self.colors['text_green'])
        self.screen.blit(method_surface, (20, status_y))
        
        # 検出パラメータ表示
        params_text = f"diff_threshold: {self.frame_diff_threshold}, motion_pixels: {self.motion_pixels_threshold}"
        params_surface = self.font_small.render(params_text, True, self.colors['text_yellow'])
        self.screen.blit(params_surface, (20, status_y + 25))
        
        # 最新検出状態
        if hasattr(self, 'last_motion_pixels'):
            detection_text = f"最新: pixels={self.last_motion_pixels}, contour={self.last_max_contour_area}, ratio={self.last_motion_ratio:.4f}"
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
            "v9: フレーム差分版"
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
        
        print("🚀 システム開始 - v9 フレーム差分版")
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
                    if self.detect_motion_frame_diff(processed_sl):
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
    system = TeamsSimpleLaptimeSystemFixedV9()
    system.run()

if __name__ == "__main__":
    main()