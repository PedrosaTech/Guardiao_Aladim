# Evolução do Fluxo de VENDAS EXTERNAS / EVENTOS

## ✅ Funcionalidades Implementadas

### 1. Action no Admin: "Gerar/abrir Pedido de Venda do Evento" ✅

**Arquivo:** `eventos/admin.py`

**Funcionalidade:**
- Action disponível no admin de `EventoVenda`
- Para cada evento selecionado:
  - Se já possui pedido: redireciona para edição do pedido
  - Se não possui: cria novo pedido e redireciona para edição

**Comportamento:**
- **1 evento selecionado**: Redireciona diretamente para o pedido
- **Múltiplos eventos**: Cria pedidos e redireciona para lista de pedidos

**Lógica do método `gerar_pedido_evento()`:**
- Cria cliente genérico "Consumidor Final" se não houver cliente
- Busca ou cria condição de pagamento padrão "À Vista" se não informada
- Usa `created_by` como vendedor, ou busca da equipe responsável
- Cria pedido com `tipo_venda='EVENTO'` e `status='ORCAMENTO'`

### 2. Serviço Fiscal: `criar_nfe_rascunho_para_pedido_evento()` ✅

**Arquivo:** `fiscal/services.py`

**Função:** `criar_nfe_rascunho_para_pedido_evento(pedido: PedidoVenda) -> NotaFiscalSaida`

**Validações:**
- Pedido deve ser do tipo `EVENTO`
- Pedido deve estar associado a um `EventoVenda`
- Verifica se já existe NF-e para o pedido (permite múltiplas rascunhos)

**Funcionalidades:**
- Busca configuração fiscal da loja (número e série)
- Cria `NotaFiscalSaida` com:
  - `tipo_documento = 'NFE'`
  - `status = 'RASCUNHO'`
  - `valor_total = pedido.valor_total`
  - Vinculada ao evento e ao pedido
  - `data_emissao = timezone.now()`

**TODOs implementados:**
- ✅ Buscar número e série de `ConfiguracaoFiscalLoja`
- ⏳ Montar XML da NF-e (futuro)
- ⏳ Integrar com SEFAZ-BA (futuro)

### 3. Action no Admin: "Gerar NF-e rascunho do Evento" ✅

**Arquivo:** `eventos/admin.py`

**Funcionalidade:**
- Action disponível no admin de `EventoVenda`
- Para cada evento selecionado:
  - Verifica se possui pedido associado
  - Chama `criar_nfe_rascunho_para_pedido_evento()`
  - Exibe mensagens de sucesso/erro

**Comportamento:**
- **1 evento selecionado**: Cria NF-e e redireciona para edição
- **Múltiplos eventos**: Cria NF-es e redireciona para lista de notas

**Validações:**
- Evento deve ter pedido associado
- Pedido deve ser do tipo `EVENTO`
- Exibe mensagens claras de erro se não atender requisitos

## 📋 Fluxo Completo de Uso

### Passo 1: Criar Evento
1. Acesse o admin: `/admin/eventos/eventovenda/`
2. Crie um novo evento ou selecione um existente
3. Preencha os dados do evento (nome, tipo, data, endereço, etc.)
4. Opcionalmente, vincule um Lead ou Cliente

### Passo 2: Gerar Pedido de Venda
1. Selecione o(s) evento(s) na lista
2. Escolha a action: **"Gerar/abrir Pedido de Venda do Evento"**
3. Clique em "Ir"
4. Sistema cria o pedido automaticamente (se não existir)
5. Você é redirecionado para editar o pedido
6. Adicione itens ao pedido através do inline no admin

### Passo 3: Gerar NF-e Rascunho
1. Volte para a lista de eventos
2. Selecione o evento (que já deve ter pedido)
3. Escolha a action: **"Gerar NF-e rascunho do Evento"**
4. Clique em "Ir"
5. Sistema cria a NF-e RASCUNHO automaticamente
6. Você é redirecionado para editar a NF-e

## 🔧 Arquivos Criados/Modificados

### Novos Arquivos
- `fiscal/services.py` - Serviço de criação de NF-e rascunho

### Arquivos Modificados
- `eventos/admin.py` - Actions adicionadas
- `eventos/models.py` - Método `gerar_pedido_evento()` melhorado

## 📝 Melhorias Implementadas

### No método `gerar_pedido_evento()`:
- ✅ Cria cliente genérico se não houver cliente
- ✅ Busca/cria condição de pagamento padrão
- ✅ Determina vendedor automaticamente (created_by → equipe → primeiro usuário)
- ✅ Validações e mensagens de erro claras

### No serviço fiscal:
- ✅ Validações robustas
- ✅ Busca configuração fiscal da loja
- ✅ Tratamento de erros
- ✅ TODOs claros para próximas etapas

### Nas actions do admin:
- ✅ Mensagens informativas
- ✅ Redirecionamentos inteligentes
- ✅ Suporte a seleção múltipla
- ✅ Tratamento de erros

## 🎯 Próximos Passos Sugeridos

1. **Montar XML da NF-e**
   - Criar estrutura XML baseada nos itens do pedido
   - Validar schema XML
   - Armazenar XML na nota

2. **Integração SEFAZ-BA**
   - Enviar NF-e para homologação/produção
   - Consultar status da nota
   - Tratar rejeições

3. **Incrementar Número da NF-e**
   - Atualizar `proximo_numero_nfe` após autorização
   - Garantir sequência única

4. **Melhorias no Admin**
   - Adicionar botões de ação rápida na página de detalhes
   - Mostrar status do pedido e NF-e no list_display do evento

5. **Validações Adicionais**
   - Validar se pedido tem itens antes de gerar NF-e
   - Validar se pedido está no status correto
   - Validar dados fiscais do cliente

## ✅ Status

Todas as funcionalidades solicitadas foram implementadas e testadas!

- ✅ Action "Gerar/abrir Pedido de Venda do Evento"
- ✅ Serviço `criar_nfe_rascunho_para_pedido_evento()`
- ✅ Action "Gerar NF-e rascunho do Evento"
- ✅ Migrações verificadas (sem mudanças necessárias)
- ✅ Sistema check passou sem erros

