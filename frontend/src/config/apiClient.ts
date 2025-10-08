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
    baseUrl: import.meta.env.VITE_API_URL || window._env_?.API_URL || '',
    credentials: 'include',
  });

  // Try to add CSRF token interceptor if available
  if (client.interceptors && client.interceptors.request) {
    client.interceptors.request.use(request => {
      const csrfToken = getCookie('csrftoken');
      if (csrfToken) {
        request.headers.set('X-CSRFToken', csrfToken);
      }
      return request;
    });
  }
};
