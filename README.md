<<<<<<< HEAD
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
=======
# README.md
# 自動運転ミニカー予選タイム計測システム

## 概要
ラズベリーパイ5 + LOGICOOL C270 x2台を使用した自動運転ミニカーの予選タイム計測システムです。

## 主な機能
- 🎯 **デュアルカメラシステム**
  - 俯瞰カメラ: コース全体を監視（メイン表示）
  - スタートライン用カメラ: 車両通過検出（左下小窓表示）

- ⏱️ **自動ラップタイム計測**
  - スタートライン通過の自動検出
  - 3周分のラップタイム測定
  - リアルタイム表示と自動保存

- 🎵 **効果音システム**
  - レーススタート時の効果音
  - ゴール時の効果音

- 📊 **データ管理**
  - ラップタイム自動保存（JSON形式）
  - レース結果の詳細記録

## システム要件
- Raspberry Pi 5
- LOGICOOL C270 Webカメラ x2台
- Python 3.8+
- OpenCV, NumPy, Pygame

## インストール
```bash
cd C:\Users\DELL\20250928_Python_LAPTIME_WEBCAM
pip install -r requirements.txt
```

## 使用方法
```bash
python main_laptime_system.py
```

### 操作方法
- **'r'キー**: レースリセット
- **'q'キー**: システム終了

### システムの流れ
1. カメラ初期化とキャリブレーション
2. 車両がスタートラインを通過 → レース開始
3. 各ラップの自動計測と表示
4. 3周目の半周で画面上のタイマー非表示
5. 3周完了で自動結果保存

## ファイル構成
```
C:\Users\DELL\20250928_Python_LAPTIME_WEBCAM\
├── main_laptime_system.py   # メインプログラム
├── config.json              # システム設定
├── requirements.txt         # 必要ライブラリ
├── README.md               # このファイル
├── sounds\                 # 効果音ファイル
│   ├── start.wav
│   └── finish.wav
└── data\                   # レース結果保存先
    └── race_result_*.json
```

## 設定項目
`config.json`で各種パラメータを調整可能：
- カメラ解像度・FPS
- 検出感度設定
- 表示レイアウト
- 効果音設定

## トラブルシューティング
- カメラが認識されない場合、USBポートを確認
- 検出感度が適切でない場合、`config.json`の`detection_settings`を調整
- 音が出ない場合、音量設定とスピーカー接続を確認

## 開発者向け
システムの拡張や改良については、各クラスのメソッドを参照してください。
特にスタートライン検出アルゴリズムは環境に応じてカスタマイズが必要です。
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
