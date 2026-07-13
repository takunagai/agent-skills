// ============================================================
// pattern-skeleton.ts ─ Strudel パターン層の骨格（オプショナル）
//
// 置換ガイド（新規作品を作るとき）:
//   - このファイルは src/audio/pattern.ts として配置する
//   - import 元 "./audio-engine-skeleton" は音響エンジン本体のファイル名
//     （リネーム後の src/audio/{{artwork-slug}}-engine.ts）に合わせて書き換える
//   - グローバル名 __artworkControl は {{ARTWORK_NAME}} 由来の一意な名前に変更してよい
//     （複数作品を同一ページで動かすことは想定しないので衝突リスクは低いが、
//     グローバル汚染を避けるため他ライブラリと被らない名前を選ぶ）
//   - PATTERN_CODE は 1 レイヤーの最小例。作品のレイヤー構成に合わせて増やす
//
// 設計意図:
//   - 外部値注入: signal(() => __artworkControl.charge / .energy)
//     （クエリごとにコールバックが再実行されるため再評価は不要）
//   - 音源は内蔵シンセのみを既定にする（外部 CDN サンプルは通信依存になるため
//     使うならオフライン時のフォールバックを用意する）
//   - パターン層は失敗しても本体（音響エンジン + ビジュアル）が動き続けるよう
//     必ず try-catch で守る ─ オプショナル層として扱う
// ============================================================

// @strudel/web は型定義を同梱していないため、companion の
// strudel-web.d.ts（同ディレクトリ）で any モジュールとして宣言している。
// 実装時は src/types/strudel-web.d.ts 等、プロジェクトの型置き場に移すとよい。
// （declare module は import 文を持つファイル内に直接書くと「既存モジュールの
// 拡張」とみなされ解決に失敗するため、必ず独立した .d.ts に分離すること）

import { controlSignals } from "./audio-engine-skeleton";

// Strudel（AGPLv3）は動的 import ─ クリックゲート後に初めてロードする
export async function startPatternLayer(ctx: AudioContext): Promise<boolean> {
  try {
    const strudel: any = await import("@strudel/web");
    strudel.setAudioContext?.(ctx); // 音響エンジンと同一 AudioContext を共有
    await strudel.initStrudel();
    // initAudioOnFirstClick は「次のクリック」を待ってしまう（ゲートのクリックは消費済み）。
    // ここは既にユーザー操作後なので worklet ロードを明示的に済ませる
    await strudel.initAudio?.();
    (globalThis as any).__artworkControl = controlSignals;
    await strudel.evaluate(PATTERN_CODE);
    return true;
  } catch (error) {
    console.warn("[pattern] Strudel 層の起動に失敗（本体は継続）:", error);
    return false;
  }
}

export async function stopPatternLayer(): Promise<void> {
  try {
    const strudel: any = await import("@strudel/web");
    strudel.hush();
  } catch {
    // 未ロードなら何もしない
  }
}

// 最小例: charge/energy に応じて 1 レイヤーだけ鳴らす。実装時はレイヤーを増やす
// （元実装は heartbeat / groove / afterglow / ambient の 4 レイヤー構成だった）
const PATTERN_CODE = `
setcps(100/60/4)

const charge = signal(() => __artworkControl.charge)
const energy = signal(() => __artworkControl.energy)

s("bd*4")
  .decay(0.1).sustain(0)
  .gain(energy.mul(0.5).add(0.1))
  .lpf(charge.mul(3000).add(400))
`;
