# Furnishing symbol library (CC0)

Top-view architectural symbols used by the Furnishings palette.

* Every SVG `viewBox` is in **inches** (`0 0 WIDTH DEPTH`), so the app
  renders each symbol at true scale (1 scene unit = 1").
* `manifest.json` lists the catalog: `id`, `name`, `category`, `file`,
  `width_in`, `depth_in`, `price` (USD purchase cost; the app's
  AI ‣ Update furnishing prices… tool fills these in).
* `groups.json` defines the palette's expandable sections: a list of
  `{name, items}` where each item is an SVG file name from this
  directory.  A furnishing may appear in several groups.  The `All`
  group always shows the whole library and is open by default.

To add your own symbol: drop an SVG here whose viewBox matches the
real-world footprint in inches, add a manifest entry, and list it in
the groups it belongs to.
