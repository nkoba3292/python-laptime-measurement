<<<<<<< HEAD
# Python Laptime Measurement System
=======
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
>>>>>>> 36cde15f076a9839f8b5486f9900884726a3a0b1

🏁 **Pythonベースのラップタイム測定システム**

ウェブカメラを使用してリアルタイムでレースカーのラップタイムを測定・表示するシステムです。

## 🎯 主な機能

- **リアルタイム映像解析**: OpenCVによる物体検知・追跡
- **ラップタイム測定**: 高精度なタイム計測
- **チーム管理**: 複数チームの成績管理
- **GUI表示**: Pygameによる直感的なインターフェース
- **データ保存**: JSON形式での結果保存
- **音声通知**: ラップ完了時の音声フィードバック

## 🔧 システム要件

### ハードウェア
- **ウェブカメラ**: USB接続またはネットワークカメラ
- **PC**: Windows/macOS/Linux対応
- **音響出力**: スピーカーまたはヘッドフォン

### ソフトウェア
- **Python**: 3.8以上
- **OpenCV**: 4.5以上
- **Pygame**: 2.0以上
- **NumPy**: 1.20以上

## 📦 インストール

```bash
# リポジトリをクローン
git clone https://github.com/nkoba3292/python-laptime-measurement.git
cd python-laptime-measurement

# 依存関係をインストール
pip install -r requirements.txt
```

## 🚀 使用方法

### 基本的な使用
```bash
python teams_simple_laptime_fixed_v13.py
```

### 設定ファイル
`config.json`でシステムパラメータを調整：

```json
{
  "camera_overview_id": 0,
  "camera_start_line_id": 0,
  "camera_settings": {
    "frame_width": 640,
    "frame_height": 480
  },
  "detection_settings": {
    "motion_pixels_threshold": 15000,
    "min_contour_area": 1000,
    "detection_conditions_required": 2
  },
  "race_settings": {
    "max_laps": 3,
    "detection_cooldown": 3.0
  }
}
```

## 🎮 操作方法

### キーボード操作
- **S**: レース開始
- **R**: システムリセット
- **Q/ESC**: システム終了
- **SPACE**: 一時停止/再開

<<<<<<< HEAD
### マウス操作
- **クリック**: 検知エリア設定
- **ドラッグ**: エリア範囲調整

## 📊 機能詳細

### 1. 映像解析システム
- **背景差分法**: 動的背景更新
- **物体検知**: 輪郭検出・追跡
- **ノイズフィルタ**: 誤検知除去

### 2. ラップタイム計測
- **高精度計測**: ミリ秒単位での計時
- **複数ラップ対応**: 最大3周まで計測
- **ベストタイム記録**: 自動ベストタイム更新

### 3. チーム管理
- **成績管理**: チーム別記録保持
- **ランキング表示**: リアルタイム順位表示
- **結果保存**: JSON形式でのデータ永続化

## 📁 プロジェクト構造

```
python-laptime-measurement/
├── teams_simple_laptime_fixed_v13.py  # メインプログラム
├── config.json                        # 設定ファイル
├── requirements.txt                    # 依存関係
├── README.md                          # このファイル
├── data/                              # 結果データ
│   └── race_result_*.json
├── sounds/                            # 音声ファイル
├── test_images_from_raspi/            # テスト用画像
└── .vscode/                           # VS Code設定
```

## 🛠️ 開発・カスタマイズ

### 検知パラメータ調整
```python
# motion_pixels_threshold: 動体検知の感度
# min_contour_area: 最小検知サイズ
# detection_cooldown: 連続検知防止時間
```

### カメラ設定
```python
# 複数カメラ使用時
camera_overview_id = 0    # 全体表示用カメラ
camera_start_line_id = 1  # スタートライン用カメラ
```

## 🏆 実績・用途

- **ミニ四駆レース**: 複数チーム同時計測
- **ラジコンレース**: 高速車両対応
- **実車レース**: 大型車両検知
- **歩行競技**: 人物検知応用

## 🐛 トラブルシューティング

### カメラが認識されない
```bash
# カメラデバイス確認
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"
```

### 検知精度が低い
1. 照明条件を改善
2. `motion_pixels_threshold`を調整
3. カメラ位置・角度を変更

### 音声が再生されない
- Pygameの音声ドライバ確認
- システム音量設定確認
- 音声ファイル形式確認

## 📝 更新履歴

### v13 (最新)
- 検知アルゴリズム改良
- GUI表示最適化
- 安定性向上

### v12
- チーム管理機能追加
- 音声フィードバック実装

### v11
- 複数カメラ対応
- 設定ファイル外部化

## 🤝 コントリビューション

1. Forkしてブランチ作成
2. 機能追加・バグ修正
3. テスト実行
4. Pull Request作成

## 📄 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照

## 👤 作成者

- **nkoba3292**
- GitHub: [@nkoba3292](https://github.com/nkoba3292)

## 🔗 関連プロジェクト

- [ESP32S3SENSE-Security-Webcamera](https://github.com/nkoba3292/ESP32S3SENSE-Security-Webcamera) - ESP32ベースセキュリティカメラ
=======
## 開発者向け
システムの拡張や改良については、各クラスのメソッドを参照してください。
特にスタートライン検出アルゴリズムは環境に応じてカスタマイズが必要です。
>>>>>>> 62bc938e0014b1c05c884bb8ba69f934c8036058
>>>>>>> 36cde15f076a9839f8b5486f9900884726a3a0b1
