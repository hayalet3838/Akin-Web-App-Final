# --- GEREKLİ KÜTÜPHANELERİN İÇERİ AKTARILMASI (IMPORTS) ---
import os
import time
import datetime
import requests
import xml.etree.ElementTree as ET
import psycopg2
import uvicorn
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File
import shutil
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, status, Depends, UploadFile, File, Form
import xml.etree.ElementTree as ET

# --- GÜVENLİK VE TOKEN İÇİN YENİ IMPORTLAR ---
import jwt
from datetime import timedelta
from pydantic import BaseModel
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# --- YENİ IMPORTLARIN SONU ---


# --- UYGULAMA VE TEMEL AYARLAR (SETUP) ---

# Uygulamanın bulunduğu klasörün tam yolunu alıyoruz.
BASE_DIR = Path(__file__).resolve().parent

# FastAPI uygulamasını oluşturma
app = FastAPI(title="Fabrika Yönetim Sistemi")

# Veritabanı Bağlantı Ayarları
DB_NAME = os.getenv("DB_NAME", "fabrika_pdks")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Veritabanı Bağlantı Havuzu (Connection Pool)
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
except Exception as e:
    print(f"Veritabanı bağlantı havuzu oluşturulurken hata oluştu: {e}")
    db_pool = None

# --- GÜVENLİK AYARLARI ---
SECRET_KEY = os.getenv("SECRET_KEY", "COK_GIZLI_VE_GUCLU_BIR_ANAHTAR_BURAYA_YAZILMALI")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Token 24 saat geçerli olacak

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/portal/login")
# --- GÜVENLİK AYARLARI SONU ---

# --- Pydantic Modelleri (Veri Şemaları) ---
class TokenData(BaseModel):
    kullanici_adi: Optional[str] = None

class PortalUserCreate(BaseModel):
    kullanici_adi: str
    sifre: str
    rol: str
    musteri_id: Optional[int] = None
    tedarikci_id: Optional[int] = None
    
class UretimPlanCreate(BaseModel):
    satis_id: int
    plan_adi: str
# --- Pydantic Modelleri SONU ---

# --- VERİTABANI YARDIMCI FONKSİYONLARI ---
def get_db_connection():
    global db_pool
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Veritabanı bağlantısı kurulamadı.")
    return db_pool.getconn()

def run_db_query(query, params=None, fetch="none"):
    global db_pool
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch == "one": result = cur.fetchone()
            elif fetch == "all": result = cur.fetchall()
            else: result = None
            conn.commit()
            return result
    except psycopg2.errors.ForeignKeyViolation:
        if conn: conn.rollback()
        raise HTTPException(status_code=409, detail="İlgili kayıt başka bir tabloda kullanıldığı için silinemez.")
    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        raise HTTPException(status_code=409, detail="Bu kayıt zaten mevcut (benzersizlik ihlali).")
    except Exception as e:
        if conn: conn.rollback()
        print(f"Veritabanı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Bir sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)

# --- GÜVENLİK YARDIMCI FONKSİYONLARI ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": True})
        kullanici_adi: str = payload.get("sub")
        if kullanici_adi is None:
            raise credentials_exception
        token_data = TokenData(kullanici_adi=kullanici_adi)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = run_db_query(
        "SELECT id, kullanici_adi, rol, musteri_id, tedarikci_id FROM portal_kullanicilari WHERE kullanici_adi = %s", 
        params=(token_data.kullanici_adi,), 
        fetch="one"
    )
    if user is None:
        raise credentials_exception
    return user
# --- GÜVENLİK YARDIMCI FONKSİYONLARI SONU ---

# =================================================================
# --- PWA, STATİK DOSYALAR ve HTML SAYFA SUNUMU ---
# =================================================================
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/sw.js", include_in_schema=False)
async def get_service_worker():
    return FileResponse(os.path.join(BASE_DIR, "static", "sw.js"))

# --- HTML Sayfa Yönlendirmeleri ---
@app.get("/", include_in_schema=False)
def anasayfa(): return FileResponse(os.path.join(BASE_DIR, "templates", "anasayfa.html"))
@app.get("/stok", include_in_schema=False)
def stok_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "stok.html"))
@app.get("/uretim", include_in_schema=False)
def uretim_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "uretim.html"))
@app.get("/recete", include_in_schema=False)
def recete_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "recete.html"))
@app.get("/satis", include_in_schema=False)
def satis_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "satis.html"))
@app.get("/cari", include_in_schema=False)
def cari_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "cari.html"))
@app.get("/personel", include_in_schema=False)
def personel_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "personel.html"))
@app.get("/maas", include_in_schema=False)
def maas_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "maas.html"))
@app.get("/raporlama", include_in_schema=False)
def raporlama_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "raporlama.html"))
@app.get("/ayarlar", include_in_schema=False)
def ayarlar_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "ayarlar.html"))
@app.get("/pdks", include_in_schema=False)
def pdks_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "pdks.html"))
@app.get("/vardiya", include_in_schema=False)
def vardiya_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "vardiya.html"))
@app.get("/siparis-detaylari", include_in_schema=False)
def siparis_detaylari_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "siparis_detaylari.html"))
@app.get("/enerji", include_in_schema=False)
def enerji_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "enerji.html"))
@app.get("/hesap-makinasi", include_in_schema=False)
def hesap_makinasi_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "hesap_makinasi.html"))
@app.get("/crm", include_in_schema=False)
def crm_yonetim_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "crm_yonetimi.html"))
@app.get("/finans", include_in_schema=False)
def finans_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "cari_finans_yonetimi.html"))
@app.get("/gelir-gider", include_in_schema=False)
def gelir_gider_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "gelir_gider_yonetimi.html"))
@app.get("/izlenebilirlik", include_in_schema=False)
def izlenebilirlik_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "izlenebilirlik.html"))
@app.get("/kaliplar", include_in_schema=False)
def kaliplar_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "kaliplar.html"))
@app.get("/kalite-kontrol", include_in_schema=False)
def kalite_kontrol_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "kalite_kontrol.html"))
@app.get("/dashboard", include_in_schema=False)
def read_dashboard_shell(): return FileResponse(os.path.join(BASE_DIR, "templates", "dashboard.html"))
@app.get("/planlama", include_in_schema=False)
def planlama_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "planlama.html"))
@app.get("/satin-alma", include_in_schema=False)
def satin_alma_sayfasi(): return FileResponse(os.path.join(BASE_DIR, "templates", "satin_alma.html"))
@app.get("/portal/login", include_in_schema=False)
def portal_login_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "portal_login.html"))
@app.get("/portal/dashboard", include_in_schema=False)
def portal_dashboard_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "musteri_dashboard.html"))
@app.get("/portal/supplier-dashboard", include_in_schema=False)
def portal_supplier_dashboard_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "tedarikci_dashboard.html"))
@app.get("/gelen-fatura-ekle", include_in_schema=False)
def gelen_fatura_ekle_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "gelen_fatura_ekle.html"))
@app.get("/sevkiyat", include_in_schema=False)
def sevkiyat_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "sevkiyat.html"))
@app.get("/gelen-faturalar", include_in_schema=False)
def gelen_faturalar_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "gelen_faturalar.html"))
@app.get("/fis-yazdir/{siparis_id}", include_in_schema=False)
def fis_yazdir_sayfasi(siparis_id: int):
    return FileResponse(os.path.join(BASE_DIR, "templates", "fis_yazdir.html"))
@app.get("/satis-fisleri", include_in_schema=False)
def satis_fisleri_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "satis_fisleri_listesi.html"))
@app.get("/yonetici-dashboard", include_in_schema=False)
def yonetici_dashboard_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "yonetici_dashboard.html"))
@app.get("/personel/{personel_id}", include_in_schema=False)
def personel_detay_sayfasi(personel_id: int):
    return FileResponse(os.path.join(BASE_DIR, "templates", "personel_detay.html"))
@app.get("/sevkiyat/{sevkiyat_id}/detay", include_in_schema=False)
def sevkiyat_detay_sayfasi(sevkiyat_id: int):
    return FileResponse(os.path.join(BASE_DIR, "templates", "siparis_detaylari.html"))

@app.get("/gelen-fatura-detay/{fatura_id}", include_in_schema=False)
def gelen_fatura_detay_sayfasi(fatura_id: int):
    return FileResponse(os.path.join(BASE_DIR, "templates", "gelen_fatura_detay.html"))

@app.get("/teklifler", include_in_schema=False)
def teklifler_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "teklifler.html"))

@app.get("/teklif-olustur", include_in_schema=False)
def teklif_olustur_sayfasi():
    return FileResponse(os.path.join(BASE_DIR, "templates", "teklif_olustur.html"))

@app.get("/teklif-detay/{teklif_id}", include_in_schema=False)
def teklif_detay_sayfasi(teklif_id: int):
    return FileResponse(os.path.join(BASE_DIR, "templates", "teklif_detay.html"))

# =================================================================
# --- API ENDPOINTS ---
# =================================================================

# --- API: Dashboard & Genel ---
@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    aktif_uretim = run_db_query("SELECT COUNT(id) as sayi FROM uretim_emirleri WHERE durum='Üretimde'", fetch="one")
    kritik_stok = run_db_query("SELECT COUNT(id) as sayi FROM hammaddeler WHERE stok_miktari <= kritik_stok_seviyesi", fetch="one")
    bekleyen_siparis = run_db_query("SELECT COUNT(id) as sayi FROM satis_siparisleri WHERE durum='Alindi' OR durum='Onaylandı'", fetch="one")
    return {
        "aktif_uretim_emri_sayisi": aktif_uretim['sayi'] if aktif_uretim else 0, 
        "bugunku_uretim_adeti": 0,  # Bu özellik henüz implemente edilmedi
        "kritik_stok_uyarisi_sayisi": kritik_stok['sayi'] if kritik_stok else 0, 
        "bekleyen_satis_siparis_sayisi": bekleyen_siparis['sayi'] if bekleyen_siparis else 0
    }

@app.get("/api/dashboard/executive-summary")
def get_executive_summary():
    try:
        ciro_query = "SELECT COALESCE(SUM(genel_toplam), 0) as toplam FROM satis_siparisleri WHERE EXTRACT(YEAR FROM siparis_tarihi) = EXTRACT(YEAR FROM CURRENT_DATE) AND EXTRACT(MONTH FROM siparis_tarihi) = EXTRACT(MONTH FROM CURRENT_DATE);"
        ciro_result = run_db_query(ciro_query, fetch="one")
        gider_query = "SELECT COALESCE(SUM(miktar), 0) as toplam FROM finansal_islemler WHERE islem_tipi = 'gider' AND EXTRACT(YEAR FROM islem_tarihi) = EXTRACT(YEAR FROM CURRENT_DATE) AND EXTRACT(MONTH FROM islem_tarihi) = EXTRACT(MONTH FROM CURRENT_DATE);"
        gider_result = run_db_query(gider_query, fetch="one")
        bakiye_query = "SELECT COALESCE(SUM(CASE WHEN islem_tipi = 'gelir' THEN miktar ELSE -miktar END), 0) as toplam FROM finansal_islemler;"
        bakiye_result = run_db_query(bakiye_query, fetch="one")
        aktif_uretim_result = run_db_query("SELECT COUNT(id) as sayi FROM uretim_emirleri WHERE durum = 'Üretimde'", fetch="one")
        bekleyen_siparis_result = run_db_query("SELECT COUNT(id) as sayi FROM satis_siparisleri WHERE durum = 'Alindi' OR durum = 'Onaylandı'", fetch="one")
        toplam_musteri_result = run_db_query("SELECT COUNT(id) as sayi FROM musteriler", fetch="one")
        summary = {
            "aylik_ciro": ciro_result['toplam'] if ciro_result else 0, 
            "aylik_gider": gider_result['toplam'] if gider_result else 0, 
            "toplam_bakiye": bakiye_result['toplam'] if bakiye_result else 0, 
            "aktif_uretim_sayisi": aktif_uretim_result['sayi'] if aktif_uretim_result else 0, 
            "bekleyen_siparis_sayisi": bekleyen_siparis_result['sayi'] if bekleyen_siparis_result else 0, 
            "toplam_musteri_sayisi": toplam_musteri_result['sayi'] if toplam_musteri_result else 0
        }
        return summary
    except Exception as e:
        print(f"Yönetici paneli özeti alınırken hata: {e}")
        raise HTTPException(status_code=500, detail="Yönetici paneli verileri alınırken bir hata oluştu.")

# --- API: Ürünler ---
@app.get("/api/urunler")
def get_urunler():
    # Bütün alanları seçiyoruz
    return run_db_query("SELECT * FROM urunler ORDER BY id;", fetch="all")

@app.post("/api/urunler", status_code=status.HTTP_201_CREATED)
async def create_urun(request: Request):
    data = await request.json()
    # INSERT sorgusuna birim_fiyat eklendi
    run_db_query(
        "INSERT INTO urunler (urun_kodu, urun_adi, stok_miktari, birim_fiyat) VALUES (%(urun_kodu)s, %(urun_adi)s, %(stok_miktari)s, %(birim_fiyat)s);", 
        params=data
    )
    return {"message": "Ürün başarıyla eklendi."}

@app.put("/api/urunler/{urun_id}")
async def update_urun(urun_id: int, request: Request):
    data = await request.json()
    data['id'] = urun_id
    # UPDATE sorgusuna birim_fiyat eklendi
    result = run_db_query(
        "UPDATE urunler SET urun_kodu=%(urun_kodu)s, urun_adi=%(urun_adi)s, stok_miktari=%(stok_miktari)s, birim_fiyat=%(birim_fiyat)s WHERE id=%(id)s RETURNING id;", 
        params=data, 
        fetch="one"
    )
    if result is None: raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    return {"message": "Ürün başarıyla güncellendi."}

