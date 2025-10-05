#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v8 - 3周計測対応版)
- 3周分の個別ラップタイム表示 (LAP1/LAP2/LAP3/TOTAL)
- ローリングスタートルール: Sキー押下後、スタートライン通過で計測開始
- 3周完了で自動停止・結果表示
- 救済システム: Rキーで5秒ペナルティ
- 極限感度設定: 高精度検出でわずかな動きも捕捉
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

class TeamsSimpleLaptimeSystemFixedV8:
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
<<<<<<< HEAD
        pygame.display.set_caption("Lap Timer")
=======
        pygame.display.set_caption("🏁 Lap Timer - Teams View (v8 - Extreme Sensitivity)")
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
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
<<<<<<< HEAD
        # 計測状態管理
        self.race_ready = False  # S押し後の計測準備状態
        self.race_active = False  # 実際の計測開始状態
        self.lap_count = 0
        self.current_lap_start = None
        self.race_start_time = None
        self.total_time = 0.0
=======
        self.race_active = False
        self.lap_count = 0
        self.current_lap_start = None
        self.last_lap_time = 0.0
        self.best_lap_time = float('inf')
        self.total_time = 0.0
        self.race_start_time = None
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
        self.clock = pygame.time.Clock()
        self.running = True
        self.detection_cooldown = 0
        self.last_detection_time = 0
        self.motion_detected_recently = False
        self.detection_threshold_time = 1.0
        
<<<<<<< HEAD
        # 3周計測用ラップタイム記録
        self.lap_times = [0.0, 0.0, 0.0]  # LAP1, LAP2, LAP3
        self.max_laps = 3  # 3周設定
        self.race_complete = False  # 3周完了フラグ
        
        # 救済システム
        self.rescue_mode = False  # 救済モードフラグ
        self.rescue_countdown = 0  # 5秒カウントダウン
        self.rescue_start_time = None  # 救済開始時刻
        self.total_penalty_time = 0.0  # 総ペナルティ時間
        self.rescue_paused_time = None  # 計測一時停止時の経過時間
        
        # v8: 極限感度設定 - わずかな動きでも検知
        self.motion_pixels_threshold = 15000  # v7: 300 → v8: 100 (極限まで減少)
        self.min_contour_area = 1000  # v7: 200 → v8: 50 (極小に設定)
        self.motion_area_ratio_min = 0.0001  # さらに小さく
        self.motion_area_ratio_max = 0.8
        self.pixel_diff_threshold = 15  # より敏感に
        self.detection_conditions_required = 6  # v7: 2 → v8: 1 (単一条件で検知)
=======
        # v8: 極限感度設定 - わずかな動きでも検知
        self.motion_pixels_threshold = 100  # v7: 300 → v8: 100 (極限まで減少)
        self.min_contour_area = 50  # v7: 200 → v8: 50 (極小に設定)
        self.motion_area_ratio_min = 0.0001  # さらに小さく
        self.motion_area_ratio_max = 0.8
        self.pixel_diff_threshold = 15  # より敏感に
        self.detection_conditions_required = 1  # v7: 2 → v8: 1 (単一条件で検知)
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
        
        self.last_motion_pixels = 0
        self.last_max_contour_area = 0
        self.last_motion_ratio = 0.0
        self.last_conditions_met = 0
        
        print(f"[v8 EXTREME] motion_pixels_threshold: {self.motion_pixels_threshold}")
        print(f"[v8 EXTREME] min_contour_area: {self.min_contour_area}")
        print(f"[v8 EXTREME] detection_conditions_required: {self.detection_conditions_required}")
        print("[v8 EXTREME] Single condition detection - ULTRA SENSITIVE")

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
<<<<<<< HEAD
        self.camera_start_line_id = 0  # 現在は1台のカメラのみ利用
=======
        self.camera_start_line_id = 0
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058

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
            
            # v8: 極限感度の背景差分設定
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
<<<<<<< HEAD
                history=10,  # v7: 300 → v8: 100 (短い履歴で敏感に)
