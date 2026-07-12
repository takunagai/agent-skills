#!/bin/bash
# claude-config-audit: ~/.claude グローバル設定の健全性検査スクリプト
#
# レポートのみ。自動削除・自動 unlink・設定ファイルの自動書き換えは一切行わない。
# macOS bash 3.2 互換（配列の連想配列は使わず、jq / find の出力をそのまま処理する）。
set -euo pipefail

CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
AGENTS_DIR="${AGENTS_DIR:-$HOME/.agents}"
SETTINGS_JSON="$CLAUDE_DIR/settings.json"
INSTALLED_PLUGINS_JSON="$CLAUDE_DIR/plugins/installed_plugins.json"
COMMANDS_DIR="$CLAUDE_DIR/commands"
CLAUDE_JSON="$HOME/.claude.json"
KNOWN_MARKETPLACES_JSON="$CLAUDE_DIR/plugins/known_marketplaces.json"

separator() { printf '%s\n' "────────────────────────────────────────"; }

# ---------------------------------------------------------------
# pre-add モード: 新規 MCP / プラグイン追加前の重複・既存導入路チェック
# ---------------------------------------------------------------
run_pre_add() {
  local query="$1"
  if [ -z "$query" ]; then
    echo "使い方: audit.sh pre-add <検索語>" >&2
    exit 1
  fi
  local query_lc
  query_lc=$(printf '%s' "$query" | tr '[:upper:]' '[:lower:]')

  echo "claude-config-audit pre-add — 検索語: $query — $(date '+%Y-%m-%d %H:%M:%S')"
  separator

  local hit_any=0

  # 1. 直接登録の mcpServers（~/.claude.json）
  echo "## 1. 直接登録 MCP（~/.claude.json）"
  if [ -f "$CLAUDE_JSON" ] && command -v jq >/dev/null 2>&1; then
    local direct_hits
    direct_hits=$(jq -r '.mcpServers // {} | keys[]' "$CLAUDE_JSON" 2>/dev/null | while IFS= read -r k; do
      k_lc=$(printf '%s' "$k" | tr '[:upper:]' '[:lower:]')
      if [[ "$k_lc" == *"$query_lc"* ]]; then
        echo "$k"
      fi
    done)
    if [ -z "$direct_hits" ]; then
      echo "  ヒットなし"
    else
      hit_any=1
      echo "$direct_hits" | while IFS= read -r h; do
        [ -z "$h" ] && continue
        echo "  直接登録あり: $h"
      done
    fi
  else
    echo "  スキップ（$CLAUDE_JSON / jq のいずれかが見つからない）"
  fi
  separator

  # 2. インストール済みプラグイン
  echo "## 2. インストール済みプラグイン"
  if [ -f "$INSTALLED_PLUGINS_JSON" ] && command -v jq >/dev/null 2>&1; then
    local plugin_hits
    plugin_hits=$(jq -r '.plugins // {} | keys[]' "$INSTALLED_PLUGINS_JSON" 2>/dev/null | while IFS= read -r k; do
      k_lc=$(printf '%s' "$k" | tr '[:upper:]' '[:lower:]')
      if [[ "$k_lc" == *"$query_lc"* ]]; then
        echo "$k"
      fi
    done)
    if [ -z "$plugin_hits" ]; then
      echo "  ヒットなし"
    else
      hit_any=1
      echo "$plugin_hits" | while IFS= read -r h; do
        [ -z "$h" ] && continue
        echo "  導入済みプラグイン: $h"
      done
    fi
  else
    echo "  スキップ（$INSTALLED_PLUGINS_JSON / jq のいずれかが見つからない）"
  fi
  separator

  # 3. settings.json の enabledPlugins
  echo "## 3. enabledPlugins（settings.json）"
  if [ -f "$SETTINGS_JSON" ] && command -v jq >/dev/null 2>&1; then
    local enabled_hits
    enabled_hits=$(jq -r '.enabledPlugins // {} | to_entries[] | select(.value == true) | .key' "$SETTINGS_JSON" 2>/dev/null | while IFS= read -r k; do
      k_lc=$(printf '%s' "$k" | tr '[:upper:]' '[:lower:]')
      if [[ "$k_lc" == *"$query_lc"* ]]; then
        echo "$k"
      fi
    done)
    if [ -z "$enabled_hits" ]; then
      echo "  ヒットなし"
    else
      hit_any=1
      echo "$enabled_hits" | while IFS= read -r h; do
        [ -z "$h" ] && continue
        echo "  有効化済み: $h"
      done
    fi
  else
    echo "  スキップ（$SETTINGS_JSON / jq のいずれかが見つからない）"
  fi
  separator

  # 4. known_marketplaces（登録済み marketplace は公式プラグイン導入路が既に選ばれている痕跡）
  echo "## 4. known_marketplaces（marketplace 登録）"
  if [ -f "$KNOWN_MARKETPLACES_JSON" ] && command -v jq >/dev/null 2>&1; then
    local mkt_hits
    mkt_hits=$(jq -r 'keys[]' "$KNOWN_MARKETPLACES_JSON" 2>/dev/null | while IFS= read -r k; do
      k_lc=$(printf '%s' "$k" | tr '[:upper:]' '[:lower:]')
      if [[ "$k_lc" == *"$query_lc"* ]]; then
        echo "$k"
      fi
    done)
    if [ -z "$mkt_hits" ]; then
      echo "  ヒットなし"
    else
      hit_any=1
      echo "$mkt_hits" | while IFS= read -r mkt; do
        [ -z "$mkt" ] && continue
        echo "  marketplace 登録あり: $mkt"
        install_location=$(jq -r --arg m "$mkt" '.[$m].installLocation // empty' "$KNOWN_MARKETPLACES_JSON" 2>/dev/null)
        if [ -n "$install_location" ] && [ -f "$install_location/.mcp.json" ]; then
          local mcp_names
          mcp_names=$(jq -r '.mcpServers // {} | keys[]' "$install_location/.mcp.json" 2>/dev/null | paste -sd, -)
          if [ -n "$mcp_names" ]; then
            echo "    -> .mcp.json あり。提供 mcpServers: $mcp_names"
          else
            echo "    -> .mcp.json あり（mcpServers なし）"
          fi
        else
          echo "    -> .mcp.json なし"
        fi
        echo "    推奨: プラグイン導入（marketplace 経由）を優先し、手動 claude mcp add による直接登録は避ける"
      done
    fi
  else
    echo "  スキップ（$KNOWN_MARKETPLACES_JSON / jq のいずれかが見つからない）"
  fi
  separator

  # 5. まとめ
  echo "## まとめ"
  if [ "$hit_any" -eq 0 ]; then
    echo "  重複なし。追加して問題なし"
  else
    echo "  既存の重複・並行路線あり。上記の推奨に従って統合してから追加を検討する"
  fi
  separator
  echo "pre-add チェック完了"
}

