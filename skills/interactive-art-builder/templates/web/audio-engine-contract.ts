// ============================================================
// audio-engine-contract.ts ─ AudioEngine インターフェースと Noop 実装（骨格）
//
// 置換ガイド（新規作品を作るとき）:
//   - このファイルは src/audio/engine.ts として配置する（ファイル名は固定でよい）
//   - import 元の "./audio-engine-skeleton" は、audio-engine-skeleton.ts を
//     src/audio/{{artwork-slug}}-engine.ts にリネームした後のファイル名に合わせて書き換える
//   - クラス名 ArtworkAudioEngine は {{ARTWORK_NAME}}AudioEngine 等、作品名に合わせて改名してよい
//     （engine.ts 側は import 元とクラス名を書き換えるだけで、このインターフェース自体は変更しない）
//
// 設計意図:
//   main.ts（呼び出し側）は createAudioEngine() 経由でのみ audio に触ること。
//   音響エンジンの実装を差し替える・音を出さないモードにする、といった変更が
//   main.ts に波及しないようにするための契約。audio/ 配下にはこの契約以外の
//   公開 API を増やさない（実装詳細は AudioEngine の背後に隠す）。
//
// メソッドは「溜めて解放する」ジェスチャーを前提にした最小契約。
// 別のジェスチャー（連続描画・多点タッチ等）を扱う作品では、このインター
// フェース自体を作品に合わせて設計し直してよい（骨格であって固定仕様ではない）。
// ============================================================

export interface AudioEngine {
  start(): Promise<void>;
  chargeStart(x: number, y: number): void; // x,y は 0..1 正規化
  chargeLevel(level: number): void; // 毎フレーム呼ばれてよい
  release(level: number, x: number, y: number): void;
  pop(x: number, y: number): void;
  setEnergy(energy: number): void; // decay 中 1→0 等、演出用の連続値
  getAmp(): number; // マスター振幅 0..1（ビジュアル側のフィードバックに使う）
}

export class NoopAudioEngine implements AudioEngine {
  async start(): Promise<void> {}
  chargeStart(): void {}
  chargeLevel(): void {}
  release(): void {}
  pop(): void {}
  setEnergy(): void {}
  getAmp(): number {
    return 0;
  }
}

import { ArtworkAudioEngine } from "./audio-engine-skeleton";

// URL に ?mute を付けると無音（視覚のみ）で起動できる
export function createAudioEngine(): AudioEngine {
  if (new URLSearchParams(location.search).has("mute")) {
    return new NoopAudioEngine();
  }
  return new ArtworkAudioEngine();
}
