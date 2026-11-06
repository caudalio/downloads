"""Validate and package the checksum-pinned CAUDALIO 4.4 public binaries."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time,urllib.request
work=Path(os.environ['RUNNER_TEMP'])/'caudalio44';work.mkdir(exist_ok=True)
platform=sys.argv[1];spec=json.loads(Path('release44-native-inputs.json').read_text());base='https://caudalio.net'
def run(args,**kw):return subprocess.run([str(x) for x in args],check=True,**kw)
def download(record,destination):
 h=hashlib.sha256()
 with destination.open('wb') as output:
  for part in record['parts']:
   for attempt in range(12):
    try:
     data=subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--retry','3','--max-time','120',base+part['url']])
     assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256']
     output.write(data);h.update(data);break
    except Exception:
     if attempt==11:raise
     time.sleep(5)
 assert destination.stat().st_size==record['bytes'] and h.hexdigest()==record['sha256']
patch=work/'patch.tar.xz';download(spec['patch'],patch);expanded=work/'patch';expanded.mkdir(exist_ok=True)
run(['tar','-xf',patch,'-C',expanded])
production=work/'production';output=work/'deliverables';output.mkdir(exist_ok=True)
if platform=='windows':
 installer=work/'baseline.exe';download(spec['baseline']['windows'],installer)
 run([installer,'/S','/D='+str(production)])
 assert (production/'CAUDALIO.exe').is_file()
 original=[p.relative_to(production) for p in production.rglob('*') if p.is_file() and p.name not in ('Uninstall.exe','NOTICE-4.3.txt','VALIDATION-4.3.txt')]
 shutil.copy2(expanded/'binaries/caudalio/windows/caudalio.exe',production/'CAUDALIO.exe')
 shutil.copy2(expanded/'windows/NOTICE-4.4.txt',production/'NOTICE-4.4.txt');original.append(Path('NOTICE-4.4.txt'))
 testroot=production
 for d in (expanded/'binaries').iterdir():
  if d.name!='caudalio':shutil.copy2(d/'windows'/(d.name+'.exe'),testroot/(d.name+'.exe'))
 shutil.copy2(expanded/'windows/Qt6Test.dll',testroot/'Qt6Test.dll')
else:
 package=work/'baseline.deb';download(spec['baseline']['linux'],package)
 stage=work/'stage';run(['dpkg-deb','-R',package,stage]);shutil.copytree(expanded/'linux-stage',stage,dirs_exist_ok=True)
 deb=output/'CAUDALIO-4.4-Linux-amd64.deb';run(['dpkg-deb','-Zxz','-z6','--root-owner-group','--build',stage,deb]);run(['sudo','dpkg','-i',deb])
 production=Path('/opt/caudalio43');testroot=work/'tests';testroot.mkdir(exist_ok=True)
 for d in (expanded/'binaries').iterdir():
  if d.name!='caudalio':shutil.copy2(d/'noble'/d.name,testroot/d.name);(testroot/d.name).chmod(0o755)
 fixture=Path('/workspace/scratch/75ec0f94b042/sources/CAUDALIO-4.4')
 run(['sudo','mkdir','-p',fixture]);run(['sudo','chown','-R',str(os.getuid())+':'+str(os.getgid()),fixture])
 shutil.copytree(expanded/'fixtures',fixture,dirs_exist_ok=True)
 for name in ('media','examples'):shutil.copytree(production/name,fixture/name,dirs_exist_ok=True)
# The test data includes no proprietary application source.
shutil.copytree(expanded/'fixtures',testroot,dirs_exist_ok=True)
shutil.copytree(expanded/'validation',testroot/'validation',dirs_exist_ok=True)
if platform!='windows':
 for name in ('media','examples'):shutil.copytree(production/name,testroot/name,dirs_exist_ok=True)
evidence=testroot/'validation';captures=evidence/'captures';captures.mkdir(exist_ok=True)
env=dict(os.environ,QT_QPA_PLATFORM='windows' if platform=='windows' else 'xcb',CAUDALIO_RENDERER='cpu',QT_MEDIA_BACKEND='ffmpeg',CAUDALIO_HW_DECODE='off',CAUDALIO_TEST_SOURCE=str(testroot),SCENIQUE_TEST_VIDEO=str(testroot/'tests/media/red.mp4'),CAUDALIO_SEQUENCE_TEST_VIDEO=str(testroot/'tests/media/red-green.mp4'),CAUDALIO_TEST_FIXTURES=str(testroot/'tests/media'),CAUDALIO_PRORES_VIDEO=str(testroot/'tests/media/prores.mov'),CAUDALIO_CHROMA_FIXTURES=str(testroot/'examples/chroma-key-3.8'),CAUDALIO_CAPTURE_DIR=str(captures))
failures=[];checks=json.loads((evidence/'test-commands.json').read_text())
if platform!='windows':checks.append({'name':'opengl','exe':'caudalio_gpu_tests.exe','args':[]})
for test in checks:
 exe=testroot/(test['exe'] if platform=='windows' else test['exe'].removesuffix('.exe'))
 result=subprocess.run([str(exe),*test['args'],'-o',str(evidence/(test['name']+'.txt'))+',txt'],env=env,timeout=300)
 print(test['name'],'exit',result.returncode,flush=True)
 if result.returncode:failures.append(test['name'])
if failures:raise RuntimeError('Failed native checks: '+', '.join(failures))
ffmpeg=production/'tools/ffmpeg/ffmpeg.exe' if platform=='windows' else Path('/usr/bin/ffmpeg')
run([ffmpeg,'-nostdin','-v','error','-i',testroot/'tests/media/red-green.mp4','-frames:v','1','-f','null','-'])
run([ffmpeg,'-nostdin','-v','error','-y','-i',testroot/'tests/media/tone.mp3','-ac','2','-ar','48000','-c:a','pcm_s16le',evidence/'converted.wav'])
if platform=='windows':
 stage=work/'runtime';stage.mkdir(exist_ok=True)
 for relative in original:
  destination=stage/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(production/relative,destination)
 # Evidence and test executables are deliberately outside the shipped runtime.
 installer=output/'CAUDALIO-4.4-Windows-x64-Setup.exe'
 run([sys.executable,expanded/'packaging/make_windows_installer.py',stage,installer])
 clean=work/'clean-install';run([installer,'/S','/D='+str(clean)]);app=clean/'CAUDALIO.exe'
else:app=production/'bin/caudalio'
version=subprocess.run([str(app),'--version'],env=dict(env,QT_QPA_PLATFORM='windows' if platform=='windows' else 'offscreen'),capture_output=True,text=True,check=True)
assert '4.4.0' in version.stdout+version.stderr
(evidence/'installed-version.txt').write_text(version.stdout+version.stderr)
run([app,'--screenshot',captures/'installed-workspace.png'],env=env,timeout=40)
assert (captures/'installed-workspace.png').is_file()
if platform=='windows':
 sentinel=Path(os.environ['APPDATA'])/'CAUDALIO/native-check-sentinel44.txt';sentinel.parent.mkdir(exist_ok=True);sentinel.write_text('preserve-user-data')
 run([clean/'Uninstall.exe','/S']);time.sleep(2);assert sentinel.read_text()=='preserve-user-data'
for p in output.iterdir():
 if p.suffix in ('.exe','.deb'):(output/(p.name+'.sha256.txt')).write_text(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n')
(evidence/'VALIDATION-4.4.txt').write_text('CAUDALIO 4.4 native '+platform+' validation passed.\nCore, interface, timeline, monitoring, chroma and multi-canvas checks passed.\nInstalled version, real GUI capture and media decoding/conversion checked.\n'+('OpenGL checked using Mesa/Xvfb.\n' if platform!='windows' else 'Physical GPU outputs not certified by this CPU-runner validation.\n')+'Physical projectors, external audio, cameras, NDI and prolonged show workloads require rehearsal on the actual hardware.\n')
shutil.copy2(evidence/'VALIDATION-4.4.txt',output/'VALIDATION-4.4.txt')
shutil.make_archive(str(output/'CAUDALIO-4.4-Native-Validation'),'zip',evidence)
print('Native installer and evidence ready:',output,flush=True)
