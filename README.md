# Python Laptime Measurement System

 **Pythonベースのラップタイム計測システム**

ウェブカメラを使用してリアルタイムでレースカーのラップタイムを計測表示するシステムです。

##  主な機能

- **リアルタイム物体検出**: OpenCVによる車両検出追跡
- **ラップタイム計測**: 高精度なタイム計測
- **チーム管理**: 複数チームの成績管理
- **GUI表示**: Pygameによる直感的なインターフェース
- **データ保存**: JSON形式での結果保存
- **音響制御**: ラップ完了時の音響フィードバック

##  システム要件

### ハードウェア
- **ウェブカメラ**: USB接続またはネットワークカメラ
- **PC**: Windows/macOS/Linux対応
- **音響出力**: スピーカーまたはヘッドフォン

### ソフトウェア
- **Python**: 3.8以上
- **OpenCV**: 4.5以上
- **Pygame**: 2.0以上
- **NumPy**: 1.20以上

##  インストール

`ash
# リポジトリをクローン
git clone https://github.com/nkoba3292/python-laptime-measurement.git
cd python-laptime-measurement

# 必要依存関係をインストール
pip install -r requirements.txt
`

##  使用方法

### 基本的な使用
`ash
python main_laptime_system.py
`

### 設定ファイル
config.jsonでシステムパラメータを調整可能

##  操作方法

### キーボード操作
- **S**: レース開始
- **R**: システムリセット
- **Q/ESC**: システム終了
- **SPACE**: 一時停止/再開

### マウス操作
- **クリック**: 検出エリア設定
- **ドラッグ**: エリア範囲調整

##  機能詳細

### 1. 物体検出システム
- **背景差分法**: 動的背景更新
- **車両検出**: 輪郭検出追跡
- **ノイズフィルタ**: 誤検出除去

### 2. ラップタイム計測
- **高精度計測**: ミリ秒単位での計時
- **複数ラップ対応**: 最大3周まで計測
- **ベストタイム記録**: 自動ベストタイム更新

### 3. チーム管理
- **成績管理**: チーム別記録保持
- **ランキング表示**: リアルタイム順位表示
- **結果保存**: JSON形式でのデータ蓄積保持

##  プロジェクト構成

`
python-laptime-measurement/
 main_laptime_system.py     # メインプログラム
 config.json                # 設定ファイル
 requirements.txt           # 必要依存関係
 README.md                  # このファイル
 LICENSE                    # ライセンス
 data/                      # 結果データ
    race_result_*.json
 sounds/                    # 音響ファイル
    start.wav
    finish.wav
 .vscode/                   # VS Code設定
     extensions.json
     settings.json
`

##  開発カスタマイズ

### 検出パラメータ調整
- motion_pixels_threshold: 動作検出の感度
- min_contour_area: 最小検出サイズ
- detection_cooldown: 連続検出防止時間

### カメラ設定
- camera_overview_id: 全体表示用カメラ
- camera_start_line_id: スタートライン用カメラ

##  実践用途

- **ミニ四駆レース**: 複数チーム同時計測
- **ラジコンレース**: 高速物体対応
- **実車レース**: 大型物体検出
- **学校競技**: 人物検出転用

##  トラブルシューティング

### カメラが認識されない
`ash
# カメラデバイス確認
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"
`

### 検出感度が低い
1. 照明条件を改善
2. motion_pixels_thresholdを調整
3. カメラ位置角度を変更

### 音響が出力されない
- Pygameの音響ドライバ確認
- システム音量設定確認
- 音響ファイル形式確認

##  更新履歴

### v13 (最新)
- 検出アルゴリズム改善
- GUI表示最適化
- 安定性向上

##  コントリビューション

1. Forkしてブランチ作成
2. 機能追加バグ修正
3. テスト実行
4. Pull Request作成

##  ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照

##  作成者

- **nkoba3292**
- GitHub: [@nkoba3292](https://github.com/nkoba3292)

##  関連プロジェクト

- [ESP32S3SENSE-Security-Webcamera](https://github.com/nkoba3292/ESP32S3SENSE-Security-Webcamera) - ESP32ベースセキュリティカメラ
