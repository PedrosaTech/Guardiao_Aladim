"""
Serializers do app produtos.
"""
from rest_framework import serializers
from .models import CategoriaProduto, Produto


class CategoriaProdutoSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)
    
    class Meta:
        model = CategoriaProduto
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class ProdutoSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True, allow_null=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    
    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

