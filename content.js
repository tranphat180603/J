// Chrome extension to capture and send hover content
(function() {
  class HoverContentSender {
    constructor() {
      this.setupEventListeners();
    }

    setupEventListeners() {
      document.addEventListener('mouseover', (e) => this.handleMouseOver(e));
    }

    handleMouseOver(e) {
      const element = e.target;
      const content = this.extractElementContent(element);

      if (content) {
        // Use arrow function to preserve 'this' context
        this.sendContentToPythonServer(content);
      }
    }

    extractElementContent(element) {
      if (!element) return null;

      // Extract different types of content based on element
      if (element.tagName === 'A') {
        return this.getLinkContent(element);
      } 
      else if (element.tagName === 'IMG') {
        return this.getImageContent(element);
      }
      else if (element.textContent && element.textContent.trim()) {
        return {
          type: 'text',
          content: element.textContent.trim(),
          source: window.location.href
        };
      }

      return null;
    }

    getLinkContent(linkElement) {
      return {
        type: 'link',
        text: linkElement.textContent.trim(),
        href: linkElement.href,
        source: window.location.href
      };
    }

    getImageContent(imgElement) {
      return {
        type: 'image',
        alt: imgElement.alt || '',
        src: imgElement.src,
        source: window.location.href
      };
    }

    sendContentToPythonServer(content) {
      // Ensure content exists before sending
      if (!content) return;

      fetch('http://localhost:5000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(content)
      })
      .then(response => response.json())
      .then(data => {
        // Optional: display or handle the analysis
        console.log('LLM Analysis:', data);
      })
      .catch(error => {
        console.error('Error sending to Python server:', error);
      });
    }
  }

  // Ensure the script runs after page load
  function initializeContentSender() {
    new HoverContentSender();
  }

  // Different initialization methods for various page load states
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeContentSender);
  } else {
    initializeContentSender();
  }
})();