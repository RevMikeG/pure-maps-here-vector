#!/usr/bin/env python3
"""Archive redundant custom HERE Vector providers, retaining HERE Vector Traffic.

Run as a normal Sailfish user, with Pure Maps fully closed.
Use --restore to undo the most recent cleanup.
Does not modify map data, app QML, or built-in HERE maps.
"""
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

MAPS = Path.home() / '.local/share/io.github.rinigus/PureMaps/maps'
ARCHIVES = Path.home() / '.local/share/io.github.rinigus/PureMaps/archived-here-maps'
MANIFEST = ARCHIVES / 'last_cleanup.json'
KEEP = 'HERE Vector Traffic'


def read_map(path):
    try:
        d = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return None
    return d if isinstance(d, dict) else None


def restore():
    if not MANIFEST.is_file():
        raise RuntimeError('No cleanup manifest found to restore.')
    m = json.loads(MANIFEST.read_text(encoding='utf-8'))
    old_dir = ARCHIVES / m['archive']
    for name in m['files']:
        if (MAPS / name).exists():
            raise RuntimeError('Restore stopped: a map already exists: ' + name)
        if not (old_dir / name).is_file():
            raise RuntimeError('Restore stopped: archived map missing: ' + name)
    for name in m['files']:
        shutil.move(str(old_dir / name), str(MAPS / name))
        print('Restored:', name)
    MANIFEST.unlink()
    print('Restored the archived HERE Vector map definitions. Restart Pure Maps.')


def main():
    if '--restore' in sys.argv[1:]:
        return restore()
    if not MAPS.is_dir():
        raise RuntimeError('Pure Maps custom map directory not found: ' + str(MAPS))
    maps = [(p, read_map(p)) for p in MAPS.glob('*.json') if p.is_file()]
    ours = [(p, d) for p, d in maps
            if d and isinstance(d.get('provider'), str)
            and d['provider'].startswith('HERE Vector')]
    kept = [(p, d) for p, d in ours if d['provider'] == KEEP]
    unwanted = [(p, d) for p, d in ours if d['provider'] != KEEP]
    if not kept:
        raise RuntimeError('No HERE Vector Traffic map definitions found. Nothing changed.')
    combinations = {(d.get('light'), d.get('type')) for p, d in kept}
    required = {('day','traffic'), ('day','default'), ('night','traffic'), ('night','default')}
    if not required.issubset(combinations):
        print('Currently found:', sorted(map(str, combinations)))
        raise RuntimeError('Missing a working day/night Traffic/Default combination. Nothing changed.')
    if MANIFEST.exists():
        raise RuntimeError('An earlier cleanup is archived. Restore it before running cleanup again.')
    print('Keeping provider:', KEEP, f'({len(kept)} style definitions)')
    for p, d in kept:
        print('  KEEP', p.name, '['+str(d.get('light'))+', '+str(d.get('type'))+']')
    if not unwanted:
        print('No redundant HERE Vector providers remain. No changes made.')
        return
    print('Archiving redundant map definitions:')
    for p, d in unwanted:
        print('  ARCHIVE', p.name, 'provider:', d['provider'])
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    os.chmod(ARCHIVES, 0o700)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    dest = ARCHIVES / stamp
    dest.mkdir(mode=0o700)
    moved = []
    try:
        for p, _ in unwanted:
            shutil.move(str(p), str(dest / p.name))
            moved.append(p.name)
        MANIFEST.write_text(json.dumps({'archive':stamp,'files':moved}, indent=2)+'\n', encoding='utf-8')
        os.chmod(MANIFEST, 0o600)
    except BaseException:
        for name in moved:
            shutil.move(str(dest/name), str(MAPS/name))
        raise
    print('Done. Restart Pure Maps. Choose HERE Vector Traffic under Settings > Maps.')
    print('In Layers > Type, use Default (off) and Traffic (on).')
    print('To restore archived maps: python3 ~/Downloads/tidy_here_maps.py --restore')
    print('Archive is outside the scanned maps directory:', dest)
    print('Archived files may contain your HERE API key: do not publish them.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('ERROR:', e, file=sys.stderr)
        sys.exit(1)
