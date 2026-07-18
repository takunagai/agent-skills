#!/usr/bin/env bash
#
# video-captions.sh ─ ローカル動画(.mp4/.mov)の焼き込みテロップ/字幕を
# ffmpeg でフレーム間引き抽出 → Vision OCR(ocr) → 隣接 dedupe し、
# <ベース名>.captions.txt と（任意で）<ベース名>.srt を生成する。
#
# 音声の文字起こしや字幕トラック(mov_text)の抽出は対象外（画面に焼き込まれた文字の OCR のみ）。
#
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OCR="$SCRIPT_DIR/ocr"
DEDUPE="$SCRIPT_DIR/dedupe_captions.py"

print_help() {
  cat <<'HELP'
usage: video-captions.sh <動画(.mp4/.mov)> [オプション]

  --interval <秒>   サンプリング間隔（既定 1。1〜2 を推奨）
  --scene <閾値>    シーン変化検出モードに切替（実写の目安 0.3。指定時 --interval は無視）
  --srt             簡易 .srt も出力する
  --crop-bottom     フレーム下 1/3 のみを OCR 対象にする（字幕向け・ノイズ減）
  --out <dir>       出力先ディレクトリ（既定: 動画と同じディレクトリ）
  --keep-frames     一時フレームを削除せず残す（デバッグ用・パスを表示）
  --help            この使い方を表示

出力:
  <ベース名>.captions.txt   常に生成（[HH:MM:SS] テキスト 形式）
  <ベース名>.srt            --srt 時のみ（標準 srt 形式）

対象は画面に焼き込まれたテロップ/字幕の OCR のみ。音声・字幕トラックは扱わない。
HELP
}

# ---- 引数パース ----
INTERVAL=1; SCENE=""; SRT=0; CROP=0; OUT=""; KEEP=0; VIDEO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --help) print_help; exit 0 ;;
    --interval) shift; [ $# -gt 0 ] || { echo "error: --interval に値が必要" >&2; exit 2; }; INTERVAL="$1"; shift ;;
    --scene)    shift; [ $# -gt 0 ] || { echo "error: --scene に値が必要" >&2; exit 2; }; SCENE="$1"; shift ;;
    --srt) SRT=1; shift ;;
    --crop-bottom) CROP=1; shift ;;
    --out) shift; [ $# -gt 0 ] || { echo "error: --out にパスが必要" >&2; exit 2; }; OUT="$1"; shift ;;
    --keep-frames) KEEP=1; shift ;;
    -*) echo "error: 不明なオプション: $1" >&2; exit 2 ;;
    *) if [ -z "$VIDEO" ]; then VIDEO="$1"; else echo "error: 引数が多すぎます: $1" >&2; exit 2; fi; shift ;;
  esac
done

[ -n "$VIDEO" ] || { echo "error: 動画ファイルを指定してください" >&2; print_help >&2; exit 2; }
[ -f "$VIDEO" ] || { echo "error: ファイルが存在しません: $VIDEO" >&2; exit 2; }
case "$(printf '%s' "$VIDEO" | tr 'A-Z' 'a-z')" in
  *.mp4|*.mov) : ;;
  *) echo "error: .mp4 / .mov のみ対応: $VIDEO" >&2; exit 2 ;;
esac
[ -x "$OCR" ]   || { echo "error: ocr バイナリがありません: $OCR" >&2; exit 3; }
[ -f "$DEDUPE" ] || { echo "error: dedupe ヘルパーがありません: $DEDUPE" >&2; exit 3; }

BASE="$(basename "$VIDEO")"; BASE="${BASE%.*}"
if [ -z "$OUT" ]; then OUT="$(cd "$(dirname "$VIDEO")" && pwd)"; fi
mkdir -p "$OUT"

FRAMES="$(mktemp -d)"
cleanup() {
  if [ "$KEEP" -eq 1 ]; then echo "frames kept: $FRAMES" >&2; return; fi
  rm -rf "$FRAMES"
}
trap cleanup EXIT

CROPF=""; [ "$CROP" -eq 1 ] && CROPF="crop=iw:ih/3:0:2*ih/3,"
MANIFEST="$FRAMES/manifest.tsv"; : > "$MANIFEST"

