"""v1.341 patch for 「来世续缘」 only (「前尘忆梦」 untouched):
Fixes remaining delay feel on mercenary ranged skills (盛开/白莲/红莲/月桂/蝉舞) after v1.340:
1. Magic_04.empak <技能>_命中 hit-effect startup fix (特效类.初始化 wrapper):
   - Strips leading invisible 4x4 / placeholder blank frames from a fresh copy of 动画配置.key
     (without mutating shared 动作组 tables) and updates 总帧数 accordingly.
   - Normalizes 延迟时间 = 0 (fixing 蝉舞's -50ms config quirk), tightens 播放速度 = 0.65 (~1.54x
     crisper hit-burst peak), and pre-primes the first visible frame via 置当前帧 so the hit
     effect renders immediately on the exact arrival frame.
2. Ranged mercenary skill cast-action speed fix (类_事件.播放指定动作 wrapper):
   - In m12/5293, 刺客普通攻击 scales 横切 with attack speed (0.8 -> 0.4, ~24 frames), while
     盛开/白莲/红莲/蝉舞 (跳斩) and 月桂 (跳刺) were hardcoded to 0.5 (~41 frames, +15..17 frames
     extra 播放动作 lock). Scales 跳斩/跳刺 by the same attack-speed curve when merc_is_ranged(self)
     so recovery matches 横切 (~24 frames at high attack speed), leaving melee two-handed assassin
     and 「前尘忆梦」 100% untouched.
3. Target-switch 蝉舞 launch unblock + arrival epsilon alignment:
   - Clears stale actor.播放动作 = false when 蝉舞 prepares on a live ranged merc so m22/4 PC 485
     never stalls 蝉舞 in 释放技能组 for 24..41 frames during target switch (m12/18047).
   - Uses explicit string keys in MERC_RETREAT_DIST and matches state.命中动画延迟 = (延迟dt or 0) - 1e-9.
4. Retains all v1.340..v1.299 features intact; 「前尘忆梦」 remains 100% untouched.
"""
import hashlib
import json
import struct
import zlib

from ljtool import Dump, Proto, rc4
from patch_v139 import W, rebuild_proto
from patch_v201 import set_string
from resource_tools import decode

BASE_SHA = '772c68e5d127c0cbfa910e937623d68d8bdf7cfd6a6bed950b1fdf9b76f7ade4'
MODULES = (12, 14, 30)


def patch_module14_init_781(m14, runtime_src):
    """Replace embedded runtime_v340.lua string constant in 14/781 with runtime_v341.lua."""
    p = Proto(m14.protos[781].raw, 781)
    marker = b'-- Guimeng v1.340 runtime helper'
    hits = []
    for slot, val in enumerate(p.kgc):
        if isinstance(val, bytes) and val.startswith(marker):
            hits.append(p.nkgc - 1 - slot)
    assert len(hits) == 1, f'Expected exactly 1 runtime_v340.lua constant in 14/781, found {hits}'
    set_string(p, hits[0], runtime_src.encode('gbk'))
    m14.protos[781] = Proto(rebuild_proto(p), 781)
    return hits[0]


def build():
    base = (W / 'game_v340.res').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_SHA, 'game_v340.res SHA256 mismatch'

    runtime_src = (W / 'runtime_v341.lua').read_text(encoding='utf-8')
    runtime_gbk = runtime_src.encode('gbk')
    for ch in runtime_src:
        b = ch.encode('gbk')
        assert not (len(b) == 2 and b[1] == 0x5C), f'GBK 0x5C hazard: {ch!r}'

    outer, modules = decode(base, MODULES)

    runtime_gc_idx = patch_module14_init_781(modules[14], runtime_src)

    version_updates = 0
    for mid, dump in modules.items():
        for p in dump.protos:
            for slot, value in enumerate(p.kgc):
                if not isinstance(value, bytes):
                    continue
                if mid == 14 and p.idx == 781 and (p.nkgc - 1 - slot) == runtime_gc_idx:
                    continue
                updated = value.replace(b'v1.340', b'v1.341')
                if mid == 12 and p.idx in (76, 22232):
                    updated = updated.replace(b'1.340', b'1.341')
                if updated != value:
                    set_string(p, p.nkgc - 1 - slot, updated)
                    version_updates += 1
        raw = dump.rebuild()
        assert Dump(raw).rebuild() == raw
        packet = bytes.fromhex('0d0f3e03') + struct.pack('<I', len(raw)) + zlib.compress(raw, 9)
        encrypted = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
        set_string(outer.protos[0], mid, encrypted if mid == 12 else encrypted.hex().upper().encode())

    data = rc4(outer.rebuild(), b'_Npi_dest__cc_&%_23') + base[-10:]
    (W / 'game_v341.res').write_bytes(data)

    report = {
        'version': 'v1.341',
        'base_sha256': BASE_SHA,
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'scope': '来世续缘 only (前尘忆梦 untouched)',
        'runtime_v341_lua_gbk_bytes': len(runtime_gbk),
        'runtime_gc_index_14_781': runtime_gc_idx,
        'version_string_updates': version_updates,
        'changes_v341': {
            'merc_hit_fx_blank_strip_and_prime': 'Wraps 特效类.初始化 for Magic_04.empak <技能>_命中 to strip leading 4x4/blank frames from a fresh copy of 动画配置.key, normalize 延迟时间=0, tighten 播放速度=0.65, and pre-prime first visible frame via 置当前帧',
            'merc_ranged_skill_action_speed': 'Wraps 类_事件.播放指定动作 for ranged assassin merc 跳斩/跳刺 to scale with 攻击速度 matching 横切 (~24f at high attack speed instead of fixed 0.5 / ~41f), keeping melee two-handed assassin untouched',
            'merc_chanwu_launch_unblock': 'Clears stale actor.播放动作=false on 蝉舞 prepare for live ranged merc so m22/4 PC 485 never stalls target-switch 蝉舞 behind a prior action; aligns state.命中动画延迟=(延迟dt or 0)-1e-9 and uses explicit string keys in MERC_RETREAT_DIST',
            'qianchi_isolated': '前尘忆梦 untouched',
        },
    }
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    (W / 'build_v341.json').write_text(report_text, encoding='utf-8')
    (W.parent / 'docs' / 'reports' / 'build_v341.json').write_text(report_text, encoding='utf-8')
    print(report['sha256'], report['bytes'], 'gc_idx=', runtime_gc_idx, 'ver_updates=', version_updates)


if __name__ == '__main__':
    build()
