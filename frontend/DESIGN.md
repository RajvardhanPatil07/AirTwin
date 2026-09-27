# Screenshot implementation direction

Source: user-provided AirTwin civic dashboard screenshot, corresponding to Kombai
canvas node `node_3810ffa21f89`.

ENERGY 1 / RHYTHM 1 / MOTION 1. Calm operational interface for hackathon judges
and city decision-makers; no decorative motion.

- Layout: 60/40 map-and-insights split follows the selected reference and keeps
  geography visible alongside action comparison. Narrow screens stack the same views.
- Typography: locally bundled Inter matches the source and keeps dense labels readable.
- Colors: off-white canvas, white surfaces, forest text, and blue actions come from
  the source. Orange dashed borders identify modeled results, not decoration.
- Map colors: concentration bands are semantic data colors, outside the UI palette.
- Geometry: 16px panel radii, 12px cards, and 3px provenance badges distinguish levels.
- Spacing: 20px outer padding, 16px panel gap, and compact cards match reference density.
- Elevation: small shadows only for header and controls floating over the map.
- Icons: Moon/Sun identify theme; RotateCw recalculates; Trophy shows rank;
  ArrowRight connects before/after; MapPin and Layers identify geography and layers.
- Assets: supplied contour logo reused; actual OpenStreetMap tiles replace fake map art.
- Hatch: a technical map pattern encodes modeled provenance. It is not an illustration.

Intentional correctness changes: synthetic badges replace invented observations;
computed scenario results replace inconsistent fixed values; one tooltip replaces
overlapping map labels; true tabs replace cosmetic tab clicks; a real theme toggle
styles the whole dashboard. The snapshot date is fixed to the synthetic fixture's
date, while the header clock shows current IST.
