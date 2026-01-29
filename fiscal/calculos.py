"""
Cálculos fiscais conforme normas SEFAZ-BA.
"""
from decimal import Decimal
from typing import Dict, List


def calcular_impostos_item(item, regime_tributario=None, config_fiscal=None) -> Dict[str, Decimal]:
    """
    Calcula os impostos de um item do pedido conforme normas SEFAZ-BA.
    
    AGORA TAMBÉM SUPORTA: Reforma Tributária 2026 (CBS/IBS)
    
    IMPORTANTE: Para Simples Nacional (CSOSN 102), os impostos NÃO são calculados
    separadamente, pois já estão embutidos no preço. Apenas informa-se a base de cálculo.
    
    Args:
        item: ItemPedidoVenda com produto OU serviço relacionado
        regime_tributario: Regime tributário da empresa ('SIMPLES_NACIONAL', 'LUCRO_PRESUMIDO', etc.)
        config_fiscal: ConfiguracaoFiscalLoja (opcional, para feature flag da reforma)
        
    Returns:
        Dict com os valores calculados (impostos atuais + reforma 2026):
        {
            'base_icms': Decimal,
            'valor_icms': Decimal,
            'base_icms_st': Decimal,
            'valor_icms_st': Decimal,
            'base_pis': Decimal,
            'valor_pis': Decimal,
            'base_cofins': Decimal,
            'valor_cofins': Decimal,
            'base_ipi': Decimal,
            'valor_ipi': Decimal,
            # Reforma 2026 (se ativada)
            'base_ibs': Decimal,
            'valor_ibs': Decimal,
            'aliquota_ibs': Decimal,
            'base_cbs': Decimal,
            'valor_cbs': Decimal,
            'aliquota_cbs': Decimal,
            'cclass_trib': str ou None,
            'cst_ibs': str ou None,
            'cst_cbs': str ou None,
        }
    """
    # ═══ IDENTIFICAR PRODUTO OU SERVIÇO ═══
    item_fiscal = None
    tipo_item = None
    
    if hasattr(item, 'produto') and item.produto:
        item_fiscal = item.produto
        tipo_item = 'PRODUTO'
    elif hasattr(item, 'servico') and item.servico:
        item_fiscal = item.servico
        tipo_item = 'SERVICO'
    else:
        # Fallback: tentar item.produto direto (compatibilidade)
        item_fiscal = getattr(item, 'produto', None)
        tipo_item = 'PRODUTO' if item_fiscal else None
    
    valor_item = item.total  # Valor total do item (já com desconto)
    
    # Inicializar valores
    base_icms = Decimal('0.00')
    valor_icms = Decimal('0.00')
    base_icms_st = Decimal('0.00')
    valor_icms_st = Decimal('0.00')
    base_pis = Decimal('0.00')
    valor_pis = Decimal('0.00')
    base_cofins = Decimal('0.00')
    valor_cofins = Decimal('0.00')
    base_ipi = Decimal('0.00')
    valor_ipi = Decimal('0.00')
    
    # Reforma 2026 (inicializar)
    base_ibs = Decimal('0.00')
    valor_ibs = Decimal('0.00')
    aliquota_ibs = Decimal('0.00')
    base_cbs = Decimal('0.00')
    valor_cbs = Decimal('0.00')
    aliquota_cbs = Decimal('0.00')
    cclass_trib = None
    cst_ibs = None
    cst_cbs = None
    
    # Verificar se tem item fiscal (produto ou serviço)
    if not item_fiscal:
        return {
            'base_icms': base_icms,
            'valor_icms': valor_icms,
            'base_icms_st': base_icms_st,
            'valor_icms_st': valor_icms_st,
            'base_pis': base_pis,
            'valor_pis': valor_pis,
            'base_cofins': base_cofins,
            'valor_cofins': valor_cofins,
            'base_ipi': base_ipi,
            'valor_ipi': valor_ipi,
            # Reforma 2026 (zerados)
            'base_ibs': base_ibs,
            'valor_ibs': valor_ibs,
            'aliquota_ibs': aliquota_ibs,
            'base_cbs': base_cbs,
            'valor_cbs': valor_cbs,
            'aliquota_cbs': aliquota_cbs,
            'cclass_trib': cclass_trib,
            'cst_ibs': cst_ibs,
            'cst_cbs': cst_cbs,
        }
    
    # Base de cálculo para todos os impostos (geralmente o valor do item)
    base_calculo = valor_item
    
    # Verificar regime tributário
    is_simples_nacional = regime_tributario and 'SIMPLES' in regime_tributario.upper()
    
    # ═══ CÁLCULO ICMS (só para produtos) ═══
    if tipo_item == 'PRODUTO':
        produto = item_fiscal
        # Verificar CST/CSOSN para determinar se calcula ICMS
        csosn_cst = produto.csosn_cst or '000'
    
        # CSOSN 102 = Simples Nacional - Tributado pelo Simples SEM permissão de crédito
        # Neste caso, NÃO calcula ICMS, PIS, COFINS separadamente (já estão no Simples)
        if csosn_cst == '102' and is_simples_nacional:
            # Simples Nacional: apenas informa base de cálculo, valor do imposto é zero
            # (o imposto já está embutido no preço e é calculado mensalmente sobre receita bruta)
            base_icms = base_calculo
            valor_icms = Decimal('0.00')  # Não calcula separadamente no Simples
            
            base_pis = base_calculo
            valor_pis = Decimal('0.00')  # Não calcula separadamente no Simples
            
            base_cofins = base_calculo
            valor_cofins = Decimal('0.00')  # Não calcula separadamente no Simples
        elif csosn_cst == '00':  # Regime Normal - Tributado integralmente
            # Regime Normal: calcula ICMS normalmente
            base_icms = base_calculo
            aliquota_icms = produto.aliquota_icms or Decimal('0.00')
            valor_icms = base_icms * (aliquota_icms / Decimal('100.00'))
            
            # PIS e COFINS no regime normal
            pis_cst = produto.pis_cst or '01'
            if pis_cst == '01':
                base_pis = base_calculo
                aliquota_pis = produto.aliquota_pis or Decimal('0.00')
                valor_pis = base_pis * (aliquota_pis / Decimal('100.00'))
            
            cofins_cst = produto.cofins_cst or '01'
            if cofins_cst == '01':
                base_cofins = base_calculo
                aliquota_cofins = produto.aliquota_cofins or Decimal('0.00')
                valor_cofins = base_cofins * (aliquota_cofins / Decimal('100.00'))
        else:
            # Outros CSOSN/CST - pode variar conforme legislação
            # Por enquanto, apenas informa base se houver alíquota configurada
            if produto.aliquota_icms and produto.aliquota_icms > 0:
                base_icms = base_calculo
                # Não calcula valor se não for regime normal ou simples específico
                valor_icms = Decimal('0.00')
        
        # ICMS-ST (Substituição Tributária)
        # ICMS-ST pode ser aplicado mesmo no Simples Nacional em casos específicos
        if produto.icms_st_cst and produto.aliquota_icms_st:
            base_icms_st = base_calculo
            aliquota_icms_st = produto.aliquota_icms_st or Decimal('0.00')
            # Cálculo simplificado: base * alíquota ST
            # Em produção, pode ser necessário calcular MVA e outras variáveis
            valor_icms_st = base_icms_st * (aliquota_icms_st / Decimal('100.00'))
        
        # IPI (na venda)
        ipi_venda_cst = produto.ipi_venda_cst or '52'
        if ipi_venda_cst == '52':  # Saída Tributada com Alíquota Zero
            base_ipi = base_calculo
            valor_ipi = Decimal('0.00')  # Alíquota zero
        elif ipi_venda_cst in ['00', '01', '02', '03']:  # Outros CSTs tributados
            base_ipi = base_calculo
            aliquota_ipi = produto.aliquota_ipi_venda or Decimal('0.00')
            valor_ipi = base_ipi * (aliquota_ipi / Decimal('100.00'))
        else:
            base_ipi = Decimal('0.00')
            valor_ipi = Decimal('0.00')
    else:
        # Serviços não têm ICMS, IPI
        base_icms = Decimal('0.00')
        valor_icms = Decimal('0.00')
        base_ipi = Decimal('0.00')
        valor_ipi = Decimal('0.00')
        
        # PIS e COFINS podem existir para serviços (se configurado)
        # Por enquanto, assumir que serviços não têm PIS/COFINS separados
        # (serão calculados via CBS na reforma)
        base_pis = Decimal('0.00')
        valor_pis = Decimal('0.00')
        base_cofins = Decimal('0.00')
        valor_cofins = Decimal('0.00')
    
    # ═══ CALCULAR REFORMA 2026 (NOVO) ═══
    usar_reforma = False
    if config_fiscal:
        usar_reforma = config_fiscal.usar_reforma_2026
    
    if usar_reforma and item_fiscal:
        # Obter classificação tributária
        cclass_trib = getattr(item_fiscal, 'cclass_trib', None)
        cst_ibs = getattr(item_fiscal, 'cst_ibs', None)
        cst_cbs = getattr(item_fiscal, 'cst_cbs', None)
        
        # Obter alíquotas (prioridade: item > config > default)
        if hasattr(item_fiscal, 'aliquota_ibs') and item_fiscal.aliquota_ibs:
            aliquota_ibs = item_fiscal.aliquota_ibs
        elif config_fiscal and hasattr(config_fiscal, 'aliquota_ibs_padrao_2026'):
            aliquota_ibs = config_fiscal.aliquota_ibs_padrao_2026
        else:
            aliquota_ibs = Decimal('0.10')  # Default 2026
        
        if hasattr(item_fiscal, 'aliquota_cbs') and item_fiscal.aliquota_cbs:
            aliquota_cbs = item_fiscal.aliquota_cbs
        elif config_fiscal and hasattr(config_fiscal, 'aliquota_cbs_padrao_2026'):
            aliquota_cbs = config_fiscal.aliquota_cbs_padrao_2026
        else:
            aliquota_cbs = Decimal('0.90')  # Default 2026
        
        # Cálculo IBS
        base_ibs = base_calculo
        valor_ibs = base_ibs * (aliquota_ibs / Decimal('100.00'))
        
        # Cálculo CBS
        base_cbs = base_calculo
        valor_cbs = base_cbs * (aliquota_cbs / Decimal('100.00'))
    
    # ═══ RETORNAR TUDO ═══
    return {
        # Impostos atuais (mantidos)
        'base_icms': base_icms,
        'valor_icms': valor_icms,
        'base_icms_st': base_icms_st,
        'valor_icms_st': valor_icms_st,
        'base_pis': base_pis,
        'valor_pis': valor_pis,
        'base_cofins': base_cofins,
        'valor_cofins': valor_cofins,
        'base_ipi': base_ipi,
        'valor_ipi': valor_ipi,
        # Reforma 2026 (novos)
        'base_ibs': base_ibs,
        'valor_ibs': valor_ibs,
        'aliquota_ibs': aliquota_ibs,
        'base_cbs': base_cbs,
        'valor_cbs': valor_cbs,
        'aliquota_cbs': aliquota_cbs,
        'cclass_trib': cclass_trib,
        'cst_ibs': cst_ibs,
        'cst_cbs': cst_cbs,
    }


