document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const kullaniciAdi = document.getElementById('kullaniciAdi').value;
            const sifre = document.getElementById('sifre').value;
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ kullanici_adi: kullaniciAdi, sifre: sifre })
                });
                const result = await response.json();
                if (response.ok) {
                    localStorage.setItem('isAuthenticated', 'true');
                    localStorage.setItem('kullanici_adi', result.kullanici_adi);
                    window.location.href = '/dashboard'; 
                } else {
                    alert(`Hata: ${result.detail}`);
                }
            } catch (error) {
                alert('Giriş yapılırken bir hata oluştu. Lütfen tekrar deneyin.');
            }
        });
    }
    if (window.location.pathname === '/dashboard') {
        const isAuthenticated = localStorage.getItem('isAuthenticated');
        if (!isAuthenticated) {
            window.location.href = '/'; 
            return;
        }
        document.querySelectorAll('[data-sayfa]').forEach(link => {
            link.addEventListener('click', (olay) => {
                olay.preventDefault();
                const sayfaAdi = olay.target.getAttribute('data-sayfa');
                sayfaYukle(sayfaAdi);
            });
        });
        async function sayfaYukle(sayfaAdi) {
            const anaIcerikDiv = document.getElementById('ana-icerik');
            anaIcerikDiv.innerHTML = '<div style="text-align: center; padding: 20px;">Yükleniyor...</div>';
            try {
                const response = await fetch(`${sayfaAdi}.html`);
                if (!response.ok) {
                    anaIcerikDiv.innerHTML = `<div style="text-align: center; padding: 20px;">Sayfa bulunamadı: ${sayfaAdi}.html</div>`;
                    return;
                }
                const htmlContent = await response.text();
                anaIcerikDiv.innerHTML = htmlContent;
                const scripts = anaIcerikDiv.querySelectorAll('script');
                scripts.forEach(script => {
                    const newScript = document.createElement('script');
                    newScript.textContent = script.textContent;
                    document.body.appendChild(newScript).parentNode.removeChild(newScript);
                });
            } catch (error) {
                anaIcerikDiv.innerHTML = `<div style="text-align: center; padding: 20px;">Sayfa yüklenirken bir hata oluştu: ${error.message}</div>`;
            }
        }
        sayfaYukle('anasayfa');
        function updateDateTime() {
            const now = new Date();
            const date = `${now.getDate().toString().padStart(2, '0')}.${(now.getMonth() + 1).toString().padStart(2, '0')}.${now.getFullYear()}`;
            const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
            const dateTimeElement = document.getElementById('currentDateTime');
            if (dateTimeElement) {
                dateTimeElement.innerText = `${date} ${time}`;
            }
        }
        updateDateTime();
        setInterval(updateDateTime, 1000);
        function loadCurrencyRates() {
            fetch('/api/doviz-kurlari').then(res => res.json()).then(data => {
                const ratesDiv = document.getElementById('currencyRates');
                if (ratesDiv) {
                    ratesDiv.innerHTML = `<span class="usd"><i class="fas fa-dollar-sign"></i> ${data.USD}</span><span class="eur"><i class="fas fa-euro-sign"></i> ${data.EUR}</span>`;
                }
            }).catch(error => console.error('Döviz kurları yüklenemedi:', error));
        }
        loadCurrencyRates();
        setInterval(loadCurrencyRates, 3600000);
        const logoutBtn = document.createElement('a');
        logoutBtn.href = '#';
        logoutBtn.classList.add('btn-primary');
        logoutBtn.innerText = 'Çıkış Yap';
        logoutBtn.style.textDecoration = 'none';
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.href = '/';
        });
        document.querySelector('.nav-right').appendChild(logoutBtn);
    }
    // Hamburger menü JavaScript'i
    document.querySelector('.menu-toggle').addEventListener('click', () => {
        document.querySelector('.nav-links').classList.toggle('active');
    });
});