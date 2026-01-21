"""
Serializers do app vendas.
"""
from rest_framework import serializers
from .models import CondicaoPagamento, PedidoVenda, ItemPedidoVenda


class CondicaoPagamentoSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)
    
    class Meta:
        model = CondicaoPagamento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class ItemPedidoVendaSerializer(serializers.ModelSerializer):
    produto_descricao = serializers.CharField(source='produto.descricao', read_only=True)
    produto_codigo = serializers.CharField(source='produto.codigo_interno', read_only=True)
    
    class Meta:
        model = ItemPedidoVenda
        fields = '__all__'
        read_only_fields = ['total', 'created_at', 'updated_at', 'created_by', 'updated_by']


class PedidoVendaSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome_razao_social', read_only=True)
    vendedor_username = serializers.CharField(source='vendedor.username', read_only=True)
    condicao_pagamento_nome = serializers.CharField(source='condicao_pagamento.nome', read_only=True)
    itens = ItemPedidoVendaSerializer(many=True, read_only=True)
    
    class Meta:
        model = PedidoVenda
        fields = '__all__'
        read_only_fields = ['data_emissao', 'created_at', 'updated_at', 'created_by', 'updated_by']

