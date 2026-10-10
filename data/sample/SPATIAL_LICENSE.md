# Spatial data attribution

`spatial_inputs.json` combines independently licensed source data:

- Population counts derive from **WorldPop India 2020 1 km UN-adjusted**, [WorldPop](https://hub.worldpop.org/geodata/summary?id=36811), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The per-cell allocation is a transformation of the source raster; it is not an official census count.
- Road and land-use geometries derive from **OpenStreetMap contributors**, [copyright and license](https://www.openstreetmap.org/copyright), licensed under the [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/). The bundled extract selects ways within the PCMC analysis bounding box. OpenStreetMap data remains under ODbL.

The repository software license does not replace these data licenses. Source URLs, checksums, dates and transformation methods are recorded in `spatial_inputs.json` and [the provenance note](../../docs/spatial_sources.md).
