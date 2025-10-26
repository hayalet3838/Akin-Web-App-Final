// Bu olay dinleyici, uygulamanın tarayıcı tarafından "yüklenebilir"
// bir PWA (Progressive Web App) olarak algılanması için zorunludur.
self.addEventListener('fetch', (event) => {
  // Şimdilik bu kadar yeterli.
  // Gelecekte buraya çevrimdışı çalışma (caching) özellikleri eklenebilir.
});