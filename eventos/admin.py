"""
Admin para modelos de eventos.
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import EventoVenda
from fiscal.services import criar_nfe_rascunho_para_pedido_evento


@admin.action(description='Gerar/abrir Pedido de Venda do Evento')
def gerar_abrir_pedido_evento(modeladmin, request, queryset):
    """
    Action para gerar ou abrir o pedido de venda associado ao evento.
    
    - Se o evento já tiver pedido, redireciona para edição do pedido.
    - Se não tiver, cria um novo pedido e redireciona.
    """
    if queryset.count() == 1:
        # Apenas um evento selecionado - redirecionar diretamente
        evento = queryset.first()
        
        if evento.pedido:
            # Já tem pedido - redirecionar para edição
            url = reverse('admin:vendas_pedidovenda_change', args=[evento.pedido.id])
            return redirect(url)
        else:
            # Criar novo pedido
            try:
                pedido = evento.gerar_pedido_evento(condicao_pagamento=None, cliente=None)
                messages.success(
                    request,
                    f'Pedido de Venda #{pedido.id} criado com sucesso para o evento "{evento.nome_evento}".'
                )
                url = reverse('admin:vendas_pedidovenda_change', args=[pedido.id])
                return redirect(url)
            except Exception as e:
                messages.error(request, f'Erro ao criar pedido: {str(e)}')
                return None
    else:
        # Múltiplos eventos selecionados
        pedidos_criados = []
        pedidos_existentes = []
        
        for evento in queryset:
            if evento.pedido:
                pedidos_existentes.append(evento)
            else:
                try:
                    pedido = evento.gerar_pedido_evento(condicao_pagamento=None, cliente=None)
                    pedidos_criados.append((evento, pedido))
                except Exception as e:
                    messages.error(
                        request,
                        f'Erro ao criar pedido para evento "{evento.nome_evento}": {str(e)}'
                    )
        
        # Mensagens de resultado
        if pedidos_criados:
            mensagem = f'{len(pedidos_criados)} pedido(s) criado(s) com sucesso: '
            mensagem += ', '.join([f'#{p.id}' for _, p in pedidos_criados])
            messages.success(request, mensagem)
        
        if pedidos_existentes:
            mensagem = f'{len(pedidos_existentes)} evento(s) já possuem pedido vinculado.'
            messages.info(request, mensagem)
        
        # Redirecionar para lista de pedidos se houver pedidos criados
        if pedidos_criados:
            url = reverse('admin:vendas_pedidovenda_changelist')
            return redirect(url)
        
        return None


@admin.action(description='Gerar NF-e rascunho do Evento')
def gerar_nfe_rascunho_evento(modeladmin, request, queryset):
    """
    Action para gerar NF-e rascunho para eventos que possuem pedido.
    """
    if queryset.count() == 1:
        # Apenas um evento selecionado
        evento = queryset.first()
        
        if not evento.pedido:
            messages.error(
                request,
                f'Evento "{evento.nome_evento}" não possui pedido de venda associado. '
                'Crie o pedido primeiro usando a action "Gerar/abrir Pedido de Venda do Evento".'
            )
            return None
        
        try:
            nota = criar_nfe_rascunho_para_pedido_evento(evento.pedido)
            messages.success(
                request,
                f'NF-e RASCUNHO #{nota.numero}/{nota.serie} criada com sucesso para o evento "{evento.nome_evento}".'
            )
            url = reverse('admin:fiscal_notafiscalsaida_change', args=[nota.id])
            return redirect(url)
        except ValidationError as e:
            messages.error(request, f'Erro de validação: {str(e)}')
            return None
        except Exception as e:
            messages.error(request, f'Erro ao criar NF-e: {str(e)}')
            return None
    else:
        # Múltiplos eventos selecionados
        notas_criadas = []
        eventos_sem_pedido = []
        erros = []
        
        for evento in queryset:
            if not evento.pedido:
                eventos_sem_pedido.append(evento)
                continue
            
            try:
                nota = criar_nfe_rascunho_para_pedido_evento(evento.pedido)
                notas_criadas.append((evento, nota))
            except ValidationError as e:
                erros.append((evento, str(e)))
            except Exception as e:
                erros.append((evento, str(e)))
        
        # Mensagens de resultado
        if notas_criadas:
            mensagem = f'{len(notas_criadas)} NF-e(s) rascunho criada(s) com sucesso.'
            messages.success(request, mensagem)
        
        if eventos_sem_pedido:
            mensagem = f'{len(eventos_sem_pedido)} evento(s) não possuem pedido de venda associado.'
            messages.warning(request, mensagem)
        
        if erros:
            for evento, erro in erros:
                messages.error(request, f'Erro ao criar NF-e para "{evento.nome_evento}": {erro}')
        
        # Redirecionar para lista de notas se houver notas criadas
        if notas_criadas:
            url = reverse('admin:fiscal_notafiscalsaida_changelist')
            return redirect(url)
        
        return None


@admin.register(EventoVenda)
class EventoVendaAdmin(admin.ModelAdmin):
    list_display = ['nome_evento', 'empresa', 'loja', 'tipo_evento', 'data_evento', 'status', 'pedido', 'is_active']
    list_filter = ['empresa', 'loja', 'tipo_evento', 'status', 'data_evento', 'is_active', 'created_at']
    search_fields = ['nome_evento', 'responsavel_evento', 'endereco_cidade', 'endereco_bairro']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    filter_horizontal = ['equipe_responsavel']
    actions = [gerar_abrir_pedido_evento, gerar_nfe_rascunho_evento]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'loja', 'nome_evento', 'tipo_evento', 'status')
        }),
        ('Data e Hora', {
            'fields': ('data_evento', 'hora_evento')
        }),
        ('Relacionamentos', {
            'fields': ('lead', 'cliente', 'pedido')
        }),
        ('Endereço do Evento', {
            'fields': (
                'endereco_logradouro', 'endereco_numero', 'endereco_complemento',
                'endereco_bairro', 'endereco_cidade', 'endereco_uf', 'endereco_cep'
            )
        }),
        ('Detalhes do Evento', {
            'fields': ('estimativa_publico', 'responsavel_evento', 'telefone_responsavel', 'equipe_responsavel')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Controle', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )

