#!/bin/bash
# Script de inicialização do Totem de Fotos - /opt/Totem/

echo "=========================================="
echo "  Iniciando Totem de Fotos"
echo "  Diretório: /opt/Totem/"
echo "  Data: $(date)"
echo "=========================================="

# Navegar para o diretório do Totem
cd /opt/Totem

# Verificar se o arquivo main.py existe
if [ ! -f "main.py" ]; then
    echo "ERRO: Arquivo main.py não encontrado em /opt/Totem/"
    echo "Verifique se o arquivo foi copiado corretamente."
    exit 1
fi

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 não está instalado"
    echo "Instale com: sudo apt install python3"
    exit 1
fi

# Verificar permissões
if [ ! -r "main.py" ]; then
    echo "Ajustando permissões..."
    sudo chmod +r main.py
fi

echo "Executando o totem de fotos..."
echo "Pressione Ctrl+C no terminal para parar ou ESC no aplicativo"

# Executar o aplicativo Python
sudo python3 main.py

echo "=========================================="
echo "  Totem de Fotos finalizado"
echo "  Data: $(date)"
echo "=========================================="
