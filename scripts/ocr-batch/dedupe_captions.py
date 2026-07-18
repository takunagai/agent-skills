#!/usr/bin/env python3
"""
dedupe_captions.py ─ フレーム順の (秒, OCRテキスト) 列を受け取り、
隣接する類似キャプションを 1 本に縮約して (開始秒, 終了秒, テキスト) 列を返す。

入力: argv[1] = マニフェスト TSV。各行 "<秒>\t<テキストファイルパス>"（フレーム順）
      argv[2] = 縮約後キャプション本文の出力先ディレクトリ
出力: stdout に "<開始秒> <終了秒> <キャプション本文ファイルパス>" を 1 行 1 キャプション

方針:
- 正規化: 各ブロックの前後空白・空行を除去。空になったブロックは捨てる
- 隣接ブロックを difflib.SequenceMatcher の ratio で比較し、>= 0.90 なら同一とみなす
  （OCR の揺れ ─ 句読点・空白差 ─ を吸収。完全一致だけでは不足）
- 同一なら先行を残し、表示終了時刻を後続フレームの時刻まで延長する
- 比較は隣接のみ。別ブロックを挟んで再出現した同文は別キャプションとして残す
本文をパイプでなくファイルで受け渡すのは、OCR テキストの改行・引用符が
シェルのクォートを壊すのを避けるため。
"""
import sys
import os
import difflib

RATIO_THRESHOLD = 0.90  # 隣接キャプションを同一とみなす類似度の下限


def normalize(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 3:
        sys.stderr.write("usage: dedupe_captions.py <manifest.tsv> <outdir>\n")
        return 2
    manifest_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    items = []  # [(sec, block)]
    with open(manifest_path, encoding="utf-8") as mf:
        for line in mf:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            sec_str, text_path = parts
            try:
                sec = float(sec_str)
            except ValueError:
                continue
            try:
                with open(text_path, encoding="utf-8") as tf:
                    raw = tf.read()
            except OSError:
                raw = ""
            block = normalize(raw)
            if block:
                items.append((sec, block))

    caps = []  # [start, end, text]
    for sec, block in items:
        if caps and difflib.SequenceMatcher(None, caps[-1][2], block).ratio() >= RATIO_THRESHOLD:
            caps[-1][1] = sec  # 表示終了を延長
        else:
            caps.append([sec, sec, block])

    for i, (start, end, text) in enumerate(caps):
        cap_path = os.path.join(out_dir, f"cap_{i + 1:04d}.txt")
        with open(cap_path, "w", encoding="utf-8") as cf:
            cf.write(text)
        sys.stdout.write(f"{start:.3f} {end:.3f} {cap_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
