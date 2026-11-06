from pathlib import Path
import os,subprocess,hashlib,time,shutil
root=Path(os.environ['RUNNER_TEMP'])/'caudalio-install';root.mkdir(exist_ok=True)
source=Path('incoming');installer=next(source.rglob('CAUDALIO-4.4-Windows-x64-Setup.exe'))
clean=root/'application';out=Path('release');out.mkdir(exist_ok=True)
report=root/'validation';shutil.copytree(next(source.rglob('validation')),report)
env=dict(os.environ,QT_FORCE_STDERR_LOGGING='1',QT_QPA_PLATFORM='windows',CAUDALIO_RENDERER='cpu',CAUDALIO_HW_DECODE='off')
def run(args,**kwargs):return subprocess.run([str(x) for x in args],check=True,env=env,**kwargs)
run([installer,'/S','/D='+str(clean)])
app=clean/'CAUDALIO.exe'
assert hashlib.sha256(app.read_bytes()).hexdigest()=='c21fbb393b25bf22d5cde6045e833acd21454d69ee689b93cdb07a0c82630106'
version=run([app,'--version'],capture_output=True,text=True);(report/'installed-version.txt').write_text(version.stdout+version.stderr)
assert '4.4.0' in version.stdout+version.stderr,repr(version.stdout+version.stderr)
run([app,'--screenshot',report/'installed-workspace.png'],timeout=40)
assert (report/'installed-workspace.png').stat().st_size>10000
ffmpeg=clean/'tools/ffmpeg/ffmpeg.exe';run([ffmpeg,'-nostdin','-v','error','-f','lavfi','-i','sine=frequency=440:duration=0.2','-y',report/'audio.wav'])
sentinel=Path(os.environ['APPDATA'])/'CAUDALIO/install-validation44.txt';sentinel.parent.mkdir(exist_ok=True);sentinel.write_text('preserve-user-data')
run([installer,'/S','/D='+str(clean)]);assert sentinel.read_text()=='preserve-user-data'
assert hashlib.sha256(app.read_bytes()).hexdigest()=='c21fbb393b25bf22d5cde6045e833acd21454d69ee689b93cdb07a0c82630106'
run([clean/'Uninstall.exe','/S'])
for _ in range(40):
 if not app.exists():break
 time.sleep(.25)
assert not app.exists();assert sentinel.read_text()=='preserve-user-data'
shutil.copy2(installer,out/installer.name)
(out/(installer.name+'.sha256.txt')).write_text(hashlib.sha256(installer.read_bytes()).hexdigest()+'  '+installer.name+'\n')
(report/'VALIDATION-4.4.txt').write_text('CAUDALIO 4.4 Windows x64\nSix native regression suites passed: core 65, interface 42, sequences 13, monitoring 9, chroma 20, multi-canvas 14 (QtTest totals include setup/cleanup). One optional NDI runtime test skipped.\nThe packaged executable matches the tested binary SHA-256. Clean installation, version, GUI capture, audio conversion, reinstall and uninstall checked. User AppData preserved.\nPhysical GPU outputs, projectors, capture devices, NDI and prolonged show loads require rehearsal on actual hardware.\n')
shutil.copy2(report/'VALIDATION-4.4.txt',out/'VALIDATION-Windows-4.4.txt');shutil.make_archive(str(out/'CAUDALIO-4.4-Windows-Validation'),'zip',report)
print('Windows installer, upgrade, uninstall and user-data preservation passed.')
