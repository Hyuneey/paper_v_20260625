@echo off
setlocal
pushd "%~dp0..\.."

set "RCC_PYTHON="
set "RCC_PYTHON_ARGS="
where py >nul 2>nul
if not errorlevel 1 (
  set "RCC_PYTHON=py"
  set "RCC_PYTHON_ARGS=-3"
)
if not defined RCC_PYTHON (
  where python >nul 2>nul
  if not errorlevel 1 set "RCC_PYTHON=python"
)
if not defined RCC_PYTHON (
  if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "RCC_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  )
)
if not defined RCC_PYTHON (
  echo [RCC] Python 3를 찾지 못했습니다. Dashboard를 열지 않습니다.
  popd
  exit /b 1
)

"%RCC_PYTHON%" %RCC_PYTHON_ARGS% research_control_center\scripts\refresh_all.py
if errorlevel 1 (
  echo [RCC] Registry 검증 또는 Dashboard 빌드가 실패했습니다. Dashboard를 열지 않습니다.
  popd
  exit /b 1
)
echo [RCC] Registry 검증과 Dashboard V2 빌드가 완료되었습니다.
echo [RCC] Pilot V1 화면을 엽니다. 과학 실행은 수행하지 않았습니다.
start "" "research_control_center\dashboard\index.html"
popd
endlocal
