import csv

with open('data/ground_truth/ibtracs.NI.list.v04r00.csv') as f:
    rows = list(csv.reader(f))

header = rows[0]
wind_idx = header.index('WMO_WIND')
name_idx = header.index('NAME')
season_idx = header.index('SEASON')
sid_idx = header.index('SID')
time_idx = header.index('ISO_TIME')
lat_idx = header.index('LAT')
lon_idx = header.index('LON')

storms = {}
for r in rows[2:]:
    try:
        w = float(r[wind_idx].strip()) if r[wind_idx].strip() else 0
    except:
        w = 0
    if w >= 90:
        name = r[name_idx].strip()
        season = r[season_idx].strip()
        sid = r[sid_idx].strip()
        key = sid
        if key not in storms or storms[key]['peak_wind'] < w:
            storms[key] = {
                'name': name, 'season': season,
                'peak_wind': w, 'time': r[time_idx],
                'sid': sid
            }

top = sorted(storms.values(), key=lambda x: -x['peak_wind'])[:20]
print('Top NI cyclones by peak wind in IBTrACS (excluding Biparjoy/Amphan):')
for s in top:
    if s['name'] not in ('BIPARJOY', 'AMPHAN'):
        print(f"  {s['name']:<20} {s['season']}  peak={s['peak_wind']:.0f}kts  {s['time'][:7]}")
