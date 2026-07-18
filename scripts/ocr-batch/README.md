# ocr-batch ─ ローカル無料 OCR バッチ（macOS / Apple Vision）

Apple Vision framework を使った、無料・ローカル・オフラインの OCR ユーティリティ。
画像フォルダを一括 OCR し、Obsidian などで全文検索できるインデックスノート(.md)を生成する。

TRex CLI(`trex --input`)はバッチ用途でハングし stdout に結果を返さないため、
土台に Swift Vision の自作 CLI(`ocr`)を使う。

## 構成

| ファイル | 役割 |
|---|---|
| `ocr.swift` | Vision OCR CLI のソース（`VNRecognizeTextRequest`、ja+en） |
| `ocr`（gitignore） | 上をビルドしたバイナリ。約 345ms/枚（warm） |
| `ocr-images.sh` | フォルダ一括 OCR → .md インデックス生成ラッパー |
| `video-captions.sh` | 動画の焼き込みテロップ/字幕を抽出 → captions.txt / srt |
| `dedupe_captions.py` | 隣接する類似キャプションを縮約（video-captions.sh が使用） |

## ビルド

```bash
swiftc -O ocr.swift -o ocr
```

macOS 実機・Xcode Command Line Tools 必須（Vision / AppKit 依存）。

## 使い方

```bash
# 単一画像 → stdout に OCR テキスト
./ocr image.png

# フォルダ一括 → Obsidian 検索に乗る .md インデックスを生成
#   既定出力先: $OCR_INDEX_DIR（未指定なら $HOME/Documents/vault-main/05_Reference/スクショOCR）
./ocr-images.sh ~/Downloads/screenshots

# 出力先を明示
./ocr-images.sh ~/Downloads/screenshots --out ~/notes/shots-index.md

# 出力先の既定を環境変数で変更
OCR_INDEX_DIR=~/ocr-index ./ocr-images.sh ~/Downloads/screenshots

# .md でなく各画像の隣に <画像名>.txt サイドカー（CLI grep 用・Obsidian 検索対象外）
./ocr-images.sh ~/Downloads/screenshots --txt
```

### 動画の焼き込みテロップ/字幕を抽出

```bash
# 1 秒間隔でサンプリング → <ベース名>.captions.txt を生成
./video-captions.sh demo.mp4

# srt も出力・字幕は画面下 1/3 に多いので --crop-bottom でノイズ減
./video-captions.sh demo.mp4 --srt --crop-bottom

# シーン変化検出モード（実写の目安 0.3）
./video-captions.sh demo.mp4 --scene 0.3 --srt
```

- 対応: `.mp4` / `.mov`。画面に焼き込まれたテロップの OCR のみ（音声・字幕トラックは対象外）
- 連続フレームで同一テロップが数百回重複するのを、抽出時の間引き（`--interval` / `--scene`）と OCR 後の隣接 dedupe（`dedupe_captions.py`）の両方で除去する
- 目安処理量: 1 秒間隔の 10 分動画 ≈ 600 フレーム × 約 345ms ≈ 3.5 分

## 仕様メモ

- 対応形式: png / jpg / jpeg / webp / heic（大小不問）。フォルダ直下のみ・再帰しない・昇順
- 再実行は全再生成（冪等）。ただし出力先に `generated_by: ocr-images.sh` を含まない既存ファイルは上書きせずエラー終了（手書きノート保護）
- Obsidian のコア検索は .md しかインデックスしないため、既定は .md インデックス方式（.txt は CLI grep 用のオプション）

## 用途例

- スクショ束の全文検索インデックス化
- 領収書・レシートの文字化（機微情報をクラウドに出さずローカル完結）
- 過去資料・名刺・書籍ページ写真の一括デジタル化
- 既存サイトのスクショ/バナーから文言だけ一括抽出
- 動画フレームからのテロップ/字幕抽出（`video-captions.sh`）
