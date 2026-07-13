// OSC 注入テスト骨格: ビジュアル側（Processing 等）の代わりに、溜め→解放の
// 操作イベントを SC(57120) と Tidal(6010) へ直接送るテストハーネス。
//
// 使い方: sclang bin/test-osc.scd
//   （sc/main.scd と、使うなら Tidal を起動した状態で別プロセスとして実行する）
//
// アドレスは main-skeleton.scd の OSCdef 契約（/charge/start, /charge/level,
// /release, /pop）と共有の固定値。作品側で OSC イベントを追加した場合は
// このファイルにも送信ブロックを足して検証する。
(
var sc = NetAddr("127.0.0.1", 57120);
var tidal = NetAddr("127.0.0.1", 6010); // Tidal を使わない作品ならこの行と /ctrl 送信は削ってよい
fork {
	"test: pop x3".postln;
	3.do {
		sc.sendMsg("/pop", 0.5, 0.5);
		0.25.wait;
	};
	1.wait;

	"test: charge 3s".postln;
	sc.sendMsg("/charge/start", 0.5, 0.5);
	90.do { |i|
		var level = ((i + 1) / 90).min(1.0);
		sc.sendMsg("/charge/level", level);
		tidal.sendMsg("/ctrl", "charge", level.asFloat);
		(1/30).wait;
	};

	"test: release (level 1.0)".postln;
	sc.sendMsg("/release", 1.0, 0.5, 0.5);
	tidal.sendMsg("/ctrl", "charge", 0.0);
	90.do { |i|
		var energy = 1.0 - ((i + 1) / 90);
		tidal.sendMsg("/ctrl", "energy", energy.asFloat);
		(1/30).wait;
	};
	tidal.sendMsg("/ctrl", "energy", 0.0);

	"test: done ─ 8 秒後に終了".postln;
	8.wait;
	0.exit;
};
)
