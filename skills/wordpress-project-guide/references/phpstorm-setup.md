# PhpStorm 連携セットアップ（WPCS + PHPStan）

PhpStorm 2026.x 系の UI を前提としたナビ。ユーザーに GUI 操作を案内するときはこの手順と「実地で判明した罠」を必ず踏まえる。

## 大前提 ─ 実地で判明した罠 3 つ

1. **品質ツールのパス設定は既存プロジェクトに共有されない**。「新規プロジェクト用設定」（プロジェクトを閉じた状態の設定ダイアログ）は文字通り新規プロジェクトにのみ適用される。既存プロジェクトは**各案件を開いて手入力**が必要
2. **「コーディング標準」ドロップダウンに更新ボタンは無い**。新しい標準（WordPress 等）を認識させるには**プロジェクトを一旦閉じて再度開く**
3. インスペクション画面（エディター → インスペクション）に Coding standard の選択肢は無い。**選択は品質ツール画面側**にある

## WordPress 統合（IDE 本体・案件ごと）

1. WP プロジェクトを開いた状態で `設定（Cmd+,）→ PHP → フレームワーク` → WordPress ノードを展開
2. 「Enable WordPress integration」にチェック → WordPress installation path に **wp-admin と wp-includes を含むディレクトリ**を指定
3. コア Include Path 追加の提案が出たら承諾（フック・関数補完が効くようになる）
4. ノード自体が見当たらない場合: `設定 → プラグイン` でバンドルの「WordPress」プラグインが有効か確認

## Code Style

- `設定 → エディター → コードスタイル → PHP` → 右上「選択して設定...（Set from...）」→ **WordPress**
- 全社的な既定を切り替える場合は Default IDE スキーム直接変更でもよいが、**Default スキームはそれを使う全プロジェクトに波及**する。非 WP 案件も同じ IDE で扱うなら、スキーム複製 → 「WordPress」命名 → 案件ごとに選択が安全
- モダン PHP 案件の既定スキームは PER-CS 3.0.0（PSR-12 の公式後継）

## PHP_CodeSniffer（WPCS）

1. `設定 → PHP → 品質ツール → PHP_CodeSniffer` を展開
2. 「構成」ドロップダウン → **システム PHP**（Mac 上の phpcs を直接叩く構成。「+」で作るのは Docker / リモート用なので通常不要）
3. パス未設定なら「...」→ phpcs パスに `<composer global bin-dir>/phpcs`（`composer global config bin-dir --absolute` で確認）→ 「検証」でバージョン表示を確認
4. 「コーディング標準」→ **Custom** → 共通ルールセット（例: `~/Projects/php-standards/wordpress-ja.phpcs.xml`）を指定。案件専用の phpcs.xml がある案件はそちらを維持
5. 画面上部トグル「PHP_CodeSniffer インスペクション」→ オン
6. 標準一覧に WordPress 系が出ない → プロジェクト再起動（罠 2）

## PHPStan

1. `設定 → PHP → 品質ツール → PHPStan` を展開
2. 構成「システム PHP」→ 「...」→ PHPStan パスに `<プロジェクト>/vendor/bin/phpstan` → 「検証」
3. 専用フィールドに入力（旧 UI の自由入力オプション欄は無い）:
   - **構成ファイル**: `<プロジェクト>/phpstan.neon` の絶対パス（空だと「構成ファイルが存在しません」エラー）
   - **レベル**: phpstan.neon の level と同値に揃える（CLI 引数が neon を上書きしてズレるのを防ぐ）
   - **メモリ上限**: `2G`
4. 画面上部トグル「PHPStan インスペクション」→ オン
5. エディターモードのチェックは PHPStan 2.1.17+ が必要（`vendor/bin/phpstan --version` で確認）

## 動作確認

- 実行モードが「アイドル時」の場合、**ファイルを開いただけでは解析されない**。1 文字編集して戻す → 数秒待つと発火
- 確実に確認するには: `コード → コードのインスペクション` → スコープ「ファイル」+ プロファイル「**Project Default**」（品質ツール画面のトグルはプロジェクト側プロファイルに書き込まれるため。Default IDE プロファイルでは無効のままのことがある）→ 解析
- 結果ウィンドウに `PHP_CodeSniffer 検証` / `PHPStan 検証` のグループが出れば稼働
- 見分け方: エディター内の警告は `phpcs:` / `phpstan:` の接頭辞付き。WP_Post 等のドキュメントポップアップは WordPress 統合の成果であり品質ツールとは別物
