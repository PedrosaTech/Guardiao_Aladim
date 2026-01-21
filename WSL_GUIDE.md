# Guia WSL - Guardião Aladin

## 🐧 Como entrar no WSL com venv ativado

### Opção 1: Usando o script (recomendado)
```bash
wsl bash entrar_wsl.sh
```

### Opção 2: Manualmente
```bash
wsl
cd /mnt/c/Users/Dell/Guardiao_Aladin
source venv/bin/activate
```

### Opção 3: Comando único
```bash
wsl bash -c "cd /mnt/c/Users/Dell/Guardiao_Aladin && source venv/bin/activate && bash"
```

## ✅ Verificação

Após entrar, você deve ver:
```
(venv) usuario@hostname:/mnt/c/Users/Dell/Guardiao_Aladin$
```

## 🚀 Comandos Úteis no WSL

### Verificar sistema
```bash
python manage.py check
```

### Criar migrações
```bash
python manage.py makemigrations
```

### Aplicar migrações
```bash
python manage.py migrate
```

### Criar superusuário
```bash
python manage.py createsuperuser
```

### Criar grupos de permissões
```bash
python manage.py setup_roles
```

### Executar servidor
```bash
python manage.py runserver
```
Acesse: http://localhost:8000

### Executar testes
```bash
pytest
```

### Shell Django
```bash
python manage.py shell
```

## 📝 Notas

- O venv está em `/mnt/c/Users/Dell/Guardiao_Aladin/venv`
- O projeto está em `/mnt/c/Users/Dell/Guardiao_Aladin`
- O banco SQLite será criado no mesmo diretório (`db.sqlite3`)
- Para usar PostgreSQL, configure `DATABASE_URL` no `.env`

## 🔧 Troubleshooting

### Se o venv não ativar:
```bash
# Recriar venv (se necessário)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Se houver problemas de permissão:
```bash
# Dar permissão de execução
chmod +x entrar_wsl.sh
```

### Verificar Python no venv:
```bash
which python
# Deve mostrar: /mnt/c/Users/Dell/Guardiao_Aladin/venv/bin/python
```

