#!/usr/bin/env python3
"""HERE Vector for Pure Maps, community release v1.2.1.

Installs self-contained day/night MapLibre map styles with optional HERE live
traffic raster overlays. Runs on the Jolla/Sailfish device, reuses the HERE API
key already configured in Pure Maps, and NEVER prints the key.

Generated map JSON files contain authenticated URLs. DO NOT publish those files.
"""
import ast
import copy
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
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
OPTIONS = [
    # Only one provider is needed; Layers controls day/night and traffic.
    ('traffic', 'HERE Vector Traffic', 'free'),
]


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


def main():
    key, source = read_key()
    if re.search(r'[\s&#?]', key):
        raise RuntimeError('HERE key contains unexpected characters')
    print('Using', source, '(key is not shown).')
    request_url = BASE_URL + '?apikey=' + key
    req = Request(request_url, headers={'User-Agent': 'PureMaps-HERE-Vector/1.2.1'})
    with urlopen(req, timeout=35) as response:
        base = json.load(response)
        final_url = response.geturl()
    if not isinstance(base, dict) or not isinstance(base.get('sources'), dict) or not isinstance(base.get('layers'), list):
        raise RuntimeError('HERE did not return an expected MapLibre vector style')
    resolve_style(base, final_url, key)
    MAPS.mkdir(parents=True, exist_ok=True)
    os.chmod(MAPS, 0o700)

    # Prepare all outputs first; refuse to replace existing generated styles.
    outputs = []
    for slug, provider, traffic in OPTIONS:
        for light, palette in [('day', DAY), ('night', NIGHT)]:
            style = copy.deepcopy(base)
            count = apply_palette(style, palette, night=(light == 'night'))
            if count < 10:
                raise RuntimeError('HERE layer names differ from the tested style; '
                                   'refusing to install incomplete colour scheme')
            if light == 'night':
                reduce_night_road_widths(style)
            add_traffic(style, key, traffic)
            item = create_map(style, provider, light)
            if slug == 'traffic':
                # Layers > Type becomes Traffic ON / Default OFF, automatically
                # respecting day/night mode because the provider is the same.
                item['type'] = 'traffic'
                off = without_traffic(item)
                off['type'] = 'default'
                off['name'] += ' (no traffic)'
                outputs.append((f'here_v12_traffic_{light}.json', item))
                outputs.append((f'here_v12_traffic_off_{light}.json', off))
            else:
                outputs.append((f'here_v12_{slug}_{light}.json', item))
    collisions = [name for name, _ in outputs if (MAPS / name).exists()]
    if collisions:
        print('HERE Vector Traffic styles already exist; refusing to overwrite:', ', '.join(collisions))
        print('Existing maps and keys unchanged.')
        return
    created = []
    try:
        for filename, item in outputs:
            dest = MAPS / filename
            fd = os.open(str(dest), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(item, f, ensure_ascii=False, indent=2)
                    f.write('\n')
            except BaseException:
                dest.unlink(missing_ok=True)
                raise
            created.append(dest)
            print('Created:', filename)
    except BaseException:
        for dest in created:
            dest.unlink(missing_ok=True)
        raise
    print('Installed', len(outputs), 'private v1.2.1 map definitions.')
    print('Restart Pure Maps; select HERE profile and HERE Vector Traffic.')
    print('For manual traffic overlay control, disable Preferences > Maps > Switch map modes.')
    print('Layers > Type: Traffic = visible, Default = hidden.')
    print('Keep Day/night mode > Sunrise and sunset for automatic switching.')
    print('HERE congestion-aware ROUTING remains independent of overlay selection.')
    print('CONFIDENTIAL: generated JSON files include authenticated HERE URLs; never publish them.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        msg = str(exc)
        if 'key' in locals() and isinstance(locals().get('key'), str):
            msg = msg.replace(locals()['key'], '[redacted]')
        msg = re.sub(r'(?i)(apiKey=)[^&\s]+', r'\1[redacted]', msg)
        print('ERROR:', type(exc).__name__, msg, file=sys.stderr)
        sys.exit(1)
