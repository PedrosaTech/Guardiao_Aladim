"""
Serializers do app pdv.
"""
from rest_framework import serializers
from .models import CaixaSessao, Pagamento


class CaixaSessaoSerializer(serializers.ModelSerializer):
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    usuario_abertura_username = serializers.CharField(source='usuario_abertura.username', read_only=True)
    usuario_fechamento_username = serializers.CharField(source='usuario_fechamento.username', read_only=True, allow_null=True)
    
    class Meta:
        model = CaixaSessao
        fields = '__all__'
        read_only_fields = ['data_hora_abertura', 'created_at', 'updated_at', 'created_by', 'updated_by']


class PagamentoSerializer(serializers.ModelSerializer):
    pedido_id = serializers.IntegerField(source='pedido.id', read_only=True)
    caixa_sessao_id = serializers.IntegerField(source='caixa_sessao.id', read_only=True)
    
    class Meta:
        model = Pagamento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

