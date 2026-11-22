"""Package only the tested player resource and the full maintenance inputs for v1.308."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

W = Path(__file__).resolve().parent
ROOT = W.parent


def package():
    data = (W / 'game_v308.res').read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    build = json.loads((W / 'build_v308.json').read_text(encoding='utf-8'))
    validation = json.loads((W / 'validation_v308.json').read_text(encoding='utf-8'))
    assert validation['all_passed'] and validation['version'] == build['version'] == 'v1.308'
    assert build['sha256'] == validation['sha256'] == sha
    for name, digest in validation['tested_files'].items():
        assert hashlib.sha256((W / name).read_bytes()).hexdigest() == digest, name

    basis = (ROOT / 'docs/玩家版说明_基础版.txt').read_text(encoding='utf-8')
    numbered = re.findall(r'^(\d+)\. (.+)$', basis, re.M)
    assert [int(number) for number, _ in numbered] == list(range(1, 31))
    changes = json.loads((W / 'player_changes_v308.json').read_text(encoding='utf-8'))
    assert changes == [item for _, item in numbered]
    assert basis.count('使用：') == basis.count('排查问题：') == 1
    info = basis.replace('《归梦 v2.26 魔改补丁》', '《归梦 v2.26 魔改补丁 v1.308》', 1)
    # Sync root-level player README (without version number in filename), overwriting if present.
    (ROOT / '使用说明_玩家版.txt').write_bytes(('\ufeff' + info).encode('utf-8'))

    output = W / 'deliverables'
    output.mkdir(exist_ok=True)
    player = output / '归梦v2.26_魔改补丁_v1.308.zip'
    with zipfile.ZipFile(player, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr('Lib/game.res', data)
        archive.writestr('log/', b'')
        archive.writestr('使用说明_玩家版.txt', ('\ufeff' + info).encode('utf-8'))

    manifest = json.loads((W / 'manifest.json').read_text(encoding='utf-8'))
    names = manifest['package_files'] + manifest['generated_reports']
    assert len(names) == len(set(names))
    kit = output / 'Guimeng_v1.308_maintenance.zip'
    with zipfile.ZipFile(kit, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in names:
            archive.write(ROOT / name, name)

    checksums = []
    for path in (player, kit):
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            if path == player:
                assert archive.namelist() == ['Lib/game.res', 'log/', '使用说明_玩家版.txt']
                assert archive.getinfo('使用说明_玩家版.txt').flag_bits & 0x800
                assert hashlib.sha256(archive.read('Lib/game.res')).hexdigest() == sha
            else:
                assert archive.namelist() == names
                assert all(info.flag_bits & 0x800 for info in archive.infolist()
                           if not info.filename.isascii())
        checksums.append({'name': path.name, 'bytes': path.stat().st_size,
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (output / 'checksums_v308.json').write_text(
        json.dumps({'resource_sha256': sha, 'packages': checksums}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(json.dumps(checksums, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    package()
