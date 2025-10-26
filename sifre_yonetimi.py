import psycopg2
import bcrypt
import getpass # Şifreyi ekranda göstermeden almak için

# Lütfen bu bilgileri kendi veritabanı bilgilerinizle güncelleyin
# app.py dosyanızdaki ile aynı olmalı
DB_NAME = "fabrika_pdks"
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"

def update_admin_password():
    """
    saha_elemanlari tablosundaki bir yöneticinin şifresini günceller
    veya yeni bir yönetici ekler.
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        kullanici_adi = input("İşlem yapmak istediğiniz yönetici kullanıcı adını girin: ")
        
        # Kullanıcının var olup olmadığını kontrol et
        cur.execute("SELECT id FROM saha_elemanlari WHERE kullanici_adi = %s", (kullanici_adi,))
        user = cur.fetchone()

        if user:
            print(f"'{kullanici_adi}' kullanıcısı bulundu. Şimdi yeni şifresini belirleyin.")
        else:
            print(f"'{kullanici_adi}' kullanıcısı bulunamadı. Bu isimle yeni bir yönetici oluşturulacak.")
            ad_soyad = input("Yeni yönetici için Ad Soyad girin: ")

        # Şifreyi güvenli bir şekilde al (ekranda görünmeyecek)
        yeni_sifre = getpass.getpass("Yeni şifreyi girin: ")
        yeni_sifre_tekrar = getpass.getpass("Yeni şifreyi tekrar girin: ")

        if yeni_sifre != yeni_sifre_tekrar:
            print("\nHATA: Şifreler uyuşmuyor. İşlem iptal edildi.")
            return

        if not yeni_sifre:
            print("\nHATA: Şifre boş olamaz. İşlem iptal edildi.")
            return

        # Şifreyi hash'le
        hashed_sifre = bcrypt.hashpw(yeni_sifre.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        if user:
            # Mevcut kullanıcıyı güncelle
            cur.execute("UPDATE saha_elemanlari SET sifre_hash = %s WHERE kullanici_adi = %s", (hashed_sifre, kullanici_adi))
            print(f"\nBAŞARILI: '{kullanici_adi}' kullanıcısının şifresi güncellendi.")
        else:
            # Yeni kullanıcıyı ekle
            cur.execute("INSERT INTO saha_elemanlari (kullanici_adi, sifre_hash, ad_soyad, aktif) VALUES (%s, %s, %s, TRUE)", (kullanici_adi, hashed_sifre, ad_soyad))
            print(f"\nBAŞARILI: '{kullanici_adi}' adlı yeni yönetici oluşturuldu ve şifresi ayarlandı.")

        conn.commit()
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"\nVERİTABANI HATASI: {e}")
    except Exception as e:
        print(f"\nBEKLENMEDİK BİR HATA OLUŞTU: {e}")

if __name__ == "__main__":
    update_admin_password()