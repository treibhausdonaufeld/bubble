class FavoritesManager {
    constructor() {
        this.initializeEventListeners();
        this.csrfToken = this.getCsrfToken();
    }

    getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    initializeEventListeners() {
        const favoriteBtn = document.getElementById('favorite-star');
        if (favoriteBtn) {
            favoriteBtn.addEventListener('click', (e) => this.handleFavoriteClick(e));
        }
    }

    async handleFavoriteClick(event) {
        event.preventDefault();
        const btn = event.currentTarget;
        const url = btn.dataset.url;
        const pageTitle = document.title || btn.dataset.title || '';

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

            const checkData = await checkResponse.json();

            if (checkResponse.ok) {
                if (checkData.is_favorited) {
                    // Was not favorited, now is - show modal to get title
                    this.showAddModal(url, pageTitle);
                } else {
                    // Was favorited, now removed
                    btn.textContent = '☆';
                    this.showToast(checkData.message);
                }
            } else {
                this.showToast(checkData.error || 'An error occurred', 'error');
                btn.textContent = originalText;
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Network error occurred', 'error');
            btn.textContent = originalText;
        } finally {
            btn.disabled = false;
        }
    }

    showAddModal(url, title) {
        const modalHtml = `
            <div class="modal-header">
                <h5 class="modal-title">${this.translate('Add to Favorites')}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="${this.translate('Close')}"></button>
            </div>
            <div class="modal-body">
                <form id="add-favorite-form">
                    <div class="mb-3">
                        <label for="favorite-title" class="form-label">${this.translate('Title')}</label>
                        <input type="text" class="form-control" id="favorite-title" name="title" value="${this.escapeHtml(title)}" required>
                    </div>
                    <div class="mb-3">
                        <label for="favorite-url" class="form-label">${this.translate('URL')}</label>
                        <input type="text" class="form-control" id="favorite-url" name="url" value="${this.escapeHtml(url)}" readonly>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${this.translate('Cancel')}</button>
                <button type="button" class="btn btn-primary" id="save-favorite">${this.translate('Save')}</button>
            </div>
        `;

        const modalContent = document.getElementById('favoritesModalContent');
        modalContent.innerHTML = modalHtml;

        const modal = new bootstrap.Modal(document.getElementById('favoritesModal'));
        modal.show();

        // Handle save
        document.getElementById('save-favorite').addEventListener('click', async () => {
            const titleInput = document.getElementById('favorite-title');
            if (titleInput.value.trim()) {
                // Update the favorite with the title
                await this.updateFavoriteTitle(url, titleInput.value.trim());
                modal.hide();
            }
        });

        // Handle modal close without save - revert the favorite
        let saved = false;
        document.getElementById('save-favorite').addEventListener('click', () => {
            saved = true;
        });

        modal._element.addEventListener('hidden.bs.modal', async () => {
            if (!saved) {
                // User closed without saving, remove the favorite
                await this.toggleFavorite(url, '');
                const btn = document.getElementById('favorite-star');    btn.textContent = '☆';
            }
        });
    }

    async updateFavoriteTitle(url, title) {
        try {
            // First remove the empty one
            await this.toggleFavorite(url, '');
            // Then add with proper title
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
            const btn = document.getElementById('favorite-star');
            if (data.is_favorited) {
                btn.textContent = '★';
                this.showToast(this.translate('Added to favorites'));
            }
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
            const btn = document.getElementById('favorite-star');
            if (data.is_favorited) {
                btn.textContent = '★';
            } else {
                btn.textContent = '☆';
            }
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
        // This would ideally use Django's translation system
        // For now, return the text as-is (English)
        return text;
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
