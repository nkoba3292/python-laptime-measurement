#!/bin/bash
# setup_python_environment.sh
# ラズベリーパイ5でのPython環境セットアップスクリプト

echo "🏁 ラップタイム計測システム - Python環境セットアップ"
echo "============================================================"

# プロジェクトディレクトリ作成
echo "📁 プロジェクトディレクトリ作成..."
mkdir -p /home/pi/laptime_system/{data,sounds,logs}
cd /home/pi/laptime_system

# システム更新
echo "📦 システム更新..."
sudo apt update

# 必要なシステムパッケージ
echo "🔧 システムパッケージインストール..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libopencv-dev \
    python3-opencv \
    v4l-utils \
    uvcdynctrl \
    ffmpeg \
    libportaudio2 \
    libasound2-dev

# Python仮想環境作成
echo "🐍 Python仮想環境作成..."
python3 -m venv laptime_env
source laptime_env/bin/activate

# Pythonライブラリインストール
echo "📚 Pythonライブラリインストール..."
pip install --upgrade pip

# OpenCV (軽量版)
pip install opencv-python-headless

# その他必要ライブラリ
pip install \
    numpy \
    pygame \
    pathlib

# USB カメラ権限設定
echo "📹 カメラ権限設定..."
sudo usermod -a -G video pi
sudo usermod -a -G audio pi

# デバイス確認
echo "🔍 利用可能なカメラデバイス:"
ls -la /dev/video* || echo "カメラが接続されていません"

echo "✅ Python環境セットアップ完了！"
echo "============================================================"
echo "📋 セットアップ内容:"
echo "• プロジェクトディレクトリ: /home/pi/laptime_system"
echo "• Python仮想環境: /home/pi/laptime_system/laptime_env"
echo "• インストール済みライブラリ: OpenCV, NumPy, Pygame"
echo "============================================================"
echo "🎯 次のステップ:"
echo "1. プロジェクトファイルをSFTPで転送"
echo "2. カメラ2台を接続"
echo "3. システムテスト実行"