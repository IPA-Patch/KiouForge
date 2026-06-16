# デバッグ用シンボル調査メモ

対象: KIOU 1.0.1 build 11 / dump.cs (全 22,542 型)

キーワード: Debug / Overlay / Test / Cheat / Dev / God

---

## Debug 系

### `Project.Foundation.DebugAgentLogger`（dump.cs:1592833）

`[Conditional("PROJECT_DEBUG")]` ガードが付いたログ出力クラス。

```csharp
public static class DebugAgentLogger {
    const string SessionId = "1a52e8bb-c79b-443a-b916-5fbb8f7a9007";  // ハードコード UUID
    static string RunId;
    const int MaxFileSize = 1048576;  // 1MB ローテーション付き

    [Conditional("PROJECT_DEBUG")]
    public static void Log(string hypothesisId, string location, string message, string data);
    public static string ReadAll();
    public static long FileSize();
    public static void Clear();
}
```

リリースビルドでは `Log()` がコンパイルアウトされる。
ハードコードされた `SessionId` はサーバーログ側で特定セッションを追跡する開発者向け仕掛けと思われる。

### `Project.ShogiCore.SearchDebugCallbacks`（dump.cs:1483984）

将棋 AI 探索のデバッグコールバック。メソッド 1 つのみ。実用上の利用価値は低い。

---

## Overlay 系（53件）

全て `Project.Composition` 以下の UI コンポーネント群。ゲームプレイへの介入手段はない。
代表的なもの:

- `ScreenOverlayController` — 画面オーバーレイの色・エフェクト制御
- `GachaRewardConfirmationOverlayPresenter` — ガチャ報酬確認 UI
- `UIBoardArrowOverlay` — 盤面の矢印表示
- `Orbital.Overlay.*` — Overlay フレームワーク基盤 (`IOverlay`, `OverlayLauncher` など)

---

## Test 系（7件）

### `Project.Game.Bootstrapper.GameTestStarter`（dump.cs:1207624）★

Unity Inspector から全パラメータを操作できる開発用シーンスターター。`MonoBehaviour` 継承。

フィールド一覧:

```csharp
MatchMode _matchMode
int       _aiDifficulty
bool      _useRshogi
int       _rshogiDepth        // エンジン探索深度を直接指定
int       _rshogiSkillLevel   // スキルレベルを直接指定
bool      _beginnerSupportEnabled
PlayerSide _localPlayerSide
bool      _overrideStartingTurn    // 開始手番の上書き
InitialPositionType _startPositionType
string    _customSFEN         // 任意の局面から開始
string    _kifu               // USI/KIF 形式の棋譜再生モード
string    _testCueSheetKey    // サウンドテスト用キー
```

Context Menu:
- `[ContextMenu("ゲーム開始")]`
- `[ContextMenu("ゲーム停止")]`
- `[ContextMenu("サウンドテスト: ロード＆再生")]`

`_rshogiDepth` / `_rshogiSkillLevel` は `KifuDetailPopupAnalysisPresenter` が使う
`SearchFull(depth)` と同じエンジンパラメータと思われる。
リリースビルドに残っている理由は不明（エディタ専用コードが剥がされていない可能性あり）。

### `Project.Composition.UIShogiBoardTestBootstrap`（dump.cs:833199）

将棋盤の各モードをシーン起動時に切り替えるテスト用ブートストラップ。

```
SetupReadOnly()        RVA 0x590839C
SetupInteractive()     RVA 0x59083F4
SetupRecordReplay()    RVA 0x590862C
SetupTsumePuzzle()     RVA 0x5908DC4
```

### `Project.Sound.Test.SoundLoadTester`（dump.cs:1628026）

`Load() / Play() / Stop() / Unload()` のみ。サウンドテスト用。

---

## Cheat 系

**0件。** 存在しない。

---

## Dev 系（56件）★

### `Constant.DeveloperRole` enum（dump.cs:510477）

```csharp
Invalid = 0, Unspecified = 1,
Administrator = 2, Server = 3, Client = 4,
Designer = 5, Planner = 6, Tester = 7,
Analyst = 8, Viewer = 9
```

### `Project.Network.DeveloperDeviceService`（dump.cs:581400）

`internal sealed` クラス。全メソッドに RVA あり、バイナリフック可能。
**ただしサーバー側の Developer 認証が必要な設計のため、クライアントのみでは機能しない。**

| メソッド | RVA | 概要 |
|---|---|---|
| `GetDeveloperListAsync` | `0x5B98D8C` | 開発者一覧取得 |
| `GetDeveloperPremiumPassAsync` | `0x5B98EA4` | プレミアムパス状態取得 |
| `GrantDeveloperAllCurrenciesAsync` | `0x5B98FBC` | 全通貨一括付与 |
| `ResetDeveloperMasterVersionAsync` | `0x5B990D4` | マスターバージョンリセット |
| `ResetDeveloperUserCurrencyAsync` | `0x5B991EC` | 通貨リセット |
| `SetDeveloperDummyTimeAsync` | `0x5B99304` | サーバー時刻偽装 |
| `SetDeveloperMasterVersionAsync` | `0x5B9941C` | マスターバージョン指定 |
| `SetDeveloperPremiumPassAsync` | `0x5B99534` | プレミアムパス強制有効化 |
| `SetDeveloperUserCurrencyAsync` | `0x5B9964C` | 通貨量指定 |

### `Service.SetDeveloperDummyTimeArgs`（dump.cs:516705）

```csharp
string UserId
bool   IsEnabledDummy   // ダミー時刻の有効/無効
bool   IsFixedDate      // 固定日時 or オフセット
Timestamp FixedDate     // 固定する日時
```

### `Service.SetDeveloperUserCurrencyArgs`（dump.cs:517546）

```csharp
CurrencyType CurrencyType
int MstCurrencyId
int Amount
```

### `Dto.DevelopmentEnvironmentStatus`（dump.cs:556291）

```csharp
string EnvironmentName   // 環境名 (dev/stg/prod 等)
string DefaultUrl        // 接続先 URL のデフォルト
```

---

## God 系

**0件。** 存在しない。

---

## まとめ

| カテゴリ | 件数 | 評価 |
|---|---|---|
| Debug | 2 | リリースでほぼ無効化済み |
| Overlay | 53 | 全て UI コンポーネント、利用価値なし |
| Test | 7 | `GameTestStarter` が唯一面白い |
| Cheat | 0 | 存在しない |
| Dev | 56 | サーバー認証必須で単体では動作しない |
| God | 0 | 存在しない |

「チートモード」相当の機能は `DeveloperDeviceService` として実装されているが、
サーバー側の `DeveloperRole` 認証なしでは呼び出せない設計になっている。
`GameTestStarter` は Unity Editor の開発用ツールがリリースバイナリに残った状態。
