#!/data/data/com.termux/files/usr/bin/bash
# Script para instalar y correr ReelCleaner 100% nativo dentro de Android con Termux
set -e

echo "📦 Instalando dependencias en Termux..."
pkg update -y
pkg install -y python ffmpeg git

echo "📦 Instalando paquetes de Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🚀 Iniciando ReelCleaner en tu celular..."
python run.py
