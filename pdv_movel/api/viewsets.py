"""
ViewSets para API do PDV Móvel.

- ProdutosPDVViewSet: busca e lista produtos
- PedidosPDVViewSet: CRUD de pedidos (atendente)
- CaixaPDVViewSet: buscar e finalizar pedidos (caixa)
"""
from decimal import Decimal
from datetime import timedelta

from django.db.models import Q, Sum, Prefetch
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from produtos.models import Produto
from produtos.utils import buscar_produto_por_codigo, buscar_produtos_por_termo
from vendas.models import PedidoVenda, ItemPedidoVenda, CondicaoPagamento
from pessoas.models import Cliente

from .serializers import (
    ProdutoListSerializer,
    ProdutoDetalheSerializer,
    PedidoTabletSerializer,
    PedidoCaixaSerializer,
    ItemPedidoSerializer,
    EstatisticasAtendenteSerializer,
)
from .permissions import IsAtendentePDVAtivo, IsCaixaOuAtendente


class ProdutosPDVViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para listar/buscar produtos no tablet.

    GET /api/produtos/ - Lista produtos
    GET /api/produtos/?busca=... - Busca por nome/código
    GET /api/produtos/?codigo_barras=... - Por código de barras
    GET /api/produtos/{id}/ - Detalhes
    GET /api/produtos/mais_vendidos/ - Top 10 mais vendidos
    """

    serializer_class = ProdutoListSerializer
    permission_classes = [IsAuthenticated, IsAtendentePDVAtivo]

    def get_queryset(self):
        atendente = self.request.user.atendente_pdv
        empresa = atendente.loja.empresa
        codigo_barras = self.request.query_params.get("codigo_barras", "").strip()
        busca = self.request.query_params.get("busca", "").strip()

        if codigo_barras:
            produto, _alt, _mult = buscar_produto_por_codigo(codigo_barras, empresa=empresa)
            if produto:
                return (
                    Produto.objects.filter(pk=produto.pk)
                    .select_related("categoria")
                    .order_by("descricao")
                )
            return Produto.objects.none()

        if busca:
            return buscar_produtos_por_termo(
                busca, empresa=empresa, limit=100,
                order_by=("descricao",), select_related=("categoria",),
            )

        return (
            Produto.objects.filter(is_active=True, empresa=empresa)
            .select_related("categoria")
            .order_by("descricao")[:100]
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProdutoDetalheSerializer
        return ProdutoListSerializer

    @action(detail=False, methods=["get"], url_path="info-codigo")
    def info_codigo(self, request):
        """
        Retorna informações sobre um código de barras (principal ou alternativo).
        GET /api/produtos/info-codigo/?codigo=7891234567890
        """
        codigo = request.query_params.get("codigo", "").strip()
        if not codigo:
            return Response(
                {"erro": "Parâmetro codigo obrigatório"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        atendente = request.user.atendente_pdv
        empresa = atendente.loja.empresa
        produto, codigo_alt, mult = buscar_produto_por_codigo(codigo, empresa=empresa)
        if not produto:
            return Response(
                {"erro": "Produto não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            "codigo": codigo,
            "tipo": "alternativo" if codigo_alt else "principal",
            "produto_id": produto.id,
            "produto_descricao": produto.descricao,
            "multiplicador": float(mult),
            "descricao_codigo": codigo_alt.descricao if codigo_alt else None,
            "codigo_alternativo_id": codigo_alt.id if codigo_alt else None,
        })

    @action(detail=False, methods=["get"])
    def mais_vendidos(self, request):
        atendente = request.user.atendente_pdv
        loja = atendente.loja
        data_inicio = timezone.now() - timedelta(days=30)
        rows = (
            ItemPedidoVenda.objects.filter(
                pedido__loja=loja,
                pedido__created_at__gte=data_inicio,
                pedido__status="FATURADO",
                is_active=True,
            )
            .values("produto")
            .annotate(total_vendido=Sum("quantidade"))
            .order_by("-total_vendido")[:10]
        )
        ids = [r["produto"] for r in rows]
        produtos = Produto.objects.filter(id__in=ids, is_active=True).select_related(
            "categoria"
        )
        # manter ordem por total_vendido
        order = {pid: i for i, pid in enumerate(ids)}
        produtos = sorted(produtos, key=lambda p: order.get(p.id, 999))
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)


class PedidosPDVViewSet(viewsets.ModelViewSet):
    """
    API para gerenciar pedidos no tablet (atendente).

    GET/POST /api/pedidos/
    GET/PUT/DELETE /api/pedidos/{id}/
    POST /api/pedidos/{id}/adicionar_item/
    POST /api/pedidos/{id}/remover_item/
    GET /api/pedidos/estatisticas/
    """

    serializer_class = PedidoTabletSerializer
    permission_classes = [IsAuthenticated, IsAtendentePDVAtivo]

    def _prefetch_itens(self, qs):
        return qs.prefetch_related(
            Prefetch(
                "itens",
                queryset=ItemPedidoVenda.objects.filter(is_active=True).select_related(
                    "produto"
                ),
            )
        )

    def get_queryset(self):
        atendente = self.request.user.atendente_pdv
        qs = (
            PedidoVenda.objects.filter(
                atendente_tablet=atendente,
                is_active=True,
            )
            .select_related("cliente", "loja", "atendente_tablet__user", "condicao_pagamento")
        )
        qs = self._prefetch_itens(qs)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        # Em ações detail (adicionar_item, remover_item, etc.) não filtrar por hoje:
        # o pedido acabou de ser criado e pode haver edge case de timezone.
        if not self.kwargs.get("pk"):
            apenas_hoje = self.request.query_params.get("hoje", "true").lower()
            if apenas_hoje == "true":
                hoje = timezone.now().date()
                qs = qs.filter(created_at__date=hoje)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        atendente = self.request.user.atendente_pdv
        try:
            config = atendente.loja.config_pdv_movel
        except Exception:
            config = None
        exigir_cliente = config.exigir_cliente if config else False

        data = serializer.validated_data
        cliente = data.get("cliente")
        if not cliente and exigir_cliente:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"cliente": "Cliente é obrigatório nas configurações do PDV Móvel."})

        if not cliente:
            cliente, _ = Cliente.objects.get_or_create(
                empresa=atendente.loja.empresa,
                tipo_pessoa="PF",
                nome_razao_social="Consumidor Final",
                cpf_cnpj="00000000000",
                defaults={"created_by": self.request.user},
            )

        condicao = data.get("condicao_pagamento")
        if not condicao:
            condicao = CondicaoPagamento.objects.filter(
                empresa=atendente.loja.empresa,
                numero_parcelas=1,
                dias_entre_parcelas=0,
                is_active=True,
            ).first()
            if not condicao:
                condicao = CondicaoPagamento.objects.filter(
                    empresa=atendente.loja.empresa,
                    nome__icontains="vista",
                    is_active=True,
                ).first()
            if not condicao:
                condicao = CondicaoPagamento.objects.create(
                    empresa=atendente.loja.empresa,
                    nome="À Vista",
                    numero_parcelas=1,
                    dias_entre_parcelas=0,
                    created_by=self.request.user,
                )

        tipo_venda = data.get("tipo_venda") or "BALCAO"
        observacoes = data.get("observacoes")
        forma_pagamento_pretendida = data.get("forma_pagamento_pretendida") or "NAO_INFORMADO"

        serializer.save(
            loja=atendente.loja,
            vendedor=self.request.user,
            atendente_tablet=atendente,
            origem="TABLET",
            status="AGUARDANDO_PAGAMENTO",
            cliente=cliente,
            condicao_pagamento=condicao,
            tipo_venda=tipo_venda,
            observacoes=observacoes or None,
            forma_pagamento_pretendida=forma_pagamento_pretendida,
            valor_total=Decimal("0.00"),
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        pedido = self.get_object()
        if pedido.status not in ("AGUARDANDO_PAGAMENTO", "ORCAMENTO"):
            raise PermissionDenied(
                f"Pedido não pode mais ser editado (status: {pedido.status})"
            )
        try:
            config = pedido.loja.config_pdv_movel
        except Exception:
            config = None
        if not config or not config.permitir_edicao_pedido:
            raise PermissionDenied("Edição de pedidos desabilitada nas configurações.")
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status == "FATURADO":
            raise PermissionDenied("Não é possível cancelar pedido faturado.")
        instance.is_active = False
        instance.status = "CANCELADO"
        instance.updated_by = self.request.user
        instance.save(update_fields=["is_active", "status", "updated_by", "updated_at"])

    def _recalcular_total_pedido(self, pedido):
        pedido.recalcular_total()

    @action(detail=True, methods=["post"], url_path="adicionar_item")
    def adicionar_item(self, request, pk=None):
        pedido = self.get_object()
        if pedido.status not in ("AGUARDANDO_PAGAMENTO", "ORCAMENTO"):
            return Response(
                {"erro": "Pedido não pode mais ser editado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = ItemPedidoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        codigo_barras_usado = (ser.validated_data.get("codigo_barras_usado") or "").strip() or None
        codigo_alt = ser.validated_data.get("codigo_alternativo_usado")
        multiplicador_aplicado = ser.validated_data.get("multiplicador_aplicado") or Decimal("1.000")
        item = ItemPedidoVenda.objects.create(
            pedido=pedido,
            produto=ser.validated_data["produto"],
            quantidade=ser.validated_data["quantidade"],
            preco_unitario=ser.validated_data["preco_unitario"],
            desconto=ser.validated_data.get("desconto") or Decimal("0.00"),
            codigo_barras_usado=codigo_barras_usado,
            codigo_alternativo_usado=codigo_alt,
            multiplicador_aplicado=multiplicador_aplicado,
            created_by=request.user,
        )
        self._recalcular_total_pedido(pedido)
        pedido.refresh_from_db()
        out = self._prefetch_itens(
            PedidoVenda.objects.filter(pk=pedido.pk).select_related(
                "cliente", "loja", "atendente_tablet__user", "condicao_pagamento"
            )
        ).first()
        return Response(
            PedidoTabletSerializer(out).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="remover_item")
    def remover_item(self, request, pk=None):
        pedido = self.get_object()
        if pedido.status not in ("AGUARDANDO_PAGAMENTO", "ORCAMENTO"):
            return Response(
                {"erro": "Pedido não pode mais ser editado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item_id = request.data.get("item_id")
        if not item_id:
            return Response(
                {"erro": "item_id é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            item = pedido.itens.get(id=item_id, is_active=True)
        except ItemPedidoVenda.DoesNotExist:
            return Response(
                {"erro": "Item não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.is_active = False
        item.updated_by = request.user
        item.save(update_fields=["is_active", "updated_by", "updated_at"])
        self._recalcular_total_pedido(pedido)
        pedido.refresh_from_db()
        out = self._prefetch_itens(
            PedidoVenda.objects.filter(pk=pedido.pk).select_related(
                "cliente", "loja", "atendente_tablet__user", "condicao_pagamento"
            )
        ).first()
        return Response(PedidoTabletSerializer(out).data)

    @action(detail=False, methods=["get"])
    def estatisticas(self, request):
        atendente = request.user.atendente_pdv
        hoje = timezone.now().date()
        qs = PedidoVenda.objects.filter(
            atendente_tablet=atendente,
            created_at__date=hoje,
            is_active=True,
        )
        total_pedidos = qs.count()
        aguardando = qs.filter(status="AGUARDANDO_PAGAMENTO").count()
        finalizados = qs.filter(status="FATURADO").count()
        abandonados = qs.filter(status="ABANDONADO").count()
        agg = qs.filter(status="FATURADO").aggregate(
            total=Sum("valor_total"),
        )
        valor_total = agg["total"] or Decimal("0.00")
        ticket_medio = (valor_total / finalizados) if finalizados > 0 else Decimal("0.00")
        stats = {
            "total_pedidos": total_pedidos,
            "aguardando_pagamento": aguardando,
            "finalizados": finalizados,
            "abandonados": abandonados,
            "valor_total": valor_total,
            "ticket_medio": ticket_medio,
        }
        ser = EstatisticasAtendenteSerializer(stats)
        return Response(ser.data)


class CaixaPDVViewSet(viewsets.ViewSet):
    """
    API para o caixa buscar e finalizar pedidos do tablet.

    GET /api/caixa/buscar/?numero=...
    POST /api/caixa/{id}/finalizar/
    """

    permission_classes = [IsAuthenticated, IsCaixaOuAtendente]

    @action(detail=False, methods=["get"])
    def buscar(self, request):
        numero = request.query_params.get("numero", "").strip()
        if not numero:
            return Response(
                {"erro": "Número do pedido é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            pedido_id = int(numero.lstrip("0") or "0")
        except (ValueError, TypeError):
            return Response(
                {"erro": "Número inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if pedido_id <= 0:
            return Response(
                {"erro": "Pedido não encontrado ou já finalizado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = (
            PedidoVenda.objects.filter(
                pk=pedido_id,
                origem="TABLET",
                status="AGUARDANDO_PAGAMENTO",
                is_active=True,
            )
            .select_related("cliente", "atendente_tablet__user", "condicao_pagamento")
            .prefetch_related(
                Prefetch(
                    "itens",
                    queryset=ItemPedidoVenda.objects.filter(is_active=True).select_related(
                        "produto"
                    ),
                )
            )
        )
        pedido = qs.first()
        if not pedido:
            return Response(
                {"erro": "Pedido não encontrado ou já finalizado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PedidoCaixaSerializer(pedido).data)

    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request, pk=None):
        try:
            pedido = PedidoVenda.objects.get(
                pk=pk,
                origem="TABLET",
                status="AGUARDANDO_PAGAMENTO",
                is_active=True,
            )
        except PedidoVenda.DoesNotExist:
            return Response(
                {"erro": "Pedido não encontrado ou já finalizado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        pedido.status = "FATURADO"
        pedido.updated_by = request.user
        pedido.save(update_fields=["status", "updated_by", "updated_at"])
        return Response(
            {
                "sucesso": True,
                "pedido_id": pedido.id,
                "numero": f"{pedido.id:04d}",
                "valor_total": float(pedido.valor_total),
            }
        )
