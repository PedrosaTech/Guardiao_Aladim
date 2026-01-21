"""
Serializers do app pessoas.
"""
from rest_framework import serializers
from .models import Cliente, Fornecedor


class ClienteSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True, allow_null=True)
    
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class FornecedorSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)
    
    class Meta:
        model = Fornecedor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

