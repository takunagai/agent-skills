// {{ARTWORK_NAME}} ─ SuperCollider 音響エンジンの骨格
//
// 置換ガイド（新規作品を作るとき）:
//   - このファイルは sc/main.scd として配置する
//   - {{ARTWORK_NAME}} はすべて postln の起動メッセージ文字列の中にしかない
//     （文字列置換だけで安全に差し替えられる。構文には影響しない）
//   - SynthDef は \pluck の 1 個だけ例示している。OSCdef 内の
//     「ここに作品の音を実装する」を実際の SynthDef 呼び出しに差し替える
//
// 「溜めて解放する」ジェスチャーを OSC 経由で受け、音を鳴らす骨格。
// web 版（templates/web/audio-engine-skeleton.ts）と同じ 4 イベントを
// 固定契約として共有する（OscBridge.pde の送信メソッドと対応）:
//   /charge/start x y   : 溜め始め（継続音があればここで起動）
//   /charge/level level : 溜めレベル 0..1 の追従（毎フレーム呼ばれてよい）
//   /release level x y  : 解放（継続音を止め、単発の音を鳴らす）
//   /pop x y            : 短いタップ（軽い単発）
//
// 起動: sclang sc/main.scd（IDE 不要・headless 動作）
// 受信 OSC :57120（sclang 既定 langPort） / 送信 OSC :12000（ビジュアル側へ振幅を送る）
//
// web 版と両方作る場合、チューニング定数は両ファイルで質感が揃うように更新する。

// ─────────────────────────────────────────────
// チューニング定数（上部集約 ─ ここだけ触れば全体の質感を調整できる）
// ─────────────────────────────────────────────
~masterVolume   = 0.9;    // マスター音量（Limiter 前段）
~reverbMix      = 0.33;   // リバーブのドライ/ウェット（0=ドライ 1=ウェット）
~reverbRoom     = 0.86;   // 残響の広さ
~reverbDamp     = 0.25;   // 残響の高域減衰
~ampSendRate    = 30;     // /sc/amp 送出レート（Hz）
~processingPort = 12000;  // ビジュアル側（Processing 等）の受信ポート。衝突する場合はここを変更
~superDirtPort  = 57120;  // SuperDirt が Tidal からの dirt メッセージを受けるポート（sclang langPort と同一）

s = Server.default;
s.options.numBuffers = 1024 * 16;  // Pluck/SuperDirt 用に多めに確保
s.options.memSize    = 1024 * 64;  // リアルタイムメモリ（KB）
s.options.numInputBusChannels = 0; // 出力専用アプリ。入力を開かず、入出力デバイスのサンプルレート不一致を回避

