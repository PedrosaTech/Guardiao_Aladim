"""
Serializers do módulo de orçamentos.
"""
from rest_framework import serializers
from .models import OrcamentoVenda, ItemOrcamentoVenda


class ItemOrcamentoVendaSerializer(serializers.ModelSerializer):
    """
    Serializer para ItemOrcamentoVenda.
    """
    produto_descricao = serializers.CharField(source='produto.descricao', read_only=True)
    produto_codigo = serializers.CharField(source='produto.codigo_interno', read_only=True)
    
    class Meta:
        model = ItemOrcamentoVenda
        fields = [
            'id', 'orcamento', 'produto', 'produto_descricao', 'produto_codigo',
            'descricao_produto', 'classe_risco', 'subclasse_risco',
            'quantidade', 'valor_unitario', 'desconto', 'valor_total',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class OrcamentoVendaSerializer(serializers.ModelSerializer):
    """
    Serializer para OrcamentoVenda com itens nested.
    """
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome_razao_social', read_only=True, allow_null=True)
    vendedor_nome = serializers.CharField(source='vendedor.get_full_name', read_only=True)
    pedido_gerado_id = serializers.IntegerField(source='pedido_gerado.id', read_only=True, allow_null=True)
    condicao_pagamento_nome = serializers.CharField(
        source='condicao_pagamento_prevista.nome',
        read_only=True,
        allow_null=True
    )
    
    itens = ItemOrcamentoVendaSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrcamentoVenda
        fields = [
            'id', 'empresa', 'empresa_nome', 'loja', 'loja_nome',
            'cliente', 'cliente_nome', 'vendedor', 'vendedor_nome',
            'pedido_gerado', 'pedido_gerado_id',
            'nome_responsavel', 'telefone_contato', 'whatsapp_contato', 'email_contato',
            'origem', 'tipo_operacao', 'data_emissao', 'data_validade', 'status',
            'total_bruto', 'desconto_total', 'acrescimo_total', 'total_liquido',
            'condicao_pagamento_prevista', 'condicao_pagamento_nome',
            'observacoes', 'itens',
            'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'total_bruto', 'total_liquido'
        ]

