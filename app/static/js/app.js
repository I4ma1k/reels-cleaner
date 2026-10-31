document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const tabUrl = document.getElementById('tabUrl');
  const tabUpload = document.getElementById('tabUpload');
  const urlMode = document.getElementById('url-mode');
  const uploadMode = document.getElementById('upload-mode');

  const urlForm = document.getElementById('urlForm');
  const reelUrlInput = document.getElementById('reelUrlInput');
  const btnPaste = document.getElementById('btnPaste');
  const btnSubmitUrl = document.getElementById('btnSubmitUrl');

  const uploadForm = document.getElementById('uploadForm');
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const btnSelectFile = document.getElementById('btnSelectFile');
  const selectedFileInfo = document.getElementById('selectedFileInfo');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const btnRemoveFile = document.getElementById('btnRemoveFile');
  const btnSubmitUpload = document.getElementById('btnSubmitUpload');

  // Trimming settings
  const settingsToggle = document.getElementById('settingsToggle');
  const settingsBox = document.querySelector('.settings-box');
  const autoTrimToggle = document.getElementById('autoTrimToggle');
  const customTrimInput = document.getElementById('customTrimInput');
  const currentTrimLabel = document.getElementById('currentTrimLabel');
  const presetButtons = document.querySelectorAll('.btn-preset');

  // Processing & Results
  const processingCard = document.getElementById('processingCard');
  const processingStepTitle = document.getElementById('processingStepTitle');
  const processingStepSub = document.getElementById('processingStepSub');
  const progressBar = document.getElementById('progressBar');

  const errorCard = document.getElementById('errorCard');
  const errorMessage = document.getElementById('errorMessage');
  const btnDismissError = document.getElementById('btnDismissError');

  const resultCard = document.getElementById('resultCard');
  const videoPreview = document.getElementById('videoPreview');
  const resAuthor = document.getElementById('resAuthor');
  const resTrimmed = document.getElementById('resTrimmed');
  const resDuration = document.getElementById('resDuration');
  const resSize = document.getElementById('resSize');
  const btnDownloadClean = document.getElementById('btnDownloadClean');
  const btnShare = document.getElementById('btnShare');
  const btnReset = document.getElementById('btnReset');

  // QR Modal
  const btnOpenQrModal = document.getElementById('btnOpenQrModal');
  const qrModal = document.getElementById('qrModal');
  const btnCloseQrModal = document.getElementById('btnCloseQrModal');
  const btnCopyNetworkUrl = document.getElementById('btnCopyNetworkUrl');
  const networkUrlText = document.getElementById('networkUrlText');

  let activeResultData = null;
  let progressInterval = null;

  // --- Tab Switching ---
  function switchTab(activeTab, contentId) {
    [tabUrl, tabUpload].forEach(t => t.classList.remove('active'));
    [urlMode, uploadMode].forEach(m => m.classList.remove('active'));
    activeTab.classList.add('active');
    document.getElementById(contentId).classList.add('active');
    hideError();
  }

  tabUrl.addEventListener('click', () => switchTab(tabUrl, 'url-mode'));
  tabUpload.addEventListener('click', () => switchTab(tabUpload, 'upload-mode'));

  // --- Clipboard Paste Helper ---
  if (btnPaste) {
    btnPaste.addEventListener('click', async () => {
      try {
        const text = await navigator.clipboard.readText();
        if (text) {
          reelUrlInput.value = text.trim();
          reelUrlInput.focus();
        }
      } catch (err) {
        // Fallback for browsers that restrict clipboard read
        reelUrlInput.focus();
        document.execCommand('paste');
      }
    });
  }

  // --- Settings Box ---
  settingsToggle.addEventListener('click', () => {
    settingsBox.classList.toggle('open');
  });

  autoTrimToggle.addEventListener('change', (e) => {
    const isChecked = e.target.checked;
    currentTrimLabel.textContent = isChecked ? `${customTrimInput.value}s` : 'Desactivado';
    currentTrimLabel.style.opacity = isChecked ? '1' : '0.5';
  });

  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      presetButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const val = parseFloat(btn.dataset.val);
      customTrimInput.value = val;
      if (autoTrimToggle.checked) {
        currentTrimLabel.textContent = `${val}s`;
      }
    });
  });

  customTrimInput.addEventListener('input', (e) => {
    presetButtons.forEach(b => b.classList.remove('active'));
    const val = parseFloat(e.target.value) || 0;
    if (autoTrimToggle.checked) {
      currentTrimLabel.textContent = `${val}s`;
    }
  });

  // --- File Dropzone ---
  btnSelectFile.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropzone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function handleFileSelected(file) {
    fileNameDisplay.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(1)} MB)`;
    selectedFileInfo.style.display = 'flex';
    dropzone.style.display = 'none';
    btnSubmitUpload.disabled = false;
  }

  btnRemoveFile.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.value = '';
    selectedFileInfo.style.display = 'none';
    dropzone.style.display = 'block';
    btnSubmitUpload.disabled = true;
  });

  // --- Progress Animation ---
  function startProgress(isUpload = false) {
    hideError();
    resultCard.style.display = 'none';
    urlMode.style.display = 'none';
    uploadMode.style.display = 'none';
    document.querySelector('.tabs-container').style.display = 'none';
    processingCard.style.display = 'block';

    let progress = 10;
    progressBar.style.width = '10%';

    const steps = isUpload ? [
      { p: 30, title: 'Subiendo video...', sub: 'Transfiriendo archivo localmente...' },
      { p: 65, title: 'Analizando video...', sub: 'Detectando duración con FFmpeg...' },
      { p: 85, title: 'Recortando final...', sub: 'Eliminando los últimos segundos de Instagram...' },
      { p: 95, title: 'Generando video limpio...', sub: 'Optimizando para celular y web...' }
    ] : [
      { p: 30, title: 'Conectando con Instagram...', sub: 'Buscando servidor de medios...' },
      { p: 60, title: 'Descargando Reel...', sub: 'Obteniendo stream de video en alta calidad...' },
      { p: 85, title: 'Eliminando outro...', sub: 'Cortando el logo final de Instagram con FFmpeg...' },
      { p: 95, title: 'Finalizando...', sub: 'Preparando descarga...' }
    ];

    let currentStep = 0;
    progressInterval = setInterval(() => {
      if (currentStep < steps.length) {
        const step = steps[currentStep];
        progress = step.p;
        progressBar.style.width = `${progress}%`;
        processingStepTitle.textContent = step.title;
        processingStepSub.textContent = step.sub;
        currentStep++;
      }
    }, 1200);
  }

  function stopProgress() {
    if (progressInterval) clearInterval(progressInterval);
    processingCard.style.display = 'none';
    document.querySelector('.tabs-container').style.display = 'grid';
    // restore active tab
    if (tabUrl.classList.contains('active')) {
      urlMode.style.display = 'block';
    } else {
      uploadMode.style.display = 'block';
    }
  }

  // --- Show Results ---
  function showResults(data) {
    stopProgress();
    activeResultData = data;
    
    // Hide forms, show result
    urlMode.style.display = 'none';
    uploadMode.style.display = 'none';
    document.querySelector('.tabs-container').style.display = 'none';
    resultCard.style.display = 'block';

    resAuthor.textContent = data.author ? `@${data.author}` : 'Instagram Reel';
    resTrimmed.textContent = data.seconds_removed > 0 ? `✂️ -${data.seconds_removed}s` : 'Sin corte';
    resDuration.textContent = `${data.clean_duration}s`;
    resSize.textContent = `${data.file_size_mb} MB`;

    videoPreview.src = data.stream_url;
    videoPreview.load();

    btnDownloadClean.href = data.download_url;
    btnDownloadClean.setAttribute('download', `Reel_Limpio_${data.file_id}`);
  }

  // --- Error Handling ---
  function showError(msg) {
    stopProgress();
    errorMessage.textContent = msg || 'Ocurrió un error inesperado al procesar el Reel.';
    errorCard.style.display = 'flex';
  }

  function hideError() {
    errorCard.style.display = 'none';
  }

  btnDismissError.addEventListener('click', hideError);

  // --- Form 1 Submit: URL ---
  urlForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = reelUrlInput.value.trim();
    if (!url) return;

    const trimEnd = parseFloat(customTrimInput.value) || 3.0;
    const autoTrim = autoTrimToggle.checked;

    startProgress(false);

    try {
      const response = await fetch('/api/process-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url,
          trim_end: trimEnd,
          auto_trim: autoTrim
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Error procesando el enlace');
      }

      showResults(data);
    } catch (err) {
      showError(err.message);
    }
  });

  // --- Form 2 Submit: Upload ---
  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = fileInput.files[0];
    if (!file) return;

    const trimEnd = parseFloat(customTrimInput.value) || 3.0;
    const autoTrim = autoTrimToggle.checked;

    startProgress(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('trim_end', trimEnd);
      formData.append('auto_trim', autoTrim);

      const response = await fetch('/api/process-upload', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Error procesando el archivo');
      }

      showResults(data);
    } catch (err) {
      showError(err.message);
    }
  });

  // --- Native Web Share ---
  btnShare.addEventListener('click', async () => {
    if (!activeResultData) return;

    if (navigator.share) {
      try {
        await navigator.share({
          title: activeResultData.title || 'Reel Limpio',
          text: 'Video descargado sin final de Instagram:',
          url: window.location.origin + activeResultData.download_url
        });
      } catch (err) {
        // User cancelled share
      }
    } else {
      // Fallback: Copy direct download link to clipboard
      try {
        await navigator.clipboard.writeText(window.location.origin + activeResultData.download_url);
        alert('¡Enlace de descarga copiado al portapapeles!');
      } catch (err) {
        alert('Enlace: ' + window.location.origin + activeResultData.download_url);
      }
    }
  });

  // --- Reset to download another ---
  btnReset.addEventListener('click', () => {
    videoPreview.pause();
    videoPreview.src = '';
    resultCard.style.display = 'none';
    document.querySelector('.tabs-container').style.display = 'grid';
    if (tabUrl.classList.contains('active')) {
      urlMode.style.display = 'block';
    } else {
      uploadMode.style.display = 'block';
    }
    reelUrlInput.value = '';
    fileInput.value = '';
    selectedFileInfo.style.display = 'none';
    dropzone.style.display = 'block';
    btnSubmitUpload.disabled = true;
  });

  // --- QR Modal for Mobile ---
  btnOpenQrModal.addEventListener('click', () => {
    qrModal.style.display = 'flex';
  });

  btnCloseQrModal.addEventListener('click', () => {
    qrModal.style.display = 'none';
  });

  qrModal.addEventListener('click', (e) => {
    if (e.target === qrModal) {
      qrModal.style.display = 'none';
    }
  });

  // --- Service Worker & PWA Installation ---
  let deferredPrompt = null;
  const btnInstallPwa = document.getElementById('btnInstallPwa');

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').catch(err => {
        console.log('SW registration error:', err);
      });
    });
  }

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (btnInstallPwa) {
      btnInstallPwa.style.display = 'inline-flex';
    }
  });

  if (btnInstallPwa) {
    btnInstallPwa.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        btnInstallPwa.style.display = 'none';
      }
      deferredPrompt = null;
    });
  }

  window.addEventListener('appinstalled', () => {
    if (btnInstallPwa) {
      btnInstallPwa.style.display = 'none';
    }
  });
});
