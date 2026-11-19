# HERE Hybrid Maps for Pure Maps v1.3

A cleaned-up public release of our Jolla/Sailfish OS HERE map customisation.

**Browsing:** HERE raster map with traffic, day or night. **Route preview/navigation:** automatically switch to HERE vector maps with upright street names, a daytime palette based on the familiar HERE raster appearance, and the previously tested high-contrast night styling. End navigation to return automatically to raster.

The package now has a **single standalone hybrid installer** (`install.py`), a separate automatic mode-selection preference fix (`fix_auto_switch.py`) and an **optional** navigation QML patch (`navigation_patch.py`) for the 11-unit magenta route and GPS marker. Fresh installs create only the six definitions for **HERE Hybrid**, not an extra v1.2.1 provider. Safe removal verifies an installer manifest and each file's checksum. Existing compatible vector definitions are not modified.

**Installation:** See `README.md` for setup, prerequisites, backup and rollback instructions. This release needs an existing HERE API key and internet access. Private generated JSON may contain your key and must not be uploaded.

**For users of the previous experiment:** do not reinstall over a working setup. The installer deliberately refuses to replace existing experimental v1.3 files. Your own `HERE Hybrid Experimental` can continue working as it is.

Tested by syntax checking and simulated installation/removal, including fresh API-style generation and safeguards against deleting edited files. The author's earlier customised Jolla setup has been road-tested; this *clean* installer has not yet been independently verified on a fresh device.

Unofficial community project, unaffiliated with HERE or the Pure Maps project. Changes to navigation settings should be tested while stationary.
