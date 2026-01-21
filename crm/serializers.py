"""
Serializers do app crm.
"""
from rest_framework import serializers
from .models import Lead, InteracaoCRM


class LeadSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True, allow_null=True)
    
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class InteracaoCRMSerializer(serializers.ModelSerializer):
    lead_nome = serializers.CharField(source='lead.nome', read_only=True, allow_null=True)
    cliente_nome = serializers.CharField(source='cliente.nome_razao_social', read_only=True, allow_null=True)
    
    class Meta:
        model = InteracaoCRM
        fields = '__all__'
        read_only_fields = ['data_hora', 'created_at', 'updated_at', 'created_by', 'updated_by']

