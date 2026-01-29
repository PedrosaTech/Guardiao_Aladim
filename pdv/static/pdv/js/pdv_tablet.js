/**
 * PDV Balcão – Integração com pedidos do tablet.
 * Buscar pedido por número, exibir resumo, forma de pagamento, troco, efetivar.
 */
(function () {
    'use strict';

    function formatMoney(value) {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    }

    function showLoading(msg) {
        var el = document.getElementById('loadingMessageTablet');
        var m = document.getElementById('modalLoadingTablet');
        if (el) el.textContent = msg || 'Processando...';
        if (m) m.classList.add('active');
    }

    function hideLoading() {
        var m = document.getElementById('modalLoadingTablet');
        if (m) m.classList.remove('active');
    }

    function abrirModalBuscarTablet() {
        var inp = document.getElementById('numeroPedidoTablet');
        var err = document.getElementById('erroBuscaTablet');
        if (inp) { inp.value = ''; inp.focus(); }
        if (err) { err.style.display = 'none'; err.textContent = ''; }
        var modal = document.getElementById('modalBuscarTablet');
        if (modal) modal.classList.add('active');
    }

    function fecharModalBuscarTablet() {
        var modal = document.getElementById('modalBuscarTablet');
        if (modal) modal.classList.remove('active');
    }

    function mostrarErroBusca(msg) {
        var err = document.getElementById('erroBuscaTablet');
        if (err) {
            err.textContent = msg;
            err.style.display = 'block';
        }
    }

    function buscarPedidoTablet() {
        var numero = (document.getElementById('numeroPedidoTablet') || {}).value.trim();
        if (!numero) {
            mostrarErroBusca('Informe o número do pedido.');
            return;
        }
        if (typeof caixaSessaoId === 'undefined' || caixaSessaoId == null) {
            mostrarErroBusca('Caixa não está aberto. Abra o caixa antes de processar pedidos.');
            return;
        }

        showLoading('Buscando pedido...');
        fetch('/pdv/api/buscar-pedido-tablet/?numero=' + encodeURIComponent(numero), {
            method: 'GET',
            headers: { 'X-CSRFToken': typeof getCookie !== 'undefined' ? getCookie('csrftoken') : '' },
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                hideLoading();
                if (data.erro) {
                    mostrarErroBusca(data.erro);
                    return;
                }
                fecharModalBuscarTablet();
                exibirPedidoTablet(data);
            })
            .catch(function (e) {
                hideLoading();
                mostrarErroBusca('Erro ao buscar pedido: ' + (e.message || 'erro desconhecido'));
            });
    }

    function exibirPedidoTablet(pedido) {
        var areaNormal = document.getElementById('areaVendaNormal');
        var areaTablet = document.getElementById('areaPedidoTablet');
        if (areaNormal) areaNormal.style.display = 'none';
        if (!areaTablet) return;

        var forma = pedido.forma_pagamento_pretendida || 'NAO_INFORMADO';
        var formaLabel = pedido.forma_pagamento_pretendida_label || forma;
        var htmlPretendido = '';
        if (forma !== 'NAO_INFORMADO') {
            htmlPretendido = '<div style="background:#0f3460;padding:10px;border-radius:8px;margin-bottom:16px;">' +
                'Cliente informou que pretende pagar em: <strong>' + (formaLabel || forma) + '</strong>. Você pode alterar se necessário.</div>';
        }

        var itensHtml = (pedido.itens || []).map(function (i) {
            return '<tr><td>' + (i.codigo || '') + '</td><td>' + (i.produto || '') + '</td><td style="text-align:center">' + i.quantidade + '</td><td style="text-align:right">' + formatMoney(i.preco_unitario) + '</td><td style="text-align:right"><strong>' + formatMoney(i.total) + '</strong></td></tr>';
        }).join('');

        var selectOpts = [
            { v: 'DINHEIRO', l: 'Dinheiro' },
            { v: 'CARTAO_DEBITO', l: 'Cartão Débito' },
            { v: 'CARTAO_CREDITO', l: 'Cartão Crédito' },
            { v: 'PIX', l: 'PIX' },
        ];
        var sel = selectOpts.map(function (o) {
            var s = forma === o.v ? ' selected' : '';
            return '<option value="' + o.v + '"' + s + '>' + o.l + '</option>';
        }).join('');

        var html =
            '<div style="background:#16213e;border:2px solid #667eea;border-radius:12px;padding:24px;max-width:800px;">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">' +
            '<h2 style="margin:0;">Pedido Tablet #' + (pedido.numero || pedido.id) + '</h2>' +
            '<button type="button" class="action-btn danger" id="btnCancelarPedidoTablet">Cancelar</button>' +
            '</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px;">' +
            '<div><strong>Atendente</strong><p style="margin:4px 0 0;">' + (pedido.atendente || '—') + '</p></div>' +
            '<div><strong>Cliente</strong><p style="margin:4px 0 0;">' + (pedido.cliente && pedido.cliente.nome ? pedido.cliente.nome : 'Sem cliente') + '</p></div>' +
            '<div><strong>Data/Hora</strong><p style="margin:4px 0 0;">' + (pedido.created_at || '') + '</p></div>' +
            '</div>' +
            '<h3 style="margin-bottom:12px;">Itens</h3>' +
            '<div style="overflow-x:auto;margin-bottom:24px;">' +
            '<table style="width:100%;border-collapse:collapse;">' +
            '<thead><tr><th>Código</th><th>Produto</th><th style="text-align:center">Qtd</th><th style="text-align:right">Preço</th><th style="text-align:right">Total</th></tr></thead>' +
            '<tbody>' + itensHtml + '</tbody>' +
            '<tfoot><tr><td colspan="4" style="text-align:right"><strong>TOTAL</strong></td><td style="text-align:right"><strong id="pedidoValorTotal" data-valor="' + pedido.valor_total + '">' + formatMoney(pedido.valor_total) + '</strong></td></tr></tfoot>' +
            '</table></div>' +
            htmlPretendido +
            '<div style="background:#1a1a2e;padding:16px;border-radius:8px;margin-bottom:16px;">' +
            '<label style="display:block;margin-bottom:8px;"><strong>Forma de pagamento</strong></label>' +
            '<select id="tipoPagamentoTablet" style="width:100%;padding:10px;font-size:16px;border-radius:6px;background:#16213e;color:#fff;border:2px solid #667eea;">' + sel + '</select>' +
            '<div id="divValorRecebidoTablet" style="display:none;margin-top:12px;">' +
            '<label style="display:block;margin-bottom:6px;">Valor recebido (R$)</label>' +
            '<input type="text" id="valorRecebidoTablet" placeholder="0,00" style="width:100%;padding:10px;font-size:18px;border-radius:6px;background:#16213e;color:#fff;border:2px solid #667eea;">' +
            '<div id="trocoDisplayTablet" style="margin-top:10px;padding:10px;border-radius:6px;display:none;"></div>' +
            '</div>' +
            '<div style="margin-top:12px;"><label style="display:block;margin-bottom:6px;">Observações (opcional)</label>' +
            '<textarea id="observacoesPagamentoTablet" rows="2" style="width:100%;padding:8px;border-radius:6px;background:#16213e;color:#fff;border:2px solid #667eea;"></textarea></div>' +
            '<div style="margin-top:20px;display:flex;gap:10px;">' +
            '<button type="button" class="action-btn primary" id="btnEfetivarPedidoTablet" data-pedido-id="' + pedido.id + '">Efetivar venda</button>' +
            '<button type="button" class="action-btn danger" id="btnCancelarPedidoTablet2">Cancelar</button>' +
            '</div></div></div>';

        areaTablet.innerHTML = html;
        areaTablet.style.display = 'block';

        var tipoSel = document.getElementById('tipoPagamentoTablet');
        var divValor = document.getElementById('divValorRecebidoTablet');
        var inputValor = document.getElementById('valorRecebidoTablet');
        var trocoDisp = document.getElementById('trocoDisplayTablet');

        function toggleValorRecebido() {
            if (tipoSel && tipoSel.value === 'DINHEIRO') {
                if (divValor) divValor.style.display = 'block';
                if (inputValor) {
                    var total = parseFloat(document.getElementById('pedidoValorTotal').dataset.valor || '0');
                    inputValor.value = total.toFixed(2);
                    inputValor.focus();
                }
                calcTroco();
            } else {
                if (divValor) divValor.style.display = 'none';
                if (trocoDisp) { trocoDisp.style.display = 'none'; trocoDisp.textContent = ''; }
            }
        }

        function calcTroco() {
            var total = parseFloat(document.getElementById('pedidoValorTotal').dataset.valor || '0');
            var raw = (inputValor && inputValor.value) ? String(inputValor.value).replace(',', '.').replace(/\s/g, '') : '';
            var recebido = parseFloat(raw) || 0;
            var troco = recebido - total;
            if (!trocoDisp) return;
            if (recebido <= 0) {
                trocoDisp.style.display = 'none';
                return;
            }
            trocoDisp.style.display = 'block';
            if (troco >= 0) {
                trocoDisp.style.background = '#0f3460';
                trocoDisp.style.color = '#4ecca3';
                trocoDisp.innerHTML = 'Troco: <strong>' + formatMoney(troco) + '</strong>';
            } else {
                trocoDisp.style.background = '#4a1623';
                trocoDisp.style.color = '#e74c3c';
                trocoDisp.innerHTML = 'Faltam: <strong>' + formatMoney(-troco) + '</strong>';
            }
        }

        if (tipoSel) {
            tipoSel.addEventListener('change', toggleValorRecebido);
        }
        if (inputValor) {
            inputValor.addEventListener('input', calcTroco);
            inputValor.addEventListener('blur', calcTroco);
        }
        if (forma === 'DINHEIRO') toggleValorRecebido();

        function cancelar(skipConfirm) {
            if (!skipConfirm && !confirm('Cancelar e voltar ao PDV normal?')) return;
            areaTablet.innerHTML = '';
            areaTablet.style.display = 'none';
            if (areaNormal) areaNormal.style.display = '';
        }
        window.cancelarPedidoTablet = function () { cancelar(true); };

        document.getElementById('btnCancelarPedidoTablet').addEventListener('click', cancelar);
        var btn2 = document.getElementById('btnCancelarPedidoTablet2');
        if (btn2) btn2.addEventListener('click', cancelar);

        document.getElementById('btnEfetivarPedidoTablet').addEventListener('click', function () {
            var pid = parseInt(this.getAttribute('data-pedido-id'), 10);
            var tipo = (document.getElementById('tipoPagamentoTablet') || {}).value;
            var valorTotal = parseFloat((document.getElementById('pedidoValorTotal') || {}).dataset.valor || '0');
            var valorRecebido = null;

            if (typeof caixaSessaoId === 'undefined' || caixaSessaoId == null) {
                alert('Caixa não está aberto. Abra o caixa antes de efetivar.');
                return;
            }
            if (tipo === 'DINHEIRO') {
                var raw = (document.getElementById('valorRecebidoTablet') || {}).value;
                raw = String(raw || '').replace(',', '.').replace(/\s/g, '');
                valorRecebido = parseFloat(raw);
                if (!valorRecebido || valorRecebido < valorTotal) {
                    alert('Informe o valor recebido (maior ou igual ao total).');
                    return;
                }
            }
            abrirModalFiscal(pid, tipo, valorRecebido);
        });
    }

    function abrirModalFiscal(pedidoId, tipoPagamento, valorRecebido) {
        window.dadosEfetivacao = { pedidoId: pedidoId, tipoPagamento: tipoPagamento, valorRecebido: valorRecebido };
        var sim = document.getElementById('fiscal-sim');
        var cpf = document.getElementById('cpf-cnpj-nota');
        if (sim) sim.checked = true;
        if (cpf) cpf.value = '';
        toggleCpfCnpj();
        var m = document.getElementById('modalFiscal');
        if (m) m.classList.add('active');
    }

    function toggleCpfCnpj() {
        var emitir = document.getElementById('fiscal-sim') && document.getElementById('fiscal-sim').checked;
        var div = document.getElementById('div-cpf-cnpj');
        var cpf = document.getElementById('cpf-cnpj-nota');
        if (div) div.style.display = emitir ? 'block' : 'none';
        if (cpf && !emitir) cpf.value = '';
    }

    function fecharModalFiscal() {
        var m = document.getElementById('modalFiscal');
        if (m) m.classList.remove('active');
    }

    function confirmarEfetivarComFiscal() {
        var dados = window.dadosEfetivacao;
        if (!dados) return;
        var emitirCupom = document.getElementById('fiscal-sim') && document.getElementById('fiscal-sim').checked;
        var cpfCnpj = (document.getElementById('cpf-cnpj-nota') && document.getElementById('cpf-cnpj-nota').value.trim()) || '';
        if (emitirCupom && cpfCnpj) {
            cpfCnpj = cpfCnpj.replace(/\D/g, '');
            if (cpfCnpj.length !== 11 && cpfCnpj.length !== 14) {
                alert('CPF deve ter 11 dígitos e CNPJ 14 dígitos.');
                var el = document.getElementById('cpf-cnpj-nota');
                if (el) el.focus();
                return;
            }
        }
        if (!emitirCupom) cpfCnpj = '';
        fecharModalFiscal();
        var tipoEl = document.getElementById('tipoPagamentoTablet');
        var totalEl = document.getElementById('pedidoValorTotal');
        var tipoLabel = tipoEl && tipoEl.selectedOptions && tipoEl.selectedOptions[0] ? tipoEl.selectedOptions[0].text : dados.tipoPagamento;
        var totalStr = totalEl ? totalEl.textContent : '';
        var msg = 'Confirmar efetivação?\n\nPedido #' + dados.pedidoId + '\nPagamento: ' + tipoLabel + '\nTotal: ' + totalStr + '\n\nCupom fiscal: ' + (emitirCupom ? 'Sim' + (cpfCnpj ? '\nCPF/CNPJ: ' + cpfCnpj : '') : 'Não');
        if (!confirm(msg)) return;
        showLoading('Efetivando venda...');
        var obs = (document.getElementById('observacoesPagamentoTablet') && document.getElementById('observacoesPagamentoTablet').value.trim()) || '';
        var body = {
            pedido_id: dados.pedidoId,
            caixa_sessao_id: typeof caixaSessaoId !== 'undefined' ? caixaSessaoId : null,
            tipo_pagamento: dados.tipoPagamento,
            valor_recebido: dados.valorRecebido,
            observacoes: obs || null,
            emitir_cupom_fiscal: emitirCupom,
            cpf_cnpj_nota: cpfCnpj || null,
        };
        fetch('/pdv/api/efetivar-pedido-tablet/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': typeof getCookie !== 'undefined' ? getCookie('csrftoken') : '',
            },
            body: JSON.stringify(body),
        })
            .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
            .then(function (res) {
                hideLoading();
                if (!res.ok) {
                    alert('Erro: ' + (res.data.erro || 'Erro ao efetivar'));
                    return;
                }
                var d = res.data;
                var msgSucesso = 'Venda efetivada.\n\nPedido #' + d.pedido_id + '\nPagamento ID #' + d.pagamento_id + '\nValor pago: ' + formatMoney(d.valor_pago);
                if (d.valor_troco > 0) msgSucesso += '\n\nTroco: ' + formatMoney(d.valor_troco);
                if (d.cupom_fiscal_emitido && d.numero_cupom) msgSucesso += '\n\nCupom fiscal: ' + d.numero_cupom;
                msgSucesso += '\n\nMovimentos estoque: ' + d.movimentos_estoque;
                if (d.titulos_gerados > 0) msgSucesso += '\nTítulos gerados: ' + d.titulos_gerados;
                alert(msgSucesso);
                if (typeof window.cancelarPedidoTablet === 'function') window.cancelarPedidoTablet();
                if (typeof atualizarTotaisCaixa === 'function') atualizarTotaisCaixa();
                if (d.cupom_fiscal_emitido && d.numero_cupom && confirm('Deseja imprimir o cupom fiscal?')) {
                    window.open('/pdv/cupom-fiscal/' + dados.pedidoId + '/?autoprint=1', '_blank');
                }
            })
            .catch(function (e) {
                hideLoading();
                alert('Erro: ' + (e.message || 'Erro ao efetivar'));
            });
    }

    window.toggleCpfCnpj = toggleCpfCnpj;
    window.fecharModalFiscal = fecharModalFiscal;
    window.confirmarEfetivarComFiscal = confirmarEfetivarComFiscal;

    function init() {
        var btnBuscar = document.getElementById('btnBuscarPedidoTablet');
        var btnConfirmar = document.getElementById('btnBuscarTabletConfirmar');
        var btnFechar = document.getElementById('btnFecharModalBuscarTablet');
        var inp = document.getElementById('numeroPedidoTablet');

        if (btnBuscar) btnBuscar.addEventListener('click', abrirModalBuscarTablet);
        if (btnConfirmar) btnConfirmar.addEventListener('click', buscarPedidoTablet);
        if (btnFechar) btnFechar.addEventListener('click', fecharModalBuscarTablet);
        if (inp) {
            inp.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    buscarPedidoTablet();
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
