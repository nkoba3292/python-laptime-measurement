#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v11 - 簡易差分版)
- シンプルなピクセル差分による高速動き検出
- 最小限の処理で最大の感度を実現
- 軽量で高速な動作を重視した実装
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

class TeamsSimpleLaptimeSystemFixedV11:
    def __init__(self):
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🏁 Lap Timer - Teams View (v11 - Simple Pixel Diff)")
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
        
        # v11: 簡易差分用変数
        self.previous_frame_gray = None
        self.frame_buffer = []  # フレームバッファ
        self.buffer_size = 3    # バッファサイズ
        
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
        
        # v11: 簡易差分設定（極めて敏感）
        self.pixel_diff_threshold = 10   # ピクセル差の閾値（極小）
        self.total_diff_threshold = 500  # 総差分の閾値（極小）
        self.region_diff_threshold = 50  # 領域差分の閾値（極小）
        self.motion_percentage_threshold = 0.1  # 動き領域の割合（0.1%）
        
        self.last_total_diff = 0
        self.last_motion_percentage = 0.0
        self.last_max_region_diff = 0
        
        print(f"[v11 SIMPLE_DIFF] pixel_diff_threshold: {self.pixel_diff_threshold}")
        print(f"[v11 SIMPLE_DIFF] total_diff_threshold: {self.total_diff_threshold}")
        print(f"[v11 SIMPLE_DIFF] motion_percentage_threshold: {self.motion_percentage_threshold}%")
        print("[v11 SIMPLE_DIFF] Ultra-fast simple pixel difference")

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
        self.camera_start_line_id = 0

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
            # 簡易差分初期化
            self.previous_frame_gray = None
            self.frame_buffer = []
            print("🏁 レース開始 (v11 - Simple Pixel Diff)")

    def stop_race(self):
        if self.race_active:
            self.race_active = False
            self.previous_frame_gray = None
            self.frame_buffer = []
            print("🏁 レース終了")

    def detect_motion_simple_diff(self, frame):
        """v11: シンプルなピクセル差分による動き検出"""
        try:
            current_time = time.time()
            
            # クールダウン期間チェック（短縮）
            if current_time - self.last_detection_time < 1.5:
                return False
            
            # グレースケール変換（リサイズで高速化）
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (160, 120))  # 1/4サイズで高速化
            
            # 軽いガウシアンブラー
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # フレームバッファに追加
            self.frame_buffer.append(gray)
            if len(self.frame_buffer) > self.buffer_size:
                self.frame_buffer.pop(0)
            
            # バッファが満たない場合は処理しない
            if len(self.frame_buffer) < 2:
                return False
            
            # 複数の差分計算
            motion_detected = False
            total_diffs = []
            
            # 連続フレーム差分
            for i in range(len(self.frame_buffer) - 1):
                current_frame = self.frame_buffer[i + 1]
                previous_frame = self.frame_buffer[i]
                
                # 絶対差分
                diff = cv2.absdiff(current_frame, previous_frame)
                
                # 閾値処理
                _, thresh = cv2.threshold(diff, self.pixel_diff_threshold, 255, cv2.THRESH_BINARY)
                
                # 統計計算
                total_diff = np.sum(thresh) // 255  # 動いたピクセル数
                frame_area = current_frame.shape[0] * current_frame.shape[1]
                motion_percentage = (total_diff / frame_area) * 100
                
                total_diffs.append(total_diff)
                
                # v11: 極めて敏感な検出条件
                if (total_diff > self.total_diff_threshold or 
                    motion_percentage > self.motion_percentage_threshold):
                    motion_detected = True
            
            # 追加検証：最新と最古フレームの比較
            if len(self.frame_buffer) == self.buffer_size:
                long_diff = cv2.absdiff(self.frame_buffer[-1], self.frame_buffer[0])
                _, long_thresh = cv2.threshold(long_diff, self.pixel_diff_threshold, 255, cv2.THRESH_BINARY)
                long_total_diff = np.sum(long_thresh) // 255
                
                if long_total_diff > self.region_diff_threshold:
                    motion_detected = True
            
            # 統計保存
            self.last_total_diff = max(total_diffs) if total_diffs else 0
            self.last_motion_percentage = (self.last_total_diff / (160 * 120)) * 100
            self.last_max_region_diff = long_total_diff if len(self.frame_buffer) == self.buffer_size else 0
            
            if motion_detected:
                print(f"🔥 [v11 SIMPLE_DIFF] Motion detected!")
                print(f"   - Max total diff: {self.last_total_diff} (threshold: {self.total_diff_threshold})")
                print(f"   - Motion percentage: {self.last_motion_percentage:.3f}% (threshold: {self.motion_percentage_threshold}%)")
                print(f"   - Long range diff: {self.last_max_region_diff} (threshold: {self.region_diff_threshold})")
                self.last_detection_time = current_time
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 簡易差分検出エラー: {e}")
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
        """v11状態表示"""
        status_y = 650
        
        # v11検出方式表示
        method_text = f"v11 SIMPLE_DIFF - 高速ピクセル差分"
        method_surface = self.font_small.render(method_text, True, self.colors['text_green'])
        self.screen.blit(method_surface, (20, status_y))
        
        # 検出パラメータ表示
        params_text = f"pixel_threshold: {self.pixel_diff_threshold}, total_threshold: {self.total_diff_threshold}"
        params_surface = self.font_small.render(params_text, True, self.colors['text_yellow'])
        self.screen.blit(params_surface, (20, status_y + 25))
        
        # 最新検出状態
        if hasattr(self, 'last_total_diff'):
            detection_text = f"最新: total_diff={self.last_total_diff}, motion={self.last_motion_percentage:.3f}%, range_diff={self.last_max_region_diff}"
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
            "v11: 簡易差分版"
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
        
        print("🚀 システム開始 - v11 簡易差分版")
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
                    if self.detect_motion_simple_diff(processed_sl):
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
    system = TeamsSimpleLaptimeSystemFixedV11()
    system.run()

if __name__ == "__main__":
    main()