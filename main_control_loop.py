# main_control_loop.py
# -*- coding: utf-8 -*-
"""
統合メインシステム - 走行モード選択 → IMUキャリブレーション → レース実行
"""
import json
import time
import os
import sys
from datetime import datetime

# IMUキャリブレーションシステムをインポート
try:
    from imu_calibration_vehicle_footprint import IMUCalibrationSystem
    CALIBRATION_AVAILABLE = True
except ImportError:
    CALIBRATION_AVAILABLE = False
    print("⚠️ Warning: IMU calibration system not available")

class MainControlSystem:
    def __init__(self):
        # 走行モード定義（waypoint_editor_multi_mode.pyと同じ）
        self.DRIVING_MODES = {
            'qualifying': {'name': 'Qualifying', 'file': 'waypoints_qualifying.json'},
            'qualifying_backup': {'name': 'Qualifying Backup', 'file': 'waypoints_qualifying_backup.json'},
            'final': {'name': 'Final Race', 'file': 'waypoints_final.json'},
            'final_backup': {'name': 'Final Backup', 'file': 'waypoints_final_backup.json'}
        }
        
        self.selected_mode = None
        self.waypoints = []
        self.calibration_data = None
        self.imu_offset = 0.0
        
        # システム状態
        self.system_ready = False
        self.calibration_completed = False
        
    def display_startup_banner(self):
        """システム起動時のバナー表示"""
        print("\n" + "="*70)
        print("🏁 AUTONOMOUS RACING SYSTEM - MAIN CONTROL")
        print("="*70)
        print("System Features:")
        print("• 4-Mode Waypoint Racing (Qualifying/Final + Backup)")
        print("• IMU Calibration Integration")
        print("• Real-time Race Control")
        print("• Safety & Monitoring")
        print(f"Calibration System: {'✅ Available' if CALIBRATION_AVAILABLE else '❌ Not Available'}")
        print("="*70)
    
    def select_driving_mode(self):
        """走行モード選択"""
        print("\n📋 DRIVING MODE SELECTION")
        print("="*50)
        
        # 利用可能なモード表示
        mode_list = []
        for i, (mode_key, mode_info) in enumerate(self.DRIVING_MODES.items(), 1):
            file_exists = os.path.exists(mode_info['file'])
            status = "✅ Ready" if file_exists else "❌ No Data"
            print(f"  {i}. {mode_info['name']} - {status}")
            mode_list.append(mode_key)
        
        # モード選択
        while True:
            try:
                print(f"\nSelect mode (1-{len(mode_list)}): ", end="")
                choice = int(input())
                if 1 <= choice <= len(mode_list):
                    selected_key = mode_list[choice - 1]
                    self.selected_mode = selected_key
                    
                    # Waypointファイル読み込み
                    waypoint_file = self.DRIVING_MODES[selected_key]['file']
                    if self.load_waypoints(waypoint_file):
                        print(f"✅ Mode Selected: {self.DRIVING_MODES[selected_key]['name']}")
                        print(f"📍 Waypoints Loaded: {len(self.waypoints)} points")
                        return True
                    else:
                        print(f"❌ Failed to load waypoints from {waypoint_file}")
                        continue
                else:
                    print("❌ Invalid selection. Please try again.")
            except ValueError:
                print("❌ Please enter a number.")
            except KeyboardInterrupt:
                print("\n🛑 Operation cancelled.")
                return False
    
    def load_waypoints(self, filename):
        """Waypointファイル読み込み"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.waypoints = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Error loading waypoints: {e}")
            return False
    
    def run_imu_calibration(self):
        """IMUキャリブレーション実行"""
        if not CALIBRATION_AVAILABLE:
            print("❌ IMU Calibration system not available")
            return False
        
        print("\n🎯 IMU CALIBRATION")
        print("="*50)
        print("📡 Starting IMU calibration system...")
        print("📋 Instructions:")
        print("  1. Position vehicle at Pos 1 (red footprint)")  
        print("  2. Click 'Measure IMU 1' button")
        print("  3. Move to Pos 2 (blue footprint)")
        print("  4. Click 'Measure IMU 2' button") 
        print("  5. Click 'Save Results' to complete")
        print("\n🔄 Launching calibration interface...")
        
        try:
            # IMUキャリブレーションシステム実行
            calibration_system = IMUCalibrationSystem()
            calibration_system.run_calibration_system()
            
            # キャリブレーション完了後、ファイル読み込み
            return self.load_calibration_data()
            
        except Exception as e:
            print(f"❌ Calibration error: {e}")
            return False
    
    def load_calibration_data(self):
        """キャリブレーションデータ読み込み"""
        calibration_files = ["imu_custom_calib.json"]
        
        for filename in calibration_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.calibration_data = json.load(f)
                
                if self.calibration_data.get('validation', {}).get('is_valid', False):
                    self.imu_offset = self.calibration_data.get('calculated_offset', 0.0)
                    print(f"✅ Calibration loaded: Offset = {self.imu_offset:.2f}°")
                    self.calibration_completed = True
                    return True
                else:
                    print(f"⚠️ Calibration validation failed: {self.calibration_data.get('validation', {}).get('message', 'Unknown error')}")
                    
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"❌ Error reading calibration: {e}")
        
        print("❌ No valid calibration data found")
        return False
    
    def system_status_check(self):
        """システム状態確認"""
        print("\n🔍 SYSTEM STATUS CHECK")
        print("="*50)
        
        # 走行モード確認
        mode_status = "✅ Ready" if self.selected_mode else "❌ Not Selected"
        waypoint_status = f"✅ {len(self.waypoints)} points" if self.waypoints else "❌ No Data"
        
        # キャリブレーション確認
        calib_status = "✅ Completed" if self.calibration_completed else "❌ Required"
        offset_info = f"({self.imu_offset:.2f}°)" if self.calibration_completed else ""
        
        print(f"📋 Driving Mode: {mode_status}")
        if self.selected_mode:
            print(f"   → {self.DRIVING_MODES[self.selected_mode]['name']}")
        print(f"📍 Waypoints: {waypoint_status}")
        print(f"🎯 IMU Calibration: {calib_status} {offset_info}")
        
        # システム準備完了判定
        self.system_ready = (self.selected_mode is not None and 
                           len(self.waypoints) > 0 and 
                           self.calibration_completed)
        
        status_icon = "🟢" if self.system_ready else "🔴"
        status_text = "READY FOR RACING" if self.system_ready else "SETUP INCOMPLETE"
        
        print(f"\n{status_icon} System Status: {status_text}")
        return self.system_ready
    
    def wait_for_race_start(self):
        """レース開始待機"""
        if not self.system_ready:
            print("❌ System not ready for racing")
            return False
        
        print("\n🏁 RACE START PREPARATION")
        print("="*50)
        print("📋 Pre-race Checklist:")
        print(f"   ✅ Mode: {self.DRIVING_MODES[self.selected_mode]['name']}")
        print(f"   ✅ Waypoints: {len(self.waypoints)} loaded")
        print(f"   ✅ IMU Offset: {self.imu_offset:.2f}°")
        print("\n🚗 Vehicle Positioning:")
        print("   1. Place vehicle at START position")
        print("   2. Ensure clear racing path")
        print("   3. Check battery level")
        print("   4. Verify all systems operational")
        
        print(f"\n⏳ System ready. Press ENTER to start racing...")
        
        try:
            input()  # Enter待機
            return True
        except KeyboardInterrupt:
            print("\n🛑 Race start cancelled.")
            return False
    
    def run_race(self):
        """レース実行（メインループ）"""
        print("\n🏁 RACE STARTED!")
        print("="*50)
        print(f"🎯 Mode: {self.DRIVING_MODES[self.selected_mode]['name']}")
        print(f"📍 Following {len(self.waypoints)} waypoints")
        print(f"🧭 IMU Offset: {self.imu_offset:.2f}°")
        
        race_start_time = time.time()
        
        # レースループ（実装例）
        try:
            for i, waypoint in enumerate(self.waypoints):
                elapsed = time.time() - race_start_time
                
                # Waypoint情報表示
                world_x = waypoint.get('x', 0) * 0.05 - 3.2  # グリッド→ワールド座標変換例
                world_y = waypoint.get('y', 0) * 0.05 - 1.5
                target_speed = waypoint.get('v', 100)
                target_yaw = waypoint.get('yaw', 0)
                
                print(f"🎯 WP{i+1:3d}: ({world_x:5.1f}, {world_y:5.1f}) "
                      f"Speed:{target_speed:6.1f} Yaw:{target_yaw:6.1f}° "
                      f"Time:{elapsed:6.1f}s")
                
                # ここに実際の制御ロジックを実装
                # - IMU読み取り + オフセット補正
                # - モーター制御
                # - センサー監視
                # - Pure Pursuit アルゴリズム等
                
                time.sleep(0.1)  # 制御周期
                
                # 安全停止チェック（Ctrl+C）
                # 実際には緊急停止センサー等も監視
                
        except KeyboardInterrupt:
            print(f"\n🛑 RACE STOPPED (Manual)")
            
        except Exception as e:
            print(f"\n❌ RACE ERROR: {e}")
            
        finally:
            # レース終了処理
            total_time = time.time() - race_start_time
            print(f"\n🏁 RACE COMPLETED")
            print(f"   Total Time: {total_time:.1f} seconds")
            print(f"   Waypoints: {len(self.waypoints)} processed")
            print(f"   Mode: {self.DRIVING_MODES[self.selected_mode]['name']}")
    
    def main_loop(self):
        """メインシステムループ"""
        self.display_startup_banner()
        
        try:
            # ① 走行モード選択
            if not self.select_driving_mode():
                print("🛑 System startup cancelled.")
                return
            
            # ② IMUキャリブレーション
            print(f"\n🎯 Ready for IMU calibration...")
            if not self.run_imu_calibration():
                print("❌ Calibration required for racing.")
                return
            
            # ③ システム状態確認
            if not self.system_status_check():
                print("❌ System setup incomplete.")
                return
            
            # ④ レース開始待機
            if not self.wait_for_race_start():
                print("🛑 Race cancelled.")
                return
            
            # ⑤ レース実行
            self.run_race()
            
        except Exception as e:
            print(f"\n❌ System Error: {e}")
        
        finally:
            print("\n📴 Main Control System shutdown.")

def main():
    """メイン実行関数"""
    system = MainControlSystem()
    system.main_loop()

if __name__ == "__main__":
    main()