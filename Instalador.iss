; ================================================================
; Script do Inno Setup - Gerenciador de Capas e Metadados para MP3
; Gera um instalador .exe profissional em portugues
; ================================================================

#define MyAppName "Gerenciador de Capas e Metadados para MP3"
#define MyAppShortName "Gerenciador de Capas"
#define MyAppVersion "1.0"
#define MyAppPublisher "Kdu5411"
#define MyAppExeName "GerenciadorCapas.exe"

[Setup]
AppId={{8E3A4C21-9F1B-4D5E-A3C7-B2D8E9F0A1B2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\GerenciadorCapas
DefaultGroupName={#MyAppShortName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Instalador_GerenciadorCapas_v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableWelcomePage=no
DisableDirPage=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Area de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "dist\GerenciadorCapas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppShortName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppShortName} agora"; Flags: nowait postinstall skipifsilent