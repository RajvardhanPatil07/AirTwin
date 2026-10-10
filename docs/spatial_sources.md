# Spatial input provenance and limits

The PCMC dashboard bundles [WorldPop India 2020 1 km UN-adjusted](https://hub.worldpop.org/geodata/summary?id=36811)
modeled population counts ([raster](https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif), CC BY 4.0).
The source pixel values are estimated people **per pixel**. `prepare_spatial_inputs.py`
splits each pixel into the 12×12 cells by spherical-area overlap and rounds the
sum using largest remainders, so the grid does not replicate or bilinearly
interpolate whole-pixel counts. The bundled AOI sum is 6,989,281 people across
the wider 73.70–73.98 E, 18.45–18.80 N bounding box; it is **not** a PCMC
administrative population total. The source year is 2020. The original raster
SHA-256 and fractional pre-rounding total are stored in
`data/sample/spatial_inputs.json`.

Mapped geometry comes from [OpenStreetMap](https://www.openstreetmap.org/copyright)
via Overpass under ODbL 1.0. The extract reports OSM data timestamp
2026-06-01T08:52:28Z. It queried industrial and construction `landuse` ways,
plus `primary`, `secondary` and `trunk` highways in the AOI. To keep the UI
bounded, the processor retains the two longest ways per category and tile in a
4×4 partition, producing 73 features. This sampling can omit nearby features.
OSM coverage varies, and mapped land use/roads cannot establish operating
facilities, active construction, traffic volume or PM2.5 emissions. The source
weights and intervention pass-through remain **assumptions**.

The Overpass query was:

```text
[out:json][timeout:30];(way[landuse=industrial](18.45,73.70,18.80,73.98);way[highway~"^(primary|trunk|secondary)$"](18.45,73.70,18.80,73.98);way[landuse=construction](18.45,73.70,18.80,73.98););out geom;
```

The original Overpass JSON is not bundled. OSM can change between downloads;
the bundled derived geometry and original-response SHA-256 are the exact inputs
for reviewing this dashboard version. Data-specific license attribution is in
[`data/sample/SPATIAL_LICENSE.md`](../data/sample/SPATIAL_LICENSE.md).

The bundled processed JSON is under 1 MB and lets the dashboard use these
sources without downloading the full raster at startup. Regenerate locally with:

```sh
python -m pip install rasterio==1.4.4
python backend/scripts/prepare_spatial_inputs.py --raster data/raw/worldpop_ind_ppp_2020_1km_unadj.tif --osm /path/to/overpass-extract.json
```

`data/processed/spatial_inputs.json` takes precedence when present. The
preprocessor validates EPSG:4326 and records source checksums. If optional
spatial input is unavailable or invalid, runtime falls back to explicitly
SYNTHETIC population and illustrative zones. Offline `--offline` tests keep
the synthetic population deliberately. For PCMC sourced operation, scenario
exposure remains an index in person·µg/m³, **not** people protected or a
measured policy benefit.
