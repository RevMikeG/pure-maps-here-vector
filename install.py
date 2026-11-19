#!/usr/bin/env python3
"""HERE Hybrid v1.3: standalone installer and verified rollback.

Creates one provider: raster while browsing, vector while navigating.
Existing compatible vector styles are reused as input; otherwise new HERE
styles are downloaded. Does not modify original styles or QML.
Generated files may contain API credentials. NEVER commit them to GitHub.
"""
import argparse
import ast
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit, quote
from urllib.request import Request, urlopen

HOME = Path.home()
MAPS = HOME / '.local/share/io.github.rinigus/PureMaps/maps'
CONFIGS = [HOME / '.config/io.github.rinigus/PureMaps/pure-maps.json',
           HOME / '.config/harbour-pure-maps/pure-maps.json',
           HOME / '.config/pure-maps/pure-maps.json']
BUNDLED = [Path('/usr/share/harbour-pure-maps/poor/apikeys.py'),
           Path('/usr/share/pure-maps/poor/apikeys.py')]
BASE_URL = 'https://assets.vector.hereapi.com/styles/berlin/base/mapbox/tilezen'
# Use the fixed, tested HERE v3 traffic tile coordinate order XYZ z/x/y.
TRAFFIC_URL = ('https://traffic.maps.hereapi.com/v3/flow/mc/{{z}}/{{x}}/{{y}}/png'
               '?apiKey={key}&size=512&minTrafficCongestion={level}')

DAY = {
    'background': ('background-color', '#F5F3E9'),
    'landuse-urban-copy': ('fill-color', '#EEEDE5'),
    'landuse-urban': ('fill-color', '#EEEDE5'),
    'landuse-urban-area': ('fill-color', '#EEEDE5'),
    'landuse-park': ('fill-color', '#BCE3AE'),
    'landuse-park-national': ('fill-color', '#C5DDB5'),
    'landuse-pitch': ('fill-color', '#B4D99D'),
    'landuse-hospital': ('fill-color', '#F5DFE5'),
    'landuse-cemetery': ('fill-color', '#D7E7D0'),
    'landuse-bridge': ('fill-color', '#E8E5DD'),
    'landuse-farmyard': ('fill-color', '#EDE9D9'),
    'landuse-zoo': ('fill-color', '#C9E6B8'),
    'landuse-religion': ('fill-color', '#EEE5D3'),
    'landuse-industrial': ('fill-color', '#E1E3E5'),
    'landuse-beach': ('fill-color', '#F6E7B6'),
    'landuse-aerodrome': ('fill-color', '#E8E9E8'),
    'landuse-runway': ('fill-color', '#B9C0C4'),
    'water': ('fill-color', '#90CBE8'),
    'road-residential': ('line-color', '#FFFFFF'),
    'road-secondary': ('line-color', '#F9E4A3'),
    'road-tertiary': ('line-color', '#F8EDCB'),
    'road-trunk': ('line-color', '#F5AF55'),
    'road-primary': ('line-color', '#F5AF55'),
    'road-highway-link': ('line-color', '#8BB9E8'),
    'road-highway': ('line-color', '#579ADD'),
}
NIGHT = {
    'background': ('background-color', '#18232D'),
    'landuse-urban-copy': ('fill-color', '#293741'),
    'landuse-urban': ('fill-color', '#293741'),
    'landuse-urban-area': ('fill-color', '#293741'),
    'landuse-park': ('fill-color', '#28493E'),
    'landuse-park-national': ('fill-color', '#2B4D40'),
    'landuse-pitch': ('fill-color', '#335745'),
    'landuse-hospital': ('fill-color', '#503B4B'),
    'landuse-cemetery': ('fill-color', '#35483E'),
    'landuse-bridge': ('fill-color', '#35414B'),
    'landuse-farmyard': ('fill-color', '#403D36'),
    'landuse-zoo': ('fill-color', '#355542'),
    'landuse-religion': ('fill-color', '#453E44'),
    'landuse-industrial': ('fill-color', '#374049'),
    'landuse-beach': ('fill-color', '#535044'),
    'landuse-aerodrome': ('fill-color', '#303D48'),
    'landuse-runway': ('fill-color', '#54616B'),
    'water': ('fill-color', '#183E5A'),
    'road-residential': ('line-color', '#89969F'),
    'road-secondary': ('line-color', '#89969F'),
    'road-tertiary': ('line-color', '#A8A798'),
    'road-trunk': ('line-color', '#A8B2BC'),
    'road-primary': ('line-color', '#A8B2BC'),
    'road-highway-link': ('line-color', '#4B99D3'),
    'road-highway': ('line-color', '#4D9CE3'),
}

