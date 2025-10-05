#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v12 - デバッグ強化版)
- リアルタイム閾値調整機能
- 詳細なデバッグ表示
- キーボードでパラメータを動的に変更可能
- 検出状況の視覚的フィードバック強化
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

class TeamsSimpleLaptimeSystemFixedV12:
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🏁 Lap Timer - Teams View (v12 - Debug Enhanced)")
        self.colors = {
            'background': (15, 15, 25),
            'text_white': (255, 255, 255),
            'text_green': (0, 255, 100),
            'text_yellow': (255, 255, 50),
            'text_red': (255, 80, 80),
            'text_blue': (100, 150, 255),
            'text_orange': (255, 165, 0),
            'panel_bg': (40, 40, 60),
            'border': (80, 80, 100),
            'debug_bg': (25, 25, 45)
        }
        try:
            self.font_huge = pygame.font.Font(None, 120)
            self.font_large = pygame.font.Font(None, 80)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
            self.font_tiny = pygame.font.Font(None, 24)
        except:
            self.font_huge = pygame.font.SysFont('arial', 120, bold=True)
            self.font_large = pygame.font.SysFont('arial', 80, bold=True)
            self.font_medium = pygame.font.SysFont('arial', 48)
            self.font_small = pygame.font.SysFont('arial', 32)
            self.font_tiny = pygame.font.SysFont('arial', 24)
        
        self.camera_overview = None
        self.camera_start_line = None
        self.bg_subtractor = None
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
        
        # v12: デバッグ強化版設定（リアルタイム調整可能）
        self.motion_pixels_threshold = 500  # 初期値
        self.min_contour_area = 300         # 初期値
        self.motion_area_ratio_min = 0.001
        self.motion_area_ratio_max = 0.8
        self.pixel_diff_threshold = 20      # 初期値
        self.detection_conditions_required = 3  # 初期値
        self.cooldown_time = 2.5            # 初期値
        
        # デバッグ情報保存
        self.debug_info = {
            'motion_pixels': 0,
            'max_contour_area': 0,
            'motion_ratio': 0.0,
            'conditions_met': 0,
            'total_contours': 0,
            'avg_contour_area': 0,
            'motion_density': 0,
            'frame_diff_total': 0
        }
        
        # 調整ステップ
        self.adjust_step = {
            'motion_pixels': 50,
            'contour_area': 50,
            'pixel_diff': 5,
            'conditions': 1,
            'cooldown': 0.5
        }
        
        print(f"[v12 DEBUG] 初期設定:")
        print(f"  motion_pixels_threshold: {self.motion_pixels_threshold}")
        print(f"  min_contour_area: {self.min_contour_area}")
        print(f"  detection_conditions_required: {self.detection_conditions_required}")
        print(f"  cooldown_time: {self.cooldown_time}")
        print("[v12 DEBUG] Real-time adjustable parameters")
        print("キー操作: ↑↓=motion_pixels, ←→=contour_area, PgUp/PgDn=conditions, +/-=cooldown")

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
        self.camera_start_line_id = 1
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
            
            # デバッグ用背景差分
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=200,
                varThreshold=16,
                detectShadows=False
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
            print("🏁 レース開始 (v12 - Debug Enhanced)")

    def stop_race(self):
        if self.race_active:
            self.race_active = False
            print("🏁 レース終了")

    def adjust_parameters(self, keys):
        """v12: リアルタイムパラメータ調整"""
        adjusted = False
        
        # motion_pixels_threshold 調整 (↑↓キー)
        if keys[pygame.K_UP]:
            self.motion_pixels_threshold += self.adjust_step['motion_pixels']
            adjusted = True
        elif keys[pygame.K_DOWN]:
            self.motion_pixels_threshold = max(50, self.motion_pixels_threshold - self.adjust_step['motion_pixels'])
            adjusted = True
        
        # min_contour_area 調整 (←→キー)
        elif keys[pygame.K_RIGHT]:
            self.min_contour_area += self.adjust_step['contour_area']
            adjusted = True
        elif keys[pygame.K_LEFT]:
            self.min_contour_area = max(50, self.min_contour_area - self.adjust_step['contour_area'])
            adjusted = True
        
        # detection_conditions_required 調整 (PageUp/PageDown)
        elif keys[pygame.K_PAGEUP]:
            self.detection_conditions_required = min(6, self.detection_conditions_required + 1)
            adjusted = True
        elif keys[pygame.K_PAGEDOWN]:
            self.detection_conditions_required = max(1, self.detection_conditions_required - 1)
            adjusted = True
        
        # cooldown_time 調整 (+/-)
        elif keys[pygame.K_PLUS] or keys[pygame.K_EQUALS]:
            self.cooldown_time += self.adjust_step['cooldown']
            adjusted = True
        elif keys[pygame.K_MINUS]:
            self.cooldown_time = max(0.5, self.cooldown_time - self.adjust_step['cooldown'])
            adjusted = True
        
        if adjusted:
            print(f"🔧 [v12 ADJUST] motion_pixels: {self.motion_pixels_threshold}, "
                  f"contour_area: {self.min_contour_area}, "
                  f"conditions: {self.detection_conditions_required}, "
                  f"cooldown: {self.cooldown_time:.1f}s")

    def detect_motion_debug_enhanced(self, frame):
        """v12: デバッグ強化版動き検出"""
        try:
            current_time = time.time()
            
            # クールダウン期間チェック
            if current_time - self.last_detection_time < self.cooldown_time:
                return False
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fg_mask = self.bg_subtractor.apply(gray)
            
            # ノイズ除去
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            motion_pixels = cv2.countNonZero(fg_mask)
            frame_area = frame.shape[0] * frame.shape[1]
            motion_ratio = motion_pixels / frame_area
            
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 詳細な条件チェック
            conditions_met = 0
            max_contour_area = 0
            total_contour_area = 0
            
            # 条件1: 動きピクセル数
            if motion_pixels > self.motion_pixels_threshold:
                conditions_met += 1
            
            # 条件2: 最大輪郭面積
            if contours:
                max_contour_area = max(cv2.contourArea(c) for c in contours)
                total_contour_area = sum(cv2.contourArea(c) for c in contours)
                if max_contour_area > self.min_contour_area:
                    conditions_met += 1
            
            # 条件3: 動き面積比
            if self.motion_area_ratio_min < motion_ratio < self.motion_area_ratio_max:
                conditions_met += 1
            
            # 条件4: 輪郭数
            if len(contours) >= 3:
                conditions_met += 1
            
            # 条件5: 平均輪郭面積
            avg_contour_area = total_contour_area / len(contours) if contours else 0
            if avg_contour_area > 100:
                conditions_met += 1
            
            # 条件6: 動きピクセル密度
            motion_density = motion_pixels / max(1, len(contours)) if contours else 0
            if motion_density > 100:
                conditions_met += 1
            
            # デバッグ情報更新
            self.debug_info.update({
                'motion_pixels': motion_pixels,
                'max_contour_area': max_contour_area,
                'motion_ratio': motion_ratio,
                'conditions_met': conditions_met,
                'total_contours': len(contours),
                'avg_contour_area': avg_contour_area,
                'motion_density': motion_density,
                'frame_diff_total': np.sum(fg_mask) // 255
            })
            
            # 動き検出判定
            motion_detected = conditions_met >= self.detection_conditions_required
            
            if motion_detected:
                print(f"🔥 [v12 DEBUG] Motion detected! Conditions: {conditions_met}/{self.detection_conditions_required}")
                print(f"   - Motion pixels: {motion_pixels} (threshold: {self.motion_pixels_threshold})")
                print(f"   - Max contour: {max_contour_area} (threshold: {self.min_contour_area})")
                print(f"   - Motion ratio: {motion_ratio:.4f}")
                print(f"   - Contours: {len(contours)}, Avg area: {avg_contour_area:.1f}")
                self.last_detection_time = current_time
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ デバッグ強化版動き検出エラー: {e}")
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

    def draw_debug_panel(self):
        """v12: デバッグパネル表示"""
        debug_x = 20
        debug_y = 400
        panel_width = 800
        panel_height = 140
        
        # デバッグパネル背景
        debug_rect = pygame.Rect(debug_x, debug_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, self.colors['debug_bg'], debug_rect)
        pygame.draw.rect(self.screen, self.colors['border'], debug_rect, 2)
        
        # タイトル
        title_surface = self.font_small.render("🔍 v12 DEBUG PANEL - Real-time Parameters", True, self.colors['text_orange'])
        self.screen.blit(title_surface, (debug_x + 10, debug_y + 5))
        
        # 現在のパラメータ表示
        params_y = debug_y + 35
        param_lines = [
            f"motion_pixels: {self.motion_pixels_threshold} (↑↓で調整)",
            f"contour_area: {self.min_contour_area} (←→で調整)",
            f"conditions: {self.detection_conditions_required}/6 (PgUp/PgDnで調整)",
            f"cooldown: {self.cooldown_time:.1f}s (+/-で調整)"
        ]
        
        for i, line in enumerate(param_lines):
            param_surface = self.font_tiny.render(line, True, self.colors['text_yellow'])
            self.screen.blit(param_surface, (debug_x + 10, params_y + i * 20))
        
        # 検出状況表示
        status_x = debug_x + 400
        status_lines = [
            f"Motion Pixels: {self.debug_info['motion_pixels']}",
            f"Max Contour: {self.debug_info['max_contour_area']}",
            f"Conditions: {self.debug_info['conditions_met']}/6",
            f"Contours: {self.debug_info['total_contours']}"
        ]
        
        for i, line in enumerate(status_lines):
            color = self.colors['text_green'] if i == 2 and self.debug_info['conditions_met'] >= self.detection_conditions_required else self.colors['text_white']
            status_surface = self.font_tiny.render(line, True, color)
            self.screen.blit(status_surface, (status_x, params_y + i * 20))

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
            "S: レース開始  Q: レース停止  ESC: 終了",
            "v12: デバッグ強化版 - リアルタイム調整可能"
        ]
        
        for i, control in enumerate(controls):
            color = self.colors['text_green'] if i == 0 else self.colors['text_blue']
            control_surface = self.font_small.render(control, True, color)
            self.screen.blit(control_surface, (20, controls_y + i * 25))

    def handle_events(self):
        """イベント処理"""
        keys = pygame.key.get_pressed()
        
        # リアルタイム調整
        self.adjust_parameters(keys)
        
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
        
        print("🚀 システム開始 - v12 デバッグ強化版")
        print("📋 操作: S=開始, Q=停止, ESC=終了")
        print("🔧 調整: ↑↓=motion_pixels, ←→=contour_area, PgUp/PgDn=conditions, +/-=cooldown")
        
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
                if self.race_active and processed_sl is not None and self.bg_subtractor is not None:
                    if self.detect_motion_debug_enhanced(processed_sl):
                        self.process_detection()
                
                # UI描画
                self.draw_lap_info()
                self.draw_controls()
                self.draw_debug_panel()
                
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
    system = TeamsSimpleLaptimeSystemFixedV12()
    system.run()

if __name__ == "__main__":
    main()