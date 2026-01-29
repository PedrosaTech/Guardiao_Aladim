/**
 * Lógica de gerenciamento de pedido
 * Inclui Ajuste 2 (limparPedido via API) e Ajuste 3 (incrementar qtd se duplicado)
 */

var pedidoAtual = {
    id: null,
    itens: [],
    subtotal: 0,
    desconto: 0,
    total: 0,
};

function _atualizarPedidoFromResponse(response) {
    var vd = response.valor_desconto != null ? parseFloat(response.valor_desconto) : 0;
    var vt = response.valor_total != null ? parseFloat(response.valor_total) : 0;
    pedidoAtual = {
        id: response.id,
        itens: response.itens || [],
        subtotal: vt + vd,
        desconto: vd,
        total: vt,
    };
}

function iniciarNovoPedido() {
    return api.criarPedido({ observacoes: "Pedido tablet" }).then(
        function (response) {
            pedidoAtual.id = response.id;
            var numEl = document.getElementById("pedido-numero");
            if (numEl) numEl.textContent = "#" + String(response.id).padStart(4, "0");
            return response;
        },
        function (err) {
            if (typeof showToast === "function") showToast("Erro ao criar pedido: " + err.message, "error");
            throw err;
        }
    );
}

function adicionarProduto(produto) {
    if (!pedidoAtual.id) {
        if (typeof showToast === "function") showToast("Erro: Pedido não iniciado", "error");
        return Promise.resolve();
    }

    var itemExistente = null;
    for (var i = 0; i < pedidoAtual.itens.length; i++) {
        if (pedidoAtual.itens[i].produto === produto.id) {
            itemExistente = pedidoAtual.itens[i];
            break;
        }
    }

    if (itemExistente) {
        if (!confirm(produto.descricao + " já está no pedido.\n\nAdicionar mais 1 unidade?")) {
            return Promise.resolve();
        }
        if (typeof showLoading === "function") showLoading("Adicionando item...");
        var pid = pedidoAtual.id;
        var qty = parseFloat(itemExistente.quantidade) + 1;
        var pu = itemExistente.preco_unitario;
        var desc = itemExistente.desconto != null ? itemExistente.desconto : 0;

        return api
            .removerItem(pid, itemExistente.id)
            .then(function () {
                return api.adicionarItem(pid, {
                    produto: produto.id,
                    quantidade: qty,
                    preco_unitario: pu,
                    desconto: desc,
                });
            })
            .then(function (response) {
                _atualizarPedidoFromResponse(response);
                if (typeof renderizarPedido === "function") renderizarPedido();
                if (typeof vibrate === "function") vibrate(50);
                if (typeof showToast === "function") showToast("Quantidade atualizada: " + qty + "x", "success");
                return response;
            })
            .catch(function (err) {
                if (typeof showToast === "function") showToast("Erro ao adicionar: " + err.message, "error");
                throw err;
            })
            .finally(function () {
                if (typeof hideLoading === "function") hideLoading();
            });
    }

    if (typeof showLoading === "function") showLoading("Adicionando item...");

    return api
        .adicionarItem(pedidoAtual.id, {
            produto: produto.id,
            quantidade: 1,
            preco_unitario: produto.preco_venda_sugerido,
            desconto: 0,
        })
        .then(function (response) {
            _atualizarPedidoFromResponse(response);
            if (typeof renderizarPedido === "function") renderizarPedido();
            if (typeof vibrate === "function") vibrate(50);
            if (typeof showToast === "function") showToast(produto.descricao + " adicionado", "success");
            return response;
        })
        .catch(function (err) {
            if (typeof showToast === "function") showToast("Erro ao adicionar: " + err.message, "error");
            throw err;
        })
        .finally(function () {
            if (typeof hideLoading === "function") hideLoading();
        });
}

