import csv
from collections import defaultdict

with open('data/ground_truth/ibtracs.NI.list.v04r00.csv') as f:
    rows = list(csv.reader(f))

header = rows[0]
wind_idx = header.index('WMO_WIND')
name_idx = header.index('NAME')
season_idx = header.index('SEASON')
sid_idx = header.index('SID')
time_idx = header.index('ISO_TIME')

storm_data = defaultdict(list)
for r in rows[2:]:
    try:
        w = float(r[wind_idx].strip()) if r[wind_idx].strip() else 0
    except:
        w = 0
    sid = r[sid_idx].strip()
    name = r[name_idx].strip()
    try:
        season = int(r[season_idx].strip())
    except:
        season = 0
    storm_data[sid].append({'name': name, 'season': season, 'wind': w, 'time': r[time_idx]})

skip = {'NOT_NAMED', '', 'BIPARJOY', 'AMPHAN'}
candidates = []
for sid, entries in storm_data.items():
    name = entries[0]['name']
    season = entries[0]['season']
    if season < 2010 or name in skip:
        continue
    peak = max(e['wind'] for e in entries)
    if peak < 80:
        continue
    times = sorted(e['time'] for e in entries if e['time'].strip())
    candidates.append({
        'sid': sid, 'name': name, 'season': season,
        'peak': peak, 'frames': len(entries),
        'start': times[0][:10] if times else '?',
        'end': times[-1][:10] if times else '?'
    })

candidates.sort(key=lambda x: -x['peak'])
print('Strong named NI cyclones 2010+ (suitable for GridSat download):')
print(f"{'Name':<18} {'Year':<6} {'Peak_kts':<10} {'Frames':<8} {'Start':<12} {'End'}")
for c in candidates[:15]:
    print(f"{c['name']:<18} {c['season']:<6} {c['peak']:<10.0f} {c['frames']:<8} {c['start']:<12} {c['end']}")
