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
uv.exe pip install -r requirements.txt
python.exe main.py
