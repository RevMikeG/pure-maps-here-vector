# pure-maps-here-vector
HERE Vector Maps for Pure Maps on Sailfish OS
An experimental custom map definition that adds HERE Vector to Pure Maps on Sailfish OS. It uses HERE's MapLibre-compatible vector style rather than raster tiles, so map labels can stay readable when the map rotates during navigation.

This was tested with Pure Maps 3.5.1 on a Jolla Phone 2026. It is a community configuration, not an official HERE or Pure Maps release.
What it does
- Adds HERE Vector as a selectable map provider.
- Uses HERE's hosted vector style via the existing Pure Maps Mapbox GL-compatible renderer.
- Can be selected with the HERE profile so that the existing HERE routing integration remains available.
- Does not itself implement traffic routing, traffic overlays, or automatic rerouting. Those are functions of the selected routing provider and navigation settings.
Requirements
- Pure Maps with vector-map support (tested with version 3.5.1 on Sailfish OS).
- Internet connection to fetch HERE vector-map resources.
- A valid HERE API key configured in Pure Maps under HERE_APIKEY with access to the vector-style service. Do not put your actual key in the JSON file or commit it to GitHub.
- Appropriate HERE service entitlement and compliance with HERE's usage terms.
Installation on Sailfish OS
1. Download [`here_vector_day.json`](here_vector_day.json).
2. Open Terminal on your Jolla and create the Sailfish-specific map directory:
   mkdir -p ~/.local/share/io.github.rinigus/PureMaps/maps
3. Copy the downloaded definition into that directory (adjust the source path if the download went elsewhere):
   cp ~/Downloads/here_vector_day.json ~/.local/share/io.github.rinigus/PureMaps/maps/
   Alternatively, transfer the file using SSH or a file manager. Verify it is in place:
   ls -l ~/.local/share/io.github.rinigus/PureMaps/maps/here_vector_day.json
4. Make sure HERE_APIKEY is set up in Pure Maps. The definition contains the placeholder #HERE_APIKEY#, which Pure Maps replaces with its configured key.
5. Fully close Pure Maps, including its home-screen application card, then launch it again.
6. Open Settings / Preferences → Maps and select HERE Vector. (The exact menu wording may differ by version.)
Important: The Sailfish-specific path above is not the generic Linux path ~/.local/share/pure-maps/maps/ and not the old ~/.local/share/harbour-pure-maps/maps/. The Sailfish application sets PUREMAPS_HOME_DATA to io.github.rinigus/PureMaps at startup.

Using HERE congestion-aware routing
The map display and routing provider are separate concerns. To use HERE's existing traffic-aware route calculations:
1. Switch the Pure Maps profile to HERE.
2. Select HERE Vector under the map provider options, if necessary.
3. In the route-planning options, enable Traffic if offered.
4. In navigation settings, enable the traffic-update option if offered, so traffic can be refreshed while navigating.
The vector map does not supply traffic data on its own. Whether a route actually accounts for live congestion depends on HERE routing configuration, network access, service permissions, and the Pure Maps version. Test routing and rerouting before relying on it for a journey.
Troubleshooting
HERE Vector does not appear in the Maps list
- Check that the file is in ~/.local/share/io.github.rinigus/PureMaps/maps/, not only one of the generic directories.
- Validate the JSON:
  python3 -m json.tool ~/.local/share/io.github.rinigus/PureMaps/maps/here_vector_day.json >/dev/null && echo 'JSON valid'
- Fully close Pure Maps and reopen it.
- Confirm the definition has "profiles": ["mixed", "online", "HERE"] and "provider": "HERE Vector".
“loading style failed: HTTP status code 401”
- The HERE vector service has rejected authentication. Confirm that Pure Maps has a valid HERE API key and that the key has access to the relevant HERE service.
- Do not remove "keys": ["HERE_APIKEY"] as a permanent workaround. Without it, Pure Maps does not replace #HERE_APIKEY# in the URL, which can lead to an HTTP 401 error.
- Close and reopen Pure Maps after updating the key.
Vector map displays but congestion is not taken into account
- Verify that the HERE profile, not merely the HERE Vector map, is selected.
- Check that HERE traffic routing is enabled for the route and available under your HERE access arrangement.
Map loads but labels or route lines behave strangely
- HERE's hosted style or Pure Maps' renderer may change. This configuration is experimental, and may need future adjustments such as label/route-layer settings.
Configuration
The included JSON uses the following HERE-hosted style URL:
https://assets.vector.hereapi.com/styles/berlin/base/mapbox/tilezen?apikey=#HERE_APIKEY#
The #HERE_APIKEY# token is an application-side placeholder, not a usable API key. Leave it unchanged in a public repository.
Removal
Select another map provider first, then remove the definition and restart Pure Maps:
rm ~/.local/share/io.github.rinigus/PureMaps/maps/here_vector_day.json
This does not remove Pure Maps, change its built-in HERE maps, or alter your routing settings.
References
- Pure Maps source
- Pure Maps custom map-definition documentation
- Sailfish startup data-directory configuration
- Sailfish data-directory prefix
- HERE legal information
Disclaimer
Unofficial community configuration, tested on one device and installation. HERE and Pure Maps are trademarks or projects of their respective owners. Check service terms, entitlement, and any applicable attribution requirements before redistributing or using this configuration.
