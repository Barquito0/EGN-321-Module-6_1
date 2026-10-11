# Last Day — Temperature Sensor

Window: **2026-10-01T14:00:00 → 2026-10-02T14:00:00** (anchored to latest stored timestamp)

- Expected readings: **1441**
- Received readings: **1421**
- Missing timestamps: **20**
- Completeness: **98.61%**
- Accepted: **1419**; rejected: **2**
- Accepted temperature minimum / maximum / mean: **19.29 / 24.62 / 22.01 °C**
- Source status counts: **{'OK': 1419, 'OUT_OF_RANGE': 2}**
- Largest observed inter-reading gap: **21 minutes**

## Detected gaps

- 2026-10-02T05:59:00 → 2026-10-02T06:20:00: 20 missing expected slots (21-minute timestamp separation)

**Evidence limit:** missing intervals contain no measured values. No interpolation or averaging across gaps is used.