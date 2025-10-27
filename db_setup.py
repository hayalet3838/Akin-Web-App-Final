import os
import psycopg2
import sys

def load_sql_dump(db_host, db_name, db_user, db_password, db_port, sql_file_path):
    """
    Belirtilen SQL dosyasını, verilen bağlantı bilgileriyle veritabanına yükler.
    """
    conn = None
    try:
        # psycop2 ile ayrı ayrı parametreleri kullanarak bağlantı kuruyoruz
        print(f"INFO: Veritabanına bağlanılıyor: Host={db_host}, DB={db_name}, User={db_user}")
        conn = psycopg2.connect(
            host=db_host,
            dbname=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print(f"INFO: {sql_file_path} dosyasını okuma...")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("INFO: SQL komutları çalıştırılıyor...")
        cursor.execute(sql_script)
        print("INFO: Veritabanı yedeği BAŞARIYLA yüklendi.")

    except psycopg2.Error as e:
        print(f"HATA: Veritabanı işlemi başarısız oldu: {e}")
        raise # Hatanın yukarıya fırlatılmasını sağlıyoruz
    except FileNotFoundError:
        print(f"HATA: {sql_file_path} dosyası bulunamadı. Yüklenemedi.")
        raise
    finally:
        if conn:
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()
            print("INFO: Veritabanı bağlantısı kapatıldı.")

if __name__ == "__main__":
    # Render'da manuel olarak tanımladığımız ortam değişkenlerini kullanıyoruz
    DB_HOST_ENV = os.environ.get("DB_HOST")
    DB_NAME_ENV = os.environ.get("DB_NAME")
    DB_USER_ENV = os.environ.get("DB_USER")
    DB_PASSWORD_ENV = os.environ.get("DB_PASSWORD")
    DB_PORT_ENV = os.environ.get("DB_PORT", "5432") # Port yoksa varsayılan 5432

    SQL_FILE = "GUNCEL_YEDEK.sql"

    if not all([DB_HOST_ENV, DB_NAME_ENV, DB_USER_ENV, DB_PASSWORD_ENV]):
        print("HATA: Gerekli veritabanı ortam değişkenlerinden biri veya birkaçı bulunamadı (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD).")
        exit(1) # Hata koduyla çık

    try:
        load_sql_dump(DB_HOST_ENV, DB_NAME_ENV, DB_USER_ENV, DB_PASSWORD_ENV, DB_PORT_ENV, SQL_FILE)
    except Exception as e:
        print(f"KRİTİK HATA: Veritabanı kurulum betiği başarısız oldu: {e}")
        exit(1) # Hata koduyla çık