#!/usr/bin/env bash
# sync-styles.sh
# references/styles/ は共有ライブラリ(_image-styles)への symlink。
# .skill としてパッケージ配布すると symlink は同梱されず壊れるため、
# このスクリプトで symlink を実体コピーに展開してからパッケージ化する。
#
# Usage:
#   bash scripts/sync-styles.sh          # symlink → 実体コピーへ展開
#   bash scripts/sync-styles.sh --relink # 実体コピー → symlink へ戻す（開発用）
#
# 冪等。実行後に references/styles/ は通常ディレクトリ（配布可能）になる。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STYLES="$SKILL_DIR/references/styles"

mode="${1:---embed}"

case "$mode" in
  --embed)
    if [[ -L "$STYLES" ]]; then
      # symlink の指す先を、リンクを除去する前に絶対パスで解決しておく
      link_target="$(readlink "$STYLES")"
      target="$(cd "$(dirname "$STYLES")" && cd "$link_target" && pwd)"
      tmp="$(mktemp -d)"
      cp -R "$target"/. "$tmp"/
      rm "$STYLES"
      mkdir -p "$STYLES"
      cp -R "$tmp"/. "$STYLES"/
      rm -rf "$tmp"
      echo "embedded: styles/ は実体コピーになりました（配布可能）。元の正本: $target"
    elif [[ -d "$STYLES" ]]; then
      echo "already embedded: styles/ は既に実体ディレクトリです。スキップ。"
    else
      echo "error: $STYLES が見つかりません。" >&2
      exit 1
    fi
    ;;
  --relink)
    if [[ -d "$STYLES" && ! -L "$STYLES" ]]; then
      rm -rf "$STYLES"
    fi
    ln -snf ../../_image-styles "$STYLES"
    echo "relinked: styles/ -> ../../_image-styles（開発モードに戻しました）"
    ;;
  *)
    echo "usage: sync-styles.sh [--embed|--relink]" >&2
    exit 2
    ;;
esac
