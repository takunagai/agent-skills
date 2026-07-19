# wordpress-project-guide

WordPress 案件の「規約ガイダンス」と「品質ツール導入」を 1 つにまとめた基盤スキルです。AI エージェントが WP 案件に触れるとき、汎用 PHP（PSR/PER）前提の助言をやめて WordPress Coding Standards（WPCS）準拠で振る舞い、頼めば静的解析一式（WPCS + PHPStan）を案件へ自動導入します。

---

## 背景 ─ なぜ必要か

JetBrains 公式の Claude Code 用 PhpStorm プラグイン（php-project-guide スキル）は、フレームワーク判定が Laravel / Symfony の 2 種のみで、それ以外はすべて「汎用 PHP」として PSR/PER 標準（4 スペースインデント・`strict_types` 必須・`global` 禁止）を案内します。これは WordPress の規約（タブ・snake_case・Yoda 条件・`global $wpdb`）と真っ向から衝突し、WP 案件では有害です。本スキルはその WordPress 向けの穴を埋めます。

## できること

| 機能 | 内容 |
|------|------|
| 規約ガイダンス | WPCS 準拠のコード生成・レビュー指針（エスケープ / サニタイズ / nonce / `$wpdb->prepare` / i18n / タブ / snake_case / Yoda） |
| 品質ツール導入 | WPCS 3.x + PHP_CodeSniffer（グローバル 1 回）と PHPStan + phpstan-wordpress（案件ごと）のセットアップを自動実行 |
| レイアウト検出 | 標準型（`wp-content/` 直下）とコア分離型（`wp/` `wpd/` などのサブディレクトリ）の両対応 |
| 自作コード特定 | git 追跡状況と style.css の Author / Template 行から解析対象を絞り込み |
| PhpStorm 連携 | GUI 設定ナビ（設定が既存プロジェクトに共有されない等、実地で判明した罠を織り込み済み） |
| 日本語対応 | 日本語コメントで警告が出ない共通ルールセット `wordpress-ja.phpcs.xml` の雛形同梱 |

## 使い方

WP 案件のディレクトリで Claude Code に話しかけます。

```
WP セットアップして
WordPress 案件に品質ツールを入れて
PHPStan を WordPress に導入して
```

コーディング規約のガイダンスは、WP 案件での PHP 作業時に自動で効きます（明示呼び出し不要）。

## セットアップの中身（スキルが実行すること）

1. WPCS をグローバル導入（初回のみ・全案件共通）
2. 案件のレイアウト検出 → 自作テーマ / プラグインの特定
3. `composer require --dev szepeviktor/phpstan-wordpress`（classic WP でも require-dev 専用 composer.json を作成。本番コードは composer 非依存のまま）
4. `phpstan.neon` 生成 ─ level 1・親テーマ / カスタムフィールド系プラグインの scanDirectories・テーマ内 `dev/`（node_modules）の除外
5. `--memory-limit=2G` で解析実行 → `function.notFound` の残りは「死んだ参照」として報告（削除済みプラグイン参照などの検出成果）
6. `.gitignore` に `/vendor/` 追記

## 構成ファイル

```
skills/wordpress-project-guide/
├── SKILL.md                          # 本体（規約ダイジェスト + セットアップランブック）
└── references/
    ├── wordpress-ja.phpcs.xml        # 日本語コメント対応の共通ルールセット雛形
    └── phpstorm-setup.md             # PhpStorm GUI 設定ナビ（実地の罠 3 つを明記）
```

共通ルールセットの実働コピーは `~/Projects/php-standards/wordpress-ja.phpcs.xml` に置く運用を既定とし、無ければ雛形からコピーします。案件固有の除外（特定 sniff の無効化など）が必要になったら、共通版をコピーして案件専用 phpcs.xml に fork します。

## インストール

```bash
ln -s ~/Projects/agent-assets/skills/wordpress-project-guide ~/.claude/skills/wordpress-project-guide
ln -s ~/Projects/agent-assets/skills/wordpress-project-guide ~/.agents/skills/wordpress-project-guide
```

## 関連

- JetBrains php-project-guide（Laravel / Symfony はそちら。WP は本スキルが優先）
- `git-workflow`（導入後のコミットは通常フローで）