=======
                history=100,  # v7: 300 → v8: 100 (短い履歴で敏感に)
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
                varThreshold=8,  # v7: 16 → v8: 8 (より低い閾値)
                detectShadows=False  # 影検出無効で純粋な動き検出
            )
            
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
<<<<<<< HEAD
            # 3周計測用ラップタイム初期化
            self.lap_times = [0.0, 0.0, 0.0]
            print("🏁 レース開始 - ローリングスタート準備 (v8)")
            print("📍 スタートラインを通過してから計測開始")

    def stop_race(self):
        """レース停止"""
        self.race_ready = False
        self.race_active = False
        self.race_complete = False
        self.rescue_mode = False
        self.rescue_countdown = 0
        print("⏹️ 計測停止")

    def start_rescue(self):
        """救済申請開始"""
        if self.race_active and not self.rescue_mode:
            self.rescue_mode = True
            self.rescue_countdown = 5.0
            self.rescue_start_time = time.time()
            
            # 現在のラップ時間を一時保存
            if self.current_lap_start:
                self.rescue_paused_time = time.time() - self.current_lap_start
            
            print("🆘 救済申請！5秒ペナルティ開始")
            print("⏳ 5秒間その場で待機してください")

    def update_rescue_countdown(self):
        """救済カウントダウン更新"""
        if self.rescue_mode and self.rescue_countdown > 0:
            current_time = time.time()
            elapsed = current_time - self.rescue_start_time
            remaining = 5.0 - elapsed
            
            if remaining <= 0:
                # 救済完了
                self.rescue_mode = False
                self.rescue_countdown = 0
                self.total_penalty_time += 5.0
                
                # 計測再開
                if self.current_lap_start and self.rescue_paused_time:
                    # ペナルティ時間を加算して計測再開
                    self.current_lap_start = time.time() - self.rescue_paused_time
                
                print("✅ 救済完了！計測再開")
                print(f"📊 総ペナルティ時間: {self.total_penalty_time:.1f}秒")
                self.rescue_paused_time = None
            else:
                self.rescue_countdown = remaining
=======
            print("🏁 レース開始 (v8 - Extreme Sensitivity)")

    def stop_race(self):
        if self.race_active:
            self.race_active = False
            print("🏁 レース終了")
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058

    def detect_motion_advanced(self, frame):
        """v8: 極限感度の動き検出 - 単一条件でも検知"""
        try:
            current_time = time.time()
            
            # クールダウン期間チェック (v8: 2.0秒に短縮)
<<<<<<< HEAD
            if current_time - self.last_detection_time < 5.0:
=======
            if current_time - self.last_detection_time < 2.0:
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
                return False
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fg_mask = self.bg_subtractor.apply(gray)
            
            # v8: 最小限のノイズ除去
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))  # v7: (3,3) → v8: (2,2)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
            
            motion_pixels = cv2.countNonZero(fg_mask)
            frame_area = frame.shape[0] * frame.shape[1]
            motion_ratio = motion_pixels / frame_area
            
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # v8: 極限感度条件チェック
            conditions_met = 0
            
            # 条件1: 動きピクセル数（極小閾値）
            if motion_pixels > self.motion_pixels_threshold:  # 100
                conditions_met += 1
            
            # 条件2: 最大輪郭面積（極小閾値）
            max_contour_area = 0
            if contours:
                max_contour_area = max(cv2.contourArea(c) for c in contours)
                if max_contour_area > self.min_contour_area:  # 50
                    conditions_met += 1
            
            # 条件3: 動き面積比（極小閾値）
            if self.motion_area_ratio_min < motion_ratio < self.motion_area_ratio_max:
                conditions_met += 1
            
            # 条件4: 輪郭数（v8: 1個以上で検知）
            if len(contours) >= 1:
                conditions_met += 1
            
            # 条件5: 平均輪郭面積（v8: 25以上で検知）
            if contours:
                avg_contour_area = sum(cv2.contourArea(c) for c in contours) / len(contours)
                if avg_contour_area > 25:
                    conditions_met += 1
            
            # 条件6: 動きピクセル密度（v8: 0.05%以上で検知）
            motion_density = motion_pixels / max(1, len(contours)) if contours else 0
            if motion_density > 50:  # 極小値
                conditions_met += 1
            
            # 状態保存
            self.last_motion_pixels = motion_pixels
            self.last_max_contour_area = max_contour_area
            self.last_motion_ratio = motion_ratio
            self.last_conditions_met = conditions_met
            
            # v8: 単一条件でも検知
            motion_detected = conditions_met >= self.detection_conditions_required  # 1
            
            if motion_detected:
                print(f"🔥 [v8 EXTREME] Motion detected! Conditions: {conditions_met}/6")
                print(f"   - Motion pixels: {motion_pixels} (threshold: {self.motion_pixels_threshold})")
                print(f"   - Max contour: {max_contour_area} (threshold: {self.min_contour_area})")
                print(f"   - Motion ratio: {motion_ratio:.4f}")
                self.last_detection_time = current_time
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 動き検出エラー: {e}")
            return False

