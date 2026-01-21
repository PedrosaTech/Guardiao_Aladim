# Frontend - Módulo de Produtos

## ✅ Páginas Criadas

### 1. Lista de Produtos ✅

**URL:** `/produtos/`  
**Template:** `templates/produtos/lista_produtos.html`  
**View:** `produtos.views.lista_produtos`

**Funcionalidades:**
- Listagem de produtos em tabela responsiva
- Filtros por:
  - Busca (código interno, código de barras, descrição, NCM)
  - Categoria
  - Classe de Risco
  - Empresa
  - Restrição de Exército (Sim/Não)
- Badges coloridos por classe de risco:
  - 1.1G: Vermelho (risco máximo)
  - 1.2G: Laranja
  - 1.3G: Amarelo
  - 1.4G: Verde (baixo risco)
  - 1.4S: Verde claro (risco muito reduzido)
  - OUTRA: Cinza
- Badge de restrição de Exército
- Link para criar novo produto
- Link para ver detalhes

**Design:**
- Tabela limpa e organizada
- Badges coloridos para identificação visual rápida
- Filtros em grid adaptável
- Hover effect nas linhas

### 2. Criar Produto ✅

**URL:** `/produtos/criar/`  
**Template:** `templates/produtos/criar_produto.html`  
**View:** `produtos.views.criar_produto`

**Funcionalidades:**
- Formulário completo organizado em seções:
  - Informações Básicas (empresa, loja, categoria, código, descrição)
  - Características de Pirotecnia (classe de risco, restrição, certificado, lote, validade)
  - Dados Fiscais - NCM, CEST e CFOP
  - Dados Fiscais - ICMS
  - Dados Fiscais - PIS e COFINS
  - Dados Fiscais - IPI
  - Comercial (preço, observações)
- Valores padrão pré-preenchidos:
  - Unidade Comercial: UN
  - Origem: 0
  - Alíquota ICMS: 18.00%
  - CST PIS: 01
  - Alíquota PIS: 1.65%
  - CST COFINS: 01
  - Alíquota COFINS: 7.60%
  - CST IPI Venda: 52
  - CST IPI Compra: 02
- Validação de campos obrigatórios
- Mensagens de erro
- Dropdown para classe de risco (choices)

**Design:**
- Formulário organizado em seções claras
- Grid responsivo para campos
- Visual consistente com o resto do sistema

### 3. Detalhes do Produto ✅

**URL:** `/produtos/detalhes/<produto_id>/`  
**Template:** `templates/produtos/detalhes_produto.html`  
**View:** `produtos.views.detalhes_produto`

**Funcionalidades:**
- Visualização completa do produto
- Seções:
  - Informações do Produto (código, categoria, empresa, loja, preço)
  - Características de Pirotecnia (classe de risco com badge, restrição, certificado, lote, validade, condições de armazenamento)
  - Dados Fiscais (NCM, CEST, CFOPs, alíquotas)
  - Estoque Atual (tabela com locais e quantidades)
  - Observações
- Badges coloridos para classe de risco
- Badge de restrição de Exército

**Design:**
- Cards organizados
- Badges coloridos
- Tabela de estoque
- Layout responsivo

## 🔗 Navegação

```
/produtos/ (Lista)
    ├── /criar/ (Criar novo)
    └── /detalhes/<id>/ (Detalhes)
```

## 🎨 Design System

### Cores de Classe de Risco
- **1.1G**: Vermelho (#e74c3c) - Risco máximo
- **1.2G**: Laranja (#e67e22) - Alto risco
- **1.3G**: Amarelo (#f39c12) - Risco médio
- **1.4G**: Verde (#27ae60) - Baixo risco
- **1.4S**: Verde claro (#2ecc71) - Risco muito reduzido
- **OUTRA**: Cinza (#95a5a6) - Não aplicável

### Componentes
- **Tabela**: Fundo branco, hover effect, bordas sutis
- **Badges**: Border-radius 20px, cores por classe de risco
- **Formulário**: Seções bem definidas, grid responsivo

## 📋 Funcionalidades

### Filtros Disponíveis
1. **Busca**: Código interno, código de barras, descrição, NCM
2. **Categoria**: Dropdown com todas as categorias
3. **Classe de Risco**: Dropdown com todas as classes
4. **Empresa**: Dropdown com todas as empresas
5. **Restrição de Exército**: Sim/Não/Todas

### Informações Exibidas
- Código interno (gerado automaticamente)
- Descrição completa
- Categoria
- Classe de risco (com badge colorido)
- NCM
- Preço de venda sugerido
- Restrição de Exército (se aplicável)
- Estoque por local (na página de detalhes)

## 🚀 Como Usar

### 1. Acessar Lista de Produtos
```
http://localhost:8000/produtos/
```

### 2. Criar Novo Produto
- Clique em "+ Novo Produto"
- Preencha o formulário (campos obrigatórios marcados com *)
- Valores padrão já estão preenchidos para facilitar
- Clique em "Criar Produto"

### 3. Ver Detalhes
- Na lista, clique em "Ver" em qualquer produto
- Ou acesse `/produtos/detalhes/<id>/`

### 4. Filtrar Produtos
- Use os filtros na parte superior
- Clique em "Filtrar" ou pressione Enter no campo de busca
- Clique em "Limpar" para remover filtros

## 📝 URLs Configuradas

```python
# produtos/urls.py
path('', views.lista_produtos, name='lista_produtos'),
path('criar/', views.criar_produto, name='criar_produto'),
path('detalhes/<int:produto_id>/', views.detalhes_produto, name='detalhes_produto'),
```

## ✅ Status

Todas as páginas frontend foram criadas e estão funcionando!

- ✅ Lista de produtos com filtros
- ✅ Criar produto (formulário completo)
- ✅ Detalhes do produto (visualização completa)
- ✅ Badges coloridos por classe de risco
- ✅ Integração com estoque
- ✅ Design responsivo
- ✅ Visual consistente com eventos

