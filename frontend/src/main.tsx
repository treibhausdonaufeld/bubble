import * as Sentry from '@sentry/react';

import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

declare global {
  interface Window {
    _env_?: {
      VITE_API_URL?: string;
      TRACKING_PROJECT_ID?: string;
    };
  }
}

if (window._env_?.TRACKING_PROJECT_ID) {
  Sentry.init({
    dsn: window._env_?.TRACKING_PROJECT_ID,
    // Adds request headers and IP for users, for more info visit:
    // https://docs.sentry.io/platforms/javascript/guides/react/configuration/options/#sendDefaultPii
    sendDefaultPii: true,
  });
}

const container = document.getElementById('root')!;
createRoot(container, {
  // Callback called when an error is thrown and not caught by an ErrorBoundary.
  onUncaughtError: Sentry.reactErrorHandler((error, errorInfo) => {
    console.warn('Uncaught error', error, errorInfo.componentStack);
  }),
  // Callback called when React catches an error in an ErrorBoundary.
  onCaughtError: Sentry.reactErrorHandler(),
  // Callback called when React automatically recovers from errors.
  onRecoverableError: Sentry.reactErrorHandler(),
}).render(<App />);
