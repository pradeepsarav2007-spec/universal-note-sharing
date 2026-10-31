/**
 * Universal Notes Sharing Platform
 * Global Application JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Toggle
  const mobileToggle = document.getElementById('mobileNavToggle');
  const navMenu = document.getElementById('navMenu');
  
  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      navMenu.classList.toggle('show');
      const icon = mobileToggle.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-bars');
        icon.classList.toggle('fa-xmark');
      }
    });
  }

  // 2. User Avatar Dropdown
  const userAvatarBtn = document.getElementById('userAvatarBtn');
  const userDropdownMenu = document.getElementById('userDropdownMenu');

  if (userAvatarBtn && userDropdownMenu) {
    userAvatarBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdownMenu.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!userDropdownMenu.contains(e.target) && !userAvatarBtn.contains(e.target)) {
        userDropdownMenu.classList.remove('show');
      }
    });
  }

  // 3. Navbar Live Search (with debounce)
  const navSearchInput = document.getElementById('navSearchInput');
  const navSearchDropdown = document.getElementById('navSearchDropdown');

  if (navSearchInput && navSearchDropdown) {
    let debounceTimer;

    navSearchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      const query = navSearchInput.value.trim();

      if (query.length < 2) {
        navSearchDropdown.style.display = 'none';
        navSearchDropdown.innerHTML = '';
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`/api/quick-search?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
            if (data.length === 0) {
              navSearchDropdown.innerHTML = `
                <div class="search-item" style="color: var(--text-muted); font-size: 0.85rem; justify-content: center; padding: 1rem;">
                  <i class="fa-solid fa-magnifying-glass"></i> No matching notes found
                </div>
              `;
            } else {
              navSearchDropdown.innerHTML = data.map(item => `
                <a href="${item.url}" class="search-item">
                  <span class="file-type-badge file-type-${item.type.toLowerCase()}" style="font-size: 0.65rem; padding: 0.2rem 0.4rem;">
                    ${item.type}
                  </span>
                  <div style="flex: 1; overflow: hidden;">
                    <div style="font-weight: 600; font-size: 0.875rem; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;">
                      ${item.title}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">
                      ${item.subject} &bull; Sem ${item.semester}
                    </div>
                  </div>
                  <i class="fa-solid fa-chevron-right" style="font-size: 0.7rem; color: var(--text-light);"></i>
                </a>
              `).join('');
            }
            navSearchDropdown.style.display = 'block';
          })
          .catch(err => {
            console.error('Quick search error:', err);
          });
      }, 250);
    });

    document.addEventListener('click', (e) => {
      if (!navSearchDropdown.contains(e.target) && e.target !== navSearchInput) {
        navSearchDropdown.style.display = 'none';
      }
    });
  }

  // 4. Auto-dismiss Flash Alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 400);
    }, 5500);

    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => alert.remove());
    }
  });

  // 5. Copy Link Helper
  window.copyToClipboard = function(text, elementBtn) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        showCopySuccess(elementBtn);
      });
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      showCopySuccess(elementBtn);
    }
  };

  function showCopySuccess(btn) {
    if (!btn) return;
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
    btn.classList.add('btn-primary');
    setTimeout(() => {
      btn.innerHTML = originalHtml;
      btn.classList.remove('btn-primary');
    }, 2000);
  }
});