function removerItem(itemId) {
    if (!confirm("Remover este item?")) return Promise.resolve();
    if (typeof showLoading === "function") showLoading("Removendo item...");

    return api
        .removerItem(pedidoAtual.id, itemId)
        .then(function (response) {
            _atualizarPedidoFromResponse(response);
            if (typeof renderizarPedido === "function") renderizarPedido();
            if (typeof showToast === "function") showToast("Item removido", "success");
            return response;
        })
        .catch(function (err) {
            if (typeof showToast === "function") showToast("Erro ao remover: " + err.message, "error");
            throw err;
        })
        .finally(function () {
            if (typeof hideLoading === "function") hideLoading();
        });
}

function renderizarPedido() {
    var container = document.getElementById("itens-container");
    if (!container) return;

    if (!pedidoAtual.itens || pedidoAtual.itens.length === 0) {
        container.innerHTML =
            '<div class="empty-state"><div class="empty-state-icon">🛍️</div><div class="empty-state-text">Nenhum item adicionado</div></div>';
    } else {
        var html = "";
        for (var i = 0; i < pedidoAtual.itens.length; i++) {
            var item = pedidoAtual.itens[i];
            var qty = typeof formatNumber === "function" ? formatNumber(item.quantidade, 3) : item.quantidade;
            var pu = typeof formatMoney === "function" ? formatMoney(item.preco_unitario) : item.preco_unitario;
            var tot = typeof formatMoney === "function" ? formatMoney(item.total) : item.total;
            var descStr = item.desconto > 0 && typeof formatMoney === "function" ? " - Desc. " + formatMoney(item.desconto) : "";
            html +=
                '<div class="item-pedido" data-item-id="' +
                item.id +
                '">' +
                '<div class="item-info">' +
                '<div class="item-nome">' +
                (item.produto_descricao || "") +
                "</div>" +
                '<div class="item-detalhes">' +
                qty +
                "x " +
                pu +
                descStr +
                "</div>" +
                "</div>" +
                '<div class="item-total">' +
                tot +
                "</div>" +
                '<button type="button" class="btn-remover" data-remove-id="' +
                item.id +
                '" aria-label="Remover">✕</button>' +
                "</div>";
        }
        container.innerHTML = html;

        container.querySelectorAll(".btn-remover[data-remove-id]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var id = parseInt(btn.getAttribute("data-remove-id"), 10);
                if (!isNaN(id)) removerItem(id);
            });
        });
    }

    var subEl = document.getElementById("subtotal");
    var dscEl = document.getElementById("desconto");
    var totEl = document.getElementById("total");
    if (subEl) subEl.textContent = typeof formatMoney === "function" ? formatMoney(pedidoAtual.subtotal) : pedidoAtual.subtotal;
    if (dscEl) dscEl.textContent = typeof formatMoney === "function" ? formatMoney(pedidoAtual.desconto) : pedidoAtual.desconto;
    if (totEl) totEl.textContent = typeof formatMoney === "function" ? formatMoney(pedidoAtual.total) : pedidoAtual.total;

    var btnSalvar = document.getElementById("btn-salvar");
    if (btnSalvar) btnSalvar.disabled = !pedidoAtual.itens || pedidoAtual.itens.length === 0;
}

function salvarPedido() {
    if (!pedidoAtual.itens || pedidoAtual.itens.length === 0) {
        if (typeof showToast === "function") showToast("Adicione pelo menos 1 item", "warning");
        return;
    }
    abrirModalEnviarCaixa();
}

function abrirModalEnviarCaixa() {
    if (!pedidoAtual.itens || pedidoAtual.itens.length === 0) {
        if (typeof showToast === "function") showToast("Adicione pelo menos um item ao pedido.", "warning");
        else alert("Adicione pelo menos um item ao pedido.");
        return;
    }
    var modal = document.getElementById("modal-enviar-caixa");
    var totalEl = document.getElementById("modal-enviar-total");
    if (totalEl) totalEl.textContent = typeof formatMoney === "function" ? formatMoney(pedidoAtual.total) : "R$ " + (pedidoAtual.total || 0).toFixed(2);
    if (modal) modal.style.display = "flex";
    var sel = document.getElementById("modal-enviar-forma");
    if (sel) sel.value = "NAO_INFORMADO";
    var btnConfirm = document.getElementById("modal-enviar-confirmar");
    if (btnConfirm) { btnConfirm.disabled = false; btnConfirm.textContent = "Enviar para o Caixa"; }
}

