from src.history import connect, insert_reading, fetch_window, detect_gaps, summarize


def test_sqlite_insert_and_query(tmp_path):
    db = connect(tmp_path/'test.db')
    insert_reading(db, 'temperature', 1, '2026-10-01T10:00:00', 20.5, 20.5, 'C', 'OK', 'ACCEPTED', 'valid')
    insert_reading(db, 'temperature', 2, '2026-10-01T10:01:00', 80.0, None, 'C', 'OUT_OF_RANGE', 'REJECTED', 'invalid')
    db.commit()
    _, _, rows = fetch_window(db, 'temperature')
    assert len(rows) == 2
    assert rows[0]['raw_value'] == rows[0]['accepted_value'] == 20.5
    assert rows[1]['raw_value'] == 80.0 and rows[1]['accepted_value'] is None
    db.close()


def test_gap_detection_and_completeness(tmp_path):
    db = connect(tmp_path/'test.db')
    for num, minute in enumerate([0, 1, 5], start=1):
        insert_reading(db, 'temperature', num, f'2026-10-01T10:{minute:02d}:00', 22.0, 22.0, 'C', 'OK', 'ACCEPTED', 'valid')
    db.commit()
    _, _, rows = fetch_window(db, 'temperature')
    gaps = detect_gaps(rows, 60)
    assert len(gaps) == 1
    assert gaps[0]['missing_slots'] == 3
    assert gaps[0]['duration_seconds'] == 240
    totals = summarize(db, 'temperature')
    assert (totals['expected'], totals['received'], totals['missing']) == (6, 3, 3)
    db.close()


def test_windows_anchor_to_latest_historical_record(tmp_path):
    db = connect(tmp_path/'test.db')
    for num, stamp in enumerate(['2026-10-01T00:00:00', '2026-10-02T12:00:00', '2026-10-02T13:00:00'], 1):
        insert_reading(db, 'temperature', num, stamp, 22.0, 22.0, 'C', 'OK', 'ACCEPTED', 'valid')
    db.commit()
    assert summarize(db, hours=1)['received'] == 2
    assert summarize(db, hours=24)['received'] == 2
    assert summarize(db, hours=None)['received'] == 3
    db.close()