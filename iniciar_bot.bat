@echo off
cd /d "C:\Users\Ana Rita\Desktop\Bot\vagas"

echo === Atualizando repositorio ===
git pull

echo === Iniciando bot (sem travar o CMD) ===
start /b "" python vaga_bot_pc.py

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
