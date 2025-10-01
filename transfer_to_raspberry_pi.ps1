# transfer_to_raspberry_pi.ps1
# Raspberry Pi へのファイル転送スクリプト (PowerShell版)

param(
    [string]$RaspberryPiIP = "192.168.1.100",  # デフォルトIP（変更してください）
    [string]$Username = "pi",
    [string]$RemoteDir = "~/laptime_system"
)

Write-Host "🍓 Raspberry Pi へのファイル転送スクリプト" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "設定:" -ForegroundColor Yellow
Write-Host "  ラズパイIP: $RaspberryPiIP"
Write-Host "  ユーザー: $Username"
Write-Host "  転送先: $RemoteDir"
Write-Host ""

# 確認
$confirm = Read-Host "続行しますか？ (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "転送をキャンセルしました。" -ForegroundColor Red
    exit 1
}

# SSH/SCPが利用可能かチェック
try {
    ssh -V 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ SSH が見つかりません。OpenSSH をインストールしてください。" -ForegroundColor Red
        Write-Host "   Windows: Settings > Apps > Optional Features > OpenSSH Client" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ SSH コマンドが利用できません。" -ForegroundColor Red
    exit 1
}

# リモートディレクトリ作成
Write-Host "📁 リモートディレクトリを作成中..." -ForegroundColor Blue
ssh $Username@$RaspberryPiIP "mkdir -p $RemoteDir/data"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SSH接続に失敗しました。IPアドレスとSSH設定を確認してください。" -ForegroundColor Red
    exit 1
}

# ファイル転送
Write-Host "📤 ファイルを転送中..." -ForegroundColor Blue

$filesToTransfer = @(
    @{Source="teams_simple_laptime_fixed_v2.py"; Dest="teams_simple_laptime_fixed_v2.py"},
    @{Source="config_raspberry_pi.json"; Dest="config.json"},
    @{Source="raspberry_pi_debug_teams.py"; Dest="raspberry_pi_debug_teams.py"}
)

foreach ($file in $filesToTransfer) {
    $source = $file.Source
    $dest = $file.Dest
    
    if (Test-Path $source) {
        Write-Host "  📄 転送中: $source -> $dest" -ForegroundColor Cyan
        scp $source $Username@${RaspberryPiIP}:$RemoteDir/$dest
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ 成功" -ForegroundColor Green
        } else {
            Write-Host "    ❌ 失敗" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠️ ファイルが見つかりません: $source" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ 転送完了！" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 ラズパイでの実行方法:" -ForegroundColor Yellow
Write-Host "ssh $Username@$RaspberryPiIP"
Write-Host "cd $RemoteDir"
Write-Host "python3 teams_simple_laptime_fixed_v2.py"
Write-Host ""
Write-Host "🔧 デバッグ診断:" -ForegroundColor Yellow
Write-Host "python3 raspberry_pi_debug_teams.py"
Write-Host ""
Write-Host "⚠️ 重要な設定:" -ForegroundColor Red
Write-Host "  1. ラズパイでSSHを有効化"
Write-Host "  2. カメラを2台接続"
Write-Host "  3. 必要なパッケージをインストール:"
Write-Host "     sudo apt install python3-opencv python3-pygame"
Write-Host "     pip3 install opencv-python pygame numpy"

# 接続テスト用コマンドの提案
Write-Host ""
Write-Host "🧪 接続テスト:" -ForegroundColor Cyan
Write-Host "ssh $Username@$RaspberryPiIP 'python3 --version && python3 -c \"import cv2, pygame; print(\"パッケージOK\")\"'"