<<<<<<< HEAD
    def prepare_race(self):
        """計測準備状態へ移行（Sキー押下時）"""
        self.race_ready = True
        self.race_active = False
        self.lap_count = 0
        self.current_lap_start = None
        self.race_start_time = None
        self.total_time = 0.0
        self.lap_times = [0.0, 0.0, 0.0]
        self.race_complete = False
        print("🛠️ 計測準備完了！ローリングスタートでスタートラインを通過してください")
        print("🏁 スタートライン通過で計測開始します")

    def start_race(self):
        """レース開始（スタートライン通過時）"""
        if self.race_ready and not self.race_active:
            self.race_active = True
            self.race_start_time = time.time()
            self.current_lap_start = self.race_start_time
            print("🏁 計測開始！LAP1 スタート")

    def process_detection(self):
        """検出処理とラップ計測"""
        current_time = time.time()
        
        # 救済モード中は検出処理をスキップ
        if self.rescue_mode:
            return
        
        # 計測準備中にスタートライン通過で計測開始
        if self.race_ready and not self.race_active:
            self.start_race()
            return
        
        # レース中のラップ計測
        if self.race_active and not self.race_complete:
            if self.current_lap_start is not None:
                lap_time = current_time - self.current_lap_start
                self.lap_count += 1
                
                # 3周までのラップタイムを記録
                if self.lap_count <= 3:
                    self.lap_times[self.lap_count - 1] = lap_time
                    print(f"⏱️ LAP{self.lap_count}: {self.format_time(lap_time)}")
                
                # 3周完了チェック
                if self.lap_count >= 3:
                    self.total_time = current_time - self.race_start_time
                    self.race_complete = True
                    print(f"🏁 3周完了！ 総時間: {self.format_time(self.total_time)}")
                    print("=== 最終結果 ===")
                    for i in range(3):
                        print(f"LAP{i+1}: {self.format_time(self.lap_times[i])}")
                    print(f"TOTAL: {self.format_time(self.total_time)}")
                    if self.total_penalty_time > 0:
                        final_time = self.total_time + self.total_penalty_time
                        print(f"ペナルティ: +{self.total_penalty_time:.1f}秒")
                        print(f"最終時間: {self.format_time(final_time)}")
                    return
                
                # 次のラップの開始時刻を設定
                self.current_lap_start = current_time

    def format_time(self, seconds):
        """時間フォーマット - MM:SS.sss形式"""
=======
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
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
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
        """v8感度状態表示"""
        status_y = 650
        
        # v8感度レベル表示
        sensitivity_text = f"v8 EXTREME - 極限感度 (1/6条件で検知)"
        sensitivity_surface = self.font_small.render(sensitivity_text, True, self.colors['text_red'])
        self.screen.blit(sensitivity_surface, (20, status_y))
        
        # 検出パラメータ表示
        params_text = f"motion_pixels: {self.motion_pixels_threshold}, contour_area: {self.min_contour_area}"
        params_surface = self.font_small.render(params_text, True, self.colors['text_yellow'])
        self.screen.blit(params_surface, (20, status_y + 25))
        
        # 最新検出状態
        if hasattr(self, 'last_motion_pixels'):
            detection_text = f"最新: pixels={self.last_motion_pixels}, contour={self.last_max_contour_area}, 条件={self.last_conditions_met}/6"
            detection_surface = self.font_small.render(detection_text, True, self.colors['text_white'])
            self.screen.blit(detection_surface, (450, status_y))

    def draw_lap_info(self):
        """ラップ情報表示"""
        info_x = 850
        info_y = 50
        
<<<<<<< HEAD
        # 背景パネル（縦長に拡張）
        panel_rect = pygame.Rect(info_x-20, info_y-20, 400, 350)
=======
        # 背景パネル
        panel_rect = pygame.Rect(info_x-20, info_y-20, 400, 300)
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
        pygame.draw.rect(self.screen, self.colors['panel_bg'], panel_rect)
        pygame.draw.rect(self.screen, self.colors['border'], panel_rect, 3)
        
        # タイトル
