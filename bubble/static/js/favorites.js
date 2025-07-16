// Modal will be available via global bootstrap object

class FavoritesManager {
    constructor() {
        this.initializeEventListeners();
        this.csrfToken = this.getCsrfToken();
        this.checkFavoriteStatus();
    }

    getCsrfToken() {
        // Try to get CSRF token from meta tag first
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }

        // Fallback to cookies
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    getFavoriteButtons() {
        return [
            document.getElementById('favorite-star'),
            document.getElementById('favorite-star-desktop'),
            document.getElementById('favorite-star-mobile')
        ].filter(btn => btn !== null);
    }

    initializeEventListeners() {
        const favoriteBtns = this.getFavoriteButtons();
        favoriteBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFavoriteClick(e));
        });
    }

    async checkFavoriteStatus() {
        const favoriteBtns = this.getFavoriteButtons();
        if (favoriteBtns.length === 0) return;

        const url = favoriteBtns[0].dataset.url;
        if (!url) return;

        try {
            const response = await fetch(`/favorites/check/?url=${encodeURIComponent(url)}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                favoriteBtns.forEach(btn => this.updateStarAppearance(btn, data.is_favorited));
            }
        } catch (error) {
            console.error('Error checking favorite status:', error);
        }
    }

    updateStarAppearance(btn, isFavorited) {
        if (isFavorited) {
            btn.textContent = '★';
            btn.classList.add('favorited');
            btn.title = gettext('Manage favorites');
        } else {
            btn.textContent = '☆';
            btn.classList.remove('favorited');
            btn.title = gettext('Add to favorites');
        }
    }

    async openManagementForm(url, pageTitle) {
        // Load management form content via AJAX and show in modal
        try {
            const response = await fetch(`/favorites/manage/?url=${encodeURIComponent(url)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const html = await response.text();
            // Extract just the form content from the response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const formContent = doc.querySelector('.card-body').innerHTML;

            // Show in modal
            this.showManagementModal(formContent, url);

        } catch (error) {
            console.error('Error loading management form:', error);
            this.showToast('Error loading favorites form', 'error');
        }
    }

    showManagementModal(formContent, url) {
        const modalHtml = `
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="fas fa-star"></i> ${gettext('Manage Favorite')}
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="${gettext('Close')}"></button>
            </div>
            <div class="modal-body">
                ${formContent}
            </div>
        `;

        const modalContent = document.getElementById('favoritesModalContent');
        modalContent.innerHTML = modalHtml;

        const modal = new bootstrap.Modal(document.getElementById('favoritesModal'));
        modal.show();

        // Initialize Select2 for the modal form
        $('.select2-lists').select2({
            placeholder: gettext('Select lists for this favorite...'),
            allowClear: true,
            width: '100%',
            theme: 'bootstrap-5',
            dropdownParent: $('#favoritesModal'), // Important for modal
            language: {
                noResults: function() {
                    return gettext('No lists found');
                },
                searching: function() {
                    return gettext('Searching...');
                },
                removeAllItems: function() {
                    return gettext('Remove from all lists');
                }
            }
        });

        // Handle form submission
        const form = document.getElementById('manage-favorite-form');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleManagementFormSubmit(form, modal, url);
            });
        }
    }

    async handleManagementFormSubmit(form, modal, url) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>' + gettext('Saving...');

        try {
            const formData = new FormData(form);
            const response = await fetch('/favorites/manage/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.status === 'success') {
                // Update star appearance
                const btns = this.getFavoriteButtons();
                btns.forEach(btn => this.updateStarAppearance(btn, data.is_favorited));

                // Show success message and close modal
                this.showToast(data.message);
                modal.hide();
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error saving favorite:', error);
            this.showToast(error.message || 'Error saving favorite', 'error');
        } finally {
            // Restore button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    async handleFavoriteClick(event) {
        event.preventDefault();
        const btn = event.currentTarget;
        const url = btn.dataset.url;
        const pageTitle = document.title || btn.dataset.title || '';

        // Always open the management form (never toggle)
        this.openManagementForm(url, pageTitle);
    }



    showToast(message, type = 'success') {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : 'success'} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    translate(text) {
        // Using Django's JavaScript i18n system
        return gettext(text);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new FavoritesManager();
});

export default FavoritesManager;
