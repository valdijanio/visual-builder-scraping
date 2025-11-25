// Visual Builder Scraping - Content Script
(function () {
  let selecting = false;
  let highlightedElement = null;
  let modeIndicator = null;

  // Generate CSS selector for an element
  function generateSelector(element) {
    // Priority 1: ID
    if (element.id) {
      return '#' + CSS.escape(element.id);
    }

    // Priority 2: Unique class combination
    if (element.classList.length > 0) {
      const classes = Array.from(element.classList)
        .filter(c => !c.startsWith('scraper-'))
        .map(c => '.' + CSS.escape(c))
        .join('');

      if (classes) {
        const selector = element.tagName.toLowerCase() + classes;
        const matches = document.querySelectorAll(selector);
        if (matches.length === 1) {
          return selector;
        }
      }
    }

    // Priority 3: Build path from ancestors
    const path = [];
    let current = element;

    while (current && current !== document.body && current !== document.documentElement) {
      let selector = current.tagName.toLowerCase();

      if (current.id) {
        selector = '#' + CSS.escape(current.id);
        path.unshift(selector);
        break;
      }

      // Add nth-child if there are siblings of same type
      const parent = current.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter(
          child => child.tagName === current.tagName
        );
        if (siblings.length > 1) {
          const index = siblings.indexOf(current) + 1;
          selector += ':nth-child(' + index + ')';
        }
      }

      path.unshift(selector);
      current = current.parentElement;
    }

    return path.join(' > ');
  }

  // Get element preview text
  function getPreviewText(element) {
    const text = element.innerText || element.textContent || '';
    return text.trim().substring(0, 100) + (text.length > 100 ? '...' : '');
  }

  // Handle mouse over
  function handleMouseOver(e) {
    if (!selecting) return;

    e.stopPropagation();
    e.preventDefault();

    // Remove previous highlight
    if (highlightedElement) {
      highlightedElement.classList.remove('scraper-highlight');
    }

    // Add highlight to current element
    highlightedElement = e.target;
    highlightedElement.classList.add('scraper-highlight');
  }

  // Handle mouse out
  function handleMouseOut(e) {
    if (!selecting) return;

    if (highlightedElement) {
      highlightedElement.classList.remove('scraper-highlight');
    }
  }

  // Handle click
  function handleClick(e) {
    if (!selecting) return;

    e.stopPropagation();
    e.preventDefault();

    const element = e.target;
    const selector = generateSelector(element);
    const preview = getPreviewText(element);

    // Mark as selected
    element.classList.remove('scraper-highlight');
    element.classList.add('scraper-selected');

    // Send selector to popup
    chrome.runtime.sendMessage({
      type: 'ELEMENT_SELECTED',
      payload: {
        selector: selector,
        preview: preview,
        tagName: element.tagName.toLowerCase(),
        url: window.location.href,
      },
    });

    // Remove selected class after a delay
    setTimeout(() => {
      element.classList.remove('scraper-selected');
    }, 1000);
  }

  // Start selection mode
  function startSelection() {
    selecting = true;
    document.body.classList.add('scraper-selecting');

    // Add mode indicator
    modeIndicator = document.createElement('div');
    modeIndicator.className = 'scraper-mode-indicator';
    modeIndicator.textContent = 'Modo de seleção ativo - clique em um elemento';
    document.body.appendChild(modeIndicator);

    // Add event listeners
    document.addEventListener('mouseover', handleMouseOver, true);
    document.addEventListener('mouseout', handleMouseOut, true);
    document.addEventListener('click', handleClick, true);
  }

  // Stop selection mode
  function stopSelection() {
    selecting = false;
    document.body.classList.remove('scraper-selecting');

    // Remove mode indicator
    if (modeIndicator) {
      modeIndicator.remove();
      modeIndicator = null;
    }

    // Remove highlight
    if (highlightedElement) {
      highlightedElement.classList.remove('scraper-highlight');
      highlightedElement = null;
    }

    // Remove all selected classes
    document.querySelectorAll('.scraper-selected').forEach(el => {
      el.classList.remove('scraper-selected');
    });

    // Remove event listeners
    document.removeEventListener('mouseover', handleMouseOver, true);
    document.removeEventListener('mouseout', handleMouseOut, true);
    document.removeEventListener('click', handleClick, true);
  }

  // Listen for messages from popup/background
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.type) {
      case 'START_SELECTION':
        startSelection();
        sendResponse({ success: true });
        break;

      case 'STOP_SELECTION':
        stopSelection();
        sendResponse({ success: true });
        break;

      case 'GET_STATUS':
        sendResponse({ selecting: selecting });
        break;

      case 'TEST_SELECTOR':
        try {
          const elements = document.querySelectorAll(message.selector);
          const results = Array.from(elements).map(el => getPreviewText(el));
          sendResponse({ success: true, count: elements.length, results: results });
        } catch (e) {
          sendResponse({ success: false, error: e.message });
        }
        break;
    }

    return true; // Keep message channel open for async response
  });
})();
