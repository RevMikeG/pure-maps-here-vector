# HERE Vector Maps v1.2 — Traffic control and improved night navigation

This community release for **Pure Maps on Sailfish OS** consolidates the configuration tested on a Jolla Phone with Pure Maps 3.5.1.

### Highlights

* Toggle visual HERE traffic colours through **Layers → Type → Traffic / Default**.
* Keep congestion-aware HERE **routing** independently of the traffic display toggle.
* Automatic sunrise/sunset switching between bright day maps and high-contrast night maps.
* Narrower night motorways and muted A-road colours, making navigation clearer.
* Driving-tested **11-unit magenta route**, with a highly visible blue-and-white GPS position marker.
* Reproducible installer, optional QML patch, rollback precautions and credential-safe public files.

### Installation

See [README.md](README.md) for installing `install.py` (no root) and optional `navigation\_patch.py` (requires `devel-su`). Existing users with the completed experimental setup need not reinstall.

### Important notes

Requires a valid HERE service key in Pure Maps and appropriate HERE entitlements. The generated maps contain authenticated HERE URLs. The consolidated v1.2 installers are compatibility-checked but have not been tested on a fresh phone; the individual changes were tested on the project author's Jolla.

Unofficial community project, not an official HERE or Pure Maps release.

