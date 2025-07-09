// Select2 initialization module

export function initializeSelect2() {
  // Check if jQuery and Select2 are available
  if (typeof $ === 'undefined' || typeof $.fn.select2 === 'undefined') {
    console.error('Select2 initialization failed: jQuery or Select2 not available');
    return;
  }

  // Initialize Select2 for category dropdowns with search
  $('.select2-category').select2({
    placeholder: gettext('Search and select a category...'),
    allowClear: false,
    width: '100%',
    theme: 'default',
    minimumInputLength: 0, // Allow search from first character
    language: {
      inputTooShort: function() {
        return gettext('Type to search...');
      },
      noResults: function() {
        return gettext('No results found');
      },
      searching: function() {
        return gettext('Searching...');
      }
    }
  });

  // Initialize Select2 for all other select fields with search
  $('.select2-field').select2({
    allowClear: false,
    width: '100%',
    theme: 'default',
    minimumInputLength: 0, // Allow search from first character
    language: {
      inputTooShort: function() {
        return gettext('Type to search...');
      },
      noResults: function() {
        return gettext('No results found');
      },
      searching: function() {
        return gettext('Searching...');
      }
    }
  });

  // Initialize any standard select elements that should have Select2
  $('select.form-select').not('.select2-hidden-accessible').each(function() {
    // Skip if already initialized or has specific classes to exclude
    if ($(this).hasClass('no-select2') || $(this).hasClass('select2-hidden-accessible')) {
      return;
    }

    $(this).select2({
      allowClear: false,
      width: '100%',
      theme: 'default',
      minimumInputLength: 0,
      language: {
        inputTooShort: function() {
          return gettext('Type to search...');
        },
        noResults: function() {
          return gettext('No results found');
        },
        searching: function() {
          return gettext('Searching...');
        }
      }
    });
  });
}

// Function to initialize Select2 on dynamically added elements
export function initializeSelect2OnElement(element) {
  if (typeof $ === 'undefined' || typeof $.fn.select2 === 'undefined') {
    console.error('Select2 initialization failed: jQuery or Select2 not available');
    return;
  }

  const $element = $(element);

  // Skip if already initialized
  if ($element.hasClass('select2-hidden-accessible')) {
    return;
  }

  // Determine options based on class
  let options = {
    allowClear: false,
    width: '100%',
    theme: 'default',
    minimumInputLength: 0,
    language: {
      inputTooShort: function() {
        return gettext('Type to search...');
      },
      noResults: function() {
        return gettext('No results found');
      },
      searching: function() {
        return gettext('Searching...');
      }
    }
  };

  // Add placeholder for category fields
  if ($element.hasClass('select2-category')) {
    options.placeholder = gettext('Search and select a category...');
  }

  $element.select2(options);
}

// Auto-initialize on document ready
document.addEventListener('DOMContentLoaded', () => {
  // Wait a bit for everything to load
  setTimeout(() => {
    initializeSelect2();
  }, 100);
});

// Re-initialize when new content is added to the DOM
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      if (node.nodeType === 1) { // Element node
        // Check if the node itself is a select
        if (node.tagName === 'SELECT' && (node.classList.contains('form-select') || node.classList.contains('select2-field') || node.classList.contains('select2-category'))) {
          initializeSelect2OnElement(node);
        }
        // Check for selects within the added node
        const selects = node.querySelectorAll('select.form-select, select.select2-field, select.select2-category');
        selects.forEach(select => {
          initializeSelect2OnElement(select);
        });
      }
    });
  });
});

// Start observing the document body for changes
observer.observe(document.body, {
  childList: true,
  subtree: true
});
