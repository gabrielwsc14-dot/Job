@echo off
cd /d "C:\Users\Ana Rita\Desktop\Bot\vagas"

echo === Atualizando repositorio ===
git pull

echo === Encerrando instancias antigas do bot ===
taskkill /IM python.exe /F >nul 2>&1

echo === Iniciando vaga_bot_pc.py ===
start "" python vaga_bot_pc.py

echo === Iniciando monitor_bot_pc.py ===
start "" python monitor_bot.py

echo Aguardando o bot gerar o vagas.json...
timeout /t 180 >nul

echo === Enviando atualizacoes para o GitHub ===
git add .

:: Garante que data/hora nao tenha caracteres proibidos
set DATA=%DATE:/=-%
set HORA=%TIME::=-%
set HORA=%HORA: =0%

git commit -m "Auto-update %DATA% %HORA%"
git push
