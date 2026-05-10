@echo off
setlocal enabledelayedexpansion

:: Show loading prompt to confirm script is running
echo Searching for Git repository... (max 10 parent directories)
echo.

:: Auto-detect Git project root (with depth limit)
call :FindGitRoot "%~dp0"

:: Clear loading screen and show main menu
cls
goto MainMenu

:MainMenu
echo.
echo ================= Git Quick Operations Menu =================
if defined GIT_ROOT (
    echo Current Git Project Path: !GIT_ROOT!
) else (
    echo No active Git project path set.
)
echo.
echo 1. git pull
echo 2. git add .
echo 3. git commit (enter commit message)
echo 4. git push
echo 5. git status
echo 6. Set custom project path (manual input)
echo 7. Clear current project path
echo 8. Exit
echo 9. [Quick Push] Add + Commit(Time) + Push  <-- 新增
echo.
set /p choice=Enter your selection (1-9): 

if "%choice%"=="1" goto GitPull
if "%choice%"=="2" goto GitAdd
if "%choice%"=="3" goto GitCommit
if "%choice%"=="4" goto GitPush
if "%choice%"=="5" goto GitStatus
if "%choice%"=="6" goto SetCustomPath
if "%choice%"=="7" goto ClearPath
if "%choice%"=="8" goto ExitScript
if "%choice%"=="9" goto QuickPush

echo Invalid option. Please try again.
timeout /t 2 /nobreak >nul
goto MainMenu

:: --- 新增的一键推送逻辑 ---
:QuickPush
if not defined GIT_ROOT (
    echo Error: No active Git project path set.
    pause
    goto MainMenu
)
cd /d "!GIT_ROOT!"

:: 获取当前时间并格式化 (例如: 2026-04-18 15:30)
set "t=%date% %time%"
set "timestamp=!t:~0,16!"

echo.
echo === Starting Quick Push ===
echo Current Time: !timestamp!
echo.

echo Step 1: git add .
git add .

echo.
echo Step 2: git commit -m "Backup: !timestamp!"
git commit -m "Backup: !timestamp!"

echo.
echo Step 3: git push
git push
if errorlevel 1 (
    echo.
    echo [INFO] Direct push failed, retrying with proxy 127.0.0.1:7890...
    git push -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890
)

echo.
echo === Quick Push Completed ===
pause
goto MainMenu
:: -----------------------

:GitPull
if not defined GIT_ROOT (
    echo Error: No active Git project path set. Use option 6 to specify one.
    pause
    goto MainMenu
)
cd /d "!GIT_ROOT!"
echo.
echo Executing: git pull (in !GIT_ROOT!)
git pull
echo.
pause
goto MainMenu

:GitAdd
if not defined GIT_ROOT (
    echo Error: No active Git project path set. Use option 6 to specify one.
    pause
    goto MainMenu
)
cd /d "!GIT_ROOT!"
echo.
echo Executing: git add . (in !GIT_ROOT!)
git add .
echo.
pause
goto MainMenu

:GitCommit
if not defined GIT_ROOT (
    echo Error: No active Git project path set. Use option 6 to specify one.
    pause
    goto MainMenu
)
cd /d "!GIT_ROOT!"
echo.
set /p commit_msg=Enter commit message: 
if "!commit_msg!"=="" (
    echo Error: Commit message cannot be empty.
    pause
    goto MainMenu
)
echo Executing: git commit -m "!commit_msg!" (in !GIT_ROOT!)
git commit -m "!commit_msg!"
echo.
pause
goto MainMenu

:GitPush
if not defined GIT_ROOT (
    echo Error: No active Git project path set. Use option 6 to specify one.
    pause
    goto MainMenu
)
cd /d "!GIT_ROOT!"
echo.
echo Executing: git push (in !GIT_ROOT!)
git push
if errorlevel 1 (
    echo.
    echo [INFO] Direct push failed, retrying with proxy 127.0.0.1:7890...
    git push -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890
)
echo.
pause
goto MainMenu

:GitStatus
if not defined GIT_ROOT (
    echo Error: No active Git project path set. Use option 6 to specify one.
    pause
    goto MainMenu
)
cd /d "!GIT_ROOT!"
echo.
echo Executing: git status (in !GIT_ROOT!)
git status
echo.
pause
goto MainMenu

:SetCustomPath
echo.
set /p custom_path=Enter full Git project path (e.g., D:\Projects\MyRepo): 
:: Trim trailing backslash if exists
if "!custom_path:~-1!"=="\" set "custom_path=!custom_path:~0,-1!"
:: Verify path exists and contains .git folder
if not exist "!custom_path!" (
    echo Error: Path "!custom_path!" does not exist.
    pause
    goto MainMenu
)
if not exist "!custom_path!\.git" (
    echo Error: Path "!custom_path!" is not a Git repository (no .git folder found).
    pause
    goto MainMenu
)
:: Set as active project path
set "GIT_ROOT=!custom_path!"
echo Success: Active Git project path updated to: !GIT_ROOT!
pause
goto MainMenu

:ClearPath
if not defined GIT_ROOT (
    echo Info: No active Git project path to clear.
    pause
    goto MainMenu
)
set "GIT_ROOT="
echo Success: Current Git project path has been cleared.
pause
goto MainMenu

:ExitScript
echo.
echo Script exited successfully.
exit /b

:: Fixed Function: Find Git root with depth limit (prevents infinite loops)
:FindGitRoot
set "dir=%~1"
set "max_depth=10"
set "current_depth=0"

:FindLoop
if !current_depth! gtr !max_depth! (
    set "GIT_ROOT="
    exit /b
)
if exist "%dir%\.git" (
    set "GIT_ROOT=%dir%"
    if "!GIT_ROOT:~-1!"=="\" set "GIT_ROOT=!GIT_ROOT:~0,-1!"
    exit /b
)
if "%dir:~1%"==":\" (
    set "GIT_ROOT="
    exit /b
)
for %%F in ("%dir%") do set "dir=%%~dpF"
set "dir=!dir:~0,-1!"
set /a current_depth+=1
goto FindLoop