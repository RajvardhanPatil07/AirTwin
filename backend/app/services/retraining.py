"""Conservative, automatic live-station LightGBM retraining.

Runs independently of the 15-minute provider refresh. A new model is trained
only on OBSERVED PM2.5 station hours, validated on a purged chronological
holdout, and atomically installed into a *separate* live artifact. Historical
replay and the original model artifact remain untouched.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import logging
import os
from pathlib import Path
import tempfile
import threading

import joblib
import numpy as np
import pandas as pd

from app.services import database
from app.services.data_loader import load_all
from app.services.live_observations import read_training_observations
from app.services.model import MODELS, VERSION, train

LOG = logging.getLogger("airtwin.retraining")
LIVE_ARTIFACT = MODELS / "forecast_live.joblib"
CHECK_HOURS = max(1, int(os.getenv("RETRAIN_CHECK_HOURS", "24")))
MIN_GAP_HOURS = max(1, int(os.getenv("RETRAIN_MIN_GAP_HOURS", "168")))
MIN_NEW_ROWS = max(1, int(os.getenv("RETRAIN_MIN_NEW_ROWS", "48")))
MIN_OBSERVED_ROWS = max(300, int(os.getenv("RETRAIN_MIN_OBSERVED_ROWS", "720")))
MIN_TEST_ROWS = max(24, int(os.getenv("RETRAIN_MIN_TEST_ROWS", "48")))
INITIAL_DELAY_SECONDS = max(0, int(os.getenv("RETRAIN_INITIAL_DELAY_SECONDS", "900")))
_state_lock = threading.Lock()
_state = {"status": "pending", "reason": "First scheduled check has not run"}


def retraining_status():
    with _state_lock:
        return dict(_state)


def _record(status, reason, **details):
    with _state_lock:
        _state.clear()
        _state.update(status=status, reason=reason,
                      checked_at=datetime.now(timezone.utc).isoformat(), **details)
    LOG.info("Retraining %s: %s", status, reason)
    return retraining_status()


@contextmanager
def _exclusive_training():
    """Cross-process lock for multi-worker deployments (PostgreSQL or local)."""
    if database.configured():
        with database._connect() as connection:
            acquired = connection.execute(
                "SELECT pg_try_advisory_lock(67204102)"
            ).fetchone()[0]
            # The lock is session-scoped: end the SQL transaction before the
            # long CPU-bound fit to avoid idle-in-transaction timeouts.
            connection.commit()
            try:
                yield bool(acquired)
            finally:
                if acquired:
                    connection.execute("SELECT pg_advisory_unlock(67204102)")
                    connection.commit()
        return

    # Without an external database, models are local per-instance. A small
    # cross-process file lock works on Windows (msvcrt) and Unix (fcntl).
    MODELS.mkdir(parents=True, exist_ok=True)
    with (MODELS / ".retrain.lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(bytes([0]))
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                yield False
                return
            try:
                yield True
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            try:
                yield True
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _existing_live_artifact():
    if not LIVE_ARTIFACT.is_file():
        return None
    try:
        saved = joblib.load(LIVE_ARTIFACT)
        if (saved.get("version") == VERSION
                and set(saved.get("report", {}).get("target_source_types", [])) == {"observed"}
                and 24 in saved.get("models", {})):
            return saved
    except (OSError, ValueError, EOFError, TypeError, AttributeError):
        LOG.warning("Previous live model cannot be read; keeping legacy fallback")
    return None


def prepare_training_data(base, recent):
    """Merge valid observed targets; never train on CAMS or synthetic PM2.5."""
    base = base.loc[base.source_type.eq("observed")].copy()
    if recent:
        live = pd.DataFrame(recent).copy()
        required = {"station_id", "timestamp", "pm25", "latitude", "longitude", "source_type"}
        if not required.issubset(live):
            raise ValueError("missing_live_observation_columns")
        live = live[live.source_type.eq("observed")].copy()
        live = live[live.station_id.astype(str).str.fullmatch(r"openaq-\d+")].copy()
        live["timestamp"] = pd.to_datetime(live.timestamp, utc=True).dt.tz_convert("Asia/Kolkata")
        live["pm25"] = pd.to_numeric(live.pm25, errors="coerce")
        live = live[live.pm25.between(0, 1000)]
        live = live.dropna(subset=["timestamp", "latitude", "longitude"])
    else:
        live = pd.DataFrame(columns=["station_id", "timestamp", "pm25", "latitude",
                                     "longitude", "source_type"])
    if not base.empty:
        base["timestamp"] = pd.to_datetime(base.timestamp, utc=True).dt.tz_convert("Asia/Kolkata")
    combined = pd.concat([base, live], ignore_index=True, sort=False)
    if combined.empty:
        return combined, live
    combined["station_id"] = combined.station_id.astype(str)
    combined = (combined.sort_values(["station_id", "timestamp"])
                .drop_duplicates(["station_id", "timestamp"], keep="last")
                .reset_index(drop=True))
    return combined, live


def _training_fingerprint(frame, base_fingerprint):
    columns = ["station_id", "timestamp", "pm25", "latitude", "longitude"]
    stable = frame[columns].sort_values(["station_id", "timestamp"])
    digest = hashlib.sha256(base_fingerprint.encode())
    digest.update(pd.util.hash_pandas_object(stable, index=False).values.tobytes())
    return digest.hexdigest()


def _validate(candidate):
    report = candidate["report"]
    if set(report["target_source_types"]) != {"observed"}:
        return "candidate_includes_nonobserved_targets"
    if 24 not in candidate["models"]:
        return "candidate_missing_24h_model"
    # Reject candidates whose installed 24h model would serve persistence
    # exclusively, even if an earlier holdout fit happened to improve.
    bundle = candidate["models"][24]
    weight = bundle.get("weight") if isinstance(bundle, dict) else None
    if weight is None or not np.isfinite(weight) or not 0 < weight <= 1:
        return "24h_production_model_has_no_lightgbm_contribution"
    metric = report["metrics"]
    mae, persistence = float(metric["mae"]), float(metric["persistence_mae"])
    if (int(report["test_rows"]) < MIN_TEST_ROWS or not np.isfinite(mae)
            or not np.isfinite(persistence) or persistence <= 0):
        return "insufficient_or_invalid_holdout"
    # A persistence-only blend (weight=0) can tie the baseline exactly.
    # Such a candidate must not be advertised as a model improvement.
    # 1e-6 avoids promoting a numerical rounding artefact.
    if mae >= persistence - 1e-6:
        return "24h_model_does_not_beat_persistence"
    return None


def _promote(candidate):
    """Atomic swap: an invalid/partial candidate never overwrites live serving."""
    MODELS.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".forecast_live-", suffix=".joblib",
                                            dir=MODELS)
    os.close(descriptor)
    try:
        joblib.dump(candidate, temporary)
        # Verify what will actually be served before replacing the good artifact.
        check = joblib.load(temporary)
        if (check.get("version") != VERSION or 24 not in check.get("models", {})
                or set(check["report"]["target_source_types"]) != {"observed"}):
            raise ValueError("invalid_candidate_artifact")
        os.replace(temporary, LIVE_ARTIFACT)
    finally:
        Path(temporary).unlink(missing_ok=True)


def run_retraining_check():
    """One bounded check. Called by the scheduler, never by user requests."""
    with _exclusive_training() as acquired:
        if not acquired:
            return _record("skipped", "Another worker is retraining")
        previous = _existing_live_artifact()
        previous_meta = previous.get("retraining", {}) if previous else {}
        if previous_meta.get("trained_at"):
            age_hours = (pd.Timestamp.now(tz="UTC") -
                         pd.Timestamp(previous_meta["trained_at"])).total_seconds() / 3600
            if age_hours < MIN_GAP_HOURS:
                return _record("skipped", "Waiting for minimum time between promotions",
                               hours_remaining=round(MIN_GAP_HOURS - age_hours, 1))

        base, warnings, base_fingerprint, exog = load_all()
        recent = read_training_observations()
        frame, live = prepare_training_data(base, recent)
        if len(frame) < MIN_OBSERVED_ROWS:
            return _record("skipped", "Not enough measured station hours",
                           observed_rows=len(frame), required_rows=MIN_OBSERVED_ROWS)
        if frame.timestamp.dt.floor("D").nunique() < 14:
            return _record("skipped", "Less than 14 distinct days of observations",
                           observed_rows=len(frame))

        original_observed = base[base.source_type.eq("observed")]
        previous_cutoff = previous_meta.get("latest_observed_at")
        if previous_cutoff is None and not original_observed.empty:
            previous_cutoff = pd.to_datetime(original_observed.timestamp, utc=True).max().isoformat()
        new_rows = (len(live) if previous_cutoff is None else int(
            (live.timestamp > pd.Timestamp(previous_cutoff).tz_convert("Asia/Kolkata")).sum()))
        if new_rows < MIN_NEW_ROWS:
            return _record("skipped", "Not enough new measured station hours",
                           new_rows=new_rows, required_new_rows=MIN_NEW_ROWS)
        fingerprint = _training_fingerprint(frame, base_fingerprint)
        if previous and previous.get("fingerprint") == fingerprint:
            return _record("skipped", "Candidate dataset is unchanged", new_rows=new_rows)

        LOG.info("Training measured-only candidate: %s rows, %s new", len(frame), new_rows)
        # Training uses only valid observed targets; missing historical weather
        # remains missing rather than inventing issue-time weather.
        source_warnings = [warning for warning in warnings if not warning.startswith(
            ("SYNTHETIC targets:", "CAMS MODELED targets:"))]
        if not base.source_type.eq("observed").all():
            source_warnings.append(
                "Non-observed baseline targets were excluded from candidate training.")
        candidate = train(frame, fingerprint, [*source_warnings,
            "Scheduled training combines measured archive and retained OpenAQ hours; "
            "missing historical weather is not filled with future weather."],
            exog=exog, persist=False, prefer_recent_holdout=True)
        failure = _validate(candidate)
        if failure:
            return _record("rejected", failure, observed_rows=len(frame),
                           new_rows=new_rows, holdout_mae=candidate["report"]["metrics"]["mae"],
                           persistence_mae=candidate["report"]["metrics"]["persistence_mae"])

        trained_at = datetime.now(timezone.utc).isoformat()
        latest_live = live.timestamp.max().isoformat() if not live.empty else None
        candidate["retraining"] = {
            "trained_at": trained_at, "latest_observed_at": latest_live,
            "base_fingerprint": base_fingerprint, "observed_rows": len(frame),
            "new_rows": new_rows, "validation": "chronological_purged_holdout",
        }
        _promote(candidate)
        return _record("promoted", "Validated observed-only model activated",
                       trained_at=trained_at, observed_rows=len(frame), new_rows=new_rows,
                       holdout_mae=candidate["report"]["metrics"]["mae"],
                       persistence_mae=candidate["report"]["metrics"]["persistence_mae"])


def retraining_loop(stop):
    """Daily check with an initial ingestion grace period and clean shutdown."""
    if stop.wait(INITIAL_DELAY_SECONDS):
        return
    while not stop.is_set():
        try:
            run_retraining_check()
        except Exception:
            LOG.exception("Background retraining failed; previous forecasts preserved")
            _record("error", "Retraining failed; previous model unchanged")
        if stop.wait(CHECK_HOURS * 3600):
            break
