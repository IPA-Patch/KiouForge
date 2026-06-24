#import "Internal.h"
#import "Settings.h"
#import <mach-o/dyld.h>
#import <dlfcn.h>
#import <string.h>

// ===========================================================================
// KiouForge — entry point.
//
// Distribution shapes:
//   JB rootless / jailed (Dobby static): KFInstall*Hook() patches the
//     UnityFramework at runtime via MSHookFunction / DobbyHook.
//   Chinlan (make ipa): UnityFramework is statically rewritten so each
//     site BLs into a __TEXT cave; the dylib publishes hook pointers into
//     the __DATA slot table via KFChinlanPublish().
// ===========================================================================

static BOOL g_unityHooked = NO;

static void installUnityHooks(uintptr_t unityBase, const char *unityName);

// dyld add-image callback. Fires synchronously for every image already
// loaded at registration time, then for every subsequent dlopen. We watch
// for UnityFramework and install our hooks the first time it appears.
static void kfOnImageAdded(const struct mach_header *mh, intptr_t slide) {
    (void)slide;
    if (g_unityHooked) return;
    Dl_info info;
    if (dladdr(mh, &info) == 0 || !info.dli_fname) return;
    if (!strstr(info.dli_fname, "UnityFramework")) return;
    installUnityHooks((uintptr_t)mh, info.dli_fname);
}

static void installUnityHooks(uintptr_t unityBase, const char *unityName) {
    if (g_unityHooked) return;
    if (unityBase == 0) return;

    IPALog([NSString stringWithFormat:
              @"UnityFramework base=0x%lx (%s)",
              (unsigned long)unityBase, unityName ? unityName : "?"]);

#if IPA_CHINLAN
    KFChinlanPublish(unityBase);
#else
    KFInstallFrameRateHook(unityBase);
    KFInstallAfkDisableHook(unityBase);
    KFInstallAnalysisTuneHook(unityBase);
    KFInstallKifuObserveHook(unityBase);
    KFInstallAccountObserveHook(unityBase);
    KFInstallGrpcLoggingHook(unityBase);
#endif

    g_unityHooked = YES;
    IPALog(@"=== All KiouForge hooks installed ===");
}

__attribute__((constructor)) static void init(void) {
    IPALoggingInit("com.neconome.shogi.kiouforge");
    IPALog([NSString stringWithFormat:
              @"=== KiouForge %s (%s) loaded ===",
              KIOU_FORGE_VERSION, KIOU_FORGE_COMMIT]);

    // Build identity so a stray log file can be matched back to the exact
    // dylib that wrote it. Flavor distinguishes JB (libsubstrate) / jailed
    // (Dobby-static) / chinlan (static cave + SLOT dispatcher).
#if IPA_CHINLAN
    static const char *const kBuildFlavor = "chinlan";
#elif IPA_JAILED
    static const char *const kBuildFlavor = "jailed";
#else
    static const char *const kBuildFlavor = "jb";
#endif
    IPALog([NSString stringWithFormat:
              @"build commit=%s flavor=%s built=%s %s",
              KIOU_FORGE_COMMIT, kBuildFlavor, __DATE__, __TIME__]);

    // Settings panel (right-edge swipe). Dispatches to main queue internally
    // and retries until the key window is available — safe to call here.
    KFGestureInstall();

    // Wire UnityFramework hooks the moment UnityFramework is mapped.
    // _dyld_register_func_for_add_image fires synchronously for every image
    // already loaded at registration time, then for every subsequent dlopen
    // — so this works whether UnityFramework is mapped when our constructor
    // runs or it gets dlopened later.
    _dyld_register_func_for_add_image(&kfOnImageAdded);

    IPALog(@"=== KiouForge constructor done ===");
}
