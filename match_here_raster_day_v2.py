#!/usr/bin/env python3
"""HERE Hybrid v1.3: recolour only vector day maps towards supplied HERE raster screenshot.

No root; no network access; never prints keys or URLs. Preserves geometry, text,
traffic, road widths and night styles. --restore restores these changes only.
"""
import argparse
import copy
import json
import os
import re
import shutil
from pathlib import Path

MAPS = Path.home() / '.local/share/io.github.rinigus/PureMaps/maps'
MODES = ('guidance', 'preview')
TARGETS = [MAPS / ('here_hybrid_v13_vector_%s_day.json' % mode) for mode in MODES]
BACKUP = '.before_raster_reference_v2.bak'

# Approximate reference colours measured from user's HERE raster screenshot.
# Note: exact pixels vary with opacity/antialiasing and zoom level.
PALETTE = {
    'background': '#F4F8FA',
    'land': '#F4F8FA',
    'urban': '#ECF1F7',
    'park': '#C8EEE4',
    'wood': '#B9E6D8',
    'water': '#C7E2F4',
    'motorway': '#9BAFCB',
    'trunk': '#A9BDD4',
    'primary': '#C1D2E8',
    'secondary': '#D2E0F0',
    'local': '#DCE7F3',
}
# For road outlines/casing a darker tint gives visual definition.
CASING = {
    'motorway': '#879DBA', 'trunk': '#97ADC8',
    'primary': '#ADBFDA', 'secondary': '#C0D1E7', 'local': '#CAD9EA',
}

COLOR_RE = re.compile(r'^(?:#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\))$')


def terms(layer):
    parts = [str(layer.get('id', '')), str(layer.get('source-layer', ''))]
    # Only filter metadata names, never arbitrary string values, to avoid URLs or keys.
    filt = layer.get('filter')
    if isinstance(filt, list):
        parts.extend(str(x) for x in filt if isinstance(x, str) and len(x) < 80)
    return ' '.join(parts).lower().replace('_', '-').replace(' ', '-')


def classify(layer):
    typ = layer.get('type')
    name = terms(layer)
    ident = str(layer.get('id', '')).lower()
    if any(x in name for x in ('traffic', 'congestion', 'flow', 'incident', 'route', 'navigation', 'shield', 'label', 'text', 'symbol', 'rail', 'ferry', 'boundary', 'border', 'contour')):
        return None
    if typ == 'background': return 'background', 'background-color', False
    if typ == 'fill':
        if any(x in name for x in ('water', 'lake', 'river', 'ocean', 'sea')):
            return 'water', 'fill-color', False
        if any(x in name for x in ('forest', 'wood', 'tree')):
            return 'wood', 'fill-color', False
        if any(x in name for x in ('park', 'grass', 'garden', 'green', 'recreation', 'nature', 'vegetation', 'golf')):
            return 'park', 'fill-color', False
        if any(x in name for x in ('urban', 'residential', 'built-up', 'builtup', 'building', 'industrial', 'commercial')):
            return 'urban', 'fill-color', False
        if any(x in name for x in ('land', 'ground', 'earth')):
            return 'land', 'fill-color', False
    if typ == 'line':
        if any(x in name for x in ('river', 'water', 'stream', 'canal')):
            return 'water', 'line-color', False
        if not any(x in name for x in ('road','highway','street','motorway','freeway','trunk','primary','secondary','tertiary','residential','minor','service','local','path','track')):
            return None
        casing = any(x in ident for x in ('casing', 'outline', 'border', 'edge', 'stroke'))
        if any(x in name for x in ('motorway', 'freeway')): return 'motorway', 'line-color', casing
        if 'trunk' in name: return 'trunk', 'line-color', casing
        if any(x in name for x in ('primary', 'major')): return 'primary', 'line-color', casing
        if any(x in name for x in ('secondary', 'tertiary')): return 'secondary', 'line-color', casing
        if any(x in name for x in ('local', 'minor', 'residential', 'service', 'street', 'road', 'highway')):
            return 'local', 'line-color', casing
    return None


