// Visual Builder Scraping - Background Service Worker

// Relay messages between popup and content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ELEMENT_SELECTED') {
    // Forward to popup if it's open
    chrome.runtime.sendMessage(message).catch(() => {
      // Popup might be closed, that's ok
    });
  }

  return true;
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  // Open popup
  chrome.action.openPopup();
});
