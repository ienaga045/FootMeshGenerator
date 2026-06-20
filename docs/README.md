# GitHub Pages Web版

このフォルダは、Python版をベースにしたGitHub Pages公開用の静的Webアプリです。

## 動かし方

ローカル確認は、このフォルダを静的サーバで開きます。

```bash
python3 -m http.server 8080 -d docs
```

ブラウザで以下を開きます。

```text
http://127.0.0.1:8080
```

## GitHub Pages公開

GitHubのリポジトリ設定で Pages の公開元を以下にします。

- Source: Deploy from a branch
- Branch: `main`
- Folder: `/docs`

## 仕様

- サーバ不要です。
- Python、PySimpleGUI、OpenCVは使いません。
- Canvasで2Dプレビューを描画します。
- OBJはブラウザ内で生成し、Blobとしてダウンロードします。
- Barefoot modeは5本指を生成します。
- Shoe base modeは足指を生成せず、`toe_box` を生成します。