@app.delete("/api/urunler/{urun_id}")
def delete_urun(urun_id: int):
    result = run_db_query("DELETE FROM urunler WHERE id=%s RETURNING id;", params=(urun_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    return {"message": "Ürün başarıyla silindi."}

# --- API: Hammaddeler ---
@app.get("/api/hammaddeler")
def get_hammaddeler():
    return run_db_query("SELECT * FROM hammaddeler ORDER BY id;", fetch="all")
@app.post("/api/hammaddeler", status_code=status.HTTP_201_CREATED)
async def create_hammadde(request: Request):
    data = await request.json()
    run_db_query("INSERT INTO hammaddeler (hammadde_kodu, hammadde_adi, stok_miktari, birim, kritik_stok_seviyesi) VALUES (%(hammadde_kodu)s, %(hammadde_adi)s, %(stok_miktari)s, %(birim)s, %(kritik_stok_seviyesi)s);", params=data)
    return {"message": "Hammadde başarıyla eklendi."}
@app.put("/api/hammaddeler/{hammadde_id}")
async def update_hammadde(hammadde_id: int, request: Request):
    data = await request.json()
    data['id'] = hammadde_id
    result = run_db_query("UPDATE hammaddeler SET hammadde_kodu=%(hammadde_kodu)s, hammadde_adi=%(hammadde_adi)s, stok_miktari=%(stok_miktari)s, birim=%(birim)s, kritik_stok_seviyesi=%(kritik_stok_seviyesi)s WHERE id=%(id)s RETURNING id;", params=data, fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Hammadde bulunamadı.")
    return {"message": "Hammadde başarıyla güncellendi."}
@app.delete("/api/hammaddeler/{hammadde_id}")
def delete_hammadde(hammadde_id: int):
    result = run_db_query("DELETE FROM hammaddeler WHERE id = %s RETURNING id;", params=(hammadde_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Hammadde bulunamadı.")
    return {"message": "Hammadde başarıyla silindi."}

# --- API: Reçeteler ---
@app.get("/api/receteler/{urun_id}")
def get_receteler_by_urun_id(urun_id: int):
    sorgu = "SELECT r.id, COALESCE(u.urun_adi, 'SİLİNMİŞ ÜRÜN') as urun_adi, COALESCE(h.hammadde_adi, 'SİLİNMİŞ HAMMADDE') as hammadde_adi, r.miktar, h.birim FROM urun_receteleri r LEFT JOIN urunler u ON r.urun_id = u.id LEFT JOIN hammaddeler h ON r.hammadde_id = h.id WHERE r.urun_id = %s ORDER BY r.id;"
    return run_db_query(sorgu, params=(urun_id,), fetch="all")
@app.get("/api/receteler")
def get_all_receteler():
    sorgu = "SELECT r.id, COALESCE(u.urun_adi, 'SİLİNMİŞ ÜRÜN') as urun_adi, COALESCE(h.hammadde_adi, 'SİLİNMİŞ HAMMADDE') as hammadde_adi, r.miktar, h.birim FROM urun_receteleri r LEFT JOIN urunler u ON r.urun_id = u.id LEFT JOIN hammaddeler h ON r.hammadde_id = h.id ORDER BY r.id;"
    return run_db_query(sorgu, fetch="all")
@app.post("/api/receteler", status_code=status.HTTP_201_CREATED)
async def create_recete(request: Request):
    data = await request.json()
    run_db_query("INSERT INTO urun_receteleri (urun_id, hammadde_id, miktar) VALUES (%(urun_id)s, %(hammadde_id)s, %(miktar)s);", params=data)
    return {"message": "Reçete başarıyla eklendi."}
@app.delete("/api/receteler/{recete_id}")
def delete_recete(recete_id: int):
    result = run_db_query("DELETE FROM urun_receteleri WHERE id = %s RETURNING id;", params=(recete_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Reçete bulunamadı.")
    return {"message": "Reçete başarıyla silindi."}

# --- API: Makineler ---
@app.get("/api/makineler")
def get_makineler():
    return run_db_query("SELECT * FROM makineler ORDER BY makine_adi;", fetch="all")
@app.post("/api/makineler", status_code=status.HTTP_201_CREATED)
async def create_makine(request: Request):
    data = await request.json()
    makine_adi = data.get('makine_adi')
    if not makine_adi:
        raise HTTPException(status_code=400, detail="Makine adı zorunludur.")
    run_db_query("INSERT INTO makineler (makine_adi) VALUES (%s);", params=(makine_adi,))
    return {"message": "Makine başarıyla eklendi."}
@app.put("/api/makineler/{makine_id}")
async def update_makine(makine_id: int, request: Request):
    data = await request.json()
    makine_adi = data.get('makine_adi')
    if not makine_adi:
        raise HTTPException(status_code=400, detail="Makine adı zorunludur.")
    result = run_db_query("UPDATE makineler SET makine_adi = %s WHERE id = %s RETURNING id;", params=(makine_adi, makine_id), fetch="one")
    if result is None:
        raise HTTPException(status_code=404, detail="Makine bulunamadı.")
    return {"message": "Makine başarıyla güncellendi."}
@app.delete("/api/makineler/{makine_id}")
def delete_makine(makine_id: int):
    kullanim = run_db_query("SELECT id FROM uretim_emirleri WHERE atanan_makine_id = %s LIMIT 1;", params=(makine_id,), fetch="one")
    if kullanim:
        raise HTTPException(status_code=409, detail="Bu makine bir üretim emrine atandığı için silinemez.")
    result = run_db_query("DELETE FROM makineler WHERE id = %s RETURNING id;", params=(makine_id,), fetch="one")
    if result is None:
        raise HTTPException(status_code=404, detail="Makine bulunamadı.")
    return {"message": "Makine başarıyla silindi."}

# --- API: Üretim Emirleri ---
# --- API: Üretim Emirleri ---

@app.get("/api/uretim-emirleri")
def get_uretim_emirleri():
    sorgu = """
    SELECT 
        ue.id, ue.is_emri_kodu, ue.urun_id,
        COALESCE(u.urun_adi, 'Bilinmeyen Ürün') as urun_adi, 
        ue.hedef_miktar, ue.uretilen_miktar, ue.durum,
        COALESCE(m.makine_adi, 'Atanmadı') as makine_adi,
        ue.olusturma_tarihi
    FROM uretim_emirleri ue
    LEFT JOIN urunler u ON ue.urun_id = u.id
    LEFT JOIN makineler m ON ue.atanan_makine_id = m.id
    WHERE ue.arsivlendi IS NOT TRUE
    ORDER BY ue.olusturma_tarihi DESC;
    """
    return run_db_query(sorgu, fetch="all")

@app.post("/api/uretim-emirleri", status_code=status.HTTP_201_CREATED)
async def create_uretim_emri(request: Request):
    data = await request.json()
    if not all(k in data for k in ['is_emri_kodu', 'urun_id', 'hedef_miktar']):
        raise HTTPException(status_code=400, detail="İş emri kodu, ürün ve hedef miktar zorunludur.")
    
    # atanan_makine_id'nin None olabileceğini kontrol et
    atanan_makine_id = data.get('atanan_makine_id')
    if isinstance(atanan_makine_id, str) and not atanan_makine_id.strip():
        atanan_makine_id = None
        
    params = {
        'is_emri_kodu': data['is_emri_kodu'],
        'urun_id': data['urun_id'],
        'hedef_miktar': data['hedef_miktar'],
        'atanan_makine_id': atanan_makine_id
    }
    sorgu = "INSERT INTO uretim_emirleri (is_emri_kodu, urun_id, hedef_miktar, durum, atanan_makine_id) VALUES (%(is_emri_kodu)s, %(urun_id)s, %(hedef_miktar)s, 'Bekliyor', %(atanan_makine_id)s);"
    run_db_query(sorgu, params=params)
    return {"message": "Üretim emri başarıyla oluşturuldu."}

@app.put("/api/uretim-emirleri/{emir_id}/baslat")
def start_uretim_emri(emir_id: int):
    sorgu = "UPDATE uretim_emirleri SET durum = 'Üretimde', baslama_tarihi = CURRENT_TIMESTAMP WHERE id = %s AND durum = 'Bekliyor' RETURNING id;"
    result = run_db_query(sorgu, params=(emir_id,), fetch="one")
    if result is None:
        raise HTTPException(status_code=404, detail="Üretim emri bulunamadı veya zaten başlatılmış.")
    return {"message": "Üretim emri başarıyla başlatıldı."}

@app.put("/api/uretim-emirleri/{emir_id}/tamamla")
async def tamamla_uretim_emri(emir_id: int, request: Request):
    data = await request.json()
    uretilen_miktar = data.get('uretilen_miktar')
    urun_id = data.get('urun_id')
    
    if not uretilen_miktar or not urun_id:
        raise HTTPException(status_code=400, detail="Üretilen miktar ve ürün ID'si zorunludur.")
    
    try:
        uretilen_miktar_float = float(uretilen_miktar)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Üretilen miktar geçerli bir sayı olmalıdır.")

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("UPDATE uretim_emirleri SET durum = 'Tamamlandı', bitis_tarihi = CURRENT_TIMESTAMP, uretilen_miktar = %s WHERE id = %s RETURNING id;", (uretilen_miktar_float, emir_id))
            if cur.rowcount == 0: 
                raise HTTPException(status_code=404, detail="Üretim emri bulunamadı veya tamamlanmaya uygun değil.")
            
            cur.execute("UPDATE urunler SET stok_miktari = stok_miktari + %s WHERE id = %s;", (uretilen_miktar_float, urun_id))
            
            cur.execute("SELECT hammadde_id, miktar FROM urun_receteleri WHERE urun_id = %s;", (urun_id,))
            recete_listesi = cur.fetchall()
            
            if recete_listesi:
                for recete_item in recete_listesi:
                    hammadde_id = recete_item['hammadde_id']
                    toplam_gereken_miktar = float(recete_item['miktar']) * uretilen_miktar_float
                    
                    cur.execute("SELECT COALESCE(SUM(kalan_miktar), 0) as toplam FROM hammadde_girisleri WHERE hammadde_id = %s AND kalan_miktar > 0;", (hammadde_id,))
                    lotlarda_bulunan_toplam = cur.fetchone()['toplam']

                    if toplam_gereken_miktar > lotlarda_bulunan_toplam:
                        conn.rollback()
                        raise HTTPException(status_code=409, detail=f"Hammadde ID {hammadde_id} için yeterli lot stoğu bulunmuyor! Gereken: {toplam_gereken_miktar:.4f}, Lotlarda bulunan: {lotlarda_bulunan_toplam:.4f}")

                    cur.execute("SELECT id, kalan_miktar FROM hammadde_girisleri WHERE hammadde_id = %s AND kalan_miktar > 0 ORDER BY giris_tarihi ASC;", (hammadde_id,))
                    kullanilabilir_lotlar = cur.fetchall()
                    dusulecek_miktar = toplam_gereken_miktar

                    for lot in kullanilabilir_lotlar:
                        if dusulecek_miktar <= 0: break
                        lot_id, lottaki_miktar = lot['id'], lot['kalan_miktar']
                        kullanilan_bu_lottan = min(dusulecek_miktar, lottaki_miktar)
                        cur.execute("UPDATE hammadde_girisleri SET kalan_miktar = kalan_miktar - %s WHERE id = %s;", (kullanilan_bu_lottan, lot_id))
                        cur.execute("INSERT INTO uretim_lot_kullanimi (uretim_emri_id, hammadde_giris_id, kullanilan_miktar) VALUES (%s, %s, %s);", (emir_id, lot_id, kullanilan_bu_lottan))
                        dusulecek_miktar -= kullanilan_bu_lottan
                    
                    cur.execute("UPDATE hammaddeler SET stok_miktari = stok_miktari - %s WHERE id = %s;", (toplam_gereken_miktar, hammadde_id))

            # Tamamlanan emri arşivle
            cur.execute("UPDATE uretim_emirleri SET arsivlendi = TRUE WHERE id = %s;", (emir_id,))

            conn.commit()
            return {"message": "Üretim emri başarıyla tamamlandı, stoklar güncellendi ve emir arşivlendi."}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Üretim tamamlama hatası: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Tamamlama işlemi başarısız. Sunucu hatası: {str(e)}")
    finally:
        if conn: db_pool.putconn(conn)

@app.delete("/api/uretim-emirleri/{emir_id}")
def delete_uretim_emri(emir_id: int):
    # Bu fonksiyon aslında silme değil, arşivleme yapıyor.
    emir = run_db_query("SELECT durum FROM uretim_emirleri WHERE id = %s", params=(emir_id,), fetch="one")
    if not emir: 
        raise HTTPException(status_code=404, detail="Üretim emri bulunamadı.")
    
    if emir['durum'] == 'Üretimde': 
        raise HTTPException(status_code=409, detail=f"'Üretimde' durumundaki üretim emirleri arşivlenemez.")
    
    result = run_db_query("UPDATE uretim_emirleri SET arsivlendi = TRUE WHERE id = %s RETURNING id;", params=(emir_id,), fetch="one")
    
    if result is None: 
        raise HTTPException(status_code=404, detail="Arşivleme sırasında bir sorun oluştu.")
        
    return {"message": "Üretim emri başarıyla arşivlendi."}# --- API: Üretim Emirleri ---

@app.get("/api/uretim-emirleri")
def get_uretim_emirleri():
    sorgu = """
    SELECT 
        ue.id, ue.is_emri_kodu, ue.urun_id,
        COALESCE(u.urun_adi, 'Bilinmeyen Ürün') as urun_adi, 
        ue.hedef_miktar, ue.uretilen_miktar, ue.durum,
        COALESCE(m.makine_adi, 'Atanmadı') as makine_adi,
        ue.olusturma_tarihi
    FROM uretim_emirleri ue
    LEFT JOIN urunler u ON ue.urun_id = u.id
    LEFT JOIN makineler m ON ue.atanan_makine_id = m.id
    WHERE ue.arsivlendi IS NOT TRUE
    ORDER BY ue.olusturma_tarihi DESC;
    """
    return run_db_query(sorgu, fetch="all")

@app.post("/api/uretim-emirleri", status_code=status.HTTP_201_CREATED)
async def create_uretim_emri(request: Request):
    data = await request.json()
    if not all(k in data for k in ['is_emri_kodu', 'urun_id', 'hedef_miktar']):
        raise HTTPException(status_code=400, detail="İş emri kodu, ürün ve hedef miktar zorunludur.")
    
    # atanan_makine_id'nin None olabileceğini kontrol et
    atanan_makine_id = data.get('atanan_makine_id')
    if isinstance(atanan_makine_id, str) and not atanan_makine_id.strip():
        atanan_makine_id = None
        
    params = {
        'is_emri_kodu': data['is_emri_kodu'],
        'urun_id': data['urun_id'],
        'hedef_miktar': data['hedef_miktar'],
        'atanan_makine_id': atanan_makine_id
    }
    sorgu = "INSERT INTO uretim_emirleri (is_emri_kodu, urun_id, hedef_miktar, durum, atanan_makine_id) VALUES (%(is_emri_kodu)s, %(urun_id)s, %(hedef_miktar)s, 'Bekliyor', %(atanan_makine_id)s);"
    run_db_query(sorgu, params=params)
    return {"message": "Üretim emri başarıyla oluşturuldu."}

@app.put("/api/uretim-emirleri/{emir_id}/baslat")
def start_uretim_emri(emir_id: int):
    sorgu = "UPDATE uretim_emirleri SET durum = 'Üretimde', baslama_tarihi = CURRENT_TIMESTAMP WHERE id = %s AND durum = 'Bekliyor' RETURNING id;"
    result = run_db_query(sorgu, params=(emir_id,), fetch="one")
    if result is None:
        raise HTTPException(status_code=404, detail="Üretim emri bulunamadı veya zaten başlatılmış.")
    return {"message": "Üretim emri başarıyla başlatıldı."}

@app.put("/api/uretim-emirleri/{emir_id}/tamamla")
async def tamamla_uretim_emri(emir_id: int, request: Request):
    data = await request.json()
    uretilen_miktar = data.get('uretilen_miktar')
    urun_id = data.get('urun_id')
    
    if not uretilen_miktar or not urun_id:
        raise HTTPException(status_code=400, detail="Üretilen miktar ve ürün ID'si zorunludur.")
    
    try:
        uretilen_miktar_float = float(uretilen_miktar)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Üretilen miktar geçerli bir sayı olmalıdır.")

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("UPDATE uretim_emirleri SET durum = 'Tamamlandı', bitis_tarihi = CURRENT_TIMESTAMP, uretilen_miktar = %s WHERE id = %s RETURNING id;", (uretilen_miktar_float, emir_id))
            if cur.rowcount == 0: 
                raise HTTPException(status_code=404, detail="Üretim emri bulunamadı veya tamamlanmaya uygun değil.")
            
            cur.execute("UPDATE urunler SET stok_miktari = stok_miktari + %s WHERE id = %s;", (uretilen_miktar_float, urun_id))
            
            cur.execute("SELECT hammadde_id, miktar FROM urun_receteleri WHERE urun_id = %s;", (urun_id,))
            recete_listesi = cur.fetchall()
            
            if recete_listesi:
                for recete_item in recete_listesi:
                    hammadde_id = recete_item['hammadde_id']
                    toplam_gereken_miktar = float(recete_item['miktar']) * uretilen_miktar_float
                    
                    cur.execute("SELECT COALESCE(SUM(kalan_miktar), 0) as toplam FROM hammadde_girisleri WHERE hammadde_id = %s AND kalan_miktar > 0;", (hammadde_id,))
                    lotlarda_bulunan_toplam = cur.fetchone()['toplam']

                    if toplam_gereken_miktar > lotlarda_bulunan_toplam:
                        conn.rollback()
                        raise HTTPException(status_code=409, detail=f"Hammadde ID {hammadde_id} için yeterli lot stoğu bulunmuyor! Gereken: {toplam_gereken_miktar:.4f}, Lotlarda bulunan: {lotlarda_bulunan_toplam:.4f}")

                    cur.execute("SELECT id, kalan_miktar FROM hammadde_girisleri WHERE hammadde_id = %s AND kalan_miktar > 0 ORDER BY giris_tarihi ASC;", (hammadde_id,))
                    kullanilabilir_lotlar = cur.fetchall()
                    dusulecek_miktar = toplam_gereken_miktar

                    for lot in kullanilabilir_lotlar:
                        if dusulecek_miktar <= 0: break
                        lot_id, lottaki_miktar = lot['id'], lot['kalan_miktar']
                        kullanilan_bu_lottan = min(dusulecek_miktar, lottaki_miktar)
                        cur.execute("UPDATE hammadde_girisleri SET kalan_miktar = kalan_miktar - %s WHERE id = %s;", (kullanilan_bu_lottan, lot_id))
                        cur.execute("INSERT INTO uretim_lot_kullanimi (uretim_emri_id, hammadde_giris_id, kullanilan_miktar) VALUES (%s, %s, %s);", (emir_id, lot_id, kullanilan_bu_lottan))
                        dusulecek_miktar -= kullanilan_bu_lottan
                    
                    cur.execute("UPDATE hammaddeler SET stok_miktari = stok_miktari - %s WHERE id = %s;", (toplam_gereken_miktar, hammadde_id))

            # Tamamlanan emri arşivle
            cur.execute("UPDATE uretim_emirleri SET arsivlendi = TRUE WHERE id = %s;", (emir_id,))

            conn.commit()
            return {"message": "Üretim emri başarıyla tamamlandı, stoklar güncellendi ve emir arşivlendi."}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Üretim tamamlama hatası: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Tamamlama işlemi başarısız. Sunucu hatası: {str(e)}")
    finally:
        if conn: db_pool.putconn(conn)

@app.delete("/api/uretim-emirleri/{emir_id}")
def delete_uretim_emri(emir_id: int):
    # Bu fonksiyon aslında silme değil, arşivleme yapıyor.
    emir = run_db_query("SELECT durum FROM uretim_emirleri WHERE id = %s", params=(emir_id,), fetch="one")
    if not emir: 
        raise HTTPException(status_code=404, detail="Üretim emri bulunamadı.")
    
    if emir['durum'] == 'Üretimde': 
        raise HTTPException(status_code=409, detail=f"'Üretimde' durumundaki üretim emirleri arşivlenemez.")
    
    result = run_db_query("UPDATE uretim_emirleri SET arsivlendi = TRUE WHERE id = %s RETURNING id;", params=(emir_id,), fetch="one")
    
    if result is None: 
        raise HTTPException(status_code=404, detail="Arşivleme sırasında bir sorun oluştu.")
        
    return {"message": "Üretim emri başarıyla arşivlendi."}
# --- API: Satış Siparişleri & Fişleri ---


@app.get("/api/satis-fisleri/{siparis_id}")
def get_satis_fisi_detay(siparis_id: int):
    # GÜNCELLEME: Şirket ayarlarını veritabanından çekiyoruz
    sirket_ayarlari_raw = run_db_query(
        "SELECT ayar_anahtari, ayar_degeri FROM sistem_ayarlari WHERE ayar_anahtari LIKE 'firma_%'", 
        fetch="all"
    )
    # Ayarları kolay erişilebilir bir sözlüğe çeviriyoruz
    sirket_bilgileri = {ayar['ayar_anahtari']: ayar['ayar_degeri'] for ayar in sirket_ayarlari_raw}

    # Fiş bilgilerini çekiyoruz (Bu kısım aynı kalıyor)
    fis_sorgu = "SELECT ss.*, m.ad as musteri_adi, m.adres, m.telefon, m.vergi_dairesi, m.vergi_no FROM satis_siparisleri ss JOIN musteriler m ON ss.musteri_id = m.id WHERE ss.id = %s;"
    fis_detay = run_db_query(fis_sorgu, params=(siparis_id,), fetch="one")
    
    if not fis_detay:
        raise HTTPException(status_code=404, detail="Satış fişi bulunamadı.")
    
    # Fiş kalemlerini çekiyoruz (Bu kısım aynı kalıyor)
    kalem_sorgu = "SELECT sk.id, sk.urun_id, sk.miktar, sk.birim_fiyat, sk.kdv_orani, u.urun_adi FROM siparis_kalemleri sk JOIN urunler u ON sk.urun_id = u.id WHERE sk.siparis_id = %s;"
    fis_kalemleri = run_db_query(kalem_sorgu, params=(siparis_id,), fetch="all")
    
    # GÜNCELLEME: Şirket bilgilerini de yanıta ekliyoruz
    return {"fis": fis_detay, "kalemler": fis_kalemleri, "sirket": sirket_bilgileri}

@app.get("/api/satis-fisleri")
def get_satis_fisleri():
    # GÜNCELLEME: Sorguya, her siparişin içindeki ürün adlarını birleştiren bir alt sorgu eklendi.
    query = """
        SELECT 
            ss.id, 
            ss.siparis_kodu, 
            ss.siparis_tarihi, 
            ss.genel_toplam, 
            ss.durum, 
            COALESCE(m.ad, 'Bilinmeyen Müşteri') AS musteri_adi,
            (SELECT string_agg(u.urun_adi, ', ') 
             FROM siparis_kalemleri sk
             JOIN urunler u ON sk.urun_id = u.id
             WHERE sk.siparis_id = ss.id) AS siparis_icerigi
        FROM satis_siparisleri ss 
        LEFT JOIN musteriler m ON ss.musteri_id = m.id 
        ORDER BY ss.siparis_tarihi DESC, ss.id DESC;
    """
    return run_db_query(query, fetch="all")
    
@app.post("/api/satis-fisleri", status_code=status.HTTP_201_CREATED, summary="Finansal Etkili Satış Fişi Oluşturur")
async def create_satis_fisi(request: Request):
    data = await request.json()
    siparis_bilgileri = data.get('siparis')
    kalemler = data.get('kalemler')
    if not siparis_bilgileri or not kalemler:
        raise HTTPException(status_code=400, detail="Sipariş ve kalem bilgileri zorunludur.")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            siparis_sorgu = """
                INSERT INTO satis_siparisleri (siparis_kodu, musteri_id, durum, toplam_tutar, kdv_tutari, genel_toplam, siparis_tarihi) 
                VALUES (%(siparis_kodu)s, %(musteri_id)s, 'Onaylandı', %(toplam_tutar)s, %(kdv_tutari)s, %(genel_toplam)s, CURRENT_DATE) RETURNING id;
            """
            cur.execute(siparis_sorgu, siparis_bilgileri)
            siparis_id = cur.fetchone()['id']
            for kalem in kalemler:
                kalem_sorgu = """
                    INSERT INTO siparis_kalemleri (siparis_id, urun_id, miktar, birim_fiyat, kdv_orani, toplam_fiyat, birim)
                    VALUES (%(siparis_id)s, %(urun_id)s, %(miktar)s, %(birim_fiyat)s, %(kdv_orani)s, %(toplam_fiyat)s, 'Adet');
                """
                kalem['siparis_id'] = siparis_id
                cur.execute(kalem_sorgu, kalem)
                is_emri_kodu = f"FIS-{siparis_id}-URUN-{kalem['urun_id']}"
                uretim_params = { 'is_emri_kodu': is_emri_kodu, 'urun_id': kalem['urun_id'], 'hedef_miktar': kalem['miktar'] }
                cur.execute("INSERT INTO uretim_emirleri (is_emri_kodu, urun_id, hedef_miktar, durum) VALUES (%(is_emri_kodu)s, %(urun_id)s, %(hedef_miktar)s, 'Bekliyor');", uretim_params)
            finans_sorgu = """
                INSERT INTO finansal_islemler (islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi)
                VALUES (CURRENT_DATE, 'gelir', %(aciklama)s, %(miktar)s, %(ilgili_cari_id)s, 'musteri');
            """
            cur.execute(finans_sorgu, {'aciklama': f"{siparis_bilgileri['siparis_kodu']} nolu satış fişi", 'miktar': siparis_bilgileri['genel_toplam'], 'ilgili_cari_id': siparis_bilgileri['musteri_id']})
            conn.commit()
            return {"message": "Satış fişi başarıyla oluşturuldu ve müşteri bakiyesine işlendi.", "siparis_id": siparis_id}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Satış fişi kaydı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Fiş kaydedilirken bir sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)

# --- API: Cariler (Müşteriler & Tedarikçiler) ---
@app.get("/api/musteriler")
def get_all_musteriler():
    return run_db_query("SELECT * FROM musteriler ORDER BY ad;", fetch="all")

@app.post("/api/musteriler", status_code=status.HTTP_201_CREATED)
async def create_musteri(request: Request):
    data = await request.json()
    if not data.get('ad'): raise HTTPException(status_code=400, detail="Müşteri adı zorunludur.")
    run_db_query("""
        INSERT INTO musteriler (ad, adres, telefon, email, vergi_dairesi, vergi_no, sorumlu_kisi) 
        VALUES (%(ad)s, %(adres)s, %(telefon)s, %(email)s, %(vergi_dairesi)s, %(vergi_no)s, %(sorumlu_kisi)s);
        """, params=data)
    return {"message": "Müşteri başarıyla eklendi."}

@app.put("/api/musteriler/{musteri_id}")
async def update_musteri(musteri_id: int, request: Request):
    data = await request.json()
    data['id'] = musteri_id
    result = run_db_query("""
        UPDATE musteriler SET ad=%(ad)s, adres=%(adres)s, telefon=%(telefon)s, email=%(email)s, 
        vergi_dairesi=%(vergi_dairesi)s, vergi_no=%(vergi_no)s, sorumlu_kisi=%(sorumlu_kisi)s 
        WHERE id=%(id)s RETURNING id;
        """, params=data, fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    return {"message": "Müşteri başarıyla güncellendi."}

@app.delete("/api/musteriler/{musteri_id}")
def delete_musteri(musteri_id: int):
    result = run_db_query("DELETE FROM musteriler WHERE id = %s RETURNING id;", params=(musteri_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    return {"message": "Müşteri başarıyla silindi."}

@app.get("/api/tedarikciler")
def get_all_tedarikciler():
    return run_db_query("SELECT * FROM tedarikciler ORDER BY firma_adi;", fetch="all")

@app.post("/api/tedarikciler", status_code=status.HTTP_201_CREATED)
async def create_tedarikci(request: Request):
    data = await request.json()
    if not data.get('firma_adi'): 
        raise HTTPException(status_code=400, detail="Firma adı zorunludur.")
    sorgu = """
        INSERT INTO tedarikciler 
        (firma_adi, yetkili_kisi, email, telefon, vergi_dairesi, vergi_no) 
        VALUES (%(firma_adi)s, %(yetkili_kisi)s, %(email)s, %(telefon)s, %(vergi_dairesi)s, %(vergi_no)s);
    """
    run_db_query(sorgu, params=data)
    return {"message": "Tedarikçi başarıyla eklendi."}

@app.put("/api/tedarikciler/{tedarikci_id}")
async def update_tedarikci(tedarikci_id: int, request: Request):
    data = await request.json()
    data['id'] = tedarikci_id
    sorgu = """
        UPDATE tedarikciler SET 
        firma_adi=%(firma_adi)s, yetkili_kisi=%(yetkili_kisi)s, email=%(email)s, telefon=%(telefon)s,
        vergi_dairesi=%(vergi_dairesi)s, vergi_no=%(vergi_no)s 
        WHERE id=%(id)s RETURNING id;
    """
    result = run_db_query(sorgu, params=data, fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı.")
    return {"message": "Tedarikçi başarıyla güncellendi."}

@app.delete("/api/tedarikciler/{tedarikci_id}")
def delete_tedarikci(tedarikci_id: int):
    result = run_db_query("DELETE FROM tedarikciler WHERE id = %s RETURNING id;", params=(tedarikci_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı.")
    return {"message": "Tedarikçi başarıyla silindi."}

# --- API: Personel ---
@app.get("/api/personel")
def get_personel():
    return run_db_query("SELECT id, ad_soyad, pozisyon, ise_giris_tarihi, net_maas FROM personel ORDER BY id DESC;", fetch="all")

@app.get("/api/personel/{personel_id}")
def get_personel_detay(personel_id: int):
    sorgu = "SELECT id, ad_soyad, pozisyon, ise_giris_tarihi, net_maas, tc_kimlik_no, dogum_tarihi, telefon, adres FROM personel WHERE id = %s;"
    personel = run_db_query(sorgu, params=(personel_id,), fetch="one")
    if not personel:
        raise HTTPException(status_code=404, detail="Personel bulunamadı.")
    return personel

@app.post("/api/personel", status_code=status.HTTP_201_CREATED)
async def create_personel(request: Request):
    data = await request.json()
    if not data.get('ad_soyad'): raise HTTPException(status_code=400, detail="Ad Soyad alanı zorunludur.")
    run_db_query("INSERT INTO personel (ad_soyad, pozisyon, ise_giris_tarihi) VALUES (%(ad_soyad)s, %(pozisyon)s, %(ise_giris_tarihi)s);", params=data)
    return {"message": "Personel başarıyla eklendi."}

@app.put("/api/personel/{personel_id}")
async def update_personel(personel_id: int, request: Request):
    data = await request.json()
    data['id'] = personel_id
    if not data.get('ad_soyad'): raise HTTPException(status_code=400, detail="Ad Soyad alanı zorunludur.")
    result = run_db_query("""
        UPDATE personel SET ad_soyad=%(ad_soyad)s, pozisyon=%(pozisyon)s, ise_giris_tarihi=%(ise_giris_tarihi)s 
        WHERE id=%(id)s RETURNING id;
    """, params=data, fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Personel bulunamadı.")
    return {"message": "Personel başarıyla güncellendi."}

@app.put("/api/personel/{personel_id}/maas")
async def update_personel_maas(personel_id: int, request: Request):
    data = await request.json()
    if 'net_maas' not in data: raise HTTPException(status_code=400, detail="net_maas alanı zorunludur.")
    result = run_db_query("UPDATE personel SET net_maas = %s WHERE id = %s RETURNING id;", params=(data['net_maas'], personel_id), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Personel bulunamadı.")
    return {"message": "Personel net maaşı başarıyla güncellendi."}

@app.delete("/api/personel/{personel_id}")
def delete_personel(personel_id: int):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM maas_bordrolari WHERE personel_id = %s;", (personel_id,))
            cur.execute("DELETE FROM personel_giris_cikis WHERE personel_id = %s;", (personel_id,))
            cur.execute("DELETE FROM personel_vardiyalari WHERE personel_id = %s;", (personel_id,))
            cur.execute("DELETE FROM izin_kayitlari WHERE personel_id = %s;", (personel_id,))
            cur.execute("DELETE FROM performans_degerlendirmeleri WHERE personel_id = %s;", (personel_id,))
            cur.execute("DELETE FROM egitim_kayitlari WHERE personel_id = %s;", (personel_id,))
            cur.execute("DELETE FROM personel WHERE id = %s RETURNING id;", (personel_id,))
            if cur.rowcount == 0:
                conn.rollback()
                raise HTTPException(status_code=404, detail="Personel bulunamadı.")
            conn.commit()
            return {"message": "Personel ve ilgili tüm kayıtları başarıyla silindi."}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Silme işlemi sırasında bir hata oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)

# --- API: Personel Detayları (İzin, Performans, Eğitim) ---
@app.get("/api/personel/{personel_id}/izinler")
def get_personel_izinleri(personel_id: int):
    sorgu = "SELECT id, izin_tipi, baslangic_tarihi, bitis_tarihi, aciklama FROM izin_kayitlari WHERE personel_id = %s ORDER BY baslangic_tarihi DESC;"
    return run_db_query(sorgu, params=(personel_id,), fetch="all")

@app.post("/api/personel/{personel_id}/izinler", status_code=status.HTTP_201_CREATED)
async def create_personel_izni(personel_id: int, request: Request):
    data = await request.json()
    if not all(k in data for k in ['izin_tipi', 'baslangic_tarihi', 'bitis_tarihi']):
        raise HTTPException(status_code=400, detail="İzin tipi, başlangıç ve bitiş tarihleri zorunludur.")
    data['personel_id'] = personel_id
    sorgu = "INSERT INTO izin_kayitlari (personel_id, izin_tipi, baslangic_tarihi, bitis_tarihi, aciklama) VALUES (%(personel_id)s, %(izin_tipi)s, %(baslangic_tarihi)s, %(bitis_tarihi)s, %(aciklama)s);"
    run_db_query(sorgu, params=data)
    return {"message": "İzin kaydı başarıyla eklendi."}   

@app.delete("/api/izinler/{izin_id}")
def delete_personel_izni(izin_id: int):
    result = run_db_query("DELETE FROM izin_kayitlari WHERE id = %s RETURNING id;", params=(izin_id,), fetch="one")
    if result is None:
        raise HTTPException(status_code=404, detail="İzin kaydı bulunamadı.")
    return {"message": "İzin kaydı başarıyla silindi."}

@app.get("/api/personel/{personel_id}/performans")
def get_personel_performans_notlari(personel_id: int):
    sorgu = "SELECT id, degerlendirme_tarihi, degerlendiren_yonetici, puan, yonetici_notlari FROM performans_degerlendirmeleri WHERE personel_id = %s ORDER BY degerlendirme_tarihi DESC;"
    return run_db_query(sorgu, params=(personel_id,), fetch="all")

@app.post("/api/personel/{personel_id}/performans", status_code=status.HTTP_201_CREATED)
async def create_performans_notu(personel_id: int, request: Request):
    data = await request.json()
    if not all(k in data for k in ['degerlendirme_tarihi', 'yonetici_notlari']):
        raise HTTPException(status_code=400, detail="Değerlendirme tarihi ve yönetici notları zorunludur.")
    data['personel_id'] = personel_id
    data['puan'] = data.get('puan') or None
    data['degerlendiren_yonetici'] = data.get('degerlendiren_yonetici') or None
    sorgu = "INSERT INTO performans_degerlendirmeleri (personel_id, degerlendirme_tarihi, degerlendiren_yonetici, puan, yonetici_notlari) VALUES (%(personel_id)s, %(degerlendirme_tarihi)s, %(degerlendiren_yonetici)s, %(puan)s, %(yonetici_notlari)s);"
    run_db_query(sorgu, params=data)
    return {"message": "Performans notu başarıyla eklendi."}

@app.delete("/api/performans/{not_id}")
def delete_performans_notu(not_id: int):
    result = run_db_query("DELETE FROM performans_degerlendirmeleri WHERE id = %s RETURNING id;", params=(not_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Performans notu bulunamadı.")
    return {"message": "Performans notu başarıyla silindi."}

@app.get("/api/personel/{personel_id}/egitimler")
def get_personel_egitimleri(personel_id: int):
    sorgu = "SELECT * FROM egitim_kayitlari WHERE personel_id = %s ORDER BY baslangic_tarihi DESC;"
    return run_db_query(sorgu, params=(personel_id,), fetch="all")

@app.post("/api/personel/{personel_id}/egitimler", status_code=status.HTTP_201_CREATED)
async def create_egitim_kaydi(personel_id: int, request: Request):
    data = await request.json()
    if not data.get('egitim_adi'):
        raise HTTPException(status_code=400, detail="Eğitim adı zorunludur.")
    data['personel_id'] = personel_id
    sorgu = "INSERT INTO egitim_kayitlari (personel_id, egitim_adi, egitim_kurumu, baslangic_tarihi, bitis_tarihi, aciklama) VALUES (%(personel_id)s, %(egitim_adi)s, %(egitim_kurumu)s, %(baslangic_tarihi)s, %(bitis_tarihi)s, %(aciklama)s);"
    run_db_query(sorgu, params=data)
    return {"message": "Eğitim kaydı başarıyla eklendi."}

@app.delete("/api/egitimler/{egitim_id}")
def delete_egitim_kaydi(egitim_id: int):
    result = run_db_query("DELETE FROM egitim_kayitlari WHERE id = %s RETURNING id;", params=(egitim_id,), fetch="one")
    if result is None:
        raise HTTPException(status_code=404, detail="Eğitim kaydı bulunamadı.")
    return {"message": "Eğitim kaydı başarıyla silindi."}

# --- API: Maaş Bordroları ---
@app.get("/api/maas-bordrolari")
def get_maas_bordrolari():
    sorgu = "SELECT mb.id, p.ad_soyad, mb.odeme_tarihi, mb.net_maas FROM maas_bordrolari mb JOIN personel p ON mb.personel_id = p.id ORDER BY mb.odeme_tarihi DESC, p.ad_soyad;"
    return run_db_query(sorgu, fetch="all")
@app.post("/api/maas-bordrolari", status_code=status.HTTP_201_CREATED)
async def create_maas_bordro(request: Request):
    data = await request.json()
    personel_id, odeme_tarihi = data.get('personel_id'), data.get('donem')
    if not personel_id or not odeme_tarihi: raise HTTPException(status_code=400, detail="Personel ve dönem bilgileri zorunludur.")
    personel = run_db_query("SELECT net_maas FROM personel WHERE id = %s;", params=(personel_id,), fetch="one")
    if not personel or personel.get('net_maas') is None: raise HTTPException(status_code=404, detail="Personel bulunamadı veya net maaşı tanımlanmamış.")
    mevcut_bordro = run_db_query("SELECT id FROM maas_bordrolari WHERE personel_id = %s AND odeme_tarihi = %s;", params=(personel_id, odeme_tarihi), fetch="one")
    if mevcut_bordro: raise HTTPException(status_code=409, detail="Bu personel için bu dönemde zaten bir bordro oluşturulmuş.")
    bordro_data = {"personel_id": personel_id, "odeme_tarihi": odeme_tarihi, "net_maas": personel['net_maas']}
    run_db_query("INSERT INTO maas_bordrolari (personel_id, odeme_tarihi, net_maas) VALUES (%(personel_id)s, %(odeme_tarihi)s, %(net_maas)s);", params=bordro_data)
    return {"message": f"{odeme_tarihi} dönemi için maaş bordrosu başarıyla oluşturuldu."}
@app.delete("/api/maas-bordrolari/{bordro_id}")
def delete_maas_bordro(bordro_id: int):
    result = run_db_query("DELETE FROM maas_bordrolari WHERE id = %s RETURNING id;", params=(bordro_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Bordro bulunamadı.")
    return {"message": "Maaş bordrosu başarıyla silindi."}

# --- API: PDKS (Personel Devam Kontrol Sistemi) ---
@app.get("/api/pdks/iceridekiler")
def get_icerideki_personel():
    sorgu = "SELECT pgc.id, p.ad_soyad, pgc.giris_zamani FROM personel_giris_cikis pgc JOIN personel p ON p.id = pgc.personel_id WHERE pgc.cikis_zamani IS NULL AND p.aktif_mi = TRUE ORDER BY pgc.giris_zamani DESC;"
    return run_db_query(sorgu, fetch="all")
@app.post("/api/pdks/giris", status_code=status.HTTP_201_CREATED)
async def create_giris(request: Request):
    data = await request.json()
    personel_id = data.get('personel_id')
    if not personel_id: raise HTTPException(status_code=400, detail="Personel ID zorunludur.")
    iceride_mi = run_db_query("SELECT id FROM personel_giris_cikis WHERE personel_id = %s AND cikis_zamani IS NULL;", params=(personel_id,), fetch="one")
    if iceride_mi: raise HTTPException(status_code=409, detail="Bu personel zaten giriş yapmış görünüyor.")
    run_db_query("INSERT INTO personel_giris_cikis (personel_id) VALUES (%s);", params=(personel_id,))
    return {"message": "Giriş kaydı başarılı."}
@app.put("/api/pdks/cikis")
async def create_cikis(request: Request):
    data = await request.json()
    personel_id = data.get('personel_id')
    if not personel_id: raise HTTPException(status_code=400, detail="Personel ID zorunludur.")
    son_giris = run_db_query("SELECT id FROM personel_giris_cikis WHERE personel_id = %s AND cikis_zamani IS NULL ORDER BY giris_zamani DESC LIMIT 1;", params=(personel_id,), fetch="one")
    if not son_giris: raise HTTPException(status_code=404, detail="Bu personel için bekleyen bir giriş kaydı bulunamadı.")
    run_db_query("UPDATE personel_giris_cikis SET cikis_zamani = CURRENT_TIMESTAMP WHERE id = %s;", params=(son_giris['id'],))
    return {"message": "Çıkış kaydı başarılı."}

# --- API: Vardiyalar ---
@app.get("/api/vardiyalar")
def get_vardiyalar(): return run_db_query("SELECT id, vardiya_adi, TO_CHAR(baslangic_saati, 'HH24:MI') as baslangic_saati, TO_CHAR(bitis_saati, 'HH24:MI') as bitis_saati FROM vardiyalar ORDER BY baslangic_saati;", fetch="all")
@app.post("/api/vardiyalar", status_code=status.HTTP_201_CREATED)
async def create_vardiya(request: Request):
    data = await request.json()
    if not data.get('vardiya_adi') or not data.get('baslangic_saati') or not data.get('bitis_saati'): raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    run_db_query("INSERT INTO vardiyalar (vardiya_adi, baslangic_saati, bitis_saati) VALUES (%(vardiya_adi)s, %(baslangic_saati)s, %(bitis_saati)s);", params=data)
    return {"message": "Vardiya başarıyla oluşturuldu."}
@app.delete("/api/vardiyalar/{vardiya_id}")
def delete_vardiya(vardiya_id: int):
    result = run_db_query("DELETE FROM vardiyalar WHERE id = %s RETURNING id;", params=(vardiya_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Vardiya bulunamadı.")
    return {"message": "Vardiya başarıyla silindi."}
@app.get("/api/personel-vardiyalari")
def get_personel_vardiyalari(yil: int, ay: int):
    sorgu = "SELECT personel_id, vardiya_id, EXTRACT(DAY FROM tarih) as gun FROM personel_vardiyalari WHERE EXTRACT(YEAR FROM tarih) = %s AND EXTRACT(MONTH FROM tarih) = %s;"
    atamalar_liste = run_db_query(sorgu, params=(yil, ay), fetch="all")
    sonuc = {}
    for atama in atamalar_liste:
        personel_id, gun, vardiya_id = atama['personel_id'], int(atama['gun']), atama['vardiya_id']
        if personel_id not in sonuc: sonuc[personel_id] = {}
        sonuc[personel_id][gun] = vardiya_id
    return sonuc
@app.post("/api/personel-vardiyalari")
async def save_personel_vardiyalari(request: Request):
    data = await request.json()
    atamalar = data.get('atamalar', [])
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for atama in atamalar:
                if atama['vardiya_id'] == 0: cur.execute("DELETE FROM personel_vardiyalari WHERE personel_id = %s AND tarih = %s;", (atama['personel_id'], atama['tarih']))
                else: cur.execute("INSERT INTO personel_vardiyalari (personel_id, tarih, vardiya_id) VALUES (%s, %s, %s) ON CONFLICT (personel_id, tarih) DO UPDATE SET vardiya_id = EXCLUDED.vardiya_id;", (atama['personel_id'], atama['tarih'], atama['vardiya_id']))
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {e}")
    finally:
        db_pool.putconn(conn)
    return {"message": "Vardiya planı başarıyla kaydedildi."}

# --- API: Finans ---
@app.get("/api/finansal-islemler")
def get_finansal_islemler():
    sorgu = "SELECT fi.id, fi.islem_tarihi, fi.islem_tipi, fi.aciklama, fi.miktar, COALESCE(m.ad, t.firma_adi, 'Bilinmiyor') AS ilgili_cari_adi FROM finansal_islemler fi LEFT JOIN musteriler m ON fi.ilgili_cari_id = m.id AND fi.cari_tipi = 'musteri' LEFT JOIN tedarikciler t ON fi.ilgili_cari_id = t.id AND fi.cari_tipi = 'tedarikci' ORDER BY fi.islem_tarihi DESC;"
    return run_db_query(sorgu, fetch="all")
@app.post("/api/finansal-islemler", status_code=status.HTTP_201_CREATED)
async def create_finansal_islem(request: Request):
    data = await request.json()
    if not data.get('islem_tarihi') or not data.get('islem_tipi') or not data.get('miktar'): raise HTTPException(status_code=400, detail="İşlem tarihi, tipi ve miktarı zorunludur.")
    ilgili_cari_id = data.get('ilgili_cari_id')
    cari_tipi = None
    if ilgili_cari_id and '-' in str(ilgili_cari_id):
        cari_tipi, ilgili_cari_id = str(ilgili_cari_id).split('-')
    params = {"islem_tarihi": data['islem_tarihi'], "islem_tipi": data['islem_tipi'], "aciklama": data.get('aciklama'), "miktar": data['miktar'], "ilgili_cari_id": int(ilgili_cari_id) if ilgili_cari_id else None, "cari_tipi": cari_tipi}
    run_db_query("INSERT INTO finansal_islemler (islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi) VALUES (%(islem_tarihi)s, %(islem_tipi)s, %(aciklama)s, %(miktar)s, %(ilgili_cari_id)s, %(cari_tipi)s);", params=params)
    return {"message": "Finansal işlem başarıyla eklendi."}
@app.delete("/api/finansal-islemler/{islem_id}")
def delete_finansal_islem(islem_id: int):
    result = run_db_query("DELETE FROM finansal_islemler WHERE id = %s RETURNING id;", params=(islem_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Finansal işlem bulunamadı.")
    return {"message": "Finansal işlem başarıyla silindi."}
@app.get("/api/musteri-bakiyeleri")
async def get_musteri_bakiyeleri():
    query = "SELECT m.id, m.ad, COALESCE(SUM(CASE WHEN fi.islem_tipi = 'gelir' THEN fi.miktar ELSE -fi.miktar END), 0) AS bakiye FROM musteriler m LEFT JOIN finansal_islemler fi ON m.id = fi.ilgili_cari_id AND fi.cari_tipi = 'musteri' GROUP BY m.id, m.ad ORDER BY m.ad;"
    return run_db_query(query, fetch="all")
@app.get("/api/tedarikci-bakiyeleri")
async def get_tedarikci_bakiyeleri():
    query = "SELECT t.id, t.firma_adi, COALESCE(SUM(CASE WHEN fi.islem_tipi = 'gider' THEN fi.miktar ELSE -fi.miktar END), 0) AS bakiye FROM tedarikciler t LEFT JOIN finansal_islemler fi ON t.id = fi.ilgili_cari_id AND fi.cari_tipi = 'tedarikci' GROUP BY t.id, t.firma_adi ORDER BY t.firma_adi;"
    return run_db_query(query, fetch="all")

# --- API: Sistem Ayarları ---
@app.get("/api/sistem-ayarlari")
def get_ayarlar(): return run_db_query("SELECT * FROM sistem_ayarlari ORDER BY ayar_anahtari;", fetch="all")
@app.post("/api/sistem-ayarlari", status_code=status.HTTP_201_CREATED)
async def create_ayar(request: Request):
    data = await request.json()
    if not data.get('ayar_anahtari') or not data.get('ayar_degeri'): raise HTTPException(status_code=400, detail="Ayar anahtarı ve değeri zorunludur.")
    run_db_query("INSERT INTO sistem_ayarlari (ayar_anahtari, ayar_degeri, aciklama) VALUES (%(ayar_anahtari)s, %(ayar_degeri)s, %(aciklama)s);", params=data)
    return {"message": "Ayar başarıyla eklendi."}
@app.put("/api/sistem-ayarlari/{ayar_id}")
async def update_ayar(ayar_id: int, request: Request):
    data = await request.json()
    result = run_db_query("UPDATE sistem_ayarlari SET ayar_degeri = %(ayar_degeri)s WHERE id = %(id)s RETURNING id;", params={'ayar_degeri': data.get('ayar_degeri'), 'id': ayar_id}, fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Ayar bulunamadı.")
    return {"message": "Ayar başarıyla güncellendi."}
@app.delete("/api/sistem-ayarlari/{ayar_id}")
def delete_ayar(ayar_id: int):
    result = run_db_query("DELETE FROM sistem_ayarlari WHERE id = %s RETURNING id;", params=(ayar_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Ayar bulunamadı.")
    return {"message": "Ayar başarıyla silindi."}

# --- API: Raporlama ---
@app.get("/api/raporlar/uretim-ozeti")
def get_uretim_ozeti_raporu():
    sorgu = """
        SELECT 
            ue.is_emri_kodu, 
            COALESCE(u.urun_adi, 'Silinmiş/Bilinmeyen Ürün') as urun_adi, 
            ue.hedef_miktar, 
            ue.uretilen_miktar, 
            ue.durum, 
            TO_CHAR(ue.baslama_tarihi, 'DD-MM-YYYY HH24:MI') as baslama_tarihi, 
            TO_CHAR(ue.bitis_tarihi, 'DD-MM-YYYY HH24:MI') as bitis_tarihi 
        FROM uretim_emirleri ue 
        LEFT JOIN urunler u ON ue.urun_id = u.id 
        ORDER BY ue.id DESC;
    """
    return run_db_query(sorgu, fetch="all")
# --- API: Kalite Kontrol ---
@app.get("/api/kalite-kontrol")
def get_kalite_kontrol_kayitlari():
    sorgu = "SELECT kk.id, u.urun_adi, p.ad_soyad AS kontrol_eden_personel, kk.kontrol_tarihi, kk.sonuc, kk.aciklama FROM kalite_kontrol kk JOIN urunler u ON kk.urun_id = u.id LEFT JOIN personel p ON kk.kontrol_eden_personel_id = p.id ORDER BY kk.kontrol_tarihi DESC;"
    return run_db_query(sorgu, fetch="all")
@app.post("/api/kalite-kontrol", status_code=status.HTTP_201_CREATED)
async def create_kalite_kontrol_kaydi(request: Request):
    data = await request.json()
    if not data.get('urun_id') or not data.get('sonuc') or not data.get('kontrol_tarihi'): raise HTTPException(status_code=400, detail="Ürün ID, sonuç ve kontrol tarihi zorunludur.")
    run_db_query("INSERT INTO kalite_kontrol (urun_id, kontrol_tarihi, kontrol_eden_personel_id, sonuc, aciklama) VALUES (%(urun_id)s, %(kontrol_tarihi)s, %(kontrol_eden_personel_id)s, %(sonuc)s, %(aciklama)s);", params=data)
    return {"message": "Kalite kontrol kaydı başarıyla eklendi."}
@app.delete("/api/kalite-kontrol/{kayit_id}")
def delete_kalite_kontrol_kaydi(kayit_id: int):
    result = run_db_query("DELETE FROM kalite_kontrol WHERE id = %s RETURNING id;", params=(kayit_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Kalite kontrol kaydı bulunamadı.")
    return {"message": "Kalite kontrol kaydı başarıyla silindi."}



# --- API: İzlenebilirlik (Hammadde Lot) ---
@app.get("/api/hammadde-girisleri")
def get_hammadde_girisleri():
    sorgu = "SELECT hg.*, h.hammadde_adi, h.birim FROM hammadde_girisleri hg JOIN hammaddeler h ON hg.hammadde_id = h.id ORDER BY hg.giris_tarihi DESC LIMIT 50;"
    return run_db_query(sorgu, fetch="all")
@app.post("/api/hammadde-girisleri", status_code=status.HTTP_201_CREATED)
async def create_hammadde_girisi(request: Request):
    data = await request.json()
    data['kalan_miktar'] = data.get('giris_miktari')
    run_db_query("INSERT INTO hammadde_girisleri (hammadde_id, lot_numarasi, giris_miktari, kalan_miktar, tedarikci) VALUES (%(hammadde_id)s, %(lot_numarasi)s, %(giris_miktari)s, %(kalan_miktar)s, %(tedarikci)s);", params=data)
    return {"message": "Hammadde lot girişi başarıyla kaydedildi."}
@app.delete("/api/hammadde-girisleri/{giris_id}")
def delete_hammadde_girisi(giris_id: int):
    kullanim = run_db_query("SELECT id FROM uretim_lot_kullanimi WHERE hammadde_giris_id = %s LIMIT 1;", params=(giris_id,), fetch="one")
    if kullanim: raise HTTPException(status_code=409, detail="Bu lot bir üretimde kullanıldığı için silinemez.")
    result = run_db_query("DELETE FROM hammadde_girisleri WHERE id = %s RETURNING id;", params=(giris_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Lot girişi bulunamadı.")
    return {"message": "Lot girişi başarıyla silindi."}
@app.get("/api/izlenebilirlik/uretim/{uretim_emri_id}")
def get_uretim_izlenebilirlik_raporu(uretim_emri_id: int):
    sorgu = "SELECT ulk.kullanilan_miktar, hg.lot_numarasi, h.hammadde_adi, h.birim FROM uretim_lot_kullanimi ulk JOIN hammadde_girisleri hg ON ulk.hammadde_giris_id = hg.id JOIN hammaddeler h ON hg.hammadde_id = h.id WHERE ulk.uretim_emri_id = %s;"
    return run_db_query(sorgu, params=(uretim_emri_id,), fetch="all")

# --- API: Kalıp Yönetimi ---
@app.get("/api/kaliplar")
def get_all_kaliplar():
    return run_db_query("SELECT * FROM kaliplar ORDER BY kalip_kodu;", fetch="all")
@app.post("/api/kaliplar", status_code=status.HTTP_201_CREATED)
async def create_kalip(request: Request):
    data = await request.json()
    sorgu = "INSERT INTO kaliplar (kalip_kodu, kalip_adi, goz_sayisi, cevrim_suresi_sn, garanti_baski_sayisi, lokasyon, durum) VALUES (%(kalip_kodu)s, %(kalip_adi)s, %(goz_sayisi)s, %(cevrim_suresi_sn)s, %(garanti_baski_sayisi)s, %(lokasyon)s, %(durum)s);"
    run_db_query(sorgu, params=data)
    return {"message": "Kalıp başarıyla eklendi."}
@app.put("/api/kaliplar/{kalip_id}")
async def update_kalip(kalip_id: int, request: Request):
    data = await request.json()
    data['id'] = kalip_id
    sorgu = "UPDATE kaliplar SET kalip_kodu=%(kalip_kodu)s, kalip_adi=%(kalip_adi)s, goz_sayisi=%(goz_sayisi)s, cevrim_suresi_sn=%(cevrim_suresi_sn)s, garanti_baski_sayisi=%(garanti_baski_sayisi)s, lokasyon=%(lokasyon)s, durum=%(durum)s WHERE id=%(id)s RETURNING id;"
    result = run_db_query(sorgu, params=data, fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Kalıp bulunamadı.")
    return {"message": "Kalıp başarıyla güncellendi."}
@app.delete("/api/kaliplar/{kalip_id}")
def delete_kalip(kalip_id: int):
    result = run_db_query("DELETE FROM kaliplar WHERE id = %s RETURNING id;", params=(kalip_id,), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Kalıp bulunamadı.")
    return {"message": "Kalıp başarıyla silindi."}

# --- API: Saha Elemanı (Login) ---
@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    kullanici_adi, sifre = data.get("kullanici_adi"), data.get("sifre")
    if not kullanici_adi or not sifre: raise HTTPException(status_code=400, detail="Kullanıcı adı ve şifre zorunludur.")
    eleman = run_db_query("SELECT * FROM saha_elemanlari WHERE kullanici_adi = %s AND aktif = TRUE;", params=(kullanici_adi,), fetch="one")
    if not eleman or not verify_password(sifre, eleman['sifre_hash']):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")
    return {"message": "Giriş başarılı", "kullanici_adi": eleman['kullanici_adi'], "id": eleman['id']}

@app.post("/api/saha_elemanlari")
async def create_saha_elemani(request: Request):
    data = await request.json()
    kullanici_adi, sifre, ad_soyad = data.get("kullanici_adi"), data.get("sifre"), data.get("ad_soyad")
    if not kullanici_adi or not sifre or not ad_soyad: raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    hashed_sifre = get_password_hash(sifre)
    try:
        run_db_query("INSERT INTO saha_elemanlari (kullanici_adi, sifre_hash, ad_soyad) VALUES (%s, %s, %s);", params=(kullanici_adi, hashed_sifre, ad_soyad))
        return {"message": "Saha elemanı başarıyla eklendi."}
    except:
        raise HTTPException(status_code=409, detail="Kullanıcı adı zaten mevcut.")

# --- API: TCMB Döviz Kurları ---
currency_cache = {"data": None, "timestamp": 0}
@app.get("/api/doviz-kurlari")
def get_doviz_kurlari():
    if time.time() - currency_cache["timestamp"] < 3600 and currency_cache["data"]:
        return JSONResponse(content=currency_cache["data"])
    try:
        response = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        usd_rate = root.find("./Currency[@Kod='USD']/ForexBuying").text
        eur_rate = root.find("./Currency[@Kod='EUR']/ForexBuying").text
        data = {"USD": f"{float(usd_rate):.4f}", "EUR": f"{float(eur_rate):.4f}"}
        currency_cache["data"], currency_cache["timestamp"] = data, time.time()
        return JSONResponse(content=data)
    except Exception as e:
        print(f"Döviz kuru alınırken hata: {e}")
        if currency_cache["data"]: return JSONResponse(content=currency_cache["data"])
        raise HTTPException(status_code=503, detail="Döviz kuru verileri anlık olarak alınamadı.")

# --- API: Akıllı Planlama (MRP) ---

@app.get("/api/planlama/planlanacak-siparisler", summary="Henüz planı oluşturulmamış onaylı siparişleri listeler")
def get_plannable_orders():
    # Bu sorgu, satis_siparisleri tablosunda olup uretim_planlari tablosunda karşılığı olmayan kayıtları getirir.
    sorgu = """
        SELECT 
            ss.id as satis_id,
            ss.siparis_kodu
        FROM satis_siparisleri ss
        LEFT JOIN uretim_planlari up ON ss.id = up.satis_id
        WHERE ss.durum = 'Onaylandı' AND up.id IS NULL
        ORDER BY ss.siparis_tarihi DESC;
    """
    return run_db_query(sorgu, fetch="all")

@app.get("/api/planlama/aktif-planlar", summary="Oluşturulmuş ve aktif olan tüm üretim planlarını listeler")
def get_active_plans():
    sorgu = """
        SELECT 
            up.id, 
            up.plan_adi, 
            up.durum,
            up.olusturma_tarihi,
            ss.siparis_kodu
        FROM uretim_planlari up
        LEFT JOIN satis_siparisleri ss ON up.satis_id = ss.id
        ORDER BY up.olusturma_tarihi DESC;
    """
    return run_db_query(sorgu, fetch="all")

@app.post("/api/planlama", status_code=status.HTTP_201_CREATED)
def create_uretim_plani(plan_data: UretimPlanCreate):
    satis_id = plan_data.satis_id
    plan_adi = plan_data.plan_adi
    
    mevcut_plan = run_db_query("SELECT id FROM uretim_planlari WHERE satis_id = %s", params=(satis_id,), fetch="one")
    if mevcut_plan:
        raise HTTPException(status_code=409, detail="Bu satış siparişi için zaten bir üretim planı oluşturulmuş.")

    plan_params = {
        "plan_adi": plan_adi,
        "satis_id": satis_id,
        "durum": "Planlandı"
    }
    run_db_query("""
        INSERT INTO uretim_planlari (plan_adi, satis_id, durum)
        VALUES (%(plan_adi)s, %(satis_id)s, %(durum)s);
    """, params=plan_params)

    return {"message": f"'{plan_adi}' kodlu üretim planı başarıyla oluşturuldu!"}

@app.delete("/api/planlama/{plan_id}", status_code=status.HTTP_200_OK)
def delete_uretim_plani(plan_id: int):
    # Planı silmeden önce, bu plana bağlı üretim emirleri var mı diye kontrol edilebilir.
    # Şimdilik direkt silme işlemi yapıyoruz.
    result = run_db_query("DELETE FROM uretim_planlari WHERE id = %s RETURNING id;", params=(plan_id,), fetch="one")
    if result is None:
        raise HTTPException(status_code=4.4, detail="Üretim planı bulunamadı.")
    return {"message": "Üretim planı başarıyla silindi."}

# ... (MRP Analiz ve Üretim Emri Oluşturma endpoint'leri burada devam edebilir)
@app.get("/api/planlama/analiz")
def analyze_for_mrp():
    # ... Bu fonksiyonun içeriği aynı kalabilir ...
    pass

@app.post("/api/planlama/uretim-emri-olustur", status_code=status.HTTP_201_CREATED)
async def create_uretim_emri_from_mrp(request: Request):
    # ... Bu fonksiyonun içeriği aynı kalabilir ...
    pass
# --- API: Satın Alma Talepleri ---
@app.get("/api/satin-alma-talepleri")
def get_satin_alma_talepleri():
    sorgu = "SELECT sat.id, sat.talep_edilen_miktar, sat.birim, sat.durum, sat.talep_tarihi, COALESCE(h.hammadde_adi, 'SİLİNMİŞ HAMMADDE') as hammadde_adi FROM satin_alma_talepleri sat LEFT JOIN hammaddeler h ON sat.hammadde_id = h.id ORDER BY sat.talep_tarihi DESC;"
    return run_db_query(sorgu, fetch="all")

@app.post("/api/satin-alma-talepleri", status_code=status.HTTP_201_CREATED)
async def create_satin_alma_talebi(request: Request):
    data = await request.json()
    hammadde_id, miktar, birim = data.get('hammadde_id'), data.get('miktar'), data.get('birim')
    if not hammadde_id or not miktar:
        raise HTTPException(status_code=400, detail="Hammadde ID ve miktar zorunludur.")
    sorgu = "INSERT INTO satin_alma_talepleri (hammadde_id, talep_edilen_miktar, birim) VALUES (%(hammadde_id)s, %(miktar)s, %(birim)s);"
    params = {'hammadde_id': hammadde_id, 'miktar': miktar, 'birim': birim}
    run_db_query(sorgu, params=params)
    return {"message": "Satın alma talebi başarıyla oluşturuldu."}
    
@app.put("/api/satin-alma-talepleri/{talep_id}/durum")
async def update_satin_alma_talep_durumu(talep_id: int, request: Request):
    data = await request.json()
    new_status = data.get('durum')
    if not new_status: raise HTTPException(status_code=400, detail="Yeni durum belirtilmelidir.")
    result = run_db_query("UPDATE satin_alma_talepleri SET durum = %s WHERE id = %s RETURNING id;", params=(new_status, talep_id), fetch="one")
    if result is None: raise HTTPException(status_code=404, detail="Satın alma talebi bulunamadı.")
    return {"message": f"Talep #{talep_id} durumu başarıyla '{new_status}' olarak güncellendi."}

# --- API: Bildirimler ---
@app.get("/api/notifications")
def get_notifications():
    notifications = []
    try:
        query_stock = "SELECT hammadde_adi, stok_miktari, kritik_stok_seviyesi FROM hammaddeler WHERE stok_miktari <= kritik_stok_seviyesi AND arsivlendi IS NOT TRUE;"
        low_stock_items = run_db_query(query_stock, fetch="all")
        if low_stock_items:
            for item in low_stock_items:
                message = f"'{item['hammadde_adi']}' stoğu kritik seviyede! (Mevcut: {item['stok_miktari']}, Kritik: {item['kritik_stok_seviyesi']})"
                notifications.append({"type": "stock_alert", "message": message, "level": "warning", "icon": "fas fa-boxes"})
    except Exception as e:
        print(f"Bildirim sorgusu hatası (kritik stok): {e}")
    try:
        query_uretim = "SELECT is_emri_kodu, olusturma_tarihi FROM uretim_emirleri WHERE durum = 'Bekliyor' AND olusturma_tarihi < NOW() - INTERVAL '2 days';"
        gecikmis_emirler = run_db_query(query_uretim, fetch="all")
        if gecikmis_emirler:
            for emir in gecikmis_emirler:
                message = f"'{emir['is_emri_kodu']}' nolu üretim emri 2 günden fazladır bekliyor."
                notifications.append({"type": "uretim_alert", "message": message, "level": "danger", "icon": "fas fa-gears"})
    except Exception as e:
        print(f"Bildirim sorgusu hatası (üretim emri): {e}")
    return notifications
    
# ==========================================================
# --- API: MÜŞTERİ & TEDARİKÇİ PORTALI ---
# ==========================================================
@app.post("/api/portal/register", summary="Yeni bir portal kullanıcısı oluştur (Yönetici için)")
def register_portal_user(user_data: PortalUserCreate):
    hashed_sifre = get_password_hash(user_data.sifre)
    if user_data.rol == 'musteri' and not user_data.musteri_id:
        raise HTTPException(status_code=400, detail="Müşteri rolü için musteri_id zorunludur.")
    if user_data.rol == 'tedarikci' and not user_data.tedarikci_id:
        raise HTTPException(status_code=400, detail="Tedarikçi rolü için tedarikci_id zorunludur.")
    query = "INSERT INTO portal_kullanicilari (kullanici_adi, sifre_hash, rol, musteri_id, tedarikci_id) VALUES (%(kullanici_adi)s, %(sifre_hash)s, %(rol)s, %(musteri_id)s, %(tedarikci_id)s)"
    params = {"kullanici_adi": user_data.kullanici_adi, "sifre_hash": hashed_sifre, "rol": user_data.rol, "musteri_id": user_data.musteri_id, "tedarikci_id": user_data.tedarikci_id}
    try:
        run_db_query(query, params=params)
        return {"message": f"'{user_data.kullanici_adi}' adlı portal kullanıcısı başarıyla oluşturuldu."}
    except HTTPException as e:
        if e.status_code == 409:
            raise HTTPException(status_code=409, detail="Bu kullanıcı adı zaten mevcut.")
        raise e

@app.post("/api/portal/login", summary="Portal kullanıcısı için giriş ve token alma")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = run_db_query("SELECT * FROM portal_kullanicilari WHERE kullanici_adi = %s", params=(form_data.username,), fetch="one")
    if not user or not verify_password(form_data.password, user['sifre_hash']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz kullanıcı adı veya şifre", headers={"WWW-Authenticate": "Bearer"},)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user['kullanici_adi']}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "rol": user['rol']}

@app.get("/api/portal/my-orders", summary="Giriş yapmış müşterinin kendi siparişlerini listeler")
def get_my_orders(current_user: dict = Depends(get_current_user)):
    if current_user['rol'] != 'musteri':
        raise HTTPException(status_code=403, detail="Bu kaynağa erişim yetkiniz yok.")
    musteri_id = current_user['musteri_id']
    query = "SELECT ss.id, ss.siparis_kodu, ss.durum, ss.siparis_tarihi FROM satis_siparisleri ss WHERE ss.musteri_id = %s ORDER BY ss.siparis_tarihi DESC;"
    orders = run_db_query(query, params=(musteri_id,), fetch="all")
    return {"musteri_id": musteri_id, "siparisler": orders}

@app.get("/api/portal/my-purchase-orders", summary="Giriş yapmış tedarikçinin kendi satınalma taleplerini listeler")
def get_my_purchase_orders(current_user: dict = Depends(get_current_user)):
    if current_user['rol'] != 'tedarikci':
        raise HTTPException(status_code=403, detail="Bu kaynağa erişim yetkiniz yok.")
    tedarikci_id = current_user['tedarikci_id']
    query = """
        SELECT sat.id, h.hammadde_adi, sat.talep_edilen_miktar, sat.birim, sat.durum, sat.talep_tarihi
        FROM satin_alma_talepleri sat
        JOIN hammaddeler h ON sat.hammadde_id = h.id
        ORDER BY sat.talep_tarihi DESC;
    """
    orders = run_db_query(query, fetch="all")
    return {"tedarikci_id": tedarikci_id, "talepler": orders}

# --- API: Gelen Alış Faturaları ---
@app.get("/api/gelen-faturalar")
def get_gelen_faturalar():
    query = """
        SELECT 
            af.id, af.fatura_numarasi, af.fatura_tarihi, af.genel_toplam, af.odeme_durumu,
            COALESCE(t.firma_adi, 'Bilinmeyen Tedarikçi') AS tedarikci_adi
        FROM alis_faturalari af
        LEFT JOIN tedarikciler t ON af.tedarikci_id = t.id
        ORDER BY af.fatura_tarihi DESC, af.id DESC;
    """
    return run_db_query(query, fetch="all")
    
@app.post("/api/gelen-faturalar", status_code=status.HTTP_201_CREATED)
async def create_gelen_fatura(request: Request):
    data = await request.json()
    fatura_bilgileri = data.get('fatura')
    kalemler = data.get('kalemler')
    if not fatura_bilgileri or not kalemler:
        raise HTTPException(status_code=400, detail="Fatura ve kalem bilgileri zorunludur.")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Alış faturasını kaydet
            fatura_sorgu = """
                INSERT INTO alis_faturalari 
                (tedarikci_id, fatura_numarasi, fatura_tarihi, vade_tarihi, toplam_tutar, kdv_tutari, genel_toplam, odeme_durumu, aciklama)
                VALUES (%(tedarikci_id)s, %(fatura_numarasi)s, %(fatura_tarihi)s, %(vade_tarihi)s, %(toplam_tutar)s, %(kdv_tutari)s, %(genel_toplam)s, 'Odenmedi', %(aciklama)s)
                RETURNING id;
            """
            cur.execute(fatura_sorgu, fatura_bilgileri)
            fatura_id = cur.fetchone()['id']
            
            # 2. Fatura kalemlerini kaydet
            for kalem in kalemler:
                kalem['fatura_id'] = fatura_id
                cur.execute("""
                    INSERT INTO alis_fatura_kalemleri
                    (fatura_id, aciklama, miktar, birim, birim_fiyat, kdv_orani, toplam_fiyat)
                    VALUES (%(fatura_id)s, %(aciklama)s, %(miktar)s, %(birim)s, %(birim_fiyat)s, %(kdv_orani)s, %(toplam_fiyat)s);
                """, kalem)

            # 3. Finansal işlemi oluştur (Tedarikçiye olan borcu artırır)
            finans_sorgu = """
                INSERT INTO finansal_islemler (islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi)
                VALUES (%(islem_tarihi)s, 'gider', %(aciklama)s, %(miktar)s, %(ilgili_cari_id)s, 'tedarikci');
            """
            cur.execute(finans_sorgu, {
                'islem_tarihi': fatura_bilgileri['fatura_tarihi'],
                'aciklama': f"{fatura_bilgileri['fatura_numarasi']} nolu alış faturası", 
                'miktar': fatura_bilgileri['genel_toplam'],
                'ilgili_cari_id': fatura_bilgileri['tedarikci_id']
            })
            
            conn.commit()
            return {"message": "Gelen fatura ve finansal işlem başarıyla kaydedildi.", "fatura_id": fatura_id}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Gelen fatura kaydı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Fatura kaydedilirken bir sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)

# --- API: Sevkiyat Yönetimi ---
UPLOAD_DIRECTORY = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@app.post("/api/sevkiyatlar", status_code=status.HTTP_201_CREATED)
# DEĞİŞİKLİK: Parametrelerin Form'dan geleceğini belirtiyoruz.
async def create_sevkiyat(
    satis_siparis_id: int = Form(...), 
    kargo_firmasi: str = Form(...), 
    sevk_tarihi: str = Form(...), 
    takip_numarasi: str = Form(""), 
    notlar: str = Form(""), 
    kargo_fisi: Optional[UploadFile] = File(None)
):
    kargo_fisi_path = None
    if kargo_fisi and kargo_fisi.filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        safe_filename = f"{timestamp}_{kargo_fisi.filename}"
        file_location = os.path.join(UPLOAD_DIRECTORY, safe_filename)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(kargo_fisi.file, file_object)
        kargo_fisi_path = f"/static/uploads/{safe_filename}"
    
    query = """
        INSERT INTO sevkiyatlar 
        (satis_siparis_id, kargo_firmasi, sevk_tarihi, takip_numarasi, notlar, kargo_fisi_path, durum)
        VALUES (%(satis_siparis_id)s, %(kargo_firmasi)s, %(sevk_tarihi)s, %(takip_numarasi)s, %(notlar)s, %(kargo_fisi_path)s, 'Sevk Edildi');
    """
    params = {
        "satis_siparis_id": satis_siparis_id, 
        "kargo_firmasi": kargo_firmasi, 
        "sevk_tarihi": sevk_tarihi, 
        "takip_numarasi": takip_numarasi, 
        "notlar": notlar, 
        "kargo_fisi_path": kargo_fisi_path
    }
    run_db_query(query, params=params)
    run_db_query("UPDATE satis_siparisleri SET durum = 'Sevk Edildi' WHERE id = %s", params=(satis_siparis_id,))
    
    return {"message": "Sevkiyat başarıyla kaydedildi."}

@app.get("/api/sevkiyatlar")
def get_sevkiyatlar():
    # ... Bu fonksiyon aynı kalıyor ...
    query = """
        SELECT 
            s.id, s.kargo_firmasi, s.takip_numarasi, s.sevk_tarihi, ss.durum, s.kargo_fisi_path, 
            ss.siparis_kodu, m.ad as musteri_adi, ss.id as satis_siparis_id
        FROM sevkiyatlar s
        RIGHT JOIN satis_siparisleri ss ON s.satis_siparis_id = ss.id
        JOIN musteriler m ON ss.musteri_id = m.id
        WHERE ss.durum IN ('Onaylandı', 'Sevk Edildi')
        ORDER BY ss.siparis_tarihi DESC, s.id DESC;
    """
    return run_db_query(query, fetch="all")

# ... (diğer sevkiyat fonksiyonları aynı kalıyor)

@app.get("/api/sevkiyat/{sevkiyat_id}")
def get_sevkiyat_detaylari(sevkiyat_id: int):
    sorgu = """
        SELECT 
            s.id as sevkiyat_id, s.kargo_firmasi, s.takip_numarasi, s.sevk_tarihi, s.notlar, s.kargo_fisi_path,
            ss.id as siparis_id, ss.siparis_kodu, ss.siparis_tarihi,
            m.ad as musteri_adi, m.adres as musteri_adres, m.telefon as musteri_telefon,
            json_agg(json_build_object('urun_kodu', u.urun_kodu, 'urun_adi', u.urun_adi, 'miktar', sk.miktar, 'birim', sk.birim)) as kalemler
        FROM sevkiyatlar s
        JOIN satis_siparisleri ss ON s.satis_siparis_id = ss.id
        JOIN musteriler m ON ss.musteri_id = m.id
        LEFT JOIN siparis_kalemleri sk ON ss.id = sk.siparis_id
        LEFT JOIN urunler u ON sk.urun_id = u.id
        WHERE s.id = %s
        GROUP BY s.id, ss.id, m.id;
    """
    result = run_db_query(sorgu, params=(sevkiyat_id,), fetch="one")
    if not result:
        raise HTTPException(status_code=404, detail="Sevkiyat bulunamadı.")
    
    sevkiyat_data = dict(result)
    kalemler_data = sevkiyat_data.pop('kalemler', [])
    if kalemler_data == [None]: kalemler_data = []

    return {"sevkiyat": sevkiyat_data, "kalemler": kalemler_data}

# --- API: Sistem Yönetimi ---
@app.post("/api/sistem/test-verilerini-sifirla", status_code=status.HTTP_200_OK)
def sifirla_test_verileri():
    silinecek_tablolar = ["uretim_lot_kullanimi", "uretim_emirleri", "siparis_kalemleri", "satis_siparisleri", "alis_fatura_kalemleri", "alis_faturalari", "sevkiyatlar", "satin_alma_talepleri", "finansal_islemler", "maas_bordrolari", "personel_giris_cikis", "personel_vardiyalari", "kalite_kontrol", "enerji_tuketimi", "hammadde_girisleri"]
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for tablo in silinecek_tablolar:
                cur.execute(f"TRUNCATE TABLE {tablo} RESTART IDENTITY CASCADE;")
                print(f"{tablo} tablosu temizlendi.")
            conn.commit()
        return {"message": "Tüm test verileri başarıyla sıfırlandı."}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Test verileri sıfırlanırken hata oluştu: {e}")
        raise HTTPException(status_code=500, detail=f"Veritabanı sıfırlanırken bir hata oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)
@app.post("/api/sistem/ornek-veri-ekle", status_code=status.HTTP_201_CREATED)
def ornek_veri_ekle():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            tum_tablolar = ["uretim_lot_kullanimi", "uretim_emirleri", "siparis_kalemleri", "satis_siparisleri", "alis_fatura_kalemleri", "alis_faturalari", "sevkiyatlar", "satin_alma_talepleri", "finansal_islemler", "maas_bordrolari", "personel_giris_cikis", "personel_vardiyalari", "kalite_kontrol", "enerji_tuketimi", "hammadde_girisleri", "urun_receteleri", "urunler", "hammaddeler", "kaliplar", "musteriler", "tedarikciler", "personel", "makineler", "vardiyalar"]
            for tablo in sorted(tum_tablolar, reverse=True):
                cur.execute(f"TRUNCATE TABLE {tablo} RESTART IDENTITY CASCADE;")
            cur.execute("INSERT INTO makineler (makine_adi) VALUES ('CNC Torna'), ('Enjeksiyon Pres 1'), ('Montaj Hattı');")
            cur.execute("INSERT INTO vardiyalar (vardiya_adi, baslangic_saati, bitis_saati) VALUES ('Sabah', '08:00', '16:00'), ('Akşam', '16:00', '00:00');")
            cur.execute("INSERT INTO hammaddeler (hammadde_kodu, hammadde_adi, stok_miktari, birim, kritik_stok_seviyesi) VALUES ('PP-01', 'Polipropilen Granül', 1000, 'kg', 200), ('STL-01', 'Çelik Levha', 500, 'adet', 50), ('BOYA-01', 'Mavi Boya', 50, 'litre', 10);")
            cur.execute("INSERT INTO urunler (urun_kodu, urun_adi, stok_miktari) VALUES ('UR-001', 'Plastik Kasa', 150), ('UR-002', 'Metal Braket', 200);")
            cur.execute("INSERT INTO urun_receteleri (urun_id, hammadde_id, miktar) VALUES (1, 1, 2.5), (1, 3, 0.1), (2, 2, 1);")
            cur.execute("INSERT INTO musteriler (ad, adres, telefon, vergi_dairesi, vergi_no) VALUES ('ABC İnşaat', 'Ankara', '5551112233', 'Ankara VD', '1112223344');")
            cur.execute("INSERT INTO tedarikciler (firma_adi, yetkili_kisi, vergi_dairesi, vergi_no) VALUES ('Petkim Petrokimya', 'Ali Veli', 'İzmir VD', '5556667788');")
            cur.execute("INSERT INTO personel (ad_soyad, pozisyon, ise_giris_tarihi, net_maas) VALUES ('Ahmet Yılmaz', 'Operatör', '2023-01-15', 18000);")
            conn.commit()
            return {"message": "Sistem temizlendi ve örnek veriler başarıyla eklendi."}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Örnek veri eklenirken hata oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)  
# --- API: Finans ---

@app.get("/api/finansal-islemler/{cari_tipi}/{cari_id}")
def get_cari_hesap_ozeti(cari_tipi: str, cari_id: int):
    if cari_tipi not in ['musteri', 'tedarikci']:
        raise HTTPException(status_code=400, detail="Geçersiz cari tipi.")
    
    sorgu = """
        SELECT islem_tarihi, aciklama, miktar 
        FROM finansal_islemler 
        WHERE cari_tipi = %s AND ilgili_cari_id = %s
        ORDER BY islem_tarihi DESC, id DESC;
    """
    return run_db_query(sorgu, params=(cari_tipi, cari_id), fetch="all")

@app.post("/api/finansal-islemler", status_code=status.HTTP_201_CREATED)
async def create_finansal_islem(request: Request):
    data = await request.json()
    if not all(k in data for k in ['islem_tarihi', 'islem_tipi', 'miktar', 'ilgili_cari_id']): 
        raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    
    # islem_tipi formdan 'gelir' (tahsilat) veya 'gider' (ödeme) olarak gelir.
    # Bu doğrudan veritabanına yazılacak. Hesaplama sorgusu bunu yorumlayacak.
    cari_data = data.get('ilgili_cari_id')
    cari_tipi, ilgili_cari_id = str(cari_data).split('-')
    
    params = {
        "islem_tarihi": data['islem_tarihi'], 
        "islem_tipi": data['islem_tipi'],
        "aciklama": data.get('aciklama'), 
        "miktar": abs(float(data.get('miktar'))), 
        "ilgili_cari_id": int(ilgili_cari_id), 
        "cari_tipi": cari_tipi
    }
    run_db_query("""
        INSERT INTO finansal_islemler (islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi) 
        VALUES (%(islem_tarihi)s, %(islem_tipi)s, %(aciklama)s, %(miktar)s, %(ilgili_cari_id)s, %(cari_tipi)s);
    """, params=params)
    return {"message": "Finansal işlem başarıyla eklendi."}

@app.get("/api/musteri-bakiyeleri")
async def get_musteri_bakiyeleri():
    # Müşteri borcunu hesapla: 'gelir' (fatura) artırır, 'gider' (tahsilat) azaltır.
    query = """
        SELECT m.id, m.ad, 
               COALESCE(SUM(CASE WHEN fi.islem_tipi = 'gelir' THEN fi.miktar WHEN fi.islem_tipi = 'gider' THEN -fi.miktar ELSE 0 END), 0) AS bakiye 
        FROM musteriler m 
        LEFT JOIN finansal_islemler fi ON m.id = fi.ilgili_cari_id AND fi.cari_tipi = 'musteri' 
        GROUP BY m.id, m.ad 
        ORDER BY m.ad;
    """
    return run_db_query(query, fetch="all")

@app.get("/api/tedarikci-bakiyeleri")
async def get_tedarikci_bakiyeleri():
    # Tedarikçi alacağını hesapla: 'gider' (fatura) artırır, 'gelir' (ödeme) azaltır.
    query = """
        SELECT t.id, t.firma_adi, 
               COALESCE(SUM(CASE WHEN fi.islem_tipi = 'gider' THEN fi.miktar WHEN fi.islem_tipi = 'gelir' THEN -fi.miktar ELSE 0 END), 0) AS bakiye 
        FROM tedarikciler t 
        LEFT JOIN finansal_islemler fi ON t.id = fi.ilgili_cari_id AND fi.cari_tipi = 'tedarikci' 
        GROUP BY t.id, t.firma_adi 
        ORDER BY t.firma_adi;
    """
    return run_db_query(query, fetch="all")

@app.post("/api/enerji-tuketimi", status_code=status.HTTP_201_CREATED)
async def create_enerji_tuketimi(request: Request):
    data = await request.json()
    if not all(k in data for k in ['donem', 'enerji_tipi', 'tuketim_miktari', 'birim']): 
        raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    
    # ***** DÜZELTME BURADA: Gelen 'YYYY-MM' formatına '-01' ekleniyor *****
    donem = f"{data['donem']}-01"

    params = {
        "donem": donem,
        "enerji_tipi": data['enerji_tipi'],
        "tuketim_miktari": data['tuketim_miktari'],
        "birim": data['birim']
    }
    run_db_query("""
        INSERT INTO enerji_tuketimi (donem, enerji_tipi, tuketim_miktari, birim) 
        VALUES (%(donem)s, %(enerji_tipi)s, %(tuketim_miktari)s, %(birim)s);
    """, params=params)
    return {"message": "Enerji tüketim kaydı başarıyla eklendi."}

@app.post("/api/enerji-tuketimi", status_code=status.HTTP_201_CREATED)
async def create_enerji_tuketimi(request: Request):
    data = await request.json()
    if not all(k in data for k in ['donem', 'enerji_tipi', 'tuketim_miktari', 'birim']): 
        raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    
    # ***** DÜZELTME BURADA: Gelen 'YYYY-MM' formatına '-01' ekleniyor *****
    donem = f"{data['donem']}-01"

    params = {
        "donem": donem,
        "enerji_tipi": data['enerji_tipi'],
        "tuketim_miktari": data['tuketim_miktari'],
        "birim": data['birim']
    }
    run_db_query("""
        INSERT INTO enerji_tuketimi (donem, enerji_tipi, tuketim_miktari, birim) 
        VALUES (%(donem)s, %(enerji_tipi)s, %(tuketim_miktari)s, %(birim)s);
    """, params=params)
    return {"message": "Enerji tüketim kaydı başarıyla eklendi."}

@app.post("/api/gelen-faturalar", status_code=status.HTTP_201_CREATED)
async def create_gelen_fatura(request: Request):
    data = await request.json()
    fatura_bilgileri = data.get('fatura')
    kalemler = data.get('kalemler')
    if not fatura_bilgileri or not kalemler:
        raise HTTPException(status_code=400, detail="Fatura ve kalem bilgileri zorunludur.")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Alış faturasını kaydet
            fatura_sorgu = """
                INSERT INTO alis_faturalari 
                (tedarikci_id, fatura_numarasi, fatura_tarihi, vade_tarihi, toplam_tutar, kdv_tutari, genel_toplam, odeme_durumu, aciklama)
                VALUES (%(tedarikci_id)s, %(fatura_numarasi)s, %(fatura_tarihi)s, %(vade_tarihi)s, %(toplam_tutar)s, %(kdv_tutari)s, %(genel_toplam)s, 'Odenmedi', %(aciklama)s)
                RETURNING id;
            """
            cur.execute(fatura_sorgu, fatura_bilgileri)
            fatura_id = cur.fetchone()['id']
            
            # Fatura kalemlerini kaydet
            for kalem in kalemler:
                kalem['fatura_id'] = fatura_id
                cur.execute("""
                    INSERT INTO alis_fatura_kalemleri
                    (fatura_id, aciklama, miktar, birim, birim_fiyat, kdv_orani, toplam_fiyat)
                    VALUES (%(fatura_id)s, %(aciklama)s, %(miktar)s, %(birim)s, %(birim_fiyat)s, %(kdv_orani)s, %(toplam_fiyat)s);
                """, kalem)

            # Finansal işlemi oluştur (Tedarikçiye olan borcu artırır, islem_tipi='gider' olmalı)
            finans_sorgu = """
                INSERT INTO finansal_islemler (islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi)
                VALUES (%(islem_tarihi)s, 'gider', %(aciklama)s, %(miktar)s, %(ilgili_cari_id)s, 'tedarikci');
            """
            cur.execute(finans_sorgu, {
                'islem_tarihi': fatura_bilgileri['fatura_tarihi'],
                'aciklama': f"{fatura_bilgileri['fatura_numarasi']} nolu alış faturası", 
                'miktar': fatura_bilgileri['genel_toplam'],
                'ilgili_cari_id': fatura_bilgileri['tedarikci_id']
            })
            
            conn.commit()
            return {"message": "Gelen fatura ve finansal işlem başarıyla kaydedildi.", "fatura_id": fatura_id}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Gelen fatura kaydı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Fatura kaydedilirken bir sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)
# YENİ EKLENDİ: Gelen faturaları ve ilgili finansal işlemi siler.
@app.delete("/api/gelen-faturalar/{fatura_id}", status_code=status.HTTP_200_OK)
def delete_gelen_fatura(fatura_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Önce faturanın numarasını ve ilgili cari bilgilerini alalım (finansal işlemi bulmak için)
            cur.execute("SELECT fatura_numarasi, tedarikci_id FROM alis_faturalari WHERE id = %s", (fatura_id,))
            fatura_info = cur.fetchone()
            if not fatura_info:
                raise HTTPException(status_code=404, detail="Fatura bulunamadı.")
            
            # İlgili finansal işlemi sil
            aciklama = f"{fatura_info['fatura_numarasi']} nolu alış faturası"
            cur.execute("""
                DELETE FROM finansal_islemler 
                WHERE aciklama = %s AND ilgili_cari_id = %s AND cari_tipi = 'tedarikci'
            """, (aciklama, fatura_info['tedarikci_id']))

            # Fatura kalemlerini sil
            cur.execute("DELETE FROM alis_fatura_kalemleri WHERE fatura_id = %s;", (fatura_id,))
            # Ana faturayı sil
            cur.execute("DELETE FROM alis_faturalari WHERE id = %s;", (fatura_id,))
            
            conn.commit()
            return {"message": "Fatura ve ilgili finans kaydı başarıyla silindi."}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Gelen fatura silinirken hata: {e}")
        raise HTTPException(status_code=500, detail=f"Fatura silinirken bir sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)
        
@app.post("/api/finansal-islemler", status_code=status.HTTP_201_CREATED)
async def create_finansal_islem(request: Request):
    data = await request.json()
    if not all(k in data for k in ['islem_tarihi', 'islem_tipi', 'miktar', 'ilgili_cari_id']): 
        raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    
    cari_data = data.get('ilgili_cari_id')
    cari_tipi, ilgili_cari_id = str(cari_data).split('-')
    
    # Gelen islem_tipi'ne göre işlem yap. Bu tip doğrudan veritabanına yazılacak.
    # Bakiye hesaplama sorgusu bu tipleri doğru yorumlayacak.
    params = {
        "islem_tarihi": data['islem_tarihi'], 
        "islem_tipi": data['islem_tipi'], # 'gelir' veya 'gider'
        "aciklama": data.get('aciklama'), 
        "miktar": abs(float(data.get('miktar'))), 
        "ilgili_cari_id": int(ilgili_cari_id), 
        "cari_tipi": cari_tipi
    }
    run_db_query("""
        INSERT INTO finansal_islemler (islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi) 
        VALUES (%(islem_tarihi)s, %(islem_tipi)s, %(aciklama)s, %(miktar)s, %(ilgili_cari_id)s, %(cari_tipi)s);
    """, params=params)
    return {"message": "Finansal işlem başarıyla eklendi."}

# --- API: Akıllı Planlama (MRP) ---
@app.get("/api/planlama")
def get_uretim_planlari():
    sorgu = """
        SELECT 
            up.id, 
            up.plan_adi, 
            up.durum,
            up.olusturma_tarihi,
            ss.siparis_kodu,
            ss.id as satis_id 
        FROM uretim_planlari up
        RIGHT JOIN satis_siparisleri ss ON up.satis_id = ss.id
        WHERE ss.durum = 'Onaylandı'
        ORDER BY ss.siparis_tarihi DESC;
    """
    return run_db_query(sorgu, fetch="all")

@app.post("/api/planlama", status_code=status.HTTP_201_CREATED)
def create_uretim_plani(plan_data: UretimPlanCreate):
    satis_id = plan_data.satis_id
    plan_adi = plan_data.plan_adi
    
    # İlgili satış siparişinin zaten bir plana dahil olup olmadığını kontrol et
    mevcut_plan = run_db_query("SELECT id FROM uretim_planlari WHERE satis_id = %s", params=(satis_id,), fetch="one")
    if mevcut_plan:
        raise HTTPException(status_code=409, detail="Bu satış siparişi için zaten bir üretim planı oluşturulmuş.")

    # Yeni üretim planını veritabanına oluştur
    plan_params = {
        "plan_adi": plan_adi,
        "satis_id": satis_id,
        "durum": "Planlandı"
    }
    run_db_query("""
        INSERT INTO uretim_planlari (plan_adi, satis_id, durum)
        VALUES (%(plan_adi)s, %(satis_id)s, %(durum)s);
    """, params=plan_params)

    return {"message": f"'{plan_adi}' kodlu üretim planı başarıyla oluşturuldu!"}

@app.get("/api/planlama/analiz")
def analyze_for_mrp():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            talep_sorgusu = "SELECT sk.urun_id, u.urun_adi, SUM(sk.miktar) AS toplam_talep FROM siparis_kalemleri sk JOIN satis_siparisleri ss ON sk.siparis_id = ss.id JOIN urunler u ON sk.urun_id = u.id WHERE ss.durum = 'Onaylandı' GROUP BY sk.urun_id, u.urun_adi;"
            cur.execute(talep_sorgusu)
            tum_talepler = cur.fetchall()
            uretim_onerileri = []
            if tum_talepler:
                urun_idler = [t['urun_id'] for t in tum_talepler]
                cur.execute("SELECT id, stok_miktari FROM urunler WHERE id = ANY(%s);", (urun_idler,))
                stok_verileri = {stok['id']: stok['stok_miktari'] for stok in cur.fetchall()}
                for talep in tum_talepler:
                    mevcut_stok = stok_verileri.get(talep['urun_id'], 0)
                    uretim_ihtiyaci = talep['toplam_talep'] - mevcut_stok
                    if uretim_ihtiyaci > 0:
                        uretim_onerileri.append({"urun_id": talep['urun_id'], "urun_adi": talep['urun_adi'], "toplam_talep": talep['toplam_talep'], "mevcut_stok": mevcut_stok, "uretim_ihtiyaci": uretim_ihtiyaci})
            toplam_hammadde_ihtiyaci = {}
            if uretim_onerileri:
                uretim_yapilacak_urun_idler = [uo['urun_id'] for uo in uretim_onerileri]
                cur.execute("SELECT urun_id, hammadde_id, miktar FROM urun_receteleri WHERE urun_id = ANY(%s);", (uretim_yapilacak_urun_idler,))
                receteler = cur.fetchall()
                recete_map = {}
                for r in receteler:
                    if r['urun_id'] not in recete_map: recete_map[r['urun_id']] = []
                    recete_map[r['urun_id']].append({'hammadde_id': r['hammadde_id'], 'miktar': r['miktar']})
                for uretim in uretim_onerileri:
                    if uretim['urun_id'] in recete_map:
                        for recete_item in recete_map[uretim['urun_id']]:
                            gereken = uretim['uretim_ihtiyaci'] * recete_item['miktar']
                            h_id = recete_item['hammadde_id']
                            toplam_hammadde_ihtiyaci[h_id] = toplam_hammadde_ihtiyaci.get(h_id, 0) + gereken
            satin_alma_onerileri = []
            if toplam_hammadde_ihtiyaci:
                hammadde_idler = list(toplam_hammadde_ihtiyaci.keys())
                cur.execute("SELECT id, hammadde_adi, stok_miktari, birim FROM hammaddeler WHERE id = ANY(%s);", (hammadde_idler,))
                hammadde_stok_verileri = {h['id']: h for h in cur.fetchall()}
                for hammadde_id, toplam_gereken in toplam_hammadde_ihtiyaci.items():
                    hammadde_bilgisi = hammadde_stok_verileri.get(hammadde_id)
                    if hammadde_bilgisi:
                        mevcut_stok = hammadde_bilgisi.get('stok_miktari', 0)
                        satin_alma_ihtiyaci = toplam_gereken - mevcut_stok
                        if satin_alma_ihtiyaci > 0:
                            satin_alma_onerileri.append({"hammadde_id": hammadde_id, "hammadde_adi": hammadde_bilgisi['hammadde_adi'], "toplam_gereken": round(toplam_gereken, 2), "mevcut_stok": mevcut_stok, "satin_alma_ihtiyaci": round(satin_alma_ihtiyaci, 2), "birim": hammadde_bilgisi['birim']})
            return {"uretim_onerileri": uretim_onerileri, "satin_alma_onerileri": satin_alma_onerileri}
    except Exception as e:
        print(f"MRP Analiz Hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Analiz sırasında sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn) 

# --- UYGULAMA BAŞLANGIÇ AYARLARI ---
@app.on_event("startup")
def create_initial_settings():
    """Uygulama başladığında temel sistem ayarlarının mevcut olduğundan emin olur."""
    conn = None
    try:
        required_settings = [
            {'key': 'firma_adi', 'value': 'Düğmeci Makina San. ve Tic. A.Ş.', 'desc': 'Fiş ve faturalarda görünecek resmi firma adı'},
            {'key': 'firma_adresi', 'value': 'Organize Sanayi Bölgesi, 12. Cadde No: 34, Kayseri', 'desc': 'Firmanın tam adresi'},
            {'key': 'firma_telefon', 'value': '0352 123 45 67', 'desc': 'Firmanın telefon numarası'},
            {'key': 'firma_email', 'value': 'info@dugmecimakina.com', 'desc': 'Firmanın e-posta adresi'},
            {'key': 'firma_logo_yolu', 'value': '/static/logo.png', 'desc': 'Fişlerde kullanılacak firma logosunun yolu'},
            # YENİ: Yetkili kişi ayarı eklendi
            {'key': 'firma_yetkili_kisi', 'value': 'Akın Sümengen', 'desc': 'Tekliflerde görünecek yetkili kişi adı'},
            {'key': 'maas_sifresi', 'value': '656514', 'desc': 'Maaş yönetimi sayfasına erişim şifresi'},
            
            {'key': 'firma_website', 'value': 'https://www.google.com', 'desc': 'QR Kod için kullanılacak web sitesi adresi'},
            
            {'key': 'birim_maliyet_elektrik', 'value': '4.55', 'desc': 'Elektrik için kWh başına maliyet (TL)'},
            {'key': 'birim_maliyet_dogalgaz', 'value': '12.80', 'desc': 'Doğalgaz için m³ başına maliyet (TL)'},
            {'key': 'birim_maliyet_su', 'value': '9.75', 'desc': 'Su için m³ başına maliyet (TL)'}
        ]
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            for setting in required_settings:
                cur.execute("""
                    INSERT INTO sistem_ayarlari (ayar_anahtari, ayar_degeri, aciklama)
                    VALUES (%(key)s, %(value)s, %(desc)s)
                    ON CONFLICT (ayar_anahtari) DO NOTHING;
                """, setting)
        conn.commit()
        print("Gerekli sistem ayarları kontrol edildi ve eksikler eklendi.")
    except Exception as e:
        if conn: conn.rollback()
        print(f"Başlangıç ayarları oluşturulurken hata oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)
# --- BAŞLANGIÇ AYARLARI SONU ---

# --- API: Enerji Yönetimi ---
@app.get("/api/enerji-tuketimi")
def get_enerji_tuketimi():
    try:
        ayarlar_query = "SELECT ayar_anahtari, ayar_degeri FROM sistem_ayarlari WHERE ayar_anahtari LIKE 'birim_maliyet_%'"
        maliyet_ayarlari = run_db_query(ayarlar_query, fetch="all")
        
        birim_maliyetler = {
            ayar['ayar_anahtari'].split('_')[-1].capitalize(): float(ayar['ayar_degeri'])
            for ayar in maliyet_ayarlari
        }
    except Exception as e:
        print(f"Birim maliyet ayarları okunurken hata: {e}")
        birim_maliyetler = {}

    sorgu = "SELECT *, TO_CHAR(donem, 'YYYY-MM') as donem_str FROM enerji_tuketimi ORDER BY donem DESC;"
    tuketimler = run_db_query(sorgu, fetch="all")

    if tuketimler:
        for tuketim in tuketimler:
            enerji_tipi = tuketim.get('enerji_tipi')
            maliyet = birim_maliyetler.get(enerji_tipi, 0)
            tuketim_miktari = tuketim.get('tuketim_miktari', 0)
            tuketim['toplam_maliyet'] = float(tuketim_miktari) * maliyet
    
    return tuketimler

@app.post("/api/enerji-tuketimi", status_code=status.HTTP_201_CREATED)
async def create_or_update_enerji_tuketimi(request: Request):
    data = await request.json()
    if not all(k in data for k in ['donem', 'enerji_tipi', 'tuketim_miktari', 'birim']): 
        raise HTTPException(status_code=400, detail="Tüm alanlar zorunludur.")
    
    donem = f"{data['donem']}-01"

    params = {
        "donem": donem,
        "enerji_tipi": data['enerji_tipi'],
        "tuketim_miktari": data['tuketim_miktari'],
        "birim": data['birim']
    }
    
    # YENİ VE AKILLI SORGU:
    # Eğer (donem, enerji_tipi) ikilisi mevcutsa YENİ KAYIT EKLEMEZ,
    # bunun yerine mevcut kaydın miktarını ve birimini GÜNCELLER.
    upsert_query = """
        INSERT INTO enerji_tuketimi (donem, enerji_tipi, tuketim_miktari, birim) 
        VALUES (%(donem)s, %(enerji_tipi)s, %(tuketim_miktari)s, %(birim)s)
        ON CONFLICT (donem, enerji_tipi) 
        DO UPDATE SET 
            tuketim_miktari = EXCLUDED.tuketim_miktari,
            birim = EXCLUDED.birim;
    """
    try:
        run_db_query(upsert_query, params=params)
        return {"message": "Enerji tüketim kaydı başarıyla kaydedildi veya güncellendi."}
    except Exception as e:
        # run_db_query zaten genel hataları yakalıyor ama bu özel bir durum olabilir.
        raise HTTPException(status_code=500, detail=f"Kayıt işlemi sırasında bir hata oluştu: {e}")


@app.delete("/api/enerji-tuketimi/{kayit_id}")
def delete_enerji_tuketimi(kayit_id: int):
    result = run_db_query("DELETE FROM enerji_tuketimi WHERE id = %s RETURNING id;", params=(kayit_id,), fetch="one")
    if result is None: 
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    return {"message": "Enerji tüketim kaydı başarıyla silindi."}

@app.get("/api/enerji-raporu")
def get_enerji_raporu():
    sorgu = "SELECT donem, enerji_tipi, SUM(tuketim_miktari) as toplam_tuketim FROM enerji_tuketimi GROUP BY donem, enerji_tipi ORDER BY donem;"
    return run_db_query(sorgu, fetch="all")

@app.put("/api/personel/{personel_id}")
async def update_personel(personel_id: int, request: Request):
    data = await request.json()
    data['id'] = personel_id
    if not data.get('ad_soyad'): 
        raise HTTPException(status_code=400, detail="Ad Soyad alanı zorunludur.")
    
    # GÜNCELLENMİŞ SORGUS: Yeni eklenen tüm alanları UPDATE sorgusuna dahil ediyoruz.
    sorgu = """
        UPDATE personel SET 
            ad_soyad=%(ad_soyad)s, 
            pozisyon=%(pozisyon)s, 
            ise_giris_tarihi=%(ise_giris_tarihi)s,
            net_maas=%(net_maas)s,
            tc_kimlik_no=%(tc_kimlik_no)s,
            dogum_tarihi=%(dogum_tarihi)s,
            telefon=%(telefon)s,
            adres=%(adres)s
        WHERE id=%(id)s RETURNING id;
    """
    
    # Eksik gelebilecek alanlar için varsayılan None değerini atıyoruz.
    data.setdefault('net_maas', None)
    data.setdefault('tc_kimlik_no', None)
    data.setdefault('dogum_tarihi', None)
    data.setdefault('telefon', None)
    data.setdefault('adres', None)

    result = run_db_query(sorgu, params=data, fetch="one")

    if result is None: 
        raise HTTPException(status_code=404, detail="Personel bulunamadı.")
    
    return {"message": "Personel bilgileri başarıyla güncellendi."}

@app.get("/api/finansal-ozet")
def get_finansal_ozet():
    # Tek bir sorguda hem toplam geliri hem de toplam gideri hesaplıyoruz.
    # COALESCE fonksiyonu, eğer hiç kayıt yoksa ve sonuç NULL dönerse, 0 olarak kabul etmemizi sağlar.
    sorgu = """
        SELECT
            COALESCE(SUM(miktar) FILTER (WHERE islem_tipi = 'gelir'), 0) AS toplam_gelir,
            COALESCE(SUM(miktar) FILTER (WHERE islem_tipi = 'gider'), 0) AS toplam_gider
        FROM finansal_islemler;
    """
    sonuc = run_db_query(sorgu, fetch="one")
    
    if sonuc:
        toplam_gelir = sonuc.get('toplam_gelir', 0)
        toplam_gider = sonuc.get('toplam_gider', 0)
        bakiye = toplam_gelir - toplam_gider
        
        return {
            "toplam_gelir": toplam_gelir,
            "toplam_gider": toplam_gider,
            "bakiye": bakiye
        }
    
    # Herhangi bir hata durumunda varsayılan değerleri dön
    return {"toplam_gelir": 0, "toplam_gider": 0, "bakiye": 0}

@app.get("/api/satis-fisleri")
def get_satis_fisleri():
    # Sorgu basitleştirildi, artık ürünleri (kalemler) içermiyor.
    query = """
        SELECT ss.id, ss.siparis_kodu, ss.siparis_tarihi, ss.genel_toplam, ss.durum, 
        COALESCE(m.ad, 'Bilinmeyen Müşteri') AS musteri_adi 
        FROM satis_siparisleri ss 
        LEFT JOIN musteriler m ON ss.musteri_id = m.id 
        ORDER BY ss.siparis_tarihi DESC, ss.id DESC;
    """
    return run_db_query(query, fetch="all")

@app.get("/api/satis-fisleri/{siparis_id}")
def get_satis_fisi_detay(siparis_id: int):
    # Ana fiş bilgilerini çekiyoruz
    fis_sorgu = """
        SELECT ss.*, m.ad as musteri_adi, m.adres, m.telefon, m.vergi_dairesi, m.vergi_no 
        FROM satis_siparisleri ss 
        JOIN musteriler m ON ss.musteri_id = m.id WHERE ss.id = %s;
    """
    fis_detay = run_db_query(fis_sorgu, params=(siparis_id,), fetch="one")
    
    if not fis_detay:
        raise HTTPException(status_code=404, detail="Satış fişi bulunamadı.")
    
    # Fişe ait ürün kalemlerini çekiyoruz
    kalem_sorgu = """
        SELECT sk.miktar, sk.birim_fiyat, u.urun_adi 
        FROM siparis_kalemleri sk 
        JOIN urunler u ON sk.urun_id = u.id 
        WHERE sk.siparis_id = %s;
    """
    fis_kalemleri = run_db_query(kalem_sorgu, params=(siparis_id,), fetch="all")
    
    # İki sonucu birleştirip döndürüyoruz
    return {"fis": fis_detay, "kalemler": fis_kalemleri}

@app.post("/api/gelen-faturalar/{fatura_id}/odeme", status_code=status.HTTP_200_OK)
def odeme_yap(fatura_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Faturanın mevcut durumunu ve bilgilerini al
            cur.execute("SELECT * FROM alis_faturalari WHERE id = %s", (fatura_id,))
            fatura = cur.fetchone()

            if not fatura:
                raise HTTPException(status_code=404, detail="Fatura bulunamadı.")
            if fatura['odeme_durumu'] == 'Ödendi':
                raise HTTPException(status_code=400, detail="Bu fatura zaten ödenmiş.")

            # 2. Faturanın durumunu 'Ödendi' olarak güncelle
            cur.execute("UPDATE alis_faturalari SET odeme_durumu = 'Ödendi' WHERE id = %s", (fatura_id,))
            
            # 3. Ödemeyi finansal işlemlere 'gider' olarak kaydet
            # Not: Fatura geldiğinde tedarikçiye borç (gider) oluşmuştu. Ödeme yapıldığında kasadan para çıktığı için bu da bir giderdir.
            # Cari hesap özetinde bu iki işlem birbirini dengeleyecektir.
            # DÜZELTME: Fatura geldiğinde borcu artırmak için 'gider' işlemi yapmıştık. Ödeme yaptığımızda borcu azaltmak için 'gelir' işlemi yapmalıyız.
            # Tedarikçi açısından bakıldığında, bizden alacağı (onun geliri) azalmış olur.
            # Kafa karışıklığını önlemek için en doğrusu: Fatura bir borç (gider), ödeme ise bu borcu kapatan bir işlem (tahsilat/tediye)
            # Tedarikçi bakiyesini doğru hesaplamak için ödemeyi 'gelir' olarak kaydedelim ki 'gider'i sıfırlasın.
            
            finans_sorgu = """
                INSERT INTO finansal_islemler (islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi)
                VALUES (CURRENT_DATE, 'gelir', %(aciklama)s, %(miktar)s, %(ilgili_cari_id)s, 'tedarikci');
            """
            cur.execute(finans_sorgu, {
                'aciklama': f"{fatura['fatura_numarasi']} nolu faturanın ödemesi", 
                'miktar': fatura['genel_toplam'],
                'ilgili_cari_id': fatura['tedarikci_id']
            })

            conn.commit()
            return {"message": "Fatura başarıyla 'Ödendi' olarak işaretlendi ve finansal kayıt oluşturuldu."}

    except HTTPException as http_exc:
        if conn: conn.rollback()
        raise http_exc # HTTP hatalarını doğrudan yükselt
    except Exception as e:
        if conn: conn.rollback()
        print(f"Ödeme yapılırken hata: {e}")
        raise HTTPException(status_code=500, detail=f"Ödeme kaydedilirken bir sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)
        
@app.get("/api/gelen-faturalar/{fatura_id}")
def get_gelen_fatura_detay(fatura_id: int):
    fatura_sorgu = """
        SELECT af.*, t.firma_adi, t.vergi_dairesi, t.vergi_no
        FROM alis_faturalari af
        JOIN tedarikciler t ON af.tedarikci_id = t.id
        WHERE af.id = %s;
    """
    fatura_detay = run_db_query(fatura_sorgu, params=(fatura_id,), fetch="one")

    if not fatura_detay:
        raise HTTPException(status_code=404, detail="Fatura bulunamadı.")

    kalem_sorgu = "SELECT * FROM alis_fatura_kalemleri WHERE fatura_id = %s;"
    fatura_kalemleri = run_db_query(kalem_sorgu, params=(fatura_id,), fetch="all")

    return {"fatura": fatura_detay, "kalemler": fatura_kalemleri} 


# YENİ: Logo yükleme endpoint'i
@app.post("/api/ayarlar/logo-yukle", status_code=status.HTTP_200_OK)
async def upload_logo(logo: UploadFile = File(...)):
    # Logo dosyasını static klasörüne kaydediyoruz
    logo_path = os.path.join(BASE_DIR, "static", "logo.png")
    with open(logo_path, "wb") as buffer:
        shutil.copyfileobj(logo.file, buffer)
    
    # Dosya yolunu veritabanındaki ayarlara kaydediyoruz
    run_db_query(
        "UPDATE sistem_ayarlari SET ayar_degeri = '/static/logo.png' WHERE ayar_anahtari = 'firma_logo_yolu';"
    )
    return {"message": "Logo başarıyla güncellendi.", "path": "/static/logo.png"}

@app.get("/api/satis-fisleri/{siparis_id}")
def get_satis_fisi_detay(siparis_id: int):
    # GÜNCELLEME: Tüm şirket ayarlarını tek seferde çekiyoruz
    sirket_ayarlari_raw = run_db_query(
        "SELECT ayar_anahtari, ayar_degeri FROM sistem_ayarlari WHERE ayar_anahtari LIKE 'firma_%'", 
        fetch="all"
    )
    sirket_bilgileri = {ayar['ayar_anahtari']: ayar['ayar_degeri'] for ayar in sirket_ayarlari_raw}

    fis_sorgu = "SELECT ss.*, m.ad as musteri_adi, m.adres, m.telefon, m.vergi_dairesi, m.vergi_no FROM satis_siparisleri ss JOIN musteriler m ON ss.musteri_id = m.id WHERE ss.id = %s;"
    fis_detay = run_db_query(fis_sorgu, params=(siparis_id,), fetch="one")
    
    if not fis_detay:
        raise HTTPException(status_code=404, detail="Satış fişi bulunamadı.")
    
    kalem_sorgu = "SELECT sk.miktar, sk.birim_fiyat, u.urun_adi FROM siparis_kalemleri sk JOIN urunler u ON sk.urun_id = u.id WHERE sk.siparis_id = %s;"
    fis_kalemleri = run_db_query(kalem_sorgu, params=(siparis_id,), fetch="all")
    
    # GÜNCELLEME: Şirket bilgilerini de yanıta ekliyoruz
    return {"fis": fis_detay, "kalemler": fis_kalemleri, "sirket": sirket_bilgileri}  

# --- API: Satış Siparişleri & Fişleri ---

@app.get("/api/satis-fisleri/{siparis_id}")
def get_satis_fisi_detay(siparis_id: int):
    # Bu fonksiyon, hem satış fişleri listesindeki detaylar hem de fiş yazdırma için kullanılacak
    sirket_ayarlari_raw = run_db_query(
        "SELECT ayar_anahtari, ayar_degeri FROM sistem_ayarlari WHERE ayar_anahtari LIKE 'firma_%'", 
        fetch="all"
    )
    sirket_bilgileri = {ayar['ayar_anahtari']: ayar['ayar_degeri'] for ayar in sirket_ayarlari_raw}

    fis_sorgu = "SELECT ss.*, m.ad as musteri_adi, m.adres, m.telefon, m.vergi_dairesi, m.vergi_no FROM satis_siparisleri ss JOIN musteriler m ON ss.musteri_id = m.id WHERE ss.id = %s;"
    fis_detay = run_db_query(fis_sorgu, params=(siparis_id,), fetch="one")
    
    if not fis_detay:
        raise HTTPException(status_code=404, detail="Satış fişi bulunamadı.")
    
    kalem_sorgu = "SELECT sk.miktar, sk.birim_fiyat, sk.kdv_orani, u.urun_adi FROM siparis_kalemleri sk JOIN urunler u ON sk.urun_id = u.id WHERE sk.siparis_id = %s;"
    fis_kalemleri = run_db_query(kalem_sorgu, params=(siparis_id,), fetch="all")
    
    return {"fis": fis_detay, "kalemler": fis_kalemleri, "sirket": sirket_bilgileri}

@app.get("/api/satis-fisleri")
def get_satis_fisleri():
    # Bu fonksiyon, sadece ana listeyi çeker. Detaylar tıklandığında yukarıdaki fonksiyon çağrılır.
    query = """
        SELECT ss.id, ss.siparis_kodu, ss.siparis_tarihi, ss.genel_toplam, ss.durum, 
        COALESCE(m.ad, 'Bilinmeyen Müşteri') AS musteri_adi 
        FROM satis_siparisleri ss 
        LEFT JOIN musteriler m ON ss.musteri_id = m.id 
        ORDER BY ss.siparis_tarihi DESC, ss.id DESC;
    """
    return run_db_query(query, fetch="all")
    
@app.post("/api/satis-fisleri", status_code=status.HTTP_201_CREATED, summary="Finansal Etkili Satış Fişi Oluşturur")
async def create_satis_fisi(request: Request):
    data = await request.json()
    siparis_bilgileri = data.get('siparis')
    kalemler = data.get('kalemler')
    if not siparis_bilgileri or not kalemler:
        raise HTTPException(status_code=400, detail="Sipariş ve kalem bilgileri zorunludur.")
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. SATIŞ SİPARİŞİNİ KAYDET
            siparis_sorgu = """
                INSERT INTO satis_siparisleri (musteri_id, siparis_kodu, siparis_tarihi, durum, toplam_tutar, kdv_tutari, genel_toplam) 
                VALUES (%(musteri_id)s, %(siparis_kodu)s, CURRENT_DATE, 'Onaylandı', %(toplam_tutar)s, %(kdv_tutari)s, %(genel_toplam)s) RETURNING id;
            """
            cur.execute(siparis_sorgu, siparis_bilgileri)
            siparis_id = cur.fetchone()['id']
            
            # 2. SİPARİŞ KALEMLERİNİ KAYDET VE ÜRETİM EMRİ OLUŞTUR
            for kalem in kalemler:
                kalem['siparis_id'] = siparis_id
                kalem_sorgu = """
                    INSERT INTO siparis_kalemleri (siparis_id, urun_id, miktar, birim_fiyat, kdv_orani, toplam_fiyat, birim)
                    VALUES (%(siparis_id)s, %(urun_id)s, %(miktar)s, %(birim_fiyat)s, %(kdv_orani)s, %(toplam_fiyat)s, 'Adet');
                """
                cur.execute(kalem_sorgu, kalem)
                
                # Üretim Emri Oluşturma (İsteğe bağlı, mevcut mantığınızı koruyoruz)
                is_emri_kodu = f"FIS-{siparis_id}-URUN-{kalem['urun_id']}"
                uretim_params = { 'is_emri_kodu': is_emri_kodu, 'urun_id': kalem['urun_id'], 'hedef_miktar': kalem['miktar'] }
                cur.execute("INSERT INTO uretim_emirleri (is_emri_kodu, urun_id, hedef_miktar, durum) VALUES (%(is_emri_kodu)s, %(urun_id)s, %(hedef_miktar)s, 'Bekliyor');", uretim_params)

            # 3. FİNANSAL İŞLEMİ OLUŞTUR (MÜŞTERİ CARİSİNE BORÇ EKLE)
            # Bu satış, müşteri için bir 'gelir' (borç) oluşturur.
            finans_sorgu = """
                INSERT INTO finansal_islemler (islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi)
                VALUES (CURRENT_DATE, 'gelir', %(aciklama)s, %(miktar)s, %(ilgili_cari_id)s, 'musteri');
            """
            cur.execute(finans_sorgu, {
                'aciklama': f"{siparis_bilgileri['siparis_kodu']} nolu satış", 
                'miktar': siparis_bilgileri['genel_toplam'], 
                'ilgili_cari_id': siparis_bilgileri['musteri_id']
            })
            
            conn.commit()
            return {"message": "Satış fişi başarıyla oluşturuldu ve müşteri carisine işlendi.", "siparis_id": siparis_id}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Satış fişi kaydı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Fiş kaydedilirken bir sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn) 
        
# =================================================================
# --- API: Teklif Yönetimi ---
# =================================================================

@app.post("/api/teklifler", status_code=status.HTTP_201_CREATED)
async def create_teklif(request: Request):
    data = await request.json()
    teklif_bilgileri = data.get('teklif')
    kalemler = data.get('kalemler')

    if not teklif_bilgileri or not kalemler:
        raise HTTPException(status_code=400, detail="Teklif ve kalem bilgileri zorunludur.")

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Ana teklif kaydını oluştur ve yeni ID'yi al
            teklif_sorgu = """
                INSERT INTO teklifler 
                (teklif_kodu, musteri_id, gecerlilik_tarihi, notlar, toplam_tutar, kdv_tutari, genel_toplam, durum)
                VALUES (%(teklif_kodu)s, %(musteri_id)s, %(gecerlilik_tarihi)s, %(notlar)s, %(toplam_tutar)s, %(kdv_tutari)s, %(genel_toplam)s, 'Gönderildi')
                RETURNING id;
            """
            cur.execute(teklif_sorgu, teklif_bilgileri)
            teklif_id = cur.fetchone()['id']

            # 2. Her bir teklif kalemini, ana teklif ID'si ile ilişkilendirerek kaydet
            for kalem in kalemler:
                kalem['teklif_id'] = teklif_id
                kalem_sorgu = """
                    INSERT INTO teklif_kalemleri
                    (teklif_id, aciklama, miktar, birim, birim_fiyat, kdv_orani, toplam_fiyat)
                    VALUES (%(teklif_id)s, %(aciklama)s, %(miktar)s, %(birim)s, %(birim_fiyat)s, %(kdv_orani)s, %(toplam_fiyat)s);
                """
                cur.execute(kalem_sorgu, kalem)
            
            conn.commit()
            return {"message": "Teklif başarıyla oluşturuldu.", "teklif_id": teklif_id}
    except Exception as e:
        if conn: conn.rollback()
        print(f"Teklif oluşturma hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Teklif oluşturulurken bir sunucu hatası oluştu: {e}")
    finally:
        if conn: db_pool.putconn(conn)    
        
@app.get("/api/teklifler/{teklif_id}")
def get_teklif_detay(teklif_id: int):
    # Şirket ayarlarını veritabanından çekiyoruz
    sirket_ayarlari_raw = run_db_query(
        "SELECT ayar_anahtari, ayar_degeri FROM sistem_ayarlari WHERE ayar_anahtari LIKE 'firma_%'", 
        fetch="all"
    )
    sirket_bilgileri = {ayar['ayar_anahtari']: ayar['ayar_degeri'] for ayar in sirket_ayarlari_raw}

    # Ana teklif bilgilerini ve ilişkili müşteri bilgilerini çekiyoruz
    teklif_sorgu = """
        SELECT t.*, m.ad as musteri_adi, m.adres as musteri_adres, m.telefon as musteri_telefon, m.vergi_dairesi as musteri_vergi_dairesi, m.vergi_no as musteri_vergi_no
        FROM teklifler t
        JOIN musteriler m ON t.musteri_id = m.id
        WHERE t.id = %s;
    """
    teklif_detay = run_db_query(teklif_sorgu, params=(teklif_id,), fetch="one")
    
    if not teklif_detay:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı.")
    
    # Teklife ait ürün/hizmet kalemlerini çekiyoruz
    kalem_sorgu = "SELECT * FROM teklif_kalemleri WHERE teklif_id = %s ORDER BY id;"
    teklif_kalemleri = run_db_query(kalem_sorgu, params=(teklif_id,), fetch="all")
    
    # Tüm verileri birleştirip gönderiyoruz
    return {"teklif": teklif_detay, "kalemler": teklif_kalemleri, "sirket": sirket_bilgileri}

# =================================================================
# --- API: Teklif Yönetimi ---
# =================================================================

# Önceki adımdaki create_teklif fonksiyonu burada olmalı...

# YENİ: Tüm teklifleri listeleyen fonksiyon
@app.get("/api/teklifler")
def get_teklifler():
    sorgu = """
        SELECT t.id, t.teklif_kodu, t.teklif_tarihi, t.genel_toplam, t.durum, m.ad as musteri_adi
        FROM teklifler t
        LEFT JOIN musteriler m ON t.musteri_id = m.id
        ORDER BY t.teklif_tarihi DESC, t.id DESC;
    """
    return run_db_query(sorgu, fetch="all")

# YENİ: Tek bir teklifi silen fonksiyon
@app.delete("/api/teklifler/{teklif_id}")
def delete_teklif(teklif_id: int):
    # Veritabanı tablosunu ON DELETE CASCADE ile kurduğumuz için
    # ana teklif silindiğinde, bağlı olan teklif kalemleri de otomatik silinecektir.
    result = run_db_query("DELETE FROM teklifler WHERE id = %s RETURNING id;", params=(teklif_id,), fetch="one")
    if result is None:
        raise HTTPException(status_code=404, detail="Teklif bulunamadı.")
    return {"message": "Teklif ve bağlı kalemleri başarıyla silindi."}

# create_teklif ve get_teklif_detay fonksiyonları burada olmalı...


# YENİ: XML'den fatura okumak için eklendi.
import xml.etree.ElementTree as ET

# ... (dosyanın geri kalanı) ...

# YENİ: XML fatura yükleme ve ayrıştırma (parse) endpoint'i
@app.post("/api/fatura-yukle/xml")
async def upload_and_parse_xml_fatura(xml_file: UploadFile = File(...)):
    try:
        xml_content = await xml_file.read()
        root = ET.fromstring(xml_content)

        # XML içindeki namespace'leri (xmlns) tanımlıyoruz. Bunlar standart UBL-TR formatıdır.
        ns = {
            '': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        }

        # Temel fatura bilgilerini XML'den çekiyoruz
        fatura_numarasi = root.find('cbc:ID', ns).text
        fatura_tarihi = root.find('cbc:IssueDate', ns).text
        
        # Tedarikçi bilgilerini çekiyoruz
        tedarikci_parti = root.find('cac:AccountingSupplierParty/cac:Party', ns)
        tedarikci_vkn = tedarikci_parti.find('cac:PartyIdentification/cbc:ID[@schemeID="VKN"]', ns).text
        
        # Fatura kalemlerini çekiyoruz
        kalemler = []
        for line in root.findall('cac:InvoiceLine', ns):
            kalemler.append({
                'aciklama': line.find('cac:Item/cbc:Name', ns).text,
                'miktar': float(line.find('cbc:InvoicedQuantity', ns).text),
                'birim': line.find('cbc:InvoicedQuantity', ns).attrib.get('unitCode', 'ADET'),
                'birim_fiyat': float(line.find('cac:Price/cbc:PriceAmount', ns).text),
                'kdv_orani': float(line.find('cac:TaxTotal/cac:TaxSubtotal/cbc:Percent', ns).text),
                'toplam_fiyat': float(line.find('cbc:LineExtensionAmount', ns).text)
            })

        # Toplam tutarları çekiyoruz
        monetary_total = root.find('cac:LegalMonetaryTotal', ns)
        toplam_tutar = float(monetary_total.find('cbc:LineExtensionAmount', ns).text)
        kdv_tutari = float(monetary_total.find('cbc:TaxExclusiveAmount', ns).text) - toplam_tutar
        genel_toplam = float(monetary_total.find('cbc:PayableAmount', ns).text)
        
        # Toplanan verileri arayüze göndermek için bir JSON yapısı oluşturuyoruz
        parsed_data = {
            "fatura": {
                "fatura_numarasi": fatura_numarasi,
                "fatura_tarihi": fatura_tarihi,
                "tedarikci_vkn": tedarikci_vkn, # Arayüz bu VKN ile doğru tedarikçiyi seçecek
                "toplam_tutar": toplam_tutar,
                "kdv_tutari": kdv_tutari,
                "genel_toplam": genel_toplam,
            },
            "kalemler": kalemler
        }
        return parsed_data
    except Exception as e:
        print(f"XML parse hatası: {e}")
        raise HTTPException(status_code=400, detail=f"XML dosyası işlenirken bir hata oluştu: {e}")
    
@app.get("/api/planlama/analiz/{satis_id}")
def analyze_order_for_mrp(satis_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Siparişteki ürünleri ve miktarlarını al
            cur.execute("SELECT urun_id, miktar FROM siparis_kalemleri WHERE siparis_id = %s", (satis_id,))
            siparis_urunleri = cur.fetchall()

            if not siparis_urunleri:
                return {"analiz": []} # Siparişte ürün yoksa boş liste dön

            # 2. Tüm ürünler için toplam hammadde ihtiyacını hesapla
            toplam_hammadde_ihtiyaci = {}
            for urun in siparis_urunleri:
                # Her ürünün reçetesini al
                cur.execute("SELECT hammadde_id, miktar FROM urun_receteleri WHERE urun_id = %s", (urun['urun_id'],))
                recete = cur.fetchall()
                for recete_item in recete:
                    gereken_miktar = float(recete_item['miktar']) * float(urun['miktar'])
                    h_id = recete_item['hammadde_id']
                    toplam_hammadde_ihtiyaci[h_id] = toplam_hammadde_ihtiyaci.get(h_id, 0) + gereken_miktar

            # 3. İhtiyaç duyulan hammaddelerin stok durumlarını kontrol et
            analiz_sonuclari = []
            if toplam_hammadde_ihtiyaci:
                hammadde_idler = list(toplam_hammadde_ihtiyaci.keys())
                cur.execute("SELECT id, hammadde_adi, stok_miktari, birim FROM hammaddeler WHERE id = ANY(%s);", (hammadde_idler,))
                hammadde_stoklari = {h['id']: h for h in cur.fetchall()}

                for hammadde_id, gereken in toplam_hammadde_ihtiyaci.items():
                    stok_bilgisi = hammadde_stoklari.get(hammadde_id)
                    if stok_bilgisi:
                        mevcut_stok = float(stok_bilgisi.get('stok_miktari', 0))
                        fark = mevcut_stok - gereken
                        analiz_sonuclari.append({
                            "hammadde_id": hammadde_id,
                            "hammadde_adi": stok_bilgisi['hammadde_adi'],
                            "birim": stok_bilgisi['birim'],
                            "gereken_miktar": round(gereken, 2),
                            "mevcut_stok": mevcut_stok,
                            "fark": round(fark, 2),
                            "durum": "Yeterli" if fark >= 0 else "Yetersiz"
                        })
            
            return {"analiz": analiz_sonuclari}

    except Exception as e:
        print(f"Sipariş analizi hatası: {e}")
        raise HTTPException(status_code=500, detail="Sipariş analizi sırasında bir hata oluştu.")
    finally:
        if conn: db_pool.putconn(conn)
        
# YENİ: Otomatik Toplu Analiz API Endpoint'i
@app.get("/api/planlama/toplu-analiz")
def analyze_all_orders_for_mrp():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Durumu 'Onaylandı' olan tüm sipariş kalemlerini al
            cur.execute("""
                SELECT sk.urun_id, sk.miktar 
                FROM siparis_kalemleri sk
                JOIN satis_siparisleri ss ON sk.siparis_id = ss.id
                WHERE ss.durum = 'Onaylandı'
            """)
            tum_siparis_urunleri = cur.fetchall()

            if not tum_siparis_urunleri:
                return {"analiz": []}

            # 2. Tüm ürünler için toplam hammadde ihtiyacını hesapla
            toplam_hammadde_ihtiyaci = {}
            for urun in tum_siparis_urunleri:
                cur.execute("SELECT hammadde_id, miktar FROM urun_receteleri WHERE urun_id = %s", (urun['urun_id'],))
                recete = cur.fetchall()
                for recete_item in recete:
                    gereken_miktar = float(recete_item['miktar']) * float(urun['miktar'])
                    h_id = recete_item['hammadde_id']
                    toplam_hammadde_ihtiyaci[h_id] = toplam_hammadde_ihtiyaci.get(h_id, 0) + gereken_miktar

            # 3. İhtiyaç duyulan hammaddelerin stok durumlarını kontrol et
            analiz_sonuclari = []
            if toplam_hammadde_ihtiyaci:
                hammadde_idler = list(toplam_hammadde_ihtiyaci.keys())
                cur.execute("SELECT id, hammadde_adi, stok_miktari, birim FROM hammaddeler WHERE id = ANY(%s);", (hammadde_idler,))
                hammadde_stoklari = {h['id']: h for h in cur.fetchall()}

                for hammadde_id, gereken in toplam_hammadde_ihtiyaci.items():
                    stok_bilgisi = hammadde_stoklari.get(hammadde_id)
                    if stok_bilgisi:
                        mevcut_stok = float(stok_bilgisi.get('stok_miktari', 0))
                        fark = mevcut_stok - gereken
                        if fark < 0: # Sadece eksik olanları rapora ekle
                            analiz_sonuclari.append({
                                "hammadde_id": hammadde_id,
                                "hammadde_adi": stok_bilgisi['hammadde_adi'],
                                "birim": stok_bilgisi['birim'],
                                "gereken_miktar": round(gereken, 2),
                                "mevcut_stok": mevcut_stok,
                                "eksik_miktar": round(abs(fark), 2)
                            })
            
            return {"analiz": sorted(analiz_sonuclari, key=lambda x: x['hammadde_adi'])}

    except Exception as e:
        print(f"Toplu analiz hatası: {e}")
        raise HTTPException(status_code=500, detail="Toplu analiz sırasında bir hata oluştu.")
    finally:
        if conn: db_pool.putconn(conn)                           
                       
                       

# --- UYGULAMAYI ÇALIŞTIRMA ---
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

