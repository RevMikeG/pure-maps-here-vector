# HERE Vector Maps for Pure Maps on Sailfish OS

**v1.2** · Unofficial community customisation for [Pure Maps](https://github.com/rinigus/pure-maps), developed and tested on a Jolla Phone running **Pure Maps 3.5.1**.

Adds HERE vector maps with upright labels, colourful day/night rendering, optional traffic-flow overlays and improved navigation visibility. **HERE congestion-aware routing still comes from the HERE routing profile**, not from the map overlay.

## What's new in v1.2

- **Layers → Type → Traffic / Default** toggles coloured traffic display on/off within the same provider, for **both day and night**.
- **Night road-width improvement:** motorways 42% narrower; motorway links and trunk roads 30% narrower, to keep the navigation line visible.
- **More distinctive night palette:** muted grey A-roads and clear blue motorways.
- **11-unit magenta navigation route** (instead of the old 7-unit width), with a stronger blue-and-white GPS position marker above the line.
- **Day/night switch** still works automatically at sunrise and sunset or manually from Layers.
- Safeguards around user API keys and existing installations.

## Requirements

- Jolla / Sailfish OS, Pure Maps with Mapbox GL vector rendering (tested on version 3.5.1).
- A valid HERE API key already available in Pure Maps, with relevant HERE vector/traffic service access and accepted HERE terms.
- Internet access for downloading vector tiles and real-time traffic.
- Developer Mode / `devel-su` **only** for the optional navigation QML patch.

## For a new installation

1. Download `install.py` onto your Sailfish phone.
2. In Terminal run:

   ```sh
   python3 ~/Downloads/install.py
   ```

   If the browser saved it elsewhere, move the file to `~/Downloads/` or adjust the command to match its location.
3. Fully close and reopen Pure Maps, select the **HERE** profile, then choose **HERE Vector Traffic** from Settings → Maps.
4. Under **Preferences → Maps**, turn **Switch map modes** **off** for predictable manual traffic display selection, and choose **Day/night mode → Sunrise and sunset**.
5. In the **Layers** menu, select **Traffic** to display traffic colours or **Default** to hide them. Day/night continues to work independently.
6. To keep routes congestion-aware, enable **Traffic** in HERE route options and configure traffic updates during navigation, where available. The visual overlay toggle does not disable traffic-aware route calculations.

The public installer creates **eight private map definitions** (two HERE Vector Colour, four HERE Vector Traffic [two overlay-on, two overlay-off], and two HERE Vector Queues).

### Optional: navigation display patch

The map-style installer works without root. The **optional** `navigation_patch.py` changes installed QML to draw an **11-unit magenta navigation route**, a slimmer casing and a **white/blue GPS marker above it**. It changes `/usr/share/harbour-pure-maps/qml/Map.qml` and `PositionMarker.qml` and backs up both before changes.

Completely close Pure Maps, then:

```sh
devel-su
python3 /home/defaultuser/Downloads/navigation_patch.py install
exit
```

Check without modifying files:

```sh
python3 ~/Downloads/navigation_patch.py status
```

To restore **only if this v1.2 script created the backup**:

```sh
devel-su
python3 /home/defaultuser/Downloads/navigation_patch.py restore
exit
```

If you used older experimental navigation patches, their old backups remain separate. **Do not blindly restore an older backup over a newer patch.** Application package upgrades may overwrite QML changes. The patch refuses unfamiliar source layouts instead of forcing an edit.

## Privacy and licence

Generated local map definitions can contain your HERE API key inside authenticated tile, sprite and glyph URLs. 

## Troubleshooting

- **Map missing:** check `~/.local/share/io.github.rinigus/PureMaps/maps/` and restart Pure Maps completely.
- **401 authentication error:** check the HERE key, licence acceptance, and service entitlement in Pure Maps.
- **Traffic switch doesn't respond:** ensure `HERE Vector Traffic` is the selected map provider, disable *Switch map modes*, and use **Layers → Type → Traffic / Default**.
- **Dark/bright styles don't switch:** choose **Day/night mode → Sunrise and sunset** and allow GPS, or set Manual and use sun/moon.
- **Navigation patch rejected:** the QML structure may differ, or earlier patches/backups may be present. Do not force it. Report the exact error.
- **After an upgrade:** verify whether Pure Maps package updates restored the original QML files.

## History

- `v0.1-alpha` Basic HERE vector style.
- `v1.0` Day/night styling and live traffic overlays.
- `v1.1` Navigation visibility and GPS layer ordering.
- `v1.2` Traffic display toggle, 11-unit route and night road visibility refinements.

See [CHANGELOG.md](CHANGELOG.md). This project is unofficial, independent of HERE and Pure Maps. Test navigation while stationary; never adjust phone settings while driving.
