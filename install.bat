@echo off
echo ========================================
echo   Ghost-Bridge - Instalador
echo ========================================
echo.

echo [1/3] Verificando Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.10+ de https://python.org
    pause
    exit /b 1
)

echo.
echo [2/3] Instalando dependencias...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] Algumas dependencias podem ter falhado.
    echo Isso e normal para pyaudio no Windows.
    echo.
    echo Para pyaudio, tente:
    echo   pip install pipwin
    echo   pipwin install pyaudio
    echo.
)

echo.
echo [3/3] Configurando ambiente...
if not exist .env (
    copy .env.example .env
    echo Arquivo .env criado. Edite com suas credenciais.
) else (
    echo Arquivo .env ja existe.
)

echo.
echo ========================================
echo   Instalacao concluida!
echo ========================================
echo.
echo Para testar:
echo   python demo.py
echo.
echo Para rodar o agente:
echo   python agent.py
echo.
echo Para ver comandos:
echo   python agent.py --test !help
echo.
pause
