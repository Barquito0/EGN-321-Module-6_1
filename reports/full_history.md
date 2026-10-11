# Full History — Temperature Sensor

Window: **2026-10-01T08:00:00 → 2026-10-02T14:00:00** (anchored to latest stored timestamp)

- Expected readings: **1801**
- Received readings: **1756**
- Missing timestamps: **45**
- Completeness: **97.50%**
- Accepted: **1753**; rejected: **3**
- Accepted temperature minimum / maximum / mean: **19.29 / 24.62 / 22.27 °C**
- Source status counts: **{'OK': 1753, 'OUT_OF_RANGE': 3}**
- Largest observed inter-reading gap: **26 minutes**

## Detected gaps

- 2026-10-01T13:09:00 → 2026-10-01T13:35:00: 25 missing expected slots (26-minute timestamp separation)
- 2026-10-02T05:59:00 → 2026-10-02T06:20:00: 20 missing expected slots (21-minute timestamp separation)

**Evidence limit:** missing intervals contain no measured values. No interpolation or averaging across gaps is used.