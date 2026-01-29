/**
 * Lógica de busca e exibição de produtos
 * Ajuste 1: cache global (produtosCache), data-produto-id, event delegation
 */

var produtosCache = {};
function _cacheSet(id, p) {
    produtosCache[id] = p;
}
function _cacheGet(id) {
    return produtosCache[id];
}

function renderProdutoCard(produto) {
    var estoque = produto.estoque_disponivel != null ? Number(produto.estoque_disponivel) : 0;
    var estoqueClass = estoque < 10 ? "estoque-baixo" : "";
    var cod = produto.codigo_interno || "";
    var nome = produto.descricao || "";
    var preco = typeof formatMoney === "function" ? formatMoney(produto.preco_venda_sugerido) : produto.preco_venda_sugerido;
    return (
        '<div class="produto-card" data-produto-id="' +
        produto.id +
        '">' +
        '<div class="produto-codigo">' +
        cod +
        "</div>" +
        '<div class="produto-nome">' +
        nome +
        "</div>" +
        '<div class="produto-preco">' +
        preco +
        "</div>" +
        '<div class="produto-estoque ' +
        estoqueClass +
        '">Estoque: ' +
        estoque +
        "</div>" +
        "</div>"
    );
}

function buscarProdutos(query) {
    return api.buscarProdutos(query).then(
        function (response) {
            var container = document.getElementById("produtos-container");
            var maisVendidosContainer = document.getElementById("mais-vendidos-container");
            if (!container) return;

            var list = response.results || [];
            list.forEach(function (p) {
                _cacheSet(p.id, p);
            });

            if (list.length === 0) {
                container.innerHTML =
                    '<div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-text">Nenhum produto encontrado</div></div>';
            } else {
                container.innerHTML = list.map(renderProdutoCard).join("");
            }

            container.style.display = "grid";
            if (maisVendidosContainer) maisVendidosContainer.style.display = "none";
        },
        function (err) {
            if (typeof showToast === "function") showToast("Erro ao buscar produtos: " + err.message, "error");
        }
    );
}

function carregarMaisVendidos() {
    return api.produtosMaisVendidos().then(
        function (response) {
            var container = document.getElementById("mais-vendidos-grid");
            if (!container) return;

            var list = Array.isArray(response) ? response : response.results || [];
            list.forEach(function (p) {
                _cacheSet(p.id, p);
            });

            if (list.length === 0) {
                container.innerHTML = '<p style="text-align:center;color:var(--gray-600);">Nenhum produto disponível</p>';
            } else {
                container.innerHTML = list.map(renderProdutoCard).join("");
            }
        },
        function (err) {
            if (typeof console !== "undefined" && console.error) console.error("Erro ao carregar mais vendidos:", err);
        }
    );
}

function abrirCamera() {
    if (typeof showToast === "function") showToast("Scanner em desenvolvimento", "warning");
}

function _onProdutoCardClick(e) {
    var card = e.target && e.target.closest ? e.target.closest(".produto-card") : null;
    if (!card) return;
    var raw = card.getAttribute("data-produto-id");
    var id = raw ? parseInt(raw, 10) : NaN;
    if (isNaN(id)) return;
    var produto = _cacheGet(id);
    if (produto && typeof adicionarProduto === "function") adicionarProduto(produto);
}

if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", function () {
        document.addEventListener("click", _onProdutoCardClick);
    });
}
