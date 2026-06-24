#pragma once

#include <stdint.h>

// ===========================================================================
// ChinlanSites.h — KiouForge Chinlan slot table.
//
// Single source of truth shared between:
//   * Sources/KiouForge/ChinlanEntries.m
//   * recipes/__init__.py (active version selected by TARGET_VERSION)
//
// The @generated block below is machine-written by:
//   make gen-sites   (calls shared/tools/gen_chinlan_sites.py)
// Do NOT edit that block by hand — edit the recipe and re-run gen-sites.
//
// CO-EXISTENCE
// ---------------------------------
// KiouForge reserves 11 slots (88 B) in UnityFramework __DATA,__bss at
// [KIOU_HOOK_SLOT_BASE_RVA, KIOU_HOOK_SLOT_BASE_RVA + KIOU_SLOT_COUNT*8).
// The patcher's assert_slot_in_bss() validates the range at patch time.
// KiouForge is designed to be installed standalone; it does not co-exist
// with KiouEditor in the same IPA.
// ===========================================================================

// ---------------------------------------------------------------------------
// Slot indices.
// ---------------------------------------------------------------------------
enum {
    KIOU_SLOT_SET_TARGET_FRAMERATE      = 0,   // Application.set_targetFrameRate
    KIOU_SLOT_GAME_ORCHESTRATOR_IS_AFK  = 1,   // GameOrchestrator.IsAfkEnabled
    KIOU_SLOT_NSS_SETHASHSIZE           = 2,   // NativeSyncSession.SetHashSize
    KIOU_SLOT_NSS_SETSKILLEVEL          = 3,   // NativeSyncSession.SetSkillLevel
    KIOU_SLOT_NSS_SEARCHFULL            = 4,   // NativeSyncSession.SearchFull (depth)
    KIOU_SLOT_KIFU_OBSERVE              = 5,   // IMatchMode.OnMatchEndAsync x5 (observer)
    // Account switching slots (entry caves — bypass published per-slot)
    KIOU_SLOT_ACCOUNT_EXISTS                    = 6,   // UserSaveDataExtensions.AccountExists
    KIOU_SLOT_ACCOUNT_LOGIN_ARGS_CREATE         = 7,   // ILoginArgs.Create
    KIOU_SLOT_ACCOUNT_REGISTER_USER_ARGS_CREATE = 8,   // IRegisterUserArgs.Create
    KIOU_SLOT_ACCOUNT_RUN_LOGIN_SEQ_MOVENEXT    = 9,   // RunLoginSequenceAsync.MoveNext
    KIOU_SLOT_ACCOUNT_GET_SELF_PROFILE_MOVENEXT = 10,  // GetSelfUserProfileAsync.MoveNext
    KIOU_SLOT_COUNT                             = 11,
};

// ---------------------------------------------------------------------------
// __bss slot table base.
// 6 slots * 8 B = 48 B at the tail of UnityFramework __DATA,__bss.
// KiouForge replaces KiouKifExporter's autosave so the two should not be
// installed together. The base is positioned so the table ends at 0x8F90CD8
// (one slot above where KKE used to live, to leave room for the observer
// slot that subsumes KKE's role).
// ---------------------------------------------------------------------------
#define KIOU_HOOK_SLOT_BASE_RVA  0x8F90C80   // 0x8F90CD8 - 11*8
extern void **g_kfHookSlot;

// ---------------------------------------------------------------------------
// Cave payload size — must match recipes/common.py::CAVE_PAYLOAD_SIZE.
// ---------------------------------------------------------------------------
#define KIOU_CHINLAN_CAVE_PAYLOAD_SIZE  84

// Offset of the orig-trampoline tail within each cave payload.
// cave_bypass_va = unityBase + KIOU_CAVE_REGION_RVA
//                + alloc_idx * KIOU_CHINLAN_CAVE_PAYLOAD_SIZE
//                + KIOU_CHINLAN_CAVE_BYPASS_OFFSET
#define KIOU_CHINLAN_CAVE_BYPASS_OFFSET  (KIOU_CHINLAN_CAVE_PAYLOAD_SIZE - 8)

