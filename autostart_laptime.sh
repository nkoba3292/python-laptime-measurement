#!/bin/bash
# Raspberry Pi 5 ラップタイム計測システム自動起動スクリプト

# スクリプト保存: ~/laptime_system/autostart_laptime.sh
# 実行権限付与: chmod +x ~/laptime_system/autostart_laptime.sh

echo "🚀 Raspberry Pi 5 ラップタイム計測システム自動起動"

# 作業ディレクトリ移動
cd /home/pi/laptime_system

# 仮想環境アクティベート
source laptime_env/bin/activate

# 5秒待機（システム起動完了待ち）
sleep 5

# システム起動
python3 raspberry_display_laptime.py

echo "✅ システム終了"