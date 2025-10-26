import os
import psycopg2

def load_sql_dump(db_url, sql_file_path):
    """
    Belirtilen SQL dosyasını veritabanına yükler.
    """
    try:
        # psycop2 ile bağlantı kurmak için DATABASE_URL'yi kullanıyoruz
        conn = psycopg2.connect(db_url)
        conn.autocommit = True  # Otomatik onaylama (commit)
        cursor = conn.cursor()

        print(f"INFO: {sql_file_path} dosyasını okuma...")
        
        # SQL dosyasını okuyoruz
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("INFO: SQL komutları çalıştırılıyor...")
        
        # SQL komutlarını çalıştırıyoruz
        cursor.execute(sql_script)

        print("INFO: Veritabanı yedeği BAŞARIYLA yüklendi.")
        
    except psycopg2.Error as e:
        print(f"HATA: Veritabanı işlemi başarısız oldu: {e}")
        # Hata durumunda uygulamanın durmasını sağlıyoruz
        raise
    except FileNotFoundError:
        print(f"HATA: {sql_file_path} dosyası bulunamadı. Yüklenemedi.")
        # Hata durumunda uygulamanın durmasını sağlıyoruz
        raise
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    # Render'da otomatik tanımlanan ortam değişkenini kullan
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SQL_FILE = "GUNCEL_YEDEK.sql" # Kök dizinde olduğundan eminiz

    if not DATABASE_URL:
        print("HATA: DATABASE_URL ortam değişkeni bulunamadı. Veritabanı bağlantısı yapılamıyor.")
        exit(1)

    try:
        load_sql_dump(DATABASE_URL, SQL_FILE)
    except Exception:
        # Hata oldu, uygulama başlamamalı
        print("KRİTİK HATA: Veritabanı kurulumu başarısız oldu. Uygulama başlatılmayacak.")
        exit(1)