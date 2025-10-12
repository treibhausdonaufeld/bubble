import { Button } from '@/components/ui/button';
import { getCSRFToken } from '@/lib/utils';
import { client } from '@/services/django/client.gen';

interface LoginWithSocialButtonProps {
  name: string;
  id: string;
}

export default function LoginWithSocialButton({ name, id }: LoginWithSocialButtonProps) {
  function handleClick() {
    const form = document.createElement('form');
    form.style.display = 'none';
    form.method = 'POST';
    form.action = `${client.getConfig().baseUrl}/api/_allauth/browser/v1/auth/provider/redirect`;
    const data = {
      provider: id,
      callback_url: `${window.location.origin}/`,
      csrfmiddlewaretoken: getCSRFToken() || '',
      process: 'login',
    };

    Object.entries(data).forEach(([k, v]) => {
      const input = document.createElement('input');
      input.name = k;
      input.value = v;
      form.appendChild(input);
    });
    document.body.appendChild(form);
    form.submit();
  }
  return <Button onClick={handleClick}>Login with {name}</Button>;
}
