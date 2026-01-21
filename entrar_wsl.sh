#!/bin/bash
# Script para entrar no WSL com venv ativado

cd /mnt/c/Users/Dell/Guardiao_Aladin
source venv/bin/activate
echo "✅ Ambiente virtual ativado!"
echo "📁 Diretório: $(pwd)"
echo "🐍 Python: $(python --version)"
echo ""
echo "Comandos úteis:"
echo "  python manage.py runserver    - Iniciar servidor"
echo "  python manage.py makemigrations - Criar migrações"
echo "  python manage.py migrate       - Aplicar migrações"
echo "  pytest                         - Executar testes"
echo "  python manage.py shell         - Abrir shell Django"
echo ""
exec bash

