"""Publish only checksum-pinned native installers whose validation jobs passed."""
from pathlib import Path
import json,hashlib,subprocess,tempfile,zipfile
spec=json.loads(Path('.github/release44-assets.json').read_text());out=Path('release');out.mkdir()
for record in spec['assets']:
 job=json.loads(subprocess.check_output(['gh','api',f"repos/caudalio/downloads/actions/jobs/{record['validation_job']}"]))
 assert job['status']=='completed' and job['conclusion']=='success'
 with tempfile.TemporaryDirectory() as tmp:
  archive=Path(tmp)/'artifact.zip'
  with archive.open('wb') as f:subprocess.run(['gh','api',f"repos/caudalio/downloads/actions/artifacts/{record['artifact_id']}/zip"],stdout=f,check=True)
  with zipfile.ZipFile(archive) as z:
   candidates=[x for x in z.namelist() if Path(x).name==record['filename']]
   assert len(candidates)==1
   data=z.read(candidates[0]);assert hashlib.sha256(data).hexdigest()==record['sha256'] and len(data)==record['bytes']
   (out/record['filename']).write_bytes(data)
(out/'CAUDALIO-4.4-SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['filename']+'\n' for r in spec['assets']))
(out/'CAUDALIO-4.4-Validation.txt').write_text(Path('.github/release-caudalio44-validation.txt').read_text())
print('Verified',len(spec['assets']),'native installers. Ready for release.')