def read_key():
    for path in CONFIGS:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                key = data.get('keys', {}).get('HERE_APIKEY', '')
                if isinstance(key, str) and key.strip():
                    return key.strip(), 'existing Pure Maps configuration'
            except (OSError, ValueError, AttributeError):
                pass
    for path in BUNDLED:
        if not path.is_file():
            continue
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in tree.body:
                if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == 'Keys' for t in node.targets
                ):
                    data = ast.literal_eval(node.value)
                    key = data.get('HERE_APIKEY', '')
                    if isinstance(key, str) and key.strip():
                        return key.strip(), 'bundled Pure Maps key'
        except (OSError, SyntaxError, ValueError, TypeError, AttributeError):
            pass
    raise RuntimeError('Could not access the HERE key used by Pure Maps. '
                       'Check HERE account settings and licence acceptance.')


def add_key(url, key):
    if not isinstance(url, str) or not url.startswith(('https://', 'http://')):
        return url
    parts = urlsplit(url)
    if not (parts.hostname and (parts.hostname == 'hereapi.com' or
                                parts.hostname.endswith('.hereapi.com'))):
        return url
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if not any(x.lower() == 'apikey' for x in query):
        query['apikey'] = key
    return urlunsplit((parts.scheme, parts.netloc, parts.path,
                       urlencode(query), parts.fragment))


def resolve_style(style, style_url, key):
    for property_name in ('sprite', 'glyphs'):
        val = style.get(property_name)
        if isinstance(val, str) and not val.startswith(('data:', 'mapbox://')):
            style[property_name] = add_key(urljoin(style_url, val), key)
    for source in style.get('sources', {}).values():
        if isinstance(source.get('url'), str):
            source['url'] = add_key(urljoin(style_url, source['url']), key)
        if isinstance(source.get('tiles'), list):
            source['tiles'] = [add_key(urljoin(style_url, u), key) if isinstance(u, str)
                               and not u.startswith(('data:', 'mapbox://')) else u
                               for u in source['tiles']]
    return style


def apply_palette(style, palette, night=False):
    count = 0
    for layer in style['layers']:
        lid = layer.get('id', '')
        if lid in palette:
            field, value = palette[lid]
            layer.setdefault('paint', {})[field] = value
            count += 1
        if night and layer.get('type') == 'symbol' and 'text-field' in layer.get('layout', {}):
            paint = layer.setdefault('paint', {})
            paint['text-color'] = '#F2F2E9'
            paint['text-halo-color'] = '#17222C'
            paint['text-halo-width'] = 1.4
    return count


def add_traffic(style, key, minimum):
    if minimum is None:
        return
    # Source and layer names must match Pure Maps' earlier experimental layouts.
    style['sources']['here-live-traffic'] = {
        'type': 'raster',
        'tiles': [TRAFFIC_URL.format(key=key, level=minimum)],
        'tileSize': 512, 'attribution': '© HERE',
    }
    traffic_layer = {'id': 'here-live-traffic-overlay', 'type': 'raster',
                     'source': 'here-live-traffic',
                     'paint': {'raster-opacity': 0.85}}
    i = next((i for i, layer in enumerate(style['layers'])
              if layer.get('type') == 'symbol'), len(style['layers']))
    style['layers'].insert(i, traffic_layer)


