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
  echo Python 3 was not found. The dashboard was not opened.
  popd
  exit /b 1
)

"%RCC_PYTHON%" %RCC_PYTHON_ARGS% research_control_center\scripts\refresh_all.py
if errorlevel 1 (
  echo RCC dashboard refresh failed. The dashboard was not opened.
  popd
  exit /b 1
)
start "" "research_control_center\dashboard\index.html"
popd
endlocal
