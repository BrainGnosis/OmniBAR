import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';
import './index.css';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found');
}

const root = ReactDOM.createRoot(rootElement);

async function renderApp() {
  const shouldEnableMsw = import.meta.env.DEV && import.meta.env.VITE_ENABLE_MSW === 'true';

  if (shouldEnableMsw) {
    const { worker } = await import('./mocks/browser');
    await worker.start({ onUnhandledRequest: 'bypass' });
  }

  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

renderApp();
