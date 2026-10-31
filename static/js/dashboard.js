/**
 * Universal Notes Sharing Platform
 * Dashboard & Admin Interactive Behaviors
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Tab Switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-content-panel');

  if (tabBtns.length > 0) {
    function activateTab(targetId) {
      tabBtns.forEach(btn => {
        if (btn.dataset.target === targetId) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });

      tabPanels.forEach(panel => {
        if (panel.id === targetId) {
          panel.classList.add('active');
        } else {
          panel.classList.remove('active');
        }
      });
    }

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.target;
        activateTab(target);
        window.location.hash = target;
      });
    });

    // Check for hash on page load
    if (window.location.hash) {
      const hashId = window.location.hash.substring(1);
      const matchBtn = document.querySelector(`.tab-btn[data-target="${hashId}"]`);
      if (matchBtn) {
        activateTab(hashId);
      }
    }
  }

  // 2. Generic Modal Open & Close
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('show');
    }
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('show');
    }
  };

  // Close modals on clicking overlay outside the box
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('show');
      }
    });
  });

  // 3. Confirm Delete Note Setup
  window.confirmDeleteNote = function(noteId, noteTitle) {
    const modal = document.getElementById('deleteNoteModal');
    const titleEl = document.getElementById('deleteNoteTitle');
    const formEl = document.getElementById('deleteNoteForm');

    if (modal && titleEl && formEl) {
      titleEl.textContent = noteTitle;
      formEl.action = `/notes/${noteId}/delete`;
      openModal('deleteNoteModal');
    }
  };

  // 4. Admin Live Search on Tables
  const searchInput = document.getElementById('adminTableSearch');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const filter = searchInput.value.toLowerCase();
      const activeTable = document.querySelector('.tab-content-panel.active .custom-table');
      if (!activeTable) return;

      const rows = activeTable.querySelectorAll('tbody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
      });
    });
  }
});

