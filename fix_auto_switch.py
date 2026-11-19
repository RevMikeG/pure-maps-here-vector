#!/usr/bin/env python3
"""Safely clear saved manual map type and enable Pure Maps automatic mode selection.

Run only while Pure Maps is fully closed. Backs up configuration before editing.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

CONFIG_NAMES = (
    '.config/io.github.rinigus/PureMaps/pure-maps.json',
    '.config/harbour-pure-maps/pure-maps.json',
    '.config/pure-maps/pure-maps.json',
)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    candidates = [Path.home() / name for name in CONFIG_NAMES]
    found = [p for p in candidates if p.is_file() and not p.is_symlink()]
    if len(found) != 1:
        raise RuntimeError('Expected one Pure Maps configuration; found %s. %s' %
                           (len(found), ', '.join(str(x) for x in found)))
    path = found[0]
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise RuntimeError('Configuration is not an object')
    print('Manual map type:', repr(data.get('basemap_type')))
    print('Automatic map modes:', repr(data.get('basemap_auto_mode')))
    if args.dry_run:
        print('Dry run only. Would clear the manual type and enable automatic mode selection.')
        return
    backup = path.with_name('pure-maps.before-v13-auto-switch.json')
    if not backup.exists():
        shutil.copy2(path, backup)
        os.chmod(backup, 0o600)
    data['basemap_type'] = ''
    data['basemap_auto_mode'] = True
    temp = path.with_name(path.name + '.v13.tmp')
    fd = os.open(str(temp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    print('Saved automatic mode settings. Backup:', backup.name)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('ERROR:', str(e), file=sys.stderr)
        sys.exit(1)
