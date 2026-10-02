@echo off
cd /d "%~dp0"
echo ============================================
echo   Painel de Ocorrencias - iniciando...
echo ============================================
for /f "usebackq delims=" %%i in (`python -c "from core.config import url_local; print(url_local())"`) do set "URL=%%i"
echo.
echo Acesse este computador:  http://localhost:8501
echo Acesse pela rede Wi-Fi:  %URL%
echo.
echo (Deixe esta janela aberta. Para parar, feche-a com Ctrl+C)
echo ============================================
python -m streamlit run app.py
pause
