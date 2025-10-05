#!/bin/bash
# Raspberry Pi用 v8ファイル手動修正スクリプト (文字化け対応版)

echo "Raspberry Pi: v8 file merge conflict fix"
echo "=========================================="

# 現在のディレクトリに移動
cd /home/pi/laptime-system

# バックアップ作成
cp teams_simple_laptime_fixed_v8.py teams_simple_laptime_fixed_v8.py.backup_$(date +%Y%m%d_%H%M%S)
echo "Backup created"

# マージ競合マーカーを除去
echo "Removing merge conflict markers..."

# 一時ファイルを作成してマージ競合マーカーを除去
sed '/^<<<<<<< HEAD$/,/^=======$/d' teams_simple_laptime_fixed_v8.py | \
sed '/^>>>>>>> [a-f0-9]*$/d' > teams_simple_laptime_fixed_v8.py.tmp

# ファイルサイズチェック
if [ -s teams_simple_laptime_fixed_v8.py.tmp ]; then
    mv teams_simple_laptime_fixed_v8.py.tmp teams_simple_laptime_fixed_v8.py
    echo "Merge conflict markers removed"
    
    # 構文チェック
    echo "Checking syntax..."
    python3 -m py_compile teams_simple_laptime_fixed_v8.py
    if [ $? -eq 0 ]; then
        echo "Syntax check passed"
        echo "v8 file fixed successfully!"
    else
        echo "Syntax errors still exist"
        echo "Manual editing required"
        exit 1
    fi
else
    echo "Error: Processed file is empty"
    rm teams_simple_laptime_fixed_v8.py.tmp
    exit 1
fi