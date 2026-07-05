#!/bin/bash
# デプロイ自動化スクリプト
# Usage: ./deploy.sh [production|preview] [--skip-build]
#
# 本番環境:     ./deploy.sh production
# プレビュー:   ./deploy.sh preview
# ビルド省略:   ./deploy.sh production --skip-build

set -euo pipefail

# --- 設定 ---
# DEPLOY_PROJECT_DIR でデプロイ対象プロジェクトのルートを指定可。未指定ならカレントディレクトリ。
PROJECT_DIR="${DEPLOY_PROJECT_DIR:-$(pwd)}"
BRANCH="main"
# 本番 URL は wrangler.toml の routes を参照するか、PRODUCTION_URL で指定する（未指定でもデプロイは動作する）。
PRODUCTION_URL="${PRODUCTION_URL:-}"

# --- 引数解析 ---
ENV="${1:-production}"
SKIP_BUILD=false

for arg in "$@"; do
  if [ "$arg" = "--skip-build" ]; then
    SKIP_BUILD=true
  fi
done

if [ "$ENV" != "production" ] && [ "$ENV" != "preview" ]; then
  echo "エラー: 環境は 'production' または 'preview' を指定してください"
  exit 1
fi

# --- ヘルパー関数 ---
info() { echo -e "\033[34m[INFO]\033[0m $1"; }
success() { echo -e "\033[32m[OK]\033[0m $1"; }
error() { echo -e "\033[31m[ERROR]\033[0m $1"; }
step() { echo -e "\n\033[1m=== Step $1: $2 ===\033[0m"; }

cd "$PROJECT_DIR"

echo ""
echo "=============================="
echo "  デプロイ: $ENV 環境"
echo "=============================="

# --- Step 1: 状態確認 ---
step 1 "状態確認"

UNCOMMITTED=$(git status --porcelain)
UNPUSHED_COUNT=$(git log --oneline "origin/$BRANCH..$BRANCH" 2>/dev/null | wc -l | tr -d ' ')

if [ -n "$UNCOMMITTED" ]; then
  info "未コミットの変更があります:"
  git status --short
  echo ""
  error "先にコミットしてください（/commit を実行）"
  exit 1
else
  success "ワーキングツリーはクリーンです"
fi

info "未プッシュのコミット: ${UNPUSHED_COUNT}件"

# --- Step 2: ビルド確認 ---
if [ "$SKIP_BUILD" = true ]; then
  step 2 "ビルド確認 (スキップ)"
  info "--skip-build が指定されたためスキップします"
else
  step 2 "ビルド確認"
  info "npm run build を実行中..."
  if npm run build; then
    success "ビルド成功"
  else
    error "ビルド失敗。デプロイを中止します"
    exit 1
  fi
fi

# --- Step 3: プッシュ ---
step 3 "リモートにプッシュ"

if [ "$UNPUSHED_COUNT" -gt 0 ]; then
  info "${UNPUSHED_COUNT}件のコミットをプッシュ中..."
  if git push origin "$BRANCH"; then
    success "プッシュ完了"
  else
    error "プッシュ失敗"
    exit 1
  fi
else
  info "未プッシュのコミットはありません。スキップします"
fi

# --- Step 4: デプロイ ---
step 4 "デプロイ実行 ($ENV)"

DEPLOY_CMD="npm run deploy:$ENV"
info "$DEPLOY_CMD を実行中..."

if $DEPLOY_CMD; then
  success "デプロイ完了"
else
  error "デプロイ失敗"
  exit 1
fi

# --- 完了 ---
echo ""
echo "=============================="
echo "  デプロイ完了"
echo "=============================="
if [ "$ENV" = "production" ]; then
  if [ -n "$PRODUCTION_URL" ]; then
    info "本番サイト: $PRODUCTION_URL"
  else
    info "本番サイト: wrangler.toml の routes で設定したドメインを確認してください（PRODUCTION_URL 未設定）"
  fi
fi
echo ""