if [ "${1:-}" = "pre-add" ]; then
  run_pre_add "${2:-}"
  exit 0
fi

echo "claude-config-audit — $(date '+%Y-%m-%d %H:%M:%S')"
separator

# ---------------------------------------------------------------
# 1. 死 symlink（~/.claude/skills, ~/.claude/agents, ~/.agents/skills）
# ---------------------------------------------------------------
echo "## 1. 死 symlink"
found_broken=0
for dir in "$CLAUDE_DIR/skills" "$CLAUDE_DIR/agents" "$AGENTS_DIR/skills"; do
  if [ ! -d "$dir" ]; then
    echo "  (スキップ: $dir が存在しない)"
    continue
  fi
  while IFS= read -r link; do
    [ -z "$link" ] && continue
    found_broken=1
    target=$(readlink "$link" 2>/dev/null || echo "?")
    echo "  死 symlink: $link -> $target"
  done < <(find -L "$dir" -maxdepth 1 -type l 2>/dev/null)
done
if [ "$found_broken" -eq 0 ]; then
  echo "  問題なし"
else
  echo "  推奨対処: リンク先が移動・削除されていないか確認し、不要なら手動で unlink する"
fi
separator

# ---------------------------------------------------------------
# 2. disabled なのにキャッシュ残存の plugin
# ---------------------------------------------------------------
echo "## 2. disabled なのにキャッシュ残存の plugin"
if [ -f "$SETTINGS_JSON" ] && [ -f "$INSTALLED_PLUGINS_JSON" ] && command -v jq >/dev/null 2>&1; then
  stale_plugins=$(jq -r '.plugins | keys[]' "$INSTALLED_PLUGINS_JSON" 2>/dev/null | while IFS= read -r key; do
    enabled=$(jq -r --arg k "$key" '.enabledPlugins[$k] // false' "$SETTINGS_JSON" 2>/dev/null)
    if [ "$enabled" != "true" ]; then
      echo "$key"
    fi
  done)
  if [ -z "$stale_plugins" ]; then
    echo "  問題なし"
  else
    echo "$stale_plugins" | while IFS= read -r p; do
      [ -z "$p" ] && continue
      echo "  disabled/未登録だがキャッシュ残存: $p"
    done
    echo "  推奨対処: 使わないなら $CLAUDE_DIR/plugins/ 配下のキャッシュを手動整理する"
  fi
