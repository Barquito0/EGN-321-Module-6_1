"""Build SQLite history and honest anchored reports from the instructor-supplied CSV."""
import json
from pathlib import Path
from src.history import connect, import_csv, summarize
from src.plots import plot_series

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'sensor_history.db'
if DB.exists():
    DB.unlink()
conn = connect(DB)
import_csv(conn, ROOT / 'data' / 'module6_sample_sensor_history.csv')
for name, hours in [('last_hour',1),('last_day',24),('full_history',None)]:
    result = summarize(conn, 'temperature', hours)
    (ROOT/'reports'/f'{name}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    with (ROOT/'reports'/f'{name}.md').open('w', encoding='utf-8') as f:
        f.write(f'# {name.replace("_", " ").title()} — Temperature Sensor\n\n')
        f.write(f"Window: **{result['start']} → {result['end']}** (anchored to latest stored timestamp)\n\n")
        f.write(f"- Expected readings: **{result['expected']}**\n- Received readings: **{result['received']}**\n")
        f.write(f"- Missing timestamps: **{result['missing']}**\n- Completeness: **{result['completeness_pct']:.2f}%**\n")
        f.write(f"- Accepted: **{result['accepted']}**; rejected: **{result['rejected']}**\n")
        f.write(f"- Accepted temperature minimum / maximum / mean: **{result['accepted_min']:.2f} / {result['accepted_max']:.2f} / {result['accepted_mean']:.2f} °C**\n")
        f.write(f"- Source status counts: **{result['statuses']}**\n- Largest observed inter-reading gap: **{result['largest_gap_seconds']/60:g} minutes**\n\n")
        f.write('## Detected gaps\n\n')
        if result['gaps']:
            for g in result['gaps']:
                f.write(f"- {g['after']} → {g['before']}: {g['missing_slots']} missing expected slots ({g['duration_seconds']/60:g}-minute timestamp separation)\n")
        else:
            f.write('No missing timestamp slots detected in this window.\n')
        f.write('\n**Evidence limit:** missing intervals contain no measured values. No interpolation or averaging across gaps is used.\n')
    plot_series(conn, name, hours, ROOT/'plots'/f'{name}.png')
    print(name, result['expected'], result['received'], result['missing'], result['largest_gap_seconds'])
conn.close()