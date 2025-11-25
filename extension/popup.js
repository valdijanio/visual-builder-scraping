// Visual Builder Scraping - Popup Script

// State
let backendUrl = 'http://localhost:8000/api';
let templateName = '';
let fields = [];
let selecting = false;
let pendingSelector = null;

// DOM Elements
const backendUrlInput = document.getElementById('backendUrl');
const templateNameInput = document.getElementById('templateName');
const toggleSelectionBtn = document.getElementById('toggleSelection');
const fieldsList = document.getElementById('fieldsList');
const fieldCount = document.getElementById('fieldCount');
const testTemplateBtn = document.getElementById('testTemplate');
const saveTemplateBtn = document.getElementById('saveTemplate');
const testResults = document.getElementById('testResults');
const testResultsContent = document.getElementById('testResultsContent');
const closeResultsBtn = document.getElementById('closeResults');
const statusMessage = document.getElementById('statusMessage');
const fieldNameModal = document.getElementById('fieldNameModal');
const fieldNameInput = document.getElementById('fieldNameInput');
const modalSelector = document.getElementById('modalSelector');
const modalPreview = document.getElementById('modalPreview');
const fieldTypeSelect = document.getElementById('fieldTypeSelect');
const attributeSection = document.getElementById('attributeSection');
const attributeInput = document.getElementById('attributeInput');
const cancelFieldBtn = document.getElementById('cancelField');
const confirmFieldBtn = document.getElementById('confirmField');

// Initialize
async function init() {
  // Load saved settings
  const saved = await chrome.storage.local.get(['backendUrl', 'templateName', 'fields']);
  if (saved.backendUrl) {
    backendUrl = saved.backendUrl;
    backendUrlInput.value = backendUrl;
  }
  if (saved.templateName) {
    templateName = saved.templateName;
    templateNameInput.value = templateName;
  }
  if (saved.fields) {
    fields = saved.fields;
    renderFields();
  }

  // Check current selection state
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_STATUS' });
      selecting = response?.selecting || false;
      updateSelectionButton();
    } catch (e) {
      // Content script might not be loaded
    }
  }
}

// Save settings
async function saveSettings() {
  await chrome.storage.local.set({
    backendUrl,
    templateName,
    fields,
  });
}

// Render fields list
function renderFields() {
  fieldCount.textContent = fields.length;
  testTemplateBtn.disabled = fields.length === 0;
  saveTemplateBtn.disabled = fields.length === 0 || !templateName;

  if (fields.length === 0) {
    fieldsList.innerHTML = `
      <div class="empty-state">
        Nenhum campo capturado ainda.<br>
        Clique em "Iniciar Seleção" e selecione elementos na página.
      </div>
    `;
    return;
  }

  fieldsList.innerHTML = fields
    .map(
      (field, index) => `
      <div class="field-item">
        <div class="field-info">
          <div class="field-name">${escapeHtml(field.name)}</div>
          <div class="field-selector">${escapeHtml(field.selector)}</div>
        </div>
        <span class="field-type">${field.type}</span>
        <button class="field-remove" data-index="${index}">&times;</button>
      </div>
    `
    )
    .join('');

  // Add remove event listeners
  fieldsList.querySelectorAll('.field-remove').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const index = parseInt(e.target.dataset.index);
      fields.splice(index, 1);
      renderFields();
      saveSettings();
    });
  });
}

// Update selection button state
function updateSelectionButton() {
  if (selecting) {
    toggleSelectionBtn.textContent = 'Parar Seleção';
    document.body.classList.add('selection-active');
  } else {
    toggleSelectionBtn.textContent = 'Iniciar Seleção';
    document.body.classList.remove('selection-active');
  }
}

// Toggle selection mode
async function toggleSelection() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;

  // Check if content script is already injected
  let scriptInjected = false;
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_STATUS' });
    scriptInjected = response !== undefined;
  } catch (e) {
    scriptInjected = false;
  }

  // Only inject if not already present
  if (!scriptInjected) {
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });
      await chrome.scripting.insertCSS({
        target: { tabId: tab.id },
        files: ['content.css']
      });
      // Wait for script to initialize
      await new Promise(resolve => setTimeout(resolve, 100));
    } catch (e) {
      console.log('Script injection:', e.message);
    }
  }

  try {
    const messageType = selecting ? 'STOP_SELECTION' : 'START_SELECTION';
    await chrome.tabs.sendMessage(tab.id, { type: messageType });
    selecting = !selecting;
    updateSelectionButton();
  } catch (e) {
    showStatus('Erro: esta página não permite scripts de extensão', 'error');
  }
}

