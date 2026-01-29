/**
 * Códigos alternativos – CRUD via AJAX
 */

let fornecedorContext = 'add';

function isCodigoBarrasValido(code) {
    if (!code) return false;
    if (!/^\d+$/.test(code)) return false;
    return [8, 12, 13, 14].includes(code.length);
}

function getCookie(name) {
    let v = null;
    if (document.cookie && document.cookie !== '') {
        const parts = document.cookie.split(';');
        for (let i = 0; i < parts.length; i++) {
            const p = parts[i].trim();
            if (p.substring(0, name.length + 1) === name + '=') {
                v = decodeURIComponent(p.substring(name.length + 1));
                break;
            }
        }
    }
    return v;
}

function showMessage(message, type) {
    type = type || 'success';
    const container = document.getElementById('messages-container');
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? '✓' : '✕';
    container.innerHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <strong>${icon}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    setTimeout(function () {
        const el = container.querySelector('.alert');
        if (el) {
            el.classList.remove('show');
            setTimeout(function () { el.remove(); }, 300);
        }
    }, 5000);
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function limparFormulario() {
    const form = document.getElementById('form-adicionar');
    if (form) form.reset();
    const mult = document.getElementById('id_multiplicador');
    if (mult) mult.value = '1.000';
    limparFornecedor('add');
}

document.getElementById('form-adicionar').addEventListener('submit', async function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const fid = document.getElementById('add-fornecedor-id');
    if (fid && fid.value) formData.set('fornecedor_id', fid.value);
    const btn = this.querySelector('button[type="submit"]');
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Adicionando...';
    try {
        const r = await fetch('/produtos/api/codigo-alternativo/criar/' + PRODUTO_ID + '/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : getCookie('csrftoken')) },
            body: formData,
        });
        const data = await r.json();
        if (data.success) {
            showMessage(data.message, 'success');
            limparFormulario();
            adicionarCodigoNaLista(data.codigo);
            atualizarContador();
        } else {
            showMessage(data.message || 'Erro ao adicionar.', 'error');
        }
    } catch (err) {
        console.error(err);
        showMessage('Erro ao adicionar código alternativo. Tente novamente.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
    }
});

