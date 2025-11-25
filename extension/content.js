// Visual Builder Scraping - Content Script

// Prevent multiple injections
if (window.__SCRAPER_INJECTED__) {
  console.log('[Scraper] Already injected, skipping...');
} else {
  window.__SCRAPER_INJECTED__ = true;

(function () {
  let selecting = false;
  let highlightedElement = null;
  let modeIndicator = null;

  console.log('[Scraper] Content script loaded');

  // Check if a selector matches exactly one element
  function isUnique(selector) {
    try {
      return document.querySelectorAll(selector).length === 1;
    } catch {
      return false;
    }
  }

  // Try to get a unique selector using classes
  function getUniqueClassSelector(element) {
    if (!element.classList.length) return null;

    const classes = Array.from(element.classList)
      .filter(c => !c.startsWith('scraper-') && !c.match(/^(active|hover|focus|selected|show|hide|open|closed)/));

    if (!classes.length) return null;

    // Try tag + all classes
    const fullSelector = element.tagName.toLowerCase() + classes.map(c => '.' + CSS.escape(c)).join('');
    if (isUnique(fullSelector)) return fullSelector;

    // Try just classes (without tag)
    const classOnlySelector = classes.map(c => '.' + CSS.escape(c)).join('');
    if (isUnique(classOnlySelector)) return classOnlySelector;

    // Try individual classes
    for (const cls of classes) {
      const singleSelector = '.' + CSS.escape(cls);
      if (isUnique(singleSelector)) return singleSelector;
    }

    return null;
  }

  // Try to get selector using semantic attributes
  function getSemanticSelector(element) {
    const semanticAttrs = ['name', 'role', 'aria-label', 'title', 'placeholder', 'alt', 'for', 'type'];

    for (const attr of semanticAttrs) {
      const value = element.getAttribute(attr);
      if (value && value.length < 100) {
        const selector = `${element.tagName.toLowerCase()}[${attr}="${CSS.escape(value)}"]`;
        if (isUnique(selector)) return selector;
      }
    }
    return null;
  }

  // Try to get selector using :has-text() - works with Playwright
  function getTextBasedSelector(element) {
    // Find the nearest container with an ID
    let container = element;
    while (container && container !== document.body) {
      if (container.id && !container.id.match(/^[0-9]|:|\s/)) {
        break;
      }
      container = container.parentElement;
    }

    if (!container || !container.id) return null;

    // Look for a label/title text in the parent or siblings
    const parent = element.parentElement;
    if (!parent) return null;

    // Get all text from parent to find a label
    const parentText = parent.innerText || '';
    const lines = parentText.split('\n').map(l => l.trim()).filter(l => l.length > 0 && l.length < 50);

    if (lines.length >= 1) {
      // First line is usually the label
      const labelText = lines[0].toUpperCase();
      // Create selector with :has-text() - Playwright pseudo-selector
      const containerId = '#' + CSS.escape(container.id);

      // Try with parent's class
      const parentClasses = Array.from(parent.classList || [])
        .filter(c => !c.startsWith('scraper-'))
        .slice(0, 1);

      if (parentClasses.length > 0) {
        const selector = `${containerId} .${CSS.escape(parentClasses[0])}:has-text("${labelText}")`;
        // Note: :has-text is a Playwright pseudo-selector, not standard CSS
        // We return it for Playwright compatibility
        return selector;
      }
    }

    return null;
  }

  // Try to get selector anchored to an ancestor with ID
  function getAnchorSelector(element) {
    let current = element;
    const path = [];

    while (current && current !== document.body) {
      // Check if current element has a valid ID
      if (current.id && !current.id.match(/^[0-9]|:|\s/)) {
        const idSelector = '#' + CSS.escape(current.id);

        if (path.length === 0) {
          // The element itself has an ID
          if (isUnique(idSelector)) return idSelector;
        } else {
          // Build path from this ID
          const relativePath = path.reverse().join(' > ');
          const fullSelector = idSelector + ' > ' + relativePath;
          if (isUnique(fullSelector)) return fullSelector;

          // Try without direct child combinator
          const looseSelector = idSelector + ' ' + relativePath;
          if (isUnique(looseSelector)) return looseSelector;
        }
      }

      // Add element to path with classes for specificity
      let part = current.tagName.toLowerCase();
      const classes = Array.from(current.classList || [])
        .filter(c => !c.startsWith('scraper-') && !c.match(/^(active|hover|focus|selected)/))
        .slice(0, 2);
      if (classes.length) {
        part += classes.map(c => '.' + CSS.escape(c)).join('');
      }
      path.push(part);

      current = current.parentElement;
    }

    return null;
  }

  // Fallback: build path using nth-child (fragile but always works)
  function buildNthChildPath(element) {
    const path = [];
    let current = element;

    while (current && current !== document.body && current !== document.documentElement) {
      let selector = current.tagName.toLowerCase();

      if (current.id && !current.id.match(/^[0-9]|:|\s/)) {
        selector = '#' + CSS.escape(current.id);
        path.unshift(selector);
        break;
      }

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

  // Generate CSS selector for an element - uses hierarchy of strategies
  function generateSelector(element) {
    // 1. ID único (most reliable)
    if (element.id && !element.id.match(/^[0-9]|:|\s/)) {
      const selector = '#' + CSS.escape(element.id);
      if (isUnique(selector)) return selector;
    }

    // 2. data-* attributes (common in modern frameworks)
    for (const attr of element.attributes) {
      if (attr.name.startsWith('data-') && attr.value && attr.value.length < 100) {
        const selector = `[${attr.name}="${CSS.escape(attr.value)}"]`;
        if (isUnique(selector)) return selector;
      }
    }

    // 3. Unique class combination
    const uniqueClassSelector = getUniqueClassSelector(element);
    if (uniqueClassSelector) return uniqueClassSelector;

    // 4. Semantic attributes (name, role, aria-label, etc.)
    const semanticSelector = getSemanticSelector(element);
    if (semanticSelector) return semanticSelector;

    // 5. Text-based selector with :has-text() - works in Playwright
    const textSelector = getTextBasedSelector(element);
    if (textSelector) return textSelector;

    // 6. Anchor to ancestor with ID (more stable than nth-child)
    const anchorSelector = getAnchorSelector(element);
    if (anchorSelector) return anchorSelector;

    // 7. Last resort: nth-child path (fragile)
    return buildNthChildPath(element);
  }

  // Get element preview text
  function getPreviewText(element) {
    const text = element.innerText || element.textContent || '';
    return text.trim().substring(0, 100) + (text.length > 100 ? '...' : '');
  }

  // Handle mouse over
  function handleMouseOver(e) {
    if (!selecting) return;

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

  // Handle click (using mousedown for reliability)
  function handleClick(e) {
    console.log('[Scraper] Mousedown detected on:', e.target);

    if (!selecting) {
      console.log('[Scraper] Not in selecting mode, ignoring');
      return;
    }

    e.stopPropagation();
    e.preventDefault();

    const element = e.target;
    const selector = generateSelector(element);
    const preview = getPreviewText(element);

    console.log('[Scraper] Selected element:', selector);
    console.log('[Scraper] Preview:', preview);

    // Mark as selected
    element.classList.remove('scraper-highlight');
    element.classList.add('scraper-selected');

    // Send selector to popup
    console.log('[Scraper] Sending message to popup...');
    chrome.runtime.sendMessage({
      type: 'ELEMENT_SELECTED',
      payload: {
        selector: selector,
        preview: preview,
        tagName: element.tagName.toLowerCase(),
        url: window.location.href,
      },
    }).then(() => {
      console.log('[Scraper] Message sent successfully');
    }).catch((err) => {
      console.log('[Scraper] Error sending message:', err);
    });

    // Remove selected class after a delay
    setTimeout(() => {
      element.classList.remove('scraper-selected');
    }, 1000);
  }

  // Start selection mode
  function startSelection() {
    console.log('[Scraper] Starting selection mode');
    selecting = true;
    document.body.classList.add('scraper-selecting');

    // Add mode indicator
    modeIndicator = document.createElement('div');
    modeIndicator.className = 'scraper-mode-indicator';
    modeIndicator.textContent = 'Modo de seleção ativo - clique em um elemento';
    document.body.appendChild(modeIndicator);

    // Add event listeners - use mousedown instead of click for better capture
    document.addEventListener('mouseover', handleMouseOver, true);
    document.addEventListener('mouseout', handleMouseOut, true);
    document.addEventListener('mousedown', handleClick, true);

    console.log('[Scraper] Event listeners added');
  }

  // Stop selection mode
  function stopSelection() {
    console.log('[Scraper] Stopping selection mode');
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
    document.removeEventListener('mousedown', handleClick, true);

    console.log('[Scraper] Event listeners removed');
  }

  // Listen for messages from popup/background
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('[Scraper] Received message:', message.type);

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

} // End of injection guard