def create_map(style, provider, light):
    return {
        'attribution': {'© HERE': 'https://legal.here.com'},
        'format': 'mapbox-gl', 'name': provider + (' (Night)' if light == 'night' else ' (Day)'),
        'provider': provider, 'profiles': ['HERE', 'online', 'mixed'],
        'light': light, 'type': 'default', 'style_json': style,
        'style_gui': {'route': '#E300FF', 'routeOpacity': 0.98,
                      **({'fg': 'white', 'itemFg': 'white', 'itemBg': '#26333F'}
                         if light == 'night' else {})},
    }


def reduce_night_road_widths(style):
    """Match tested v1.2 night styling without changing the day map."""
    factors = {'road-highway': 0.58,
               'road-highway-link': 0.70,
               'road-trunk': 0.70}
    def scale(value, factor):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return round(value * factor, 4)
        if isinstance(value, dict) and isinstance(value.get('stops'), list):
            result = copy.deepcopy(value)
            for stop in result['stops']:
                if not isinstance(stop, list) or len(stop) != 2 or not isinstance(stop[1], (int, float)):
                    raise ValueError('Unsupported width stop expression')
                stop[1] = round(stop[1] * factor, 4)
            return result
        if isinstance(value, list):
            return ['*', value, factor]
        raise ValueError('Unsupported HERE road-width syntax')
    for layer in style['layers']:
        factor = factors.get(layer.get('id'))
        if not factor or layer.get('type') != 'line':
            continue
        paint = layer.get('paint', {})
        if 'line-width' in paint:
            paint['line-width'] = scale(paint['line-width'], factor)


def without_traffic(spec):
    """Remove the traffic raster source and layers, without changing routing."""
    item = copy.deepcopy(spec)
    style = item['style_json']
    style['layers'] = [x for x in style['layers']
                       if x.get('source') != 'here-live-traffic']
    style['sources'].pop('here-live-traffic', None)
    return item



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



PROVIDER = 'HERE Hybrid'
PREFIX = 'here_hybrid_v13_'
MANIFEST = 'here_hybrid_v13_manifest.json'
PROFILES = ['HERE', 'online', 'mixed']
BUILTINS = [Path('/usr/share/harbour-pure-maps/maps'),
            Path('/usr/share/pure-maps/maps'),
            Path('/usr/share/harbour-pure-maps/poor/maps')]
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
    return None, None

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

def fresh_vectors():
    """Fetch once and generate base day/night styles without extra map providers."""
    key, _ = read_key()
    request_url = BASE_URL + '?apikey=' + quote(key, safe='')
    with urlopen(Request(request_url, headers={'User-Agent': 'PureMaps-HERE-Hybrid/1.3'}), timeout=25) as response:
        if response.status != 200:
            raise RuntimeError('HERE vector style download failed')
        final_url = response.geturl()
        base = json.load(response)
    if not isinstance(base, dict) or not isinstance(base.get('sources'), dict) or not isinstance(base.get('layers'), list):
        raise RuntimeError('Unexpected HERE vector style')
    resolve_style(base, final_url, key)
    variants = {}
    for light, colors in (('day', DAY), ('night', NIGHT)):
        style = copy.deepcopy(base)
        count = apply_palette(style, colors, night=light == 'night')
        if count < 10:
            raise RuntimeError('Unexpected HERE layer names: refusing partial style')
        if light == 'night':
            reduce_night_road_widths(style)
        add_traffic(style, key, 'free')
        traffic_map = create_map(style, PROVIDER, light)
        traffic_map['type'] = 'traffic'
        variants[(light, True)] = traffic_map
        variants[(light, False)] = without_traffic(traffic_map)
    return variants


def vector(light, mode, traffic, fallback):
    data, source_name = choose_vector(light, traffic)
    if data is None:
        data = fallback[(light, traffic)]
        source_name = 'fresh HERE vector style'
    data = copy.deepcopy(data)
    data.update(provider=PROVIDER, name='HERE vector ' + mode + ' (' + light + ')',
                profiles=PROFILES, light=light, type=mode)
    if light == 'day':
        count = recolour_day(data['style_json'])
        print('Prepared daytime', mode, 'with', count, 'recoloured layers from', source_name)
    else:
        print('Preserved night styling from', source_name)
    return data

