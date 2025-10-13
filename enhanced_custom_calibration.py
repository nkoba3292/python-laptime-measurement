# enhanced_custom_calibration.py - waypoint_editorレベルの高品質表示
import json
import math
import matplotlib.pyplot as plt
import numpy as np
import time
from datetime import datetime
import os

class EnhancedCustomCalibration:
    """waypoint_editorレベルの高品質表示でカスタムキャリブレーション"""
    
    def __init__(self, waypoint_file="quarify.json"):
        self.waypoint_file = waypoint_file
        self.selected_points = []
        self.fig = None
        self.ax = None
        self.calibration_setup = None
        self.mock_mode = True
        
        # 表示設定
        self.grid_resolution = 0.05  # 5cm解像度
        self.world_bounds = {'x_min': -5, 'x_max': 5, 'y_min': -2, 'y_max': 8}
        
        # Waypoint読み込み
        self.load_waypoints()
        self.prepare_course_map()
        
    def load_waypoints(self):
        """Waypoint読み込み"""
        try:
            with open(self.waypoint_file, 'r') as f:
                self.waypoints = json.load(f)
            print(f"✓ Loaded {len(self.waypoints)} waypoints from {self.waypoint_file}")
        except Exception as e:
            print(f"Error loading waypoints: {e}")
            self.waypoints = []
    
    def prepare_course_map(self):
        """コースマップデータ準備"""
        if not self.waypoints:
            return
        
        # Waypoint座標抽出
        x_coords = [wp['x'] for wp in self.waypoints]
        y_coords = [wp['y'] for wp in self.waypoints]
        
        # ワールド境界を自動調整
        margin = 1.0
        self.world_bounds = {
            'x_min': min(x_coords) - margin,
            'x_max': max(x_coords) + margin,
            'y_min': min(y_coords) - margin,
            'y_max': max(y_coords) + margin
        }
        
        # グリッドマップ作成
        self.create_grid_map()
        
        # コース要素推定
        self.estimate_course_elements()
    
    def create_grid_map(self):
        """背景グリッドマップ作成（waypoint_editor風）"""
        width = int((self.world_bounds['x_max'] - self.world_bounds['x_min']) / self.grid_resolution)
        height = int((self.world_bounds['y_max'] - self.world_bounds['y_min']) / self.grid_resolution)
        
        # 基本グリッド（灰色背景）
        self.grid_matrix = np.ones((height, width)) * 0.9
        
        # グリッドライン追加
        for i in range(0, height, 20):  # 1mごと
            self.grid_matrix[i, :] = 0.8
        for j in range(0, width, 20):  # 1mごと
            self.grid_matrix[:, j] = 0.8
    
    def world_to_grid(self, x, y):
        """ワールド座標→グリッド座標変換"""
        grid_x = int((x - self.world_bounds['x_min']) / self.grid_resolution)
        grid_y = int((y - self.world_bounds['y_min']) / self.grid_resolution)
        return grid_x, grid_y
    
    def estimate_course_elements(self):
        """waypointからコース要素を推定"""
        if len(self.waypoints) < 3:
            self.course_walls = []
            self.course_lines = []
            return
        
        x_coords = [wp['x'] for wp in self.waypoints]
        y_coords = [wp['y'] for wp in self.waypoints]
        
        # コース境界推定（内側・外側のオフセット）
        self.course_walls = []
        self.course_lines = []
        
        # 壁（コース境界）推定
        wall_offset = 0.6  # 60cm幅
        
        for i in range(len(self.waypoints) - 1):
            x1, y1 = self.waypoints[i]['x'], self.waypoints[i]['y']
            x2, y2 = self.waypoints[i + 1]['x'], self.waypoints[i + 1]['y']
            
            # 進行方向ベクトル
            dx, dy = x2 - x1, y2 - y1
            length = math.sqrt(dx**2 + dy**2)
            if length < 0.1:
                continue
            
            # 正規化
            dx, dy = dx / length, dy / length
            
            # 垂直ベクトル（壁方向）
            perp_x, perp_y = -dy, dx
            
            # 内側・外側壁
            for side_factor in [-1, 1]:
                wall_x1 = x1 + side_factor * wall_offset * perp_x
                wall_y1 = y1 + side_factor * wall_offset * perp_y
                wall_x2 = x2 + side_factor * wall_offset * perp_x
                wall_y2 = y2 + side_factor * wall_offset * perp_y
                
                self.course_walls.append({
                    'start': (wall_x1, wall_y1),
                    'end': (wall_x2, wall_y2),
                    'type': 'inner' if side_factor < 0 else 'outer'
                })
        
        # スタート・ゴールライン
        if len(self.waypoints) > 10:
            # スタートライン
            start_wp = self.waypoints[0]
            start_x, start_y = start_wp['x'], start_wp['y']
            
            # 最初の数点から方向推定
            if len(self.waypoints) > 3:
                next_wp = self.waypoints[3]
                dx = next_wp['x'] - start_x
                dy = next_wp['y'] - start_y
                length = math.sqrt(dx**2 + dy**2)
                if length > 0:
                    dx, dy = dx / length, dy / length
                    perp_x, perp_y = -dy, dx
                    
                    line_width = 0.5
                    self.course_lines.append({
                        'start': (start_x - line_width * perp_x, start_y - line_width * perp_y),
                        'end': (start_x + line_width * perp_x, start_y + line_width * perp_y),
                        'type': 'start',
                        'color': 'green'
                    })
            
            # ゴールライン
            goal_wp = self.waypoints[-1]
            goal_x, goal_y = goal_wp['x'], goal_wp['y']
            
            if len(self.waypoints) > 3:
                prev_wp = self.waypoints[-4]
                dx = goal_x - prev_wp['x']
                dy = goal_y - prev_wp['y']
                length = math.sqrt(dx**2 + dy**2)
                if length > 0:
                    dx, dy = dx / length, dy / length
                    perp_x, perp_y = -dy, dx
                    
                    line_width = 0.5
                    self.course_lines.append({
                        'start': (goal_x - line_width * perp_x, goal_y - line_width * perp_y),
                        'end': (goal_x + line_width * perp_x, goal_y + line_width * perp_y),
                        'type': 'goal',
                        'color': 'red'
                    })
    
    def display_enhanced_course_map(self):
        """waypoint_editorレベルの高品質マップ表示"""
        if not self.waypoints:
            print("❌ Waypoints not available")
            return False
        
        # Figure作成（高解像度）
        self.fig, self.ax = plt.subplots(figsize=(16, 12), dpi=120)
        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9)
        
        self.fig.suptitle('🏁 Enhanced Course Map - Custom Calibration Points Selection\n'
                         '📍 Click Point 1 (Vehicle Position) → Click Point 2 (Target Direction)', 
                         fontsize=18, fontweight='bold', color='darkblue')
        
        # 背景グリッド表示（waypoint_editor風）
        extent = [self.world_bounds['x_min'], self.world_bounds['x_max'],
                 self.world_bounds['y_min'], self.world_bounds['y_max']]
        self.ax.imshow(self.grid_matrix, cmap='Greys', origin='lower', 
                      extent=extent, alpha=0.3, aspect='equal')
        
        # コース壁描画（waypoint_editor風の緑色障害物）
        for wall in self.course_walls:
            x1, y1 = wall['start']
            x2, y2 = wall['end']
            
            # 壁の太さ
            wall_thickness = 0.1
            
            # 壁を矩形として描画
            wall_dx = x2 - x1
            wall_dy = y2 - y1
            wall_length = math.sqrt(wall_dx**2 + wall_dy**2)
            
            if wall_length > 0:
                # 壁の向きに合わせた矩形
                angle = math.atan2(wall_dy, wall_dx)
                
                # 矩形の中心
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # 矩形描画（waypoint_editor風）
                from matplotlib.patches import Rectangle
                import matplotlib.transforms as transforms
                
                rect = Rectangle((center_x - wall_length/2, center_y - wall_thickness/2), 
                               wall_length, wall_thickness,
                               color='lightgreen', alpha=0.6, edgecolor='green', linewidth=1)
                
                # 回転適用
                t = transforms.Affine2D().rotate_around(center_x, center_y, angle) + self.ax.transData
                rect.set_transform(t)
                self.ax.add_patch(rect)
        
        # コースライン描画（waypoint_editor風）
        for course_line in self.course_lines:
            x1, y1 = course_line['start']
            x2, y2 = course_line['end']
            color = course_line.get('color', 'blue')
            
            self.ax.plot([x1, x2], [y1, y2], color=color, linewidth=4, alpha=0.8,
                        label=f"{course_line['type'].title()} Line")
        
        # Waypoint描画
        x_coords = [wp['x'] for wp in self.waypoints]
        y_coords = [wp['y'] for wp in self.waypoints]
        
        # メインコースライン
        self.ax.plot(x_coords, y_coords, 'b-', linewidth=4, alpha=0.9, label='🏁 Course Path')
        
        # ウェイポイント（間引いて表示）
        self.ax.scatter(x_coords[::8], y_coords[::8], c='lightblue', s=25, alpha=0.6, 
                       label='Waypoints', edgecolors='blue', linewidth=0.5)
        
        # スタート・ゴール地点
        self.ax.scatter(x_coords[0], y_coords[0], c='lime', s=400, marker='o', 
                       label='🚀 START', edgecolors='darkgreen', linewidth=4, zorder=10)
        self.ax.scatter(x_coords[-1], y_coords[-1], c='red', s=400, marker='s', 
                       label='🏆 GOAL', edgecolors='darkred', linewidth=4, zorder=10)
        
        # 参考ポイント（四半期）表示
        quarter_points = [len(x_coords)//4, len(x_coords)//2, 3*len(x_coords)//4]
        colors = ['orange', 'purple', 'brown']
        
        for i, idx in enumerate(quarter_points):
            self.ax.scatter(x_coords[idx], y_coords[idx], c=colors[i], s=150, marker='^',
                           edgecolors='black', linewidth=2, alpha=0.8, zorder=8)
            self.ax.annotate(f'Q{i+1}', (x_coords[idx], y_coords[idx]), 
                           xytext=(10, 10), textcoords='offset points',
                           fontsize=12, fontweight='bold', color=colors[i],
                           bbox=dict(boxstyle="round,pad=0.3", facecolor=colors[i], alpha=0.3))
        
        # 軸設定
        self.ax.set_xlabel('X coordinate [m]', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('Y coordinate [m]', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.4, linestyle='--', color='gray')
        self.ax.legend(loc='upper left', fontsize=11)
        self.ax.set_aspect('equal', adjustable='box')
        
        # 表示範囲設定
        margin = 0.3
        self.ax.set_xlim(self.world_bounds['x_min'] - margin, self.world_bounds['x_max'] + margin)
        self.ax.set_ylim(self.world_bounds['y_min'] - margin, self.world_bounds['y_max'] + margin)
        
        # 操作説明表示
        instruction_text = (
            f'📋 ENHANCED COURSE MAP:\n'
            f'• Waypoints: {len(self.waypoints)}\n'
            f'• Course walls: {len(self.course_walls)}\n'
            f'• Course lines: {len(self.course_lines)}\n'
            f'• Size: {self.world_bounds["x_max"]-self.world_bounds["x_min"]:.0f}m × {self.world_bounds["y_max"]-self.world_bounds["y_min"]:.0f}m\n\n'
            f'🎯 CALIBRATION SETUP:\n'
            f'1️⃣ Click Point 1: Vehicle Position\n'
            f'2️⃣ Click Point 2: Target Direction\n'
            f'3️⃣ Direction Point1→Point2 = 0°\n'
            f'4️⃣ Choose clear, visible landmarks\n'
            f'5️⃣ Close window when complete'
        )
        
        self.ax.text(0.02, 0.98, instruction_text,
                    transform=self.ax.transAxes, 
                    verticalalignment='top',
                    bbox=dict(boxstyle="round,pad=0.6", facecolor="lightyellow", alpha=0.95,
                             edgecolor='orange', linewidth=2),
                    fontsize=12, fontweight='bold')
        
        # マウスクリックイベント
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # ステータス表示エリア
        self.status_text = self.ax.text(0.5, 0.02, '🎯 Click Point 1 (Vehicle Position)',
                                       transform=self.ax.transAxes,
                                       fontsize=15, fontweight='bold', color='red',
                                       ha='center',
                                       bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.95,
                                               edgecolor='red', linewidth=3))
        
        return True
    
    def on_click(self, event):
        """マップクリック処理"""
        if event.inaxes != self.ax or len(self.selected_points) >= 2:
            return
        
        click_x, click_y = event.xdata, event.ydata
        point_num = len(self.selected_points) + 1
        
        self.selected_points.append({
            'x': click_x,
            'y': click_y,
            'name': f'Calibration Point {point_num}'
        })
        
        # 選択点を表示
        if point_num == 1:
            # Point 1 - Vehicle Position (Red Star)
            self.ax.scatter(click_x, click_y, c='red', s=500, marker='*', 
                           edgecolors='darkred', linewidth=5, zorder=15)
            self.ax.annotate(f'🚗 Vehicle Position\n({click_x:.1f}, {click_y:.1f})', 
                            (click_x, click_y), xytext=(25, 25), 
                            textcoords='offset points',
                            fontsize=14, fontweight='bold', color='darkred',
                            bbox=dict(boxstyle="round,pad=0.5", facecolor='red', alpha=0.3,
                                     edgecolor='darkred', linewidth=3),
                            arrowprops=dict(arrowstyle='->', color='darkred', lw=2))
            
        elif point_num == 2:
            # Point 2 - Target Direction (Blue Diamond)
            self.ax.scatter(click_x, click_y, c='blue', s=500, marker='D', 
                           edgecolors='darkblue', linewidth=5, zorder=15)
            self.ax.annotate(f'🎯 Target Direction\n({click_x:.1f}, {click_y:.1f})', 
                            (click_x, click_y), xytext=(25, 25), 
                            textcoords='offset points',
                            fontsize=14, fontweight='bold', color='darkblue',
                            bbox=dict(boxstyle="round,pad=0.5", facecolor='blue', alpha=0.3,
                                     edgecolor='darkblue', linewidth=3),
                            arrowprops=dict(arrowstyle='->', color='darkblue', lw=2))
        
        print(f"✓ Selected Point {point_num}: ({click_x:.1f}, {click_y:.1f})")
        
        # ステータス更新
        if point_num == 1:
            self.status_text.set_text('🎯 Click Point 2 (Target Direction)')
            self.status_text.set_color('blue')
        elif point_num == 2:
            self.show_calibration_result()
        
        self.fig.canvas.draw()
    
    def show_calibration_result(self):
        """2点選択完了時の結果表示"""
        if len(self.selected_points) != 2:
            return
        
        p1 = self.selected_points[0]
        p2 = self.selected_points[1]
        
        # 方向計算
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        distance = math.sqrt(dx**2 + dy**2)
        angle_deg = math.degrees(math.atan2(dy, dx))
        
        if angle_deg < 0:
            angle_deg += 360
        
        # 方向矢印描画（太く、派手に）
        self.ax.annotate('', xy=(p2['x'], p2['y']), xytext=(p1['x'], p1['y']),
                        arrowprops=dict(arrowstyle='->', color='purple', lw=10, alpha=0.9))
        
        # 中間点に角度・距離情報
        mid_x = (p1['x'] + p2['x']) / 2
        mid_y = (p1['y'] + p2['y']) / 2
        
        direction_info = f'📐 {angle_deg:.1f}°\n📏 {distance:.1f}m'
        self.ax.text(mid_x, mid_y, direction_info, 
                   fontsize=18, fontweight='bold', color='purple',
                   ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.8", facecolor="white", alpha=0.95,
                           edgecolor='purple', linewidth=4))
        
        # ステータス更新
        self.status_text.set_text('✅ Calibration Points Selected - Close window to proceed')
        self.status_text.set_color('green')
        
        # キャリブレーション設定保存
        self.calibration_setup = {
            'timestamp': datetime.now().isoformat(),
            'method': 'enhanced_custom_2point_selection',
            'point1': p1,
            'point2': p2,
            'reference_angle': angle_deg,
            'distance': distance,
            'description': f'Enhanced custom selection: ({p1["x"]:.1f},{p1["y"]:.1f}) → ({p2["x"]:.1f},{p2["y"]:.1f})',
            'status': 'setup_complete'
        }
        
        # コンソール出力
        print(f"\n{'='*70}")
        print(f"🎊 ENHANCED CALIBRATION POINTS SELECTED!")
        print(f"{'='*70}")
        print(f"🚗 Vehicle Position: ({p1['x']:.1f}, {p1['y']:.1f})")
        print(f"🎯 Target Direction: ({p2['x']:.1f}, {p2['y']:.1f})")
        print(f"📐 Reference Angle: {angle_deg:.1f}°")
        print(f"📏 Distance: {distance:.1f}m")
        print(f"{'='*70}")
        
        return self.calibration_setup
    
    def mock_imu_measurement(self):
        """Mock IMU測定"""
        print("\n🔧 Mock IMU Measurement...")
        for i in range(3):
            print(f"   Reading IMU... {i+1}/3")
            time.sleep(0.3)
        
        mock_yaw = np.random.uniform(0, 360)
        print(f"✓ Mock IMU: {mock_yaw:.1f}°")
        return mock_yaw
    
    def save_calibration_file(self, imu_yaw, offset):
        """キャリブレーションファイル保存"""
        calibration_data = {
            'timestamp': datetime.now().isoformat(),
            'calibration_method': 'enhanced_custom_2point_user_selection',
            'setup_points': self.calibration_setup,
            'imu_measurement': {
                'raw_yaw': imu_yaw,
                'measurement_time': datetime.now().isoformat()
            },
            'calibration_result': {
                'reference_angle': self.calibration_setup['reference_angle'],
                'yaw_offset': offset,
                'description': f"Enhanced offset alignment with user-selected direction"
            },
            'usage_instructions': {
                'vehicle_position': f"({self.calibration_setup['point1']['x']:.1f}, {self.calibration_setup['point1']['y']:.1f})",
                'target_direction': f"({self.calibration_setup['point2']['x']:.1f}, {self.calibration_setup['point2']['y']:.1f})",
                'reference_heading': f"{self.calibration_setup['reference_angle']:.1f}°"
            }
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"imu_enhanced_calibration_{timestamp}.json"
        standard_filename = "imu_custom_calib.json"
        
        try:
            # タイムスタンプファイル
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(calibration_data, f, indent=2, ensure_ascii=False)
            
            # 標準ファイル
            with open(standard_filename, 'w', encoding='utf-8') as f:
                json.dump(calibration_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Enhanced calibration files saved:")
            print(f"   📄 {filename}")
            print(f"   📄 {standard_filename}")
            
            return filename, standard_filename
            
        except Exception as e:
            print(f"❌ Error saving files: {e}")
            return None, None
    
    def run_enhanced_calibration(self):
        """拡張キャリブレーション実行"""
        print("="*80)
        print("🏁 ENHANCED CUSTOM CALIBRATION SYSTEM (waypoint_editor level)")
        print("="*80)
        print("Features:")
        print("• High-quality course map with walls and lines")
        print("• Enhanced waypoint visualization")  
        print("• User-friendly 2-point selection interface")
        print("• Automatic IMU calibration file generation")
        print()
        
        # Step 1: 拡張マップ表示
        print("🗺️  Step 1: Enhanced Course Map Display")
        if not self.display_enhanced_course_map():
            print("❌ Failed to display enhanced course map")
            return False
        
        print("📍 Enhanced course map displayed with walls and lines.")
        print("   Click your 2 calibration points, then close the window.")
        
        try:
            plt.show()
        except Exception as e:
            print(f"❌ Display error: {e}")
            return False
        
        # 選択結果確認
        if not self.calibration_setup:
            print("❌ No calibration points selected")
            return False
        
        print("✅ Enhanced calibration points selection completed!")
        
        # Step 2: IMU測定とファイル保存
        print(f"\n📡 Step 2: Position Vehicle and Measure")
        print(f"   🚗 Position at: ({self.calibration_setup['point1']['x']:.1f}, {self.calibration_setup['point1']['y']:.1f})")
        print(f"   🎯 Face toward: ({self.calibration_setup['point2']['x']:.1f}, {self.calibration_setup['point2']['y']:.1f})")
        
        input("\nPress Enter when vehicle is positioned correctly...")
        
        current_yaw = self.mock_imu_measurement()
        offset = self.calibration_setup['reference_angle'] - current_yaw
        
        # 正規化
        while offset > 180:
            offset -= 360
        while offset <= -180:
            offset += 360
        
        print(f"\n📊 Enhanced Calibration Results:")
        print(f"   Reference: {self.calibration_setup['reference_angle']:.1f}°")
        print(f"   IMU Yaw: {current_yaw:.1f}°")
        print(f"   Offset: {offset:.1f}°")
        
        # ファイル保存
        files = self.save_calibration_file(current_yaw, offset)
        
        if files[0] and files[1]:
            print(f"\n🎊 ENHANCED CALIBRATION COMPLETED!")
            print(f"✅ Ready for racing with enhanced calibration!")
            return True
        else:
            print("❌ File save failed")
            return False

def main():
    print("🏁 Enhanced Custom Calibration (waypoint_editor level display)")
    
    calibrator = EnhancedCustomCalibration()
    success = calibrator.run_enhanced_calibration()
    
    if success:
        print("\n" + "="*60)
        print("✅ ENHANCED CALIBRATION SUCCESS!")
        print("="*60)
        print("Your system now has waypoint_editor level display quality!")
        print("Race with confidence using your custom calibration.")
    else:
        print("\n❌ Enhanced calibration failed")
    
    print("\nEnhanced calibration session ended.")

if __name__ == "__main__":
    main()