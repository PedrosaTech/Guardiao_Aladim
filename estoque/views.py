"""
Views do app estoque.
"""
from rest_framework import viewsets
from .models import LocalEstoque, EstoqueAtual, MovimentoEstoque
from .serializers import LocalEstoqueSerializer, EstoqueAtualSerializer, MovimentoEstoqueSerializer


class LocalEstoqueViewSet(viewsets.ModelViewSet):
    queryset = LocalEstoque.objects.filter(is_active=True)
    serializer_class = LocalEstoqueSerializer


class EstoqueAtualViewSet(viewsets.ModelViewSet):
    queryset = EstoqueAtual.objects.filter(is_active=True)
    serializer_class = EstoqueAtualSerializer


class MovimentoEstoqueViewSet(viewsets.ModelViewSet):
    queryset = MovimentoEstoque.objects.all()
    serializer_class = MovimentoEstoqueSerializer

