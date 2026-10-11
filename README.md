# EGN 321 — Module 6, Assignment 6.1: SQLite History Builder

## What this project does

Imports the **instructor-supplied** `module6_sample_sensor_history.csv` into SQLite, queries three anchored historical windows, identifies absent timestamp slots, and draws **gap-preserving** plots. The CSV was supplied with the Module 6 assignment. It is not represented as data captured from the student's personal Velxio simulation. This distinction matters when interpreting the evidence.

**Source dataset:** `data/module6_sample_sensor_history.csv` (1,756 timestamped records, five sensors per row).  
**Timestamp source:** original ISO timestamps provided in the CSV; **not reconstructed**.  
**Timestamp time zone:** unspecified by the source CSV; reports use the CSV's clock time without claiming a zone.  
**Nominal frequency:** one reading per minute per sensor (`60 seconds`).  
**Sensors:** temperature (°C), humidity (%), light (raw sensor units), distance (cm), potentiometer (%).  
**Primary report sensor:** temperature, with all five sensors stored in the database.

The source includes two missing periods in the **temperature timestamp sequence**, which are also missing for the other sensors because each CSV row contains all five:

| Last reading before interruption | First reading after interruption | Elapsed interval | Expected samples not present |
|---|---|---:|---:|
| 2026-10-01 13:09 | 2026-10-01 13:35 | 26 minutes | 25 |
| 2026-10-02 05:59 | 2026-10-02 06:20 | 21 minutes | 20 |

A gap is detected when neighboring received timestamps are separated by more than `1.5 × expected sampling interval` (90 seconds). With timestamps on the 60-second cadence, missing-slot count is `round(elapsed_seconds / 60) - 1`. This identifies absent **rows in time**, not rows that were received and marked invalid. Those are separate quality issues.

## SQLite schema and traceability

The database `sensor_history.db` includes table `readings` and an index on `(sensor, timestamp)`. Each sensor-specific record preserves:

`(sensor, sample_number, timestamp, raw_value, accepted_value, unit, status, decision, reason, timestamp_source)`.

The importer retains a reading's raw numeric value even when the source status is not `OK`, while `accepted_value` becomes `NULL` for a rejected reading. A nonnumeric or missing raw cell also results in a `NULL` accepted value. The source status is preserved **exactly** and the derived acceptance decision is recorded separately. Classroom acceptance requires source `OK`, a finite numeric value, and (for temperature/humidity/potentiometer) a documented physical/domain range. No missing timestamp rows are inserted. A received but invalid reading still counts as **received** for temporal completeness.

## Three time windows, all anchored to stored data

The last-hour and last-day reports use the **latest timestamp actually stored**, not today's wall clock. Windows are inclusive (`>= start` and `<= end`), so a complete hour has 61 minute-aligned sample slots, and a complete 24-hour period has 1,441 slots.

| Temperature view | Start | End | Expected | Received | Missing | Completeness | Largest time separation |
|---|---|---|---:|---:|---:|---:|---:|
| Last hour | Oct 2, 13:00 | Oct 2, 14:00 | 61 | 61 | 0 | 100.00% | 1 minute (normal cadence; **0 detected gaps**) |
| Last day | Oct 1, 14:00 | Oct 2, 14:00 | 1,441 | 1,421 | 20 | 98.61% | 21 minutes |
| Full history | Oct 1, 08:00 | Oct 2, 14:00 | 1,801 | 1,756 | 45 | 97.50% | 26 minutes |

All three windows are for the temperature sensor, but the data structure supports querying the other four sensors using `summarize(conn, sensor='humidity', ...)` and similar calls. The detailed reports are in `reports/`, including machine-readable `.json` versions.

## Interpretation and limitations

The observed readings support statements about **measured times only**. In particular, the data cannot establish what happened inside the 25-minute and 20-minute unobserved periods. No interpolation, averaging across a gap, synthetic insertion, or chart-line connection across a gap is performed. In `src/plots.py`, a NaN break is inserted in the **plotting arrays only**, not the SQLite table or source CSV, when successive timestamps are separated by a gap. Rejected values also plot as missing rather than a false trusted observation.

The datasets are classroom simulation evidence, not calibrated measurements; nominal cadence is inferred from the consistent source timestamps; no time zone is supplied; sensor-specific thresholds are simplified classroom policies, not device calibration specifications. The source offers temperature statuses such as `OUT_OF_RANGE`, which we preserve, but the database does not silently treat them as accepted measurements.

## How to run

From the repository root:

```bash
python -m pip install -r requirements.txt
python build_history.py
python -m pytest -q
```

`build_history.py` recreates `sensor_history.db` from the unchanged instructor-provided CSV and writes:

- `reports/last_hour.md` and `.json`
- `reports/last_day.md` and `.json`
- `reports/full_history.md` and `.json`
- `plots/last_hour.png`
- `plots/last_day.png`
- `plots/full_history.png`

`src/history.py` contains the SQLite schema, import, query, and gap algorithms. `src/plots.py` creates disconnected time series. Tests under `tests/` cover actual database logging, gap detection/completeness, and latest-timestamp anchored windows.

## GitHub repository

**GitHub repository:** https://github.com/Barquito0/EGN-321-Module-6_1

## Instructor example alignment

The accompanying student guide emphasizes traceability, last-hour/day/full-history views, gap detection, and explicit limitations. The worked example cautions that a plot must not connect observations across an unmeasured period. This implementation follows those rules.