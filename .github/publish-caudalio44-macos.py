"""Publish only the native Mac installer whose exact validation job passed."""
from pathlib import Path
import json,hashlib,subprocess,tempfile,zipfile
spec=json.loads(Path('.github/release44-macos-asset.json').read_text())
job=json.loads(subprocess.check_output(['gh','api',f"repos/caudalio/downloads/actions/jobs/{spec['validation_job']}"]))
assert job['status']=='completed' and job['conclusion']=='success'
release=json.loads(subprocess.check_output(['gh','api','repos/caudalio/downloads/releases/tags/v4.4.0']))
assert not release['draft'] and not release['prerelease']
prior=json.loads(Path('.github/release44-assets.json').read_text())['assets']
for record in prior:
 asset=next(a for a in release['assets'] if a['name']==record['filename'])
 assert asset['size']==record['bytes'] and asset['digest']=='sha256:'+record['sha256']
assert not any(a['name']==spec['filename'] for a in release['assets'])
out=Path('release');out.mkdir()
with tempfile.TemporaryDirectory() as tmp:
 archive=Path(tmp)/'mac.zip'
 with archive.open('wb') as f:subprocess.run(['gh','api',f"repos/caudalio/downloads/actions/artifacts/{spec['artifact_id']}/zip"],stdout=f,check=True)
 with zipfile.ZipFile(archive) as z:
  matches=[n for n in z.namelist() if Path(n).name==spec['filename']];assert len(matches)==1
  data=z.read(matches[0]);assert len(data)==spec['bytes'] and hashlib.sha256(data).hexdigest()==spec['sha256']
  (out/spec['filename']).write_bytes(data)
(out/'CAUDALIO-4.4-SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['filename']+'\n' for r in prior+[spec]))
(out/'CAUDALIO-4.4-Validation.txt').write_text(Path('.github/release-caudalio44-validation.txt').read_text())
print('Exact Mac installer verified; existing Linux and Windows installers preserved.')