else
  echo "  スキップ（settings.json / installed_plugins.json / jq のいずれかが見つからない）"
fi
separator

# ---------------------------------------------------------------
# 3. MCP 重複登録（chrome-devtools）
# ---------------------------------------------------------------
# 重要な制約: --autoConnect 付きの直接登録（.mcp.json 等）が正である。
# 重複が見つかっても直接登録側の削除は絶対に提案しない。
# 解消は常にプラグイン版（chrome-devtools-mcp@claude-plugins-official）の無効化を提案する。
echo "## 3. MCP 重複登録（chrome-devtools）"
direct_registered=0
plugin_registered=0

for mcp_conf in "$HOME/.claude.json" "$CLAUDE_DIR/.mcp.json" "$HOME/.mcp.json" "$CLAUDE_DIR/mcp.json"; do
  if [ -f "$mcp_conf" ] && command -v jq >/dev/null 2>&1; then
    if jq -e '.mcpServers["chrome-devtools"] // empty' "$mcp_conf" >/dev/null 2>&1; then
      direct_registered=1
    fi
  fi
done

if [ -f "$SETTINGS_JSON" ] && command -v jq >/dev/null 2>&1; then
  plugin_enabled=$(jq -r '.enabledPlugins["chrome-devtools-mcp@claude-plugins-official"] // false' "$SETTINGS_JSON" 2>/dev/null)
  if [ "$plugin_enabled" = "true" ]; then
    plugin_registered=1
  fi
fi

if [ "$direct_registered" -eq 1 ] && [ "$plugin_registered" -eq 1 ]; then
  echo "  重複を検出: 直接登録（--autoConnect 付き、正） + プラグイン版 chrome-devtools-mcp@claude-plugins-official（両方有効）"
  echo "  推奨対処: プラグイン版（chrome-devtools-mcp@claude-plugins-official）を無効化する。直接登録は削除しない"
elif [ "$plugin_registered" -eq 1 ] && [ "$direct_registered" -eq 0 ]; then
  echo "  プラグイン版のみ有効。直接登録（--autoConnect）が見つからない場合は意図確認を推奨"
else
  echo "  問題なし（重複なし、または直接登録の設定ファイルが検出範囲外）"
fi
separator

# ---------------------------------------------------------------
# 4. orphan commands（用途不明な commands/*.md）
# ---------------------------------------------------------------
echo "## 4. orphan commands（列挙のみ・判定はユーザーが行う）"
if [ -d "$COMMANDS_DIR" ]; then
  cmd_count=$(find "$COMMANDS_DIR" -maxdepth 1 -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$cmd_count" -eq 0 ]; then
    echo "  問題なし（commands/*.md が存在しない）"
  else
    find "$COMMANDS_DIR" -maxdepth 1 -name '*.md' -type f 2>/dev/null | sort | while IFS= read -r f; do
      echo "  $(basename "$f")"
    done
    echo "  推奨対処: 上記のうち直近で使っていないものは用途を確認し、不要なら archive へ退避する"
  fi
else
  echo "  スキップ（$COMMANDS_DIR が存在しない）"
fi
separator

echo "監査完了"
