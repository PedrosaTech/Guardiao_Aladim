# Guia Rápido - Guardião Aladin

## ✅ Status do Projeto

O projeto está configurado e pronto para uso! Todos os módulos foram criados e as migrações foram executadas.

## 🚀 Acessos

### Admin do Django
- URL: http://localhost:8000/admin/
- Use o superusuário criado para acessar

### API REST
- Base URL: http://localhost:8000/api/v1/
- Documentação interativa: http://localhost:8000/api/v1/ (quando autenticado)

### PDV
- URL: http://localhost:8000/pdv/
- Requer login e sessão de caixa aberta

## 📋 Endpoints da API

### Core
- `GET /api/v1/empresas/` - Listar empresas
- `GET /api/v1/lojas/` - Listar lojas

### Pessoas
- `GET /api/v1/clientes/` - Listar clientes
- `GET /api/v1/fornecedores/` - Listar fornecedores

### Produtos
- `GET /api/v1/categorias-produto/` - Listar categorias
- `GET /api/v1/produtos/` - Listar produtos

### Estoque
- `GET /api/v1/locais-estoque/` - Listar locais
- `GET /api/v1/estoque-atual/` - Consultar estoque atual
- `GET /api/v1/movimentos-estoque/` - Histórico de movimentações

### Vendas
- `GET /api/v1/pedidos-venda/` - Listar pedidos
- `GET /api/v1/condicoes-pagamento/` - Listar condições

### PDV
- `GET /api/v1/caixas-sessao/` - Sessões de caixa
- `GET /api/v1/pagamentos/` - Pagamentos

### CRM
- `GET /api/v1/leads/` - Listar leads
- `GET /api/v1/interacoes-crm/` - Interações

## 🔐 Grupos de Usuários Criados

Execute `python manage.py setup_roles` para criar os grupos:
- **ADMINISTRADOR** - Acesso total
- **GERENTE** - Acesso amplo
- **CAIXA** - Operador de caixa
- **ESTOQUISTA** - Gestão de estoque
- **VENDEDOR_EXTERNO** - Vendas externas
- **FINANCEIRO** - Módulo financeiro
- **FISCAL** - Módulo fiscal

## 📝 Próximos Passos Recomendados

### 1. Dados Iniciais
- Criar uma Empresa no admin
- Criar uma Loja vinculada à empresa
- Criar Locais de Estoque
- Criar Categorias de Produtos
- Cadastrar alguns Produtos de exemplo

### 2. Configuração Fiscal
- Configurar `ConfiguracaoFiscalLoja` para cada loja
- Preparar certificado digital (quando for integrar com SEFAZ)

### 3. Testar Fluxo Completo
1. Abrir sessão de caixa
2. Cadastrar cliente
3. Cadastrar produtos
4. Fazer entrada de estoque
5. Realizar venda no PDV
6. Verificar movimentação financeira

### 4. Personalizações
- Ajustar permissões dos grupos conforme necessidade
- Configurar templates de mensagens WhatsApp
- Criar relatórios personalizados

## 🔧 Comandos Úteis

```bash
# Criar migrações (se modificar modelos)
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Criar grupos de permissões
python manage.py setup_roles

# Executar testes
pytest

# Executar servidor de desenvolvimento
python manage.py runserver

# Shell do Django (para testes manuais)
python manage.py shell
```

## 📚 Estrutura de Apps

```
guardiao_aladin/
├── core/           # Base, auditoria, LGPD
├── pessoas/        # Clientes e Fornecedores
├── produtos/       # Produtos e Categorias
├── fiscal/         # NF-e/NFC-e
├── estoque/        # Locais e Movimentação
├── vendas/         # Pedidos de Venda
├── pdv/            # Ponto de Venda
├── compras/        # Pedidos de Compra
├── financeiro/     # Contas e Títulos
├── crm/            # Leads e Interações
└── mensagens/      # WhatsApp
```

## ⚠️ Lembretes Importantes

1. **LGPD**: Campos sensíveis (CPF, CNPJ, telefone) estão preparados para criptografia, mas ainda não implementada
2. **SEFAZ**: Integração com SEFAZ-BA ainda não implementada (TODOs no código)
3. **WhatsApp**: Base criada, mas integração com API externa pendente
4. **Testes**: Testes básicos criados, expandir conforme necessário

## 🐛 Troubleshooting

### Erro ao acessar admin
- Verifique se criou o superusuário: `python manage.py createsuperuser`

### Erro 404 nas URLs
- Verifique se executou as migrações: `python manage.py migrate`

### Erro ao executar testes
- Verifique se instalou pytest-django: `pip install pytest-django`

### Banco de dados vazio
- Acesse o admin e crie os dados iniciais (Empresa, Loja, etc.)

## 📞 Suporte

Para dúvidas ou problemas, consulte:
- Documentação do Django: https://docs.djangoproject.com/
- Documentação do DRF: https://www.django-rest-framework.org/
- README.md do projeto

