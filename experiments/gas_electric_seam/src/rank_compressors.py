# Screen Texas7k compressors: which plant nodes lie downstream (following base-case flow direction),
# how much plant MW they serve, and how close those plants sit to the 2.8 MPag floor.
import json, sys, collections, math
raw = json.load(open(sys.argv[1])); cd = json.load(open(sys.argv[2])); out = sys.argv[3]
nodes = {n['number']: n for n in raw['nodes']}
FLOOR = 2901.3
adj = collections.defaultdict(list)
for b in raw['branches']:
    a, c, q = b['n1'], b['n2'], b['q']
    if q >= 0: adj[a].append(c)
    else: adj[c].append(a)
plants = {int(k): v for k, v in cd['plants'].items()}
rows = []
for b in raw['branches']:
    if b['dev_type'] != 'compressor': continue
    start = b['n2'] if b['q'] >= 0 else b['n1']
    seen = {start}; st = [start]
    while st:
        x = st.pop()
        for y in adj[x]:
            if y not in seen: seen.add(y); st.append(y)
    dp = sorted(p for p in plants if p in seen)
    mw = sum(plants[p]['pg'] for p in dp)
    marg = min((abs(nodes[p]['p']) - FLOOR for p in dp), default=None)
    n1 = nodes[b['n1']]
    rows.append(dict(comp=b['uid'], n1=b['n1'], n2=b['n2'], ratio=b['r'],
                     flow_std_m3h=round(abs(b['q'])), lat=n1['lat'], lon=n1['lon'],
                     downstream_plants=len(dp), downstream_plant_mw=round(mw, 1),
                     min_downstream_margin_kPa=None if marg is None else round(marg, 1),
                     plant_nodes=dp))
rows.sort(key=lambda r: -r['downstream_plant_mw'])
json.dump(rows, open(out, 'w'), indent=1)
for r in rows:
    print(r['comp'], r['ratio'], r['flow_std_m3h'], round(r['lat'],2), round(r['lon'],2), r['downstream_plants'],
          r['downstream_plant_mw'], r['min_downstream_margin_kPa'], r['plant_nodes'][:8])
