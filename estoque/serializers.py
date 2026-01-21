"""
Serializers do app estoque.
"""
from rest_framework import serializers
from .models import LocalEstoque, EstoqueAtual, MovimentoEstoque


class LocalEstoqueSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    
    class Meta:
        model = LocalEstoque
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class EstoqueAtualSerializer(serializers.ModelSerializer):
    produto_descricao = serializers.CharField(source='produto.descricao', read_only=True)
    produto_codigo = serializers.CharField(source='produto.codigo_interno', read_only=True)
    local_nome = serializers.CharField(source='local_estoque.nome', read_only=True)
    
    class Meta:
        model = EstoqueAtual
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class MovimentoEstoqueSerializer(serializers.ModelSerializer):
    produto_descricao = serializers.CharField(source='produto.descricao', read_only=True)
    produto_codigo = serializers.CharField(source='produto.codigo_interno', read_only=True)
    local_origem_nome = serializers.CharField(source='local_origem.nome', read_only=True, allow_null=True)
    local_destino_nome = serializers.CharField(source='local_destino.nome', read_only=True, allow_null=True)
    
    class Meta:
        model = MovimentoEstoque
        fields = '__all__'
        read_only_fields = ['data_movimento', 'created_at', 'updated_at', 'created_by', 'updated_by']

