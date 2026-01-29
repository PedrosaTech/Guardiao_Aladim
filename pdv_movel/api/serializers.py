"""
Serializers para API do PDV Móvel.
Otimizados para tráfego tablet ↔ servidor.
"""
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers

from produtos.models import Produto
from vendas.models import PedidoVenda, ItemPedidoVenda, CondicaoPagamento
from pessoas.models import Cliente
from estoque.models import EstoqueAtual


def _estoque_produto_loja(produto, loja):
    if not loja:
        return 0
    qs = EstoqueAtual.objects.filter(
        produto=produto,
        local_estoque__loja=loja,
        is_active=True,
    )
    result = qs.aggregate(s=Sum("quantidade"))["s"]
    return float(result) if result is not None else 0


class ProdutoListSerializer(serializers.ModelSerializer):
    estoque_disponivel = serializers.SerializerMethodField()
    categoria_nome = serializers.CharField(
        source="categoria.nome",
        read_only=True,
        default="",
    )

    class Meta:
        model = Produto
        fields = [
            "id",
            "codigo_interno",
            "codigo_barras",
            "descricao",
            "preco_venda_sugerido",
            "unidade_comercial",
            "estoque_disponivel",
            "categoria_nome",
            "is_active",
        ]

    def get_estoque_disponivel(self, obj):
        request = self.context.get("request")
        loja = None
        if request and hasattr(request.user, "atendente_pdv"):
            try:
                loja = request.user.atendente_pdv.loja
            except Exception:
                pass
        return _estoque_produto_loja(obj, loja)


class ProdutoDetalheSerializer(serializers.ModelSerializer):
    estoque_disponivel = serializers.SerializerMethodField()
    categoria_nome = serializers.CharField(
        source="categoria.nome",
        read_only=True,
        default="",
    )

    class Meta:
        model = Produto
        fields = [
            "id",
            "codigo_interno",
            "codigo_barras",
            "descricao",
            "observacoes",
            "preco_venda_sugerido",
            "unidade_comercial",
            "estoque_disponivel",
            "categoria_nome",
            "ncm",
            "is_active",
        ]

    def get_estoque_disponivel(self, obj):
        request = self.context.get("request")
        loja = None
        if request and hasattr(request.user, "atendente_pdv"):
            try:
                loja = request.user.atendente_pdv.loja
            except Exception:
                pass
        return _estoque_produto_loja(obj, loja)


class ItemPedidoSerializer(serializers.ModelSerializer):
    produto_descricao = serializers.CharField(
        source="produto.descricao",
        read_only=True,
    )
    produto_codigo = serializers.CharField(
        source="produto.codigo_interno",
        read_only=True,
    )

    class Meta:
        model = ItemPedidoVenda
        fields = [
            "id",
            "produto",
            "produto_descricao",
            "produto_codigo",
            "quantidade",
            "preco_unitario",
            "desconto",
            "total",
            "codigo_barras_usado",
            "codigo_alternativo_usado",
            "multiplicador_aplicado",
        ]
        read_only_fields = ["total"]

    def validate(self, attrs):
        quantidade = attrs.get("quantidade") or 0
        preco_unitario = attrs.get("preco_unitario") or 0
        desconto = attrs.get("desconto") or 0
        if isinstance(quantidade, (int, float)):
            quantidade = Decimal(str(quantidade))
        if isinstance(preco_unitario, (int, float)):
            preco_unitario = Decimal(str(preco_unitario))
        if isinstance(desconto, (int, float)):
            desconto = Decimal(str(desconto))
        if quantidade <= 0:
            raise serializers.ValidationError({"quantidade": "Quantidade deve ser maior que zero"})
        if preco_unitario <= 0:
            raise serializers.ValidationError({"preco_unitario": "Preço deve ser maior que zero"})
        subtotal = quantidade * preco_unitario
        if desconto > subtotal:
            raise serializers.ValidationError(
                {"desconto": "Desconto não pode ser maior que o subtotal"}
            )
        return attrs


class ClienteResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            "id",
            "nome_razao_social",
            "cpf_cnpj",
            "telefone",
        ]


class PedidoTabletSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    cliente_nome = serializers.CharField(
        source="cliente.nome_razao_social",
        read_only=True,
        allow_null=True,
    )
    atendente_nome = serializers.SerializerMethodField()
    numero = serializers.SerializerMethodField()
    valor_desconto = serializers.SerializerMethodField()
    tempo_criacao = serializers.SerializerMethodField()

    class Meta:
        model = PedidoVenda
        fields = [
            "id",
            "numero",
            "status",
            "origem",
            "cliente",
            "cliente_nome",
            "condicao_pagamento",
            "tipo_venda",
            "atendente_nome",
            "valor_total",
            "valor_desconto",
            "observacoes",
            "forma_pagamento_pretendida",
            "itens",
            "created_at",
            "tempo_criacao",
        ]
        read_only_fields = [
            "numero",
            "origem",
            "valor_total",
            "atendente_nome",
            "created_at",
        ]
        extra_kwargs = {
            "cliente": {"required": False},
            "condicao_pagamento": {"required": False},
            "tipo_venda": {"required": False},
            "forma_pagamento_pretendida": {"required": False},
        }

    def get_numero(self, obj):
        return f"{obj.id:04d}"

    def get_valor_desconto(self, obj):
        total = sum(
            (item.desconto for item in obj.itens.filter(is_active=True)),
            Decimal("0.00"),
        )
        return total

    def get_atendente_nome(self, obj):
        if obj.atendente_tablet_id and hasattr(obj, "atendente_tablet") and obj.atendente_tablet:
            u = obj.atendente_tablet.user
            return u.get_full_name() or u.username
        return None

    def get_tempo_criacao(self, obj):
        agora = timezone.now()
        diff = agora - obj.created_at
        if diff < timedelta(minutes=1):
            return "Agora"
        if diff < timedelta(hours=1):
            mins = int(diff.total_seconds() / 60)
            return f"Há {mins} min"
        if diff < timedelta(days=1):
            horas = int(diff.total_seconds() / 3600)
            return f"Há {horas}h"
        return obj.created_at.strftime("%d/%m %H:%M")


class PedidoCaixaSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    cliente = ClienteResumoSerializer(read_only=True)
    atendente_nome = serializers.SerializerMethodField()
    numero = serializers.SerializerMethodField()
    valor_desconto = serializers.SerializerMethodField()
    forma_pagamento_pretendida_label = serializers.SerializerMethodField()

    class Meta:
        model = PedidoVenda
        fields = [
            "id",
            "numero",
            "status",
            "origem",
            "cliente",
            "atendente_nome",
            "valor_total",
            "valor_desconto",
            "observacoes",
            "forma_pagamento_pretendida",
            "forma_pagamento_pretendida_label",
            "itens",
            "created_at",
        ]

    def get_numero(self, obj):
        return f"{obj.id:04d}"

    def get_valor_desconto(self, obj):
        total = sum(
            (item.desconto for item in obj.itens.filter(is_active=True)),
            Decimal("0.00"),
        )
        return total

    def get_atendente_nome(self, obj):
        if obj.atendente_tablet_id and hasattr(obj, "atendente_tablet") and obj.atendente_tablet:
            return obj.atendente_tablet.user.get_full_name() or obj.atendente_tablet.user.username
        return None

    def get_forma_pagamento_pretendida_label(self, obj):
        forma = getattr(obj, "forma_pagamento_pretendida", None) or "NAO_INFORMADO"
        display = getattr(obj, "get_forma_pagamento_pretendida_display", None)
        return display() if callable(display) else forma


class EstatisticasAtendenteSerializer(serializers.Serializer):
    total_pedidos = serializers.IntegerField()
    aguardando_pagamento = serializers.IntegerField()
    finalizados = serializers.IntegerField()
    abandonados = serializers.IntegerField()
    valor_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    ticket_medio = serializers.DecimalField(max_digits=15, decimal_places=2)