def recolour(value, target):
    """Keep style expression mechanics, replace *only* CSS colour literals inside."""
    if isinstance(value, str):
        if COLOR_RE.fullmatch(value.strip()):
            return target, int(value.lower() != target.lower())
        return value, 0
    if isinstance(value, list):
        result = []; changed = 0
        for v in value:
            nv, n = recolour(v, target)
            result.append(nv); changed += n
        return result, changed
    # MapLibre colours generally arrays or strings, but support nested values safely.
    if isinstance(value, dict):
        result = {}; changed = 0
        for k, v in value.items():
            nv, n = recolour(v, target)
            result[k] = nv; changed += n
        return result, changed
    return value, 0


def load(path, mode):
    if not path.is_file() or path.is_symlink():
        raise ValueError('Expected safe hybrid daytime file missing: ' + path.name)
    obj = json.loads(path.read_text(encoding='utf-8'))
    if any((obj.get('provider') != 'HERE Hybrid Experimental',
            obj.get('type') != mode, obj.get('light') != 'day',
            obj.get('format') != 'mapbox-gl')):
        raise ValueError('Unexpected metadata in ' + path.name)
    style = obj.get('style_json')
    if not isinstance(style, dict) or not isinstance(style.get('layers'), list):
        raise ValueError('Missing style_json.layers in ' + path.name)
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    backups = [p.with_name(p.name + BACKUP) for p in TARGETS]

    if args.restore:
        for p, b in zip(TARGETS, backups):
            if p.is_symlink() or not b.is_file() or b.is_symlink():
                raise ValueError('Missing safe backup for ' + p.name)
        if args.dry_run:
            print('Both backups present; restore is possible.')
            return
        for p, b in zip(TARGETS, backups):
            shutil.copy2(b, p)
            p.chmod(0o600)
            print('Restored:', p.name)
        return

    if any(b.exists() for b in backups) and not all(b.is_file() for b in backups):
        raise ValueError('Partial backup set. Refusing to continue.')
    if all(b.exists() for b in backups):
        raise ValueError('This palette was already applied. Use --restore to undo before running again.')
    originals = [load(p, mode) for p, mode in zip(TARGETS, MODES)]
    updated = copy.deepcopy(originals)
    change_counts = []
    for obj, target_path in zip(updated, TARGETS):
        altered = []
        for layer in obj['style_json']['layers']:
            spec = classify(layer)
            if not spec: continue
            category, prop, casing = spec
            paint = layer.get('paint')
            if not isinstance(paint, dict) or prop not in paint: continue
            target = CASING.get(category, PALETTE[category]) if casing else PALETTE[category]
            new_val, n = recolour(paint[prop], target)
            if n:
                paint[prop] = new_val
                altered.append((layer.get('id','?'), n))
        change_counts.append(len(altered))
        print('%s: %s layers recoloured' % (target_path.name, len(altered)))
        for name, n in altered[:40]:
            print('  -', name, '(colour entries:', n, ')')
        if len(altered) > 40:
            print('  ... plus', len(altered)-40, 'other layers')
    if not all(change_counts):
        print('No matching colour layers in one or both files. Nothing written.')
        print('Please share the layer-ID report from the existing inspector.')
        return
    if args.dry_run:
        print('Dry run complete. Nothing written.')
        return
    for path, backup in zip(TARGETS, backups):
        shutil.copy2(path, backup)
        backup.chmod(0o600)
    written = []
    try:
        for path, doc in zip(TARGETS, updated):
            temp = path.with_name(path.name + '.raster-v2.tmp')
            fd = os.open(str(temp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as fh:
                json.dump(doc, fh, ensure_ascii=False, indent=2)
                fh.write('\n')
            os.replace(temp, path)
            written.append(path)
    except Exception:
        for p, b in zip(TARGETS, backups):
            if b.is_file(): shutil.copy2(b, p)
        raise
    print('Finished. Restart Pure Maps; select HERE Hybrid Experimental and enter daytime navigation.')
    print('Only the two hybrid day-vector definitions were edited; no night, raster or QML changes.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        raise SystemExit('ERROR: ' + str(exc))
