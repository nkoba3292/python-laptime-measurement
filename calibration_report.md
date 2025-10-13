
# 🎯 Laptime System キャリブレーション完了レポート

## 📊 最適化された設定値
- **Motion Pixels Threshold**: 15000
- **Min Contour Area**: 1000
- **Detection Conditions Required**: 6/6
- **Detection Cooldown**: 5.0秒
- **Camera Configuration**: Overview=0, StartLine=2

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
2025年10月04日 22:33:37
