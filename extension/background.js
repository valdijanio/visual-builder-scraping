// Visual Builder Scraping - Background Service Worker

// Relay messages between popup and content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ELEMENT_SELECTED') {
    console.log('[Background] Element selected:', message.payload);

    // Save to storage so popup can retrieve it when opened
    chrome.storage.local.set({ pendingSelection: message.payload });

    // Also try to forward to popup if open
    chrome.runtime.sendMessage(message).catch(() => {
      // Popup might be closed, that's ok - we saved to storage
      console.log('[Background] Popup not open, selection saved to storage');
    });
  }

  return true;
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  // Open popup
  chrome.action.openPopup();
});
