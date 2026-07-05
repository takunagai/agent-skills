#!/bin/bash
# Claude Code のフォーク（/branch 派生）セッションを安全に削除するヘルパー。
#
# 使い方:
#   delete-fork.sh <sid>                 # dry-run（削除対象を表示するだけ。既定）
#   delete-fork.sh <sid> --apply         # 実行（ゴミ箱 ~/.claude/.trash へ退避＝復元可）
#   delete-fork.sh <sid> --apply --purge # 実行（rm で完全削除＝復元不可）
#
# 安全ガード:
#   - SID は UUID 形式のみ受理
#   - 対象 JSONL に forkedFrom が無ければ中止（＝大元セッションを誤爆しない）
#   - 対象が現在実行中セッション($CLAUDE_CODE_SESSION_ID)なら中止（自分自身は消せない）
#   - ファイルはフル ID の完全一致でのみ特定。sessions メタは sessionId を厳密一致で判定
#   - 全文ログはヘッダ行(**セッションID**: <sid>)で判定し、本文に sid を含むだけの別ログは対象外
#   - 既定はゴミ箱退避（復元可）。--purge で完全削除

set -uo pipefail

SID="${1:-}"
APPLY=0
PURGE=0
shift 2>/dev/null || true
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    --purge) PURGE=1 ;;
    *) echo "ERROR: 不明な引数: $a" >&2; exit 2 ;;
  esac
done

# 1) UUID 形式チェック
if ! printf '%s' "$SID" | grep -qiE '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'; then
  echo "ERROR: セッション ID が UUID 形式ではありません: '$SID'" >&2
  exit 2
fi

PROJECTS="$HOME/.claude/projects"

# 2) transcript を特定（フル ID 完全一致）
JSONL=$(find "$PROJECTS" -type f -name "$SID.jsonl" 2>/dev/null | head -1)
if [ -z "$JSONL" ]; then
  echo "ERROR: セッション $SID の transcript が見つかりません（既に削除済み？）" >&2
  exit 4
fi
PROJ_DIR=$(dirname "$JSONL")

