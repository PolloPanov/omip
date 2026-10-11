; Instalador de OMIP para Windows
#define MyAppName "OMIP"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PolloPanov"

[Setup]
AppId={{B1A56A0D-0B4A-4C3A-8C7A-2026A001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\OMIP
DefaultGroupName=OMIP
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=OMIP-Setup
SetupIconFile=..\omip.ico
UninstallDisplayIcon={app}\Generar_Graficas_OMIP.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
Source: "..\dist\Generar_Graficas_OMIP.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\omip_futuros_365d_*.csv"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\OMIP"; Filename: "{app}\Generar_Graficas_OMIP.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\OMIP"; Filename: "{app}\Generar_Graficas_OMIP.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Generar_Graficas_OMIP.exe"; Description: "Abrir OMIP ahora"; Flags: postinstall nowait skipifsilent
