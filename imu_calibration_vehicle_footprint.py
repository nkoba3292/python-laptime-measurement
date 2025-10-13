# imu_calibration_vehicle_footprint.py
# -*- coding: utf-8 -*-
"""
waypoint_editor_multi_mode.pyベースのIMUキャリブレーションシステム
車両フットプリント（180mm×350mm）を描画してIMU測定を行う
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
from matplotlib.widgets import Button
import json
import math
import numpy as np
from datetime import datetime

# コースマップデータ（内部実装 - cource_map依存を解決）
# 10m x 10m のサンプルコース
x_min, x_max = -2.0, 8.0
y_min, y_max = -1.0, 9.0
resolution = 0.05  # 5cm/pixel

# グリッド作成
grid_width = int((x_max - x_min) / resolution)
grid_height = int((y_max - y_min) / resolution)
grid_matrix = np.zeros((grid_height, grid_width))

# 座標変換関数
def world_to_grid(world_x, world_y):
    """ワールド座標をグリッド座標に変換"""
    grid_x = int((world_x - x_min) / resolution)
    grid_y = int((world_y - y_min) / resolution)
    return grid_x, grid_y

def grid_to_world(grid_x, grid_y):
    """グリッド座標をワールド座標に変換"""
    world_x = grid_x * resolution + x_min
    world_y = grid_y * resolution + y_min
    return world_x, world_y

# コース要素定義
obstacles = [
    {"start": (1.0, 2.0), "end": (2.0, 3.0)},
    {"start": (4.0, 5.0), "end": (5.0, 6.0)},
    {"start": (6.0, 1.0), "end": (7.0, 2.0)}
]

start_lines = [
    {"start": (0.0, 4.0), "end": (1.0, 4.0)}
]

pylons = [
    {"pos": (3.0, 3.0)},
    {"pos": (5.0, 7.0)},
    {"pos": (7.0, 4.0)}
]

# グリッドに障害物を描画
for obs in obstacles:
    x0, y0 = obs["start"]
    x1, y1 = obs["end"]
    gx0, gy0 = world_to_grid(x0, y0)
    gx1, gy1 = world_to_grid(x1, y1)
    for gy in range(min(gy0, gy1), max(gy0, gy1) + 1):
        for gx in range(min(gx0, gx1), max(gx0, gx1) + 1):
            if 0 <= gx < grid_width and 0 <= gy < grid_height:
                grid_matrix[gy, gx] = 1

# 文字化け完全修正 - 英語表示に変更
plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class IMUCalibrationSystem:
    def __init__(self):
        # 車両フットプリント設定（メートル単位）
        self.vehicle_width = 0.180   # 180mm
        self.vehicle_length = 0.350  # 350mm
        
        # 測定データ
        self.measurement_points = []
        self.current_measurement = 1  # 1 or 2
        self.max_measurements = 2
        
        # 車両フットプリント位置設定（後でパラメータ化）
        self.footprint_positions = [
            {"x": 2.0, "y": 4.0, "yaw": 0.0},    # Position 1
            {"x": -1.0, "y": 6.0, "yaw": 45.0}   # Position 2
        ]
        
        # プロット要素
        self.fig = None
        self.ax = None
        self.vehicle_footprints = []
        self.measurement_texts = []
        
        # IMU mockup mode
        self.mock_mode = True
        
    def setup_plot(self):
        """waypoint_editor_multi_mode.pyと同じ高品質プロット設定"""
        self.fig, self.ax = plt.subplots(figsize=(14, 10), dpi=100)
        plt.subplots_adjust(bottom=0.20, left=0.12, right=0.98, top=0.95)
        
        # 背景グリッド（正しいワールド座標で表示）
        self.ax.imshow(grid_matrix, cmap="Greys", origin="lower", 
                      extent=[x_min, x_max, y_min, y_max], alpha=0.7)
        
        # 軸設定：正しいアスペクト比と範囲（ワールド座標）
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(x_min - 0.2, x_max + 0.2)
        self.ax.set_ylim(y_min - 0.2, y_max + 0.2)
        
        # 軸ラベル（ワールド座標表示）
        self.ax.set_xlabel(f'X [meters] - Course Width: {x_max-x_min:.1f}m', fontsize=14, fontweight='bold')
        self.ax.set_ylabel(f'Y [meters] - Course Height: {y_max-y_min:.1f}m', fontsize=14, fontweight='bold')
        self.ax.set_title('IMU Calibration System - Vehicle Footprint Method', fontsize=16, fontweight='bold')
        
        # 障害物描画（ワールド座標）
        for obs in obstacles:
            x0, y0 = obs["start"]
            x1, y1 = obs["end"]
            left = min(x0, x1)
            bottom = min(y0, y1)
            width = abs(x1 - x0)
            height = abs(y1 - y0)
            rect = Rectangle((left, bottom), width, height, 
                           color="lightgreen", alpha=0.6, edgecolor='green', linewidth=2)
            self.ax.add_patch(rect)
        
        # スタートライン描画（ワールド座標）
        for line_def in start_lines:
            x0, y0 = line_def["start"]
            x1, y1 = line_def["end"]
            self.ax.plot([x0, x1], [y0, y1], "b-", linewidth=4, alpha=0.8, label='Start Lines')
        
        # パイロン描画（ワールド座標）
        for p in pylons:
            x, y = p["pos"]
            circ = Circle((x, y), radius=0.1, color="darkorange", alpha=0.9, 
                         edgecolor='red', linewidth=2)
            self.ax.add_patch(circ)
    
    def draw_vehicle_footprints(self):
        """車両フットプリント（180mm×350mm長方形）を描画"""
        for i, pos in enumerate(self.footprint_positions):
            x_center = pos["x"]
            y_center = pos["y"]
            yaw_deg = pos["yaw"]
            yaw_rad = math.radians(yaw_deg)
            
            # 長方形の角を計算（車両中心基準）
            half_length = self.vehicle_length / 2
            half_width = self.vehicle_width / 2
            
            # 回転前の長方形の角（ローカル座標）
            corners_local = np.array([
                [-half_length, -half_width],  # 後左
                [half_length, -half_width],   # 前左
                [half_length, half_width],    # 前右
                [-half_length, half_width]    # 後右
            ])
            
            # 回転行列を適用
            cos_yaw = math.cos(yaw_rad)
            sin_yaw = math.sin(yaw_rad)
            rotation_matrix = np.array([[cos_yaw, -sin_yaw], [sin_yaw, cos_yaw]])
            
            # 回転後の座標計算
            corners_rotated = corners_local @ rotation_matrix.T
            corners_world = corners_rotated + np.array([x_center, y_center])
            
            # 長方形描画
            color = 'red' if i == self.current_measurement - 1 else 'blue'
            alpha = 0.8 if i == self.current_measurement - 1 else 0.4
            
            # Polygon として描画
            footprint = Polygon(corners_world, closed=True, 
                              facecolor=color, alpha=alpha, edgecolor='black', linewidth=2)
            self.ax.add_patch(footprint)
            self.vehicle_footprints.append(footprint)
            
            # 位置ラベル
            label = f"Pos {i+1}\n({x_center:.1f}, {y_center:.1f})\nYaw: {yaw_deg:.1f}°"
            text = self.ax.text(x_center, y_center, label, 
                              ha='center', va='center', fontsize=10, fontweight='bold',
                              bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            self.measurement_texts.append(text)
            
            # 車両前方向矢印
            arrow_length = 0.4
            dx = arrow_length * math.cos(yaw_rad)
            dy = arrow_length * math.sin(yaw_rad)
            self.ax.arrow(x_center, y_center, dx, dy, 
                         head_width=0.08, head_length=0.12, 
                         fc=color, ec='black', alpha=0.9, linewidth=1.5)
    
    def setup_buttons(self):
        """コントロールボタンの設定"""
        # Measure IMU ボタン
        ax_measure = plt.axes([0.15, 0.05, 0.15, 0.05])
        self.button_measure = Button(ax_measure, f"Measure IMU {self.current_measurement}")
        self.button_measure.on_clicked(self.measure_imu)
        
        # Save ボタン
        ax_save = plt.axes([0.35, 0.05, 0.12, 0.05])
        self.button_save = Button(ax_save, "Save Results")
        self.button_save.on_clicked(self.save_calibration)
        
        # Reset ボタン
        ax_reset = plt.axes([0.52, 0.05, 0.12, 0.05])
        self.button_reset = Button(ax_reset, "Reset All")
        self.button_reset.on_clicked(self.reset_measurements)
        
        # Status text
        self.status_text = self.ax.text(0.02, 0.98, "Ready for measurement", 
                                       transform=self.ax.transAxes, 
                                       fontsize=12, fontweight='bold',
                                       bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8),
                                       verticalalignment='top')
    
    def mock_imu_measurement(self):
        """IMU測定のモック（実際のBNO055実装時に置き換え）"""
        import random
        # フットプリント角度に基づいたリアルな測定値をシミュレート
        expected_yaw = self.footprint_positions[self.current_measurement - 1]["yaw"]
        # ±5度のランダムノイズを追加
        noise = random.uniform(-5.0, 5.0)
        measured_yaw = expected_yaw + noise
        
        # 0-360度範囲に正規化
        while measured_yaw < 0:
            measured_yaw += 360
        while measured_yaw >= 360:
            measured_yaw -= 360
            
        return measured_yaw
    
    def measure_imu(self, event):
        """IMU測定実行"""
        if self.current_measurement > self.max_measurements:
            self.update_status("All measurements completed. Click Save Results.")
            return
        
        # IMU値測定
        if self.mock_mode:
            measured_yaw = self.mock_imu_measurement()
        else:
            # 実際のBNO055測定コードをここに追加
            measured_yaw = self.mock_imu_measurement()
        
        # 測定結果を保存
        pos_data = self.footprint_positions[self.current_measurement - 1].copy()
        pos_data["measured_yaw"] = measured_yaw
        pos_data["measurement_time"] = datetime.now().isoformat()
        self.measurement_points.append(pos_data)
        
        # 測定結果を画面に表示
        self.display_measurement_result(measured_yaw)
        
        # 次の測定へ
        self.current_measurement += 1
        if self.current_measurement <= self.max_measurements:
            self.button_measure.label.set_text(f"Measure IMU {self.current_measurement}")
            self.update_status(f"Measurement {self.current_measurement-1} completed. Position vehicle at Pos {self.current_measurement}.")
            self.update_vehicle_highlights()
        else:
            self.button_measure.label.set_text("All Complete")
            self.update_status("All measurements completed! Review and click Save Results.")
        
        self.fig.canvas.draw()
    
    def display_measurement_result(self, measured_yaw):
        """測定結果をプロット上に表示"""
        pos = self.footprint_positions[self.current_measurement - 1]
        expected_yaw = pos["yaw"]
        error = measured_yaw - expected_yaw
        
        # エラー正規化（-180 to +180）
        while error > 180:
            error -= 360
        while error <= -180:
            error += 360
        
        # 結果表示テキスト
        result_text = f"IMU {self.current_measurement-1}:\nExpected: {expected_yaw:.1f}°\nMeasured: {measured_yaw:.1f}°\nError: {error:+.1f}°"
        
        # 既存のテキストを更新
        if len(self.measurement_texts) > self.current_measurement - 1:
            old_text = self.measurement_texts[self.current_measurement - 1]
            old_text.set_text(result_text)
            
            # エラーに応じて色を変更
            if abs(error) <= 2.0:  # 2度以内なら緑
                old_text.set_bbox(dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.9))
            elif abs(error) <= 5.0:  # 5度以内なら黄
                old_text.set_bbox(dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.9))
            else:  # それ以上なら赤
                old_text.set_bbox(dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.9))
    
    def update_vehicle_highlights(self):
        """現在測定する車両フットプリントをハイライト"""
        for i, footprint in enumerate(self.vehicle_footprints):
            if i == self.current_measurement - 1:  # 現在の測定位置
                footprint.set_facecolor('red')
                footprint.set_alpha(0.8)
            else:  # 完了した位置
                footprint.set_facecolor('green')
                footprint.set_alpha(0.4)
    
    def update_status(self, message):
        """ステータステキスト更新"""
        self.status_text.set_text(message)
    
    def check_measurement_validity(self):
        """測定値の妥当性チェック（外れ値検出）"""
        if len(self.measurement_points) < 2:
            return True, "Insufficient data for validation"
        
        errors = []
        for point in self.measurement_points:
            expected = point["yaw"]
            measured = point["measured_yaw"]
            error = measured - expected
            
            # エラー正規化
            while error > 180:
                error -= 360
            while error <= -180:
                error += 360
            
            errors.append(abs(error))
        
        max_error = max(errors)
        avg_error = sum(errors) / len(errors)
        
        # 外れ値判定基準
        if max_error > 15.0:  # 15度以上の誤差
            return False, f"Large measurement error detected: {max_error:.1f}°"
        
        if avg_error > 8.0:  # 平均誤差が8度以上
            return False, f"High average error: {avg_error:.1f}°"
        
        return True, f"Measurements valid. Max error: {max_error:.1f}°, Avg: {avg_error:.1f}°"
    
    def save_calibration(self, event):
        """キャリブレーション結果の保存"""
        if len(self.measurement_points) < self.max_measurements:
            self.update_status(f"Need {self.max_measurements} measurements. Currently have {len(self.measurement_points)}.")
            return
        
        # 測定値妥当性チェック
        is_valid, validation_msg = self.check_measurement_validity()
        
        # キャリブレーションファイル作成
        calibration_data = {
            "calibration_type": "vehicle_footprint",
            "measurement_count": len(self.measurement_points),
            "vehicle_dimensions": {
                "width_mm": self.vehicle_width * 1000,
                "length_mm": self.vehicle_length * 1000
            },
            "measurements": self.measurement_points,
            "validation": {
                "is_valid": is_valid,
                "message": validation_msg
            },
            "created_at": datetime.now().isoformat()
        }
        
        # オフセット計算（2点の平均）
        if len(self.measurement_points) >= 2:
            offsets = []
            for point in self.measurement_points:
                expected = point["yaw"]
                measured = point["measured_yaw"]
                offset = expected - measured
                
                # 正規化
                while offset > 180:
                    offset -= 360
                while offset <= -180:
                    offset += 360
                
                offsets.append(offset)
            
            avg_offset = sum(offsets) / len(offsets)
            calibration_data["calculated_offset"] = avg_offset
        
        # ファイル保存
        filename = f"imu_calibration_footprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(calibration_data, f, indent=2, ensure_ascii=False)
            
            # 標準ファイル名でもコピー
            standard_filename = "imu_custom_calib.json"
            with open(standard_filename, 'w', encoding='utf-8') as f:
                json.dump(calibration_data, f, indent=2, ensure_ascii=False)
            
            if is_valid:
                self.update_status(f"✅ SUCCESS: Calibration saved to {filename}")
                print(f"✅ CALIBRATION COMPLETED SUCCESSFULLY!")
                print(f"Files saved: {filename}, {standard_filename}")
                print(f"Calculated offset: {calibration_data.get('calculated_offset', 'N/A'):.2f}°")
            else:
                self.update_status(f"⚠️ WARNING: Saved with validation errors. Check {filename}")
                print(f"⚠️ CALIBRATION SAVED WITH WARNINGS!")
                print(f"Validation issue: {validation_msg}")
            
        except Exception as e:
            self.update_status(f"❌ ERROR: Failed to save calibration - {str(e)}")
            print(f"❌ Save error: {e}")
    
    def reset_measurements(self, event):
        """測定データをリセット"""
        self.measurement_points.clear()
        self.current_measurement = 1
        self.button_measure.label.set_text(f"Measure IMU {self.current_measurement}")
        self.update_status("Reset completed. Position vehicle at Pos 1 and start measuring.")
        
        # フットプリント色をリセット
        for footprint in self.vehicle_footprints:
            footprint.set_facecolor('blue')
            footprint.set_alpha(0.4)
        
        # 最初のフットプリントをハイライト
        if self.vehicle_footprints:
            self.vehicle_footprints[0].set_facecolor('red')
            self.vehicle_footprints[0].set_alpha(0.8)
        
        # テキストをリセット
        for i, text in enumerate(self.measurement_texts):
            pos = self.footprint_positions[i]
            label = f"Pos {i+1}\n({pos['x']:.1f}, {pos['y']:.1f})\nYaw: {pos['yaw']:.1f}°"
            text.set_text(label)
            text.set_bbox(dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        self.fig.canvas.draw()
    
    def run_calibration_system(self):
        """キャリブレーションシステム実行"""
        print("🎯 IMU Calibration System - Vehicle Footprint Method")
        print("="*60)
        print("Features:")
        print("• High-quality course map display (same as waypoint_editor_multi_mode.py)")
        print("• Vehicle footprint visualization (180mm × 350mm)")
        print("• 2-point IMU measurement system")
        print("• Automatic validation and error detection")
        print("• Calibration file generation")
        
        self.setup_plot()
        self.draw_vehicle_footprints()
        self.setup_buttons()
        
        print("\nInstructions:")
        print("1. Position your vehicle at Pos 1 (red footprint)")
        print("2. Align vehicle orientation with the footprint")
        print("3. Click 'Measure IMU 1' button")
        print("4. Move to Pos 2 and repeat")
        print("5. Click 'Save Results' when both measurements are complete")
        
        self.update_status("Ready: Position vehicle at Pos 1 and click Measure IMU 1")
        
        plt.legend()
        plt.show()

    def run_calibration_with_return(self):
        """キャリブレーション実行（完了時に結果を返す）"""
        self.run_calibration_system()
        return self.pos1_data is not None and self.pos2_data is not None

# メイン実行
def main():
    calibration_system = IMUCalibrationSystem()
    calibration_system.run_calibration_system()

if __name__ == "__main__":
    main()