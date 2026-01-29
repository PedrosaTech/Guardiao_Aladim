"""
Serviços do módulo fiscal.
"""
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import NotaFiscalSaida, ConfiguracaoFiscalLoja
from vendas.models import PedidoVenda
import logging

logger = logging.getLogger(__name__)


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


def criar_nfe_rascunho_para_pedido(pedido: PedidoVenda, usuario=None) -> NotaFiscalSaida:
    """
    Cria uma NF-e RASCUNHO a partir de um PedidoVenda qualquer.
    
    Esta função é genérica e funciona para qualquer tipo de pedido (BALCAO, EXTERNA, EVENTO, etc).
    Para pedidos do tipo EVENTO, use criar_nfe_rascunho_para_pedido_evento() que inclui
    o relacionamento com EventoVenda.
    
    Args:
        pedido: PedidoVenda a ser convertido em nota fiscal
        usuario: Usuário que está criando a nota (opcional)
        
    Returns:
        NotaFiscalSaida criada com status RASCUNHO
        
    Raises:
        ValidationError: Se houver erro de validação
    """
    # Verificar se já existe uma NF-e para este pedido
    nota_existente = NotaFiscalSaida.objects.filter(
        pedido_venda=pedido,
        tipo_documento='NFE',
        is_active=True
    ).first()
    
    if nota_existente:
        logger.info(f"Nota fiscal já existe para pedido {pedido.id}: {nota_existente.numero}/{nota_existente.serie}")
        return nota_existente
    
    # Validações básicas
    if not pedido.itens.filter(is_active=True).exists():
        raise ValidationError(f"Pedido #{pedido.id} não possui itens ativos")
    
    # Buscar configuração fiscal da loja
    config_fiscal = None
    try:
        config_fiscal = ConfiguracaoFiscalLoja.objects.get(loja=pedido.loja, is_active=True)
    except ConfiguracaoFiscalLoja.DoesNotExist:
        logger.warning(f"Loja {pedido.loja.id} não possui configuração fiscal. Usando valores padrão.")
    
    # Determinar número e série
    if config_fiscal:
        serie = config_fiscal.serie_nfe
        # Buscar o próximo número disponível
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
        
        # Incrementar proximo_numero_nfe na configuração
        config_fiscal.proximo_numero_nfe = numero + 1
        config_fiscal.save(update_fields=['proximo_numero_nfe', 'updated_at'])
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
    
    # Determinar tipo de documento baseado no tipo de venda
    # Para vendas de balcão, pode ser NFC-e, mas por enquanto usamos NF-e
    tipo_documento = 'NFE'
    if pedido.tipo_venda == 'BALCAO':
        # TODO: No futuro, pode ser NFC-e para vendas de balcão
        tipo_documento = 'NFE'
    
    # Buscar evento se for pedido de evento
    evento = None
    if pedido.tipo_venda == 'EVENTO':
        try:
            from eventos.models import EventoVenda
            evento = EventoVenda.objects.filter(pedido=pedido).first()
        except:
            pass
    
    # Criar NotaFiscalSaida
    nota = NotaFiscalSaida.objects.create(
        loja=pedido.loja,
        cliente=pedido.cliente,
        pedido_venda=pedido,
        evento=evento,
        tipo_documento=tipo_documento,
        numero=numero,
        serie=serie,
        chave_acesso='',  # Será preenchida quando gerar o XML
        valor_total=pedido.valor_total,
        xml_arquivo='',  # TODO: Montar XML da NF-e com base nos itens do pedido
        status='RASCUNHO',
        data_emissao=timezone.now(),
        created_by=usuario or pedido.created_by,
    )
    
    logger.info(
        f"Nota fiscal criada: {nota.numero}/{nota.serie} para pedido {pedido.id} "
        f"(Tipo: {pedido.tipo_venda})"
    )
    
    return nota

