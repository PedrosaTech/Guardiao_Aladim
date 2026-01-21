"""
Serializers do app eventos.
"""
from rest_framework import serializers
from .models import EventoVenda


class EventoVendaSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    lead_nome = serializers.CharField(source='lead.nome', read_only=True, allow_null=True)
    cliente_nome = serializers.CharField(source='cliente.nome_razao_social', read_only=True, allow_null=True)
    pedido_id = serializers.IntegerField(source='pedido.id', read_only=True, allow_null=True)
    equipe_responsavel_usuarios = serializers.SerializerMethodField()
    
    class Meta:
        model = EventoVenda
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_equipe_responsavel_usuarios(self, obj):
        """Retorna lista de IDs dos usuários da equipe."""
        return [user.id for user in obj.equipe_responsavel.all()]

