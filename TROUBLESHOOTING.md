# XiaoESP32S3 接続トラブルシューティング

## 現在の問題
- デバイスがPCに認識されていない
- COMポートが検出されない
- アップロードが "Could not open AUTO" エラーで失敗

## 解決手順

### 1. 物理的な接続確認
- [ ] USB-Cケーブルがデータ転送対応か確認
- [ ] XiaoESP32S3の電源LEDが点灯しているか確認
- [ ] 別のUSBポートで接続試行
- [ ] デバイスマネージャーで新しいデバイスが表示されるか確認

### 2. ドライバーのインストール
Xiao ESP32S3では以下のドライバーが必要な場合があります：

#### CP210x USB to UART Bridge Driver
- 製造元: Silicon Labs
- ダウンロード: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
- 対象: VID_10C4&PID_EA60

#### CH340/CH341 USB Serial Driver  
- 製造元: WCH
- ダウンロード: http://www.wch-ic.com/downloads/CH341SER_ZIP.html
- 対象: VID_1A86&PID_7523

### 3. Bootloaderモードでの接続
1. XiaoESP32S3をUSBから切断
2. Bootボタン（B）を押しながらUSB接続
3. または接続後にBootボタンを2秒間長押し
4. デバイスマネージャーで新しいCOMポートを確認

### 4. 手動でのCOMポート指定
デバイスが認識されたら、platformio.iniを以下のように変更：

```ini
[env:seeed_xiao_esp32s3]
platform = espressif32
board = seeed_xiao_esp32s3
framework = arduino
upload_port = COM3  ; 実際のCOMポート番号に変更
monitor_port = COM3 ; 同じCOMポート番号
monitor_speed = 115200
```

### 5. 代替アップロード方法
```powershell
# ESPtoolを直接使用（COMポートを手動指定）
C:\Users\DELL\AppData\Roaming\Python\Python310\Scripts\platformio.exe run --target upload --upload-port COM3
```

### 6. デバイス認識確認コマンド
```powershell
# COMポート一覧表示
Get-CimInstance -Class Win32_SerialPort | Select-Object DeviceID, Description

# USBデバイス一覧表示
Get-CimInstance -ClassName Win32_PnPEntity | Where-Object {$_.DeviceID -match "USB.*VID_"}
```

## よくある問題と解決方法

### 問題: "Port is busy" エラー
- 他のプログラム（Arduino IDE、シリアルモニター等）がポートを使用中
- 全てのシリアル関連プログラムを終了して再試行

### 問題: "Device not found" エラー  
- ドライバーが正しくインストールされていない
- Bootloaderモードで接続していない
- USBケーブルが充電専用（データ転送非対応）

### 問題: アップロード中にエラー
1. Bootボタンを押しながらアップロード開始
2. "Connecting..." 表示中にBootボタンを離す
3. 必要に応じてResetボタンも併用

## 確認手順チェックリスト
- [ ] USB-Cケーブル確認
- [ ] 電源LED点灯確認  
- [ ] デバイスマネージャー確認
- [ ] ドライバーインストール
- [ ] Bootloaderモード試行
- [ ] COMポート手動指定
- [ ] 他のシリアルアプリ終了