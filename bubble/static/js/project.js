// Import Font Awesome
import '@fortawesome/fontawesome-free/css/all.min.css';

// Project styles
import '../sass/project.scss';
import './favorites.js';
import './select2-init.js';

/* Project specific Javascript goes here. */

// Initialize all Bootstrap components when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize all tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map((tooltipTriggerEl) => {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize all popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map((popoverTriggerEl) => {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Initialize all toasts
  const toastElList = [].slice.call(document.querySelectorAll('.toast'));
  toastElList.map((toastEl) => {
    return new bootstrap.Toast(toastEl);
  });

  // Initialize all collapsible elements
  const collapseElementList = [].slice.call(document.querySelectorAll('.collapse'));
  collapseElementList.map((collapseEl) => {
    return new bootstrap.Collapse(collapseEl, { toggle: false });
  });

  console.log('Bootstrap components initialized');
});
