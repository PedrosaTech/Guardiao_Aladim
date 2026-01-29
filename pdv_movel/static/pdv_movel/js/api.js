/**
 * Cliente API REST para PDV Móvel
 */

var API_BASE = "/pdv-movel/api";

function PDVAPI() {
    this.headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": typeof csrftoken !== "undefined" ? csrftoken : "",
    };
}

PDVAPI.prototype.request = function (url, options) {
    options = options || {};
    var config = {
        method: options.method || "GET",
        headers: Object.assign({}, this.headers, options.headers || {}),
    };
    if (options.body) config.body = options.body;

    return fetch(url, config).then(function (response) {
        if (!response.ok) {
            return response.json().catch(function () { return {}; }).then(function (data) {
                throw new Error(data.erro || data.detail || "Erro na requisição");
            });
        }
        return response.json();
    });
};

PDVAPI.prototype.buscarProdutos = function (query) {
    var params = query ? "?busca=" + encodeURIComponent(query) : "";
    return this.request(API_BASE + "/produtos/" + params);
};

PDVAPI.prototype.buscarProdutoPorCodigo = function (codigo) {
    return this.request(API_BASE + "/produtos/?codigo_barras=" + encodeURIComponent(codigo));
};

PDVAPI.prototype.obterProduto = function (id) {
    return this.request(API_BASE + "/produtos/" + id + "/");
};

PDVAPI.prototype.produtosMaisVendidos = function () {
    return this.request(API_BASE + "/produtos/mais_vendidos/");
};

PDVAPI.prototype.listarPedidos = function (params) {
    params = params || {};
    var q = Object.keys(params).length ? "?" + new URLSearchParams(params).toString() : "";
    return this.request(API_BASE + "/pedidos/" + q);
};

PDVAPI.prototype.criarPedido = function (data) {
    return this.request(API_BASE + "/pedidos/", {
        method: "POST",
        body: JSON.stringify(data || {}),
    });
};

PDVAPI.prototype.obterPedido = function (id) {
    return this.request(API_BASE + "/pedidos/" + id + "/");
};

PDVAPI.prototype.atualizarPedido = function (id, data) {
    return this.request(API_BASE + "/pedidos/" + id + "/", {
        method: "PUT",
        body: JSON.stringify(data),
    });
};

PDVAPI.prototype.cancelarPedido = function (id) {
    return this.request(API_BASE + "/pedidos/" + id + "/", { method: "DELETE" });
};

PDVAPI.prototype.adicionarItem = function (pedidoId, item) {
    return this.request(API_BASE + "/pedidos/" + pedidoId + "/adicionar_item/", {
        method: "POST",
        body: JSON.stringify(item),
    });
};

PDVAPI.prototype.removerItem = function (pedidoId, itemId) {
    return this.request(API_BASE + "/pedidos/" + pedidoId + "/remover_item/", {
        method: "POST",
        body: JSON.stringify({ item_id: itemId }),
    });
};

PDVAPI.prototype.obterEstatisticas = function () {
    return this.request(API_BASE + "/pedidos/estatisticas/");
};

PDVAPI.prototype.buscarPedidoCaixa = function (numero) {
    return this.request(API_BASE + "/caixa/buscar/?numero=" + encodeURIComponent(numero));
};

PDVAPI.prototype.finalizarPedido = function (id, formaPagamento) {
    return this.request(API_BASE + "/caixa/" + id + "/finalizar/", {
        method: "POST",
        body: JSON.stringify({ forma_pagamento: formaPagamento || "DINHEIRO" }),
    });
};

var api = new PDVAPI();
