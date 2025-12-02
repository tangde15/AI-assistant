import React from 'react';
import { createRoot } from 'react-dom/client';
import './global.css';
import Chat from './pages/Chat';

const rootEl = document.getElementById('app');
if (rootEl) {
  const root = createRoot(rootEl);
  root.render(<Chat />);
}