def calcular_impostos_nota(itens: List, regime_tributario=None, config_fiscal=None) -> Dict[str, Decimal]:
    """
    Calcula os impostos totais da nota fiscal somando todos os itens.
    
    AGORA TAMBÉM SUPORTA: Reforma Tributária 2026 (CBS/IBS)
    
    IMPORTANTE: Para Simples Nacional, os impostos não são calculados separadamente.
    Apenas informa-se a base de cálculo para fins de informação na NF-e.
    
    Args:
        itens: Lista de ItemPedidoVenda
        regime_tributario: Regime tributário da empresa ('SIMPLES_NACIONAL', etc.)
        config_fiscal: ConfiguracaoFiscalLoja (opcional, para feature flag da reforma)
        
    Returns:
        Dict com os totais calculados (impostos atuais + reforma 2026)
    """
    totais = {
        # Impostos atuais (mantidos)
        'base_icms': Decimal('0.00'),
        'valor_icms': Decimal('0.00'),
        'base_icms_st': Decimal('0.00'),
        'valor_icms_st': Decimal('0.00'),
        'base_pis': Decimal('0.00'),
        'valor_pis': Decimal('0.00'),
        'base_cofins': Decimal('0.00'),
        'valor_cofins': Decimal('0.00'),
        'base_ipi': Decimal('0.00'),
        'valor_ipi': Decimal('0.00'),
        'valor_produtos': Decimal('0.00'),
        'valor_frete': Decimal('0.00'),
        'valor_seguro': Decimal('0.00'),
        'valor_desconto': Decimal('0.00'),
        'valor_outras_despesas': Decimal('0.00'),
        'regime_tributario': regime_tributario or '',
        'is_simples_nacional': regime_tributario and 'SIMPLES' in (regime_tributario or '').upper(),
        # Reforma 2026 (novos)
        'base_ibs': Decimal('0.00'),
        'valor_ibs': Decimal('0.00'),
        'base_cbs': Decimal('0.00'),
        'valor_cbs': Decimal('0.00'),
    }
    
    for item in itens:
        # Calcular impostos do item (inclui CBS/IBS se ativado)
        impostos_item = calcular_impostos_item(item, regime_tributario, config_fiscal)
        
        # Somar totais atuais
        totais['base_icms'] += impostos_item['base_icms']
        totais['valor_icms'] += impostos_item['valor_icms']
        totais['base_icms_st'] += impostos_item['base_icms_st']
        totais['valor_icms_st'] += impostos_item['valor_icms_st']
        totais['base_pis'] += impostos_item['base_pis']
        totais['valor_pis'] += impostos_item['valor_pis']
        totais['base_cofins'] += impostos_item['base_cofins']
        totais['valor_cofins'] += impostos_item['valor_cofins']
        totais['base_ipi'] += impostos_item['base_ipi']
        totais['valor_ipi'] += impostos_item['valor_ipi']
        totais['valor_produtos'] += item.total
        
        # Somar totais reforma 2026
        totais['base_ibs'] += impostos_item.get('base_ibs', Decimal('0.00'))
        totais['valor_ibs'] += impostos_item.get('valor_ibs', Decimal('0.00'))
        totais['base_cbs'] += impostos_item.get('base_cbs', Decimal('0.00'))
        totais['valor_cbs'] += impostos_item.get('valor_cbs', Decimal('0.00'))
    
    return totais

