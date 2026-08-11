@echo off
echo Starting Dialysis Automation Web App...
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Install streamlit if needed
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Installing Streamlit...
    pip install streamlit
)

REM Get and display IP
echo.
echo ================================
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    echo Access URL: http://%%a:8501
)
echo ================================
echo.
echo Keep this window open!
echo.

REM Start the app
streamlit run app.py --server.address 0.0.0.0

pause
