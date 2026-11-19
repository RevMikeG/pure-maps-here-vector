# HERE Hybrid Maps v1.3

**Raster browsing, vector navigation.** This release adds automatic map-format switching to the HERE Vector customisation for Pure Maps on Sailfish OS.

## Highlights

* **HERE raster map with traffic** for normal browsing, with automatic day/night selection.
* **Automatic switch to HERE vector** for guidance and route previews, and back to raster after navigation.
* **New daytime vector palette** modelled on the appearance of the HERE raster map: pale land, mint greens, blue-grey roads and light-blue water.
* **Retains the tested night guidance map**, narrower major roads, 11-unit magenta route and improved GPS marker (the latter two via the existing optional navigation QML patch).
* **Startup automatic-mode fix** clears the saved manual `basemap_type` and enables `basemap_auto_mode`, preventing the manual Guidance double-tap after restarting.
* Supports both published v1.2.1 files and the older custom Jolla map filenames; the separate hybrid provider does not overwrite either source.

## Install

See the full `README.md`. On a fresh setup with a working HERE API key:

```sh
python3 ~/Downloads/install.py
python3 ~/Downloads/install_hybrid.py --dry-run
python3 ~/Downloads/install_hybrid.py
# With Pure Maps fully closed:
python3 ~/Downloads/fix_auto_switch.py
```

Select **HERE Hybrid Experimental**, enable **Switch map modes**, and keep automatic day/night selection enabled.

**Existing author-tested hybrid setups require no reinstallation.**

**Known limitation:** Pure Maps uses Layers → Type for automatic map modes, so the separate traffic on/off selector from v1.2.1 is not independent in the hybrid provider. Choose the `HERE Vector Traffic` provider to retain the original manual traffic toggle.

Unofficial community project; tested on Pure Maps 3.5.1 on Sailfish OS. Do not adjust settings while driving.

