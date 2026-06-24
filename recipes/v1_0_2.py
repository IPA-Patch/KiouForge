"""KiouForge patch constants for app version 1.0.2 (CFBundleVersion 12).

RVAs verified against assets/1.0.2/dump.cs.index.json on 2026-06-24.
Slot table base (HOOK_SLOT_BASE_RVA) is identical to 1.0.1 — __bss is a
zero-fill section whose layout is stable across these builds.
"""

from recipes.common import CAVE_ENTRY, CAVE_OBSERVER

BUILD = 12

CAVE_REGION        = (0x826F5E8, 0x8274000)
HOOK_SLOT_BASE_RVA = 0x8F90C80

# fmt: off
SITES: list = [
    # --- Entry caves (CAVE_ENTRY) ---
    (0,  0x6B718A4, "f44fbea9", CAVE_ENTRY, None, "Application.set_targetFrameRate"),
    (1,  0x594A034, "f44fbea9", CAVE_ENTRY, None, "GameOrchestrator.IsAfkEnabled"),
    (2,  0x5D379DC, "ff0301d1", CAVE_ENTRY, None, "NativeSyncSession.SetHashSize"),
    (3,  0x5D37968, "ff0301d1", CAVE_ENTRY, None, "NativeSyncSession.SetSkillLevel"),
    (4,  0x5D37A74, "ffc305d1", CAVE_ENTRY, None, "NativeSyncSession.SearchFull"),

    # --- Observer caves (CAVE_OBSERVER): IMatchMode.OnMatchEndAsync × 5 ---
    (5,  0x59EA720, "f657bda9", CAVE_OBSERVER, 0, "AIMatchMode.OnMatchEndAsync"),
    (5,  0x59F15D4, "ff8301d1", CAVE_OBSERVER, 1, "CPUStreamMode.OnMatchEndAsync"),
    (5,  0x5A046B4, "f44fbea9", CAVE_OBSERVER, 2, "LocalPvPMode.OnMatchEndAsync"),
    (5,  0x5A06158, "ff8301d1", CAVE_OBSERVER, 3, "OnlinePvPMode.OnMatchEndAsync"),
    (5,  0x5A30320, "f85fbca9", CAVE_OBSERVER, 4, "RecordReplayMode.OnMatchEndAsync"),

    # --- Account switching entry caves (CAVE_ENTRY) ---
    (6,  0x591E860, "fd7bbfa9", CAVE_ENTRY, None, "UserSaveDataExtensions.AccountExists"),
    (7,  0x5B9899C, "f657bda9", CAVE_ENTRY, None, "ILoginArgs.Create"),
    (8,  0x5B98A2C, "f657bda9", CAVE_ENTRY, None, "IRegisterUserArgs.Create"),
    (9,  0x5812534, "ff8302d1", CAVE_ENTRY, None, "AuthServiceExtensions+<RunLoginSequenceAsync>d__1.MoveNext"),
    (10, 0x5BB4774, "ff4302d1", CAVE_ENTRY, None, "GameService+<GetSelfUserProfileAsync>d__36.MoveNext"),
]
# fmt: on
