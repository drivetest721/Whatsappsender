@echo off

echo Creating virtual environment...

python -m venv envAutomation

echo Virtual environment created successfully.

echo Activating environment...

call envAutomation\Scripts\activate.bat

echo Environment activated successfully.

echo Installing playwright Library...

pip install playwright

@REM Download browser binaries
set "PLAYWRIGHT_BROWSERS_PATH=envAutomation\Lib\site-packages\playwright\driver\package\.local-browsers\"
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    mkdir "%PLAYWRIGHT_BROWSERS_PATH%"
)

playwright install

echo Project-required modules installed successfully.

echo Environment is ready to be used for envAutomation.

pause

exit /b