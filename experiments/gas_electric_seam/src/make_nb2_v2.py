import json, sys
def md(s): return {"cell_type":"markdown","metadata":{},"source":s}
def code(s): return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s}
cells=[
md("""# SCFL Gas–Electric Seam: Preliminary Run v2 (gas-only, exploratory, not blind)
Upstream Coherence Measurement Stratum (UCMS) | Ronald L. Brogdon | ORCID: https://orcid.org/0009-0009-0507-2971

Frozen engine v1.1.0 (https://doi.org/10.5281/zenodo.23839571). GasTranSim.jl on the Texas A&M combined electric–gas case, started from a 76-hour no-shortfall spin-up (settling below 0.06 kPa/h).

Four inputs, 8 h each at 5-min steps, 19 north Texas plant-node pressures (kPa) as state series:
- **INPUT_control_clean / INPUT_shortfall_clean:** simulator output as is.
- **INPUT_control_noise / INPUT_shortfall_noise:** plus declared sensor noise, sd 1.4 kPa (Rosemount 3051P reference accuracy 0.04% of a 0–1,500 psig span, read as 3-sigma), seed 20261124, same noise in control and shortfall.

Shortfall: 12 north Texas processing plants cut 50%, ramp 01:00–03:00, held. Margin: weakest plant pressure minus minimum delivery pressure (2.8 MPag = 2,901.3 kPa abs). Fixed SHIFT baseline 00:00–00:55, search from 01:00. North Texas is excluded from the sealed test.

1. **Upload** `scfl_measure.py`, `scfl_ingest_qc.py` and `SCFL_prelim_gas_inputs_v2.zip`.
2. **Check** the engine is the frozen v1.1.0.
3. **Run** ingest QC and the engine on all four inputs.
4. **Save** fingerprint the outputs and download them."""),
code("""# Cell 1: upload the two engine files and the inputs zip (select all three)
import os, glob, shutil
from google.colab import files
files.upload()
# Fix names the browser changed, e.g. 'scfl measure (1).py' or 'scfl measure.py'
want = {'scfl_measure.py': 'measure', 'scfl_ingest_qc.py': 'ingest', 'SCFL_prelim_gas_inputs_v2.zip': 'inputs_v2'}
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
for name, key in {'scfl_measure.py': 'measure', 'scfl_ingest_qc.py': 'ingest', 'SCFL_prelim_gas_inputs_v2.zip': 'inputs_v2'}.items():
    if not os.path.exists(name):
        found = [f for f in glob.glob('*') if key in f.lower().replace(' ', '_').replace('_(','(') and f.lower().endswith(name.rsplit('.', 1)[1])]
        if found: shutil.copy(sorted(found)[-1], name); print('renamed', sorted(found)[-1], '->', name)
def h(p): return hashlib.sha256(open(p,'rb').read().replace(b'\\r\\n', b'\\n')).hexdigest()
FROZEN = {'scfl_measure.py': '233d9d9c154639c3e7c4fcc0f57bc2044cfe313e17f89d09bed9610a61e5b020',
          'scfl_ingest_qc.py': '50a9ebc2a860fe0a8b82eb7d716e0dce13432bda89ea0fb5768d535ccb8eaa3b'}
ok = True
for f, want_h in FROZEN.items():
    got = h(f); print(f, 'MATCH' if got == want_h else 'MISMATCH ' + got); ok &= got == want_h
zh = hashlib.sha256(open('SCFL_prelim_gas_inputs_v2.zip','rb').read()).hexdigest()
print('inputs package', 'MATCH' if zh == 'ZIPHASH' else 'MISMATCH ' + zh)
print('Frozen engine confirmed. Run Cell 3.' if ok else 'STOP: engine does not match the freeze.')"""),
code("""# Cell 3: run ingest QC and the engine on both inputs
import zipfile, subprocess, json
zipfile.ZipFile('SCFL_prelim_gas_inputs_v2.zip').extractall('.')
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
    print(d, 'engine:', 'RUN' if r.returncode == 0 else 'ENGINE ERROR: ' + (r.stderr or r.stdout)[-600:])"""),
code("""# Cell 4: fingerprint the outputs and download them
import os, glob, zipfile, hashlib
from google.colab import files
out = 'prelim_gas_readings_v2.zip'
lines = []
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(glob.glob('inputs/INPUT_*/qc_output/*') + glob.glob('inputs/INPUT_*/measure_output/*')):
        if os.path.isfile(f):
            z.write(f); lines.append(f'{hashlib.sha256(open(f,"rb").read()).hexdigest()}  {f}')
open('prelim_gas_fingerprints_v2.txt', 'w').write('\\n'.join(lines) + '\\n')
print(len(lines), 'output files')
files.download(out); files.download('prelim_gas_fingerprints_v2.txt')"""),
]
nb={"cells":cells,"metadata":{"kernelspec":{"name":"python3","display_name":"Python 3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":5}
s=json.dumps(nb,indent=1).replace('ZIPHASH',sys.argv[2])
open(sys.argv[1],'w').write(s)
