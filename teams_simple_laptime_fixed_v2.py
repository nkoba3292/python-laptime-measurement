#!/usr/bin/env python3
"""
🔧 修正版: Teams共有用シンプル表示版ラップタイム計測システム (Raspberry Pi最適化版)
- 全画面表示対応
- カメラ画像ミラー（左右反転）
- 動き検知感度調整
- ラズパイ5最適化
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

class TeamsSimpleLaptimeSystemFixed:
    def __init__(self):
        # 🖥️ 全画面表示設定（ラズパイ最適化）
        # 画面解像度を自動取得
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        
        print(f"🖥️ 検出された画面解像度: {self.screen_width}x{self.screen_height}")
        
        # 全画面モード設定
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("🏁 Lap Timer - Full Screen (Raspberry Pi)")

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

        # 🎨 全画面用フォント設定（スケール調整）
        font_scale = min(self.screen_width / 1920, self.screen_height / 1080)
        
        try:
            self.font_huge = pygame.font.Font(None, int(150 * font_scale))     # 周回数用
            self.font_large = pygame.font.Font(None, int(100 * font_scale))    # タイム用
            self.font_medium = pygame.font.Font(None, int(60 * font_scale))    # ラベル用
            self.font_small = pygame.font.Font(None, int(40 * font_scale))     # 状態用
        except:
            self.font_huge = pygame.font.SysFont('arial', int(150 * font_scale), bold=True)
            self.font_large = pygame.font.SysFont('arial', int(100 * font_scale), bold=True)
            self.font_medium = pygame.font.SysFont('arial', int(60 * font_scale))
            self.font_small = pygame.font.SysFont('arial', int(40 * font_scale))

        print(f"🎨 フォントスケール: {font_scale:.2f}")

        # カメラ設定
        self.camera_overview = None
        self.camera_start_line = None
        self.bg_subtractor = None

        # 📷 カメラミラー設定
        self.mirror_cameras = True  # 左右反転有効

        # レース状態
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        self.last_detection_time = 0
        self.detection_cooldown = 3.0  # 感度調整: 3秒に延長

        # タイム表示制御
        self.hide_time_after_lap = 3        # 3周目以降でタイム非表示
        self.time_visible = True

        # 時間表示最適化
        self.last_time_update = 0
        self.display_time = 0.0
        self.time_update_interval = 0.1  # 100ms間隔で更新

        # 🎯 動き検知感度調整（ラズパイ最適化）
        self.last_motion_pixels = 0
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 30  # ラズパイ用に30FPSに調整

        # フレームバッファ
        self.current_overview_frame = None
        self.current_startline_frame = None

        # カメラ検索結果
        self.available_cameras = []

        # 設定読み込み
        self.load_config()

        # カメラスレッド用ロック
        self.frame_lock = threading.Lock()

    def load_config(self):
        """設定ファイル読み込み（感度調整版）"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
                print("✅ config.json 読み込み完了")
        except FileNotFoundError:
            # 🎯 ラズパイ最適化デフォルト設定
            self.config = {
                "camera_settings": {
                    "overview_camera_index": 0,
                    "startline_camera_index": 1,
                    "frame_width": 640,
                    "frame_height": 480
                },
                "detection_settings": {
                    "motion_pixels_threshold": 1500,  # 感度を下げる（500→1500）
                    "motion_area_threshold": 0.05,    # 追加：面積閾値
                    "background_learning_rate": 0.01  # 背景学習率を下げる
                },
                "race_settings": {
                    "max_laps": 10,
                    "detection_cooldown": 3.0  # 3秒に延長
                }
            }
            print("⚠️ config.json not found, using Raspberry Pi optimized settings")

    def find_available_cameras(self):
        """利用可能なカメラを検索"""
        print("🔍 利用可能なカメラを検索中...")
        self.available_cameras = []

        for i in range(10):  # 0-9のインデックスをチェック
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.available_cameras.append(i)
                    print(f"✅ カメラ {i}: 利用可能")
                else:
                    print(f"❌ カメラ {i}: フレーム取得失敗")
                cap.release()
            else:
                if i < 3:  # 最初の3つだけログ
                    print(f"❌ カメラ {i}: 開けません")

        print(f"📹 検出されたカメラ: {self.available_cameras}")
        return len(self.available_cameras) >= 1

    def initialize_cameras(self):
        """カメラ初期化（ミラー対応版）"""
        print("📹 全画面表示カメラシステム初期化中...")

        # 利用可能なカメラを検索
        if not self.find_available_cameras():
            print("❌ 利用可能なカメラが見つかりません")
            return False

        # Overview カメラ設定
        overview_idx = self.available_cameras[0]
        print(f"📹 Overview カメラ: インデックス {overview_idx}")

        self.camera_overview = cv2.VideoCapture(overview_idx)
        if not self.camera_overview.isOpened():
            print(f"❌ Overview camera (index {overview_idx}) failed to open")
            return False

        # StartLine カメラ設定
        if len(self.available_cameras) >= 2:
            startline_idx = self.available_cameras[1]
            print(f"📹 StartLine カメラ: インデックス {startline_idx}")
        else:
            startline_idx = self.available_cameras[0]
            print(f"⚠️ StartLine カメラ: Overview と同じカメラを使用 (index {startline_idx})")

        self.camera_start_line = cv2.VideoCapture(startline_idx)
        if not self.camera_start_line.isOpened():
            print(f"❌ Start line camera (index {startline_idx}) failed to open")
            return False

        # カメラ設定最適化
        camera_width = self.config['camera_settings']['frame_width']
        camera_height = self.config['camera_settings']['frame_height']
        
        for camera in [self.camera_overview, self.camera_start_line]:
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            camera.set(cv2.CAP_PROP_FPS, 30)

        # 背景差分初期化
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=50,  # 感度調整
            history=500
        )

        print("✅ カメラ初期化完了")
        print(f"📷 ミラー効果: {'有効' if self.mirror_cameras else '無効'}")
        return True

    def capture_frames(self):
        """フレーム取得（ミラー処理付き）"""
        while self.running:
            if self.camera_overview and self.camera_start_line:
                ret1, frame1 = self.camera_overview.read()
                ret2, frame2 = self.camera_start_line.read()

                if ret1 and ret2:
                    # 🪞 カメラ画像ミラー処理（左右反転）
                    if self.mirror_cameras:
                        frame1 = cv2.flip(frame1, 1)  # 水平反転
                        frame2 = cv2.flip(frame2, 1)  # 水平反転

                    with self.frame_lock:
                        self.current_overview_frame = frame1.copy()
                        self.current_startline_frame = frame2.copy()

            time.sleep(0.03)  # 約30fps

    def detect_motion_improved(self, frame):
        """改良版動き検知（感度調整）"""
        if self.bg_subtractor is None:
            return False

        # クールダウンチェック
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            return False

        # 🎯 動き検知処理（感度調整版）
        fg_mask = self.bg_subtractor.apply(frame, learningRate=self.config['detection_settings'].get('background_learning_rate', 0.01))

        # ノイズ除去
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        # 動きピクセル数を計算
        motion_pixels = cv2.countNonZero(fg_mask)
        self.last_motion_pixels = motion_pixels

        # 閾値チェック（感度調整）
        motion_threshold = self.config['detection_settings']['motion_pixels_threshold']
        
        if motion_pixels > motion_threshold:
            # 追加チェック：動きの面積が十分大きいか
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area_ratio = cv2.contourArea(largest_contour) / (frame.shape[0] * frame.shape[1])
                
                area_threshold = self.config['detection_settings'].get('motion_area_threshold', 0.05)
                if area_ratio > area_threshold:
                    self.last_detection_time = current_time
                    print(f"🚗 車両検知! (ピクセル: {motion_pixels}, 面積比: {area_ratio:.3f})")
                    return True

        return False

    def handle_lap_completion(self):
        """ラップ完了処理（感度調整版）"""
        current_time = time.time()

        if not self.race_active:
            # レース開始
            self.race_active = True
            self.start_time = current_time
            self.lap_count = 1
            print("🏁 レーススタート!")

        else:
            # ラップ完了
            lap_time = current_time - self.start_time
            self.lap_times.append(lap_time)
            self.lap_count += 1

            print(f"⏱️ ラップ {len(self.lap_times)} 完了: {lap_time:.3f}秒")

            # 次のラップ開始
            self.start_time = current_time

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
            'total_time': sum(self.lap_times) if self.lap_times else 0,
            'detection_settings': self.config['detection_settings']
        }

        filename = f"data/race_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"💾 結果保存: {filename}")

    def update_display_time(self):
        """表示時間更新（最適化版）"""
        current_time = time.time()

        # 一定間隔で時間更新（滑らかな表示）
        if current_time - self.last_time_update >= self.time_update_interval:
            if self.race_active and self.start_time:
                self.display_time = current_time - self.start_time
            self.last_time_update = current_time

    def draw_fullscreen_interface(self):
        """🖥️ 全画面インターフェース描画"""
        self.screen.fill(self.colors['background'])

        # レイアウト計算（全画面対応）
        margin = int(self.screen_width * 0.02)
        
        # カメラ表示エリア（上部2/3）
        camera_area_height = int(self.screen_height * 0.65)
        info_area_height = self.screen_height - camera_area_height - margin

        # カメラフレーム描画
        if self.current_overview_frame is not None and self.current_startline_frame is not None:
            with self.frame_lock:
                # フレームサイズ調整
                camera_width = (self.screen_width - margin * 3) // 2
                camera_height = camera_area_height - margin * 2

                # Overview カメラ（左）
                overview_resized = cv2.resize(self.current_overview_frame, (camera_width, camera_height))
                overview_rgb = cv2.cvtColor(overview_resized, cv2.COLOR_BGR2RGB)
                overview_surface = pygame.surfarray.make_surface(overview_rgb.swapaxes(0, 1))
                self.screen.blit(overview_surface, (margin, margin))

                # StartLine カメラ（右）
                startline_resized = cv2.resize(self.current_startline_frame, (camera_width, camera_height))
                startline_rgb = cv2.cvtColor(startline_resized, cv2.COLOR_BGR2RGB)
                startline_surface = pygame.surfarray.make_surface(startline_rgb.swapaxes(0, 1))
                self.screen.blit(startline_surface, (camera_width + margin * 2, margin))

                # カメララベル
                overview_label = self.font_medium.render("📹 Overview Camera", True, self.colors['text_white'])
                startline_label = self.font_medium.render("🏁 Start Line Camera", True, self.colors['text_white'])
                
                self.screen.blit(overview_label, (margin + 10, margin + 10))
                self.screen.blit(startline_label, (camera_width + margin * 2 + 10, margin + 10))

        # 情報パネル（下部1/3）
        info_y = camera_area_height + margin
        
        # 背景パネル
        info_rect = pygame.Rect(margin, info_y, self.screen_width - margin * 2, info_area_height)
        pygame.draw.rect(self.screen, self.colors['panel_bg'], info_rect)
        pygame.draw.rect(self.screen, self.colors['border'], info_rect, 3)

        # レース情報描画
        self.draw_race_info(info_rect)

    def draw_race_info(self, rect):
        """レース情報描画（全画面レイアウト）"""
        padding = 20
        col_width = rect.width // 3

        # 周回数表示（左列）
        lap_text = f"LAP {self.lap_count}"
        if self.lap_count == 0:
            lap_text = "READY"
        
        lap_surface = self.font_huge.render(lap_text, True, self.colors['text_green'])
        lap_rect = lap_surface.get_rect()
        lap_x = rect.x + padding
        lap_y = rect.y + (rect.height - lap_rect.height) // 2
        self.screen.blit(lap_surface, (lap_x, lap_y))

        # タイム表示（中央列）
        if self.race_active and self.time_visible:
            self.update_display_time()
            time_text = f"{self.display_time:.1f}s"
            time_color = self.colors['text_yellow']
        elif not self.time_visible:
            time_text = "---"
            time_color = self.colors['text_red']
        else:
            time_text = "0.0s"
            time_color = self.colors['text_white']

        time_surface = self.font_large.render(time_text, True, time_color)
        time_rect = time_surface.get_rect()
        time_x = rect.x + col_width + (col_width - time_rect.width) // 2
        time_y = rect.y + (rect.height - time_rect.height) // 2
        self.screen.blit(time_surface, (time_x, time_y))

        # ラップタイム履歴（右列）
        if self.lap_times:
            latest_laps = self.lap_times[-3:]  # 最新3つのラップ
            lap_history_x = rect.x + col_width * 2 + padding
            
            for i, lap_time in enumerate(latest_laps):
                lap_text = f"L{len(self.lap_times) - len(latest_laps) + i + 1}: {lap_time:.2f}s"
                lap_surface = self.font_small.render(lap_text, True, self.colors['text_white'])
                lap_y = rect.y + padding + i * 40
                self.screen.blit(lap_surface, (lap_history_x, lap_y))

        # ステータス情報（下部）
        status_y = rect.y + rect.height - 60
        
        # 動き検知情報
        motion_text = f"Motion: {self.last_motion_pixels} pixels"
        motion_surface = self.font_small.render(motion_text, True, self.colors['text_white'])
        self.screen.blit(motion_surface, (rect.x + padding, status_y))

        # 感度設定情報
        threshold_text = f"Threshold: {self.config['detection_settings']['motion_pixels_threshold']}"
        threshold_surface = self.font_small.render(threshold_text, True, self.colors['text_white'])
        self.screen.blit(threshold_surface, (rect.x + padding + 200, status_y))

        # 終了方法（右下）
        quit_text = "Press ESC to quit"
        quit_surface = self.font_small.render(quit_text, True, self.colors['text_red'])
        quit_rect = quit_surface.get_rect()
        self.screen.blit(quit_surface, (rect.x + rect.width - quit_rect.width - padding, status_y))

    def run(self):
        """メインループ（全画面版）"""
        print("🚀 全画面ラップタイマー開始")
        print("=" * 50)

        if not self.initialize_cameras():
            print("❌ カメラ初期化失敗")
            return

        # カメラスレッド開始
        camera_thread = threading.Thread(target=self.capture_frames, daemon=True)
        camera_thread.start()

        print("✅ システム準備完了")
        print("🎯 動き検知感度設定:")
        print(f"   - 動きピクセル閾値: {self.config['detection_settings']['motion_pixels_threshold']}")
        print(f"   - 面積比閾値: {self.config['detection_settings'].get('motion_area_threshold', 0.05)}")
        print(f"   - 検知クールダウン: {self.detection_cooldown}秒")
        print("🪞 カメラミラー: 有効")
        print("📺 ESCキーで終了")

        # メインループ
        while self.running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        # スペースキーで手動ラップ
                        print("🔘 手動ラップトリガー")
                        self.handle_lap_completion()
                    elif event.key == pygame.K_r:
                        # リセット
                        self.race_active = False
                        self.lap_count = 0
                        self.lap_times.clear()
                        self.time_visible = True
                        print("🔄 レースリセット")

            # 動き検知
            if self.current_startline_frame is not None:
                with self.frame_lock:
                    if self.detect_motion_improved(self.current_startline_frame):
                        self.handle_lap_completion()

            # 画面描画
            self.draw_fullscreen_interface()
            pygame.display.flip()

            # FPS制御
            self.clock.tick(self.fps)

        # 終了処理
        self.cleanup()

    def cleanup(self):
        """リソース解放"""
        print("🧹 システム終了処理中...")
        
        self.running = False
        
        if self.camera_overview:
            self.camera_overview.release()
        if self.camera_start_line:
            self.camera_start_line.release()
        
        cv2.destroyAllWindows()
        pygame.quit()
        
        print("✅ 終了完了")

def main():
    """メイン関数"""
    print("🍓 Raspberry Pi 5 Full Screen Lap Timer")
    print("🔧 Features: 全画面表示 + カメラミラー + 感度調整")
    print("=" * 60)
    
    try:
        system = TeamsSimpleLaptimeSystemFixed()
        system.run()
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C で中断されました")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()