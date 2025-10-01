#!/bin/bash
# transfer_to_raspberry_pi.sh
# ラズパイへのファイル転送スクリプト

# 設定
RASPBERRY_PI_IP="192.168.1.100"  # ラズパイのIPアドレスに変更
RASPBERRY_PI_USER="pi"
REMOTE_DIR="~/laptime_system"

echo "🍓 Raspberry Pi へのファイル転送スクリプト"
echo "=" * 50

# IPアドレスの確認
echo "ラズパイのIPアドレス: $RASPBERRY_PI_IP"
echo "ユーザー: $RASPBERRY_PI_USER"
echo "転送先ディレクトリ: $REMOTE_DIR"
echo ""

read -p "続行しますか？ (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "転送をキャンセルしました。"
    exit 1
fi

# ディレクトリ作成
echo "📁 リモートディレクトリを作成中..."
ssh $RASPBERRY_PI_USER@$RASPBERRY_PI_IP "mkdir -p $REMOTE_DIR/data"

# ファイル転送
echo "📤 ファイルを転送中..."

# メインファイル
scp teams_simple_laptime_fixed_v2.py $RASPBERRY_PI_USER@$RASPBERRY_PI_IP:$REMOTE_DIR/
scp config_raspberry_pi.json $RASPBERRY_PI_USER@$RASPBERRY_PI_IP:$REMOTE_DIR/config.json

# デバッグヘルパー
scp raspberry_pi_debug_teams.py $RASPBERRY_PI_USER@$RASPBERRY_PI_IP:$REMOTE_DIR/

echo "✅ 転送完了！"
echo ""
echo "🎯 ラズパイでの実行方法:"
echo "ssh $RASPBERRY_PI_USER@$RASPBERRY_PI_IP"
echo "cd $REMOTE_DIR"
echo "python3 teams_simple_laptime_fixed_v2.py"
echo ""
echo "🔧 デバッグ診断:"
echo "python3 raspberry_pi_debug_teams.py"