// Show field name modal
function showFieldNameModal(selector, preview) {
  pendingSelector = { selector, preview };
  modalSelector.textContent = selector;
  modalPreview.textContent = preview || '(sem preview)';
  fieldNameInput.value = '';
  fieldTypeSelect.value = 'text';
  attributeInput.value = '';
  attributeSection.classList.add('hidden');
  fieldNameModal.classList.remove('hidden');
  fieldNameInput.focus();
}

// Hide field name modal
function hideFieldNameModal() {
  fieldNameModal.classList.add('hidden');
  pendingSelector = null;
}

// Add field
function addField() {
  const name = fieldNameInput.value.trim();
  const type = fieldTypeSelect.value;
  const attribute = attributeInput.value.trim();

  if (!name) {
    showStatus('Digite um nome para o campo', 'error');
    return;
  }

  if (fields.some((f) => f.name === name)) {
    showStatus('Já existe um campo com esse nome', 'error');
    return;
  }

  if (type === 'attribute' && !attribute) {
    showStatus('Digite o nome do atributo', 'error');
    return;
  }

  fields.push({
    name,
    selector: pendingSelector.selector,
    type,
    attribute: type === 'attribute' ? attribute : undefined,
  });

  renderFields();
  saveSettings();
  hideFieldNameModal();
  showStatus(`Campo "${name}" adicionado`, 'success');
}

// Test template
async function testTemplate() {
  if (fields.length === 0) return;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url) {
    showStatus('Não foi possível obter a URL da página', 'error');
    return;
  }

  testResults.classList.remove('hidden');
  testResultsContent.textContent = 'Testando...';

  try {
    // First create or update template temporarily
    const response = await fetch(`${backendUrl}/templates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: templateName || 'Teste Temporário',
        url_pattern: null,
        selectors: fields,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const template = await response.json();

    // Test the template
    const testResponse = await fetch(`${backendUrl}/templates/${template.id}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: tab.url }),
    });

    if (!testResponse.ok) {
      throw new Error(`HTTP ${testResponse.status}`);
    }

    const result = await testResponse.json();
    testResultsContent.textContent = JSON.stringify(result.data, null, 2);
    showStatus(`Teste concluído em ${result.duration_ms}ms`, 'success');
  } catch (e) {
    testResultsContent.textContent = `Erro: ${e.message}`;
    showStatus('Erro ao testar template', 'error');
  }
}

// Save template
async function saveTemplate() {
  if (fields.length === 0 || !templateName) return;

  try {
    const response = await fetch(`${backendUrl}/templates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: templateName,
        url_pattern: null,
        selectors: fields,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const template = await response.json();
    showStatus(`Template "${template.name}" salvo com sucesso!`, 'success');

    // Clear fields after save
    fields = [];
    renderFields();
    saveSettings();
  } catch (e) {
    showStatus(`Erro ao salvar: ${e.message}`, 'error');
  }
}

// Show status message
function showStatus(message, type = 'info') {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
  statusMessage.classList.remove('hidden');

  setTimeout(() => {
    statusMessage.classList.add('hidden');
  }, 3000);
}

// Escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Event Listeners
backendUrlInput.addEventListener('change', (e) => {
  backendUrl = e.target.value;
  saveSettings();
});

templateNameInput.addEventListener('input', (e) => {
  templateName = e.target.value;
  saveTemplateBtn.disabled = fields.length === 0 || !templateName;
  saveSettings();
});

toggleSelectionBtn.addEventListener('click', toggleSelection);
testTemplateBtn.addEventListener('click', testTemplate);
saveTemplateBtn.addEventListener('click', saveTemplate);

closeResultsBtn.addEventListener('click', () => {
  testResults.classList.add('hidden');
});

fieldTypeSelect.addEventListener('change', (e) => {
  if (e.target.value === 'attribute') {
    attributeSection.classList.remove('hidden');
  } else {
    attributeSection.classList.add('hidden');
  }
});

cancelFieldBtn.addEventListener('click', hideFieldNameModal);
confirmFieldBtn.addEventListener('click', addField);

fieldNameInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    addField();
  }
});

// Listen for element selections from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ELEMENT_SELECTED') {
    showFieldNameModal(message.payload.selector, message.payload.preview);
  }
});

// Initialize popup
init();