function fecharModalEnviarCaixa() {
    var modal = document.getElementById("modal-enviar-caixa");
    if (modal) modal.style.display = "none";
}

function enviarParaCaixa() {
    var forma = (document.getElementById("modal-enviar-forma") || {}).value || "NAO_INFORMADO";
    var pid = pedidoAtual.id;
    if (!pid) {
        if (typeof showToast === "function") showToast("Erro: pedido não encontrado", "error");
        return;
    }
    var btnConfirm = document.getElementById("modal-enviar-confirmar");
    if (btnConfirm) {
        btnConfirm.disabled = true;
        btnConfirm.textContent = "Enviando...";
    }
    var csrf = typeof getCookie !== "undefined" ? getCookie("csrftoken") : (typeof csrftoken !== "undefined" ? csrftoken : "");
    if (typeof showLoading === "function") showLoading("Enviando para o caixa...");
    fetch("/pdv-movel/api/pedidos/" + pid + "/", {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({ forma_pagamento_pretendida: forma }),
    })
        .then(function (r) {
            if (!r.ok) return r.json().then(function (d) { throw new Error(d.erro || d.detail || "Erro"); });
            return r.json();
        })
        .then(function (data) {
            if (typeof hideLoading === "function") hideLoading();
            fecharModalEnviarCaixa();
            var id = data && (data.id != null) ? data.id : (pedidoAtual && pedidoAtual.id);
            var msg = id != null
                ? "✅ Pedido #" + id + " enviado para o caixa!\n\nInforme ao cliente: \"Pedido " + id + "\""
                : "✅ Pedido enviado para o caixa!";
            alert(msg);
            window.location.href = "/pdv-movel/pedidos/";
        })
        .catch(function (e) {
            if (typeof hideLoading === "function") hideLoading();
            if (btnConfirm) {
                btnConfirm.disabled = false;
                btnConfirm.textContent = "Enviar para o Caixa";
            }
            if (typeof showToast === "function") showToast("Erro: " + (e.message || "Erro ao enviar"), "error");
        });
}

(function setupModalEnviarCaixa() {
    document.addEventListener("DOMContentLoaded", function () {
        var cancel = document.getElementById("modal-enviar-cancelar");
        var confirm = document.getElementById("modal-enviar-confirmar");
        if (cancel) cancel.addEventListener("click", fecharModalEnviarCaixa);
        if (confirm) confirm.addEventListener("click", enviarParaCaixa);
    });
})();

function limparPedido() {
    if (!confirm("Deseja realmente limpar o pedido atual?")) return;

    if (!pedidoAtual.itens || pedidoAtual.itens.length === 0) {
        if (typeof showToast === "function") showToast("Pedido já está vazio", "info");
        return;
    }

    if (typeof showLoading === "function") showLoading("Limpando pedido...");

    var pid = pedidoAtual.id;
    var itens = pedidoAtual.itens.slice();
    var idx = 0;

    function next() {
        if (idx >= itens.length) {
            pedidoAtual.itens = [];
            pedidoAtual.subtotal = 0;
            pedidoAtual.desconto = 0;
            pedidoAtual.total = 0;
            if (typeof renderizarPedido === "function") renderizarPedido();
            if (typeof showToast === "function") showToast("Pedido limpo", "success");
            if (typeof hideLoading === "function") hideLoading();
            return;
        }
        var item = itens[idx++];
        api.removerItem(pid, item.id)
            .then(next)
            .catch(function (err) {
                if (typeof showToast === "function") showToast("Erro ao limpar: " + err.message, "error");
                if (typeof hideLoading === "function") hideLoading();
            });
    }

    next();
}
