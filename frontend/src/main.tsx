import React from 'react';
import ReactDOM from 'react-dom/client';
import WebApp from '@twa-dev/sdk';
import { App } from './App';
import './styles/global.css';

// Initialize Telegram WebApp
WebApp.ready();
WebApp.expand();

// Theme CSS variables
const tp = WebApp.themeParams;
const root = document.documentElement;
root.style.setProperty('--tg-bg', tp.bg_color ?? '#ffffff');
root.style.setProperty('--tg-text', tp.text_color ?? '#000000');
root.style.setProperty('--tg-hint', tp.hint_color ?? '#999999');
root.style.setProperty('--tg-link', tp.link_color ?? '#2481cc');
root.style.setProperty('--tg-btn', tp.button_color ?? '#4CAF50');
root.style.setProperty('--tg-btn-text', tp.button_text_color ?? '#ffffff');
root.style.setProperty('--tg-secondary', tp.secondary_bg_color ?? '#f1f1f1');

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