s.waitForBoot {
	var superDirtClass;

	// ── バス確保 ──
	~fxBus    = Bus.audio(s, 2);    // 全音源を集約する共有 FX（リバーブ）バス
	~levelBus = Bus.control(s, 1);  // /charge/level を書き込む溜めレベル（0..1）
	~levelBus.set(0);

	// ── ビジュアル側への送信先 ──
	~processingAddr = NetAddr("127.0.0.1", ~processingPort);

	// ── OSC の正規化 x（0..1、欠損時 0.5）を pan（-1..1）へ写す共通ヘルパ ──
	~xToPan = { |x| ((x ? 0.5) * 2) - 1 };

	// ═══════════ SynthDef 群 ═══════════
	// ここに作品の音を実装する。以下はプラック単発の例のみ。
	// \master は汎用インフラ（マスターチェーン + 振幅送出）なので変更不要。

	SynthDef(\pluck, { |out, freq = 440, amp = 0.4, pan = 0, decayTime = 0.4|
		var env = EnvGen.kr(Env.perc(0.001, decayTime, curve: -4), doneAction: 2);
		var sig = Pluck.ar(WhiteNoise.ar, Impulse.kr(0), freq.reciprocal, freq.reciprocal, decayTime, 0.5);
		sig = sig * env * amp;
		Out.ar(out, Pan2.ar(sig, pan));
	}).add;

	// マスター: FX バス集約 → FreeVerb2 → Limiter → Out(0)。振幅を SendReply で送出（汎用）
	SynthDef(\master, { |in, out = 0, mix = 0.33, room = 0.86, damp = 0.25, amp = 0.9, sendRate = 30|
		var sig = In.ar(in, 2);
		sig = FreeVerb2.ar(sig[0], sig[1], mix: mix, room: room, damp: damp);
		sig = Limiter.ar(sig * amp, 0.95);
		SendReply.kr(Impulse.kr(sendRate), '/sc/ampReply', Amplitude.kr(sig.sum * 0.5, 0.01, 0.2));
		Out.ar(out, sig);
	}).add;

	s.sync;  // 全 SynthDef の登録完了を待つ

	// ── ノードツリー: 音源グループの後段にマスターを置き実行順を保証 ──
	~srcGroup = Group.new(s);
	~fxGroup  = Group.after(~srcGroup);
	~master   = Synth(\master, [\in, ~fxBus, \out, 0,
		\mix, ~reverbMix, \room, ~reverbRoom, \damp, ~reverbDamp,
		\amp, ~masterVolume, \sendRate, ~ampSendRate], ~fxGroup);

	// ═══════════ OSCdef 群（受信 :57120）═══════════
	// アドレスは web 版 AudioEngine と共有する固定契約。各ハンドラの中身だけを
	// 作品の音に差し替える（継続音を使わない設計なら chargeStart/chargeLevel は
	// levelBus の更新だけで空でもよい）。

	// /charge/start x y : 溜め始め
	OSCdef(\chargeStart, { |msg|
		~levelBus.set(0);
		// ここに作品の音を実装する（例: 継続的に鳴る Synth を ~chargeSynth として起動）
		// if(~chargeSynth.notNil) { ~chargeSynth.release };
		// ~chargeSynth = Synth(\yourChargeSound, [\out, ~fxBus, \levelBus, ~levelBus], ~srcGroup);
	}, '/charge/start');

	// /charge/level level : 溜めレベルを制御バスへ書き込む（継続音があれば追従させる）
	OSCdef(\chargeLevel, { |msg|
		~levelBus.set(msg[1].clip(0, 1));
	}, '/charge/level');

	// /release level x y : 継続音を止め、単発の音を発火する
	OSCdef(\release, { |msg|
		var level = msg[1].clip(0, 1);
		var pan = ~xToPan.(msg[2]);
		// if(~chargeSynth.notNil) { ~chargeSynth.release; ~chargeSynth = nil };
		Synth(\pluck, [\out, ~fxBus, \freq, 220, \amp, level.linlin(0, 1, 0.2, 0.6), \pan, pan], ~srcGroup);
	}, '/release');

	// /pop x y : 短いタップ用の軽い単発
	OSCdef(\pop, { |msg|
		Synth(\pluck, [\out, ~fxBus, \freq, 440, \amp, 0.3, \pan, ~xToPan.(msg[1]) * 0.6, \decayTime, 0.2], ~srcGroup);
	}, '/pop');

	// /sc/ampReply : SendReply を受けビジュアル側へ /sc/amp を転送（音→視覚の唯一の線）
	OSCdef(\ampForward, { |msg|
		~processingAddr.sendMsg('/sc/amp', msg[3].clip(0, 1));
	}, '/sc/ampReply');

	s.sync;

	// ═══════════ Tier 2: SuperDirt（クラス存在ガード付き）═══════════
	// 未導入環境でコンパイルエラーにしないため、クラス名を直接書かず asClass 経由で参照する
	superDirtClass = \SuperDirt.asClass;
	if(superDirtClass.notNil) {
		"[{{ARTWORK_NAME}}] SuperDirt を検出 ─ Tier 2 を起動します".postln;
		~dirt = superDirtClass.new(2, s);
		~dirt.loadSoundFiles;
		s.sync;
		~dirt.start(~superDirtPort, 0 ! 12);
		"[{{ARTWORK_NAME}}] SuperDirt 起動完了（port 57120）".postln;
	} {
		"[{{ARTWORK_NAME}}] SuperDirt 未導入 ─ Tier 1（カスタム SynthDef のみ）で動作".postln;
	};

	s.sync;
	"════════════════════════════════════════".postln;
	"{{ARTWORK_NAME}} audio ready".postln;
	("  受信 OSC :" ++ NetAddr.langPort.asString ++ "  /charge/start /charge/level /release /pop").postln;
	("  送信 OSC :" ++ ~processingPort.asString ++ " /sc/amp（マスター振幅 " ++ ~ampSendRate.asString ++ "Hz）").postln;
	"════════════════════════════════════════".postln;
};
