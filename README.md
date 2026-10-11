# EGN 321 — Module 6.1 SQLite History Builder

This project imports an instructor-provided virtual-sensor history into SQLite, calculates last-hour, last-day and full-history completeness, detects gaps, and plots measurements **without joining observations across missing periods**.

**Source:** `module6_sample_sensor_history.csv` (instructor practice data, not a personal Velxio capture). Each input row has a timestamp and five sensor readings: temperature (°C), humidity (%), light (raw), distance (cm), potentiometer (%). Original CSV timestamps are retained, not reconstructed; timezone unspecified.

**Sample interval:** 60 seconds per sensor. Last-hour/day windows are anchored to the latest stored timestamp, not the wall clock.

## Evidence summary — temperature

| Window | Expected | Received | Missing | Completeness |
|---|---:|---:|---:|---:|
| Last hour | 61 | 61 | 0 | 100% |
| Last day | 1441 | 1421 | 20 | 98.61% |
| Full history | 1801 | 1756 | 45 | 97.50% |

Gaps: Oct 1, 2026 13:09→13:35 (25 absent samples) and Oct 2, 2026 05:59→06:20 (20 absent samples). The largest timestamp separation is 26 minutes.

## SQLite model

Table `readings` stores `sensor, sample_number, timestamp, raw_value, accepted_value, unit, status, decision, reason, timestamp_source`. Index: `(sensor, timestamp)`. A rejected reading still counts as received for time completeness. No synthetic timestamp rows are inserted.

## Running

```sh
python -m pip install -r requirements.txt
python build_history.py
python -m pytest -q
```

The builder regenerates `sensor_history.db`, reports in `reports/`, and gap-preserving plots in `plots/`.

## Honesty & limitations

There are **no measurements inside gaps**. Neither plotted lines nor summary averages represent conditions inside the gaps. Timestamp timezone is not provided. Classroom sensor statuses and acceptance thresholds are not device calibration claims. Do not substitute the instructor dataset for the student's own Velxio dataset without disclosure.

## Source / submission

Instructor CSV: `data/module6_sample_sensor_history.csv`. The complete downloadable submission bundle also contains `sensor_history.db`, three reports and PNG plots. [Source GitHub repository](https://github.com/Barquito0/EGN-321-Module-6_1).
