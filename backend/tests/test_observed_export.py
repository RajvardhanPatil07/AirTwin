"""Offline tests for the strict observed-only export gate."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_observed_history as exporter


def fake_database(monkeypatch, records):
    monkeypatch.setattr(exporter.database, "configured", lambda: True)
    monkeypatch.setattr(exporter.database, "status", lambda: {"connected": True})

    class StubConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def execute(self, sql, params):
            assert "airtwin.station_observations" in sql
            assert params[0] <= 90
            return self

        def fetchall(self):
            return records

    monkeypatch.setattr(exporter.database, "_connect", lambda: StubConnection())


def observed_row(hour, station="openaq-123"):
    t = pd.Timestamp("2026-10-07T00:00:00Z") + pd.Timedelta(hours=hour)
    return (t.to_pydatetime(), station, "Test monitor", 18.62, 73.85, 33.0)


def test_export_observed_provenance_excludes_non_openaq_rows(monkeypatch, tmp_path):
    fake_database(monkeypatch, [observed_row(0), observed_row(1),
                                observed_row(2, station="cams-model")])
    target = tmp_path / "genuine.csv"
    path, count, sensors, best = exporter.export_dataset(
        days=90, min_station_hours=2, destination=target)
    frame = pd.read_csv(path)
    assert (count, sensors, best) == (2, 1, 2)
    assert set(frame.source_type) == {"observed"}
    assert set(frame.target_provider) == {"OpenAQ"}
    assert set(frame.station_id) == {"openaq-123"}


def test_export_aborts_without_overwriting_if_insufficient_data(monkeypatch, tmp_path):
    fake_database(monkeypatch, [observed_row(0)])
    target = tmp_path / "genuine.csv"
    target.write_text("previous working dataset")
    with pytest.raises(RuntimeError, match="Only 1 distinct observed hours"):
        exporter.export_dataset(days=90, min_station_hours=720, destination=target)
    assert target.read_text() == "previous working dataset"
