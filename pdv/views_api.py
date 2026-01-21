"""
Views API do app pdv.
"""
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.core.exceptions import ValidationError
from produtos.models import Produto
from .models import CaixaSessao, Pagamento
from .serializers import CaixaSessaoSerializer, PagamentoSerializer
from .validators import validar_cpf, formatar_cpf, calcular_idade, validar_idade_minima


class CaixaSessaoViewSet(viewsets.ModelViewSet):
    queryset = CaixaSessao.objects.all()
    serializer_class = CaixaSessaoSerializer


class PagamentoViewSet(viewsets.ModelViewSet):
    queryset = Pagamento.objects.all()
    serializer_class = PagamentoSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_produtos_pdv(request):
    """
    API para buscar produtos no PDV.
    
    GET /api/v1/pdv/produtos/?q=termo
    
    Retorna lista de produtos que correspondem ao termo de busca.
    """
    termo = request.query_params.get('q', '').strip()
    
    if not termo:
        return Response({'erro': 'Parâmetro q é obrigatório'}, status=400)
    
    # Busca APENAS por código numérico (código interno ou código de barras)
    # Remove espaços e caracteres não numéricos para busca mais flexível
    termo_limpo = ''.join(filter(str.isdigit, termo))
    
    produtos = Produto.objects.filter(
        is_active=True
    ).filter(
        Q(codigo_interno__icontains=termo_limpo) |
        Q(codigo_barras__icontains=termo_limpo)
    )[:20]  # Limita a 20 resultados
    
    resultados = []
    for produto in produtos:
        resultados.append({
            'id': produto.id,
            'codigo_interno': produto.codigo_interno,
            'codigo_barras': produto.codigo_barras or '',
            'descricao': produto.descricao,
            'preco_venda_sugerido': str(produto.preco_venda_sugerido),
            'unidade_comercial': produto.unidade_comercial,
            'possui_restricao_exercito': produto.possui_restricao_exercito,
            'classe_risco': produto.classe_risco,
        })
    
    return Response({'produtos': resultados})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validar_comprador_pirotecnia(request):
    """
    API para validar dados do comprador de produtos pirotécnicos.
    
    POST /api/v1/pdv/validar-comprador/
    
    Body:
    {
        "cpf": "123.456.789-00",
        "data_nascimento": "1990-01-01",
        "nome_completo": "Nome do Comprador"
    }
    
    Retorna validação de CPF e idade.
    """
    try:
        cpf = request.data.get('cpf', '').strip()
        data_nascimento = request.data.get('data_nascimento', '').strip()
        nome_completo = request.data.get('nome_completo', '').strip()
        
        erros = {}
        
        # Valida CPF
        cpf_formatado = None
        if not cpf:
            erros['cpf'] = 'CPF é obrigatório'
        else:
            try:
                cpf_limpo = validar_cpf(cpf)
                cpf_formatado = formatar_cpf(cpf_limpo)
            except ValidationError as e:
                erros['cpf'] = str(e)
                cpf_formatado = None
        
        # Valida data de nascimento
        idade = None
        if not data_nascimento:
            erros['data_nascimento'] = 'Data de nascimento é obrigatória'
        else:
            try:
                from datetime import datetime
                data_nasc = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                validar_idade_minima(data_nasc, idade_minima=18)
                idade = calcular_idade(data_nasc)
            except ValueError:
                erros['data_nascimento'] = 'Data de nascimento inválida'
            except ValidationError as e:
                erros['data_nascimento'] = str(e)
                idade = None
        
        # Valida nome
        if not nome_completo:
            erros['nome_completo'] = 'Nome completo é obrigatório'
        
        if erros:
            return Response({'valido': False, 'erros': erros}, status=400)
        
        return Response({
            'valido': True,
            'cpf_formatado': cpf_formatado,
            'idade': idade,
            'maior_idade': idade >= 18
        })
    
    except Exception as e:
        return Response({'valido': False, 'erro': str(e)}, status=500)
