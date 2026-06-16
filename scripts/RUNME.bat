if /I "%~nx0"=="RUNME.bat" (
    echo "No pending updates"

    if exist ".\RUNME.tmp.bat" (
        del ".\RUNME.tmp.bat"
    )
) else (
    echo "An update is pending"

    if exist ".tmp_update" (
        robocopy ".tmp_update" . /E /MOVE
        .\RUNME.bat
    )
)

cd casual-preloader
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv self update
uv run python main.py %*