<<<<<<< HEAD
        title = self.font_large.render("LAP INFO", True, self.colors['text_white'])
        self.screen.blit(title, (info_x, info_y))
        
        # レース状態
        if self.rescue_mode:
            status_text = f"救済中 ({self.rescue_countdown:.1f}秒)"
            status_color = self.colors['text_red']
        elif self.race_ready and not self.race_active:
            status_text = "計測準備完了"
            status_color = self.colors['text_yellow']
        elif self.race_active:
            status_text = "レース中"
            status_color = self.colors['text_green']
        elif self.race_complete:
            status_text = "完了"
            status_color = self.colors['text_yellow']
        else:
            status_text = "待機中 (Sキーで準備)"
            status_color = self.colors['text_red']
        
        status = self.font_medium.render(f"状態: {status_text}", True, status_color)
        self.screen.blit(status, (info_x, info_y + 60))
        
        # 3周分のラップタイム表示
        y_offset = 100
        for i in range(3):
            if self.lap_times[i] > 0:  # 記録済み
                lap_text = f"LAP{i+1}: {self.format_time(self.lap_times[i])}"
                color = self.colors['text_green']
            else:  # 未記録
                lap_text = f"LAP{i+1}: 00:00.000"
                color = self.colors['text_white']
            
            lap_surface = self.font_medium.render(lap_text, True, color)
            self.screen.blit(lap_surface, (info_x, info_y + y_offset + i * 40))
        
        # 総時間表示
        if self.race_active and self.race_start_time:
            total = time.time() - self.race_start_time
            total_text = f"TOTAL: {self.format_time(total)}"
        elif self.total_time > 0:  # レース完了後
            total_text = f"TOTAL: {self.format_time(self.total_time)}"
        else:
            total_text = "TOTAL: 00:00.000"
        
        total_color = self.colors['text_yellow'] if self.lap_count >= 3 else self.colors['text_white']
        total_surface = self.font_medium.render(total_text, True, total_color)
        self.screen.blit(total_surface, (info_x, info_y + y_offset + 120))
        
        # ペナルティ時間表示
        if self.total_penalty_time > 0:
            penalty_text = f"ペナルティ: +{self.total_penalty_time:.1f}秒"
            penalty_surface = self.font_small.render(penalty_text, True, self.colors['text_red'])
            self.screen.blit(penalty_surface, (info_x, info_y + y_offset + 160))
=======
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
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058

    def draw_controls(self):
        """操作方法表示"""
        controls_y = 550
        controls = [
<<<<<<< HEAD
            "S: 計測準備（ローリングスタート）",
            "R: 救済申請（5秒ペナルティ）",
            "Q: レース停止", 
            "ESC: 終了",
            "📍 スタートライン通過で計測開始",
            "� 自走不能時はRキーで救済",
            "v8: 高感度版"
        ]
        
        for i, control in enumerate(controls):
            if i < 3:
                color = self.colors['text_green']
            elif i < 5:
                color = self.colors['text_yellow']
            else:
                color = self.colors['text_red']
=======
            "S: レース開始",
            "Q: レース停止", 
            "ESC: 終了",
            "v8: 極限感度版"
        ]
        
        for i, control in enumerate(controls):
            color = self.colors['text_green'] if i < 3 else self.colors['text_red']
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
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
<<<<<<< HEAD
                    if not self.race_ready and not self.race_active:
                        self.prepare_race()
                elif event.key == pygame.K_r:
                    if self.race_active and not self.rescue_mode:
                        self.start_rescue()
=======
                    self.start_race()
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
                elif event.key == pygame.K_q:
                    self.stop_race()

    def run(self):
        """メインループ"""
        self.load_config()
        
        if not self.init_cameras():
            print("❌ カメラの初期化に失敗しました")
            return
        
        print("🚀 システム開始 - v8 極限感度版")
<<<<<<< HEAD
        print("📋 操作: S=計測準備, R=救済申請, Q=停止, ESC=終了")
        print("📋 ローリングスタート: S押下後、スタートライン通過で計測開始")
        print("🆘 自走不能時: Rキーで救済申請（5秒ペナルティ）")
=======
        print("📋 操作: S=開始, Q=停止, ESC=終了")
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
        
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
                
<<<<<<< HEAD
                # カメラ映像描画（同サイズで統一）
                processed_ov = self.draw_camera_view(frame_ov, 30, 80, 375, 280, "Overview Camera")
                processed_sl = self.draw_camera_view(frame_sl, 430, 80, 375, 280, "Start Line Camera")
                
                # 救済カウントダウン更新
                if self.rescue_mode:
                    self.update_rescue_countdown()
=======
                # カメラ映像描画
                processed_ov = self.draw_camera_view(frame_ov, 30, 80, 400, 300, "📹 Overview Camera")
                processed_sl = self.draw_camera_view(frame_sl, 450, 80, 350, 260, "🏁 Start Line Camera")
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
                
                # 動き検出（スタートラインカメラで）
                if self.race_active and processed_sl is not None and self.bg_subtractor is not None:
                    if self.detect_motion_advanced(processed_sl):
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
    system = TeamsSimpleLaptimeSystemFixedV8()
    system.run()

if __name__ == "__main__":
    main()