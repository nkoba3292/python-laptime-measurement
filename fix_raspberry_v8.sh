#!/bin/bash
# Raspberry Pi用 v8ファイル修正スクリプト

echo "🔧 Raspberry Pi: v8ファイルのマージ競合修正"
echo "=============================================="

# 現在のディレクトリに移動
cd /home/pi/laptime-system

# バックアップ作成
cp teams_simple_laptime_fixed_v8.py teams_simple_laptime_fixed_v8.py.backup_$(date +%Y%m%d_%H%M%S)
echo "📋 バックアップ作成完了"

# GitHubから最新版を取得
echo "🌐 GitHubから最新版を取得中..."
curl -o teams_simple_laptime_fixed_v8.py.tmp https://raw.githubusercontent.com/nkoba3292/python-laptime-measurement/master/teams_simple_laptime_fixed_v8.py

# ファイルの検証
if grep -q "<<<<<<< HEAD" teams_simple_laptime_fixed_v8.py.tmp; then
    echo "❌ ダウンロードしたファイルにまだ競合マーカーが含まれています"
    echo "手動修正が必要です"
    exit 1
else
    # 正常なファイルの場合、置き換え
    mv teams_simple_laptime_fixed_v8.py.tmp teams_simple_laptime_fixed_v8.py
    echo "✅ v8ファイル更新完了"
    
    # 構文チェック
    echo "🔍 構文チェック実行中..."
    python3 -m py_compile teams_simple_laptime_fixed_v8.py
    if [ $? -eq 0 ]; then
        echo "✅ 構文チェック成功"
        echo "🚀 v8ファイル修正完了！実行可能です"
    else
        echo "❌ 構文エラーが残っています"
        exit 1
    fi
fi