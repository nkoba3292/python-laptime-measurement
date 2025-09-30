# VS Code拡張機能インストールガイド
# ラズベリーパイ5開発環境用

## 必須拡張機能リスト

### 1. Remote - SSH
- 拡張機能ID: `ms-vscode-remote.remote-ssh`
- 機能: ラズパイにSSH経由で直接アクセス
- インストール: VS Code → Extensions → "Remote - SSH" で検索

### 2. Remote - SSH: Editing Configuration Files
- 拡張機能ID: `ms-vscode-remote.remote-ssh-edit`
- 機能: SSH設定ファイルの編集サポート
- 自動的にRemote - SSHと一緒にインストールされる

### 3. SFTP
- 拡張機能ID: `Natizyskunk.sftp`
- 機能: ファイル同期・転送
- インストール: VS Code → Extensions → "SFTP" で検索

### 4. Python（推奨）
- 拡張機能ID: `ms-python.python`
- 機能: Python開発サポート
- リモート環境でのPythonデバッグに必要

## インストール方法

### VS Codeでの手動インストール:
1. VS Code起動
2. Ctrl+Shift+X (Extensions)
3. 各拡張機能名で検索してインストール

### コマンドラインでの一括インストール:
```bash
code --install-extension ms-vscode-remote.remote-ssh
code --install-extension ms-vscode-remote.remote-ssh-edit
code --install-extension Natizyskunk.sftp
code --install-extension ms-python.python
```

## 設定確認
拡張機能インストール後、左下に「><」アイコンが表示されることを確認