function adicionarCodigoNaLista(codigo) {
    const list = document.getElementById('lista-codigos');
    const empty = list.querySelector('.empty-state');
    if (empty) empty.remove();
    const badgeClass = codigo.multiplicador === '1.000' ? 'bg-secondary' : 'bg-info';
    const esc = function (s) { return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
    const desc = esc(codigo.descricao);
    const cb = esc(codigo.codigo_barras);
    let fornecedorBadge = '';
    if (codigo.fornecedor_nome) {
        const fn = esc(codigo.fornecedor_nome);
        fornecedorBadge = `<div class="mt-1"><span class="badge bg-secondary"><i class="bi bi-building"></i> ${fn}</span></div>`;
    }
    const fid = codigo.fornecedor_id || 'null';
    const fnome = (codigo.fornecedor_nome || '').replace(/'/g, "\\'");
    const html = `
        <div class="codigo-card mb-3 p-3 border rounded" data-codigo-id="${codigo.id}">
            <div class="row align-items-center">
                <div class="col-md-4"><small class="text-muted">Código de barras</small><div class="codigo-barras">${cb}</div></div>
                <div class="col-md-4"><small class="text-muted">Descrição</small><div>${desc || '—'}</div>${fornecedorBadge}</div>
                <div class="col-md-2"><small class="text-muted">Multiplicador</small><div><span class="badge badge-multiplicador ${badgeClass}">${codigo.multiplicador}x</span></div></div>
                <div class="col-md-2 text-end">
                    <button type="button" class="btn btn-sm btn-outline-primary me-1" onclick="editarCodigo(${codigo.id}, '${(codigo.codigo_barras || '').replace(/'/g, "\\'")}', '${(codigo.descricao || '').replace(/'/g, "\\'")}', '${codigo.multiplicador}', ${fid}, '${fnome}')"><i class="bi bi-pencil"></i></button>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="confirmarRemover(${codigo.id})"><i class="bi bi-trash"></i></button>
                </div>
            </div>
        </div>
    `;
    list.insertAdjacentHTML('afterbegin', html);
    const card = list.querySelector('[data-codigo-id="' + codigo.id + '"]');
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(-20px)';
        setTimeout(function () {
            card.style.transition = 'all 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 10);
    }
}

function editarCodigo(id, codigoBarras, descricao, multiplicador, fornecedorId, fornecedorNome) {
    document.getElementById('edit-codigo-id').value = id;
    document.getElementById('edit-codigo-barras').value = codigoBarras || '';
    document.getElementById('edit-descricao').value = descricao || '';
    document.getElementById('edit-multiplicador').value = multiplicador || '1.000';
    if (fornecedorId && fornecedorNome) {
        document.getElementById('edit-fornecedor-id').value = fornecedorId;
        document.getElementById('edit-fornecedor-nome').textContent = fornecedorNome;
        document.getElementById('edit-fornecedor-display').style.display = 'block';
    } else {
        limparFornecedor('edit');
    }
    var m = new bootstrap.Modal(document.getElementById('modalEditar'));
    m.show();
}

async function salvarEdicao() {
    const id = document.getElementById('edit-codigo-id').value;
    const codigoBarras = document.getElementById('edit-codigo-barras').value.trim();
    const descricao = document.getElementById('edit-descricao').value.trim();
    const multiplicador = document.getElementById('edit-multiplicador').value;
    if (!codigoBarras) {
        showMessage('Código de barras é obrigatório', 'error');
        return;
    }
    if (!isCodigoBarrasValido(codigoBarras)) {
        showMessage('Código de barras deve ter 8, 12, 13 ou 14 dígitos (somente números)', 'error');
        return;
    }
    const fd = new FormData();
    fd.append('codigo_barras', codigoBarras);
    fd.append('descricao', descricao);
    fd.append('multiplicador', multiplicador);
    var editFid = document.getElementById('edit-fornecedor-id');
    if (editFid && editFid.value) fd.append('fornecedor_id', editFid.value);
    try {
        const r = await fetch('/produtos/api/codigo-alternativo/editar/' + id + '/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : getCookie('csrftoken')) },
            body: fd,
        });
        const data = await r.json();
        if (data.success) {
            showMessage(data.message, 'success');
            atualizarCodigoNaLista(data.codigo);
            var modal = bootstrap.Modal.getInstance(document.getElementById('modalEditar'));
            if (modal) modal.hide();
        } else {
            showMessage(data.message || 'Erro ao editar.', 'error');
        }
    } catch (err) {
        console.error(err);
        showMessage('Erro ao editar código alternativo. Tente novamente.', 'error');
    }
}

function atualizarCodigoNaLista(codigo) {
    const card = document.querySelector('[data-codigo-id="' + codigo.id + '"]');
    if (!card) return;
    const badgeClass = codigo.multiplicador === '1.000' ? 'bg-secondary' : 'bg-info';
    const esc = function (s) { return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
    const desc = esc(codigo.descricao);
    const cb = esc(codigo.codigo_barras);
    let fornecedorBadge = '';
    if (codigo.fornecedor_nome) {
        const fn = esc(codigo.fornecedor_nome);
        fornecedorBadge = `<div class="mt-1"><span class="badge bg-secondary"><i class="bi bi-building"></i> ${fn}</span></div>`;
    }
    const fid = codigo.fornecedor_id || 'null';
    const fnome = (codigo.fornecedor_nome || '').replace(/'/g, "\\'");
    card.innerHTML = `
        <div class="row align-items-center">
            <div class="col-md-4"><small class="text-muted">Código de barras</small><div class="codigo-barras">${cb}</div></div>
            <div class="col-md-4"><small class="text-muted">Descrição</small><div>${desc || '—'}</div>${fornecedorBadge}</div>
            <div class="col-md-2"><small class="text-muted">Multiplicador</small><div><span class="badge badge-multiplicador ${badgeClass}">${codigo.multiplicador}x</span></div></div>
            <div class="col-md-2 text-end">
                <button type="button" class="btn btn-sm btn-outline-primary me-1" onclick="editarCodigo(${codigo.id}, '${(codigo.codigo_barras || '').replace(/'/g, "\\'")}', '${(codigo.descricao || '').replace(/'/g, "\\'")}', '${codigo.multiplicador}', ${fid}, '${fnome}')"><i class="bi bi-pencil"></i></button>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="confirmarRemover(${codigo.id})"><i class="bi bi-trash"></i></button>
            </div>
        </div>
    `;
    card.style.backgroundColor = '#d1ecf1';
    setTimeout(function () {
        card.style.transition = 'background-color 0.5s ease';
        card.style.backgroundColor = '';
    }, 100);
}

function confirmarRemover(id) {
    const card = document.querySelector('[data-codigo-id="' + id + '"]');
    const cb = card ? (card.querySelector('.codigo-barras') || {}).textContent : '';
    if (!confirm('Remover o código alternativo?\n\n' + cb + '\n\nEsta ação não pode ser desfeita.')) return;
    removerCodigo(id);
}

async function removerCodigo(id) {
    try {
        const r = await fetch('/produtos/api/codigo-alternativo/inativar/' + id + '/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : getCookie('csrftoken')) },
        });
        const data = await r.json();
        if (data.success) {
            showMessage(data.message, 'success');
            const card = document.querySelector('[data-codigo-id="' + id + '"]');
            if (card) {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '0';
                card.style.transform = 'translateX(-100%)';
                setTimeout(function () {
                    card.remove();
                    const list = document.getElementById('lista-codigos');
                    const cards = list.querySelectorAll('.codigo-card');
                    if (cards.length === 0) {
                        list.innerHTML = '<div class="empty-state py-5 text-center text-muted"><div class="empty-state-icon mb-2" style="font-size:3rem;">📦</div><h5>Nenhum código alternativo cadastrado</h5><p>Adicione códigos usando o formulário ao lado.</p></div>';
                    }
                    atualizarContador();
                }, 300);
            }
        } else {
            showMessage(data.message || 'Erro ao remover.', 'error');
        }
    } catch (err) {
        console.error(err);
        showMessage('Erro ao remover código alternativo. Tente novamente.', 'error');
    }
}

function abrirModalFornecedor(context) {
    fornecedorContext = context;
    var modal = document.getElementById('modalFornecedor');
    if (!modal) return;
    var m = new bootstrap.Modal(modal);
    m.show();
    var busca = document.getElementById('busca-fornecedor');
    if (busca) { busca.value = ''; busca.dispatchEvent(new Event('input')); }
}

function selecionarFornecedor(id, nome) {
    var ctx = fornecedorContext;
    var hid = document.getElementById(ctx + '-fornecedor-id');
    var disp = document.getElementById(ctx + '-fornecedor-display');
    var span = document.getElementById(ctx + '-fornecedor-nome');
    if (hid) hid.value = id;
    if (span) span.textContent = nome;
    if (disp) disp.style.display = 'block';
    var modal = bootstrap.Modal.getInstance(document.getElementById('modalFornecedor'));
    if (modal) modal.hide();
    if (ctx === 'add') {
        var desc = document.getElementById('id_descricao');
        if (desc && !desc.value) desc.value = 'Código Fornecedor: ' + nome;
    }
}

function limparFornecedor(context) {
    var hid = document.getElementById(context + '-fornecedor-id');
    var disp = document.getElementById(context + '-fornecedor-display');
    var span = document.getElementById(context + '-fornecedor-nome');
    if (hid) hid.value = '';
    if (span) span.textContent = '';
    if (disp) disp.style.display = 'none';
}

function atualizarContador() {
    const list = document.getElementById('lista-codigos');
    const cards = list ? list.querySelectorAll('.codigo-card') : [];
    const badge = document.querySelector('.produto-info .badge.bg-primary');
    if (badge) badge.textContent = cards.length;
}

var elCb = document.getElementById('id_codigo_barras');
if (elCb) {
    elCb.addEventListener('input', function () {
        this.value = this.value.replace(/\D/g, '');
        if (this.value.length > 14) this.value = this.value.substring(0, 14);
        if (!this.value) {
            this.classList.remove('is-invalid');
            this.classList.remove('is-valid');
            return;
        }
        if (isCodigoBarrasValido(this.value)) {
            this.classList.remove('is-invalid');
            this.classList.add('is-valid');
            return;
        }
        this.classList.add('is-invalid');
        this.classList.remove('is-valid');
    });
}

var elEditCb = document.getElementById('edit-codigo-barras');
if (elEditCb) {
    elEditCb.addEventListener('input', function () {
        this.value = this.value.replace(/\D/g, '');
        if (this.value.length > 14) this.value = this.value.substring(0, 14);
    });
}

var elMult = document.getElementById('id_multiplicador');
if (elMult) {
    elMult.addEventListener('input', function () {
        var v = parseFloat(this.value);
        if (v < 0.001) this.value = '0.001';
    });
}

var elEditMult = document.getElementById('edit-multiplicador');
if (elEditMult) {
    elEditMult.addEventListener('input', function () {
        var v = parseFloat(this.value);
        if (v < 0.001) this.value = '0.001';
    });
}

document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        var modal = document.getElementById('modalEditar');
        if (modal && modal.classList.contains('show')) {
            e.preventDefault();
            salvarEdicao();
        }
    }
    if (e.key === 'Escape') {
        var modal = bootstrap.Modal.getInstance(document.getElementById('modalEditar'));
        if (modal) modal.hide();
    }
});

document.addEventListener('DOMContentLoaded', function () {
    var f = document.getElementById('id_codigo_barras');
    if (f) f.focus();
    var items = document.querySelectorAll('.fornecedor-item');
    items.forEach(function (el) {
        el.addEventListener('click', function () {
            var id = this.getAttribute('data-fornecedor-id');
            var nome = this.getAttribute('data-fornecedor-nome') || '';
            selecionarFornecedor(id, nome);
        });
    });
    var busca = document.getElementById('busca-fornecedor');
    if (busca) {
        busca.addEventListener('input', function () {
            var termo = (this.value || '').toLowerCase();
            var list = document.querySelectorAll('#lista-fornecedores .fornecedor-item');
            list.forEach(function (item) {
                var n = (item.getAttribute('data-fornecedor-nome') || '').toLowerCase();
                var c = (item.getAttribute('data-fornecedor-cnpj') || '').toLowerCase();
                item.style.display = (n.indexOf(termo) !== -1 || c.indexOf(termo) !== -1) ? '' : 'none';
            });
        });
    }
});
