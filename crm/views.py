"""
Views do app crm.
"""
from rest_framework import viewsets
from .models import Lead, InteracaoCRM
from .serializers import LeadSerializer, InteracaoCRMSerializer


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.filter(is_active=True)
    serializer_class = LeadSerializer


class InteracaoCRMViewSet(viewsets.ModelViewSet):
    queryset = InteracaoCRM.objects.all()
    serializer_class = InteracaoCRMSerializer

