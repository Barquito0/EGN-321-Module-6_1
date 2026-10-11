"""SQLite sensor history, source-preserving import, anchored windows and gap checks."""
import csv
import math
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

EXPECTED_SECONDS = 60
FIELDS = [
    ('temperature', 'temperature_c', 'temperature_status', 'C', 0, 50),
    ('humidity', 'humidity_percent', 'humidity_status', '%', 0, 100),
    ('light', 'light_raw', 'light_status', 'raw', None, None),
    ('distance', 'distance_cm', 'distance_status', 'cm', None, None),
    ('potentiometer', 'potentiometer_percent', 'potentiometer_status', '%', 0, 100),
]


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS readings (
        sensor TEXT NOT NULL,
        sample_number INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        raw_value REAL,
        accepted_value REAL,
        unit TEXT NOT NULL,
        status TEXT NOT NULL,
        decision TEXT NOT NULL,
        reason TEXT NOT NULL,
        timestamp_source TEXT NOT NULL,
        PRIMARY KEY(sensor, sample_number)
    )''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_readings_sensor_time ON readings(sensor, timestamp)')
    return conn


def insert_reading(conn, sensor, sample_number, timestamp, raw_value, accepted_value, unit, status, decision, reason, timestamp_source='ORIGINAL_CSV'):
    conn.execute('''INSERT INTO readings
        (sensor,sample_number,timestamp,raw_value,accepted_value,unit,status,decision,reason,timestamp_source)
        VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (sensor, sample_number, timestamp, raw_value, accepted_value, unit, status, decision, reason, timestamp_source))


def import_csv(conn, path):
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            # Preserve each original timestamp and simulator status; no timestamps reconstructed.
            moment = datetime.fromisoformat(row['timestamp']).isoformat(timespec='seconds')
            for sensor, value_field, status_field, unit, lower, upper in FIELDS:
                status = row[status_field]
                original = row[value_field].strip()
                raw = None
                reason = 'source status OK and numeric value available'
                decision = 'ACCEPTED'
                if not original:
                    decision, reason = 'REJECTED', 'missing raw value'
                else:
                    try:
                        raw = float(original)
                        if not math.isfinite(raw):
                            raw = None
                            decision, reason = 'REJECTED', 'non-finite raw value'
                    except ValueError:
                        decision, reason = 'REJECTED', 'non-numeric raw value'
                if status != 'OK':
                    decision, reason = 'REJECTED', 'source status: ' + status
                elif raw is not None and ((lower is not None and raw < lower) or (upper is not None and raw > upper)):
                    decision, reason = 'REJECTED', 'outside documented classroom acceptance range'
                insert_reading(conn, sensor, int(row['sample_number']), moment, raw,
                               raw if decision == 'ACCEPTED' else None, unit, status,
                               decision, reason)
    conn.commit()


def get_latest(conn, sensor='temperature'):
    return datetime.fromisoformat(conn.execute('SELECT MAX(timestamp) FROM readings WHERE sensor=?', (sensor,)).fetchone()[0])


def fetch_window(conn, sensor='temperature', hours=None):
    latest = get_latest(conn, sensor)
    if hours is None:
        results = conn.execute('SELECT * FROM readings WHERE sensor=? ORDER BY timestamp', (sensor,)).fetchall()
        start = datetime.fromisoformat(results[0]['timestamp'])
    else:
        start = latest - timedelta(hours=hours)
        results = conn.execute('SELECT * FROM readings WHERE sensor=? AND timestamp>=? AND timestamp<=? ORDER BY timestamp',
                               (sensor, start.isoformat(timespec='seconds'), latest.isoformat(timespec='seconds'))).fetchall()
    return start, latest, results


def detect_gaps(rows, expected_seconds=EXPECTED_SECONDS):
    """Return true missing timestamp slots between observed samples, with no fills."""
    gaps = []
    for prev, cur in zip(rows, rows[1:]):
        a, b = datetime.fromisoformat(prev['timestamp']), datetime.fromisoformat(cur['timestamp'])
        elapsed = (b-a).total_seconds()
        if elapsed > expected_seconds * 1.5:
            absent = max(0, round(elapsed / expected_seconds) - 1)
            gaps.append({'after': a.isoformat(timespec='seconds'), 'before': b.isoformat(timespec='seconds'),
                         'duration_seconds': elapsed, 'missing_slots': absent})
    return gaps


def summarize(conn, sensor='temperature', hours=None, expected_seconds=EXPECTED_SECONDS):
    start, end, rows = fetch_window(conn, sensor, hours)
    expected = int(round((end-start).total_seconds() / expected_seconds)) + 1
    received = len(rows)
    gaps = detect_gaps(rows, expected_seconds)
    accepted = [r['accepted_value'] for r in rows if r['accepted_value'] is not None]
    statuses = {r['status']: sum(x['status'] == r['status'] for x in rows) for r in rows}
    return {'sensor': sensor, 'start': start.isoformat(timespec='seconds'),
            'end': end.isoformat(timespec='seconds'), 'expected': expected, 'received': received,
            'missing': max(0, expected-received), 'completeness_pct': 100*received/expected if expected else 0,
            'accepted': len(accepted), 'rejected': received-len(accepted),
            'accepted_min': min(accepted) if accepted else None,
            'accepted_max': max(accepted) if accepted else None,
            'accepted_mean': sum(accepted)/len(accepted) if accepted else None,
            'statuses': statuses, 'gaps': gaps,
            'largest_gap_seconds': max((x['duration_seconds'] for x in gaps), default=0)}