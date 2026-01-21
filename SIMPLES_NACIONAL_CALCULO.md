# 📊 Cálculo de Impostos - Simples Nacional vs Regime Normal

## ✅ Ajuste Implementado

### Problema Identificado

No **Simples Nacional**, os impostos (ICMS, PIS, COFINS) **NÃO são calculados separadamente** por item/nota, pois:

1. Os impostos já estão **embutidos no preço** de venda
2. O imposto do Simples é calculado **mensalmente** sobre a receita bruta total
3. O **CSOSN 102** indica "Tributado pelo Simples Nacional sem permissão de crédito"

### Solução Implementada

#### 1. Verificação do Regime Tributário

A função `calcular_impostos_item()` agora recebe o `regime_tributario` e verifica:
- Se é Simples Nacional (`SIMPLES_NACIONAL`)
- Se o produto tem CSOSN 102

#### 2. Lógica para Simples Nacional (CSOSN 102)

**Quando detectado Simples Nacional + CSOSN 102:**

- ✅ **Base ICMS**: Informada (valor do produto)
- ❌ **Valor ICMS**: **R$ 0,00** (não calcula separadamente)
- ✅ **Base PIS**: Informada (valor do produto)
- ❌ **Valor PIS**: **R$ 0,00** (não calcula separadamente)
- ✅ **Base COFINS**: Informada (valor do produto)
- ❌ **Valor COFINS**: **R$ 0,00** (não calcula separadamente)

**Motivo:** Os impostos já estão embutidos no preço e são calculados mensalmente sobre a receita bruta.

#### 3. Lógica para Regime Normal (CST 00)

**Quando detectado Regime Normal + CST 00:**

- ✅ **Base ICMS**: Valor do produto
- ✅ **Valor ICMS**: Calculado (Base × Alíquota)
- ✅ **Base PIS**: Valor do produto
- ✅ **Valor PIS**: Calculado (Base × Alíquota)
- ✅ **Base COFINS**: Valor do produto
- ✅ **Valor COFINS**: Calculado (Base × Alíquota)

#### 4. Exceções

- **ICMS-ST**: Pode ser calculado mesmo no Simples Nacional (se configurado)
- **IPI**: Calculado normalmente (geralmente zero na venda)

## 📋 Exemplo Prático

### Simples Nacional (CSOSN 102)

**Produto:** R$ 100,00

**Resultado:**
- Base ICMS: R$ 100,00
- Valor ICMS: **R$ 0,00** ✅ (embutido no Simples)
- Base PIS: R$ 100,00
- Valor PIS: **R$ 0,00** ✅ (embutido no Simples)
- Base COFINS: R$ 100,00
- Valor COFINS: **R$ 0,00** ✅ (embutido no Simples)

**Observação:** O imposto do Simples será calculado mensalmente sobre toda a receita bruta, não por nota.

### Regime Normal (CST 00)

**Produto:** R$ 100,00
- Alíquota ICMS: 18%
- Alíquota PIS: 1,65%
- Alíquota COFINS: 7,6%

**Resultado:**
- Base ICMS: R$ 100,00
- Valor ICMS: **R$ 18,00** ✅ (calculado)
- Base PIS: R$ 100,00
- Valor PIS: **R$ 1,65** ✅ (calculado)
- Base COFINS: R$ 100,00
- Valor COFINS: **R$ 7,60** ✅ (calculado)

## 🎨 Exibição no PDF

O PDF agora mostra:

1. **Aviso para Simples Nacional:**
   ```
   ⚠️ SIMPLES NACIONAL: Os impostos (ICMS, PIS, COFINS) estão embutidos 
   no preço e são calculados mensalmente sobre a receita bruta. 
   Os valores abaixo são apenas informativos para fins de documentação fiscal.
   ```

2. **Valores com indicação:**
   - Valor ICMS: R$ 0,00 **(embutido no Simples)**
   - Valor PIS: R$ 0,00 **(embutido no Simples)**
   - Valor COFINS: R$ 0,00 **(embutido no Simples)**

## 🔍 Como Funciona

1. **View busca regime tributário:**
   ```python
   config_fiscal = nota.loja.configuracao_fiscal
   regime_tributario = config_fiscal.regime_tributario
   ```

2. **Passa para função de cálculo:**
   ```python
   impostos = calcular_impostos_nota(itens, regime_tributario)
   ```

3. **Função verifica:**
   - Se `regime_tributario` contém "SIMPLES"
   - Se produto tem CSOSN 102
   - Aplica lógica correta

## ⚠️ Importante

### Simples Nacional:
- ✅ Base de cálculo é informada (para documentação)
- ❌ Valor do imposto é **zero** (já embutido)
- ✅ Imposto calculado mensalmente sobre receita bruta

### Regime Normal:
- ✅ Base de cálculo é informada
- ✅ Valor do imposto é **calculado** (Base × Alíquota)
- ✅ Imposto calculado por nota

## 📝 Configuração Necessária

Para funcionar corretamente, certifique-se de:

1. **Configurar regime tributário na loja:**
   - Acesse: `/admin/fiscal/configuracaofiscalloja/`
   - Configure: `regime_tributario = "SIMPLES_NACIONAL"`

2. **Configurar CSOSN nos produtos:**
   - Para Simples Nacional: `csosn_cst = "102"`
   - Para Regime Normal: `csosn_cst = "00"`

## ✅ Status

- ✅ Lógica de Simples Nacional implementada
- ✅ Verificação de regime tributário
- ✅ CSOSN 102 trata impostos como zero
- ✅ CST 00 calcula impostos normalmente
- ✅ PDF mostra aviso para Simples Nacional
- ✅ Valores indicados como "embutido no Simples"
- ✅ Sistema check passou sem erros

## 🔄 Próximas Melhorias

- [ ] Adicionar outros CSOSN do Simples Nacional (101, 103, etc.)
- [ ] Implementar cálculo mensal do Simples (DAS)
- [ ] Adicionar validação de CSOSN conforme regime
- [ ] Criar relatório de impostos por regime

