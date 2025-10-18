import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

import { ErrorBoundary } from '@highlight-run/react';

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
);
