// The Tally sample app (recipe pwa-offline): one button, and a service worker that keeps the app working offline.
const count = document.getElementById('count');
document.getElementById('add').addEventListener('click', () => { count.textContent = String(Number(count.textContent) + 1); });
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');
