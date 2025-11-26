#!/bin/bash
# Script de inicialização do Totem de Fotos - /opt/Totem/

echo "=========================================="
echo "  Iniciando Totem de Fotos (VENV)"
echo "  Diretório: /opt/Totem/"
echo "  Data: $(date)"
echo "=========================================="

# Navegar para o diretório do Totem
cd /opt/Totem

# Verificar se o arquivo main.py existe
if [ ! -f "main.py" ]; then
    echo "ERRO: Arquivo main.py não encontrado em /opt/Totem/"
    exit 1
fi

# 1. Verifica se o VENV existe e tenta recuperar se não existir
if [ ! -d "venv" ]; then
    echo "⚠️ Ambiente virtual não encontrado. Criando..."
    sudo apt install -y python3-venv
    python3 -m venv --system-site-packages venv
    echo "📦 Instalando dependências..."
    ./venv/bin/pip install selenium webdriver-manager
fi

# Ajustar permissões
if [ ! -r "main.py" ]; then
    sudo chmod +r main.py
fi

# Libera acesso ao Xhost (importante para o Chrome abrir a tela gráfica)
xhost +local: > /dev/null 2>&1

echo "Executando o totem de fotos..."
echo "Pressione Ctrl+C no terminal para parar ou ESC no aplicativo"

# --- AQUI ESTÁ O SEGREDO ---
# Usa o ./venv/bin/python3 em vez de apenas python3
sudo ./venv/bin/python3 main.py

echo "=========================================="
echo "  Totem de Fotos finalizado"
echo "  Data: $(date)"
echo "=========================================="
