"""
Serviços do módulo fiscal.
"""
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import NotaFiscalSaida, ConfiguracaoFiscalLoja
from vendas.models import PedidoVenda


def criar_nfe_rascunho_para_pedido_evento(pedido: PedidoVenda) -> NotaFiscalSaida:
    """
    Cria uma NF-e RASCUNHO a partir de um PedidoVenda associado a um EventoVenda.
    
    Validações:
    - O pedido deve ter tipo_venda = EVENTO
    - O pedido deve estar associado a um EventoVenda
    
    Args:
        pedido: PedidoVenda do tipo EVENTO
        
    Returns:
        NotaFiscalSaida criada com status RASCUNHO
        
    Raises:
        ValidationError: Se o pedido não for do tipo EVENTO ou não tiver evento associado
        
    TODO: Buscar número e série corretos a partir de ConfiguracaoFiscalLoja.
    TODO: Montar XML da NF-e com base nos itens do pedido.
    TODO: Integrar com SEFAZ-BA (homologação) em outra etapa.
    """
    # Validação: pedido deve ser do tipo EVENTO
    if pedido.tipo_venda != 'EVENTO':
        raise ValidationError(
            f"Pedido #{pedido.id} não é do tipo EVENTO. Tipo atual: {pedido.tipo_venda}"
        )
    
    # Buscar EventoVenda associado ao pedido
    # Usando reverse lookup via related_name 'eventos' do EventoVenda
    try:
        from eventos.models import EventoVenda
        evento = EventoVenda.objects.get(pedido=pedido)
    except EventoVenda.DoesNotExist:
        raise ValidationError(
            f"Pedido #{pedido.id} não está associado a nenhum EventoVenda."
        )
    except EventoVenda.MultipleObjectsReturned:
        # Caso raro: múltiplos eventos com o mesmo pedido (não deveria acontecer)
        evento = EventoVenda.objects.filter(pedido=pedido).first()
    
    # Verificar se já existe uma NF-e para este pedido
    nota_existente = NotaFiscalSaida.objects.filter(
        pedido_venda=pedido,
        tipo_documento='NFE',
        is_active=True
    ).first()
    
    if nota_existente:
        # Se já existe, retorna a existente
        return nota_existente
    
    # Buscar configuração fiscal da loja
    config_fiscal = None
    try:
        config_fiscal = ConfiguracaoFiscalLoja.objects.get(loja=pedido.loja, is_active=True)
    except ConfiguracaoFiscalLoja.DoesNotExist:
        pass
    
    # Determinar número e série
    if config_fiscal:
        serie = config_fiscal.serie_nfe
        # Buscar o próximo número disponível
        # Começa do próximo número da configuração e incrementa até encontrar um disponível
        numero = config_fiscal.proximo_numero_nfe
        max_tentativas = 1000  # Limite de segurança
        
        for tentativa in range(max_tentativas):
            # Verifica se já existe uma nota com esse número/série/loja
            existe = NotaFiscalSaida.objects.filter(
                loja=pedido.loja,
                tipo_documento='NFE',
                serie=serie,
                numero=numero,
                is_active=True
            ).exists()
            
            if not existe:
                # Número disponível, pode usar
                break
            
            # Número já existe, tenta o próximo
            numero += 1
        else:
            # Se chegou aqui, não encontrou número disponível após muitas tentativas
            raise ValidationError(
                f"Não foi possível encontrar um número disponível para NF-e após {max_tentativas} tentativas. "
                "Verifique a configuração fiscal da loja."
            )
        
        # TODO: Incrementar proximo_numero_nfe na configuração após criar a nota (quando for autorizada)
    else:
        # Valores temporários se não houver configuração
        serie = '001'
        # Buscar o maior número existente para essa loja/série e incrementar
        ultima_nota = NotaFiscalSaida.objects.filter(
            loja=pedido.loja,
            tipo_documento='NFE',
            serie=serie,
            is_active=True
        ).order_by('-numero').first()
        
        if ultima_nota:
            numero = ultima_nota.numero + 1
        else:
            numero = 1
    
    # Criar NotaFiscalSaida
    nota = NotaFiscalSaida.objects.create(
        loja=pedido.loja,
        cliente=pedido.cliente,
        pedido_venda=pedido,
        evento=evento,
        tipo_documento='NFE',
        numero=numero,
        serie=serie,
        chave_acesso='',  # Será preenchida quando gerar o XML
        valor_total=pedido.valor_total,
        xml_arquivo='',  # TODO: Montar XML da NF-e com base nos itens do pedido
        status='RASCUNHO',
        data_emissao=timezone.now(),
        created_by=pedido.created_by,
    )
    
    return nota

