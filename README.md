# Xiao ESP32S3 プロジェクト

このプロジェクトは、Seeed Studio XIAO ESP32S3開発ボード用のPlatformIOプロジェクトです。

## 機能

- **LED制御**: 内蔵LED（Pin 21）の点滅制御
- **WiFi接続**: WiFiネットワークへの自動接続
- **シリアル通信**: 115200bpsでの詳細なステータス出力
- **ボタン入力**: ブートボタン（Pin 0）による再起動機能
- **システム監視**: メモリ使用量、WiFi信号強度の表示

## ハードウェア仕様

- **マイコン**: ESP32-S3 (240MHz, デュアルコア)
- **メモリ**: 320KB RAM, 8MB Flash
- **WiFi**: 802.11 b/g/n対応
- **内蔵LED**: Pin 21
- **ブートボタン**: Pin 0

## セットアップ

### 1. 依存関係のインストール

```powershell
pip install --user platformio
```

### 2. プロジェクトのビルド

```powershell
# プロジェクトディレクトリに移動
cd "c:\Users\DELL\OneDrive\ドキュメント\PlatformIO\Projects\XiaoESP32S3"

# ビルド実行
C:\Users\DELL\AppData\Roaming\Python\Python310\Scripts\platformio.exe run
```

### 3. コードのアップロード

デバイスを接続後、以下のコマンドでアップロード：

```powershell
C:\Users\DELL\AppData\Roaming\Python\Python310\Scripts\platformio.exe run --target upload
```

### 4. シリアル監視

```powershell
C:\Users\DELL\AppData\Roaming\Python\Python310\Scripts\platformio.exe device monitor
```

## WiFi設定

`src/main.cpp`の以下の行を編集してWiFi認証情報を設定してください：

```cpp
const char* ssid = "YourWiFiSSID";        // WiFi SSID
const char* password = "YourWiFiPassword"; // WiFiパスワード
```

## 動作

1. **起動時**: システム情報とWiFi接続状況を表示
2. **動作中**: 1秒間隔でLED点滅、システム状態をシリアル出力
3. **ボタン操作**: ブートボタン押下で3秒後に再起動

## トラブルシューティング

### ビルドエラー

- PlatformIOが見つからない場合は、パスを確認してフルパスで実行
- 必要に応じて`platformio.ini`の設定を調整

### アップロードエラー

- USBケーブルとポート接続を確認
- デバイスドライバが正しくインストールされているか確認
- `platformio.ini`の`upload_port`を手動設定

### WiFi接続問題

- SSID・パスワードが正しいか確認
- 2.4GHz帯のWiFiを使用（5GHz非対応）
- WiFi電波強度を確認

## カスタマイズ

- `platformio.ini`: ビルド設定、ライブラリ依存関係
- `src/main.cpp`: メインアプリケーションロジック
- ピン配置やタイミング調整が可能

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。