import json, sys
def md(s): return {"cell_type":"markdown","metadata":{},"source":s}
def code(s): return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s}
cells=[
md("""# SCFL Gas–Electric Seam: Operator Tuning Set T1 (coupled, pre-freeze)
Upstream Coherence Measurement Stratum (UCMS) | Ronald L. Brogdon | ORCID: https://orcid.org/0009-0009-0507-2971

Frozen engine v1.1.0 (https://doi.org/10.5281/zenodo.23839571). Testbed seam-v0.4-tuning (commit in `inputs/PROVENANCE.json`). **Tuning set (protocol Section 2B): excluded from all sealed statistics.**

13 scenarios × 10 noise seeds = 130 inputs. Every run is 18 hours: a settled 6-hour lead-in (00:00–05:55, used as the SHIFT baseline), then events from 07:00.
- **T01** control · **T02/T03/T04** strain only at 20/41/61% supply loss (ramp 07:00–09:00) · **T05** 41% slow ramp (07:00–13:00) · **T06** 41% fast ramp (07:00–07:15)
- **T07** 41% + Houston c15 isolated 08:00 · **T08** + Dallas-east c2 · **T09** + northeast c1 · **T10** + Houston c20 at 07:30 (before the gate) · **T11** + Victoria at 10:00 (well after the gate)
- **T12** 20% strain + Houston c15 at 08:00 · **T13** 61% strain + Victoria bypass at 08:00

State series: the 31 Houston plant nodes (same as v4). Margin: weakest plant minus 2,901.3 kPa. Period: hourly. Noise sd 1.4 kPa, seeds 20261201–20261210.

The operator settings in `scan_config.json` cover the baseline window, margin and period only. Apply your own tuning settings before Cell 3 if you are not using the engine defaults.

1. **Upload** `scfl_measure.py`, `scfl_ingest_qc.py` and `SCFL_tuning_inputs_T1.zip`.
2. **Check** the engine is the frozen v1.1.0.
3. **Run** ingest QC and the engine on all 130 inputs (about 10 minutes).
4. **Save** fingerprint the outputs and download them."""),
code("""# Cell 1: upload the two engine files and the inputs zip (select all three)
import os, glob, shutil
from google.colab import files
files.upload()
# Fix names the browser changed, e.g. 'scfl measure (1).py' or 'scfl measure.py'
want = {'scfl_measure.py': 'measure', 'scfl_ingest_qc.py': 'ingest', 'SCFL_tuning_inputs_T1.zip': 'tuning_inputs_t1'}
for name, key in want.items():
    if os.path.exists(name):
        continue
    found = [f for f in glob.glob('*') if key in f.lower().replace(' ', '_').replace('_(','(') and f != name
             and f.lower().endswith(name.rsplit('.', 1)[1])]
    if found:
        shutil.copy(sorted(found)[-1], name); print('renamed', sorted(found)[-1], '->', name)
missing = [n for n in want if not os.path.exists(n)]
print('Missing:', missing) if missing else print('All three files present. Run Cell 2.')"""),
code("""# Cell 2: fix any browser-renamed files, then confirm the frozen engine (line endings normalized, as in the freeze)
import hashlib, os, glob, shutil
for name, key in {'scfl_measure.py': 'measure', 'scfl_ingest_qc.py': 'ingest', 'SCFL_tuning_inputs_T1.zip': 'tuning_inputs_t1'}.items():
    if not os.path.exists(name):
        found = [f for f in glob.glob('*') if key in f.lower().replace(' ', '_').replace('_(','(') and f.lower().endswith(name.rsplit('.', 1)[1])]
        if found: shutil.copy(sorted(found)[-1], name); print('renamed', sorted(found)[-1], '->', name)
def h(p): return hashlib.sha256(open(p,'rb').read().replace(b'\\r\\n', b'\\n')).hexdigest()
FROZEN = {'scfl_measure.py': '233d9d9c154639c3e7c4fcc0f57bc2044cfe313e17f89d09bed9610a61e5b020',
          'scfl_ingest_qc.py': '50a9ebc2a860fe0a8b82eb7d716e0dce13432bda89ea0fb5768d535ccb8eaa3b'}
ok = True
for f, want_h in FROZEN.items():
    got = h(f); print(f, 'MATCH' if got == want_h else 'MISMATCH ' + got); ok &= got == want_h
zh = hashlib.sha256(open('SCFL_tuning_inputs_T1.zip','rb').read()).hexdigest()
print('inputs package', 'MATCH' if zh == 'ZIPHASH' else 'MISMATCH ' + zh)
print('Frozen engine confirmed. Run Cell 3.' if ok else 'STOP: engine does not match the freeze.')"""),
code("""# Cell 3: run ingest QC and the engine on every input
import zipfile, subprocess, json
zipfile.ZipFile('SCFL_tuning_inputs_T1.zip').extractall('.')
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
out = 'tuning_readings_T1.zip'
lines = []
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(glob.glob('inputs/INPUT_*/qc_output/*') + glob.glob('inputs/INPUT_*/measure_output/*')):
        if os.path.isfile(f):
            z.write(f); lines.append(f'{hashlib.sha256(open(f,"rb").read()).hexdigest()}  {f}')
open('tuning_fingerprints_T1.txt', 'w').write('\\n'.join(lines) + '\\n')
print(len(lines), 'output files')
files.download(out); files.download('tuning_fingerprints_T1.txt')"""),
]
nb={"cells":cells,"metadata":{"kernelspec":{"name":"python3","display_name":"Python 3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":5}
s=json.dumps(nb,indent=1).replace('ZIPHASH',sys.argv[2])
open(sys.argv[1],'w').write(s)
