#import "Internal.h"

#if IPA_CHINLAN

#import "chinlan.h"
#import "Account_Persistence.h"
#include <stdint.h>

// ---------------------------------------------------------------------------
// Account switching entry-cave hooks (IPA_CHINLAN only).
// Declared here so we can publish their addresses without dragging
// Hook_AccountObserve.m's static state into this TU.
// ---------------------------------------------------------------------------
extern bool   KFHookAccountExistsEntry(void *data);
extern void  *KFHookLoginArgsCreateEntry(void *deviceId, void *distinctId);
extern void  *KFHookRegisterUserArgsCreateEntry(void *userName, void *distinctId);
extern void   KFHookRunLoginSeqMoveNextEntry(void *self);
extern void   KFHookGetSelfProfileMoveNextEntry(void *self);

// ===========================================================================
// ChinlanEntries.m — KiouForge-local glue for the IPA_CHINLAN build.
//
// Mirrors the pattern from KiouEditor/ChinlanEntries.m. See that file and
// Sources/Chinlan/chinlan.h for the full wiring explanation.
//
// Adding a new hook: add its slot to ChinlanSites.h, add a
// KFPublish*Slots() extern to Internal.h, and add a call here in
// kfPublishAll(). The recipe's _SITES table and KIOU_SLOT_COUNT must match.
// ===========================================================================

void **g_kfHookSlot = NULL;

uintptr_t KFResolveOrigTrampoline(uintptr_t unityBase, uintptr_t siteRVA) {
    return IPAChinlanResolveOrig(unityBase, siteRVA,
                                     KIOU_CHINLAN_CAVE_PAYLOAD_SIZE);
}

static BOOL g_kiou_chinlan_published = NO;

static void kfPublishAll(uintptr_t unityBase) {
    g_kfHookSlot = (void **)(unityBase + KIOU_HOOK_SLOT_BASE_RVA);
    IPALog([NSString stringWithFormat:
              @"[Chinlan] slot base=%p (unityBase+0x%X)",
              (void *)g_kfHookSlot, KIOU_HOOK_SLOT_BASE_RVA]);

    KFPublishFrameRateSlots(unityBase);
    KFPublishAfkDisableSlots(unityBase);
    KFPublishAnalysisTuneSlots(unityBase);
    KFPublishKifuObserveSlots(unityBase);
    KFPublishAccountObserveSlots(unityBase);  // account switching entry slots
}

void KFPublishAccountObserveSlots(uintptr_t unityBase) {
    // Each account-switching hook is a CAVE_ENTRY: the cave RETs into our
    // hook, which then calls orig via the bypass entry (cave_va + 0x4C).
    // We publish the hook function pointer into its dedicated slot so the
    // cave's BLR lands in the right place.
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_EXISTS]                   = (void *)KFHookAccountExistsEntry;
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_LOGIN_ARGS_CREATE]        = (void *)KFHookLoginArgsCreateEntry;
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_REGISTER_USER_ARGS_CREATE]= (void *)KFHookRegisterUserArgsCreateEntry;
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_RUN_LOGIN_SEQ_MOVENEXT]   = (void *)KFHookRunLoginSeqMoveNextEntry;
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_GET_SELF_PROFILE_MOVENEXT]= (void *)KFHookGetSelfProfileMoveNextEntry;

    // Publish bypass entries (cave_va + 0x4C) back into g_kfHookSlot so that
    // entry hooks can invoke orig without a separate lookup.
    // The cave region starts at CAVE_REGION[0] and each cave is CAVE_PAYLOAD_SIZE bytes.
    // Allocation order in _SITES:
    //   slot 0..4  = framerate/afk/nss/kifu (existing, 10 observer caves)
    //   slot 6..10 = account (5 entry caves, allocated after the observer block)
    // The first account cave is at cave_region_start + 10 * 84.
    // The bypass entry is at cave_va + 76 (= 0x4C).
    uintptr_t caveBase = unityBase + 0x8268024UL;
    uintptr_t caveSize = 84;
    // Observer caves: 10 (5 OnMatchEnd + 5 re-used for existing entry hooks).
    // We replicate the slot indexing from the recipe here.
    // Account caves start at index 10 in allocation order (after 5 entry + 5 observer).
    // See recipes/kiouforge.py _SITES for the exact allocation index.
    // Entry cave bypass = cave_va + 0x4C.
    uintptr_t acctCaveStart = caveBase + 10 * caveSize;  // cave index 10 = first account cave
    static const int kAccountSlots[] = {
        KIOU_SLOT_ACCOUNT_EXISTS,
        KIOU_SLOT_ACCOUNT_LOGIN_ARGS_CREATE,
        KIOU_SLOT_ACCOUNT_REGISTER_USER_ARGS_CREATE,
        KIOU_SLOT_ACCOUNT_RUN_LOGIN_SEQ_MOVENEXT,
        KIOU_SLOT_ACCOUNT_GET_SELF_PROFILE_MOVENEXT,
    };
    for (int i = 0; i < 5; i++) {
        uintptr_t caveVa = acctCaveStart + (uintptr_t)i * caveSize;
        uintptr_t bypass = caveVa + 0x4C;
        g_kfHookSlot[kAccountSlots[i]] = (void *)bypass;
    }
    IPALog(@"[Chinlan] account observe slots published");
}

void KFChinlanBootstrap(void) {
    if (g_kiou_chinlan_published) return;

    uintptr_t unityBase = IPAChinlanFindImage("UnityFramework");
    if (unityBase == 0) return;

    IPALog([NSString stringWithFormat:
              @"[Chinlan] UnityFramework base=0x%lx",
              (unsigned long)unityBase]);

    kfPublishAll(unityBase);
    g_kiou_chinlan_published = YES;
    IPALog(@"[Chinlan] === all slots published ===");
}

BOOL KFChinlanPublished(void) {
    return g_kiou_chinlan_published;
}

#endif  // IPA_CHINLAN
