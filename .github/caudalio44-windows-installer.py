#!/usr/bin/env python3
"""Package an already deployed, dependency-audited runtime using NSIS 3.
Usage: python make_windows_installer.py RUNTIME_DIR OUTPUT_EXE
No installation or publishing is performed by this script.
"""
from pathlib import Path
import sys,subprocess,tempfile
app=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve()
assert (app/'CAUDALIO.exe').is_file()
def quote(s):return str(s).replace('$','$$').replace('"','$\\"')
files=sorted(p.relative_to(app) for p in app.rglob('*') if p.is_file())
dirs=sorted((p.relative_to(app) for p in app.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True)
cleanup='\n'.join('  Delete "$INSTDIR\\'+quote(str(p).replace('/','\\'))+'"' for p in files)
cleanup+='\n'+ '\n'.join('  RMDir "$INSTDIR\\'+quote(str(p).replace('/','\\'))+'"' for p in dirs)
script=r'''Unicode true
!include "MUI2.nsh"
!include "x64.nsh"
Name "CAUDALIO 4.4"
OutFile "@OUTPUT@"
InstallDir "$LOCALAPPDATA\Programs\CAUDALIO-4.4"
InstallDirRegKey HKCU "Software\CAUDALIO43" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "@LICENSE@"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "Spanish"
Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "CAUDALIO requires 64-bit Windows."
    Abort
  ${EndIf}
FunctionEnd
Section "CAUDALIO 4.4"
  SetOutPath "$INSTDIR"
  File /r "@FILES@"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  Delete "$SMPROGRAMS\CAUDALIO 4.3\CAUDALIO 4.3.lnk"
  Delete "$SMPROGRAMS\CAUDALIO 4.3\Notice.lnk"
  RMDir "$SMPROGRAMS\CAUDALIO 4.3"
  CreateDirectory "$SMPROGRAMS\CAUDALIO 4.4"
  CreateShortcut "$SMPROGRAMS\CAUDALIO 4.4\CAUDALIO 4.4.lnk" "$INSTDIR\CAUDALIO.exe"
  CreateShortcut "$SMPROGRAMS\CAUDALIO 4.4\Notice.lnk" "$INSTDIR\NOTICE-4.4.txt"
  WriteRegStr HKCU "Software\CAUDALIO43" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAUDALIO43" "DisplayName" "CAUDALIO 4.4"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAUDALIO43" "DisplayVersion" "4.4.0"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAUDALIO43" "DisplayIcon" "$INSTDIR\CAUDALIO.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAUDALIO43" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAUDALIO43" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAUDALIO43" "NoRepair" 1
SectionEnd
Section "Uninstall"
@CLEANUP@
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\CAUDALIO 4.4\CAUDALIO 4.4.lnk"
  Delete "$SMPROGRAMS\CAUDALIO 4.4\Notice.lnk"
  RMDir "$SMPROGRAMS\CAUDALIO 4.4"
  DeleteRegKey HKCU "Software\CAUDALIO43"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAUDALIO43"
SectionEnd
'''.replace('@OUTPUT@',quote(output)).replace('@LICENSE@',quote(app/'LICENSE')).replace('@FILES@',quote(app/'*')).replace('@CLEANUP@',cleanup)
output.parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='caudalio-installer-') as temporary:
    path=Path(temporary)/'installer.nsi';path.write_text(script,encoding='utf-8')
    subprocess.run(['makensis','-V3',str(path)],check=True)
print(output)
