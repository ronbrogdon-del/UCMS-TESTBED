import json, sys
def md(s): return {"cell_type":"markdown","metadata":{},"source":s}
def code(s): return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s}
cells=[
md("""# SCFL Gas–Electric Seam: Confirmation Package (rule v4-Tune-2, unchanged), tuning set only, not blind
Upstream Coherence Measurement Stratum (UCMS) | Ronald L. Brogdon | ORCID: https://orcid.org/0009-0009-0507-2971

Frozen engine v1.1.0 (https://doi.org/10.5281/zenodo.23839571). Commit, scenarios and seeds in `inputs/PROVENANCE.json`. Fresh noise seeds 20261201–20261230. These runs check the two claims (precursor gate, acute break at the Houston plants) before the freeze; they are never part of the sealed test.

Every input is 24 hours: 00:00–06:00 is the settled baseline, strain starts at 07:00.

11 conditions × 30 seeds = 330 inputs:
- C01 control; C12 medium strain (41%, ramp 07:00–09:00)
- C02 strain 30% (ramp 2 h); C03 strain 47%, 1 h ramp; C04 strain 41%, 4 h ramp
- C05, C06, C07: medium strain + stations c23, c27, c21 isolated (84–114 km from Houston)
- C08: 47% strain + Houston c20 isolated 10:00 (late)
- C09: 30% strain + Houston c15 isolated 07:30 (early)
- C11: medium strain + north-east station c1 isolated 08:00 (far)

Use the same `scfl_private_settings.json` as before, unchanged.

1. **Upload** `scfl_measure.py`, `scfl_ingest_qc.py`, `SCFL_tune2_confirm_inputs.zip` and `scfl_private_settings.json`.
2. **Check** the engine is the frozen v1.1.0.
3. **Run** ingest QC and the engine on all 330 inputs (about 30 minutes).
4. **Save** fingerprint the outputs and download them."""),
code("""# Cell 1: upload the two engine files, the inputs zip and (optional) scfl_private_settings.json
import os, glob, shutil
from google.colab import files
files.upload()
# Fix names the browser changed, e.g. 'scfl measure (1).py' or 'scfl measure.py'
want = {'scfl_measure.py': 'measure', 'scfl_ingest_qc.py': 'ingest', 'SCFL_tune2_confirm_inputs.zip': 'tune2'}
for name, key in want.items():
    if os.path.exists(name):
        continue
    found = [f for f in glob.glob('*') if key in f.lower().replace(' ', '_').replace('_(','(') and f != name
             and f.lower().endswith(name.rsplit('.', 1)[1])]
    if found:
        shutil.copy(sorted(found)[-1], name); print('renamed', sorted(found)[-1], '->', name)
missing = [n for n in want if not os.path.exists(n)]
print('Missing:', missing) if missing else print('All three files present. Run Cell 2.')
pv = [f for f in glob.glob('*') if 'private' in f.lower() and f.lower().endswith('.json')]
if pv and not os.path.exists('scfl_private_settings.json'):
    shutil.copy(sorted(pv)[-1], 'scfl_private_settings.json')
print('Private settings:', 'found' if os.path.exists('scfl_private_settings.json') else 'none (package defaults)')"""),
code("""# Cell 2: fix any browser-renamed files, then confirm the frozen engine (line endings normalized, as in the freeze)
import hashlib, os, glob, shutil
for name, key in {'scfl_measure.py': 'measure', 'scfl_ingest_qc.py': 'ingest', 'SCFL_tune2_confirm_inputs.zip': 'tune2'}.items():
    if not os.path.exists(name):
        found = [f for f in glob.glob('*') if key in f.lower().replace(' ', '_').replace('_(','(') and f.lower().endswith(name.rsplit('.', 1)[1])]
        if found: shutil.copy(sorted(found)[-1], name); print('renamed', sorted(found)[-1], '->', name)
def h(p): return hashlib.sha256(open(p,'rb').read().replace(b'\\r\\n', b'\\n')).hexdigest()
FROZEN = {'scfl_measure.py': '233d9d9c154639c3e7c4fcc0f57bc2044cfe313e17f89d09bed9610a61e5b020',
          'scfl_ingest_qc.py': '50a9ebc2a860fe0a8b82eb7d716e0dce13432bda89ea0fb5768d535ccb8eaa3b'}
ok = True
for f, want_h in FROZEN.items():
    got = h(f); print(f, 'MATCH' if got == want_h else 'MISMATCH ' + got); ok &= got == want_h
zh = hashlib.sha256(open('SCFL_tune2_confirm_inputs.zip','rb').read()).hexdigest()
print('inputs package', 'MATCH' if zh == 'ZIPHASH' else 'MISMATCH ' + zh)
print('Frozen engine confirmed. Run Cell 3.' if ok else 'STOP: engine does not match the freeze.')"""),
code("""# Cell 3: run ingest QC and the engine on every input
import zipfile, subprocess, json
zipfile.ZipFile('SCFL_tune2_confirm_inputs.zip').extractall('.')
def merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): merge(a[k], v)
        else: a[k] = v
    return a
PRIV = json.load(open('scfl_private_settings.json')) if os.path.exists('scfl_private_settings.json') else None
if PRIV:
    for d in glob.glob('inputs/INPUT_*'):
        cfg = json.load(open(f'{d}/scan_config.json')); json.dump(merge(cfg, PRIV), open(f'{d}/scan_config.json', 'w'), indent=2)
    print('private settings merged into', len(glob.glob('inputs/INPUT_*')), 'configs (this session only)')
ING, ENG = os.path.abspath('scfl_ingest_qc.py'), os.path.abspath('scfl_measure.py')
for d in sorted(glob.glob('inputs/INPUT_*')):
    q = subprocess.run(['python', ING, 'series_manifest.csv', '--out', 'qc_output'], cwd=d, capture_output=True, text=True)
    try:
        verdict = json.load(open(f'{d}/qc_output/qc_summary.json'))['run']['verdict']
    except Exception:
        print(d, 'INGEST ERROR:', (q.stderr or q.stdout)[-600:]); continue
    print(d, 'ingest:', verdict)
    if verdict != 'READY':
        print((q.stdout or '')[-600:]); continue
    r = subprocess.run(['python', ENG, 'qc_output/aligned_series.csv', 'series_manifest.csv',
                        '--config', 'scan_config.json', '--out', 'measure_output'], cwd=d, capture_output=True, text=True)
    print(d, 'engine:', 'RUN' if r.returncode == 0 else 'ENGINE ERROR: ' + (r.stderr or r.stdout)[-600:])
print('done:', len(glob.glob('inputs/INPUT_*/measure_output/operators_summary.json')), 'of', len(glob.glob('inputs/INPUT_*')), 'inputs measured')"""),
code("""# Cell 4: fingerprint the outputs and download them
import os, glob, zipfile, hashlib
from google.colab import files
out = 'tune2_readings.zip'
lines = []
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(glob.glob('inputs/INPUT_*/qc_output/*') + glob.glob('inputs/INPUT_*/measure_output/*')):
        if os.path.isfile(f):
            z.write(f); lines.append(f'{hashlib.sha256(open(f,"rb").read()).hexdigest()}  {f}')
open('tune2_fingerprints.txt', 'w').write('\\n'.join(lines) + '\\n')
print(len(lines), 'output files')
files.download(out); files.download('tune2_fingerprints.txt')"""),
]
nb={"cells":cells,"metadata":{"kernelspec":{"name":"python3","display_name":"Python 3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":5}
s=json.dumps(nb,indent=1).replace('ZIPHASH',sys.argv[2])
open(sys.argv[1],'w').write(s)
