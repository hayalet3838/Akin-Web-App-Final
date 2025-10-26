#!/bin/bash

echo "INFO: DigitalOcean ortamında veritabanı yedeği yükleme işlemi başlatılıyor..."

# $DATABASE_URL değişkeni DigitalOcean tarafından sağlanır.
psql "$DATABASE_URL" -f GUNCEL_YEDEK.sql

if [ $? -eq 0 ]; then
    echo "INFO: Veritabanı yedeği BAŞARIYLA yüklendi."
else
    echo "HATA: Veritabanı yedeği yüklenirken hata oluştu. Devam etmeden önce kontrol edin."
fi

# Gunicorn ile FastAPI uygulamasını başlatır.
echo "INFO: FastAPI uygulaması başlatılıyor..."
gunicorn app:app --bind 0.0.0.0:"$PORT"