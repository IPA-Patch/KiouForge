#if IPA_CHINLAN

#import "Internal.h"

// ===========================================================================
// ChinlanDispatcher — chinlan flavour only.
//
// Ported from KiouEngineBridge/ChinlanDispatcher.m.
//
// On the chinlan build every hook site is redirected by a static code cave
// to a slot in UnityFramework __DATA,__bss. Each slot holds a function
// pointer published here by KFChinlanPublish().
//
// CAVE_ENTRY sites: cave BLRs the slot directly and RETs to the caller.
//   The hook calls orig via the bypass trampoline in g_kfBypassEntry[].
//
// CAVE_OBSERVER sites (KifuObserve × 5): cave saves all arg registers,
//   loads KIOU_SLOT_KIFU_OBSERVE, BLRs it with mode_index in W2, restores,
//   runs displaced prologue, branches to orig+4.
//
// KFChinlanPublish() stores all hook function pointers into the slot table
//   and pre-computes g_kfBypassEntry[] from the cave layout.
// ===========================================================================

void **g_kfHookSlot        = NULL;
void  *g_kfBypassEntry[KIOU_CAVE_ALLOC_COUNT];

uintptr_t KFResolveOrigTrampoline(uintptr_t unityBase, uintptr_t siteRVA) {
    return IPAChinlanResolveOrig(unityBase, siteRVA,
                                 KIOU_CHINLAN_CAVE_PAYLOAD_SIZE);
}

// ---------------------------------------------------------------------------
// Entry-cave hook declarations (defined in their respective Hook_*.m files).
// ---------------------------------------------------------------------------
extern bool   KFHookAccountExistsEntry(void *data);
extern void  *KFHookLoginArgsCreateEntry(void *deviceId, void *distinctId);
extern void  *KFHookRegisterUserArgsCreateEntry(void *userName, void *distinctId);
extern void   KFHookRunLoginSeqMoveNextEntry(void *self);
extern void   KFHookGetSelfProfileMoveNextEntry(void *self);
extern void  *KFHookHttpMsgInvokerSendAsyncEntry(void *self, void *request, void *ct);

static BOOL g_published = NO;

void KFChinlanPublish(uintptr_t unityBase) {
    g_kfHookSlot = (void **)(unityBase + KIOU_HOOK_SLOT_BASE_RVA);
    IPALog([NSString stringWithFormat:
              @"[Chinlan] slot base=%p (unityBase+0x%X)",
              (void *)g_kfHookSlot, KIOU_HOOK_SLOT_BASE_RVA]);

    // Pre-compute bypass (orig-trampoline) addresses for every cave alloc slot.
    for (int i = 0; i < KIOU_CAVE_ALLOC_COUNT; i++) {
        g_kfBypassEntry[i] = (void *)(unityBase + KIOU_CAVE_REGION_RVA
                                      + (uintptr_t)i * KIOU_CHINLAN_CAVE_PAYLOAD_SIZE
                                      + KIOU_CHINLAN_CAVE_BYPASS_OFFSET);
    }
    IPALog([NSString stringWithFormat:
              @"[Chinlan] bypass table: [0]=%p .. [%d]=%p",
              g_kfBypassEntry[0], KIOU_CAVE_ALLOC_COUNT - 1,
              g_kfBypassEntry[KIOU_CAVE_ALLOC_COUNT - 1]]);

    // Publish all hook slots.
    KFInstallFrameRateHook(unityBase);
    KFInstallAfkDisableHook(unityBase);
    KFInstallAnalysisTuneHook(unityBase);
    KFInstallKifuObserveHook(unityBase);
    KFInstallAccountObserveHook(unityBase);
    KFInstallGrpcLoggingHook(unityBase);

    IPALog(@"[Chinlan] === all slots published ===");
}

void KFChinlanBootstrap(void) {
    if (g_published) return;

    uintptr_t unityBase = IPAChinlanFindImage("UnityFramework");
    if (unityBase == 0) return;

    IPALog([NSString stringWithFormat:
              @"[Chinlan] UnityFramework base=0x%lx",
              (unsigned long)unityBase]);

    KFChinlanPublish(unityBase);
    g_published = YES;
}

BOOL KFChinlanPublished(void) {
    return g_published;
}

#endif  // IPA_CHINLAN
