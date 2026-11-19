# Changelog

## v1.3 — 19 November 2026

* Added `HERE Hybrid Experimental`: HERE raster traffic map for browsing and custom vector maps for Preview/Guidance, with automatic return to raster.
* Matched daytime vector colours to the HERE raster reference screenshot while preserving night navigation styling.
* Added a backed-up `fix_auto_switch.py` to clear persistent manual Guidance selection after reboot.
* Made hybrid installation detect both the older custom Jolla map filenames and published v1.2.1 definitions.
* Preserved original map providers, HERE routing and optional navigation QML patch.
* Documented that traffic on/off is not independently selectable within the hybrid automatic mode.



## v1.2.1 — 19 November 2026

* Simplified fresh installations to **one HERE Vector Traffic provider**, with four day/night and traffic-on/off styles controlled from Layers.
* Included `tidy_here_maps.py` for reversible removal of redundant custom HERE Vector Colour and Queues providers from existing installations.
* Standardised installation and restore commands on Sailfish OS `~/Downloads/` (no Android storage references).
* Retained v1.2's tested night-road widths, 11-unit navigation route and GPS position marker without change.



## v1.2 — 18 November 2026

* Added traffic **on/off** via existing **Layers → Type** selector, keeping the HERE routing profile intact.
* Created paired day/night map variants within the same HERE Vector Traffic provider.
* Reduced overly wide night motorways (42%) and links/trunk roads (30%).
* Refined night A-road colours for better contrast with the navigation route.
* Set the navigation QML patch to the driving-tested **11-unit magenta line** with matching casing gap.
* Retained the white-and-blue GPS marker above navigation layers.
* Updated installation, rollback and credential-privacy instructions.

## v0.1-alpha — 17 November 2026

* Initial HERE vector-map definition for Pure Maps on Sailfish OS.

