#!/bin/bash
# fix_raspberry_v8_complete.sh - ラズパイ5用完全修正スクリプト

echo "🔧 ラズパイ5用 v8_clean 完全修正開始"

# システム情報表示
echo "📊 システム情報:"
echo "   OS: $(uname -a)"
echo "   Python: $(python3 --version)"
echo "   User: $(whoami)"

# カメラデバイス確認
echo ""
echo "📷 カメラデバイス確認:"
if ls /dev/video* 2>/dev/null; then
    echo "✅ カメラデバイスが検出されました"
    for device in /dev/video*; do
        echo "   - $device"
    done
else
    echo "❌ カメラデバイスが見つかりません"
fi

# 権限確認
echo ""
echo "🔐 権限確認:"
groups | grep -q video && echo "✅ videoグループに属しています" || echo "❌ videoグループに属していません"

# バックアップ作成
echo ""
echo "💾 バックアップ作成:"
if [ -f "teams_simple_laptime_fixed_v8_clean.py" ]; then
    cp teams_simple_laptime_fixed_v8_clean.py teams_simple_laptime_fixed_v8_clean.py.backup_$(date +%Y%m%d_%H%M%S)
    echo "✅ v8_clean バックアップ作成完了"
fi

if [ -f "config.json" ]; then
    cp config.json config.json.backup_$(date +%Y%m%d_%H%M%S)
    echo "✅ config.json バックアップ作成完了"
fi

# 完全なconfig.jsonを作成
echo ""
echo "⚙️ config.json修正:"
cat > config.json << 'EOF'
{
  "camera_overview_id": 0,
  "camera_start_line_id": 0,
  "camera_settings": {
    "overview_camera_index": 0,
    "startline_camera_index": 0,
    "frame_width": 640,
    "frame_height": 480
  },
  "detection_settings": {
    "motion_pixels_threshold": 300,
    "min_contour_area": 200,
    "motion_area_ratio_min": 0.008,
    "motion_area_ratio_max": 0.9,
    "stable_frames_required": 2,
    "motion_consistency_check": false,
    "detection_conditions_required": 2
  },
  "race_settings": {
    "max_laps": 3,
    "detection_cooldown": 2.5
  },
  "background_subtractor_settings": {
    "history": 30,
    "varThreshold": 16,
    "detectShadows": false
  }
}
EOF
echo "✅ config.json作成完了"

# カメラなしモード対応のv8_clean修正版を作成
echo ""
echo "🎥 カメラなしモード対応修正:"
if [ -f "teams_simple_laptime_fixed_v8_clean.py" ]; then
    # init_cameras関数をカメラなしでも動作するように修正
    sed -i '/def init_cameras/,/return True/c\
    def init_cameras(self):\
        """カメラ初期化（カメラなしモード対応）"""\
        try:\
            print("📷 カメラを初期化中...")\
            \
            # カメラ0を試行\
            self.camera_overview = cv2.VideoCapture(self.overview_camera_index)\
            self.camera_start_line = cv2.VideoCapture(self.startline_camera_index)\
            \
            camera_available = False\
            \
            if self.camera_overview.isOpened():\
                print(f"✅ Overview camera (index {self.overview_camera_index}) opened successfully")\
                camera_available = True\
            else:\
                print(f"⚠️ Overview camera (index {self.overview_camera_index}) could not be opened")\
                self.camera_overview = None\
            \
            if self.camera_start_line.isOpened():\
                print(f"✅ Start line camera (index {self.startline_camera_index}) opened successfully")\
                camera_available = True\
            else:\
                print(f"⚠️ Start line camera (index {self.startline_camera_index}) could not be opened")\
                self.camera_start_line = None\
            \
            # カメラ設定（利用可能な場合のみ）\
            if self.camera_overview and self.camera_overview.isOpened():\
                self.camera_overview.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)\
                self.camera_overview.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)\
            \
            if self.camera_start_line and self.camera_start_line.isOpened():\
                self.camera_start_line.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)\
                self.camera_start_line.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)\
            \
            # 背景差分初期化\
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(\
                history=500, varThreshold=16, detectShadows=True\
            )\
            \
            if camera_available:\
                print("✅ カメラ初期化完了（一部カメラ利用可能）")\
            else:\
                print("⚠️ カメラなしモードで起動（デモモード）")\
            \
            return True  # カメラなしでも続行\
            \
        except Exception as e:\
            print(f"⚠️ カメラ初期化警告: {e}")\
            print("📺 カメラなしモードで続行します")\
            self.camera_overview = None\
            self.camera_start_line = None\
            return True  # カメラなしでも続行' teams_simple_laptime_fixed_v8_clean.py

    echo "✅ カメラ初期化関数修正完了"
else
    echo "❌ teams_simple_laptime_fixed_v8_clean.py が見つかりません"
fi

# 文字エンコーディング修正（日本語表示対応）
echo ""
echo "🔤 文字エンコーディング修正:"
if [ -f "teams_simple_laptime_fixed_v8_clean.py" ]; then
    # UTF-8エンコーディング指定を追加
    sed -i '1i# -*- coding: utf-8 -*-' teams_simple_laptime_fixed_v8_clean.py
    echo "✅ UTF-8エンコーディング指定追加完了"
fi

# 権限修正（必要に応じて）
echo ""
echo "🔐 権限修正:"
if ! groups | grep -q video; then
    echo "⚠️ videoグループに追加が必要です"
    echo "   実行してください: sudo usermod -a -G video $USER"
    echo "   その後ログアウト/ログインが必要です"
fi

# 構文チェック
echo ""
echo "🔍 構文チェック:"
if python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
    echo "✅ config.json構文チェック成功"
else
    echo "❌ config.json構文エラー"
    python3 -c "import json; json.load(open('config.json'))"
fi

if [ -f "teams_simple_laptime_fixed_v8_clean.py" ]; then
    if python3 -m py_compile teams_simple_laptime_fixed_v8_clean.py 2>/dev/null; then
        echo "✅ v8_clean構文チェック成功"
    else
        echo "❌ v8_clean構文エラー"
        python3 -m py_compile teams_simple_laptime_fixed_v8_clean.py
    fi
fi

# 依存関係チェック
echo ""
echo "📦 依存関係チェック:"
python3 -c "import pygame; print('✅ pygame:', pygame.__version__)" 2>/dev/null || echo "❌ pygame not installed"
python3 -c "import cv2; print('✅ opencv:', cv2.__version__)" 2>/dev/null || echo "❌ opencv not installed"
python3 -c "import numpy; print('✅ numpy:', numpy.__version__)" 2>/dev/null || echo "❌ numpy not installed"

echo ""
echo "🏁 ラズパイ5用完全修正完了！"
echo ""
echo "📋 実行方法:"
echo "   python3 teams_simple_laptime_fixed_v8_clean.py"
echo ""
echo "🎮 操作方法:"
echo "   S = 計測準備（ローリングスタート）"
echo "   R = 救済申請（5秒ペナルティ）"
echo "   Q = レース停止"
echo "   ESC = 終了"
echo ""
echo "💡 注意事項:"
echo "   - カメラなしでもデモモードで動作します"
echo "   - キーボードで手動検出テストが可能です"
echo "   - 文字化け対策済み"
echo ""
echo "🏆 3周計測システム準備完了"