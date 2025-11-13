@echo off
cd /d "C:\Job" 

:: Atualiza repositório
git pull

:: Inicia o bot (sem travar o .bat)
start /b "" python vaga_bot_pc.py

:: Aguarda um tempo pro bot fazer a busca (opcional)
timeout /t 30 >nul

:: Envia alterações pro GitHub
git add .
git commit -m "Atualização automática de vagas"
git push
