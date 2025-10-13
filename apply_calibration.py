#!/usr/bin/env python3
"""
キャリブレーション済みlaptimeシステム設定適用ツール
最適化された設定値を既存のv8-v12に適用します

確定設定値:
- motion_pixels_threshold: 15000
- min_contour_area: 1000
- detection_conditions_required: 6
- detection_cooldown: 5.0
"""

import json
import os
import shutil
from datetime import datetime

class LaptimeCalibrationManager:
    def __init__(self):
        self.calibrated_settings = {
            "motion_pixels_threshold": 15000,
            "min_contour_area": 1000,
            "detection_conditions_required": 6,
            "detection_cooldown": 5.0,
            "camera_overview_id": 0,
            "camera_start_line_id": 2
        }
        
    def create_calibrated_config(self, output_path="config_calibrated.json"):
        """キャリブレーション済みconfig.jsonを作成"""
        config = {
            "camera_overview_id": self.calibrated_settings["camera_overview_id"],
            "camera_start_line_id": self.calibrated_settings["camera_start_line_id"],
            "camera_settings": {
                "overview_camera_index": self.calibrated_settings["camera_overview_id"],
                "startline_camera_index": self.calibrated_settings["camera_start_line_id"],
                "frame_width": 640,
                "frame_height": 480
            },
            "detection_settings": {
                "motion_pixels_threshold": self.calibrated_settings["motion_pixels_threshold"],
                "min_contour_area": self.calibrated_settings["min_contour_area"],
                "detection_conditions_required": self.calibrated_settings["detection_conditions_required"]
            },
            "race_settings": {
                "max_laps": 10,
                "detection_cooldown": self.calibrated_settings["detection_cooldown"]
            },
            "calibration_info": {
                "calibrated": True,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "optimized_for": "Raspberry Pi 5 dual camera setup"
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ キャリブレーション済み設定ファイル作成: {output_path}")
        # 背景差分アルゴリズム設定も更新
        bg_settings = calibrated_config.get('background_subtractor_settings', {})
        
        # history設定の更新
        if 'history' in bg_settings:
            content = re.sub(
                r'history=\d+',
                f'history={bg_settings["history"]}',
                content
            )
            print(f"🔧 修正: history設定 → history={bg_settings['history']}")
        
        # varThreshold設定の更新
        if 'varThreshold' in bg_settings:
            content = re.sub(
                r'varThreshold=\d+',
                f'varThreshold={bg_settings["varThreshold"]}',
                content
            )
            print(f"🔧 修正: varThreshold設定 → varThreshold={bg_settings['varThreshold']}")
        
        return content
        
    def apply_to_v8_hardcoded(self, v8_file_path):
        """v8ファイルのハードコード設定を更新"""
        if not os.path.exists(v8_file_path):
            print(f"❌ ファイルが見つかりません: {v8_file_path}")
            return False
            
        # バックアップ作成
        backup_path = f"{v8_file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(v8_file_path, backup_path)
        print(f"📋 バックアップ作成: {backup_path}")
        
        # ファイル読み込み
        with open(v8_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 設定値の置換
        replacements = [
            ("self.motion_pixels_threshold = 100", f"self.motion_pixels_threshold = {self.calibrated_settings['motion_pixels_threshold']}"),
            ("self.motion_pixels_threshold = 5000", f"self.motion_pixels_threshold = {self.calibrated_settings['motion_pixels_threshold']}"),
            ("self.motion_pixels_threshold = 50000", f"self.motion_pixels_threshold = {self.calibrated_settings['motion_pixels_threshold']}"),
            ("self.min_contour_area = 50", f"self.min_contour_area = {self.calibrated_settings['min_contour_area']}"),
            ("self.min_contour_area = 300", f"self.min_contour_area = {self.calibrated_settings['min_contour_area']}"),
            ("self.detection_conditions_required = 1", f"self.detection_conditions_required = {self.calibrated_settings['detection_conditions_required']}"),
            ("self.detection_conditions_required = 3", f"self.detection_conditions_required = {self.calibrated_settings['detection_conditions_required']}"),
            ("< 2.0:", f"< {self.calibrated_settings['detection_cooldown']}:"),
            ("< 5.0:", f"< {self.calibrated_settings['detection_cooldown']}:"),
            ("< 10.0:", f"< {self.calibrated_settings['detection_cooldown']}:")
        ]
        
        modified = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                modified = True
                print(f"🔧 修正: {old} → {new}")
        
        if modified:
            with open(v8_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ v8ファイル更新完了: {v8_file_path}")
            return True
        else:
            print(f"ℹ️  修正箇所が見つかりませんでした: {v8_file_path}")
            return False
    
    def generate_calibration_report(self):
        """キャリブレーション結果レポート生成"""
        report = f"""
# 🎯 Laptime System キャリブレーション完了レポート

## 📊 最適化された設定値
- **Motion Pixels Threshold**: {self.calibrated_settings['motion_pixels_threshold']}
- **Min Contour Area**: {self.calibrated_settings['min_contour_area']}
- **Detection Conditions Required**: {self.calibrated_settings['detection_conditions_required']}/6
- **Detection Cooldown**: {self.calibrated_settings['detection_cooldown']}秒
- **Camera Configuration**: Overview={self.calibrated_settings['camera_overview_id']}, StartLine={self.calibrated_settings['camera_start_line_id']}

## 🎛️ 検出条件の説明
1. **Motion Pixels**: 変化ピクセル数 ≥ 15000
2. **Max Contour**: 最大輪郭面積 ≥ 1000
3. **Motion Ratio**: 動き面積比が適正範囲
4. **Contour Count**: 輪郭数 ≥ 1
5. **Avg Contour**: 平均輪郭面積 ≥ 25
6. **Motion Density**: 動き密度 ≥ 50

## ✅ 特徴
- **高精度**: 全6条件を満たした場合のみ検出
- **誤検出防止**: 5秒のクールダウンで連続検出を防止
- **安定性**: 環境ノイズに対して高い耐性

## 🚀 使用方法
1. Raspberry Pi 5でv8-v12を実行
2. カメラID: Overview=0, StartLine=2
3. レース開始: Sキー
4. 物体がStartLineカメラ前を通過すると検出

## 📅 キャリブレーション完了日時
{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}
"""
        
        with open("calibration_report.md", 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("📋 キャリブレーションレポート生成: calibration_report.md")
        return report

def main():
    print("🎯 Laptime System キャリブレーション設定適用ツール")
    print("="*50)
    
    manager = LaptimeCalibrationManager()
    
    # 1. キャリブレーション済みconfig.json作成
    manager.create_calibrated_config()
    
    # 2. v8ファイルの更新（ファイルパスを指定）
    v8_files = [
        "teams_simple_laptime_fixed_v8.py",
        "/home/pi/laptime-system/teams_simple_laptime_fixed_v8.py"
    ]
    
    for v8_file in v8_files:
        if os.path.exists(v8_file):
            manager.apply_to_v8_hardcoded(v8_file)
    
    # 3. レポート生成
    manager.generate_calibration_report()
    
    print("\n🎉 キャリブレーション適用完了!")
    print("推奨: config_calibrated.jsonを本番用config.jsonとして使用")

if __name__ == "__main__":
    main()