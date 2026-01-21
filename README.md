# Guardião Aladin - ERP para Pirotecnia

Sistema ERP especializado para empresas de venda de fogos de artifício na Bahia.

## Características

- Módulo fiscal (base para NF-e/NFC-e SEFAZ-BA)
- Cadastro de produtos com foco em fogos (classe de risco, certificações, etc.)
- Estoque por local (depósito, loja, vitrine, caminhão / equipe externa)
- Vendas (PDV rápido + vendas maiores com NF-e)
- Compras
- Financeiro
- CRM
- Estrutura inicial para Mensagens / WhatsApp

## Tecnologias

- Python 3.12
- Django 5.x
- Django REST Framework
- PostgreSQL (produção) / SQLite (desenvolvimento)
- pytest para testes

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Copie o arquivo `.env.example` para `.env` e configure as variáveis:
   ```bash
   cp .env.example .env
   ```

5. Execute as migrações:
   ```bash
   python manage.py migrate
   ```

6. Crie um superusuário:
   ```bash
   python manage.py createsuperuser
   ```

7. Crie os grupos de permissões padrão:
   ```bash
   python manage.py setup_roles
   ```

8. Execute o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```

## Estrutura do Projeto

- `core/` - Modelos base, auditoria, LGPD, RBAC
- `pessoas/` - Clientes e Fornecedores
- `produtos/` - Produtos (fogos de artifício)
- `fiscal/` - Módulo fiscal (NF-e/NFC-e)
- `estoque/` - Locais e movimentação de estoque
- `vendas/` - Pedidos de venda
- `pdv/` - Ponto de venda (caixa)
- `compras/` - Pedidos de compra
- `financeiro/` - Contas, títulos, movimentos
- `crm/` - Leads e interações
- `mensagens/` - Base para WhatsApp

## API REST

A API REST está disponível em `/api/v1/` com os seguintes endpoints:

- `/api/v1/empresas/`
- `/api/v1/lojas/`
- `/api/v1/clientes/`
- `/api/v1/fornecedores/`
- `/api/v1/categorias-produto/`
- `/api/v1/produtos/`
- `/api/v1/locais-estoque/`
- `/api/v1/estoque-atual/`
- `/api/v1/movimentos-estoque/`
- `/api/v1/pedidos-venda/`
- `/api/v1/caixas-sessao/`
- `/api/v1/pagamentos/`
- `/api/v1/leads/`
- `/api/v1/interacoes-crm/`

## Testes

Execute os testes com pytest:

```bash
pytest
```

## LGPD e Segurança

- Campos sensíveis (CPF, CNPJ, telefone) usam `EncryptedCharField` (criptografia real a ser implementada)
- Auditoria de acesso via modelo `AuditLog`
- Controle de permissões via grupos Django
- TODO: Implementar criptografia real com Fernet
- TODO: Implementar logs de segurança para operações sensíveis

## TODO

- [ ] Integração com SEFAZ-BA para NF-e/NFC-e
- [ ] Criptografia real para campos sensíveis
- [ ] Integração com WhatsApp Business API
- [ ] Validação de idade para venda de fogos
- [ ] Relatórios de estoque por classe de risco
- [ ] Testes para áreas críticas (fiscal, financeiro)

## Licença

Proprietário - Guardião Aladin

