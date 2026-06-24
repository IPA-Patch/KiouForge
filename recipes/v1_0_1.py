"""KiouForge patch constants for app version 1.0.1 (CFBundleVersion 11).

RVAs verified against assets/1.0.1/dump.cs.index.json on 2026-06-15.
"""

from recipes.common import CAVE_ENTRY, CAVE_OBSERVER

BUILD = 11

# ---------------------------------------------------------------------------
# Cave region — shared front half of UnityFramework __TEXT,__oslogstring
# zero-fill (0x8268024 .. 0x826C000).
# KiouForge occupies this region; KiouEngineBridge takes the back half
# (0x826A000 .. 0x826C000) so both recipes are region-disjoint.
# ---------------------------------------------------------------------------
CAVE_REGION = (0x8268024, 0x826C000)

# ---------------------------------------------------------------------------
# Hook slot table base.
# 11 slots * 8 B = 88 B below 0x8F90CD8 (KiouKifExporter's tail).
#   0x8F90CD8 - 11*8 = 0x8F90C80
# Must match KIOU_HOOK_SLOT_BASE_RVA in Sources/KiouForge/ChinlanSites.h.
# ---------------------------------------------------------------------------
HOOK_SLOT_BASE_RVA = 0x8F90C80

# fmt: off
SITES: list = [
    # --- Entry caves (CAVE_ENTRY) ---
    # slot, site_rva, prologue_hex, kind, aux, label
    (0,  0x6B6B758, "f44fbea9", CAVE_ENTRY, None, "Application.set_targetFrameRate"),
    (1,  0x59455D4, "f44fbea9", CAVE_ENTRY, None, "GameOrchestrator.IsAfkEnabled"),
    (2,  0x5D320E0, "ff0301d1", CAVE_ENTRY, None, "NativeSyncSession.SetHashSize"),
    (3,  0x5D3206C, "ff0301d1", CAVE_ENTRY, None, "NativeSyncSession.SetSkillLevel"),
    (4,  0x5D32178, "ffc305d1", CAVE_ENTRY, None, "NativeSyncSession.SearchFull"),

    # --- Observer caves (CAVE_OBSERVER): IMatchMode.OnMatchEndAsync × 5 ---
    # All share slot 5 (KIFU_OBSERVE); aux = KiouMatchMode enum index.
    (5,  0x59E5958, "f657bda9", CAVE_OBSERVER, 0, "AIMatchMode.OnMatchEndAsync"),
    (5,  0x59EC818, "ff8301d1", CAVE_OBSERVER, 1, "CPUStreamMode.OnMatchEndAsync"),
    (5,  0x59FF8F8, "f44fbea9", CAVE_OBSERVER, 2, "LocalPvPMode.OnMatchEndAsync"),
    (5,  0x5A0139C, "ff8301d1", CAVE_OBSERVER, 3, "OnlinePvPMode.OnMatchEndAsync"),
    (5,  0x5A2B564, "f85fbca9", CAVE_OBSERVER, 4, "RecordReplayMode.OnMatchEndAsync"),

    # --- Account switching entry caves (CAVE_ENTRY) ---
    (6,  0x591E860, "fd7bbfa9", CAVE_ENTRY, None, "UserSaveDataExtensions.AccountExists"),
    (7,  0x5B9899C, "f657bda9", CAVE_ENTRY, None, "ILoginArgs.Create"),
    (8,  0x5B98A2C, "f657bda9", CAVE_ENTRY, None, "IRegisterUserArgs.Create"),
    (9,  0x5812534, "ff8302d1", CAVE_ENTRY, None, "AuthServiceExtensions+<RunLoginSequenceAsync>d__1.MoveNext"),
    (10, 0x5BB4774, "ff4302d1", CAVE_ENTRY, None, "GameService+<GetSelfUserProfileAsync>d__36.MoveNext"),
]
# fmt: on
