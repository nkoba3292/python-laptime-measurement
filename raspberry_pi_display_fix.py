#!/usr/bin/env python3
"""
🔧 ラズパイディスプレイ診断ツール
teams_simple_laptime_fixed_v2.py の黒画面問題を診断
"""

import pygame
import cv2
import os
import sys
import time

def check_display_environment():
    """ディスプレイ環境の診断"""
    print("🖥️ ディスプレイ環境診断")
    print("=" * 40)
    
    # DISPLAY環境変数
    display = os.environ.get('DISPLAY')
    print(f"DISPLAY環境変数: {display}")
    
    # Wayland環境
    wayland = os.environ.get('WAYLAND_DISPLAY')
    print(f"WAYLAND_DISPLAY: {wayland}")
    
    # SSH接続確認
    ssh_client = os.environ.get('SSH_CLIENT')
    ssh_connection = os.environ.get('SSH_CONNECTION')
    if ssh_client or ssh_connection:
        print("⚠️ SSH接続で実行中 - X11転送が必要")
    else:
        print("✅ ローカル実行")

def test_pygame_modes():
    """PyGameディスプレイモードのテスト"""
    print("\n🎮 PyGameディスプレイモードテスト")
    print("=" * 40)
    
    try:
        pygame.init()
        
        # 利用可能なディスプレイ情報
        info = pygame.display.Info()
        print(f"画面解像度: {info.current_w}x{info.current_h}")
        print(f"色深度: {info.bitsize}bit")
        
        # ウィンドウモードテスト
        print("\n1. ウィンドウモードテスト...")
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Test Window")
        
        # 簡単な描画
        screen.fill((0, 100, 200))  # 青色
        font = pygame.font.Font(None, 72)
        text = font.render("Display Test", True, (255, 255, 255))
        screen.blit(text, (200, 250))
        pygame.display.flip()
        
        print("✅ ウィンドウモード成功 - 5秒間表示")
        time.sleep(5)
        
        pygame.quit()
        return True
        
    except Exception as e:
        print(f"❌ PyGameエラー: {e}")
        return False

def test_fullscreen_safe():
    """安全な全画面テスト"""
    print("\n🖥️ 安全な全画面テスト")
    print("=" * 40)
    
    try:
        pygame.init()
        
        # まずウィンドウモードで開始
        screen = pygame.display.set_mode((800, 600))
        
        print("ESCキーで終了、Fキーで全画面切り替え")
        print("3秒後に開始...")
        time.sleep(3)
        
        fullscreen = False
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_f:
                        # 全画面切り替え
                        if not fullscreen:
                            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            fullscreen = True
                            print("全画面モード")
                        else:
                            screen = pygame.display.set_mode((800, 600))
                            fullscreen = False
                            print("ウィンドウモード")
            
            # 描画
            screen.fill((50, 50, 50))
            
            # テキスト表示
            font = pygame.font.Font(None, 48)
            text1 = font.render("Display Test", True, (255, 255, 255))
            text2 = font.render("ESC: Quit, F: Fullscreen", True, (200, 200, 200))
            
            screen.blit(text1, (50, 200))
            screen.blit(text2, (50, 300))
            
            pygame.display.flip()
            clock.tick(30)
        
        pygame.quit()
        return True
        
    except Exception as e:
        print(f"❌ 全画面テストエラー: {e}")
        pygame.quit()
        return False

def test_camera_basic():
    """基本カメラテスト"""
    print("\n📹 基本カメラテスト")
    print("=" * 40)
    
    cameras_found = []
    
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                cameras_found.append(i)
                print(f"✅ カメラ {i}: 動作OK")
            else:
                print(f"❌ カメラ {i}: フレーム取得失敗")
            cap.release()
        else:
            print(f"❌ カメラ {i}: 開けません")
    
    return cameras_found

