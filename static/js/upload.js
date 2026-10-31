/**
 * Universal Notes Sharing Platform
 * Upload Page File Handling & Validation
 */

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const selectedDisplay = document.getElementById('selectedFileDisplay');
  const fileNameEl = document.getElementById('selectedFileName');
  const fileSizeEl = document.getElementById('selectedFileSize');
  const fileIconEl = document.getElementById('selectedFileIcon');
  const removeFileBtn = document.getElementById('removeFileBtn');
  const uploadForm = document.getElementById('uploadForm');
  const submitBtn = document.getElementById('submitBtn');

  if (!dropzone || !fileInput) return;

  const MAX_SIZE = 32 * 1024 * 1024; // 32MB
  const ALLOWED_EXTS = ['pdf', 'docx', 'doc', 'pptx', 'ppt', 'txt'];

  // Drag and drop event listeners
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelected(files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  if (removeFileBtn) {
    removeFileBtn.addEventListener('click', (e) => {
      e.preventDefault();
      resetFileSelection();
    });
  }

  function handleFileSelected(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    
    // Validate Extension
    if (!ALLOWED_EXTS.includes(ext)) {
      alert(`Invalid format: ".${ext}". Permitted document formats: PDF, DOCX, DOC, PPTX, PPT, TXT.`);
      resetFileSelection();
      return;
    }

    // Validate File Size
    if (file.size > MAX_SIZE) {
      alert(`The selected file is too large (${formatBytes(file.size)}). Maximum allowed file size is 32 MB.`);
      resetFileSelection();
      return;
    }

    // Update Display
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatBytes(file.size);

    // Update Icon
    let iconClass = 'fa-file-lines text-primary';
    if (ext === 'pdf') iconClass = 'fa-file-pdf text-danger';
    else if (['docx', 'doc'].includes(ext)) iconClass = 'fa-file-word text-primary';
    else if (['pptx', 'ppt'].includes(ext)) iconClass = 'fa-file-powerpoint text-warning';
    
    fileIconEl.className = `fa-solid ${iconClass} fa-2x`;

    dropzone.style.display = 'none';
    selectedDisplay.style.display = 'flex';
  }

  function resetFileSelection() {
    fileInput.value = '';
    selectedDisplay.style.display = 'none';
    dropzone.style.display = 'block';
  }

  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // Prevent double submissions
  if (uploadForm && submitBtn) {
    uploadForm.addEventListener('submit', () => {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading & Publishing...';
    });
  }
});

