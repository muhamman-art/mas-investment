/* ============================================================
   MAS INVESTMENT - Dashboard JavaScript
   ============================================================ */

'use strict';

document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('sidebarToggle');
  const closeBtn = document.getElementById('sidebarClose');

  function openSidebar() {
    sidebar?.classList.add('open');
    overlay?.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('active');
    document.body.style.overflow = '';
  }

  toggleBtn?.addEventListener('click', openSidebar);
  closeBtn?.addEventListener('click', closeSidebar);
  overlay?.addEventListener('click', closeSidebar);

  // Active link highlighting
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    if (link.href && link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // Mark all notifications read
  document.querySelector('[data-mark-all-read]')?.addEventListener('click', async function(e) {
    e.preventDefault();
    const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    try {
      await fetch('/notifications/mark-all-read/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' }
      });
      document.querySelectorAll('.notification-item.unread').forEach(el => el.classList.remove('unread'));
      document.querySelectorAll('.badge-dot').forEach(el => el.remove());
    } catch {}
  });

  // Auto-dismiss alerts
  document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(alert)?.close(), 5000);
  });

  // Table row click to detail
  document.querySelectorAll('tr[data-href]').forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', () => window.location.href = row.dataset.href);
  });

  // Confirmation buttons
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function(e) {
      if (!confirm(this.dataset.confirm)) e.preventDefault();
    });
  });

  // Image preview before upload
  document.querySelectorAll('input[type=file][data-preview]').forEach(input => {
    input.addEventListener('change', function() {
      const previewId = this.dataset.preview;
      const preview = document.getElementById(previewId);
      if (!preview) return;
      preview.innerHTML = '';
      Array.from(this.files).slice(0, 5).forEach(file => {
        if (!file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = e => {
          const div = document.createElement('div');
          div.className = 'image-preview-item';
          div.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
          preview.appendChild(div);
        };
        reader.readAsDataURL(file);
      });
    });
  });
});
