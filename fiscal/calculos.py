"""
Cálculos fiscais conforme normas SEFAZ-BA.
"""
from decimal import Decimal
from typing import Dict, List


def calcular_impostos_item(item, regime_tributario=None) -> Dict[str, Decimal]:
    """
    Calcula os impostos de um item do pedido conforme normas SEFAZ-BA.
    
    IMPORTANTE: Para Simples Nacional (CSOSN 102), os impostos NÃO são calculados
    separadamente, pois já estão embutidos no preço. Apenas informa-se a base de cálculo.
    
    Args:
        item: ItemPedidoVenda com produto relacionado
        regime_tributario: Regime tributário da empresa ('SIMPLES_NACIONAL', 'LUCRO_PRESUMIDO', etc.)
        
    Returns:
        Dict com os valores calculados:
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
        }
    """
    produto = item.produto
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
    
    # Verificar se produto tem campos fiscais
    if not produto:
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
        }
    
    # Base de cálculo para todos os impostos (geralmente o valor do item)
    base_calculo = valor_item
    
    # Verificar regime tributário
    is_simples_nacional = regime_tributario and 'SIMPLES' in regime_tributario.upper()
    
    # ICMS
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
    }


def calcular_impostos_nota(itens: List, regime_tributario=None) -> Dict[str, Decimal]:
    """
    Calcula os impostos totais da nota fiscal somando todos os itens.
    
    IMPORTANTE: Para Simples Nacional, os impostos não são calculados separadamente.
    Apenas informa-se a base de cálculo para fins de informação na NF-e.
    
    Args:
        itens: Lista de ItemPedidoVenda
        regime_tributario: Regime tributário da empresa ('SIMPLES_NACIONAL', etc.)
        
    Returns:
        Dict com os totais calculados
    """
    totais = {
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
    }
    
    for item in itens:
        impostos_item = calcular_impostos_item(item, regime_tributario)
        
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
    
    return totais