def create_fixed_version():
    """修正版v2の作成"""
    fixed_code = '''#!/usr/bin/env python3
"""
🔧 ラズパイ修正版: 黒画面問題対応版
- ウィンドウモードでの起動オプション
- ESCキーでの緊急終了
- ディスプレイエラーハンドリング
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
    def __init__(self, windowed_mode=False):
        self.windowed_mode = windowed_mode
        
        # 🖥️ ディスプレイ設定（安全モード対応）
        try:
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            
            print(f"🖥️ 検出された画面解像度: {self.screen_width}x{self.screen_height}")
            
            # ディスプレイモード選択
            if self.windowed_mode or os.environ.get('SSH_CLIENT'):
                # ウィンドウモード（SSH接続時は強制）
                self.screen_width = min(1280, self.screen_width - 100)
                self.screen_height = min(720, self.screen_height - 100)
                self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
                print(f"🪟 ウィンドウモード: {self.screen_width}x{self.screen_height}")
            else:
                # 全画面モード
                self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
                print("🖥️ 全画面モード")
                
            pygame.display.set_caption("🏁 Lap Timer - Fixed Version")
            
        except Exception as e:
            print(f"❌ ディスプレイ初期化エラー: {e}")
            print("フォールバックモードで起動...")
            self.screen_width = 800
            self.screen_height = 600
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        # 色定義
        self.colors = {
            'background': (15, 15, 25),
            'text_white': (255, 255, 255),
            'text_green': (0, 255, 100),
            'text_yellow': (255, 255, 50),
            'text_red': (255, 80, 80),
            'panel_bg': (40, 40, 60),
            'border': (80, 80, 100)
        }

        # フォント設定（安全版）
        font_scale = min(self.screen_width / 1920, self.screen_height / 1080, 1.0)
        
        try:
            self.font_huge = pygame.font.Font(None, max(72, int(120 * font_scale)))
            self.font_large = pygame.font.Font(None, max(48, int(80 * font_scale)))
            self.font_medium = pygame.font.Font(None, max(36, int(48 * font_scale)))
            self.font_small = pygame.font.Font(None, max(24, int(32 * font_scale)))
        except:
            # システムフォント使用
            self.font_huge = pygame.font.SysFont('arial', max(72, int(120 * font_scale)), bold=True)
            self.font_large = pygame.font.SysFont('arial', max(48, int(80 * font_scale)), bold=True)
            self.font_medium = pygame.font.SysFont('arial', max(36, int(48 * font_scale)))
            self.font_small = pygame.font.SysFont('arial', max(24, int(32 * font_scale)))

        # システム状態
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = 30
        
        # カメラ設定
        self.camera_overview = None
        self.camera_start_line = None
        self.current_overview_frame = None
        self.current_startline_frame = None
        self.frame_lock = threading.Lock()
        
        # レース状態
        self.race_active = False
        self.lap_count = 0
        self.start_time = None
        self.lap_times = []
        
        print(f"🎨 フォントスケール: {font_scale:.2f}")
        print("⚠️ ESCキーで緊急終了、Fキーで全画面切り替え")

    def initialize_cameras(self):
        """カメラ初期化"""
        print("📹 カメラ初期化中...")
        
        try:
            # カメラ0をテスト
            self.camera_overview = cv2.VideoCapture(0)
            if self.camera_overview.isOpened():
                print("✅ Overview カメラ: OK")
            else:
                print("❌ Overview カメラ: 失敗")
                return False
            
            # カメラ1をテスト
            self.camera_start_line = cv2.VideoCapture(1)
            if not self.camera_start_line.isOpened():
                print("⚠️ StartLine カメラ: Overview と同じカメラを使用")
                self.camera_start_line = cv2.VideoCapture(0)
            else:
                print("✅ StartLine カメラ: OK")
            
            # カメラ設定
            for camera in [self.camera_overview, self.camera_start_line]:
                if camera and camera.isOpened():
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            return True
            
        except Exception as e:
            print(f"❌ カメラ初期化エラー: {e}")
            return False

    def capture_frames(self):
        """フレーム取得"""
        while self.running:
            try:
                if self.camera_overview and self.camera_start_line:
                    ret1, frame1 = self.camera_overview.read()
                    ret2, frame2 = self.camera_start_line.read()

                    if ret1 and ret2:
                        # ミラー処理
                        frame1 = cv2.flip(frame1, 1)
                        frame2 = cv2.flip(frame2, 1)

                        with self.frame_lock:
                            self.current_overview_frame = frame1.copy()
                            self.current_startline_frame = frame2.copy()

                time.sleep(0.03)  # 約30fps
            except Exception as e:
                print(f"⚠️ フレーム取得エラー: {e}")
                time.sleep(0.1)

    def draw_interface(self):
        """インターフェース描画"""
        self.screen.fill(self.colors['background'])

        # 基本情報表示
        title_text = self.font_large.render("🏁 Lap Timer (Fixed)", True, self.colors['text_green'])
        self.screen.blit(title_text, (20, 20))
        
        status_text = f"Resolution: {self.screen_width}x{self.screen_height}"
        status_surface = self.font_small.render(status_text, True, self.colors['text_white'])
        self.screen.blit(status_surface, (20, 80))
        
        mode_text = "Windowed Mode" if self.windowed_mode else "Fullscreen Mode"
        mode_surface = self.font_small.render(mode_text, True, self.colors['text_yellow'])
        self.screen.blit(mode_surface, (20, 110))

        # カメラフレーム表示
        if self.current_overview_frame is not None:
            with self.frame_lock:
                try:
                    # フレームサイズ調整
                    camera_width = min(400, self.screen_width // 3)
                    camera_height = min(300, self.screen_height // 3)
                    
                    # Overview カメラ
                    overview_resized = cv2.resize(self.current_overview_frame, (camera_width, camera_height))
                    overview_rgb = cv2.cvtColor(overview_resized, cv2.COLOR_BGR2RGB)
                    overview_surface = pygame.surfarray.make_surface(overview_rgb.swapaxes(0, 1))
                    self.screen.blit(overview_surface, (20, 150))
                    
                    # カメララベル
                    cam_label = self.font_small.render("📹 Camera View", True, self.colors['text_white'])
                    self.screen.blit(cam_label, (25, 155))
                    
                except Exception as e:
                    error_text = f"Camera Error: {e}"
                    error_surface = self.font_small.render(error_text, True, self.colors['text_red'])
                    self.screen.blit(error_surface, (20, 150))

        # 操作説明
        help_y = self.screen_height - 100
        help_texts = [
            "ESC: 終了",
            "F: 全画面切り替え",
            "SPACE: テストラップ"
        ]
        
        for i, text in enumerate(help_texts):
            help_surface = self.font_small.render(text, True, self.colors['text_white'])
            self.screen.blit(help_surface, (20, help_y + i * 25))

    def run(self):
        """メインループ"""
        print("🚀 ラップタイマー開始")
        print("=" * 50)

        # カメラ初期化
        camera_ok = self.initialize_cameras()
        if camera_ok:
            # カメラスレッド開始
            camera_thread = threading.Thread(target=self.capture_frames, daemon=True)
            camera_thread.start()
            print("✅ カメラスレッド開始")
        else:
            print("⚠️ カメラなしで続行")

        print("✅ システム準備完了")

        # メインループ
        try:
            while self.running:
                # イベント処理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            print("ESCキーで終了")
                            self.running = False
                        elif event.key == pygame.K_f:
                            # 全画面切り替え
                            if self.windowed_mode:
                                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                                self.windowed_mode = False
                                print("全画面モードに切り替え")
                            else:
                                self.screen = pygame.display.set_mode((1280, 720))
                                self.windowed_mode = True
                                print("ウィンドウモードに切り替え")
                        elif event.key == pygame.K_SPACE:
                            print("🔘 テストラップ")

                # 画面描画
                self.draw_interface()
                pygame.display.flip()

                # FPS制御
                self.clock.tick(self.fps)

        except KeyboardInterrupt:
            print("\\nCtrl+C で中断")
        except Exception as e:
            print(f"❌ 実行エラー: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """終了処理"""
        print("🧹 終了処理中...")
        
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
    print("🍓 Raspberry Pi Lap Timer (Fixed Version)")
    print("=" * 60)
    
    # 引数確認
    windowed = '--windowed' in sys.argv or '-w' in sys.argv
    
    if windowed:
        print("🪟 ウィンドウモードで起動")
    
    try:
        system = TeamsSimpleLaptimeSystemFixed(windowed_mode=windowed)
        system.run()
    except KeyboardInterrupt:
        print("\\n🛑 Ctrl+C で中断されました")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''
    
    with open('teams_simple_laptime_fixed_v2_safe.py', 'w', encoding='utf-8') as f:
        f.write(fixed_code)
    
    print("✅ 修正版作成: teams_simple_laptime_fixed_v2_safe.py")

def main():
    """診断メイン"""
    print("🍓 Raspberry Pi ディスプレイ診断ツール")
    print("=" * 50)
    
    # 環境診断
    check_display_environment()
    
    # PyGameテスト
    pygame_ok = test_pygame_modes()
    
    if pygame_ok:
        # 全画面テスト
        print("\\n全画面テストを実行しますか？ (y/N): ", end="")
        try:
            if input().lower() == 'y':
                test_fullscreen_safe()
        except KeyboardInterrupt:
            print("\\nテスト中断")
    
    # カメラテスト
    cameras = test_camera_basic()
    
    # 修正版作成
    create_fixed_version()
    
    # 結果サマリー
    print("\\n" + "=" * 50)
    print("🎯 診断結果サマリー")
    print("=" * 50)
    print(f"🎮 PyGame: {'OK' if pygame_ok else 'NG'}")
    print(f"📹 カメラ数: {len(cameras)}")
    print(f"✅ 修正版作成: teams_simple_laptime_fixed_v2_safe.py")
    
    print("\\n💡 推奨実行方法:")
    print("1. ウィンドウモード: python3 teams_simple_laptime_fixed_v2_safe.py --windowed")
    print("2. 全画面モード: python3 teams_simple_laptime_fixed_v2_safe.py")
    print("3. SSH経由: ssh -X pi@ip && python3 teams_simple_laptime_fixed_v2_safe.py --windowed")

if __name__ == "__main__":
    main()