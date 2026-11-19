# HERE Vector Maps v1.2.1 — Cleaner map selection

This maintenance release builds on v1.2 for Pure Maps on Sailfish OS (tested by the author on a Jolla Phone with Pure Maps 3.5.1).

### Changes

* Fresh installations create just one custom **HERE Vector Traffic** provider in **Settings → Maps**.
* The existing **Layers → Type → Default / Traffic** selection controls traffic overlay visibility; **Layers → Light** controls day and night when using manual map lighting.
* Added the reversible `tidy\_here\_maps.py` for installations with extra HERE Vector Colour/Queues provider entries.
* No changes to the driving-tested magenta route, GPS position marker, traffic-aware HERE routing or night palette.

### New installation

Copy `install.py` to your Sailfish OS Downloads folder and run:

```sh
python3 \~/Downloads/install.py
```

See [README.md](README.md) for the optional navigation QML patch and settings.

### Already using v1.2?

You do **not** need to reinstall your working maps. If Settings → Maps still shows extra custom HERE Vector Colour or Queues providers, run the cleanup script with Pure Maps closed:

```sh
python3 \~/Downloads/tidy\_here\_maps.py
```

To restore those archived entries:

```sh
python3 \~/Downloads/tidy\_here\_maps.py --restore
```

This is an unofficial community project. The consolidated fresh-install script has not yet been tested on a new device; the v1.2 features were tested on the author's Jolla.

