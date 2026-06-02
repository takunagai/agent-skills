#!/bin/bash
# validate_commit_msg.sh - Conventional Commits 形式の検証
# Usage: ./validate_commit_msg.sh <commit-message-file>
#        ./validate_commit_msg.sh -m "commit message"

# set -e は使用しない（ERRORS カウントと競合するため）

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 有効な type 一覧
VALID_TYPES="feat|fix|docs|style|refactor|perf|test|build|ci|chore"

# コミットメッセージを取得
if [ "$1" = "-m" ]; then
    COMMIT_MSG="$2"
elif [ -f "$1" ]; then
    COMMIT_MSG=$(cat "$1")
else
    echo -e "${RED}Usage: $0 <commit-message-file> or $0 -m \"message\"${NC}"
    exit 1
fi

# 1行目を取得
FIRST_LINE=$(echo "$COMMIT_MSG" | head -n 1)

echo "========================================"
echo "  コミットメッセージ検証"
echo "========================================"
echo -e "対象: ${YELLOW}$FIRST_LINE${NC}\n"

ERRORS=0

# ----------------------------------------
# 1. 形式チェック: type(scope): subject
# ----------------------------------------
echo -e "${YELLOW}[1/5] 形式チェック${NC}"

# type(scope): subject または type: subject
PATTERN="^($VALID_TYPES)(\([a-zA-Z0-9_-]+\))?!?: .+"

if echo "$FIRST_LINE" | grep -qE "$PATTERN"; then
    echo -e "${GREEN}[OK] Conventional Commits 形式に準拠${NC}"
else
    echo -e "${RED}[FAIL] 形式が正しくありません${NC}"
    echo "  期待: <type>(<scope>): <subject>"
    echo "  有効な type: feat, fix, docs, style, refactor, perf, test, build, ci, chore"
    ((ERRORS++))
fi

# ----------------------------------------
# 2. 絵文字チェック
# ----------------------------------------
echo -e "\n${YELLOW}[2/5] 絵文字チェック${NC}"

# 絵文字の正規表現パターン
if echo "$COMMIT_MSG" | grep -qP '[\x{1F300}-\x{1F9FF}]|[\x{2600}-\x{26FF}]' 2>/dev/null; then
    echo -e "${RED}[FAIL] 絵文字が含まれています（禁止）${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}[OK] 絵文字なし${NC}"
fi

# ----------------------------------------
# 3. Subject の長さチェック
# ----------------------------------------
echo -e "\n${YELLOW}[3/5] Subject 長さチェック${NC}"

SUBJECT_LENGTH=${#FIRST_LINE}
if [ "$SUBJECT_LENGTH" -gt 72 ]; then
    echo -e "${YELLOW}[WARN] Subject が長すぎます（${SUBJECT_LENGTH}文字 > 72文字推奨）${NC}"
else
    echo -e "${GREEN}[OK] Subject 長さ適切（${SUBJECT_LENGTH}文字）${NC}"
fi

# ----------------------------------------
# 4. Subject 末尾のピリオドチェック
# ----------------------------------------
echo -e "\n${YELLOW}[4/5] 末尾ピリオドチェック${NC}"

if echo "$FIRST_LINE" | grep -qE '\.$'; then
    echo -e "${YELLOW}[WARN] Subject 末尾にピリオドは不要です${NC}"
else
    echo -e "${GREEN}[OK] 末尾ピリオドなし${NC}"
fi

# ----------------------------------------
# 5. Breaking Change チェック
# ----------------------------------------
echo -e "\n${YELLOW}[5/5] Breaking Change チェック${NC}"

if echo "$COMMIT_MSG" | grep -qiE "BREAKING CHANGE:|^[a-z]+(\([a-z0-9_-]+\))?!:"; then
    echo -e "${GREEN}[INFO] Breaking Change が含まれています${NC}"
    echo "  メジャーバージョンアップが必要です"
else
    echo -e "${GREEN}[OK] Breaking Change なし${NC}"
fi

# ----------------------------------------
# 結果サマリ
# ----------------------------------------
echo -e "\n========================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}  検証完了 - コミットメッセージは有効です${NC}"
    echo "========================================"
    exit 0
else
    echo -e "${RED}  $ERRORS 件のエラーがあります${NC}"
    echo "========================================"
    exit 1
fi
