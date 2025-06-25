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
            btn.title = gettext('Remove from favorites');
        } else {
            btn.textContent = '☆';
            btn.classList.remove('favorited');
            btn.title = gettext('Add to favorites');
        }
    }

    async handleFavoriteClick(event) {
        event.preventDefault();
        const btn = event.currentTarget;
        const url = btn.dataset.url;
        const pageTitle = document.title || btn.dataset.title || '';

        console.log('CSRF Token:', this.csrfToken);
        console.log('URL to favorite:', url);
        console.log('Page title:', pageTitle);

        // First check if already favorited
        btn.disabled = true;
        const originalText = btn.textContent;
        btn.textContent = '...';

        try {
            // Check current status by attempting toggle
            const checkResponse = await fetch('/favorites/toggle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    url: url,
                    title: ''  // Empty title to check status
                })
            });

            if (!checkResponse.ok) {
                throw new Error(`HTTP error! status: ${checkResponse.status}`);
            }

            const checkData = await checkResponse.json();
            console.log('Response data:', checkData);

            if (checkData.is_favorited) {
                // Was not favorited, now is - show modal to get title
                this.showAddModal(url, pageTitle);
            } else {
                // Was favorited, now removed
                this.updateStarAppearance(btn, false);
                this.showToast(checkData.message);
            }
        } catch (error) {
            console.error('Full error details:', error);
            console.error('Error message:', error.message);
            console.error('Error stack:', error.stack);
            this.showToast(`Network error: ${error.message}`, 'error');
            btn.textContent = originalText;
        } finally {
            btn.disabled = false;
        }
    }

    showAddModal(url, title) {
        const modalHtml = `
            <div class="modal-header">
                <h5 class="modal-title">${gettext('Add to favorites')}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="${gettext('Close')}"></button>
            </div>
            <div class="modal-body">
                <form id="add-favorite-form">
                    <div class="mb-3">
                        <label for="favorite-title" class="form-label">${gettext('Title')}</label>
                        <input type="text" class="form-control" id="favorite-title" name="title" value="${this.escapeHtml(title)}" required>
                    </div>
                    <div class="mb-3">
                        <label for="favorite-url" class="form-label">${gettext('URL')}</label>
                        <input type="text" class="form-control" id="favorite-url" name="url" value="${this.escapeHtml(url)}" readonly>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${gettext('Cancel')}</button>
                <button type="button" class="btn btn-primary" id="save-favorite">${gettext('Save')}</button>
            </div>
        `;

        const modalContent = document.getElementById('favoritesModalContent');
        modalContent.innerHTML = modalHtml;

        const modal = new bootstrap.Modal(document.getElementById('favoritesModal'));
        modal.show();

        // Handle save
        let saved = false;
        document.getElementById('save-favorite').addEventListener('click', async () => {
            const titleInput = document.getElementById('favorite-title');
            if (titleInput.value.trim()) {
                saved = true;
                // Update the favorite with the title
                await this.updateFavoriteTitle(url, titleInput.value.trim());
                modal.hide();
            }
        });

        modal._element.addEventListener('hidden.bs.modal', async () => {
            if (!saved) {
                // User closed without saving, remove the favorite
                await this.toggleFavorite(url, '');
                const btns = this.getFavoriteButtons();
                btns.forEach(btn => this.updateStarAppearance(btn, false));
            }
        });
    }

    async updateFavoriteTitle(url, title) {
        try {
            // Update the existing favorite with the title by making another request
            const response = await fetch('/favorites/toggle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    url: url,
                    title: title,
                    update_title: true  // Flag to indicate we want to update title
                })
            });

            const data = await response.json();
            const btns = this.getFavoriteButtons();
            btns.forEach(btn => this.updateStarAppearance(btn, true));
            this.showToast(gettext('Added to favorites'));
        } catch (error) {
            console.error('Error updating favorite:', error);
            this.showToast('Error saving favorite', 'error');
        }
    }

    async toggleFavorite(url, title) {
        try {
            const response = await fetch('/favorites/toggle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    url: url,
                    title: title
                })
            });

            const data = await response.json();
            const btns = this.getFavoriteButtons();
            btns.forEach(btn => this.updateStarAppearance(btn, data.is_favorited));
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
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
