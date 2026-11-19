# Changelog

## v1.3 (clean release)

- Add one **HERE Hybrid** provider: HERE raster with traffic during browsing; customised HERE vector during route previews, navigation and follow mode.
- Retain automatic day/night switching, cooler raster-inspired daytime vector palette, and road-tested narrower night roads and high-contrast styling.
- Use one hybrid map installer (`install.py`) for both fresh and existing installations. Generate six hybrid definitions directly, without installing a redundant vector provider on new devices.
- Reuse earlier compatible vector style definitions without modifying them.
- Include `fix_auto_switch.py` to clear saved manual Type selections after a full application exit; back up preferences before writing.
- Add manifest-based removal that refuses to delete modified or unowned files.
- Retain optional, reversible 11-unit route and GPS marker QML patch.
- Remove old test utilities, duplicate setup scripts and `Experimental` from the new provider's display name. Preserve the existing working experimental provider on users' devices.
- No private API credentials or generated map definitions distributed.

## v1.2.1

- Simplify map selection and use standard Sailfish OS Downloads paths in the public instructions.

## v1.2

- Toggle traffic-overlay display in the vector-only provider; adjust night road widths and navigation route prominence.

## v1.1

- Improve route visibility and GPS marker layering.

## v1.0

- Custom HERE vector daytime/night-time styling and traffic overlays.

## v0.1-alpha

- Initial HERE vector map definition for Pure Maps.
