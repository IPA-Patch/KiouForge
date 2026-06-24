"""Version-independent recipe constants and cave payload builders for KiouForge.

Shared by all per-version modules (v1_0_1.py, v1_0_2.py, …).

Cave kinds
----------
entry    : REPLACES the original.  Cave BLRs the per-slot hook pointer
           (W9 = slot_index for diagnostics), then RETs.  Orig runs via
           the bypass entry at cave_va + KIOU_CHINLAN_CAVE_BYPASS_OFFSET
           when the hook needs it.
           Used for FPS, AFK, engine tuning, kifu, and account hooks.

observer : PEEKS before orig runs.  Cave saves all arg registers, BLRs
           the single shared KIFU_OBSERVE slot pointer with W2 = mode_index,
           restores, runs displaced prologue, branches to orig+4.
           The hook's return value is dead.
           Used for IMatchMode.OnMatchEndAsync × 5.
"""

from __future__ import annotations

from tools.encode import (
    add_x_imm,
    adrp,
    b_imm,
    blr_x,
    ldp_off_x,
    ldp_post_x,
    ldr_x_imm,
    movz_w_imm,
    ret_insn,
    stp_off_x,
    stp_pre_x,
)

# ---------------------------------------------------------------------------
# Target identification
# ---------------------------------------------------------------------------

TARGET_BASENAME = "UnityFramework"
DYLIB_PATH = "@executable_path/Frameworks/KiouForge.dylib"

# ---------------------------------------------------------------------------
# Info.plist additions
# ---------------------------------------------------------------------------

PLIST_KEYS: dict = {
    "CADisableMinimumFrameDurationOnPhone": True,
    "UIFileSharingEnabled": True,
    "LSSupportsOpeningDocumentsInPlace": True,
}

# ---------------------------------------------------------------------------
# Cave kinds
# ---------------------------------------------------------------------------

CAVE_ENTRY    = "entry"
CAVE_OBSERVER = "observer"

CAVE_PAYLOAD_SIZE = 84  # 21 arm64 instructions

_NOP = b"\x1f\x20\x03\xd5"

# ---------------------------------------------------------------------------
# Hook ID enum — mirrors KIOU_SLOT_* in ChinlanSites.h.
#
# Maps hook_id_name → slot_index.  CAVE_OBSERVER hooks that share a slot
# (all KIFU_OBSERVE variants map to slot 5) must also appear in
# OBSERVER_AUX with their KiouMatchMode mode_index.
# ---------------------------------------------------------------------------

HOOK_IDS: dict[str, int] = {
    "KIOU_KF_HOOK_SET_TARGET_FRAMERATE":           0,
    "KIOU_KF_HOOK_GAME_ORCHESTRATOR_IS_AFK":       1,
    "KIOU_KF_HOOK_NSS_SETHASHSIZE":                2,
    "KIOU_KF_HOOK_NSS_SETSKILLEVEL":               3,
    "KIOU_KF_HOOK_NSS_SEARCHFULL":                 4,
    "KIOU_KF_HOOK_KIFU_OBSERVE_AI":                5,
    "KIOU_KF_HOOK_KIFU_OBSERVE_CPUSTREAM":         5,
    "KIOU_KF_HOOK_KIFU_OBSERVE_LOCAL":             5,
    "KIOU_KF_HOOK_KIFU_OBSERVE_ONLINE":            5,
    "KIOU_KF_HOOK_KIFU_OBSERVE_REPLAY":            5,
    "KIOU_KF_HOOK_ACCOUNT_EXISTS":                 6,
    "KIOU_KF_HOOK_LOGIN_ARGS_CREATE":              7,
    "KIOU_KF_HOOK_REGISTER_USER_ARGS_CREATE":      8,
    "KIOU_KF_HOOK_RUN_LOGIN_SEQ_MOVENEXT":         9,
    "KIOU_KF_HOOK_GET_SELF_PROFILE_MOVENEXT":     10,
}

SLOT_COUNT = 11

# Observer-only: hook_id_name → KiouMatchMode index passed in W2.
OBSERVER_AUX: dict[str, int] = {
    "KIOU_KF_HOOK_KIFU_OBSERVE_AI":        0,
    "KIOU_KF_HOOK_KIFU_OBSERVE_CPUSTREAM": 1,
    "KIOU_KF_HOOK_KIFU_OBSERVE_LOCAL":     2,
    "KIOU_KF_HOOK_KIFU_OBSERVE_ONLINE":    3,
    "KIOU_KF_HOOK_KIFU_OBSERVE_REPLAY":    4,
}

# ---------------------------------------------------------------------------
# Cave payload builders
# ---------------------------------------------------------------------------

_ENTRY_HEAD_INSNS = 8   # STP, ADRP, LDR, MOVZ, BLR, LDP, RET, NOP
_ENTRY_TAIL_BYTES = 8   # displaced_insn + B orig+4
_ENTRY_PAD_INSNS  = (CAVE_PAYLOAD_SIZE - _ENTRY_HEAD_INSNS * 4 - _ENTRY_TAIL_BYTES) // 4


