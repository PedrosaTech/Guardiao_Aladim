/**
 * Relatório de Vendas - Charts (Chart.js)
 */
(function () {
  'use strict';

  function getDados() {
    var el = document.getElementById('dados-relatorio');
    if (!el) return [];
    try {
      return JSON.parse(el.textContent || '[]') || [];
    } catch (e) {
      return [];
    }
  }

  function topN(dados, n) {
    return (dados || []).slice(0, n || 15);
  }

  function labelOf(item) {
    if (!item) return '—';
    if (typeof item.nome === 'string') return item.nome || '—';
    // datas vêm como string ISO quando serializadas
    if (item.nome) return String(item.nome);
    return '—';
  }

  function num(v) {
    var x = Number(v);
    return Number.isFinite(x) ? x : 0;
  }

  function init() {
    var dados = topN(getDados(), 15);
    var labels = dados.map(labelOf);
    var quantidades = dados.map(function (i) { return num(i.quantidade); });
    var valores = dados.map(function (i) { return num(i.valor_total); });

    var ctxQ = document.getElementById('chartQuantidade');
    if (ctxQ && window.Chart) {
      new Chart(ctxQ, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Quantidade',
            data: quantidades,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } }
        }
      });
    }

    var ctxV = document.getElementById('chartValor');
    if (ctxV && window.Chart) {
      new Chart(ctxV, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            label: 'Valor',
            data: valores,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
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

