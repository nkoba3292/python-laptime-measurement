#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v8 - 3周計測対応版)
- v7ベース：3周分の個別ラップタイム表示 (LAP1/LAP2/LAP3/TOTAL)
- ローリングスタートルール: Sキー押下後、スタートライン通過で計測開始
- 3周完了で自動停止・結果表示
- 救済システム: Rキーで5秒ペナルティ
- v7の高感度設定を継承
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
        pygame.display.set_caption("🏁 Lap Timer v8 - 3周計測システム")
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
        
        # v8: 3周計測システム状態管理
        self.race_ready = False  # S押し後の計測準備状態
        self.race_active = False  # 実際の計測開始状態
        self.lap_count = 0
        self.current_lap_start = None
        self.race_start_time = None
        self.total_time = 0.0
        
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
        
        # v7継承: 検出関連
        self.last_detection_time = 0
        self.detection_cooldown = 2.5
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
        
        print(f"[v8 3-LAP SYSTEM] 初期化完了")
        print(f"[v8] LAP1/LAP2/LAP3の3周計測システム")
        print(f"[v8] ローリングスタート対応（Sキー準備→通過開始）")
        print(f"[v8] 救済システム（Rキーで5秒ペナルティ）")

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # v7継承: 高感度設定
            self.config = {
                "camera_settings": {
                    "overview_camera_index": 0,
                    "startline_camera_index": 0,  # 修正: 同じカメラを使用
                    "frame_width": 640,
                    "frame_height": 480
                },
                "detection_settings": {
                    "motion_pixels_threshold": 300,      # v7高感度設定継承
                    "min_contour_area": 200,
                    "motion_area_ratio_min": 0.008,
                    "motion_area_ratio_max": 0.9,
                    "stable_frames_required": 2,
                    "motion_consistency_check": False
                },
                "race_settings": {
                    "max_laps": 3,  # v8: 3周固定
                    "detection_cooldown": 2.5
                }
            }
            print("⚠️ config.json not found, using v8 3-lap system with v7 sensitivity settings")
        
        # 設定値を変数に展開
        camera_settings = self.config["camera_settings"]
        detection_settings = self.config["detection_settings"]
        race_settings = self.config["race_settings"]
        
        self.overview_camera_index = camera_settings["overview_camera_index"]
        self.startline_camera_index = camera_settings["startline_camera_index"]
        self.frame_width = camera_settings["frame_width"]
        self.frame_height = camera_settings["frame_height"]
        
        self.motion_pixels_threshold = detection_settings["motion_pixels_threshold"]
        self.min_contour_area = detection_settings["min_contour_area"]
        self.motion_area_ratio_min = detection_settings["motion_area_ratio_min"]
        self.motion_area_ratio_max = detection_settings["motion_area_ratio_max"]
        self.stable_frames_required = detection_settings["stable_frames_required"]
        self.motion_consistency_check = detection_settings["motion_consistency_check"]
        
        self.max_laps = 3  # v8: 強制的に3周
        self.detection_cooldown = race_settings["detection_cooldown"]

    def init_cameras(self):
        """カメラ初期化（ラズパイ対応・カメラなしモード対応）"""
        try:
            print("📷 カメラを初期化中...")
            
            # カメラ0を試行
            self.camera_overview = cv2.VideoCapture(self.overview_camera_index)
            self.camera_start_line = cv2.VideoCapture(self.startline_camera_index)
            
            camera_available = False
            
            if self.camera_overview.isOpened():
                print(f"✅ Overview camera (index {self.overview_camera_index}) opened successfully")
                camera_available = True
                # カメラ設定
                self.camera_overview.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.camera_overview.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            else:
                print(f"⚠️ Overview camera (index {self.overview_camera_index}) could not be opened")
                self.camera_overview = None
            
            if self.camera_start_line.isOpened():
                print(f"✅ Start line camera (index {self.startline_camera_index}) opened successfully")
                camera_available = True
                # カメラ設定
                self.camera_start_line.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.camera_start_line.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            else:
                print(f"⚠️ Start line camera (index {self.startline_camera_index}) could not be opened")
                self.camera_start_line = None
            
            # 背景差分初期化
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=500, varThreshold=16, detectShadows=True
            )
            
            if camera_available:
                print("✅ カメラ初期化完了（一部カメラ利用可能）")
            else:
                print("⚠️ カメラなしモードで起動（デモモード）")
                print("🎮 キーボードでテスト: Spaceキーで手動検出シミュレーション")
            
            return True  # カメラなしでも続行
            
        except Exception as e:
            print(f"⚠️ カメラ初期化警告: {e}")
            print("📺 カメラなしモードで続行します")
            self.camera_overview = None
            self.camera_start_line = None
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=500, varThreshold=16, detectShadows=True
            )
            return True  # カメラなしでも続行

    def prepare_race(self):
        """v8: 計測準備状態へ移行（Sキー押下時）"""
        self.race_ready = True
        self.race_active = False
        self.lap_count = 0
        self.current_lap_start = None
        self.race_start_time = None
        self.total_time = 0.0
        self.lap_times = [0.0, 0.0, 0.0]
        self.race_complete = False
        self.rescue_mode = False
        self.rescue_countdown = 0
        self.total_penalty_time = 0.0
        print("🛠️ 計測準備完了！ローリングスタートでスタートラインを通過してください")
        print("🏁 スタートライン通過で計測開始します")

    def start_race(self):
        """v8: レース開始（スタートライン通過時）"""
        if self.race_ready and not self.race_active:
            self.race_active = True
            self.race_start_time = time.time()
            self.current_lap_start = self.race_start_time
            self.last_detection_time = self.race_start_time  # 初回検出時間をリセット
            print("🏁 計測開始！LAP1 スタート")

    def stop_race(self):
        """v8: レース停止"""
        self.race_ready = False
        self.race_active = False
        self.race_complete = False
        self.rescue_mode = False
        self.rescue_countdown = 0
        print("⏹️ 計測停止")

    def start_rescue(self):
        """v8: 救済申請開始"""
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
        """v8: 救済カウントダウン更新"""
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

    def detect_motion_v7(self, frame):
        """v7継承: 高感度動き検出"""
        try:
            current_time = time.time()
            
            # クールダウン期間チェック
            if current_time - self.last_detection_time < self.detection_cooldown:
                return False
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fg_mask = self.bg_subtractor.apply(gray)
            
            # ノイズ除去
            kernel = np.ones((3,3), np.uint8)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            
            # 輪郭検出
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # v7高感度検出条件
            motion_pixels = cv2.countNonZero(fg_mask)
            max_contour_area = max([cv2.contourArea(c) for c in contours]) if contours else 0
            
            frame_area = gray.shape[0] * gray.shape[1]
            motion_ratio = motion_pixels / frame_area
            
            conditions_met = 0
            
            # 検出条件チェック
            if motion_pixels > self.motion_pixels_threshold:
                conditions_met += 1
            if max_contour_area > self.min_contour_area:
                conditions_met += 1
            if self.motion_area_ratio_min <= motion_ratio <= self.motion_area_ratio_max:
                conditions_met += 1
            if len(contours) >= 1:
                conditions_met += 1
            
            # v7: 2/4条件以上で検知（高感度）
            motion_detected = conditions_met >= 2
            
            # デバッグ情報更新
            self.last_motion_pixels = motion_pixels
            self.motion_area_ratio = motion_ratio
            
            if motion_detected:
                print(f"🔥 [v8/v7] Motion detected! Conditions: {conditions_met}/4")
                print(f"   - Motion pixels: {motion_pixels} (threshold: {self.motion_pixels_threshold})")
                print(f"   - Max contour: {max_contour_area} (threshold: {self.min_contour_area})")
                print(f"   - Motion ratio: {motion_ratio:.4f}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 動き検出エラー: {e}")
            return False

    def process_detection(self):
        """v8: 検出処理とラップ計測"""
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
                
                # 検出時間を更新
                self.last_detection_time = current_time

    def format_time(self, seconds):
        """時間フォーマット - MM:SS.sss形式"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:06.3f}"

    def draw_camera_view(self, frame, x, y, width, height, title):
        """カメラ映像を描画"""
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
            # カメラが利用できない場合
            panel_rect = pygame.Rect(x-10, y-40, width+20, height+60)
            pygame.draw.rect(self.screen, self.colors['panel_bg'], panel_rect)
            pygame.draw.rect(self.screen, self.colors['border'], panel_rect, 2)
            
            title_surface = self.font_small.render(title, True, self.colors['text_white'])
            title_rect = title_surface.get_rect(centerx=x + width//2, y=y-35)
            self.screen.blit(title_surface, title_rect)
            
            no_camera_text = self.font_medium.render("Camera N/A", True, self.colors['text_red'])
            text_rect = no_camera_text.get_rect(center=(x + width//2, y + height//2))
            self.screen.blit(no_camera_text, text_rect)
            
            return None

    def draw_lap_info(self):
        """v8: ラップ情報表示"""
        info_x = 850
        info_y = 50
        
        # 背景パネル（縦長に拡張）
        panel_rect = pygame.Rect(info_x-20, info_y-20, 400, 350)
        pygame.draw.rect(self.screen, self.colors['panel_bg'], panel_rect)
        pygame.draw.rect(self.screen, self.colors['border'], panel_rect, 3)
        
        # タイトル
        title = self.font_large.render("3-LAP INFO", True, self.colors['text_white'])
        self.screen.blit(title, (info_x, info_y))
        
        # レース状態
        if self.rescue_mode:
            status_text = f"Rescue ({self.rescue_countdown:.1f}s)"
            status_color = self.colors['text_red']
        elif self.race_ready and not self.race_active:
            status_text = "Ready"
            status_color = self.colors['text_yellow']
        elif self.race_active:
            status_text = "Racing"
            status_color = self.colors['text_green']
        elif self.race_complete:
            status_text = "Complete"
            status_color = self.colors['text_yellow']
        else:
            status_text = "Standby (S=Prepare)"
            status_color = self.colors['text_red']
        
        status = self.font_medium.render(f"Status: {status_text}", True, status_color)
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
            penalty_text = f"Penalty: +{self.total_penalty_time:.1f}s"
            penalty_surface = self.font_small.render(penalty_text, True, self.colors['text_red'])
            self.screen.blit(penalty_surface, (info_x, info_y + y_offset + 160))

    def draw_controls(self):
        """操作方法表示"""
        controls_y = 550
        controls = [
            "S: Race Prepare (Rolling Start)",
            "R: Rescue Request (5s Penalty)",
            "Q: Race Stop", 
            "ESC: Exit",
            "SPACE: Manual Detection (No Camera Mode)",
            "Start Line Pass = Start Race",
            "3 Laps = Auto Complete",
            "v8: 3-Lap System (v7 base)"
        ]
        
        for i, control in enumerate(controls):
            if i < 3:
                color = self.colors['text_green']
            elif i < 6:
                color = self.colors['text_yellow']
            else:
                color = self.colors['text_red']
            control_surface = self.font_small.render(control, True, color)
            self.screen.blit(control_surface, (20, controls_y + i * 25))

    def draw_status_info(self):
        """システム状態表示"""
        status_y = 400
        
        # レース状態
        if self.race_active:
            status_text = f"Racing (LAP{self.lap_count + 1})"
            status_color = self.colors['text_green']
        elif self.race_ready:
            status_text = "Ready for Start"
            status_color = self.colors['text_yellow']
        else:
            status_text = "Standby"
            status_color = self.colors['text_red']
        
        status_surface = self.font_medium.render(f"System: {status_text}", True, status_color)
        self.screen.blit(status_surface, (450, status_y))
        
        # 最新検出状態
        detection_text = f"Motion: pixels={self.last_motion_pixels}, ratio={self.motion_area_ratio:.4f}"
        detection_surface = self.font_small.render(detection_text, True, self.colors['text_white'])
        self.screen.blit(detection_surface, (450, status_y + 40))

    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_s:
                    if not self.race_ready and not self.race_active:
                        self.prepare_race()
                elif event.key == pygame.K_r:
                    if self.race_active and not self.rescue_mode:
                        self.start_rescue()
                elif event.key == pygame.K_q:
                    self.stop_race()
                elif event.key == pygame.K_SPACE:
                    # カメラなしモード用：手動検出シミュレーション
                    if (self.race_ready or self.race_active) and not self.rescue_mode:
                        if self.camera_overview is None and self.camera_start_line is None:
                            print("🎮 手動検出シミュレーション実行")
                            self.process_detection()

    def run(self):
        """メインループ"""
        if not self.init_cameras():
            print("❌ カメラの初期化に失敗しました")
            return
        
        print("🚀 v8 3周計測システム開始")
        print("📋 操作: S=計測準備, R=救済申請, Q=停止, ESC=終了")
        print("📋 ローリングスタート: S押下後、スタートライン通過で計測開始")
        print("🆘 自走不能時: Rキーで救済申請（5秒ペナルティ）")
        print("🏁 3周完了で自動停止")
        if self.camera_overview is None and self.camera_start_line is None:
            print("🎮 カメラなしモード: Spaceキーで手動検出テスト")
        
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
                
                # カメラ映像描画（375x280で統一）
                processed_ov = self.draw_camera_view(frame_ov, 30, 80, 375, 280, "Overview Camera")
                processed_sl = self.draw_camera_view(frame_sl, 430, 80, 375, 280, "Start Line Camera")
                
                # 救済カウントダウン更新
                if self.rescue_mode:
                    self.update_rescue_countdown()
                
                # 動き検出（スタートラインカメラで、またはカメラなしモードではスキップ）
                if processed_sl is not None and self.bg_subtractor is not None:
                    # 計測準備中または実行中のみ検出
                    if (self.race_ready or self.race_active) and not self.rescue_mode:
                        if self.detect_motion_v7(processed_sl):
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