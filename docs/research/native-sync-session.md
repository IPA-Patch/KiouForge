# NativeSyncSession 調査メモ

対象: KIOU 1.0.1 build 11 / UnityFramework

## クラス概要

`Project.RshogiEngine.NativeSyncSession` — 将棋エンジン（Rshogi NNUE）への同期呼び出しラッパー。
post-game kifu 解析 (`KifuDetailPopupAnalysisPresenter`) が使用する。

## フィールド

```
// static
private static int s_createdCount;           // 0x0
private static int s_destroyedCount;         // 0x4
private static int s_finalizedDestroyCount;  // 0x8

// instance
private readonly object _sync;               // 0x10
private IntPtr _handle;                      // 0x18  ← ネイティブセッションハンドル
private byte[] _bestmoveBuffer;              // 0x20
private byte[] _pvBuffer;                    // 0x28
private byte[] _multiMovesPackedBuffer;      // 0x30
private byte[] _multiOutMovesBuffer;         // 0x38
private byte[] _multiOutPvsBuffer;           // 0x40
private int[]  _multiScoresBuffer;           // 0x48
```

プロセス管理フィールド (`_process`, `_stdin`) は存在しない。
エンジンとの通信は `_handle`（IntPtr）を通じてネイティブライブラリに完全に委譲されている。

## 公開メソッド一覧

| シグネチャ | RVA |
|---|---|
| `.ctor(string evalPath)` | — |
| `bool get_IsDisposed()` | — |
| `void SetOption(string name, string value)` | — |
| `void SetSkillLevel(int level)` | `0x5D3206C` |
| `void SetHashSize(int mb)` | `0x5D320E0` |
| `string Search(string sfen, int depth)` | — |
| `SyncSearchResult SearchFull(string sfen, int depth)` | `0x5D32178` |
| `MoveScore[] SearchMulti(string sfen, int depth, string[] usiMoves)` | — |
| `MoveScore[] SearchMultiPV(string sfen, int depth, int capacity, int multiPv)` | — |
| `MoveScorePv[] SearchMultiWithPV(string sfen, int depth, string[] usiMoves, int pvSlotSize)` | — |
| `MoveScorePv[] SearchMultiPVWithPV(string sfen, int depth, int capacity, int multiPv, int pvSlotSize)` | — |
| `void CancelSearchMulti()` | — |
| `void CancelSearch()` | — |
| `void Dispose()` | — |

## SyncSearchResult 構造体

```csharp
public struct SyncSearchResult {
    public string Bestmove;  // +0x00
    public int Score;        // +0x08
    public string PV;        // +0x10
    public int Depth;        // +0x18
}
```

KiouForge の `KFSyncSearchResult` はこれをミラーした C 構造体。

## SearchFull の内部動作

`SearchFull(string sfen, int depth)` → `NativeUsi.SyncSearch`（P/Invoke）を呼ぶ薄いラッパー。

```csharp
// NativeUsi.SyncSearch シグネチャ（dump.cs:1602697）
internal static extern int SyncSearch(
    IntPtr handle,
    byte[] sfenUtf8, UIntPtr sfenLen,
    int depth,
    byte[] outBestmove, UIntPtr bestmoveCapacity, out UIntPtr outBestmoveLen,
    out int outScore,
    byte[] outPv, UIntPtr pvCapacity, out UIntPtr outPvLen,
    out int outDepth
);
```

- `depth` 引数のみ受け取る。`movetime` / `nodes` は C# レイヤーから指定不可
- `go depth N` の組み立てはネイティブライブラリ内部で完結
- depth を上げると解析時間が線形以上に増加することをオンデバイスで確認済み

## KifuDetailPopupAnalysisPresenter からの呼び出し

`dump.cs:819966` 付近。定数は以下のとおり：

```csharp
const int SearchDepth    = 15;   // retail default
const int OwnedHashSizeMb = 16;  // retail default
```

呼び出しフロー:

```
EnsureEngineReadyAsync  →  SetHashSize(16)
                        →  SetSkillLevel(default=20)
RunAnalysisAsync        →  SearchFull(sfen, 15)
```

`SetOption` の呼び出しは一切なし。`movetime` / `nodes` / `time` の文字列定数も dump.cs 内に存在しない。

## KiouForge でのフック対象

| フック | RVA | 変更内容 |
|---|---|---|
| `SetHashSize` | `0x5D320E0` | → `KFAnalysisHashMB()` |
| `SetSkillLevel` | `0x5D3206C` | → `KFAnalysisSkillLevel()` |
| `SearchFull` | `0x5D32178` | depth → `KFAnalysisDepth()` |

## 非同期系との比較

`NativeUsiSession`（非同期系）は `goCommand` 文字列を呼び出し元が外から組み立てて渡す設計:

```csharp
NativeUsiSession.WaitForBestMoveAsync(positionCommand, goCommand, ...)
```

`go movetime 5000` のような時間制限をかけたい場合は `NativeSyncSession` ではなく
`NativeUsiSession` を経由する必要がある。現状 KiouForge は `NativeSyncSession` 経由のみ対応。
