# image-gen-handoff

Codex の `image_gen` / Image 2.0 で大量生成した後に、保存済み画像と session JSONL から成果物を整理する後処理スキルです。画像生成そのものは行いません。

## できること

- 保存済み画像を走査し、`sha256`、寸法、ファイルサイズ、mtime を記録
- Codex session JSONL から `image_generation_call` と最終生成プロンプト候補を抽出
- 画像とプロンプトを対応付け、`high` / `medium` / `low` / `missing` の信頼度を記録
- `manifest.json` と確認用 `manifest.md` を生成
- `作業記録/<batch-name>_引き継ぎ.md` のような軽量な引き継ぎノートを生成
- 明示指定時のみ、JSONL 内の未保存画像抽出、画像コピー、JSONL 圧縮コピーを実行

## やらないこと

- デフォルトでは既存画像を移動・リネームしません。
- デフォルトでは JSONL を圧縮・移動しません。
- JSONL 削除機能はありません。
- 取得できないプロンプトを推測で埋めません。

## 基本コマンド

まず dry-run で件数と対応付けの見込みを確認します。

```bash
python3 <SKILL_DIR>/scripts/build_manifest.py \
  --project-root <PROJECT_ROOT> \
  --image-dir <IMAGE_DIR> \
  --jsonl <CODEX_SESSION_JSONL> \
  --batch-name <BATCH_NAME> \
  --out-json <IMAGE_DIR>/<BATCH_NAME>-manifest.json \
  --out-md <IMAGE_DIR>/<BATCH_NAME>-manifest.md \
  --handoff-md '作業記録/<BATCH_NAME>_引き継ぎ.md' \
  --expected-count <EXPECTED_COUNT> \
  --dry-run
```

問題なければ `--dry-run` を外して生成します。

```bash
python3 <SKILL_DIR>/scripts/build_manifest.py \
  --project-root <PROJECT_ROOT> \
  --image-dir <IMAGE_DIR> \
  --jsonl <CODEX_SESSION_JSONL> \
  --batch-name <BATCH_NAME> \
  --out-json <IMAGE_DIR>/<BATCH_NAME>-manifest.json \
  --out-md <IMAGE_DIR>/<BATCH_NAME>-manifest.md \
  --handoff-md '作業記録/<BATCH_NAME>_引き継ぎ.md'
```

生成後は manifest を再検証します。

```bash
python3 <SKILL_DIR>/scripts/validate_manifest.py \
  --manifest <PROJECT_ROOT>/<IMAGE_DIR>/<BATCH_NAME>-manifest.json
```

## 個別機能

### JSONL イベント抽出

```bash
python3 <SKILL_DIR>/scripts/extract_imagegen_events.py \
  --jsonl <CODEX_SESSION_JSONL> \
  --out <OUTPUT_JSON> \
  --limit-events 20
```

JSON 出力には base64 画像本体を含めません。

### JSONL から画像を抽出

未保存画像が JSONL にしかない場合だけ使います。

```bash
python3 <SKILL_DIR>/scripts/extract_imagegen_events.py \
  --jsonl <CODEX_SESSION_JSONL> \
  --extract-images \
  --extract-dir <OUTPUT_DIR>
```

### 画像コピーと命名

既存画像はそのままにし、コピー先へだけ書き出します。

```bash
python3 <SKILL_DIR>/scripts/build_manifest.py \
  --project-root <PROJECT_ROOT> \
  --image-dir <IMAGE_DIR> \
  --jsonl <CODEX_SESSION_JSONL> \
  --batch-name <BATCH_NAME> \
  --copy-to <COPIED_IMAGE_DIR> \
  --rename-format '{batch}-{index:03d}{ext}'
```

### JSONL 圧縮コピー

manifest 作成後に、必要な場合だけ圧縮コピーします。元 JSONL は削除されません。

```bash
python3 <SKILL_DIR>/scripts/archive_jsonl.py \
  --jsonl <CODEX_SESSION_JSONL> \
  --manifest <PROJECT_ROOT>/<IMAGE_DIR>/<BATCH_NAME>-manifest.json \
  --archive-dir <ARCHIVE_DIR> \
  --format gz
```

## 出力

標準的な出力は次の 3 点です。

```text
<IMAGE_DIR>/<BATCH_NAME>-manifest.json
<IMAGE_DIR>/<BATCH_NAME>-manifest.md
作業記録/<BATCH_NAME>_引き継ぎ.md
```

`manifest.json` は機械処理用、`manifest.md` は確認用、引き継ぎノートは次セッションで作業を再開するための軽量メモです。

## 注意

`confidence=low` と `confidence=missing` は必ず目視確認してください。`confidence=high` でも画像内容そのものを保証するものではなく、ファイル名・生成順・プロンプト番号などの対応付け根拠が強いという意味です。
