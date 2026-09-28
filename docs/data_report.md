# Downloaded data coverage

Computed from the local fetched/cleaned dataset. Raw records are not committed.

Raw hourly records: 134,654. Cleaned records: 134,624. Sensors with rows: 15.
Target provenance: observed.
Latest dataset timestamp: 2026-09-24T22:00:00+05:30. Provider delay must be read from the UI, not this static report.

| Sensor | Provider location name | Cleaned hours | First local hour | Last local hour |
| --- | --- | --- | --- | --- |
| 12235540 | Karve Road Pune, Pune - MPCB | 1167 | 2025-03-27T16:00:00+05:30 | 2025-05-23T20:00:00+05:30 |
| 12236443 | Mhada Colony, Pune - IITM | 11748 | 2025-03-27T16:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12236449 | Hadapsar, Pune - IITM | 7225 | 2025-03-27T16:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12236457 | Transport Nagar-Nigdi, Pune - IITM | 10786 | 2025-03-27T16:00:00+05:30 | 2026-09-24T11:00:00+05:30 |
| 12236463 | Revenue Colony-Shivajinagar, Pune - IITM | 10748 | 2025-03-27T17:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12237987 | Gavalinagar, Pimpri Chinchwad - MPCB | 9864 | 2025-03-27T16:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12237996 | Park Street Wakad, Pimpri Chinchwad - MPCB | 6997 | 2025-03-27T16:00:00+05:30 | 2026-03-01T03:00:00+05:30 |
| 12238005 | Savitribai Phule Pune University, Pune - MPCB | 6623 | 2025-03-27T16:00:00+05:30 | 2026-09-24T16:00:00+05:30 |
| 12238676 | Bhumkar Nagar, Pune - IITM | 9740 | 2025-03-28T09:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12238693 | Panchawati_Pashan, Pune - IITM | 11932 | 2025-03-27T16:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12238710 | Savta Mali Nagar, Pimpri-Chinchwad - IITM | 10956 | 2025-03-27T16:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12238734 | Dhankawadi, Pune - IITM | 8192 | 2025-03-31T08:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12243017 | Thergaon, Pimpri Chinchwad - MPCB | 11478 | 2025-03-27T16:00:00+05:30 | 2026-09-24T22:00:00+05:30 |
| 12248370 | Katraj Dairy, Pune - MPCB | 8000 | 2025-03-27T16:00:00+05:30 | 2026-05-23T07:00:00+05:30 |
| 12304615 | Bhosari, Pune - IITM | 9168 | 2025-03-27T16:00:00+05:30 | 2026-09-24T22:00:00+05:30 |

## Forecast-weather coverage

- 24-hour issue-aligned temperature forecasts: 134,624 non-null target rows.
- 48-hour issue-aligned temperature forecasts: 134,624 non-null target rows.
- 72-hour issue-aligned temperature forecasts: 134,624 non-null target rows.

## Limits

- OpenAQ discovery found 23 PM2.5 sensors at 19 locations; only sensors with returned rows appear above.
- Two sensors logged partial-download errors; retained rows are usable but coverage is not claimed complete.
- Snapshot display uses simultaneous recent records; all historical sensors need not appear on the current map.
- Weather is modeled centroid data. PCMC now uses a separate dated WorldPop/OSM spatial input; this report covers sensor/weather ingestion, not that spatial input.
- This is a coverage summary, not a raw dataset or a claim of current live observations.