def outputs(traffic=True):
    fallback = {}
    if any(choose_vector(light, traffic)[0] is None for light in ("day", "night")):
        fallback = fresh_vectors()
    result = {}
    for light in ('day', 'night'):
        result[PREFIX + 'raster_' + light + '.json'] = raster(light)
        for mode in ('guidance', 'preview'):
            result[PREFIX + 'vector_' + mode + '_' + light + '.json'] = vector(light, mode, traffic, fallback)
    return result


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_files():
    if MAPS.is_symlink():
        raise RuntimeError('Map directory is a symlink; refusing')
    names = [PREFIX + mode + '_' + light + '.json'
             for light in ('day', 'night')
             for mode in ('raster', 'vector_guidance', 'vector_preview')]
    return names


def remove(dry=False):
    manifest_path = MAPS / MANIFEST
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError('No v1.3 ownership manifest. No files removed.')
    doc = read_json(manifest_path)
    entries = doc.get('files')
    if doc.get('provider') != PROVIDER or not isinstance(entries, dict) or set(entries) != set(safe_files()):
        raise RuntimeError('Unrecognised v1.3 manifest. No files removed.')
    for name, expected in entries.items():
        path = MAPS / name
        if not path.is_file() or path.is_symlink() or sha(path.read_bytes()) != expected:
            raise RuntimeError('File changed or missing: ' + name + '. No files removed.')
        item = read_json(path)
        if item.get('provider') != PROVIDER:
            raise RuntimeError('Unexpected provider in ' + name + '. No files removed.')
    if dry:
        print('Safe to remove', len(entries), 'owned v1.3 map files. No changes made.')
        return
    for name in entries:
        (MAPS / name).unlink()
        print('Removed:', name)
    manifest_path.unlink()
    print('Removed only verified hybrid files; original maps and QML unchanged.')


def install(dry=False):
    expected = safe_files()
    if (MAPS / MANIFEST).exists() or any((MAPS / name).exists() for name in expected):
        raise RuntimeError('Hybrid files already exist. Nothing changed. Do not reinstall over a working setup.')
    prepared = outputs()
    if set(prepared) != set(expected):
        raise RuntimeError('Unexpected generated file list; aborting')
    print('Validated', len(prepared), 'HERE Hybrid map definitions.')
    if dry:
        print('Dry run: no files changed.')
        return
    MAPS.mkdir(parents=True, exist_ok=True)
    if MAPS.is_symlink():
        raise RuntimeError('Map directory is a symlink; refusing')
    made = []
    manifest_path = MAPS / MANIFEST
    digest = {}
    try:
        for name, item in prepared.items():
            data = (json.dumps(item, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            path = MAPS / name
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            made.append(path)
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            digest[name] = sha(data)
        data = (json.dumps({'provider': PROVIDER, 'files': digest}, indent=2) + '\n').encode('utf-8')
        fd = os.open(str(manifest_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        made.append(manifest_path)
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
    except BaseException:
        for path in made:
            path.unlink(missing_ok=True)
        raise
    print('Installed HERE Hybrid. Select it under Settings > Maps.')
    print('Enable automatic Switch map modes and sunrise/sunset lighting.')
    print('Run fix_auto_switch.py while Pure Maps is closed to clear old manual type.')
    print('Private generated JSON may contain your HERE key: do not publish.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--remove', action='store_true', help='Remove only unchanged files recorded in this installer manifest')
    args = p.parse_args()
    if args.remove:
        remove(args.dry_run)
    else:
        install(args.dry_run)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        message = re.sub(r'(?i)(apiKey=)[^&\s]+', r'\1[redacted]', str(exc))
        print('ERROR:', type(exc).__name__, message, file=sys.stderr)
        sys.exit(1)
