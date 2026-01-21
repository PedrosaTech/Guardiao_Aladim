# Frontend - Módulo de Eventos

## ✅ Páginas Criadas

### 1. Lista de Eventos ✅

**URL:** `/eventos/`  
**Template:** `templates/eventos/lista_eventos.html`  
**View:** `eventos.views.lista_eventos`

**Funcionalidades:**
- Listagem de eventos em cards responsivos
- Filtros por:
  - Busca (nome do evento ou responsável)
  - Status
  - Tipo de evento
  - Loja
- Ações rápidas:
  - Ver detalhes
  - Abrir proposta (se tiver pedido)
  - Gerar pedido (se não tiver)
- Link para criar novo evento
- Link para dashboard

**Design:**
- Cards com hover effect
- Badges de status coloridos
- Grid responsivo
- Filtros em grid adaptável

### 2. Criar Evento ✅

**URL:** `/eventos/criar/`  
**Template:** `templates/eventos/criar_evento.html`  
**View:** `eventos.views.criar_evento`

**Funcionalidades:**
- Formulário completo para criar evento
- Campos organizados em seções:
  - Informações básicas (empresa, loja, nome, tipo, data, hora, status)
  - Relacionamentos (lead, cliente)
  - Endereço completo
  - Detalhes (público, responsável, telefone, observações)
- Validação de campos obrigatórios
- Mensagens de erro
- Botão de cancelar/voltar

**Design:**
- Formulário limpo e organizado
- Grid responsivo para campos
- Seções bem definidas
- Visual consistente com o resto do sistema

### 3. Detalhes do Evento ✅

**URL:** `/eventos/detalhes/<evento_id>/`  
**Template:** `templates/eventos/detalhes_evento.html`  
**View:** `eventos.views.detalhes_evento`

**Funcionalidades:**
- Visualização completa do evento
- Seções:
  - Informações básicas (status, tipo, data, loja, responsável)
  - Endereço completo
  - Relacionamentos (lead, cliente)
  - Pedido de venda (se existir):
    - Informações do pedido
    - Tabela de itens
    - Link para adicionar itens
  - Notas fiscais (se existirem)
  - Observações
- Sidebar de ações rápidas:
  - Gerar pedido (se não tiver)
  - Editar proposta (se tiver pedido)
  - Gerar NF-e rascunho
  - Faturar evento
- Ações via JavaScript (AJAX)

**Design:**
- Layout em duas colunas (conteúdo + sidebar)
- Cards organizados
- Tabelas responsivas
- Badges de status
- Sidebar sticky (fixa ao rolar)

### 4. Proposta de Evento (Melhorada) ✅

**URL:** `/eventos/proposta/<evento_id>/`  
**Template:** `templates/eventos/proposta_evento.html`  
**View:** `eventos.views.proposta_evento`

**Melhorias:**
- Botão "Voltar" no header
- Navegação melhorada
- Visual consistente com outras páginas

**Funcionalidades existentes:**
- Busca de produtos com autocomplete
- Adição de itens à proposta
- Tabela de itens editável
- Cálculo automático de total
- Botão para faturar evento

## 🔗 Navegação

```
/eventos/ (Lista)
    ├── /criar/ (Criar novo)
    ├── /detalhes/<id>/ (Detalhes)
    │   └── /proposta/<id>/ (Proposta)
    └── /dashboard/ (Dashboard)
```

## 🎨 Design System

### Cores
- **Primária:** `#3498db` (Azul)
- **Sucesso:** `#27ae60` (Verde)
- **Aviso:** `#ffc107` (Amarelo)
- **Info:** `#17a2b8` (Azul claro)
- **Secundária:** `#95a5a6` (Cinza)
- **Perigo:** `#e74c3c` (Vermelho)

### Componentes
- **Cards:** Fundo branco, sombra suave, border-radius 8px
- **Botões:** Padding 10px 20px, border-radius 5px, transições suaves
- **Badges:** Border-radius 20px, cores por status
- **Tabelas:** Bordas sutis, hover effect
- **Formulários:** Inputs com borda 1px, focus com cor primária

### Status Badges
- **Rascunho:** Cinza claro
- **Proposta Enviada:** Amarelo
- **Aprovado:** Verde
- **Em Execução:** Azul claro
- **Concluído:** Azul
- **Cancelado:** Vermelho claro

## 📱 Responsividade

- **Desktop:** Grid de 2-3 colunas
- **Tablet:** Grid de 1-2 colunas
- **Mobile:** Coluna única, sidebar fixa no topo

## 🔧 Funcionalidades JavaScript

### Funções Disponíveis

1. **`gerarPedido(eventoId)`**
   - Gera pedido de venda para o evento
   - Via AJAX POST
   - Atualiza página após sucesso

2. **`gerarNFe(eventoId)`**
   - Gera NF-e rascunho para o evento
   - Via AJAX POST
   - Atualiza página após sucesso

3. **`faturarEvento(eventoId)`**
   - Fatura o evento completo
   - Via AJAX POST
   - Atualiza página após sucesso

4. **`filtrar()`**
   - Aplica filtros na lista de eventos
   - Atualiza URL com parâmetros
   - Recarrega página

## 🚀 Como Usar

### 1. Acessar Lista de Eventos
```
http://localhost:8000/eventos/
```

### 2. Criar Novo Evento
- Clique em "+ Novo Evento"
- Preencha o formulário
- Clique em "Criar Evento"

### 3. Ver Detalhes
- Na lista, clique em "Ver Detalhes"
- Ou acesse `/eventos/detalhes/<id>/`

### 4. Gerar Pedido
- Na página de detalhes, clique em "Gerar Pedido"
- Ou na lista, clique em "Gerar Pedido" no card

### 5. Montar Proposta
- Na página de detalhes, clique em "Proposta"
- Ou acesse `/eventos/proposta/<id>/`
- Busque e adicione produtos
- Ajuste quantidades e preços

### 6. Gerar NF-e
- Na página de detalhes, clique em "Gerar NF-e"
- Sistema cria NF-e rascunho automaticamente

### 7. Faturar Evento
- Na página de detalhes, clique em "Faturar"
- Sistema cria NF-e e finaliza processo

## 📋 URLs Configuradas

```python
# eventos/urls.py
path('', views.lista_eventos, name='lista_eventos'),
path('criar/', views.criar_evento, name='criar_evento'),
path('detalhes/<int:evento_id>/', views.detalhes_evento, name='detalhes_evento'),
path('gerar-pedido/<int:evento_id>/', views.gerar_pedido_evento_view, name='gerar_pedido_evento'),
path('gerar-nfe/<int:evento_id>/', views.gerar_nfe_evento_view, name='gerar_nfe_evento'),
path('proposta/<int:evento_id>/', views.proposta_evento, name='proposta_evento'),
# ... outras rotas
```

## ✅ Status

Todas as páginas frontend foram criadas e estão funcionando!

- ✅ Lista de eventos com filtros
- ✅ Criar evento (formulário completo)
- ✅ Detalhes do evento (visualização completa)
- ✅ Proposta de evento (melhorada)
- ✅ Navegação entre páginas
- ✅ Ações via JavaScript/AJAX
- ✅ Design responsivo
- ✅ Visual consistente

