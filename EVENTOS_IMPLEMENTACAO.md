# Módulo de Eventos - Implementação Completa

## ✅ Funcionalidades Implementadas

### 1. Tela de Proposta de Evento ✅

**Arquivo:** `templates/eventos/proposta_evento.html`

**Funcionalidades:**
- Visualização completa do evento
- Busca e adição de produtos à proposta
- Campo de quantidade e preço customizável
- Lista de itens da proposta com edição
- Cálculo automático do total
- Botão para faturar evento

**URLs:**
- `/eventos/proposta/<evento_id>/` - Tela principal
- `/eventos/proposta/<evento_id>/adicionar-item/` - Adicionar item (POST)
- `/eventos/proposta/<evento_id>/remover-item/<item_id>/` - Remover item (POST)

**Como usar:**
1. Acesse um evento no admin
2. Clique em "Ver Proposta" ou acesse `/eventos/proposta/<id>/`
3. Busque produtos e adicione à proposta
4. Ajuste quantidades e preços
5. Clique em "Faturar Evento" quando pronto

### 2. Integração com NF-e ao Faturar ✅

**Arquivo:** `eventos/services.py`

**Função:** `faturar_evento_com_nfe()`

**Funcionalidades:**
- Cria NotaFiscalSaida automaticamente ao faturar
- Vincula nota ao evento e ao pedido
- Atualiza status do pedido para FATURADO
- Atualiza status do evento para CONCLUIDO
- Gera número sequencial da NF-e
- TODO: Integração real com SEFAZ-BA

**Como usar:**
```python
from eventos.services import faturar_evento_com_nfe

nota_fiscal = faturar_evento_com_nfe(evento, usuario=request.user)
```

**View:** `/eventos/faturar/<evento_id>/` (POST)

### 3. Relatórios de Eventos ✅

**Arquivo:** `eventos/reports.py`

**Funções disponíveis:**

#### a) `relatorio_eventos_por_periodo()`
- Relatório por período (data início e fim)
- Estatísticas por tipo e status
- Total faturado
- Eventos concluídos

**API:** `GET /eventos/relatorio/periodo/?data_inicio=2024-01-01&data_fim=2024-12-31`

#### b) `relatorio_eventos_por_tipo()`
- Relatório por tipo de evento
- Estatísticas por status
- Total faturado por tipo

**API:** `GET /eventos/relatorio/tipo/?tipo_evento=SAO_JOAO`

### 4. Dashboard de Eventos em Execução ✅

**Arquivo:** `templates/eventos/dashboard.html`

**Funcionalidades:**
- Cards com estatísticas:
  - Total em execução
  - Eventos hoje
  - Eventos esta semana
- Lista de eventos de hoje
- Lista de próximos eventos (30 dias)
- Gráfico de eventos por tipo
- Links rápidos para propostas

**URL:** `/eventos/dashboard/`

**View:** `dashboard_eventos()`

## 📋 Estrutura de Arquivos Criados

```
eventos/
├── __init__.py
├── apps.py
├── models.py          # EventoVenda
├── admin.py           # Admin configurado
├── serializers.py     # API REST
├── views.py           # Views principais + ViewSet
├── views_reports.py   # Views de relatórios
├── services.py        # Serviço de faturamento
├── reports.py         # Funções de relatórios
├── urls.py            # URLs do módulo
└── migrations/
    └── 0001_initial.py

templates/eventos/
├── proposta_evento.html
└── dashboard.html
```

## 🔗 Integrações

### Com PedidoVenda
- EventoVenda tem FK para PedidoVenda
- Método `gerar_pedido_evento()` cria pedido tipo EVENTO
- Pedido é criado automaticamente ao acessar proposta

### Com NotaFiscalSaida
- NotaFiscalSaida tem FK para EventoVenda
- Serviço `faturar_evento_com_nfe()` cria nota automaticamente
- Nota vinculada ao evento e ao pedido

### Com CRM
- EventoVenda pode ser vinculado a um Lead
- Lead convertido pode virar Cliente do evento

## 🚀 Como Usar

### 1. Criar Evento
```python
# No admin ou via API
evento = EventoVenda.objects.create(
    empresa=empresa,
    loja=loja,
    nome_evento="São João 2024",
    tipo_evento="SAO_JOAO",
    data_evento="2024-06-24",
    # ... outros campos
)
```

### 2. Montar Proposta
- Acesse `/eventos/proposta/<evento_id>/`
- Busque e adicione produtos
- Ajuste quantidades e preços
- O pedido é criado/atualizado automaticamente

### 3. Faturar Evento
- Na tela de proposta, clique em "Faturar Evento"
- Sistema cria NF-e automaticamente
- Status atualizado para CONCLUIDO

### 4. Ver Dashboard
- Acesse `/eventos/dashboard/`
- Veja eventos em execução
- Acompanhe próximos eventos

### 5. Gerar Relatórios
```python
# Via API
GET /eventos/relatorio/periodo/?data_inicio=2024-01-01&data_fim=2024-12-31
GET /eventos/relatorio/tipo/?tipo_evento=SAO_JOAO
```

## 📊 API REST

### Endpoints Disponíveis

- `GET /api/v1/eventos/` - Listar eventos
- `POST /api/v1/eventos/` - Criar evento
- `GET /api/v1/eventos/{id}/` - Detalhes do evento
- `PUT /api/v1/eventos/{id}/` - Atualizar evento
- `DELETE /api/v1/eventos/{id}/` - Desativar evento
- `POST /api/v1/eventos/{id}/gerar_pedido/` - Gerar pedido (action customizada)

## 🔄 Fluxo Completo

1. **Criar Evento** → Admin ou API
2. **Vincular Lead/Cliente** → Opcional
3. **Acessar Proposta** → `/eventos/proposta/<id>/`
4. **Adicionar Produtos** → Montar proposta
5. **Enviar Proposta** → Mudar status para PROPOSTA_ENVIADA
6. **Aprovar** → Mudar status para APROVADO
7. **Executar** → Mudar status para EM_EXECUCAO
8. **Faturar** → Cria NF-e e muda para CONCLUIDO

## 🎯 Próximos Passos Sugeridos

1. **Tela de Envio de Proposta**
   - Gerar PDF da proposta
   - Enviar por email/WhatsApp

2. **Aprovação de Proposta**
   - Workflow de aprovação
   - Notificações

3. **Integração SEFAZ Real**
   - Emissão real de NF-e
   - Validação de XML
   - Consulta de status

4. **Relatórios Avançados**
   - Gráficos e visualizações
   - Exportação para Excel/PDF
   - Comparativos por período

5. **Notificações**
   - Alertas de eventos próximos
   - Lembretes de faturamento
   - Avisos de mudança de status

## ✅ Status

Todas as funcionalidades solicitadas foram implementadas e estão funcionando!

