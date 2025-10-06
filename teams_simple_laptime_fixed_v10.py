#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v10 - 背景学習最適化版)
- v8ベース：5秒間の背景学習期間＋検出分離機能
- 3周分の個別ラップタイム表示 (LAP1/LAP2/LAP3/TOTAL)
- ローリングスタートルール: Sキー押下後、スタートライン通過で計測開始
- 3周完了で自動停止・結果表示
- 救済システム: Rキーで5秒ペナルティ
- v10改良点: 背景学習期間延長（5秒）、検出完全分離、MOG2パラメータ最適化
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
pygame.font.init()  # フォント初期化を明示的に実行

class TeamsSimpleLaptimeSystemFixedV10:
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🏁 Lap Timer v10 - 背景学習最適化版")
        self.colors = {
            'background': (15, 15, 25),
            'text_white': (255, 255, 255),
            'text_green': (0, 255, 100),
            'text_yellow': (255, 255, 50),
            'text_red': (255, 80, 80),
            'panel_bg': (40, 40, 60),
            'border': (80, 80, 100)
        }
        
        # フォント初期化を確実に実行
        pygame.font.init()
        
        try:
            self.font_huge = pygame.font.Font(None, 120)
            self.font_large = pygame.font.Font(None, 80)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
        except:
            try:
                self.font_huge = pygame.font.SysFont('arial', 120, bold=True)
                self.font_large = pygame.font.SysFont('arial', 80, bold=True)
                self.font_medium = pygame.font.SysFont('arial', 48)
                self.font_small = pygame.font.SysFont('arial', 32)
            except:
                # 最終手段：デフォルトフォント
                self.font_huge = pygame.font.Font(pygame.font.get_default_font(), 120)
                self.font_large = pygame.font.Font(pygame.font.get_default_font(), 80)
                self.font_medium = pygame.font.Font(pygame.font.get_default_font(), 48)
                self.font_small = pygame.font.Font(pygame.font.get_default_font(), 32)
        
        self.camera_overview = None
        self.camera_start_line = None
        self.bg_subtractor = None
        
        # v8: 3周計測システム状態管理
        self.race_ready = False  # S押し後の計測準備状態
        self.race_active = False  # 実際の計測開始状態
        self.lap_count = 0  # 完了したラップ数
        self.current_lap_number = 0  # 現在計測中のラップ番号
        self.current_lap_start = None
        self.race_start_time = None
        self.total_time = 0.0
        self.current_lap_time = 0.0  # 現在のラップの進行時間
        
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
        self.preparation_start_time = None  # 準備開始時刻
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
                    "detection_cooldown": 5.0  # 誤検出防止のため延長
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
        """カメラ初期化（ラズパイ対応・カメラなしモード対応・自動検出）"""
        try:
            print("📷 カメラを初期化中...")
            
            # 利用可能なカメラインデックスを自動検出
            available_cameras = []
            for i in range(4):  # 0-3まで試行
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available_cameras.append(i)
                    print(f"🔍 カメラインデックス {i} が利用可能")
                cap.release()
            
            if not available_cameras:
                print("⚠️ 利用可能なカメラが見つかりません")
                self.camera_overview = None
                self.camera_start_line = None
            elif len(available_cameras) == 1:
                # 1台のカメラのみ：両方の用途で共用
                index = available_cameras[0]
                print(f"📷 1台のカメラ（インデックス {index}）を両方の用途で使用")
                self.camera_overview = cv2.VideoCapture(index)
                self.camera_start_line = None  # 同じカメラは共用せず、1つだけ使用
            else:
                # 2台以上のカメラ：それぞれに割り当て
                print(f"📷 {len(available_cameras)}台のカメラを検出：{available_cameras}")
                self.camera_overview = cv2.VideoCapture(available_cameras[0])
                self.camera_start_line = cv2.VideoCapture(available_cameras[1])
            
            camera_available = False
            
            if self.camera_overview and self.camera_overview.isOpened():
                print(f"✅ Overview camera (index {available_cameras[0] if available_cameras else 'N/A'}) opened successfully")
                camera_available = True
                # カメラ設定
                self.camera_overview.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.camera_overview.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            else:
                print(f"⚠️ Overview camera could not be opened")
                self.camera_overview = None
            
            if self.camera_start_line and self.camera_start_line.isOpened():
                print(f"✅ Start line camera (index {available_cameras[1] if len(available_cameras) > 1 else 'N/A'}) opened successfully")
                camera_available = True
                # カメラ設定
                self.camera_start_line.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.camera_start_line.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            else:
                print(f"⚠️ Start line camera could not be opened")
                self.camera_start_line = None
            
            # 背景差分初期化（より安定した設定）
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
        """計測準備状態へ移行（Sキー押下時）"""
        self.race_ready = True
        self.race_active = False
        self.lap_count = 0
        self.current_lap_number = 0
        self.current_lap_start = None
        self.race_start_time = None
        self.total_time = 0.0
        self.current_lap_time = 0.0
        self.lap_times = [0.0, 0.0, 0.0]
        self.race_complete = False
        self.rescue_mode = False
        self.rescue_countdown = 0
        self.total_penalty_time = 0.0
        
        # 重要：クールダウンタイマーをリセットして、背景学習時間を確保
        self.last_detection_time = time.time()
        self.preparation_start_time = time.time()  # 準備開始時刻を記録
        self._learning_completed = False  # 学習完了フラグをリセット
        
        # 背景減算器を新しく初期化（前回の学習をクリア）
        print("🔄 背景減算器を新規初期化中...")
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=1000,        # より長い履歴で安定した学習
            varThreshold=25,     # より高い闾値でノイズ耐性向上
            detectShadows=True
        )
        print("✅ 背景減算器初期化完了")
        
        print("🏁 計測準備完了！ローリングスタートモード")
        print("📋 待機中：スタートライン通過でTOTAL TIME計測開始")
        print("🔄 3周完了で自動的に計測終了・結果表示")
        print("⏳ 背景学習中...5秒お待ちください（重要）")

    def start_race(self):
        """レース開始（スタートライン通過時）"""
        if self.race_ready and not self.race_active:
            self.race_active = True
            self.race_ready = False  # 重要：準備状態を解除してレース状態に移行
            self.race_start_time = time.time()
            self.current_lap_start = self.race_start_time
            self.current_lap_number = 1  # LAP1開始
            self.last_detection_time = self.race_start_time  # 初回検出時間をリセット
            print(f"🏁 計測開始！LAP{self.current_lap_number} スタート - TOTAL TIMEカウント開始")

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
            
            # クールダウン期間チェック（背景学習中はスキップ）
            if not (self.race_ready and not self.race_active and self.preparation_start_time and 
                    (current_time - self.preparation_start_time) < 5.0):  # 5秒学習期間
                time_since_last = current_time - self.last_detection_time
                if time_since_last < self.detection_cooldown:
                    # 2周目以降のデバッグ情報を追加
                    if self.race_active and time_since_last < self.detection_cooldown:
                        print(f"⏱️ クールダウン中: {time_since_last:.1f}s / {self.detection_cooldown}s (LAP{self.current_lap_number})")
                    return False
            
            # 背景学習レート調整：準備中は高速学習、レース中は低速更新で誤検出防止
            if self.race_ready and not self.race_active:
                learning_rate = 0.01  # 準備中：高速学習
            elif self.race_active:
                learning_rate = 0.001  # レース中：微更新で誤検出防止
            else:
                learning_rate = 0.005  # その他：中程度更新
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fg_mask = self.bg_subtractor.apply(gray, learningRate=learning_rate)
            
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
            
            # v7高感度検出条件（安定版）
            motion_detected = False
            
            # 基本的な動き検出条件
            basic_motion = motion_pixels > self.motion_pixels_threshold and max_contour_area > self.min_contour_area
            
            # 面積比率チェック
            area_ratio_ok = self.motion_area_ratio_min <= motion_ratio <= self.motion_area_ratio_max
            
            # 輪郭数チェック
            contour_count_ok = len(contours) >= 1
            
            # 検出条件：基本動き + 面積比率 + 輪郭数（レース中はより厳しく）
            if self.race_active:
                # レース中：より厳しい条件（AND条件）
                if basic_motion and area_ratio_ok and contour_count_ok and len(contours) >= 2:
                    motion_detected = True
                    conditions_met = 4
            else:
                # 準備中：従来の条件（OR条件）
                if basic_motion and (area_ratio_ok or contour_count_ok):
                    motion_detected = True
                    conditions_met = 2 + (1 if area_ratio_ok else 0) + (1 if contour_count_ok else 0)
            
            # デバッグ情報更新
            self.last_motion_pixels = motion_pixels
            self.motion_area_ratio = motion_ratio
            
            if motion_detected:
                lap_info = f"LAP{self.current_lap_number}" if self.race_active else "READY"
                print(f"🔥 [{lap_info}] Motion detected! Conditions: {conditions_met}/4")
                print(f"   - Motion pixels: {motion_pixels} (threshold: {self.motion_pixels_threshold})")
                print(f"   - Max contour: {max_contour_area} (threshold: {self.min_contour_area})")
                print(f"   - Motion ratio: {motion_ratio:.4f}")
                print(f"   - Time since last detection: {current_time - self.last_detection_time:.2f}s")
                print(f"   - Learning rate: {learning_rate}")
                return True
            else:
                # 2周目以降で検出失敗時の詳細情報
                if self.race_active and self.current_lap_number >= 2:
                    print(f"❌ [LAP{self.current_lap_number}] 検出失敗 - Motion:{motion_pixels}, Area:{max_contour_area:.0f}, Ratio:{motion_ratio:.4f}")
                # デバッグ: 動きが検出されない理由を表示
                elif motion_pixels > 100:  # 最小限の動きがある場合のみ表示
                    print(f"📊 [DEBUG] No motion: pixels={motion_pixels}/{self.motion_pixels_threshold}, "
                          f"contour={max_contour_area}/{self.min_contour_area}, ratio={motion_ratio:.4f}")
            
            return False
            
        except Exception as e:
            print(f"❌ 動き検出エラー: {e}")
            return False

    def process_detection(self):
        """検出処理とラップ計測（4回検出システム）"""
        current_time = time.time()
        
        # 救済モード中は検出処理をスキップ
        if self.rescue_mode:
            return
        
        # 1回目：計測準備中にスタートライン通過で計測開始
        if self.race_ready and not self.race_active:
            # 背景学習時間を十分に確保（準備開始から5秒待機）
            if self.preparation_start_time and (current_time - self.preparation_start_time) < 5.0:
                learning_time = current_time - self.preparation_start_time
                print(f"⏳ 背景学習中... {learning_time:.1f}/5.0秒")
                return  # 背景学習中は検出しない
            elif not getattr(self, '_learning_completed', False):
                print("✅ 背景学習完了！")
                print("🎯 動体検出準備完了 - スタートライン通過で計測開始")
                print("-" * 50)
                # 学習完了後のテスト検出
                if hasattr(self, 'start_line_roi') and self.start_line_roi is not None and self.bg_subtractor is not None:
                    gray = cv2.cvtColor(self.start_line_roi, cv2.COLOR_BGR2GRAY) if len(self.start_line_roi.shape) == 3 else self.start_line_roi
                    test_mask = self.bg_subtractor.apply(gray, learningRate=0)
                    test_pixels = cv2.countNonZero(test_mask)
                    print(f"🧪 学習完了後ベースライン: Motion pixels = {test_pixels}")
                self._learning_completed = True  # 一度だけ表示
            
            print("🏁 レース計測開始 - スタートライン通過を検出")
            self.start_race()
            return
        
        # 2回目～4回目：レース中のラップ計測
        if self.race_active and not self.race_complete:
            current_time = time.time()
            
            # 現在のラップ時間を記録してラップ完了
            if self.current_lap_start is not None:
                lap_time = current_time - self.current_lap_start
                
                # ラップ完了処理
                if self.current_lap_number <= 3:
                    self.lap_times[self.current_lap_number - 1] = lap_time
                    self.lap_count += 1
                    print(f"⏱️ LAP{self.current_lap_number}: {self.format_time(lap_time)} 完了")
                
                # 3周完了チェック
                if self.current_lap_number >= 3:
                    # 4回目の検出 = 3周完了
                    self.total_time = current_time - self.race_start_time
                    self.race_complete = True
                    self.race_active = False
                    self.current_lap_number = 0  # 計測終了
                    
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
                
                # 次のラップ開始
                self.current_lap_number += 1
                self.current_lap_start = current_time
                print(f"🔄 LAP{self.current_lap_number} 開始")
                
                # 注意：last_detection_timeはメインループで更新

    def format_time(self, seconds):
        """時間フォーマット - MM:SS.sss形式"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:06.3f}"

    def draw_camera_view(self, frame, x, y, width, height, title):
        """カメラ映像を描画"""
        if frame is not None:
            # 左右反転を削除（正常な向きで表示）
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
            
            return frame
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
        
        # レース状態（右上のSTATUSと統一）
        if self.race_complete:
            status_text = "Finished"
            status_color = self.colors['text_yellow']
        elif self.rescue_mode:
            status_text = f"Rescue ({self.rescue_countdown:.1f}s)"
            status_color = self.colors['text_red']
        elif self.race_active:
            status_text = f"Qualifying Lap (LAP{self.current_lap_number})"
            status_color = self.colors['text_green']
        elif self.race_ready:
            status_text = "Ready for Start"
            status_color = self.colors['text_yellow']
        else:
            status_text = "Standby (S=Prepare)"
            status_color = self.colors['text_red']
        
        status = self.font_medium.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status, (info_x, info_y + 60))
        
        # 3周分のラップタイム表示（改良版）
        y_offset = 100
        for i in range(3):
            lap_number = i + 1
            
            if self.lap_times[i] > 0:  # 完了済みラップ（ホールド表示）
                lap_text = f"LAP{lap_number}: {self.format_time(self.lap_times[i])}"
                color = self.colors['text_green']
            elif self.current_lap_number == lap_number:  # 現在進行中のラップ
                if self.race_active and self.current_lap_start:
                    current_lap_time = time.time() - self.current_lap_start
                    lap_text = f"LAP{lap_number}: {self.format_time(current_lap_time)}"
                    color = self.colors['text_yellow']
                else:
                    lap_text = f"LAP{lap_number}: 00:00.000"
                    color = self.colors['text_white']
            else:  # 未開始のラップ
                lap_text = f"LAP{lap_number}: 00:00.000"
                color = self.colors['text_white']
            
            lap_surface = self.font_medium.render(lap_text, True, color)
            self.screen.blit(lap_surface, (info_x, info_y + y_offset + i * 40))
        
        # 総時間表示（修正版）
        if self.race_complete and self.total_time > 0:  # レース完了後は固定表示
            total_text = f"TOTAL: {self.format_time(self.total_time)}"
            total_color = self.colors['text_yellow']
        elif self.race_active and self.race_start_time:  # レース中は動的表示
            total = time.time() - self.race_start_time
            total_text = f"TOTAL: {self.format_time(total)}"
            total_color = self.colors['text_white']
        else:  # 準備状態または未開始（S押下時も含む）
            total_text = "TOTAL: 00:00.000"
            total_color = self.colors['text_white']
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
        """システム状態表示（簡潔版）"""
        status_y = 400
        
        # レース状態のみ表示
        if self.race_complete:
            status_text = "Finished"
            status_color = self.colors['text_yellow']
        elif self.race_active:
            status_text = f"Qualifying Lap (LAP{self.current_lap_number})"
            status_color = self.colors['text_green']
        elif self.race_ready:
            status_text = "Ready for Start"
            status_color = self.colors['text_yellow']
        else:
            status_text = "Standby"
            status_color = self.colors['text_red']
        
        status_surface = self.font_medium.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status_surface, (450, status_y))

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
                    if (self.race_ready or self.race_active) and not self.rescue_mode and not self.race_complete:
                        if self.camera_overview is None and self.camera_start_line is None:
                            print("🎮 手動検出シミュレーション実行")
                            self.process_detection()

    def run(self):
        """メインループ"""
        if not self.init_cameras():
            print("❌ カメラの初期化に失敗しました")
            return
        
        print("🚀 v10 3周計測システム開始")
        print("📋 操作: S=計測準備, R=救済申請, Q=停止, ESC=終了")
        print("📋 ローリングスタート: S押下後、スタートライン通過で計測開始")
        print("🆘 自走不能時: Rキーで救済申請（5秒ペナルティ）")
        print("🏁 3周完了で自動停止")
        print("⭐ v10改良点: 5秒背景学習＋検出分離＋MOG2最適化")
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
                
                # 動き検出（背景学習完了後のみ実行）
                if processed_sl is not None and self.bg_subtractor is not None:
                    # 背景学習の進行状況を計算
                    learning_time = 0
                    if self.race_ready and not self.race_active and self.preparation_start_time:
                        learning_time = time.time() - self.preparation_start_time
                    
                    # 学習完了後かつ、計測準備中またはレース中で、救済モードでない場合のみ検出
                    # レース中は learning_time チェックをスキップ
                    detection_ready = False
                    if self.race_active:  # レース中は常に検出可能
                        detection_ready = True
                    elif self.race_ready and not self.race_active:  # 準備中は学習完了後のみ
                        detection_ready = learning_time >= 5.0
                    
                    if detection_ready and not self.rescue_mode and not self.race_complete:
                        # 2周目以降の検出状況を詳しく監視
                        if self.race_active and self.current_lap_number >= 2:
                            time_since_last = time.time() - self.last_detection_time
                            print(f"🔍 [LAP{self.current_lap_number}] 検出試行中 - 最終検出から{time_since_last:.1f}s経過")
                        
                        if self.detect_motion_v7(processed_sl):
                            lap_info = f"LAP{self.current_lap_number}" if self.race_active else "READY"
                            print(f"🔍 [{lap_info}] スタートラインで動き検出 - 処理実行")
                            self.process_detection()
                            # 検出成功時は必ずlast_detection_timeを更新
                            self.last_detection_time = time.time()
                            print(f"⏰ クールダウンタイマー更新: {self.detection_cooldown}秒待機開始")
                
                # 背景学習進行状況表示と学習処理
                if self.race_ready and not self.race_active and self.preparation_start_time:
                    current_time = time.time()
                    learning_time = current_time - self.preparation_start_time
                    
                    # 背景学習期間中は背景減算器に継続的にフレームを学習させる（5秒に延長）
                    if processed_sl is not None and self.bg_subtractor is not None and learning_time < 5.0:
                        # 学習専用でフレームを背景モデルに追加（検出は行わない）
                        gray = cv2.cvtColor(processed_sl, cv2.COLOR_BGR2GRAY) if len(processed_sl.shape) == 3 else processed_sl
                        
                        # より慎重な学習レート（0.01に下げる）
                        _ = self.bg_subtractor.apply(gray, learningRate=0.01)
                        
                        # デバッグ: 背景学習状況を確認
                        if int(learning_time * 4) != getattr(self, '_debug_count', -1):  # 0.25秒ごと
                            test_mask = self.bg_subtractor.apply(gray, learningRate=0)  # テスト用検出
                            test_pixels = cv2.countNonZero(test_mask)
                            print(f"🔍 学習中デバッグ: {learning_time:.1f}s - Motion pixels: {test_pixels}")
                            self._debug_count = int(learning_time * 4)
                    
                    if learning_time < 5.0:
                        # 背景学習中の進行状況を定期的に表示（0.5秒ごと）
                        if int(learning_time * 2) != getattr(self, '_last_progress_count', -1):
                            print(f"⏳ 背景学習中... {learning_time:.1f}/5.0秒")
                            self._last_progress_count = int(learning_time * 2)
                    else:
                        # 5秒経過したら学習完了（計測開始はしない）
                        if not getattr(self, '_learning_completed', False):
                            print("✅ 背景学習完了！")
                            print("🎯 動体検出準備完了 - スタートライン通過で計測開始")
                            print("-" * 50)
                            # 学習完了後のテスト検出
                            if processed_sl is not None and self.bg_subtractor is not None:
                                gray = cv2.cvtColor(processed_sl, cv2.COLOR_BGR2GRAY) if len(processed_sl.shape) == 3 else processed_sl
                                test_mask = self.bg_subtractor.apply(gray, learningRate=0)
                                test_pixels = cv2.countNonZero(test_mask)
                                print(f"🧪 学習完了後ベースライン: Motion pixels = {test_pixels}")
                            self._learning_completed = True  # 一度だけ表示
                
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
    print("[v10 3-LAP SYSTEM] 初期化完了")
    print("[v10] LAP1/LAP2/LAP3の3周計測システム")
    print("[v10] ローリングスタート対応（Sキー準備→通過開始）")
    print("[v10] 救済システム（Rキーで5秒ペナルティ）")
    print("[v10] 背景学習最適化版（5秒学習期間＋検出分離）")
    main()