# ---- フレーム抽出（+ 各フレームの秒との紐付け） ----
if [ -n "$SCENE" ]; then
  # シーン検出モード: 先頭フレーム必須(eq(n,0)) + シーン変化。秒は showinfo の pts_time から
  ffmpeg -y -loglevel info -i "$VIDEO" \
    -vf "${CROPF}select='eq(n,0)+gt(scene,${SCENE})',showinfo" -fps_mode vfr \
    "$FRAMES/frame_%06d.png" 2> "$FRAMES/showinfo.log" || true
  PTS=()
  while IFS= read -r _pts; do PTS+=("$_pts"); done \
    < <(grep -oE 'pts_time:[0-9.]+' "$FRAMES/showinfo.log" | sed 's/pts_time://')
  i=0
  for f in "$FRAMES"/frame_*.png; do
    [ -e "$f" ] || continue
    sec="${PTS[$i]:-0}"; i=$((i+1))
    "$OCR" "$f" > "$f.txt" 2>/dev/null || :
    printf '%s\t%s\n' "$sec" "$f.txt" >> "$MANIFEST"
  done
else
  # インターバルモード: fps=1/interval。連番 N(1始まり) → 秒 = (N-1)*interval
  ffmpeg -y -loglevel error -i "$VIDEO" -vf "${CROPF}fps=1/${INTERVAL}" "$FRAMES/frame_%06d.png" || true
  n=0
  for f in "$FRAMES"/frame_*.png; do
    [ -e "$f" ] || continue
    sec="$(awk "BEGIN{printf \"%.3f\", ${n}*${INTERVAL}}")"; n=$((n+1))
    "$OCR" "$f" > "$f.txt" 2>/dev/null || :
    printf '%s\t%s\n' "$sec" "$f.txt" >> "$MANIFEST"
  done
fi

nframes="$(grep -c . "$MANIFEST" 2>/dev/null || echo 0)"
echo "抽出フレーム: ${nframes}（OCR 済み）" >&2

# ---- dedupe（隣接類似の縮約はヘルパーに委譲） ----
CAPDIR="$FRAMES/caps"; mkdir -p "$CAPDIR"
starts=(); ends=(); paths=()
while read -r s e p; do
  [ -n "${s:-}" ] || continue
  starts+=("$s"); ends+=("$e"); paths+=("$p")
done < <(python3 "$DEDUPE" "$MANIFEST" "$CAPDIR")
ncap=${#starts[@]}

# ---- 時刻フォーマッタ ----
fmt_ts()    { awk "BEGIN{s=$1; h=int(s/3600); m=int((s-h*3600)/60); sec=int(s-h*3600-m*60); printf \"%02d:%02d:%02d\", h,m,sec}"; }
fmt_ts_ms() { awk "BEGIN{s=$1; h=int(s/3600); m=int((s-h*3600)/60); sec=int(s-h*3600-m*60); ms=int((s-int(s))*1000+0.5); printf \"%02d:%02d:%02d,%03d\", h,m,sec,ms}"; }

# ---- captions.txt（常時） ----
TXT_OUT="$OUT/$BASE.captions.txt"; : > "$TXT_OUT"
for ((idx=0; idx<ncap; idx++)); do
  ts="$(fmt_ts "${starts[$idx]}")"
  first="$(head -1 "${paths[$idx]}")"
  printf '[%s] %s\n' "$ts" "$first" >> "$TXT_OUT"
  tail -n +2 "${paths[$idx]}" | while IFS= read -r l; do printf '           %s\n' "$l" >> "$TXT_OUT"; done
done
echo "生成: ${TXT_OUT}（${ncap} キャプション）"

# ---- srt（--srt 時のみ。終了時刻 = 次キャプション開始、最終のみ +2 秒） ----
if [ "$SRT" -eq 1 ]; then
  SRT_OUT="$OUT/$BASE.srt"; : > "$SRT_OUT"
  last=$((ncap - 1))
  for ((idx=0; idx<ncap; idx++)); do
    s="${starts[$idx]}"
    if [ "$idx" -lt "$last" ]; then e="${starts[$((idx + 1))]}"; else e="$(awk "BEGIN{printf \"%.3f\", $s + 2}")"; fi
    printf '%s\n' "$((idx + 1))" >> "$SRT_OUT"
    printf '%s --> %s\n' "$(fmt_ts_ms "$s")" "$(fmt_ts_ms "$e")" >> "$SRT_OUT"
    cat "${paths[$idx]}" >> "$SRT_OUT"
    printf '\n\n' >> "$SRT_OUT"
  done
  echo "生成: $SRT_OUT"
fi