def build_entry_cave(orig_va: int, slot_va: int, displaced_insn: bytes, slot_index: int):
    """Return a ``build(cave_va) -> bytes`` closure for an entry cave.

    W9 carries the slot_index so the hook can identify itself in logs
    (it's a caller-saved scratch reg, not an argument reg).
    """
    if len(displaced_insn) != 4:
        raise ValueError(f"displaced_insn must be 4 bytes; got {len(displaced_insn)}")
    if not (0 <= slot_index <= 0xFFFF):
        raise ValueError(f"slot_index out of MOVZ range: {slot_index}")

    def build(cave_va: int) -> bytes:
        out = bytearray()
        cur = cave_va

        def emit(insn: bytes) -> None:
            nonlocal cur
            out.extend(insn)
            cur += 4

        emit(stp_pre_x(29, 30, 31, -0x10))
        emit(adrp(16, cur, slot_va))
        emit(ldr_x_imm(16, 16, slot_va & 0xFFF))
        emit(movz_w_imm(9, slot_index))
        emit(blr_x(16))
        emit(ldp_post_x(29, 30, 31, 0x10))
        emit(ret_insn())
        emit(_NOP)

        for _ in range(_ENTRY_PAD_INSNS):
            emit(_NOP)

        emit(displaced_insn)
        emit(b_imm(cur, orig_va + 4))

        assert len(out) == CAVE_PAYLOAD_SIZE, (
            f"entry cave wrong size: got {len(out)}, expected {CAVE_PAYLOAD_SIZE}"
        )
        return bytes(out)

    return build


def build_observer_cave(orig_va: int, slot_va: int, displaced_insn: bytes, mode_index: int):
    """Return a ``build(cave_va) -> bytes`` closure for an observer cave.

    W2 carries the mode_index so a single KIFU_OBSERVE slot dispatcher
    can distinguish which IMatchMode site fired.
    """
    if len(displaced_insn) != 4:
        raise ValueError(f"displaced_insn must be 4 bytes; got {len(displaced_insn)}")
    if not (0 <= mode_index <= 0xFFFF):
        raise ValueError(f"mode_index out of MOVZ range: {mode_index}")

    def build(cave_va: int) -> bytes:
        out = bytearray()
        cur = cave_va

        def emit(insn: bytes) -> None:
            nonlocal cur
            out.extend(insn)
            cur += 4

        emit(stp_pre_x(29, 30, 31, -0x90))
        emit(stp_off_x(19, 20, 31, 0x10))
        emit(stp_off_x(21, 22, 31, 0x20))
        emit(stp_off_x(0, 1, 31, 0x30))
        emit(stp_off_x(2, 3, 31, 0x40))
        emit(stp_off_x(4, 5, 31, 0x50))
        emit(stp_off_x(6, 7, 31, 0x60))
        emit(add_x_imm(29, 31, 0))
        emit(adrp(16, cur, slot_va))
        emit(ldr_x_imm(16, 16, slot_va & 0xFFF))
        emit(movz_w_imm(2, mode_index))
        emit(blr_x(16))
        emit(ldp_off_x(6, 7, 31, 0x60))
        emit(ldp_off_x(4, 5, 31, 0x50))
        emit(ldp_off_x(2, 3, 31, 0x40))
        emit(ldp_off_x(0, 1, 31, 0x30))
        emit(ldp_off_x(21, 22, 31, 0x20))
        emit(ldp_off_x(19, 20, 31, 0x10))
        emit(ldp_post_x(29, 30, 31, 0x90))
        emit(displaced_insn)
        emit(b_imm(cur, orig_va + 4))

        assert len(out) == CAVE_PAYLOAD_SIZE, (
            f"observer cave wrong size: got {len(out)}, expected {CAVE_PAYLOAD_SIZE}"
        )
        return bytes(out)

    return build


def payload_for_site(site_rva: int, prologue_bytes: bytes, hook_id_name: str,
                     kind: str, hook_slot_rva: int):
    """Return the appropriate cave builder closure for a site row."""
    slot_index = HOOK_IDS[hook_id_name]
    slot_va = hook_slot_rva + slot_index * 8
    if kind == CAVE_ENTRY:
        return build_entry_cave(site_rva, slot_va, prologue_bytes, slot_index)
    if kind == CAVE_OBSERVER:
        mode_index = OBSERVER_AUX[hook_id_name]
        return build_observer_cave(site_rva, slot_va, prologue_bytes, mode_index)
    raise AssertionError(f"unknown cave kind {kind!r}")


# ---------------------------------------------------------------------------
# build_exports — assemble the public patch surface from per-version data.
# ---------------------------------------------------------------------------

def build_exports(sites, hook_slot_rva: int):
    """Return (PATCHES, CAVE_PATCHES, _SITES) from per-version site data.

    Parameters
    ----------
    sites:
        List of 5-tuples: (site_rva, prologue_hex, hook_id_name, kind, label)
    hook_slot_rva:
        Base address of the hook slot table in __DATA,__bss.
        Slot N lives at hook_slot_rva + N * 8.
    """
    patches: list = []  # KiouForge uses only cave patches, no inline patches

    cave_patches = [
        (
            site_rva,
            bytes.fromhex(prologue_hex),
            payload_for_site(
                site_rva, bytes.fromhex(prologue_hex), hook_id_name, kind, hook_slot_rva,
            ),
            f"{label}: route to KiouForge {kind} cave ({hook_id_name})",
        )
        for site_rva, prologue_hex, hook_id_name, kind, label in sites
    ]

    sites_index = [
        (HOOK_IDS[hook_id_name], site_rva, prologue_hex, label)
        for site_rva, prologue_hex, hook_id_name, kind, label in sites
    ]

    return patches, cave_patches, sites_index
