# Backups locais

Esta pasta guarda cópias do banco **apenas na sua máquina**. Os arquivos grandes (`.bak`, `.sql`, `.dump`) **não vão para o Git** — veja [.gitignore](../.gitignore).

## Gerar backup antes do multi-tenant

Na raiz do projeto, no PowerShell:

```powershell
.\tools\backup_pre_multitenant.ps1
```

Isso cria uma subpasta `backups/pre_multi_tenant_AAAAMMDD_HHMMSS/` com:

- `db.sqlite3.bak` — se existir `db.sqlite3` na raiz (desenvolvimento típico)
- `postgres_dump.sql` — se `DATABASE_URL` estiver definida e `pg_dump` estiver no PATH
- `BACKUP_META.txt` — data e hash do commit Git atual

## PostgreSQL (Render / produção)

Use o backup do provedor (snapshot) ou:

```bash
pg_dump "$DATABASE_URL" -F c -f backup.dump
```

## Restaurar SQLite (exemplo)

Copie o `.bak` de volta para a raiz como `db.sqlite3` (com o servidor Django parado).
