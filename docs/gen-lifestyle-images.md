# gen-lifestyle-images

商品のライフスタイル写真を AI で一括生成するスキルです。ブランドの世界観・商品カタログ・撮影シーンを**プリセット**として管理し、**セミオート**（プラン提示 → 承認 → 生成）で高品質な画像を量産します。画像生成エンジンには `gen-nanobanana-images`（Google Gemini）を使います。

```
あなた: 「商品イメージ写真を10枚生成して」
Claude: プリセットを読み込み → シーン・商品を選定 → プラン提示 → 承認後に一括生成
```

---

## インストール

このリポジトリを clone し、スキル本体（`skills/gen-lifestyle-images`）を各エージェントのスキルディレクトリへ **symlink** します。実体は 1 つ、参照を複数張る方式です。当環境では「実体 → `~/.agents` → `~/.claude`」の 2 段 symlink で統一しています。

```bash
# 1) リポジトリを取得
git clone git@github.com:takunagai/agent-skills.git ~/Projects/agent-skills

# 2) ハブ（~/.agents）から実体へ絶対 symlink
ln -s /Users/$USER/Projects/agent-skills/skills/gen-lifestyle-images ~/.agents/skills/gen-lifestyle-images

# 3) Claude Code 用に ~/.agents への相対 symlink
ln -s ../../.agents/skills/gen-lifestyle-images ~/.claude/skills/gen-lifestyle-images
```

### 前提条件

