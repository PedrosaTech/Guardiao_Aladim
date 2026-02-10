# Fixtures para deploy

Este diretório contém os dados iniciais exportados do banco local para carregar no ambiente de produção (Render) na primeira vez.

## Exportar dados (ambiente local)

Com o banco SQLite populado, execute **uma vez** na raiz do projeto:

```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -e sessions.Session --indent 2 -o data/fixtures/initial_data.json
```

Ou use o script (na raiz do projeto):

- **PowerShell:** `.\scripts\export_fixtures.ps1`
- **Bash (WSL/Linux):** `./scripts/export_fixtures.sh`

Depois, commite o arquivo `initial_data.json` no Git para que o deploy no Render carregue esses dados no PostgreSQL na primeira vez.

## Uso em produção

O comando `load_initial_data` (executado no Release Command do Render) carrega `initial_data.json` apenas se o banco ainda estiver vazio (nenhum usuário), evitando duplicar dados em deploys seguintes.
