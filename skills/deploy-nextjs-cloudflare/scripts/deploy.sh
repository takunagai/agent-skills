#!/bin/bash
# デプロイ自動化スクリプト（Next.js + OpenNext + Cloudflare Workers）
# Usage: ./deploy.sh [production|preview] [--skip-build] [--allow-branch]
#
# 本番環境:             ./deploy.sh production
# プレビュー:           ./deploy.sh preview
# ビルド省略:           ./deploy.sh production --skip-build
# main/master 以外から: ./deploy.sh production --allow-branch

set -euo pipefail

# --- 設定 ---
# DEPLOY_PROJECT_DIR でデプロイ対象プロジェクトのルートを指定可。未指定ならカレントディレクトリ。
PROJECT_DIR="${DEPLOY_PROJECT_DIR:-$(pwd)}"
# 本番 URL は wrangler.jsonc の routes を参照するか、PRODUCTION_URL で指定する（未指定でもデプロイは動作する）。
PRODUCTION_URL="${PRODUCTION_URL:-}"

# --- 引数解析 ---
ENV="production"
SKIP_BUILD=false
ALLOW_BRANCH=false

for arg in "$@"; do
  case "$arg" in
    production|preview)
      ENV="$arg"
      ;;
    --skip-build)
      SKIP_BUILD=true
      ;;
    --allow-branch)
      ALLOW_BRANCH=true
      ;;
    *)
      echo "エラー: 不明な引数です: $arg"
      echo "Usage: deploy.sh [production|preview] [--skip-build] [--allow-branch]"
      exit 1
      ;;
  esac
done

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

# --- Step 0: プリフライト ---
step 0 "プリフライト"

# 0-1: Git リポジトリ確認
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  error "Git リポジトリではありません（PROJECT_DIR: $PROJECT_DIR）"
  exit 1
fi
success "Git リポジトリを確認しました"

# 0-2: package.json 存在確認
if [ ! -f "package.json" ]; then
  error "package.json が見つかりません（PROJECT_DIR: $PROJECT_DIR）"
  exit 1
fi
success "package.json を確認しました"

# 0-3: フレームワーク検出（@opennextjs/cloudflare の有無 / astro との誤発動防止）
FRAMEWORK=$(node -e "
try {
  const pkg = require('./package.json');
  const deps = Object.assign({}, pkg.dependencies, pkg.devDependencies);
  if (deps['@opennextjs/cloudflare']) {
    console.log('opennext');
  } else if (deps['astro']) {
    console.log('astro');
  } else {
    console.log('none');
  }
} catch (e) {
  console.log('error');
}
" 2>/dev/null)

if [ "$FRAMEWORK" = "astro" ]; then
  error "Astro 構成を検出しました。deploy-astro-cloudflare スキルを使用してください"
  exit 1
elif [ "$FRAMEWORK" != "opennext" ]; then
  error "package.json に @opennextjs/cloudflare が見つかりません（dependencies/devDependencies を確認してください）"
  exit 1
fi
success "Next.js + OpenNext 構成を確認しました"

# 0-4: パッケージマネージャ自動検出
if [ -f "pnpm-lock.yaml" ]; then
  PM="pnpm"
elif [ -f "bun.lock" ] || [ -f "bun.lockb" ]; then
  PM="bun"
elif [ -f "yarn.lock" ]; then
  PM="yarn"
else
  PM="npm"
fi
case "$PM" in
  pnpm) RUN=(pnpm run) ;;
  bun) RUN=(bun run) ;;
  yarn) RUN=(yarn run) ;;
  *) RUN=(npm run) ;;
esac
success "パッケージマネージャ: $PM"

# 0-5: デプロイスクリプト検出（公式推奨形 deploy/upload、無ければ旧形式にフォールバック）
has_script() {
  node -e "
    const pkg = require('./package.json');
    process.exit(pkg.scripts && pkg.scripts['$1'] ? 0 : 1);
  " 2>/dev/null
}

if [ "$ENV" = "production" ]; then
  PRIMARY_SCRIPT="deploy"
  FALLBACK_SCRIPT="deploy:production"
else
  PRIMARY_SCRIPT="upload"
  FALLBACK_SCRIPT="deploy:preview"
fi

if has_script "$PRIMARY_SCRIPT"; then
  DEPLOY_SCRIPT="$PRIMARY_SCRIPT"
  success "デプロイスクリプト: $DEPLOY_SCRIPT"
elif has_script "$FALLBACK_SCRIPT"; then
  DEPLOY_SCRIPT="$FALLBACK_SCRIPT"
  info "旧形式のスクリプト ($FALLBACK_SCRIPT) を検出しました。公式推奨の $PRIMARY_SCRIPT スクリプトへの移行を推奨します（references/setup-checklist.md 参照）"
else
  error "package.json に $PRIMARY_SCRIPT / $FALLBACK_SCRIPT のいずれのスクリプトも見つかりません"
  exit 1
fi

# 0-6: wrangler 認証確認
if ! WHOAMI_OUTPUT=$(npx wrangler whoami 2>&1); then
  error "wrangler の実行に失敗しました。\`wrangler login\` を実行してください"
  exit 1
fi
if echo "$WHOAMI_OUTPUT" | grep -qi "not authenticated"; then
  error "wrangler が未認証です。\`wrangler login\` を実行してください"
  exit 1
fi
success "wrangler 認証を確認しました"

# 0-7: ブランチ検出・安全弁（production は main/master 限定。--allow-branch で解除可）
CURRENT_BRANCH=$(git branch --show-current)
if [ "$ENV" = "production" ] && [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
  if [ "$ALLOW_BRANCH" = true ]; then
    info "現在のブランチ ($CURRENT_BRANCH) は main/master ではありませんが、--allow-branch が指定されたため続行します"
  else
    error "現在のブランチ ($CURRENT_BRANCH) は main/master ではありません。--allow-branch を指定するか main/master に切り替えてください"
    exit 1
  fi
fi
success "ブランチ: $CURRENT_BRANCH"

# --- Step 1: 状態確認 ---
step 1 "状態確認"

UNCOMMITTED=$(git status --porcelain)
UNPUSHED_COUNT=$(git log --oneline "origin/$CURRENT_BRANCH..$CURRENT_BRANCH" 2>/dev/null | wc -l | tr -d ' ')

if [ -n "$UNCOMMITTED" ]; then
  info "未コミットの変更があります:"
  git status --short
  echo ""
  error "先にコミットしてください（/commit でコミットしてから再実行）"
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
  info "${RUN[*]} build を実行中..."
  if "${RUN[@]}" build; then
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
  if git push origin "$CURRENT_BRANCH"; then
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

info "${RUN[*]} $DEPLOY_SCRIPT を実行中..."

if "${RUN[@]}" "$DEPLOY_SCRIPT"; then
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
    info "本番サイト: wrangler.jsonc の routes / workers.dev 設定を確認してください（PRODUCTION_URL 未設定）"
  fi
  info "ロールバックは \`npx wrangler rollback\`（references/troubleshooting.md 参照）"
else
  info "wrangler の出力に表示された Preview URL を確認してください（固定エイリアスは --preview-alias）"
fi
echo ""
