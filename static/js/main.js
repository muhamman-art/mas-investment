/* ============================================================
   MAS INVESTMENT - Main JavaScript
   ============================================================ */

'use strict';

// ── PASSWORD TOGGLE ────────────────────────────────────────
function togglePassword(fieldId, btn) {
  const field = document.getElementById(fieldId);
  const icon = btn.querySelector('i');
  if (field.type === 'password') {
    field.type = 'text';
    icon.className = 'bi bi-eye-slash text-muted';
  } else {
    field.type = 'password';
    icon.className = 'bi bi-eye text-muted';
  }
}

// ── WISHLIST AJAX ──────────────────────────────────────────
function toggleWishlist(event, productId) {
  event.preventDefault();
  event.stopPropagation();
  const btn = event.currentTarget;
  const icon = btn.querySelector('i');
  const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';

  fetch(`/shop/wishlist/toggle/${productId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
  .then(r => r.json())
  .then(data => {
    if (data.added) {
      icon.className = 'bi bi-heart-fill text-danger';
      btn.title = 'Remove from Wishlist';
      showToast('Added to wishlist!', 'success');
    } else {
      icon.className = 'bi bi-heart';
      btn.title = 'Add to Wishlist';
      showToast('Removed from wishlist', 'info');
    }
  })
  .catch(() => {
    window.location.href = `/auth/login/?next=${window.location.pathname}`;
  });
}

// ── TOAST NOTIFICATION ─────────────────────────────────────
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px';
    document.body.appendChild(container);
  }

  const colors = {
    success: { bg: '#10b981', icon: 'bi-check-circle-fill' },
    error: { bg: '#ef4444', icon: 'bi-x-circle-fill' },
    warning: { bg: '#f59e0b', icon: 'bi-exclamation-triangle-fill' },
    info: { bg: '#3b82f6', icon: 'bi-info-circle-fill' },
  };
  const c = colors[type] || colors.info;

  const toast = document.createElement('div');
  toast.style.cssText = `
    background:${c.bg};color:#fff;padding:12px 18px;border-radius:10px;
    display:flex;align-items:center;gap:10px;font-size:14px;font-weight:500;
    box-shadow:0 4px 12px rgba(0,0,0,0.2);
    animation:slideIn 0.25s ease;min-width:200px;max-width:320px;
  `;
  toast.innerHTML = `<i class="bi ${c.icon}"></i><span>${message}</span>`;
  container.appendChild(toast);

  const style = document.createElement('style');
  style.textContent = `@keyframes slideIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}`;
  if (!document.getElementById('toast-style')) {
    style.id = 'toast-style';
    document.head.appendChild(style);
  }

  setTimeout(() => {
    toast.style.animation = 'slideIn 0.25s ease reverse';
    setTimeout(() => toast.remove(), 240);
  }, 3000);
}

// ── ADD TO CART AJAX ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  // Handle cart form submissions with AJAX
  document.querySelectorAll('form.ajax-cart').forEach(form => {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const btn = form.querySelector('[type=submit]');
      const original = btn.innerHTML;
      btn.innerHTML = '<i class="bi bi-arrow-repeat spin me-1"></i>Adding...';
      btn.disabled = true;

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          showToast(data.message, 'success');
          // Update cart count in navbar
          document.querySelectorAll('.cart-count').forEach(el => {
            el.textContent = data.cart_count;
            el.style.display = data.cart_count > 0 ? '' : 'none';
          });
        } else {
          showToast(data.message || 'Error', 'error');
        }
      })
      .catch(() => showToast('Network error', 'error'))
      .finally(() => {
        btn.innerHTML = original;
        btn.disabled = false;
      });
    });
  });

  // Auto-dismiss alerts after 5 seconds
  document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert?.close();
    }, 5000);
  });

  // Image lazy loading fallback
  document.querySelectorAll('img[loading="lazy"]').forEach(img => {
    img.onerror = function() {
      this.src = '/static/images/placeholder.png';
    };
  });
});

// ── CONFIRM DIALOGS ────────────────────────────────────────
function confirmAction(message, url, method = 'POST') {
  if (!confirm(message)) return false;
  if (method === 'GET') {
    window.location.href = url;
    return;
  }
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = url;
  const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
  form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">`;
  document.body.appendChild(form);
  form.submit();
}

// ── PRICE RANGE FILTER ─────────────────────────────────────
function applyPriceRange(form) {
  const min = document.getElementById('minPrice')?.value;
  const max = document.getElementById('maxPrice')?.value;
  const url = new URL(window.location.href);
  if (min) url.searchParams.set('min_price', min);
  else url.searchParams.delete('min_price');
  if (max) url.searchParams.set('max_price', max);
  else url.searchParams.delete('max_price');
  url.searchParams.set('page', 1);
  window.location.href = url.toString();
}

// ── QUANTITY STEPPER ───────────────────────────────────────
function stepQty(btn, step) {
  const input = btn.closest('.qty-wrap').querySelector('input[type=number]');
  const min = parseInt(input.min) || 1;
  const max = parseInt(input.max) || 999;
  let val = parseInt(input.value) || 1;
  val = Math.min(Math.max(val + step, min), max);
  input.value = val;
  input.dispatchEvent(new Event('change'));
}
