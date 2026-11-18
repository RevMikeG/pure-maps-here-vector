#!/usr/bin/env python3
"""Optional Pure Maps 3.5.1 Sailfish navigation visibility patch, v1.2.

Run under devel-su: python3 navigation_patch.py install|status|restore
No network access, credentials, or map style modifications.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

QML = Path('/usr/share/harbour-pure-maps/qml')
FILES = ('Map.qml', 'PositionMarker.qml')
BACKUP = QML / '.here-vector-navigation-v1.2-backup'

ROUTE_WIDTHS = (
    'map.setPaintProperty(map.layers.route, "line-width", ',
    'map.setPaintProperty(map.layers.routeOutline, "line-gap-width", ',
)
INIT_MAP_OLD = '''        map.initIcons();
        map.initLayers();
        map.configureLayers();
        positionMarker.initIcons();
        positionMarker.configureLayers();'''
INIT_MAP_NEW = '''        map.initIcons();
        map.initLayers();
        map.configureLayers();
        positionMarker.initIcons();
        // Create position layers AFTER navigation layers so GPS is on top.
        positionMarker.initLayers();
        positionMarker.configureLayers();'''
INIT_POSITION_OLD = '''    Component.onCompleted: {
        marker.initIcons();
        marker.initLayers();
        marker.configureLayers();
    }'''
INIT_POSITION_NEW = '''    // Layers are initialized by Map.setStyleAdditions(), after route layers.
'''
HALO_LAYER_OLD = '''        map.addLayer(marker.layers.still, {"type": "symbol", "source": marker.source});'''
HALO_LAYER_NEW = '''        // White and blue GPS position halo visible over the magenta route.
        map.addLayer("pure-position-navigation-halo",
                     {"type": "circle", "source": marker.source});
        map.addLayer(marker.layers.still, {"type": "symbol", "source": marker.source});'''
UPDATE_OLD = '''        updateDirection();
        updateUncertainty();
        updateVisibility();'''
UPDATE_NEW = '''        map.setPaintProperty("pure-position-navigation-halo", "circle-radius",
                             17 * map.mapToQtPixelRatio / map.devicePixelRatio);
        map.setPaintProperty("pure-position-navigation-halo", "circle-color", "#FFFFFF");
        map.setPaintProperty("pure-position-navigation-halo", "circle-stroke-color", "#075BFF");
        map.setPaintProperty("pure-position-navigation-halo", "circle-stroke-width",
                             5 * map.mapToQtPixelRatio / map.devicePixelRatio);
        map.setPaintProperty("pure-position-navigation-halo", "circle-pitch-alignment", "viewport");
        map.setPaintProperty("pure-position-navigation-halo", "circle-opacity", 1);
        map.setPaintProperty("pure-position-navigation-halo", "circle-stroke-opacity", 1);

        updateDirection();
        updateUncertainty();
        updateVisibility();'''


def replace_once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 matching fragment, found {count}; no files changed')
    return text.replace(old, new, 1)


def apply_patch(data):
    m = data['Map.qml']
    p = data['PositionMarker.qml']
    # The tested final setting is 11 map units (route and casing gap).
    # Accept stock and earlier experimental 7/9/16-unit values.
    for prefix in ROUTE_WIDTHS:
        desired = prefix + '11 * map.mapToQtPixelRatio);'
        if desired in m:
            continue
        options = [prefix + f'{w} * map.mapToQtPixelRatio);' for w in (7, 9, 16)]
        matches = [old for old in options if old in m]
        if len(matches) != 1:
            raise RuntimeError('Unexpected route width in installed Map.qml; nothing changed')
        m = replace_once(m, matches[0], desired, 'route width')
    m = replace_once(m,
        'map.setPaintProperty(map.layers.routeOutline, "line-width", 4 * map.mapToQtPixelRatio);',
        'map.setPaintProperty(map.layers.routeOutline, "line-width", 2.5 * map.mapToQtPixelRatio);',
        'route casing')
    # Only add the halo to stock PositionMarker.qml. The previous 1.1
    # experimental patch already adds it, so that case is kept unchanged.
    if '"pure-position-navigation-halo"' not in p:
        p = replace_once(p, HALO_LAYER_OLD, HALO_LAYER_NEW, 'GPS halo layer')
        p = replace_once(p, UPDATE_OLD, UPDATE_NEW, 'GPS halo colour')
    elif '"circle-color", "#FFFFFF"' not in p:
        raise RuntimeError('GPS halo exists but does not match the known patch; no files changed')
    # Ensure position icon is created last. This was tested on a Jolla.
    if 'positionMarker.initLayers();' not in m:
        m = replace_once(m, INIT_MAP_OLD, INIT_MAP_NEW, 'GPS layer order')
    if INIT_POSITION_OLD in p:
        p = replace_once(p, INIT_POSITION_OLD, INIT_POSITION_NEW, 'GPS initialization')
    elif 'Component.onCompleted:' in p or 'marker.initLayers();' in p:
        raise RuntimeError('GPS initialization differs from the known patch; no files changed')
    return {'Map.qml': m, 'PositionMarker.qml': p}


def atomic_write(path, content):
    st = path.stat()
    fd, tmp = tempfile.mkstemp(prefix='.here-v12-', dir=str(QML))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, st.st_mode)
        os.chown(tmp, st.st_uid, st.st_gid)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def original_state():
    return {name: (QML / name).read_text(encoding='utf-8') for name in FILES}


def install():
    originals = original_state()
    new = apply_patch(originals)
    altered = [name for name in FILES if originals[name] != new[name]]
    if not altered:
        print('Already matches v1.2 route-width and GPS-marker setup. Nothing changed.')
        return
    if BACKUP.exists():
        raise RuntimeError('v1.2 backup already exists; refusing to overwrite')
    BACKUP.mkdir(mode=0o700)
    try:
        for name in FILES:
            shutil.copy2(QML / name, BACKUP / name)
        for name in altered:
            atomic_write(QML / name, new[name])
    except BaseException:
        for name in FILES:
            b = BACKUP / name
            if b.exists():
                shutil.copy2(b, QML / name)
        raise
    print('Installed v1.2 navigation patch. Changed:', ', '.join(altered))
    print('Backup:', BACKUP)
    print('Close Pure Maps fully and reopen. Test while stationary.')


def status():
    current = original_state()
    try:
        proposed = apply_patch(current)
        print('v1.2 visibility changes present' if proposed == current else
              'v1.2 visibility changes not fully present')
    except RuntimeError as e:
        print('Nonstandard QML installation:', e)
    print('v1.2 backup:', 'present' if BACKUP.exists() else 'absent')


def restore():
    if not BACKUP.is_dir() or any(not (BACKUP / n).is_file() for n in FILES):
        raise RuntimeError('Complete v1.2 backup unavailable; nothing restored')
    for name in FILES:
        shutil.copy2(BACKUP / name, QML / name)
    print('Restored the QML files from just before v1.2 installation.')
    print('Close Pure Maps fully and reopen.')


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('install', 'restore', 'status'):
        raise RuntimeError('Usage: python3 navigation_patch.py install|status|restore')
    if os.geteuid() != 0 and sys.argv[1] != 'status':
        raise RuntimeError('Installation/restoration requires devel-su (root)')
    {'install': install, 'status': status, 'restore': restore}[sys.argv[1]]()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('ERROR:', str(e), file=sys.stderr)
        sys.exit(1)
