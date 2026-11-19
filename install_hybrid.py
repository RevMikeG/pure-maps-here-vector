#!/usr/bin/env python3
"""Install a separate HERE raster-browsing / vector-navigation provider.

Requires existing working HERE Vector Traffic map definitions from either the
v1.2.1 installer or an older customized Jolla setup. No API keys are logged.
Use --dry-run to inspect; --remove removes only this provider's six map files.
"""
import argparse
import copy
import json
import os
import shutil
import sys
from pathlib import Path

from match_here_raster_day_v2 import classify, recolour, PALETTE, CASING

MAPS = Path.home() / '.local/share/io.github.rinigus/PureMaps/maps'
PROVIDER = 'HERE Hybrid Experimental'
PREFIX = 'here_hybrid_v13_'
PROFILES = ['HERE', 'online', 'mixed']
BUILTINS = [Path('/usr/share/harbour-pure-maps/maps'),
            Path('/usr/share/pure-maps/maps'),
            Path('/usr/share/harbour-pure-maps/poor/maps')]
# Prefer user-tested customized build, then upstream 1.2.1 generated files.
SOURCES = {
    ('day', True): ('here_vector_traffic_experimental.json', 'here_v12_traffic_day.json'),
    ('night', True): ('here_vector_night_traffic.json', 'here_v12_traffic_night.json'),
    ('day', False): ('here_vector_day_no_traffic.json', 'here_v12_traffic_off_day.json'),
    ('night', False): ('here_vector_night_no_traffic.json', 'here_v12_traffic_off_night.json'),
}

def read_json(p):
    with p.open(encoding='utf-8') as f:
        return json.load(f)

def choose_vector(light, traffic):
    expected_type = 'traffic' if traffic else 'default'
    for candidate in SOURCES[(light, traffic)]:
        path = MAPS / candidate
        if not path.is_file() or path.is_symlink():
            continue
        obj = read_json(path)
        if (obj.get('provider') == 'HERE Vector Traffic' and
                obj.get('light') == light and obj.get('type') == expected_type and
                obj.get('format') == 'mapbox-gl' and
                isinstance(obj.get('style_json'), dict) and
                isinstance(obj['style_json'].get('layers'), list)):
            return obj, candidate
    raise RuntimeError('No compatible HERE Vector Traffic ' + light + ' ' +
                       expected_type + ' style found. Install v1.2.1 first, or verify existing styles.')

def recolour_day(style):
    count = 0
    for layer in style.get('layers', []):
        match = classify(layer)
        if not match:
            continue
        category, prop, casing = match
        paint = layer.get('paint')
        if not isinstance(paint, dict) or prop not in paint:
            continue
        new_value, n = recolour(paint[prop], CASING.get(category, PALETTE[category])
                                if casing else PALETTE[category])
        if n:
            paint[prop] = new_value
            count += 1
    if count == 0:
        raise RuntimeError('Daytime vector has no recognizable colour layers; refusing to generate mismatched style')
    return count

def raster(light):
    name = 'here_4_traffic_' + light + '.json'
    data = None
    for folder in BUILTINS:
        candidate = folder / name
        if candidate.is_file():
            item = read_json(candidate)
            if item.get('format') == 'raster' and isinstance(item.get('tile_url'), list) and len(item['tile_url']) >= 2:
                data = item
                break
    if data is None:
        data = {
            'format': 'raster', 'keys': ['HERE_APIKEY'], 'tile_size': 256,
            'tile_url': [
                'https://maps.hereapi.com/v3/base/mc/{z}/{x}/{y}/png8?apiKey=#HERE_APIKEY#&ppi=400&size=512&features=pois:all&style=explore.' + light,
                'https://traffic.maps.hereapi.com/v3/flow/mc/{z}/{x}/{y}/png8?apiKey=#HERE_APIKEY#&ppi=400&size=512&style=explore.' + light,
            ], 'attribution': {'© HERE': 'https://legal.here.com'},
        }
    data = copy.deepcopy(data)
    data.update(provider=PROVIDER, name='HERE raster traffic (' + light + ')',
                profiles=PROFILES, light=light, type='default')
    data.pop('vehicle', None)
    return data

def vector(light, mode, traffic):
    data, source_name = choose_vector(light, traffic)
    data = copy.deepcopy(data)
    data.update(provider=PROVIDER, name='HERE vector ' + mode + ' (' + light + ')',
                profiles=PROFILES, light=light, type=mode)
    if light == 'day':
        count = recolour_day(data['style_json'])
        print('Prepared daytime', mode, 'style using', count, 'recoloured layers from', source_name)
    else:
        print('Preserved tested night style from', source_name)
    return data

def outputs(traffic=True):
    result = {}
    for light in ('day', 'night'):
        result[PREFIX + 'raster_' + light + '.json'] = raster(light)
        for mode in ('guidance', 'preview'):
            result[PREFIX + 'vector_' + mode + '_' + light + '.json'] = vector(light, mode, traffic)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Validate styles without writing')
    parser.add_argument('--remove', action='store_true', help='Remove files created for hybrid provider')
    parser.add_argument('--no-vector-traffic', action='store_true',
                        help='Choose traffic-free vector source when installing')
    args = parser.parse_args()
    if MAPS.is_symlink():
        raise RuntimeError('Map directory is a symlink; refusing to proceed')
    if args.remove:
        found = sorted(MAPS.glob(PREFIX + '*.json'))
        for path in found:
            if path.is_symlink():
                raise RuntimeError('Refusing symlink: ' + path.name)
        if args.dry_run:
            print('Would remove:', ', '.join(p.name for p in found))
            return
        for path in found:
            path.unlink()
            print('Removed', path.name)
        print('Original vector maps and QML unchanged.')
        return
    prepared = outputs(traffic=not args.no_vector_traffic)
    print('Validated', len(prepared), 'hybrid map definitions for provider:', PROVIDER)
    if args.dry_run:
        print('Dry run complete; no files changed.')
        return
    MAPS.mkdir(parents=True, exist_ok=True)
    collision = [name for name in prepared if (MAPS / name).exists()]
    if collision:
        raise RuntimeError('Hybrid files already exist; no files changed. Your working setup can be kept. '
                           'Do not reinstall unless you intentionally remove the experiment first.')
    made = []
    try:
        for name, obj in prepared.items():
            path = MAPS / name
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            made.append(path)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
                f.write('\n')
    except BaseException:
        for p in made:
            p.unlink(missing_ok=True)
        raise
    print('Hybrid installed. Select HERE Hybrid Experimental in Settings > Maps.')
    print('Enable Switch map modes and Sunrise and sunset day/night selection.')
    print('If the automatic mode selection sticks, run fix_auto_switch.py with Pure Maps closed.')
    print('Generated map files may include your HERE API key. Never upload them to GitHub.')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERROR:', type(exc).__name__, str(exc).split('apiKey=')[0], file=sys.stderr)
        sys.exit(1)
