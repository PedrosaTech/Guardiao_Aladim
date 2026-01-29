/**
 * Funções utilitárias para PDV Móvel
 */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie("csrftoken");

function showLoading(message) {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) {
        const p = overlay.querySelector("p");
        if (p) p.textContent = message || "Carregando...";
        overlay.style.display = "flex";
    }
}

function hideLoading() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.style.display = "none";
}

function showToast(message, type) {
    type = type || "info";
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = "toast " + type;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function () {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(400px)";
        toast.style.transition = "0.3s ease-out";
        setTimeout(function () { toast.remove(); }, 300);
    }, 3000);
}

function formatMoney(value) {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

function formatNumber(value, decimals) {
    if (decimals === undefined) decimals = 2;
    return new Intl.NumberFormat("pt-BR", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(value);
}

function debounce(func, wait) {
    var timeout;
    return function () {
        var args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function () { func.apply(null, args); }, wait);
    };
}

function vibrate(duration) {
    if (typeof navigator !== "undefined" && navigator.vibrate) navigator.vibrate(duration || 50);
}

function isOnline() {
    return typeof navigator !== "undefined" && navigator.onLine;
}

if (typeof window !== "undefined") {
    window.addEventListener("online", function () { showToast("Conexão restaurada", "success"); });
    window.addEventListener("offline", function () { showToast("Sem conexão - Modo offline ativado", "warning"); });
}

function formatTimeAgo(date) {
    const now = new Date();
    const then = new Date(date);
    const diff = now - then;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return "Agora";
    if (minutes < 60) return "Há " + minutes + " min";
    if (hours < 24) return "Há " + hours + "h";
    return days + "d atrás";
}

function smoothScrollTo(element) {
    if (element && element.scrollIntoView) element.scrollIntoView({ behavior: "smooth", block: "center" });
}
