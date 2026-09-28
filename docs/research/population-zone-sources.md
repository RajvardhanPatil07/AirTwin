# Population and mapped activity inputs for Pune/PCMC

Research date: 2026-09-28. AOI: west 73.70, south 18.43, east 73.98, north 18.76. These sources replace invented spatial inputs; they do not validate intervention emission factors.

## Recommended population source

Use [WorldPop India population counts, 2020, UN-adjusted 1km](https://hub.worldpop.org/geodata/summary?id=36811), DOI [10.5258/SOTON/WP00671](https://doi.org/10.5258/SOTON/WP00671). The source describes **estimated people per pixel**, WGS84, 30 arc-second cells (~1km at the equator), derived by random-forest dasymetric redistribution and adjusted nationally to UN 2019 Revision totals. It is modeled residential population for 2020, not a 2026 census or a count of actual exposed people.

[Direct GeoTIFF download](https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif) is 18,313,124 bytes (17.46MiB); a live request returned HTTP 200 and TIFF bytes. Downloading the complete India raster then cropping the AOI is practical. This avoids gigabyte 100m products and hundreds of cell-level API requests. Store URL, retrieval time, SHA256, dataset year, units, CRS, transform and nodata in the resulting artifact manifest.

Aggregate counts by overlap area into target grid polygons; never use bilinear interpolation on counts or repeat a sampled pixel count into multiple smaller target cells. Preserve totals within rounding tolerance and mask nodata. If cells cut the AOI boundary, include only their overlapping fraction. Fractional overlap assumes population uniform within each source pixel and should be disclosed. Raw raster units are people/pixel; population density must divide by physical cell area, if needed.

WorldPop's metadata states [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Include WorldPop/CIESIN credit, dataset DOI, year and license with any redistributed crop and visible application attribution. The source page supplies the recommended project citation. Display “WorldPop modeled population (2020)” and avoid labeling this layer observed population. Do not manufacture vulnerable-group estimates from total population.

The [WorldPop v2 API](https://api.worldpop.org/v2/) can sum polygons without authentication (documented 1000 daily requests, 50,000km² polygon limit), but raster download is preferable for reproducible grid aggregation. The API serves Global2 data, which is a different product; do not silently mix it with this historical raster.

## Recommended mapped activity source

Download OpenStreetMap industrial polygons, construction polygons and major-road ways with [Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API). Public endpoint candidates: `https://overpass-api.de/api/interpreter`, `https://overpass.kumi.systems/api/interpreter`, `https://overpass.private.coffee/api/interpreter`. Query bbox order is south,west,north,east, unlike the app west,south,east,north convention.

```overpass
[out:json][timeout:60];
(
  way["landuse"="industrial"](18.43,73.70,18.76,73.98);
  way["landuse"="construction"](18.43,73.70,18.76,73.98);
  way["highway"~"^(motorway|trunk|primary|secondary)$"](18.43,73.70,18.76,73.98);
);
out meta geom;
```

Ways provide a manageable first import but omit relation-only multipolygon areas. Document the bounded extraction rather than claiming completeness. Closed area ways become polygons; roads remain lines. Clip to the AOI. Preserve `type/id`, tags and metadata, original query, endpoint, retrieval timestamp, `osm3s.timestamp_osm_base`, raw-response checksum and license. Do not treat query HTTP success as data success: reject Overpass `remark` errors, missing elements, or malformed geometries; cache the reviewed import so application use does not call Overpass repeatedly.

[Industrial landuse](https://wiki.openstreetmap.org/wiki/Tag:landuse%3Dindustrial) maps areas used by workshops, factories, warehouses and associated infrastructure. It is not an official emissions inventory or legal industrial-zone boundary. [Construction landuse](https://wiki.openstreetmap.org/wiki/Tag:landuse%3Dconstruction) maps areas being built on; tags can be stale, and missing features do not establish no construction. Highway classes reflect mapped road classification, not measured traffic volumes. Activity effects and road buffers remain explicit assumptions even after importing these geometries.

OpenStreetMap data uses [ODbL 1.0](https://www.openstreetmap.org/copyright). Display “© OpenStreetMap contributors” linked to its copyright page. Keep the OSM-derived data license distinct from the software license and WorldPop crop license. Redistributed adapted databases carry the applicable ODbL requirements. Retain the source extract and attribution file with generated GeoJSON.

## Operational limitations

The rectangular AOI is not the administrative boundary of Pune or PCMC. Population figures for it must not be presented as municipal census totals. Population and map data have different reference dates; map retrieval time is not a guarantee that individual objects are current. Pollution interpolation still depends on sparse monitors, and scenario changes still depend on assumed responses. Use these inputs to improve spatial realism, while continuing uncertainty and sensitivity reporting.

Live GET checks of the three full-AOI endpoints returned HTTP406 (overpass-api.de) and 40-second read timeouts (kumi/private.coffee). Endpoint availability and local data counts are therefore not verified by those checks. Retry with form-encoded POST and a smaller bounded query before importing; retain failure status if unavailable.

A subsequent small POST count query for industrial ways also failed (overpass-api.de HTTP504; kumi 20-second timeout). No actual zone data was downloaded in this research task.
