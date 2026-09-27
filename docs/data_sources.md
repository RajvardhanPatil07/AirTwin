# Sources, attribution and license notes

This page separates intended provider use from files actually redistributed.
No downloaded environmental provider dataset or WorldPop raster is committed.
No project-wide software license has been selected by the team; dependency/data
licenses do not grant a license to all repository code.

| Source | Current use | Provenance | Attribution/terms |
| --- | --- | --- | --- |
| OpenAQ v3 | Fetcher implemented; real local coverage unverified | Observed target when returned by provider | Preserve underlying provider attribution and review dataset terms |
| Open-Meteo archive | Centroid weather fetcher | Modeled reanalysis | API data CC BY 4.0; credit Open-Meteo and applicable underlying sources |
| Open-Meteo air quality / CAMS | Sparse-target fallback | Modeled concentration | Credit Open-Meteo and the relevant Copernicus/CAMS product |
| OpenStreetMap | Frontend basemap tiles | Map context, not pollution observations | © OpenStreetMap contributors; ODbL data and separate tile-use policy |
| WorldPop | Planned only | Not currently used | Check the exact product/version license before downloading or redistributing |
| Synthetic pipeline CSV | Committed offline sample | Synthetic target and weather | Repository-authored fixture, no provider observation claim |
| Synthetic frontend fixtures | Demo inputs/population | Synthetic | Separate from pipeline CSV, explicitly disclosed in UI |
| Inter / Fontsource | Locally bundled font | Visual dependency | SIL Open Font License; retain package license notices |
| Screenshot logo | User-supplied visual reference | Supplied asset | No third-party ownership or trademark clearance is claimed |

## Primary references

- [OpenAQ documentation](https://docs.openaq.org/): API and provider metadata.
- [Open-Meteo license](https://open-meteo.com/en/licence): API data attribution and licensing.
- [Open-Meteo historical weather](https://open-meteo.com/en/docs/historical-weather-api).
- [Open-Meteo air quality](https://open-meteo.com/en/docs/air-quality-api): model products/attribution.
- [OpenStreetMap copyright](https://www.openstreetmap.org/copyright): ODbL and contributor credit.
- [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/): public tile service conditions.
- [WorldPop](https://www.worldpop.org/): select a dataset and retain its own citation/license.
- [Fontsource Inter](https://fontsource.org/fonts/inter).

Open-Meteo's source code license and its API data license are different. Using
Open-Meteo data does not mean this repository incorporates Open-Meteo server code.
Similarly, OSM database licensing and access to the public tile servers are
separate responsibilities.

## When real data are integrated

Retain dataset/provider IDs, dates, source type, attribution strings and processing
steps. Credit data close to where it is displayed. Explain modifications and
avoid suggesting provider endorsement. Update screenshots if their source changes.
Do not label CAMS or reanalysis as observed, even after ML training.
