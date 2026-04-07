"""
Modelo de guias de utilizacao do sistema.
"""
from django.db import models

from .base import BaseModel


class GuiaUso(BaseModel):
    """Guia consultivo exibido para usuarios logados."""

    titulo = models.CharField("Titulo", max_length=200)
    slug = models.SlugField("Slug", max_length=220, unique=True)
    categoria = models.CharField("Categoria", max_length=100, blank=True, null=True)
    resumo = models.CharField("Resumo", max_length=255, blank=True, null=True)
    conteudo = models.TextField("Conteudo (Markdown)")
    ordem = models.PositiveIntegerField("Ordem", default=0)
    publicado = models.BooleanField("Publicado", default=True)

    class Meta:
        verbose_name = "Guia de Uso"
        verbose_name_plural = "Guias de Uso"
        ordering = ["ordem", "titulo"]
        indexes = [
            models.Index(fields=["publicado", "is_active"], name="core_guia_pub_ativo_idx"),
            models.Index(fields=["categoria", "ordem"], name="core_guia_cat_ordem_idx"),
        ]

    def __str__(self):
        return self.titulo
