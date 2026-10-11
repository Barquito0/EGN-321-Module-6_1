"""Draw disconnected history segments so missing periods remain blank."""
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.history import fetch_window, detect_gaps, EXPECTED_SECONDS


def plot_series(conn, title, hours, path, expected_seconds=EXPECTED_SECONDS):
    start, end, rows = fetch_window(conn, 'temperature', hours)
    times = [datetime.fromisoformat(r['timestamp']) for r in rows]
    values = [r['accepted_value'] for r in rows]
    # Insert NaN between neighboring observed rows separated by missing time slots.
    xx, yy = [], []
    for i, (t, v) in enumerate(zip(times, values)):
        if i and (t - times[i-1]).total_seconds() > expected_seconds * 1.5:
            xx.append(times[i-1] + (t-times[i-1])/2)
            yy.append(float('nan'))
        xx.append(t)
        yy.append(v if v is not None else float('nan'))
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(xx, yy, linewidth=1.1, marker='.', markersize=2)
    ax.set_title(f'{title.replace("_", " ").title()} | Virtual temperature sensor history')
    # Visually identify missing spans; leave sensor data unmodified.
    for gap in detect_gaps(rows, expected_seconds):
        a = datetime.fromisoformat(gap['after'])
        b = datetime.fromisoformat(gap['before'])
        ax.axvspan(a, b, alpha=0.25, hatch='///')
        ax.annotate(f"{gap['missing_slots']} missing", xy=(a+(b-a)/2, 0.91),
                    xycoords=('data', 'axes fraction'), ha='center', fontsize=8,
                    bbox=dict(boxstyle='round,pad=0.2', alpha=0.85))
    ax.set_xlabel('Source timestamp (CSV, not reconstructed)')
    ax.set_ylabel('Accepted temperature (°C)')
    ax.set_xlim(start, end)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    fig.autofmt_xdate()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)