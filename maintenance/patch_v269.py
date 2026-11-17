"""Three-minute autosave; retain v268 diagnostics and all combat behavior."""
from patch_v268 import *
from patch_v200 import numbers

BASE_SHA = 'd2463df1306b07f3411ca74d1830824c4e9cebf7edd9fe674afbc833e9c01dff'

def build(runtime=None, rebuild_history=False):
 path = W/'game_v268.res'
 if rebuild_history or not path.exists():
  subprocess.run(['python3', str(W/'patch_v268.py')] + (['--rebuild-history'] if rebuild_history else []) + (['--runtime', runtime] if runtime else []), check=True)
 base = path.read_bytes(); assert hashlib.sha256(base).hexdigest() == BASE_SHA
 outer, mods = decode(base, [12, 14, 30])
 p = mods[12].protos[20]
 assert p.bc[120] == abc('MODVN', 1, 1, 25)
 # Slot 25 was introduced solely for autosave in v264. No instruction, shared
 # 3000-tick constant, save condition, timer period, or save callback changes.
 from ljtool import Reader
 r = Reader(p.raw[p.kend:]); nums = []
 for i in range(p.nkn):
  n = r.u(); nums.append(n >> 1 if n & 1 == 0 else None)
  if n & 1: r.u()
 assert nums[25] == 200 and nums[8] == 3000
 assert [pc for pc,x in enumerate(p.bc) if (x & 255) == (p.bc[120] & 255) and ((x >> 16) & 255) == 25] == [120]
 mods[12].protos[20] = numbers(p, {25: 1800})
 for mid,d in mods.items():
  for i,p in enumerate(d.protos):
   changed = False
   for j,v in enumerate(p.kgc):
    if not isinstance(v, bytes): continue
    new = v.replace(b'v1.268', b'v1.269')
    if mid == 12 and i in [76,22196]: new = new.replace(b'1.268', b'1.269')
    if new != v: p.kgc[j] = new; p.kraw[j] = encstr(new); changed = True
   if changed: d.protos[i] = Proto(rebuild_proto(p), i)
  raw = rebuild_dump(d, set()); assert Dump(raw).rebuild() == raw
  (W/f'module_{mid}_v269.ljbc').write_bytes(raw)
  packet = bytes.fromhex('0d0f3e03') + struct.pack('<I',len(raw)) + zlib.compress(raw,9)
  enc = rc4(packet, bytes.fromhex('2621215f5f6b6c5fb2e25f495f30'))
  set_string(outer.protos[0], mid, enc if mid == 12 else enc.hex().upper().encode())
 data = rc4(rebuild_dump(outer,{0}), b'_Npi_dest__cc_&%_23') + base[-10:]
 (W/'game_v269.res').write_bytes(data)
 report = {'version':'v1.269','base_sha256':BASE_SHA,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'autosave_ticks':1800,'timer_period_seconds':0.1,'autosave_seconds':180,'autosave_divisor_slot':25,'diagnostics_retained':True,'crash_root_cause_confirmed':False}
 (W/'build_v269.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n'); print(report)

if __name__ == '__main__':
 p=argparse.ArgumentParser();p.add_argument('--runtime');p.add_argument('--rebuild-history',action='store_true');a=p.parse_args();build(a.runtime,a.rebuild_history)
