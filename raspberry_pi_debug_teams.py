# raspberry_pi_debug_teams.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5用デバッグヘルパー - teams_simple_laptime_fixed.py専用
ラズパイでの実行時の問題の診断と解決支援
"""

import cv2
import pygame
import subprocess
import sys
import time
import json
from pathlib import Path

class RaspberryPiTeamsDebugger:
    def __init__(self):
        self.debug_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_checks": {},
            "camera_tests": {},
            "display_tests": {},
            "recommendations": []
        }
    
    def log(self, message, level="INFO"):
        """ログ出力"""
        print(f"[{level}] {message}")
        
    def check_raspberry_pi_info(self):
        """Raspberry Pi 情報の確認"""
        self.log("🍓 Raspberry Pi システム情報を確認中...")
        
        try:
            # OS情報
            with open('/etc/os-release', 'r') as f:
                os_info = f.read()
            self.log(f"OS: {[line for line in os_info.split() if 'PRETTY_NAME' in line][0]}")
            
            # CPU情報
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = [line for line in f.readlines() if 'Model' in line]
                if cpu_info:
                    self.log(f"CPU: {cpu_info[0].strip()}")
            
            # メモリ情報
            with open('/proc/meminfo', 'r') as f:
                mem_total = [line for line in f.readlines() if 'MemTotal' in line][0]
                self.log(f"Memory: {mem_total.strip()}")
                
            self.debug_results["system_checks"]["raspberry_pi"] = True
            
        except Exception as e:
            self.log(f"⚠️ システム情報取得エラー: {e}", "WARNING")
            self.debug_results["system_checks"]["raspberry_pi"] = False
    
    def check_python_packages(self):
        """必要なPythonパッケージのチェック"""
        self.log("📦 Pythonパッケージをチェック中...")
        
        required_packages = {
            'cv2': 'opencv-python',
            'pygame': 'pygame', 
            'numpy': 'numpy',
            'threading': 'builtin',
            'json': 'builtin'
        }
        
        missing_packages = []
        
        for package, install_name in required_packages.items():
            try:
                if package == 'cv2':
                    import cv2
                    self.log(f"✅ OpenCV: {cv2.__version__}")
                elif package == 'pygame':
                    import pygame
                    self.log(f"✅ PyGame: {pygame.version.ver}")
                elif package == 'numpy':
                    import numpy
                    self.log(f"✅ NumPy: {numpy.__version__}")
                else:
                    __import__(package)
                    self.log(f"✅ {package}: OK")
                    
            except ImportError:
                missing_packages.append(install_name)
                self.log(f"❌ {package}: 見つかりません", "ERROR")
        
        if missing_packages:
            self.log(f"📥 不足パッケージをインストール: pip install {' '.join(missing_packages)}")
            self.debug_results["recommendations"].append(f"pip install {' '.join(missing_packages)}")
        
        self.debug_results["system_checks"]["packages"] = len(missing_packages) == 0
        return len(missing_packages) == 0
    
    def test_camera_detection(self):
        """カメラ検出テスト"""
        self.log("📹 カメラデバイスをテスト中...")
        
        available_cameras = []
        
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        available_cameras.append({
                            "index": i,
                            "resolution": f"{w}x{h}",
                            "working": True
                        })
                        self.log(f"✅ カメラ {i}: {w}x{h} - 動作OK")
                    else:
                        self.log(f"⚠️ カメラ {i}: 開けるがフレーム取得失敗")
                        available_cameras.append({
                            "index": i,
                            "working": False,
                            "error": "フレーム取得失敗"
                        })
                    cap.release()
                else:
                    if i < 3:  # 最初の3つだけログ出力
                        self.log(f"❌ カメラ {i}: 利用不可")
            except Exception as e:
                self.log(f"❌ カメラ {i}: エラー {e}")
        
        working_cameras = [cam for cam in available_cameras if cam.get("working", False)]
        self.log(f"📊 動作するカメラ数: {len(working_cameras)}")
        
        if len(working_cameras) < 2:
            self.log("⚠️ teams_simple_laptime_fixed.py は2台のカメラが推奨です", "WARNING")
            self.debug_results["recommendations"].append("USB Webカメラを追加するか、シングルカメラモードを使用")
        
        self.debug_results["camera_tests"] = {
            "available_cameras": available_cameras,
            "working_count": len(working_cameras)
        }
        
        return working_cameras
    
    def test_display_system(self):
        """ディスプレイシステムのテスト"""
        self.log("🖥️ ディスプレイシステムをテスト中...")
        
        # DISPLAY環境変数チェック
        import os
        display = os.environ.get('DISPLAY')
        self.log(f"DISPLAY環境変数: {display}")
        
        # PyGameディスプレイ初期化テスト
        try:
            pygame.init()
            # 小さなテストウィンドウ
            test_screen = pygame.display.set_mode((320, 240))
            pygame.display.set_caption("ディスプレイテスト")
            
            # 簡単な描画テスト
            test_screen.fill((0, 100, 0))
            font = pygame.font.Font(None, 36)
            text = font.render("Display Test OK", True, (255, 255, 255))
            test_screen.blit(text, (10, 100))
            pygame.display.flip()
            
            self.log("✅ PyGameディスプレイ: 初期化成功")
            
            # 2秒間表示
            time.sleep(2)
            pygame.quit()
            
            self.debug_results["display_tests"]["pygame"] = True
            
        except Exception as e:
            self.log(f"❌ PyGameディスプレイエラー: {e}", "ERROR")
            self.debug_results["display_tests"]["pygame"] = False
            self.debug_results["recommendations"].append("X11転送を有効化: ssh -X pi@raspberry_pi_ip")
    
    def create_minimal_test_script(self):
        """最小テストスクリプトの作成"""
        test_script = '''#!/usr/bin/env python3
"""
Raspberry Pi用最小カメラテスト - teams_simple_laptime_fixed.py用
"""
import cv2
import pygame
import time
import sys

def test_minimal_teams_system():
    print("🧪 Raspberry Pi最小テスト開始")
    
    # PyGame初期化
    try:
        pygame.init()
        screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption("Mini Test")
        print("✅ PyGame初期化成功")
    except Exception as e:
        print(f"❌ PyGame初期化失敗: {e}")
        return False
    
    # カメラテスト
    camera_working = False
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✅ カメラ {i}: 動作OK")
                camera_working = True
                
                # 10秒間表示テスト
                start_time = time.time()
                while time.time() - start_time < 10:
                    ret, frame = cap.read()
                    if ret:
                        # フレームサイズ調整
                        frame_resized = cv2.resize(frame, (640, 480))
                        
                        # OpenCV BGR to RGB 変換
                        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                        
                        # PyGameサーフェスに変換
                        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                        
                        # 描画
                        screen.blit(frame_surface, (0, 0))
                        
                        # テキスト追加
                        font = pygame.font.Font(None, 48)
                        text = font.render(f"Camera {i} Test", True, (255, 255, 255))
                        screen.blit(text, (10, 10))
                        
                        pygame.display.flip()
                        
                        # イベント処理
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                cap.release()
                                pygame.quit()
                                return True
                    
                    time.sleep(0.03)  # 約30fps
                
                cap.release()
                break
        else:
            print(f"❌ カメラ {i}: 利用不可")
    
    pygame.quit()
    
    if camera_working:
        print("✅ 最小テスト成功 - teams_simple_laptime_fixed.py実行可能")
        return True
    else:
        print("❌ カメラテスト失敗")
        return False

if __name__ == "__main__":
    success = test_minimal_teams_system()
    sys.exit(0 if success else 1)
'''
        
        script_path = "minimal_teams_test.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        # 実行権限付与
        import os
        os.chmod(script_path, 0o755)
        
        self.log(f"✅ 最小テストスクリプト作成: {script_path}")
        return script_path
    
    def generate_debug_report(self):
        """デバッグレポート生成"""
        report_file = f"raspberry_pi_teams_debug_{int(time.time())}.json"
        
        # 推奨事項の追加
        if self.debug_results["camera_tests"].get("working_count", 0) < 2:
            self.debug_results["recommendations"].extend([
                "USB Webカメラを2台接続することを推奨",
                "カメラがUSB 2.0ポートに接続されていることを確認",
                "sudo lsusb でカメラが認識されているか確認"
            ])
        
        if not self.debug_results["display_tests"].get("pygame", False):
            self.debug_results["recommendations"].extend([
                "SSH X11転送を有効化: ssh -X pi@192.168.x.x",
                "VNCを使用してリモートデスクトップ接続",
                "ローカルディスプレイ（HDMI）に接続して実行"
            ])
        
        # パフォーマンス関連
        self.debug_results["recommendations"].extend([
            "GPU メモリ分割を128MBに設定: sudo raspi-config",
            "カメラ解像度を640x480に制限してパフォーマンス向上",
            "不要なプロセスを終了してメモリを確保"
        ])
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.debug_results, f, indent=2, ensure_ascii=False)
        
        self.log(f"📄 デバッグレポート保存: {report_file}")
        return report_file
    
    def run_full_diagnosis(self):
        """完全診断の実行"""
        self.log("🔍 Raspberry Pi 5 - teams_simple_laptime_fixed.py 診断開始")
        self.log("=" * 60)
        
        # システム情報
        self.check_raspberry_pi_info()
        
        # パッケージチェック
        packages_ok = self.check_python_packages()
        
        # カメラテスト
        working_cameras = self.test_camera_detection()
        
        # ディスプレイテスト
        self.test_display_system()
        
        # テストスクリプト作成
        test_script = self.create_minimal_test_script()
        
        # レポート生成
        report_file = self.generate_debug_report()
        
        # 結果サマリー
        self.log("\n" + "=" * 60)
        self.log("🎯 診断結果サマリー")
        self.log("=" * 60)
        self.log(f"📦 パッケージ: {'OK' if packages_ok else 'NG'}")
        self.log(f"📹 動作カメラ数: {len(working_cameras)}")
        self.log(f"🖥️ ディスプレイ: {'OK' if self.debug_results['display_tests'].get('pygame') else 'NG'}")
        self.log(f"🧪 テストスクリプト: {test_script}")
        self.log(f"📄 詳細レポート: {report_file}")
        
        # 実行可能性判定
        if packages_ok and len(working_cameras) >= 1:
            self.log("✅ teams_simple_laptime_fixed.py実行可能")
            self.log("💡 次のステップ:")
            self.log(f"   1. {test_script} を実行してテスト")
            self.log("   2. teams_simple_laptime_fixed.py を実行")
        else:
            self.log("⚠️ 問題があります。レポートの推奨事項を確認してください")
        
        return {
            "packages_ok": packages_ok,
            "camera_count": len(working_cameras),
            "display_ok": self.debug_results["display_tests"].get("pygame", False),
            "report_file": report_file,
            "test_script": test_script
        }

def main():
    print("🍓 Raspberry Pi 5 Debug Helper for teams_simple_laptime_fixed.py")
    print("=" * 70)
    
    debugger = RaspberryPiTeamsDebugger()
    result = debugger.run_full_diagnosis()
    
    print("\n🎯 推奨実行順序:")
    print("1. 問題があれば修正")
    print("2. minimal_teams_test.py でテスト")
    print("3. teams_simple_laptime_fixed.py を実行")
    print("4. エラーが出たらデバッグレポートを確認")

if __name__ == "__main__":
    main()