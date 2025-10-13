#!/bin/bash
# fix_raspberry_v8_clean.sh - ラズパイ5用v8_clean設定修正スクリプト

echo "🔧 ラズパイ5用 v8_clean config.json修正開始"

# バックアップ作成
if [ -f "config.json" ]; then
    cp config.json config.json.backup_$(date +%Y%m%d_%H%M%S)
    echo "✅ config.json バックアップ作成完了"
fi

# 完全なconfig.jsonを作成
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

echo "✅ config.json修正完了"

# JSONの構文チェック
if python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
    echo "✅ config.json構文チェック成功"
else
    echo "❌ config.json構文エラーが検出されました"
    python3 -c "import json; json.load(open('config.json'))"
    exit 1
fi

# v8_cleanファイルの構文チェック
if [ -f "teams_simple_laptime_fixed_v8_clean.py" ]; then
    if python3 -m py_compile teams_simple_laptime_fixed_v8_clean.py 2>/dev/null; then
        echo "✅ v8_clean構文チェック成功"
    else
        echo "❌ v8_clean構文エラーが検出されました"
        python3 -m py_compile teams_simple_laptime_fixed_v8_clean.py
        exit 1
    fi
else
    echo "⚠️ teams_simple_laptime_fixed_v8_clean.py が見つかりません"
fi

echo "🏁 ラズパイ5用修正完了！"
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
echo "🏆 3周計測システム準備完了"
echo "📍 スタートライン通過で計測開始"
echo "🆘 自走不能時はRキーで救済"