# 3) forkedFrom（親）を取得
#    forkedFrom は文字列の場合と {'sessionId':..., 'messageUuid':...} 形式の場合がある
FORKED_FROM=$(head -1 "$JSONL" | python3 -c "import sys,json
try:
    ff = json.loads(sys.stdin.read()).get('forkedFrom')
    if isinstance(ff, dict):
        print(ff.get('sessionId') or '')
    elif isinstance(ff, str):
        print(ff)
    else:
        print('')
except Exception:
    print('')" 2>/dev/null)

# 4) 自分自身は消せない
CUR="${CLAUDE_CODE_SESSION_ID:-}"
if [ -n "$CUR" ] && [ "$CUR" = "$SID" ]; then
  echo "ERROR: 対象は現在実行中のセッションです。自分自身は削除できません。" >&2
  if [ -n "$FORKED_FROM" ]; then
    echo "       元へ戻る:  claude -r $FORKED_FROM   （その後にこのスキルを実行）" >&2
  else
    echo "       別ターミナル / 別セッションから実行してください。" >&2
  fi
  exit 3
fi

# 5) フォーク判定（forkedFrom が無ければ大元の可能性 → 中止）
if [ -z "$FORKED_FROM" ]; then
  echo "WARNING: このセッションには forkedFrom がありません（フォークではなく大元の可能性）。" >&2
  echo "         安全のため中止します。" >&2
  exit 5
fi

# 6) 稼働中ヒューリスティック（mtime 直近なら別所で稼働中かも）
NOW=$(date +%s)
MT=$(stat -f %m "$JSONL" 2>/dev/null || echo 0)
if [ $((NOW - MT)) -lt 60 ]; then
  echo "WARNING: transcript が直近 60 秒以内に更新されています。別ターミナルで稼働中かもしれません。" >&2
fi

# 7) 削除対象を収集
TARGETS=("$JSONL")
[ -d "$PROJ_DIR/$SID" ] && TARGETS+=("$PROJ_DIR/$SID")   # subagents 等の付随ディレクトリ

# sessions メタ（sessionId 厳密一致のみ）
SESS_DIR="$HOME/.claude/sessions"
if [ -d "$SESS_DIR" ]; then
  while IFS= read -r f; do
    [ -n "$f" ] && TARGETS+=("$f")
  done < <(python3 - "$SESS_DIR" "$SID" <<'PY'
import sys, glob, json, os
sdir, sid = sys.argv[1], sys.argv[2]
for f in glob.glob(os.path.join(sdir, "*.json")):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if d.get("sessionId") == sid:
        print(f)
PY
)
fi

# Vault 索引行・全文ログ（範囲: 実体＋Vault）
# 既定の Vault パスは自分の環境に合わせて変更してください（環境変数 CLAUDE_SESSION_INDEX_VAULT が優先）。
VAULT="${CLAUDE_SESSION_INDEX_VAULT:-$HOME/Documents/vault-main}"
INDEX_DIR="$VAULT/Log/Session/_Index"
LOG_DIR="$VAULT/Log/Session"
INDEX_HITS=()
LOG_HITS=()
if [ -d "$INDEX_DIR" ]; then
  while IFS= read -r f; do [ -n "$f" ] && INDEX_HITS+=("$f"); done \
    < <(grep -lF "$SID" "$INDEX_DIR"/*.md 2>/dev/null)
fi
if [ -d "$LOG_DIR" ]; then
  while IFS= read -r f; do [ -n "$f" ] && LOG_HITS+=("$f"); done \
    < <(grep -lE "^\*\*セッションID\*\*: $SID" "$LOG_DIR"/*.md 2>/dev/null)
fi

# 8) プレビュー
echo "==== フォーク削除プレビュー ===="
echo "対象セッション   : $SID"
echo "フォーク元(残す) : $FORKED_FROM"
echo "プロジェクト     : $PROJ_DIR"
echo "方式             : $([ $PURGE -eq 1 ] && echo '完全削除 (rm)' || echo 'ゴミ箱退避（復元可）')"
echo "--- セッション実体（削除/退避）---"
for t in "${TARGETS[@]}"; do echo "  $t"; done
echo "--- Vault 全文ログ（ファイルごと削除/退避）---"
if [ ${#LOG_HITS[@]} -gt 0 ]; then for t in "${LOG_HITS[@]}"; do echo "  $t"; done; else echo "  （なし）"; fi
echo "--- Vault 索引（該当行のみ削除。ファイルは残す）---"
if [ ${#INDEX_HITS[@]} -gt 0 ]; then
  for t in "${INDEX_HITS[@]}"; do echo "  $t : $(grep -cF "$SID" "$t") 行"; done
else
  echo "  （なし）"
fi

if [ $APPLY -eq 0 ]; then
  echo
  echo "これは dry-run です。実行するには --apply（完全削除は --apply --purge）を付けてください。"
  exit 0
fi

# 9) 実行
TS=$(date +%Y%m%d_%H%M%S)
TRASH="$HOME/.claude/.trash/forks/${SID}_${TS}"
[ $PURGE -eq 0 ] && mkdir -p "$TRASH"

relpath() {  # $1=絶対パス → 退避先の相対構造
  local p="$1" rel="${1#"$HOME"/}"
  if [ "$rel" = "$p" ]; then rel="external/$(printf '%s' "$p" | sed 's#^/##; s#/#_#g')"; fi
  printf '%s' "$rel"
}
move_or_rm() {  # $1=path
  local p="$1"
  if [ $PURGE -eq 1 ]; then
    rm -rf -- "$p"
  else
    local dest
    dest="$TRASH/$(relpath "$p")"
    mkdir -p "$(dirname "$dest")"
    mv -- "$p" "$dest"
  fi
}

for t in "${TARGETS[@]}"; do [ -e "$t" ] && move_or_rm "$t"; done
if [ ${#LOG_HITS[@]} -gt 0 ]; then for t in "${LOG_HITS[@]}"; do [ -e "$t" ] && move_or_rm "$t"; done; fi

# 索引は「行だけ」削除。先に索引ファイルをバックアップ（退避モード時）
if [ ${#INDEX_HITS[@]} -gt 0 ]; then
  for t in "${INDEX_HITS[@]}"; do
    [ -e "$t" ] || continue
    if [ $PURGE -eq 0 ]; then
      dest="$TRASH/_index-backup/$(relpath "$t")"
      mkdir -p "$(dirname "$dest")"
      cp -- "$t" "$dest"
    fi
    tmp="$t.tmp.$$"
    grep -vF "$SID" "$t" > "$tmp" && mv "$tmp" "$t"
  done
fi

echo
echo "完了しました。"
if [ $PURGE -eq 0 ]; then
  echo "退避先（復元可）: $TRASH"
  echo "完全に消すには、この退避先を後で削除するか、--purge で実行してください。"
fi