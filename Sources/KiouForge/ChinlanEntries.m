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
void  *g_kfBypassEntry[KIOU_CAVE_ALLOC_COUNT];

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

    // Pre-compute bypass (orig-trampoline) addresses for every cave slot.
    // Mirrors KEB's g_inject_entry pattern.
    for (int i = 0; i < KIOU_CAVE_ALLOC_COUNT; i++) {
        g_kfBypassEntry[i] = (void *)(unityBase + KIOU_CAVE_REGION_RVA
                                      + (uintptr_t)i * KIOU_CHINLAN_CAVE_PAYLOAD_SIZE
                                      + KIOU_CHINLAN_CAVE_BYPASS_OFFSET);
    }
    IPALog([NSString stringWithFormat:
              @"[Chinlan] bypass table: [0]=%p .. [%d]=%p",
              g_kfBypassEntry[0], KIOU_CAVE_ALLOC_COUNT - 1,
              g_kfBypassEntry[KIOU_CAVE_ALLOC_COUNT - 1]]);

    KFPublishFrameRateSlots(unityBase);
    KFPublishAfkDisableSlots(unityBase);
    KFPublishAnalysisTuneSlots(unityBase);
    KFPublishKifuObserveSlots(unityBase);
    KFPublishAccountObserveSlots(unityBase);  // account switching entry slots
}

void KFPublishAccountObserveSlots(uintptr_t unityBase) {
    // Each account-switching hook is a CAVE_ENTRY: the cave BLRs the slot
    // pointer (our hook), which then calls orig via the bypass trampoline at
    // cave_va + KIOU_CHINLAN_CAVE_BYPASS_OFFSET.  We publish the hook
    // function pointer here; bypass addresses are computed on demand via
    // KIOU_BYPASS_FOR_ALLOC() using the allocation indices from ChinlanSites.h.
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_EXISTS]                    = (void *)KFHookAccountExistsEntry;
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_LOGIN_ARGS_CREATE]         = (void *)KFHookLoginArgsCreateEntry;
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_REGISTER_USER_ARGS_CREATE] = (void *)KFHookRegisterUserArgsCreateEntry;
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_RUN_LOGIN_SEQ_MOVENEXT]    = (void *)KFHookRunLoginSeqMoveNextEntry;
    g_kfHookSlot[KIOU_SLOT_ACCOUNT_GET_SELF_PROFILE_MOVENEXT] = (void *)KFHookGetSelfProfileMoveNextEntry;
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
