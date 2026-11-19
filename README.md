# HERE Hybrid Maps for Pure Maps on Sailfish OS

**v1.3 (clean release)** · Unofficial community project · Tested on a customised Jolla / Pure Maps 3.5.1 setup.

Automatically use HERE **raster maps with traffic when browsing**, then switch to customised HERE **vector maps for route preview and navigation**, and return to raster when navigation ends. The vector map keeps street labels upright when rotating. Daytime vector colours approximate the HERE raster palette; night styling retains the tested high-contrast appearance.

| Mode | Map style |
| --- | --- |
| Browsing | HERE raster with traffic; automatic day/night |
| Route preview | HERE vector, raster-inspired daytime palette |
| Navigation / following | HERE vector, high-contrast day/night |
| Finish navigation | Return to raster automatically |

This uses Pure Maps' existing map-mode switching. **Do not manually leave Guidance selected in Layers → Type:** that overrides the automatic behaviour. HERE routing can still account for traffic independently of the displayed traffic colours. In this hybrid provider, traffic overlay on/off is **not** an independent Layers toggle. The original `HERE Vector Traffic` provider (if present) remains available for that feature.

## Requirements

- Sailfish OS / Jolla, Python 3 and a Pure Maps version with HERE and Mapbox GL map support (developed with Pure Maps 3.5.1).
- HERE API key available in Pure Maps and access to HERE raster, vector and traffic APIs.
- Network access. This is **not an offline map download**.
- Install scripts run as the regular Sailfish user, **not root**. Only the optional navigation QML patch requires `devel-su`.

## Installation (fresh or existing vector setup)

1. Extract the release files into `~/Downloads/` on your Jolla. If your browser saved them somewhere else, substitute that actual directory.
2. **Completely close Pure Maps.** In Terminal, run:

   ```sh
   python3 ~/Downloads/install.py --dry-run
   python3 ~/Downloads/install.py
   python3 ~/Downloads/fix_auto_switch.py
   ```

   The installer first reuses compatible, existing `HERE Vector Traffic` day/night styles when available. **If no suitable source is installed, it downloads a HERE vector style and creates the hybrid provider directly.** It does *not* install a second, redundant v1.2.1 map provider. `--dry-run` may download the base style for validation, but changes no local map files.

3. Open Pure Maps. Select the **HERE** profile and **Settings → Maps → HERE Hybrid**.
4. Under **Preferences → Maps**, enable **Switch map modes** and set **Day/night mode → Sunrise and sunset**.
5. Confirm that no manual **Guidance** (or other Type) selection remains active in Layers. Test route start/end while stationary; restart Pure Maps and test again.

Generated private map definitions go to:

`~/.local/share/io.github.rinigus/PureMaps/maps/`

### Already running the previous v1.3 experiment?

**Don't run the new installer over the working experiment.** It deliberately refuses to overwrite existing `here_hybrid_v13_*` files, even those created by earlier tests. Your tested `HERE Hybrid Experimental` provider can be left in place. The clean package is for new installations, or a deliberate migration with backups; there is no automatic migration that could replace your tested styles.

The clean release's provider name is **HERE Hybrid**. Your existing experimental provider retains its current name unless you explicitly migrate it. You need not alter your own working installation just to publish this release.

## Optional navigation QML patch

`navigation_patch.py` is a **separate, optional** patch for supported Pure Maps 3.5.1 application QML. It applies the 11-unit magenta route styling and improves the blue/white GPS position marker's visibility above the route. It is **not** automatically run by `install.py`. Package upgrades can undo QML changes. The patch will refuse unfamiliar or previously patched QML structures; do not force it.

After fully closing Pure Maps:

```sh
devel-su
python3 /home/defaultuser/Downloads/navigation_patch.py install
exit
```

To inspect patch status (normal user):

```sh
python3 ~/Downloads/navigation_patch.py status
```

To restore **only** the backup created by this patch:

```sh
devel-su
python3 /home/defaultuser/Downloads/navigation_patch.py restore
exit
```

**Do not reapply the optional patch to a phone with the tested GPS and route adjustments already installed.**

## Safe removal

1. In Pure Maps select another map provider, then fully close Pure Maps.
2. Check removal eligibility, then remove the six installed hybrid map definitions:

   ```sh
   python3 ~/Downloads/install.py --remove --dry-run
   python3 ~/Downloads/install.py --remove
   ```

Removal requires an installer-generated manifest and checks each file's SHA-256 and provider metadata before deleting anything. It **refuses** removal if a file is changed, missing or doesn't belong to this installer. It will not remove older experimental v1.3 files without its manifest, nor touch original vector definitions or application QML. It does not undo the saved map-mode preference adjustment.

`fix_auto_switch.py` makes a separate backup of `pure-maps.json` called `pure-maps.before-v13-auto-switch.json` beside the configuration. Restore that whole backup only deliberately, with Pure Maps closed, since it may also revert unrelated preference changes made since it was saved.

## Files in this release

- `install.py` - single standalone hybrid map installer, with verified removal and dry-run.
- `fix_auto_switch.py` - saves automatic map-mode settings, with configuration backup.
- `navigation_patch.py` - optional, reversible QML visibility enhancements.
- `README.md`, `CHANGELOG.md`, `RELEASE_NOTES.md`, `.gitignore` - public project documentation.

**No** separate colour-testing tools, redundant v1.2.1 installer, experimental inspection scripts or generated style JSON files are required.

## Limitations

Daytime vector colours are approximated from the raster reference, not exact pixel equivalents. A fresh installation is simulated and syntax-tested but has not yet been road-tested on a second Jolla device. The hybrid provider uses `Default` for raster, and `Preview`/`Guidance` for vector, so the manual Layers traffic toggle from v1.2.1 is not independently available. This is a community modification, unaffiliated with HERE or the Pure Maps maintainers. Make navigation-setting changes only while stationary.