// Pre-computed bypass table — one entry per cave allocation slot.
// Populated by kfPublishAll(); hook bodies read from here (mirrors KEB's g_inject_entry).
// Index with KIOU_CAVE_ALLOC_* constants.
#define KIOU_CAVE_ALLOC_COUNT  15
extern void *g_kfBypassEntry[KIOU_CAVE_ALLOC_COUNT];

// ---------------------------------------------------------------------------
// Orig-trampoline resolver (thin wrapper over IPAChinlanResolveOrig).
// ---------------------------------------------------------------------------
uintptr_t KFResolveOrigTrampoline(uintptr_t unityBase, uintptr_t siteRVA);

// ---------------------------------------------------------------------------
// @version TARGET_VERSION=1.0.2 BUILD=12
// Edit this block by hand when RVAs change; keep in sync with recipes/v1_0_2.py.

// Cave region start RVA (CAVE_REGION[0] from the active recipe).
#define KIOU_CAVE_REGION_RVA  0x826F5E8

// Cave allocation indices — sequential position in SITES.
// bypass_va = unityBase + KIOU_CAVE_REGION_RVA
//            + alloc_idx * KIOU_CHINLAN_CAVE_PAYLOAD_SIZE
//            + KIOU_CHINLAN_CAVE_BYPASS_OFFSET
#define KIOU_CAVE_ALLOC_SET_TARGET_FRAMERATE          0
#define KIOU_CAVE_ALLOC_GAME_ORCHESTRATOR_IS_AFK      1
#define KIOU_CAVE_ALLOC_NSS_SETHASHSIZE               2
#define KIOU_CAVE_ALLOC_NSS_SETSKILLEVEL              3
#define KIOU_CAVE_ALLOC_NSS_SEARCHFULL                4
#define KIOU_CAVE_ALLOC_AIMATMODE_ONMATCHEND          5
#define KIOU_CAVE_ALLOC_CPUSTREAMMODE_ONMATCHEND      6
#define KIOU_CAVE_ALLOC_LOCALPVPMODE_ONMATCHEND       7
#define KIOU_CAVE_ALLOC_ONLINEPVPMODE_ONMATCHEND      8
#define KIOU_CAVE_ALLOC_RECORDREPLAYMODE_ONMATCHEND   9
#define KIOU_CAVE_ALLOC_ACCOUNT_EXISTS                10
#define KIOU_CAVE_ALLOC_LOGIN_ARGS_CREATE             11
#define KIOU_CAVE_ALLOC_REGISTER_USER_ARGS_CREATE     12
#define KIOU_CAVE_ALLOC_RUN_LOGIN_SEQ_MOVENEXT        13
#define KIOU_CAVE_ALLOC_GET_SELF_PROFILE_MOVENEXT     14

// Site RVAs — first instruction of each hook site.
#define KIOU_SITE_RVA_SET_TARGET_FRAMERATE          0x6B718A4
#define KIOU_SITE_RVA_GAME_ORCHESTRATOR_IS_AFK      0x594A034
#define KIOU_SITE_RVA_NSS_SETHASHSIZE               0x5D379DC
#define KIOU_SITE_RVA_NSS_SETSKILLEVEL              0x5D37968
#define KIOU_SITE_RVA_NSS_SEARCHFULL                0x5D37A74
#define KIOU_SITE_RVA_AIMATMODE_ONMATCHEND          0x59EA720
#define KIOU_SITE_RVA_CPUSTREAMMODE_ONMATCHEND      0x59F15D4
#define KIOU_SITE_RVA_LOCALPVPMODE_ONMATCHEND       0x5A046B4
#define KIOU_SITE_RVA_ONLINEPVPMODE_ONMATCHEND      0x5A06158
#define KIOU_SITE_RVA_RECORDREPLAYMODE_ONMATCHEND   0x5A30320
#define KIOU_SITE_RVA_ACCOUNT_EXISTS                0x5922CD0
#define KIOU_SITE_RVA_LOGIN_ARGS_CREATE             0x5B9DC04
#define KIOU_SITE_RVA_REGISTER_USER_ARGS_CREATE     0x5B9DC94
#define KIOU_SITE_RVA_RUN_LOGIN_SEQ_MOVENEXT        0x58152BC
#define KIOU_SITE_RVA_GET_SELF_PROFILE_MOVENEXT     0x5BB99DC

// @version-end
