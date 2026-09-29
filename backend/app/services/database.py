"""Optional PostgreSQL persistence for provider snapshots."""
from __future__ import annotations

import os
from typing import Any

RETENTION_DAYS = 30


def _database_url() -> str | None:
    url = os.getenv('DATABASE_URL')
    if not url:
        return None
    if url.startswith('postgres://'):
        return 'postgresql://' + url[len('postgres://'):]
    return url


def configured() -> bool:
    return _database_url() is not None


def _connect():
    import psycopg
    url = _database_url()
    if not url:
        raise RuntimeError('DATABASE_URL is not configured')
    return psycopg.connect(url, connect_timeout=5)


def initialize() -> bool:
    """Create the snapshot table when a managed PostgreSQL URL is configured."""
    if not configured():
        return False
    with _connect() as connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS provider_snapshots (
                region TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                payload JSONB NOT NULL,
                PRIMARY KEY (region, updated_at)
            )
        ''')
        connection.execute('''
            CREATE INDEX IF NOT EXISTS provider_snapshots_region_latest
            ON provider_snapshots (region, updated_at DESC)
        ''')
    return True


def save_snapshot(region: str, payload: dict[str, Any]) -> None:
    """Persist a complete provider refresh and prune snapshots beyond retention."""
    from psycopg.types.json import Jsonb
    with _connect() as connection:
        connection.execute('''
            CREATE TABLE IF NOT EXISTS provider_snapshots (
                region TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                payload JSONB NOT NULL,
                PRIMARY KEY (region, updated_at)
            )
        ''')
        connection.execute('''
            CREATE INDEX IF NOT EXISTS provider_snapshots_region_latest
            ON provider_snapshots (region, updated_at DESC)
        ''')
        connection.execute(
            '''INSERT INTO provider_snapshots (region, updated_at, payload)
               VALUES (%s, %s::timestamptz, %s)
               ON CONFLICT (region, updated_at) DO UPDATE SET payload = EXCLUDED.payload''',
            (region, payload['updated_at'], Jsonb(payload)),
        )
        connection.execute(
            "DELETE FROM provider_snapshots WHERE updated_at < now() - (%s * interval '1 day')",
            (RETENTION_DAYS,),
        )


def load_latest_snapshot(region: str) -> dict[str, Any] | None:
    if not configured():
        return None
    with _connect() as connection:
        row = connection.execute(
            '''SELECT payload FROM provider_snapshots
               WHERE region = %s ORDER BY updated_at DESC LIMIT 1''',
            (region,),
        ).fetchone()
    return row[0] if row else None


def status() -> dict[str, Any]:
    if not configured():
        return {'configured': False, 'connected': False}
    try:
        with _connect() as connection:
            count = connection.execute(
                'SELECT count(*) FROM provider_snapshots'
            ).fetchone()[0]
            latest = connection.execute(
                'SELECT region, max(updated_at) FROM provider_snapshots GROUP BY region'
            ).fetchall()
        return {
            'configured': True,
            'connected': True,
            'snapshot_count': count,
            'latest_by_region': {region: updated_at.isoformat() for region, updated_at in latest},
            'retention_days': RETENTION_DAYS,
        }
    except Exception:
        return {'configured': True, 'connected': False}
