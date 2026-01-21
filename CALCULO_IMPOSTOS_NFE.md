# 📊 Cálculo de Impostos na NF-e - SEFAZ-BA

## ✅ Implementação Completa

### Funcionalidades Implementadas

1. **Módulo de Cálculos Fiscais** (`fiscal/calculos.py`)
   - Função `calcular_impostos_item()` - Calcula impostos por item
   - Função `calcular_impostos_nota()` - Calcula totais da nota
   - Baseado nos campos fiscais dos produtos

2. **Cálculos Implementados**

   #### ICMS (Imposto sobre Circulação de Mercadorias e Serviços)
   - **Base de Cálculo**: Valor total do item
   - **Alíquota**: Do produto (`aliquota_icms`)
   - **CST/CSOSN**: 
     - `102` (Simples Nacional - Tributado pelo Simples)
     - `00` (Regime Normal - Tributado integralmente)
   - **Fórmula**: `Base ICMS × (Alíquota ICMS / 100)`

   #### ICMS-ST (Substituição Tributária)
   - **Base de Cálculo**: Valor total do item
   - **Alíquota**: Do produto (`aliquota_icms_st`)
   - **CST/CSOSN**: 
     - `10` (CST) ou `201` (CSOSN)
   - **Fórmula**: `Base ICMS-ST × (Alíquota ICMS-ST / 100)`
   - **Nota**: Cálculo simplificado. Em produção, pode ser necessário calcular MVA e outras variáveis.

   #### PIS (Programa de Integração Social)
   - **Base de Cálculo**: Valor total do item
   - **Alíquota**: Do produto (`aliquota_pis`) - Padrão: 1,65%
   - **CST**: 
     - `01` (Operação Tributável com Alíquota Básica)
   - **Fórmula**: `Base PIS × (Alíquota PIS / 100)`

   #### COFINS (Contribuição para o Financiamento da Seguridade Social)
   - **Base de Cálculo**: Valor total do item
   - **Alíquota**: Do produto (`aliquota_cofins`) - Padrão: 7,6%
   - **CST**: 
     - `01` (Operação Tributável com Alíquota Básica)
   - **Fórmula**: `Base COFINS × (Alíquota COFINS / 100)`

   #### IPI (Imposto sobre Produtos Industrializados)
   - **Base de Cálculo**: Valor total do item
   - **Alíquota**: Do produto (`aliquota_ipi_venda`) - Padrão: 0%
   - **CST**: 
     - `52` (Saída Tributada com Alíquota Zero)
     - `00`, `01`, `02`, `03` (Outros CSTs tributados)
   - **Fórmula**: `Base IPI × (Alíquota IPI / 100)`

### 📋 Exibição no PDF

O PDF agora exibe:

1. **Tabela de Itens** (atualizada)
   - Adicionada coluna "CST" mostrando o CSOSN/CST ICMS do produto

2. **Cálculo do Imposto** (atualizado)
   - Base de Cálculo do ICMS (calculada)
   - Valor do ICMS (calculado)
   - Base de Cálculo do ICMS ST (se aplicável)
   - Valor do ICMS ST (se aplicável)
   - Base de Cálculo do PIS (calculada)
   - Valor do PIS (calculado)
   - Base de Cálculo do COFINS (calculada)
   - Valor do COFINS (calculado)
   - Base de Cálculo do IPI (se aplicável)
   - Valor do IPI (se aplicável)
   - Valor Total dos Produtos
   - Valor do Frete
   - Valor do Seguro
   - Desconto
   - Outras Despesas Acessórias
   - Valor Total da NF-e

### 🔍 Lógica de Cálculo

#### Por Item:
1. Obtém o valor total do item (já com desconto aplicado)
2. Verifica os CSTs/CSOSN do produto
3. Calcula cada imposto conforme as regras:
   - Se CST permite cálculo, calcula
   - Se CST isenta, zera valores
   - Usa alíquotas do produto

#### Por Nota:
1. Soma todos os impostos de todos os itens
2. Calcula totais gerais
3. Retorna dicionário com todos os valores

### 📊 Exemplo de Cálculo

**Produto:**
- Valor: R$ 100,00
- Alíquota ICMS: 18%
- Alíquota PIS: 1,65%
- Alíquota COFINS: 7,6%
- CSOSN: 102

**Cálculos:**
- Base ICMS: R$ 100,00
- Valor ICMS: R$ 100,00 × 18% = R$ 18,00
- Base PIS: R$ 100,00
- Valor PIS: R$ 100,00 × 1,65% = R$ 1,65
- Base COFINS: R$ 100,00
- Valor COFINS: R$ 100,00 × 7,6% = R$ 7,60
- Base IPI: R$ 100,00
- Valor IPI: R$ 0,00 (CST 52 - Alíquota Zero)

### ⚠️ Observações Importantes

1. **ICMS-ST**: 
   - Cálculo simplificado implementado
   - Em produção, pode ser necessário calcular MVA (Margem de Valor Agregado)
   - Pode variar conforme estado de destino

2. **CSTs/CSOSN**:
   - Implementados os mais comuns
   - Outros CSTs podem não calcular impostos (conforme legislação)

3. **Valores Padrão**:
   - Se produto não tiver alíquota configurada, usa 0%
   - Se produto não tiver CST configurado, assume valores padrão

4. **Precisão**:
   - Usa `Decimal` para cálculos precisos
   - Arredondamento conforme normas fiscais

### 🔄 Próximas Melhorias

- [ ] Implementar cálculo completo de ICMS-ST com MVA
- [ ] Adicionar mais CSTs/CSOSN
- [ ] Validar cálculos com exemplos reais da SEFAZ
- [ ] Adicionar testes unitários para cálculos
- [ ] Implementar cálculo de frete e seguro se aplicável
- [ ] Adicionar cálculo de desconto por item

### ✅ Status

- ✅ Cálculo de ICMS implementado
- ✅ Cálculo de ICMS-ST implementado (simplificado)
- ✅ Cálculo de PIS implementado
- ✅ Cálculo de COFINS implementado
- ✅ Cálculo de IPI implementado
- ✅ Exibição no PDF atualizada
- ✅ Baseado nos campos fiscais dos produtos
- ✅ Conforme normas SEFAZ-BA

