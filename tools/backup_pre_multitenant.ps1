# Backup local antes de mudancas grandes (ex.: multi-tenant).
# Uso (PowerShell na raiz do projeto):
#   .\tools\backup_pre_multitenant.ps1
# Opcional: prefixo
#   .\tools\backup_pre_multitenant.ps1 -Label "antes_migracao_x"

param(
    [string]$Label = "pre_multi_tenant"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$DestDir = Join-Path (Join-Path $Root "backups") "${Label}_${Stamp}"

New-Item -ItemType Directory -Path $DestDir -Force | Out-Null

# 1) Cópia do SQLite local (dev comum)
$DbSqlite = Join-Path $Root "db.sqlite3"
if (Test-Path $DbSqlite) {
    Copy-Item -Path $DbSqlite -Destination (Join-Path $DestDir "db.sqlite3.bak")
    Write-Host "OK: db.sqlite3 -> $DestDir\db.sqlite3.bak"
} else {
    Write-Host "Aviso: db.sqlite3 nao encontrado (talvez PostgreSQL via DATABASE_URL)."
}

# 2) PostgreSQL: se pg_dump estiver no PATH e DATABASE_URL estiver definida
$dbUrl = [Environment]::GetEnvironmentVariable("DATABASE_URL", "Process")
if (-not $dbUrl) { $dbUrl = [Environment]::GetEnvironmentVariable("DATABASE_URL", "User") }

if ($dbUrl -and (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    $DumpFile = Join-Path $DestDir "postgres_dump.sql"
    # URI normalmente aceita pg_dump com DATABASE_URL em variavel PGURL
    $env:PGPASSWORD = $null
    & pg_dump --dbname=$dbUrl -F p -f $DumpFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: PostgreSQL dump -> $DumpFile"
    } else {
        Write-Host "Erro: pg_dump falhou (codigo $LASTEXITCODE)."
    }
} elseif ($dbUrl) {
    Write-Host "Aviso: DATABASE_URL definida mas pg_dump nao encontrado. Faca dump manualmente."
    Set-Location $Root
    $head = git rev-parse HEAD 2>$null
    $readme = @(
        "Backup parcial gerado em $(Get-Date -Format o)",
        "",
        "- SQLite: copiado se existir db.sqlite3 na raiz.",
        "- PostgreSQL: instale client tools (pg_dump no PATH) e rode, por exemplo:",
        '  pg_dump $env:DATABASE_URL -F c -f backup.dump',
        "  ou use snapshot no painel do Render.",
        "",
        "Commit Git de referencia: $head"
    ) -join "`n"
    Set-Content -Path (Join-Path $DestDir "LEIA-ME.txt") -Encoding UTF8 -Value $readme
}

# 3) Registro do commit atual
Set-Location $Root
$commit = git rev-parse HEAD 2>$null
$meta = @"
label=$Label
created_utc=$(Get-Date -Format o)
git_commit=$commit
"@
Set-Content -Path (Join-Path $DestDir "BACKUP_META.txt") -Value $meta -Encoding UTF8
Write-Host "Meta: $DestDir\BACKUP_META.txt"
Write-Host "Backup concluido em: $DestDir"
