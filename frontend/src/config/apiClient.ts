import { client } from '@/services/django/client.gen';

// Helper function to get CSRF token from cookie
function getCookie(name: string): string | null {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Configure the API client
export const configureApiClient = () => {
  client.setConfig({
    baseUrl: import.meta.env.VITE_API_URL || window._env_?.VITE_API_URL || '',
    credentials: 'include',
  });

  if (import.meta.env.DEV) {
    console.log('API Client configured with baseUrl:', client.getConfig().baseUrl);
  }

  // Try to add CSRF token interceptor if available
  if (client.interceptors && client.interceptors.request) {
    client.interceptors.request.use(request => {
      const csrfToken = getCookie('csrftoken');
      if (csrfToken) {
        request.headers.set('X-CSRFToken', csrfToken);
      }
      // Always send current language
      const lang = localStorage.getItem('bubble-language') || 'en';
      request.headers.set('Accept-Language', lang);
      return request;
    });
  }
};
