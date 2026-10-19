@echo off
setlocal
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VS_PATH=%%i"
if not defined VS_PATH exit /b 1
call "%VS_PATH%\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b 1
cl /nologo /O2 /MT "%GITHUB_WORKSPACE%\scripts\win7-codex\delayhook-test.c" /Fe"%RUNNER_TEMP%\codex-delayhook-test.exe" /Fo"%RUNNER_TEMP%\codex-delayhook-test.obj"
if errorlevel 1 exit /b 1
"%RUNNER_TEMP%\codex-delayhook-test.exe"
if errorlevel 1 exit /b 1
cl /nologo /c /O2 /MT "%GITHUB_WORKSPACE%\scripts\win7-codex\delayhook.c" /Fo"%CSGCLAW_WIN7_DELAYHOOK_OBJECT%"
if errorlevel 1 exit /b 1
cd /d "%GITHUB_WORKSPACE%\codex-source\codex-rs"
cargo +1.95.0 build --locked --profile dev-small --target x86_64-win7-windows-msvc -p codex-cli --bin codex
exit /b %ERRORLEVEL%
