// @strudel/web は型定義を同梱していないため any モジュールとして宣言する
// （利用箇所は pattern-skeleton.ts のみ・動的 import 経由）
//
// 注意: この宣言は import 文を持つ .ts ファイルの中には書けない
// （TS がそれを「既存モジュールの拡張」とみなし、解決失敗のエラーになる）。
// 独立した .d.ts ファイルとして置くこと。配置先は src/types/ 等、
// プロジェクトの型置き場に合わせてよい。
declare module "@strudel/web";
