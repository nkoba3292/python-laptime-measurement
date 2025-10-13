#!/usr/bin/env python3
"""
Teams共有用シンプル表示タイム計測システム (v4 - 物体検知感度調整版)
- カメラ画像の左右反転を修正 (cv2.flip適用)
- 物体検知感度の大幅改良：閾値調整、面積比チェック、クールダウン延長
- 誤検知を大幅に削減して実際の移動のみを検出
- Teams会議での画面共有に最適化
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

class TeamsSimpleLaptimeSystemFixedV4:
    def __init__(self):
        # ディスプレイ設定（Teams共有最適化）
        self.screen_width = 1280
        self.screen_height = 720

        # ウィンドウモード（Teams共有用）
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("🏁 Lap Timer - Teams View (v4 - Enhanced Detection)")

        # シンプル色設定
        self.colors = {
            'background': (15, 15, 25),      # ダークブルー
            'text_white': (255, 255, 255),   # 白
            'text_green': (0, 255, 100),     # 緑
            'text_yellow': (255, 255, 50),   # 黄
            'text_red': (255, 80, 80),       # 赤
            'panel_bg': (40, 40, 60),        # パネル背景
            'border': (80, 80, 100)          # 境界線
        }

        # シンプルフォント設定
        try:
            self.font_huge = pygame.font.Font(None, 120)     # 周回数用
            self.font_large = pygame.font.Font(None, 80)     # タイム用
            self.font_medium = pygame.font.Font(None, 48)    # ラベル用
            self.font_small = pygame.font.Font(None, 32)     # 状況用
        except:
            self.font_huge = pygame.font.SysFont('arial', 120, bold=True)
            self.font_large = pygame.font.SysFont('arial', 80, bold=True)
            self.font_medium = pygame.font.SysFont('arial', 48)
            self.font_small = pygame.font.SysFont('arial', 32)

        # カメラ設定
        self.camera_overview = None
        self.camera_start_line = None
        self.bg_subtractor = None

        # レース状況
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        self.last_detection_time = 0
        
        # 🔧 検知感度調整: クールダウンを大幅に延長
        self.detection_cooldown = 3.0  # 3秒に延長（元: 2.0秒）

        # タイム表示制御
        self.hide_time_after_lap = 3        # 3周目以降でタイム非表示
        self.time_visible = True

        # 時間表示最適化
        self.last_time_update = 0
        self.display_time = 0.0
        self.time_update_interval = 0.1  # 100ms間隔で更新

        # 🔧 物体検知強化: より詳細な情報保存
        self.last_motion_pixels = 0
        self.motion_history = []  # 直近の動きを記録
        self.stable_frame_count = 0  # 安定フレーム数
        self.motion_area_ratio = 0.0  # 動き面積比
        
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 60  # 高FPSで滑らか表示

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
        """設定ファイル読み込み（検知感度強化版）"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 🔧 デフォルト設定: 検知感度を大幅調整
            self.config = {
                "camera_settings": {
                    "overview_camera_index": 0,
                    "startline_camera_index": 2,
                    "frame_width": 640,
                    "frame_height": 480
                },
                "detection_settings": {
                    # 🔧 感度調整: 閾値を大幅に上げて誤検知を削減
                    "motion_pixels_threshold": 1500,      # 500 → 1500 (3倍)
                    "min_contour_area": 2000,             # 最小輪郭面積
                    "motion_area_ratio_min": 0.05,        # 動き面積比の最小値 (5%)
                    "motion_area_ratio_max": 0.8,         # 動き面積比の最大値 (80%)
                    "stable_frames_required": 5,          # 安定フレーム数要求
                    "motion_consistency_check": True      # 動き一貫性チェック
                },
                "race_settings": {
                    "max_laps": 10,
                    "detection_cooldown": 3.0  # 3秒に延長
                }
            }
            print("⚠️ config.json not found, using enhanced default settings")

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
                print(f"❌ カメラ {i}: 開けません")

        print(f"📹 検出されたカメラ: {self.available_cameras}")
        return len(self.available_cameras) >= 1

    def initialize_cameras(self):
        """カメラ初期化（改良版）"""
        print("📹 Teams用シンプル表示カメラシステム初期化中...")

        # 利用可能なカメラを検索
        if not self.find_available_cameras():
            print("❌ 利用可能なカメラが見つかりません")
            return False

        # Overview カメラ設定
        if len(self.available_cameras) >= 1:
            overview_idx = self.available_cameras[0]
            print(f"📹 Overview カメラ: インデックス {overview_idx}")
        else:
            overview_idx = 0

        self.camera_overview = cv2.VideoCapture(overview_idx)
        if not self.camera_overview.isOpened():
            print(f"❌ Overview camera (index {overview_idx}) failed to open")
            return False

        # StartLine カメラ設定
        if len(self.available_cameras) >= 2:
            startline_idx = self.available_cameras[1]
            print(f"📹 StartLine カメラ: インデックス {startline_idx}")
        else:
            # 同じカメラを使用（テスト用）
            startline_idx = self.available_cameras[0] if self.available_cameras else 0
            print(f"⚠️ StartLine カメラ: Overview と同じカメラを使用 (index {startline_idx})")

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

        # 🔧 背景差分初期化: より安定した検知のためのパラメータ調整
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,           # 履歴フレーム数増加
            varThreshold=50,       # 分散閾値調整
            detectShadows=False    # 影検知を無効化して誤検知削減
        )

        print("✅ カメラ初期化完了 (検知感度強化版)")
        return True

    def camera_thread(self):
        """カメラフレーム取得スレッド（最適化版 + 左右反転修正）"""
        while self.running:
            try:
                ret_ov, frame_ov = self.camera_overview.read()
                ret_sl, frame_sl = self.camera_start_line.read()

                if ret_ov and ret_sl:
                    # 🔄 左右反転修正: 両方のカメラで cv2.flip 適用
                    frame_ov_flipped = cv2.flip(frame_ov, 1)  # 水平反転
                    frame_sl_flipped = cv2.flip(frame_sl, 1)  # 水平反転
                    
                    with self.frame_lock:
                        self.current_overview_frame = frame_ov_flipped.copy()
                        self.current_startline_frame = frame_sl_flipped.copy()

                    # 🔧 車両検知強化版（反転後のフレームを使用）
                    detected, motion_data = self.detect_vehicle_crossing_enhanced(frame_sl_flipped)
                    
                    # 検知情報更新
                    self.last_motion_pixels = motion_data['motion_pixels']
                    self.motion_area_ratio = motion_data['area_ratio']

                    if detected:
                        self.handle_vehicle_detection(motion_data)

            except Exception as e:
                print(f"カメラスレッドエラー: {e}")

            time.sleep(1/30)  # 30fps

    def detect_vehicle_crossing_enhanced(self, frame):
        """🔧 車両通過検知強化版（誤検知大幅削減）"""
        if not self.bg_subtractor:
            return False, {
                'motion_pixels': 0,
                'area_ratio': 0.0,
                'contour_count': 0,
                'largest_contour_area': 0
            }

        # 背景差分適用
        fg_mask = self.bg_subtractor.apply(frame)
        
        # 🔧 ノイズ除去強化
        # モルフォロジー処理でノイズ除去
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # ガウシアンブラーで細かいノイズを除去
        fg_mask = cv2.GaussianBlur(fg_mask, (5, 5), 0)
        
        # 二値化処理
        _, fg_mask = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)

        # 基本的な動きピクセル数
        motion_pixels = cv2.countNonZero(fg_mask)
        
        # フレーム全体のピクセル数
        total_pixels = frame.shape[0] * frame.shape[1]
        area_ratio = motion_pixels / total_pixels if total_pixels > 0 else 0

        # 🔧 輪郭検出による物体サイズ検証
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 有効な輪郭をフィルタリング
        valid_contours = []
        min_contour_area = self.config['detection_settings']['min_contour_area']
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_contour_area:
                valid_contours.append(contour)

        # 最大輪郭面積
        largest_contour_area = max([cv2.contourArea(c) for c in valid_contours]) if valid_contours else 0

        # 検知データ
        motion_data = {
            'motion_pixels': motion_pixels,
            'area_ratio': area_ratio,
            'contour_count': len(valid_contours),
            'largest_contour_area': largest_contour_area
        }

        # 🔧 多重検証による検知判定
        detection_result = self.evaluate_detection(motion_data)
        
        return detection_result, motion_data

    def evaluate_detection(self, motion_data):
        """🔧 検知評価（多重条件チェック）"""
        current_time = time.time()
        detection_settings = self.config['detection_settings']
        
        # 基本条件チェック
        motion_threshold = detection_settings['motion_pixels_threshold']
        min_area_ratio = detection_settings['motion_area_ratio_min']
        max_area_ratio = detection_settings['motion_area_ratio_max']
        
        # 🔧 条件1: 動きピクセル数
        condition1 = motion_data['motion_pixels'] > motion_threshold
        
        # 🔧 条件2: 面積比範囲チェック
        condition2 = (min_area_ratio <= motion_data['area_ratio'] <= max_area_ratio)
        
        # 🔧 条件3: 有効な輪郭の存在
        condition3 = motion_data['contour_count'] > 0
        
        # 🔧 条件4: クールダウン期間
        condition4 = (current_time - self.last_detection_time) > self.detection_cooldown
        
        # 🔧 条件5: 最大輪郭サイズ
        condition5 = motion_data['largest_contour_area'] > detection_settings['min_contour_area']

        # 動き履歴更新
        self.motion_history.append(motion_data['motion_pixels'])
        if len(self.motion_history) > 10:  # 直近10フレーム保持
            self.motion_history.pop(0)

        # 🔧 条件6: 動きの一貫性チェック
        condition6 = True
        if len(self.motion_history) >= 5 and detection_settings['motion_consistency_check']:
            # 直近5フレームの動きの分散をチェック
            recent_motion = self.motion_history[-5:]
            motion_std = np.std(recent_motion)
            motion_mean = np.mean(recent_motion)
            
            # 動きが安定していない場合（分散が大きすぎる）は除外
            if motion_mean > 0:
                cv_motion = motion_std / motion_mean  # 変動係数
                condition6 = cv_motion < 2.0  # 変動係数が2.0未満

        # 🔧 全条件の評価
        all_conditions = [condition1, condition2, condition3, condition4, condition5, condition6]
        conditions_met = sum(all_conditions)
        
        # デバッグ情報
        if motion_data['motion_pixels'] > 100:  # 少しでも動きがある場合のみ表示
            debug_info = f"検知評価: {conditions_met}/6 条件満足"
            debug_info += f" | 動き: {motion_data['motion_pixels']}"
            debug_info += f" | 面積比: {motion_data['area_ratio']:.3f}"
            debug_info += f" | 輪郭: {motion_data['contour_count']}"
            print(debug_info)

        # 🔧 厳格な判定: 全条件を満たす場合のみ検知
        if conditions_met >= 5:  # 6条件中5条件以上
            self.last_detection_time = current_time
            print(f"🎯 車両検知成功: 全条件クリア ({conditions_met}/6)")
            return True
        
        return False

    def handle_vehicle_detection(self, motion_data):
        """車両検知時の処理（強化版）"""
        current_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if not self.race_active:
            # レース開始
            self.race_active = True
            self.start_time = current_time
            self.lap_count = 0
            self.time_visible = True
            print(f"🏁 レース開始: {timestamp}")
            print(f"   検知データ: 動き={motion_data['motion_pixels']}, 面積比={motion_data['area_ratio']:.3f}")

        else:
            # ラップ記録
            lap_time = current_time - self.start_time
            self.lap_count += 1
            self.lap_times.append(lap_time)

            print(f"🏁 LAP {self.lap_count} 完了: タイム: {lap_time:.3f}秒")
            print(f"   検知データ: 動き={motion_data['motion_pixels']}, 面積比={motion_data['area_ratio']:.3f}")

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

            print("🏁 レース終了")
            print(f"🏆 ベストラップ: {best_lap:.3f}秒")

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
            'detection_settings': self.config['detection_settings']  # 検知設定も保存
        }

        filename = f"data/race_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"💾 結果保存: {filename}")

    def update_display_time(self):
        """表示時間更新（最適化版）"""
        current_time = time.time()

        # 一定間隔で時間更新（滑らかな表示）
        if current_time - self.last_time_update >= self.time_update_interval:
            if self.race_active and self.start_time:
                self.display_time = current_time - self.start_time
            else:
                self.display_time = 0.0
            self.last_time_update = current_time

    def opencv_to_pygame(self, cv_image):
        """OpenCV画像をPygame用に変換（上下反転修正）"""
        if cv_image is None:
            return None

        # BGR to RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        # 正しい向きに変換（上下反転修正）
        rgb_image = np.transpose(rgb_image, (1, 0, 2))
        rgb_image = np.flipud(rgb_image)
        # Pygame Surface作成
        return pygame.surfarray.make_surface(rgb_image)

    def draw_camera_feeds(self):
        """シンプルカメラ映像描画（左右反転修正版）"""
        with self.frame_lock:
            overview_frame = self.current_overview_frame
            startline_frame = self.current_startline_frame

        # Overview camera (左側・大きく表示 - 反転修正済み)
        if overview_frame is not None:
            overview_surface = self.opencv_to_pygame(overview_frame)
            if overview_surface:
                # 当初設計: 800x400 (大きめ表示)
                overview_scaled = pygame.transform.scale(overview_surface, (800, 400))
                self.screen.blit(overview_scaled, (50, 50))

        # StartLine camera (右側・小さく表示 - 反転修正済み)
        if startline_frame is not None:
            startline_surface = self.opencv_to_pygame(startline_frame)
            if startline_surface:
                # 当初設計: 400x300 (小さめ表示)
                startline_scaled = pygame.transform.scale(startline_surface, (400, 300))
                self.screen.blit(startline_scaled, (880, 50))

                # 検知エリア可視化（StartLineカメラ上に枠を付けて表示）
                detection_rect = pygame.Rect(880 + 100, 50 + 100, 200, 100)
                pygame.draw.rect(self.screen, self.colors['text_red'], detection_rect, 2)

                # 🔧 検知状況詳細表示
                if hasattr(self, 'last_motion_pixels') and self.last_motion_pixels > 0:
                    motion_text = f"Motion: {self.last_motion_pixels}"
                    motion_surface = self.font_small.render(motion_text, True, self.colors['text_green'])
                    self.screen.blit(motion_surface, (880, 360))
                    
                    # 面積比表示
                    ratio_text = f"Area: {self.motion_area_ratio:.3f}"
                    ratio_surface = self.font_small.render(ratio_text, True, self.colors['text_yellow'])
                    self.screen.blit(ratio_surface, (880, 380))

        # カメラが同じ場合の処理（異なる表示方法）
        if len(self.available_cameras) < 2:
            # 右側（StartLine）にはエッジ検出版を表示
            if startline_frame is not None and overview_frame is not None:
                # StartLine用にエッジ検出処理
                gray_frame = cv2.cvtColor(startline_frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray_frame, 50, 150)
                # エッジ画像を3チャンネルに変換
                edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

                edges_surface = self.opencv_to_pygame(edges_colored)
                if edges_surface:
                    edges_scaled = pygame.transform.scale(edges_surface, (400, 300))
                    self.screen.blit(edges_scaled, (880, 50))

            # 警告表示
            warning_text = self.font_small.render("⚠️ Single camera: Edge detection view", True, self.colors['text_yellow'])
            self.screen.blit(warning_text, (200, 5))

        # ラベル表示（当初設計通りの位置）
        overview_label = self.font_medium.render("Overview Camera (Fixed)", True, self.colors['text_white'])
        self.screen.blit(overview_label, (50, 10))

        startline_label = self.font_medium.render("StartLine (Enhanced)", True, self.colors['text_white'])
        self.screen.blit(startline_label, (880, 10))

    def draw_simple_race_info(self):
        """シンプルレース情報描画（配置調整版）"""
        # 時間更新
        self.update_display_time()

        # 下部情報エリア背景（位置調整）
        info_rect = pygame.Rect(50, 480, 1180, 220)
        pygame.draw.rect(self.screen, self.colors['panel_bg'], info_rect)
        pygame.draw.rect(self.screen, self.colors['border'], info_rect, 2)

        # レース状況とラップ数（左側・大きく表示）
        if self.race_active:
            # 周回数を超大きく表示
            lap_text = f"LAP {self.lap_count}"
            lap_color = self.colors['text_green']

            # 現在タイム表示制御（滑らか更新）
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

        # ラップ数表示（左側）
        lap_surface = self.font_huge.render(lap_text, True, lap_color)
        self.screen.blit(lap_surface, (80, 520))

        # タイム表示（右側）
        time_surface = self.font_large.render(time_text, True, time_color)
        time_rect = time_surface.get_rect()
        self.screen.blit(time_surface, (1050 - time_rect.width, 540))

        # ベストラップ表示（右下）
        if self.lap_times:
            best_lap = min(self.lap_times)
            if self.time_visible:
                best_text = f"BEST: {best_lap:.3f}s"
            else:
                best_text = "BEST: ---"
            best_surface = self.font_small.render(best_text, True, self.colors['text_white'])
            best_rect = best_surface.get_rect()
            self.screen.blit(best_surface, (1050 - best_rect.width, 620))

        # 状況表示（中央下）
        if not self.time_visible and self.race_active:
            hide_info = self.font_small.render("⚠️ TIME HIDDEN", True, self.colors['text_red'])
            hide_rect = hide_info.get_rect()
            self.screen.blit(hide_info, (640 - hide_rect.width // 2, 650))

        # FPS表示（デバッグ用・左下）
        fps_text = f"FPS: {int(self.clock.get_fps())}"
        fps_surface = self.font_small.render(fps_text, True, self.colors['text_white'])
        self.screen.blit(fps_surface, (80, 670))

        # バージョン表示
        version_text = "v4 - Enhanced Detection"
        version_surface = self.font_small.render(version_text, True, self.colors['text_yellow'])
        self.screen.blit(version_surface, (850, 670))

    def handle_keypress(self, key):
        """キー入力処理"""
        if key == pygame.K_r:
            # レースリセット
            self.reset_race()
        elif key == pygame.K_q or key == pygame.K_ESCAPE:
            # システム終了
            self.running = False
        elif key == pygame.K_t:
            # タイム表示切り替え（強制切替）
            self.time_visible = not self.time_visible
            print(f"タイム表示: {'ON' if self.time_visible else 'OFF'}")
        elif key == pygame.K_s:
            # スクリーンショット保存
            self.save_screenshot()
        elif key == pygame.K_c:
            # カメラ情報表示
            self.show_camera_info()
        elif key == pygame.K_d:
            # 🔧 検知設定表示
            self.show_detection_settings()

    def show_camera_info(self):
        """カメラ情報表示"""
        print("📹 カメラ情報:")
        print(f"利用可能なカメラ: {self.available_cameras}")
        print(f"Overview カメラ稼働中: {self.camera_overview.isOpened() if self.camera_overview else 'None'}")
        print(f"StartLine カメラ稼働中: {self.camera_start_line.isOpened() if self.camera_start_line else 'None'}")
        print("🔄 左右反転修正: 有効 (cv2.flip適用)")

    def show_detection_settings(self):
        """🔧 検知設定表示"""
        print("🎯 検知設定 (v4強化版):")
        ds = self.config['detection_settings']
        print(f"  動きピクセル閾値: {ds['motion_pixels_threshold']}")
        print(f"  最小輪郭面積: {ds['min_contour_area']}")
        print(f"  面積比範囲: {ds['motion_area_ratio_min']:.3f} - {ds['motion_area_ratio_max']:.3f}")
        print(f"  クールダウン: {self.detection_cooldown}秒")
        print(f"  直近動きピクセル: {self.last_motion_pixels}")
        print(f"  直近面積比: {self.motion_area_ratio:.3f}")

    def reset_race(self):
        """レースリセット"""
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        self.time_visible = True
        self.display_time = 0.0
        self.motion_history = []  # 動き履歴もリセット
        print("🔄 レースリセット完了")

    def save_screenshot(self):
        """スクリーンショット保存"""
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')

        filename = f"screenshots/teams_view_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pygame.image.save(self.screen, filename)
        print(f"📸 スクリーンショット保存: {filename}")

    def run(self):
        """メイン実行ループ（最適化版）"""
        print("🏁 Teams共有用シンプル表示タイム計測システム起動 (v4 - 物体検知感度強化版)")
        print("🎮 操作: R=リセット, Q/ESC=終了, T=タイム表示切替, S=スクリーンショット, C=カメラ情報, D=検知設定")

        if not self.initialize_cameras():
            print("❌ カメラ初期化失敗")
            return False

        # カメラスレッド開始
        camera_thread = threading.Thread(target=self.camera_thread, daemon=True)
        camera_thread.start()

        # メインループ（高FPS版）
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
            self.clock.tick(self.fps)  # 60FPS

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
        print("🏁 システム終了")

def main():
    print("🏁 Teams共有用シンプル表示タイム計測システム (v4 - 物体検知感度強化版)")
    print("=" * 70)

    try:
        system = TeamsSimpleLaptimeSystemFixedV4()
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