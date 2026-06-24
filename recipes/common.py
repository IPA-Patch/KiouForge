"""Version-independent recipe constants and cave payload builders for KiouForge.

Shared by all per-version modules (v1_0_1.py, v1_0_2.py, …).

Cave kinds
----------
entry    : REPLACES the original.  Cave BLRs the per-slot hook pointer
           (W9 = slot_index for diagnostics), then RETs.  Orig runs via
           the bypass entry at cave_va + 0x4C when the hook needs it.
           Used for FPS, AFK, engine tuning, kifu, and account hooks.

observer : PEEKS before orig runs.  Cave saves all arg registers, BLRs
           the single shared KIFU_SLOT hook pointer with W2 = mode_index,
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
# Slot index enum — must match ChinlanSites.h.
# ---------------------------------------------------------------------------

SLOT_SET_TARGET_FRAMERATE              = 0
SLOT_GAME_ORCHESTRATOR_IS_AFK          = 1
SLOT_NSS_SETHASHSIZE                   = 2
SLOT_NSS_SETSKILLEVEL                  = 3
SLOT_NSS_SEARCHFULL                    = 4
SLOT_KIFU_OBSERVE                      = 5
SLOT_ACCOUNT_EXISTS                    = 6
SLOT_ACCOUNT_LOGIN_ARGS_CREATE         = 7
SLOT_ACCOUNT_REGISTER_USER_ARGS_CREATE = 8
SLOT_ACCOUNT_RUN_LOGIN_SEQ_MOVENEXT    = 9
SLOT_ACCOUNT_GET_SELF_PROFILE_MOVENEXT = 10

SLOT_COUNT = 11

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
    if not (0 <= slot_index < SLOT_COUNT):
        raise ValueError(f"slot_index {slot_index} out of range [0, {SLOT_COUNT})")

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


# ---------------------------------------------------------------------------
# build_exports — assemble the public patch surface from per-version data.
# ---------------------------------------------------------------------------

def build_exports(sites, hook_slot_base_rva: int):
    """Return (PATCHES, CAVE_PATCHES, _SITES) from per-version site data.

    Parameters
    ----------
    sites:
        List of 5-tuples: (slot_index, site_rva, prologue_hex, kind, aux, label)
    hook_slot_base_rva:
        Base address of the hook slot table in __DATA,__bss.
        Slot N is at hook_slot_base_rva + N * 8.
    """
    patches: list = []  # KiouForge uses only cave patches, no inline patches

    cave_patches = []
    for slot_index, site_rva, prologue_hex, kind, aux, label in sites:
        prologue = bytes.fromhex(prologue_hex)
        slot_va  = hook_slot_base_rva + slot_index * 8
        if kind == CAVE_ENTRY:
            payload = build_entry_cave(site_rva, slot_va, prologue, slot_index)
            cave_label = f"slot[{slot_index:>2}] {label}"
        elif kind == CAVE_OBSERVER:
            payload = build_observer_cave(site_rva, slot_va, prologue, aux)
            cave_label = f"slot[{slot_index:>2}] observer mode={aux} {label}"
        else:
            raise AssertionError(f"unknown cave kind {kind!r} for {label}")
        cave_patches.append((site_rva, prologue, payload, cave_label))

    sites_index = [
        (slot_index, site_rva, prologue_hex, label)
        for slot_index, site_rva, prologue_hex, kind, aux, label in sites
    ]

    return patches, cave_patches, sites_index