| 必要なもの | 入手方法 |
|-----------|---------|
| `gen-nanobanana-images` スキル | 画像生成エンジン。本リポに同梱（同様に symlink） |
| Gemini API キー | [Google AI Studio](https://aistudio.google.com/apikey) で取得 |
| Python + Pillow | `pip install Pillow`（PNG→JPEG 変換用） |

```bash
export GEMINI_API_KEY="your-api-key-here"   # .zshrc / .bashrc に追加して永続化推奨
```

---

## アーキテクチャ（2 層）

```
skills/gen-lifestyle-images/
├── SKILL.md              ← Layer 1: 汎用ワークフロー（分析 → プラン → 生成 → レポート）
├── config.json           ← デフォルト生成パラメータ
├── .gitignore            ← presets/*.local.md を追跡除外
└── presets/
    └── example.md        ← Layer 2: プリセットのサンプル（ここをコピーして使う）
```

- **Layer 1**（SKILL.md）はどのプロジェクトでも共通のワークフロー。
- **Layer 2**（presets/）はブランドごとの商品・シーン・スタイリング情報。プリセットを追加するだけで別プロジェクトに対応します。

> **個人・案件固有のプリセット**は `presets/<name>.local.md` という名前にすると `.gitignore` で Git 追跡から除外されます。クライアントのカタログ・ブランドガイドなどを安全にローカル管理できます。公開サンプルは `presets/example.md` のみです。

---

## 使い方

```
1. /gen-lifestyle-images + 自然言語で指示
2. スキルがプリセットを読み込み、プランを提示
3. プランを確認・承認
4. 自動生成開始（進捗報告あり）
5. 結果レポート表示
```

最もシンプルな使い方:

```
/gen-lifestyle-images 商品イメージ写真を5枚生成して
```

これだけで、プリセットから最適なシーンと商品を自動選定し、プランを提示します。

---

## プロンプト例

```
/gen-lifestyle-images ライフスタイル画像を10枚生成して
/gen-lifestyle-images 全商品のイメージ写真を各2枚ずつ
/gen-lifestyle-images 着用シーンの画像を20枚、2Kで
```

商品・シーンタイプを指定:

```
/gen-lifestyle-images サンプル商品A のネイビーをキッチンシーンで3枚
/gen-lifestyle-images ディテールクローズアップを5枚。素材質感と甲デザインで
/gen-lifestyle-images カラーコレクション画像を3枚
```

混合・補完・おまかせ:

```
/gen-lifestyle-images 着用6枚 + ディテール2枚 + コレクション2枚 = 計10枚
/gen-lifestyle-images まだ生成が少ない商品×カラーを優先して10枚
/gen-lifestyle-images ランダムに商品を選んで15枚、いい感じに
```

---

## ワークフロー詳細

### Phase 1: ANALYZE（分析）
プリセット読み込み → 商品カタログ取得 → 既存画像スキャン（商品×カラーごとの生成済み枚数を集計）→ リファレンス確認。

### Phase 2: PLAN（プラン作成）
シーン選定 → 商品×カラー選定 → 割り当てマトリクスをテーブルで提示。**ここでユーザー承認を求めます**（修正リクエストも可能）。

### Phase 3: GENERATE（生成）
シーン定義 + 商品データ → 英語プロンプト構築 → 商品写真を入力画像（`-i`）に、トーン/ラベルリファレンスを参照画像（`-r`）に設定 → `gen-nanobanana-images` で生成 → PNG→JPEG（quality=92）変換 → 目視確認 → 進捗報告。

### Phase 4: REPORT（レポート）
生成したシーン・商品・ファイル名の一覧をテーブルで提示。

---

## プリセットの作り方

`presets/` に Markdown ファイルを作成します（サンプル `presets/example.md` をコピーするのが早道）。

```bash
cp ~/.claude/skills/gen-lifestyle-images/presets/example.md \
   ~/.claude/skills/gen-lifestyle-images/presets/your-project.md
# 案件固有で公開したくない場合は your-project.local.md にする（gitignore 済み）
```

プリセットの構成セクション:

| セクション | 内容 |
|-----------|------|
| frontmatter | `name` / `project_path` / `output_dir` / `naming` / `multi_naming` |
| Brand Guidelines | ターゲット、ブランドトーン、アンチパターン |
| Photography Style | 光源、色温度、カメラアングル、被写界深度、構図ルール |
| Reference Images | Tone References（基準画像）/ Label References（ラベル・タグ） |
| Product Catalog | 商品ごとの分類・特徴・質感ポイント + カラーバリエーションテーブル |
| Styling Guide | 商品タイプ別のスタイリング指示 |
| Scene Library | シーン定義（ID・構図・小物・光源・カメラ設定・相性） |
| Avoid | 避けるべき要素 |

### プリセット作成のコツ

| ポイント | 説明 |
|---------|------|
| トーンリファレンスは 3 枚 | 異なる光条件（サイド光・拡散光・逆光）を 1 枚ずつ |
| 商品写真は最低 5 枚 | 正面・側面・背面・上面・ディテールが揃うと再現度 UP |
| シーンは 10+ 用意 | 多いほど生成時のバリエーションが豊富に |
| 相性を明記 | 「暖色系に合う」等の指定がシーン選定の精度を上げる |
| ラベル写真は高解像度 | ラベル再現の精度に直結。マクロ撮影推奨 |

---

## 設定リファレンス（config.json）

| キー | デフォルト | 説明 |
|------|-----------|------|
| `model` | `"flash2"` | 画像生成モデル（`flash` / `flash2` / `pro`） |
| `aspect_ratio` | `"3:2"` | アスペクト比 |
| `image_size` | `"2K"` | 解像度（`512px` / `1K` / `2K` / `4K`） |
| `timeout` | `180` | 生成タイムアウト秒数 |
| `jpeg_quality` | `92` | JPEG 変換時の品質（1-100） |
| `scene_type_ratio` | `{0.6, 0.2, 0.2}` | 自動選定時のシーンタイプ比率 |
| `max_input_images` | `3` | 商品写真の最大入力枚数 |
| `max_reference_images` | `4` | リファレンス画像の最大枚数 |

優先順位: **ユーザーの指示 > プリセット定義 > config.json**

---

## FAQ・トラブルシューティング

- **プリセットがないプロジェクトで使える？** → 呼び出すと新規作成をガイドします。
- **生成が途中で止まった** → 「続きから生成して」で未完了タスクから再開（進捗は TaskList で管理）。
- **1 枚だけリテイク** → `crazy-image-5.jpg をリテイクして。朝の光を強めに` のようにファイル名指定。
- **別の画像生成サービスを使える？** → 現在は `gen-nanobanana-images`（Google Gemini）のみ。

| エラー | 原因 | 対処 |
|--------|------|------|
| `No API key` | GEMINI_API_KEY 未設定 | 環境変数を設定 |
| `No images in response` | プロンプトがフィルタされた | 表現を変えてリトライ |
| `Rate limit (429)` | API レート制限 | 自動リトライ（最大 3 回）で対応 |
| `Timeout` | 4K 生成で時間超過 | `--timeout` 延長 or 解像度を下げる |
| `FileNotFoundError` | 商品写真パスが誤り | プリセットの写真パスを確認 |

---

## 詳細

ワークフローの詳細・プロンプト構築ルールは、スキル本体の `SKILL.md` と `presets/example.md`（プリセットの書き方）を参照してください。

## ライセンス

MIT
