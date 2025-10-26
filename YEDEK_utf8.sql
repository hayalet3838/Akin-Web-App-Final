--
-- PostgreSQL database dump
--

\restrict zqf8YLO1qBazbHIsPp9CKvzFSV7kjECd0PHG9LDYB0DIGfAk1uvBtoEt5aVFvet

-- Dumped from database version 13.22
-- Dumped by pg_dump version 13.22

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alis_fatura_kalemleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alis_fatura_kalemleri (
    id integer NOT NULL,
    fatura_id integer NOT NULL,
    aciklama text NOT NULL,
    miktar numeric(10,2) NOT NULL,
    birim character varying(20) NOT NULL,
    birim_fiyat numeric(12,2) NOT NULL,
    kdv_orani integer DEFAULT 20,
    toplam_fiyat numeric(12,2) NOT NULL
);


--
-- Name: alis_fatura_kalemleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.alis_fatura_kalemleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: alis_fatura_kalemleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.alis_fatura_kalemleri_id_seq OWNED BY public.alis_fatura_kalemleri.id;


--
-- Name: alis_faturalari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alis_faturalari (
    id integer NOT NULL,
    tedarikci_id integer,
    fatura_numarasi character varying(50) NOT NULL,
    fatura_tarihi date NOT NULL,
    vade_tarihi date,
    toplam_tutar numeric(12,2) NOT NULL,
    kdv_tutari numeric(12,2) NOT NULL,
    genel_toplam numeric(12,2) NOT NULL,
    odeme_durumu character varying(30) DEFAULT 'Odenmedi'::character varying,
    aciklama text,
    kayit_tarihi timestamp with time zone DEFAULT now()
);


--
-- Name: alis_faturalari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.alis_faturalari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: alis_faturalari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.alis_faturalari_id_seq OWNED BY public.alis_faturalari.id;


--
-- Name: belgeler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.belgeler (
    id integer NOT NULL,
    dosya_adi character varying(255) NOT NULL,
    dosya_yolu character varying(512) NOT NULL,
    dosya_tipi character varying(100),
    dosya_boyutu integer,
    yukleme_tarihi timestamp with time zone DEFAULT now() NOT NULL,
    aciklama text,
    iliski_tipi character varying(50) NOT NULL,
    iliski_id integer NOT NULL
);


--
-- Name: TABLE belgeler; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.belgeler IS 'Sistemdeki ├ğe┼şitli kay─▒tlara (m├╝┼şteri, ├╝r├╝n vb.) eklenen dosyalar─▒ y├Ânetir.';


--
-- Name: COLUMN belgeler.iliski_tipi; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.belgeler.iliski_tipi IS 'Belgenin hangi tabloyla ili┼şkili oldu─şunu belirtir (├Ârn: musteri, urun).';


--
-- Name: COLUMN belgeler.iliski_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.belgeler.iliski_id IS '─░li┼şkili tablodaki kayd─▒n ID''sini belirtir.';


--
-- Name: belgeler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.belgeler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: belgeler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.belgeler_id_seq OWNED BY public.belgeler.id;


--
-- Name: cari_hareketler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cari_hareketler (
    id integer NOT NULL,
    cari_id integer NOT NULL,
    islem_tipi character varying(20) NOT NULL,
    referans_id integer,
    borc numeric(12,2) DEFAULT 0,
    alacak numeric(12,2) DEFAULT 0,
    aciklama text,
    tarih timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT cari_hareketler_islem_tipi_check CHECK (((islem_tipi)::text = ANY ((ARRAY['Fatura'::character varying, 'Tahsilat'::character varying])::text[])))
);


--
-- Name: cari_hareketler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cari_hareketler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cari_hareketler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cari_hareketler_id_seq OWNED BY public.cari_hareketler.id;


--
-- Name: cari_hesaplar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cari_hesaplar (
    id integer NOT NULL,
    hesap_kodu character varying(255) NOT NULL,
    hesap_adi character varying(255) NOT NULL,
    hesap_tipi character varying(255) NOT NULL,
    bakiye numeric(10,2) DEFAULT 0.00 NOT NULL
);


--
-- Name: cari_hesaplar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cari_hesaplar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cari_hesaplar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cari_hesaplar_id_seq OWNED BY public.cari_hesaplar.id;


--
-- Name: cari_islemler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cari_islemler (
    id integer NOT NULL,
    cari_hesap_id integer NOT NULL,
    fatura_id integer,
    tarih date DEFAULT CURRENT_DATE NOT NULL,
    aciklama text NOT NULL,
    borc numeric(15,2) DEFAULT 0.00 NOT NULL,
    alacak numeric(15,2) DEFAULT 0.00 NOT NULL
);


--
-- Name: cari_islemler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cari_islemler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cari_islemler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cari_islemler_id_seq OWNED BY public.cari_islemler.id;


--
-- Name: crm_aktiviteler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crm_aktiviteler (
    id integer NOT NULL,
    musteri_id integer NOT NULL,
    firsat_id integer,
    personel_id integer,
    aktivite_tipi character varying(50) NOT NULL,
    tarih timestamp with time zone DEFAULT now() NOT NULL,
    notlar text
);


--
-- Name: TABLE crm_aktiviteler; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.crm_aktiviteler IS 'M├╝┼şterilerle yap─▒lan t├╝m etkile┼şimlerin kayd─▒n─▒ tutar.';


--
-- Name: crm_aktiviteler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.crm_aktiviteler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crm_aktiviteler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.crm_aktiviteler_id_seq OWNED BY public.crm_aktiviteler.id;


--
-- Name: crm_firsatlar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crm_firsatlar (
    id integer NOT NULL,
    firsat_adi character varying(255) NOT NULL,
    musteri_id integer NOT NULL,
    sorumlu_personel_id integer,
    tahmini_tutar numeric(15,2),
    asama character varying(50) DEFAULT '─░lk Temas'::character varying NOT NULL,
    olusturma_tarihi date DEFAULT CURRENT_DATE NOT NULL,
    kapanis_tarihi date
);


--
-- Name: TABLE crm_firsatlar; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.crm_firsatlar IS 'Potansiyel sat─▒┼ş f─▒rsatlar─▒n─▒ ve sat─▒┼ş hunisini y├Ânetir.';


--
-- Name: crm_firsatlar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.crm_firsatlar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: crm_firsatlar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.crm_firsatlar_id_seq OWNED BY public.crm_firsatlar.id;


--
-- Name: destek_talepleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.destek_talepleri (
    id integer NOT NULL,
    talep_kodu character varying(50) NOT NULL,
    musteri_id integer NOT NULL,
    atanan_personel_id integer,
    konu character varying(255) NOT NULL,
    aciklama text,
    durum character varying(50) DEFAULT 'A├ğ─▒k'::character varying NOT NULL,
    oncelik character varying(50) DEFAULT 'Normal'::character varying,
    olusturma_tarihi timestamp with time zone DEFAULT now() NOT NULL,
    cozulme_tarihi timestamp with time zone
);


--
-- Name: TABLE destek_talepleri; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.destek_talepleri IS 'M├╝┼şteri ┼şikayet ve destek taleplerini y├Ânetir.';


--
-- Name: destek_talepleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.destek_talepleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: destek_talepleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.destek_talepleri_id_seq OWNED BY public.destek_talepleri.id;


--
-- Name: egitim_kayitlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.egitim_kayitlari (
    id integer NOT NULL,
    personel_id integer NOT NULL,
    egitim_adi character varying(255) NOT NULL,
    egitim_kurumu character varying(150),
    baslangic_tarihi date,
    bitis_tarihi date,
    sertifika_path character varying(255),
    aciklama text,
    eklenme_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: egitim_kayitlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.egitim_kayitlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: egitim_kayitlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.egitim_kayitlari_id_seq OWNED BY public.egitim_kayitlari.id;


--
-- Name: enerji_tuketimi; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.enerji_tuketimi (
    id integer NOT NULL,
    donem date NOT NULL,
    enerji_tipi character varying(50) NOT NULL,
    tuketim_miktari numeric(15,2) NOT NULL,
    birim character varying(10) NOT NULL
);


--
-- Name: enerji_tuketimi_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.enerji_tuketimi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: enerji_tuketimi_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.enerji_tuketimi_id_seq OWNED BY public.enerji_tuketimi.id;


--
-- Name: faturalar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.faturalar (
    id integer NOT NULL,
    fatura_no character varying(100) NOT NULL,
    fatura_tipi character varying(20) NOT NULL,
    cari_hesap_id integer NOT NULL,
    satis_siparisi_id integer,
    satin_alma_siparisi_id integer,
    tarih date DEFAULT CURRENT_DATE NOT NULL,
    vade_tarihi date,
    tutar numeric(15,2) NOT NULL,
    kalan_tutar numeric(15,2) NOT NULL,
    durum character varying(50) DEFAULT 'Odenmedi'::character varying NOT NULL
);


--
-- Name: faturalar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.faturalar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: faturalar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.faturalar_id_seq OWNED BY public.faturalar.id;


--
-- Name: finansal_islemler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.finansal_islemler (
    id integer NOT NULL,
    islem_tarihi date NOT NULL,
    islem_tipi character varying(20) NOT NULL,
    aciklama text,
    miktar numeric(10,2) NOT NULL,
    ilgili_cari_id integer,
    cari_tipi character varying(20),
    CONSTRAINT finansal_islemler_islem_tipi_check CHECK (((islem_tipi)::text = ANY ((ARRAY['gelir'::character varying, 'gider'::character varying])::text[])))
);


--
-- Name: finansal_islemler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.finansal_islemler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: finansal_islemler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.finansal_islemler_id_seq OWNED BY public.finansal_islemler.id;


--
-- Name: gelirler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gelirler (
    id integer NOT NULL,
    aciklama character varying(255) NOT NULL,
    kategori character varying(255),
    tutar numeric(10,2) NOT NULL,
    gelir_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    gelir_alan_hesap_id integer NOT NULL
);


--
-- Name: gelirler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.gelirler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: gelirler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.gelirler_id_seq OWNED BY public.gelirler.id;


--
-- Name: giris_cikis_kayitlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.giris_cikis_kayitlari (
    kayit_id integer NOT NULL,
    personel_id integer NOT NULL,
    giris_zamani timestamp with time zone NOT NULL,
    cikis_zamani timestamp with time zone
);


--
-- Name: giris_cikis_kayitlari_kayit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.giris_cikis_kayitlari_kayit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: giris_cikis_kayitlari_kayit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.giris_cikis_kayitlari_kayit_id_seq OWNED BY public.giris_cikis_kayitlari.kayit_id;


--
-- Name: hammadde_girisleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hammadde_girisleri (
    id integer NOT NULL,
    hammadde_id integer NOT NULL,
    lot_numarasi character varying(100) NOT NULL,
    giris_miktari numeric(10,2) NOT NULL,
    kalan_miktar numeric(10,2) NOT NULL,
    giris_tarihi date DEFAULT CURRENT_DATE,
    tedarikci character varying(255)
);


--
-- Name: hammadde_girisleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.hammadde_girisleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hammadde_girisleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.hammadde_girisleri_id_seq OWNED BY public.hammadde_girisleri.id;


--
-- Name: hammaddeler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hammaddeler (
    id integer NOT NULL,
    hammadde_kodu character varying(50) NOT NULL,
    hammadde_adi character varying(255) NOT NULL,
    stok_miktari numeric(10,2) DEFAULT 0.00 NOT NULL,
    birim character varying(20) NOT NULL,
    maliyet numeric(10,4) DEFAULT 0,
    kritik_stok_seviyesi numeric(10,2) DEFAULT 0,
    guvenlik_stogu numeric(10,2) DEFAULT 0 NOT NULL,
    yeniden_siparis_noktasi numeric(10,2) DEFAULT 0 NOT NULL
);


--
-- Name: COLUMN hammaddeler.guvenlik_stogu; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.hammaddeler.guvenlik_stogu IS 'Beklenmedik durumlar i├ğin ayr─▒lan minimum stok miktar─▒.';


--
-- Name: COLUMN hammaddeler.yeniden_siparis_noktasi; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.hammaddeler.yeniden_siparis_noktasi IS 'Stok bu seviyeye d├╝┼şt├╝─ş├╝nde sipari┼ş verilmesi gerekti─şini belirtir.';


--
-- Name: hammaddeler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.hammaddeler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hammaddeler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.hammaddeler_id_seq OWNED BY public.hammaddeler.id;


--
-- Name: izin_kayitlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.izin_kayitlari (
    id integer NOT NULL,
    personel_id integer NOT NULL,
    izin_tipi character varying(50) NOT NULL,
    baslangic_tarihi date NOT NULL,
    bitis_tarihi date NOT NULL,
    aciklama text,
    eklenme_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: izin_kayitlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.izin_kayitlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: izin_kayitlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.izin_kayitlari_id_seq OWNED BY public.izin_kayitlari.id;


--
-- Name: kaliplar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kaliplar (
    id integer NOT NULL,
    kalip_kodu character varying(100) NOT NULL,
    kalip_adi character varying(255),
    goz_sayisi integer,
    cevrim_suresi_sn integer,
    garanti_baski_sayisi bigint,
    mevcut_baski_sayisi bigint DEFAULT 0,
    lokasyon character varying(100),
    durum character varying(50) DEFAULT 'Depoda'::character varying
);


--
-- Name: kaliplar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.kaliplar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: kaliplar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.kaliplar_id_seq OWNED BY public.kaliplar.id;


--
-- Name: kalite_kontrol; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kalite_kontrol (
    id integer NOT NULL,
    urun_id integer NOT NULL,
    kontrol_tarihi date NOT NULL,
    kontrol_eden_personel_id integer,
    sonuc character varying(50) NOT NULL,
    aciklama text,
    CONSTRAINT chk_sonuc CHECK (((sonuc)::text = ANY ((ARRAY['Ge├ğti'::character varying, 'Kald─▒'::character varying, 'Onay Bekliyor'::character varying])::text[])))
);


--
-- Name: kalite_kontrol_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.kalite_kontrol_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: kalite_kontrol_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.kalite_kontrol_id_seq OWNED BY public.kalite_kontrol.id;


--
-- Name: kalite_kontrol_kayitlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kalite_kontrol_kayitlari (
    id integer NOT NULL,
    uretim_emri_id integer NOT NULL,
    saglam_adet integer DEFAULT 0 NOT NULL,
    fire_adet integer DEFAULT 0 NOT NULL,
    fire_nedeni text,
    kontrol_yapan_personel_id integer,
    kontrol_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: kalite_kontrol_kayitlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.kalite_kontrol_kayitlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: kalite_kontrol_kayitlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.kalite_kontrol_kayitlari_id_seq OWNED BY public.kalite_kontrol_kayitlari.id;


--
-- Name: maas_bordrolari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maas_bordrolari (
    id integer NOT NULL,
    personel_id integer NOT NULL,
    odeme_tarihi character varying(7) NOT NULL,
    net_maas numeric(10,2) NOT NULL
);


--
-- Name: maas_bordrolari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.maas_bordrolari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: maas_bordrolari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.maas_bordrolari_id_seq OWNED BY public.maas_bordrolari.id;


--
-- Name: maaslar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maaslar (
    id integer NOT NULL,
    personel_id integer NOT NULL,
    odeme_tarihi date NOT NULL,
    net_maas numeric(10,2) NOT NULL,
    brut_maas numeric(10,2),
    kesintiler numeric(10,2),
    aciklama text
);


--
-- Name: maaslar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.maaslar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: maaslar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.maaslar_id_seq OWNED BY public.maaslar.id;


--
-- Name: makine_bakim_kayitlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.makine_bakim_kayitlari (
    id integer NOT NULL,
    makine_id integer NOT NULL,
    personel_id integer,
    kayit_tipi character varying(50) NOT NULL,
    baslama_zamani timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    bitis_zamani timestamp with time zone,
    aciklama text,
    durum character varying(50) DEFAULT 'Devam Ediyor'::character varying NOT NULL
);


--
-- Name: makine_bakim_kayitlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.makine_bakim_kayitlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: makine_bakim_kayitlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.makine_bakim_kayitlari_id_seq OWNED BY public.makine_bakim_kayitlari.id;


--
-- Name: makineler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.makineler (
    id integer NOT NULL,
    makine_adi character varying(100) NOT NULL,
    durum character varying(50) DEFAULT 'Bosta'::character varying NOT NULL
);


--
-- Name: makineler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.makineler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: makineler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.makineler_id_seq OWNED BY public.makineler.id;


--
-- Name: masraf_kayitlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.masraf_kayitlari (
    id integer NOT NULL,
    tarih date DEFAULT CURRENT_DATE NOT NULL,
    aciklama text NOT NULL,
    kategori character varying(100),
    tutar numeric(15,2) NOT NULL,
    odeme_yapan_hesap_id integer
);


--
-- Name: masraf_kayitlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.masraf_kayitlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: masraf_kayitlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.masraf_kayitlari_id_seq OWNED BY public.masraf_kayitlari.id;


--
-- Name: masraflar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.masraflar (
    id integer NOT NULL,
    aciklama text NOT NULL,
    kategori character varying(100),
    tutar numeric(10,2) NOT NULL,
    tarih date DEFAULT CURRENT_DATE NOT NULL
);


--
-- Name: masraflar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.masraflar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: masraflar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.masraflar_id_seq OWNED BY public.masraflar.id;


--
-- Name: musteri_siparisleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.musteri_siparisleri (
    id integer NOT NULL,
    saha_elemani_id integer NOT NULL,
    musteri_adi character varying(255) NOT NULL,
    siparis_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    toplam_tutar numeric(10,2) NOT NULL,
    durum character varying(50) DEFAULT 'Al─▒nd─▒'::character varying
);


--
-- Name: musteri_siparisleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.musteri_siparisleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: musteri_siparisleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.musteri_siparisleri_id_seq OWNED BY public.musteri_siparisleri.id;


--
-- Name: musteriler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.musteriler (
    id integer NOT NULL,
    ad character varying(100) NOT NULL,
    adres text,
    telefon character varying(20),
    email character varying(100),
    vergi_no character varying(50),
    sorumlu_kisi character varying(100),
    vergi_dairesi character varying(255)
);


--
-- Name: musteriler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.musteriler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: musteriler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.musteriler_id_seq OWNED BY public.musteriler.id;


--
-- Name: oyunlastirma_kayitlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.oyunlastirma_kayitlari (
    id integer NOT NULL,
    personel_id integer NOT NULL,
    puan integer NOT NULL,
    aciklama character varying(255),
    kayit_tarihi date DEFAULT CURRENT_DATE
);


--
-- Name: oyunlastirma_kayitlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.oyunlastirma_kayitlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oyunlastirma_kayitlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.oyunlastirma_kayitlari_id_seq OWNED BY public.oyunlastirma_kayitlari.id;


--
-- Name: pazarlama_firmalari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pazarlama_firmalari (
    id integer NOT NULL,
    firma_adi character varying(255) NOT NULL,
    email character varying(255),
    sektor character varying(100),
    sorumlu_kisi character varying(100),
    olusturma_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: pazarlama_firmalari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pazarlama_firmalari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pazarlama_firmalari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pazarlama_firmalari_id_seq OWNED BY public.pazarlama_firmalari.id;


--
-- Name: performans_degerlendirmeleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performans_degerlendirmeleri (
    id integer NOT NULL,
    personel_id integer NOT NULL,
    degerlendirme_tarihi date NOT NULL,
    degerlendiren_yonetici character varying(100),
    puan numeric(3,1),
    yonetici_notlari text,
    eklenme_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: performans_degerlendirmeleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.performans_degerlendirmeleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: performans_degerlendirmeleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performans_degerlendirmeleri_id_seq OWNED BY public.performans_degerlendirmeleri.id;


--
-- Name: personel; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personel (
    id integer NOT NULL,
    ad_soyad character varying(150) NOT NULL,
    pozisyon character varying(100),
    ise_giris_tarihi date DEFAULT CURRENT_DATE NOT NULL,
    aktif_mi boolean DEFAULT true NOT NULL,
    brut_maas numeric(10,2),
    net_maas numeric(10,2),
    tc_kimlik_no character varying(11),
    dogum_tarihi date,
    telefon character varying(20),
    adres text
);


--
-- Name: personel_giris_cikis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personel_giris_cikis (
    id integer NOT NULL,
    personel_id integer NOT NULL,
    giris_zamani timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    cikis_zamani timestamp with time zone
);


--
-- Name: personel_giris_cikis_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.personel_giris_cikis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: personel_giris_cikis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.personel_giris_cikis_id_seq OWNED BY public.personel_giris_cikis.id;


--
-- Name: personel_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.personel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: personel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.personel_id_seq OWNED BY public.personel.id;


--
-- Name: personel_vardiyalari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personel_vardiyalari (
    id integer NOT NULL,
    personel_id integer NOT NULL,
    vardiya_id integer NOT NULL,
    tarih date NOT NULL
);


--
-- Name: personel_vardiyalari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.personel_vardiyalari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: personel_vardiyalari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.personel_vardiyalari_id_seq OWNED BY public.personel_vardiyalari.id;


--
-- Name: portal_kullanicilari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portal_kullanicilari (
    id integer NOT NULL,
    kullanici_adi character varying(50) NOT NULL,
    sifre_hash character varying(255) NOT NULL,
    rol character varying(20) NOT NULL,
    musteri_id integer,
    tedarikci_id integer,
    aktif_mi boolean DEFAULT true,
    olusturulma_tarihi timestamp with time zone DEFAULT now(),
    CONSTRAINT portal_kullanicilari_rol_check CHECK (((rol)::text = ANY ((ARRAY['musteri'::character varying, 'tedarikci'::character varying])::text[])))
);


--
-- Name: TABLE portal_kullanicilari; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.portal_kullanicilari IS 'M├╝┼şteri ve tedarik├ğilerin portala giri┼ş yapaca─ş─▒ kullan─▒c─▒lar─▒ tutar.';


--
-- Name: COLUMN portal_kullanicilari.rol; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.portal_kullanicilari.rol IS 'Kullan─▒c─▒n─▒n rol├╝n├╝ belirtir (musteri veya tedarikci).';


--
-- Name: COLUMN portal_kullanicilari.musteri_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.portal_kullanicilari.musteri_id IS 'E─şer rol musteri ise, musteriler tablosundaki ilgili ID.';


--
-- Name: COLUMN portal_kullanicilari.tedarikci_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.portal_kullanicilari.tedarikci_id IS 'E─şer rol tedarikci ise, tedarikciler tablosundaki ilgili ID.';


--
-- Name: portal_kullanicilari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.portal_kullanicilari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: portal_kullanicilari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.portal_kullanicilari_id_seq OWNED BY public.portal_kullanicilari.id;


--
-- Name: saha_elemanlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.saha_elemanlari (
    id integer NOT NULL,
    kullanici_adi character varying(50) NOT NULL,
    sifre_hash character varying(255) NOT NULL,
    ad_soyad character varying(100) NOT NULL,
    aktif boolean DEFAULT true,
    olusturma_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: saha_elemanlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.saha_elemanlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: saha_elemanlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.saha_elemanlari_id_seq OWNED BY public.saha_elemanlari.id;


--
-- Name: satin_alma_detaylari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.satin_alma_detaylari (
    id integer NOT NULL,
    siparis_id integer NOT NULL,
    hammadde_id integer NOT NULL,
    miktar numeric(10,2) NOT NULL,
    birim_fiyat numeric(10,2)
);


--
-- Name: satin_alma_detaylari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.satin_alma_detaylari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: satin_alma_detaylari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.satin_alma_detaylari_id_seq OWNED BY public.satin_alma_detaylari.id;


--
-- Name: satin_alma_siparisleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.satin_alma_siparisleri (
    id integer NOT NULL,
    siparis_kodu character varying(50) NOT NULL,
    tedarikci_id integer NOT NULL,
    siparis_tarihi date DEFAULT CURRENT_DATE,
    beklenen_teslim_tarihi date,
    durum character varying(50) DEFAULT 'Taslak'::character varying,
    kargo_takip_no character varying(100),
    tahmini_varis_tarihi date
);


--
-- Name: COLUMN satin_alma_siparisleri.kargo_takip_no; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.satin_alma_siparisleri.kargo_takip_no IS 'Gelen sevkiyat─▒n kargo takip numaras─▒.';


--
-- Name: COLUMN satin_alma_siparisleri.tahmini_varis_tarihi; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.satin_alma_siparisleri.tahmini_varis_tarihi IS 'Sevkiyat─▒n tahmini olarak ne zaman ula┼şaca─ş─▒.';


--
-- Name: satin_alma_siparisleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.satin_alma_siparisleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: satin_alma_siparisleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.satin_alma_siparisleri_id_seq OWNED BY public.satin_alma_siparisleri.id;


--
-- Name: satin_alma_talepleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.satin_alma_talepleri (
    id integer NOT NULL,
    hammadde_id integer,
    talep_edilen_miktar numeric(10,2) NOT NULL,
    birim character varying(50),
    talep_tarihi timestamp with time zone DEFAULT now(),
    durum character varying(50) DEFAULT 'Talep Edildi'::character varying,
    aciklama text
);


--
-- Name: satin_alma_talepleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.satin_alma_talepleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: satin_alma_talepleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.satin_alma_talepleri_id_seq OWNED BY public.satin_alma_talepleri.id;


--
-- Name: satis_siparisleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.satis_siparisleri (
    id integer NOT NULL,
    siparis_kodu character varying(50) NOT NULL,
    durum character varying(20) DEFAULT 'Alindi'::character varying,
    siparis_tarihi timestamp without time zone DEFAULT now(),
    musteri_id integer NOT NULL,
    toplam_tutar numeric(12,2),
    kdv_tutari numeric(12,2),
    genel_toplam numeric(12,2)
);


--
-- Name: satis_siparisleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.satis_siparisleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: satis_siparisleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.satis_siparisleri_id_seq OWNED BY public.satis_siparisleri.id;


--
-- Name: scm_tedarikci_performans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scm_tedarikci_performans (
    id integer NOT NULL,
    tedarikci_id integer NOT NULL,
    degerlendirme_tarihi date DEFAULT CURRENT_DATE NOT NULL,
    kalite_puani numeric(5,2),
    teslimat_hizi_puani numeric(5,2),
    fiyat_puani numeric(5,2),
    genel_puan numeric(5,2),
    notlar text,
    CONSTRAINT scm_tedarikci_performans_fiyat_puani_check CHECK (((fiyat_puani >= (0)::numeric) AND (fiyat_puani <= (100)::numeric))),
    CONSTRAINT scm_tedarikci_performans_kalite_puani_check CHECK (((kalite_puani >= (0)::numeric) AND (kalite_puani <= (100)::numeric))),
    CONSTRAINT scm_tedarikci_performans_teslimat_hizi_puani_check CHECK (((teslimat_hizi_puani >= (0)::numeric) AND (teslimat_hizi_puani <= (100)::numeric)))
);


--
-- Name: TABLE scm_tedarikci_performans; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.scm_tedarikci_performans IS 'Tedarik├ğilerin performans─▒n─▒ (kalite, h─▒z, fiyat) puanlar.';


--
-- Name: scm_tedarikci_performans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scm_tedarikci_performans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scm_tedarikci_performans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scm_tedarikci_performans_id_seq OWNED BY public.scm_tedarikci_performans.id;


--
-- Name: sevkiyatlar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sevkiyatlar (
    id integer NOT NULL,
    satis_siparis_id integer,
    kargo_firmasi character varying(100) NOT NULL,
    takip_numarasi character varying(100),
    sevk_tarihi date NOT NULL,
    durum character varying(50) DEFAULT 'Haz─▒rlan─▒yor'::character varying,
    kargo_fisi_path character varying(255),
    notlar text,
    kayit_tarihi timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE sevkiyatlar; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sevkiyatlar IS 'Sat─▒┼ş sipari┼şlerine ait kargo ve sevk bilgilerini tutar.';


--
-- Name: COLUMN sevkiyatlar.kargo_fisi_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.sevkiyatlar.kargo_fisi_path IS 'Sunucuya y├╝klenen kargo fi┼şi resminin yolu.';


--
-- Name: sevkiyatlar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sevkiyatlar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sevkiyatlar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sevkiyatlar_id_seq OWNED BY public.sevkiyatlar.id;


--
-- Name: siparis_detaylari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.siparis_detaylari (
    id integer NOT NULL,
    siparis_id integer NOT NULL,
    urun_id integer NOT NULL,
    miktar integer NOT NULL
);


--
-- Name: siparis_detaylari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.siparis_detaylari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: siparis_detaylari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.siparis_detaylari_id_seq OWNED BY public.siparis_detaylari.id;


--
-- Name: siparis_kalemleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.siparis_kalemleri (
    id integer NOT NULL,
    siparis_id integer NOT NULL,
    urun_id integer NOT NULL,
    miktar integer NOT NULL,
    birim character varying(20),
    birim_fiyat numeric(10,2),
    toplam_fiyat numeric(12,2),
    kdv_orani integer DEFAULT 20
);


--
-- Name: COLUMN siparis_kalemleri.birim_fiyat; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.siparis_kalemleri.birim_fiyat IS 'Sipari┼ş an─▒ndaki KDV hari├ğ birim sat─▒┼ş fiyat─▒.';


--
-- Name: COLUMN siparis_kalemleri.toplam_fiyat; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.siparis_kalemleri.toplam_fiyat IS 'Sipari┼ş an─▒ndaki KDV dahil toplam fiyat.';


--
-- Name: siparis_kalemleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.siparis_kalemleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: siparis_kalemleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.siparis_kalemleri_id_seq OWNED BY public.siparis_kalemleri.id;


--
-- Name: sistem_ayarlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sistem_ayarlari (
    id integer NOT NULL,
    ayar_anahtari character varying(100) NOT NULL,
    ayar_degeri character varying(255) NOT NULL,
    aciklama text
);


--
-- Name: TABLE sistem_ayarlari; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sistem_ayarlari IS 'Sistem genelindeki yap─▒land─▒rma ayarlar─▒n─▒ anahtar-de─şer olarak saklar.';


--
-- Name: sistem_ayarlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sistem_ayarlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sistem_ayarlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sistem_ayarlari_id_seq OWNED BY public.sistem_ayarlari.id;


--
-- Name: stok_hareketleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stok_hareketleri (
    id integer NOT NULL,
    hareket_tipi character varying(10) NOT NULL,
    urun_id integer,
    hammadde_id integer,
    miktar numeric(10,2) NOT NULL,
    tarih timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    aciklama text
);


--
-- Name: stok_hareketleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stok_hareketleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: stok_hareketleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stok_hareketleri_id_seq OWNED BY public.stok_hareketleri.id;


--
-- Name: tedarikciler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tedarikciler (
    id integer NOT NULL,
    firma_adi character varying(255) NOT NULL,
    yetkili_kisi character varying(255),
    email character varying(255),
    telefon character varying(20),
    vergi_dairesi character varying(255),
    vergi_no character varying(50)
);


--
-- Name: tedarikciler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tedarikciler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tedarikciler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tedarikciler_id_seq OWNED BY public.tedarikciler.id;


--
-- Name: teklif_kalemleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teklif_kalemleri (
    id integer NOT NULL,
    teklif_id integer NOT NULL,
    aciklama text NOT NULL,
    urun_id integer,
    miktar numeric(10,2) NOT NULL,
    birim character varying(50) NOT NULL,
    birim_fiyat numeric(10,2) NOT NULL,
    kdv_orani integer DEFAULT 20 NOT NULL,
    toplam_fiyat numeric(12,2) NOT NULL
);


--
-- Name: teklif_kalemleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.teklif_kalemleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: teklif_kalemleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.teklif_kalemleri_id_seq OWNED BY public.teklif_kalemleri.id;


--
-- Name: teklifler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teklifler (
    id integer NOT NULL,
    teklif_kodu character varying(50) NOT NULL,
    musteri_id integer,
    teklif_tarihi date DEFAULT CURRENT_DATE NOT NULL,
    gecerlilik_tarihi date,
    durum character varying(50) DEFAULT 'Haz─▒rlan─▒yor'::character varying NOT NULL,
    toplam_tutar numeric(12,2) DEFAULT 0.00,
    kdv_tutari numeric(12,2) DEFAULT 0.00,
    genel_toplam numeric(12,2) DEFAULT 0.00,
    notlar text
);


--
-- Name: teklifler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.teklifler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: teklifler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.teklifler_id_seq OWNED BY public.teklifler.id;


--
-- Name: uretim_emirleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.uretim_emirleri (
    id integer NOT NULL,
    is_emri_kodu character varying(50) NOT NULL,
    urun_id integer NOT NULL,
    hedef_miktar integer NOT NULL,
    uretilen_miktar integer DEFAULT 0 NOT NULL,
    durum character varying(50) DEFAULT 'Bekliyor'::character varying NOT NULL,
    olusturma_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    baslama_tarihi timestamp with time zone,
    bitis_tarihi timestamp with time zone,
    atanan_makine_id integer,
    sorumlu_personel_id integer,
    tahmini_baslama_tarihi timestamp with time zone,
    tahmini_bitis_tarihi timestamp with time zone,
    toplam_maliyet double precision DEFAULT 0,
    arsivlendi boolean DEFAULT false,
    atanan_kalip_id integer
);


--
-- Name: uretim_emirleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.uretim_emirleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: uretim_emirleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.uretim_emirleri_id_seq OWNED BY public.uretim_emirleri.id;


--
-- Name: uretim_hammadde_kullanimi; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.uretim_hammadde_kullanimi (
    id integer NOT NULL,
    uretim_emri_id integer NOT NULL,
    hammadde_giris_id integer NOT NULL,
    kullanilan_miktar numeric(10,2) NOT NULL
);


--
-- Name: uretim_hammadde_kullanimi_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.uretim_hammadde_kullanimi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: uretim_hammadde_kullanimi_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.uretim_hammadde_kullanimi_id_seq OWNED BY public.uretim_hammadde_kullanimi.id;


--
-- Name: uretim_lot_kullanimi; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.uretim_lot_kullanimi (
    id integer NOT NULL,
    uretim_emri_id integer NOT NULL,
    hammadde_giris_id integer NOT NULL,
    kullanilan_miktar numeric(10,2) NOT NULL,
    kayit_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: uretim_lot_kullanimi_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.uretim_lot_kullanimi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: uretim_lot_kullanimi_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.uretim_lot_kullanimi_id_seq OWNED BY public.uretim_lot_kullanimi.id;


--
-- Name: uretim_planlari; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.uretim_planlari (
    id integer NOT NULL,
    plan_adi character varying(255) NOT NULL,
    satis_id integer,
    olusturma_tarihi timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    baslangic_tarihi date,
    bitis_tarihi date,
    durum character varying(50) DEFAULT 'Beklemede'::character varying
);


--
-- Name: uretim_planlari_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.uretim_planlari_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: uretim_planlari_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.uretim_planlari_id_seq OWNED BY public.uretim_planlari.id;


--
-- Name: urun_receteleri; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.urun_receteleri (
    id integer NOT NULL,
    urun_id integer NOT NULL,
    hammadde_id integer NOT NULL,
    miktar numeric(10,4) NOT NULL
);


--
-- Name: urun_receteleri_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.urun_receteleri_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: urun_receteleri_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.urun_receteleri_id_seq OWNED BY public.urun_receteleri.id;


--
-- Name: urunler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.urunler (
    id integer NOT NULL,
    urun_kodu character varying(255) NOT NULL,
    urun_adi character varying(255) NOT NULL,
    stok_miktari integer DEFAULT 0 NOT NULL,
    birim_fiyat numeric(10,2) DEFAULT 0.00
);


--
-- Name: COLUMN urunler.birim_fiyat; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.urunler.birim_fiyat IS '├£r├╝n├╝n KDV hari├ğ varsay─▒lan sat─▒┼ş fiyat─▒.';


--
-- Name: urunler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.urunler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: urunler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.urunler_id_seq OWNED BY public.urunler.id;


--
-- Name: vardiyalar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vardiyalar (
    id integer NOT NULL,
    vardiya_adi character varying(100) NOT NULL,
    baslangic_saati time without time zone NOT NULL,
    bitis_saati time without time zone NOT NULL
);


--
-- Name: vardiyalar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vardiyalar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vardiyalar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vardiyalar_id_seq OWNED BY public.vardiyalar.id;


--
-- Name: yoneticiler; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.yoneticiler (
    id integer NOT NULL,
    kullanici_adi character varying(50) NOT NULL,
    sifre_hash character varying(255) NOT NULL,
    ad_soyad character varying(100),
    email character varying(255),
    aktif boolean DEFAULT true,
    olusturma_tarihi timestamp with time zone DEFAULT now()
);


--
-- Name: yoneticiler_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.yoneticiler_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: yoneticiler_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.yoneticiler_id_seq OWNED BY public.yoneticiler.id;


--
-- Name: alis_fatura_kalemleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alis_fatura_kalemleri ALTER COLUMN id SET DEFAULT nextval('public.alis_fatura_kalemleri_id_seq'::regclass);


--
-- Name: alis_faturalari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alis_faturalari ALTER COLUMN id SET DEFAULT nextval('public.alis_faturalari_id_seq'::regclass);


--
-- Name: belgeler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.belgeler ALTER COLUMN id SET DEFAULT nextval('public.belgeler_id_seq'::regclass);


--
-- Name: cari_hareketler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_hareketler ALTER COLUMN id SET DEFAULT nextval('public.cari_hareketler_id_seq'::regclass);


--
-- Name: cari_hesaplar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_hesaplar ALTER COLUMN id SET DEFAULT nextval('public.cari_hesaplar_id_seq'::regclass);


--
-- Name: cari_islemler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_islemler ALTER COLUMN id SET DEFAULT nextval('public.cari_islemler_id_seq'::regclass);


--
-- Name: crm_aktiviteler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_aktiviteler ALTER COLUMN id SET DEFAULT nextval('public.crm_aktiviteler_id_seq'::regclass);


--
-- Name: crm_firsatlar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_firsatlar ALTER COLUMN id SET DEFAULT nextval('public.crm_firsatlar_id_seq'::regclass);


--
-- Name: destek_talepleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destek_talepleri ALTER COLUMN id SET DEFAULT nextval('public.destek_talepleri_id_seq'::regclass);


--
-- Name: egitim_kayitlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.egitim_kayitlari ALTER COLUMN id SET DEFAULT nextval('public.egitim_kayitlari_id_seq'::regclass);


--
-- Name: enerji_tuketimi id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enerji_tuketimi ALTER COLUMN id SET DEFAULT nextval('public.enerji_tuketimi_id_seq'::regclass);


--
-- Name: faturalar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faturalar ALTER COLUMN id SET DEFAULT nextval('public.faturalar_id_seq'::regclass);


--
-- Name: finansal_islemler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finansal_islemler ALTER COLUMN id SET DEFAULT nextval('public.finansal_islemler_id_seq'::regclass);


--
-- Name: gelirler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gelirler ALTER COLUMN id SET DEFAULT nextval('public.gelirler_id_seq'::regclass);


--
-- Name: giris_cikis_kayitlari kayit_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.giris_cikis_kayitlari ALTER COLUMN kayit_id SET DEFAULT nextval('public.giris_cikis_kayitlari_kayit_id_seq'::regclass);


--
-- Name: hammadde_girisleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hammadde_girisleri ALTER COLUMN id SET DEFAULT nextval('public.hammadde_girisleri_id_seq'::regclass);


--
-- Name: hammaddeler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hammaddeler ALTER COLUMN id SET DEFAULT nextval('public.hammaddeler_id_seq'::regclass);


--
-- Name: izin_kayitlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.izin_kayitlari ALTER COLUMN id SET DEFAULT nextval('public.izin_kayitlari_id_seq'::regclass);


--
-- Name: kaliplar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kaliplar ALTER COLUMN id SET DEFAULT nextval('public.kaliplar_id_seq'::regclass);


--
-- Name: kalite_kontrol id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kalite_kontrol ALTER COLUMN id SET DEFAULT nextval('public.kalite_kontrol_id_seq'::regclass);


--
-- Name: kalite_kontrol_kayitlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kalite_kontrol_kayitlari ALTER COLUMN id SET DEFAULT nextval('public.kalite_kontrol_kayitlari_id_seq'::regclass);


--
-- Name: maas_bordrolari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maas_bordrolari ALTER COLUMN id SET DEFAULT nextval('public.maas_bordrolari_id_seq'::regclass);


--
-- Name: maaslar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maaslar ALTER COLUMN id SET DEFAULT nextval('public.maaslar_id_seq'::regclass);


--
-- Name: makine_bakim_kayitlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.makine_bakim_kayitlari ALTER COLUMN id SET DEFAULT nextval('public.makine_bakim_kayitlari_id_seq'::regclass);


--
-- Name: makineler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.makineler ALTER COLUMN id SET DEFAULT nextval('public.makineler_id_seq'::regclass);


--
-- Name: masraf_kayitlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.masraf_kayitlari ALTER COLUMN id SET DEFAULT nextval('public.masraf_kayitlari_id_seq'::regclass);


--
-- Name: masraflar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.masraflar ALTER COLUMN id SET DEFAULT nextval('public.masraflar_id_seq'::regclass);


--
-- Name: musteri_siparisleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.musteri_siparisleri ALTER COLUMN id SET DEFAULT nextval('public.musteri_siparisleri_id_seq'::regclass);


--
-- Name: musteriler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.musteriler ALTER COLUMN id SET DEFAULT nextval('public.musteriler_id_seq'::regclass);


--
-- Name: oyunlastirma_kayitlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oyunlastirma_kayitlari ALTER COLUMN id SET DEFAULT nextval('public.oyunlastirma_kayitlari_id_seq'::regclass);


--
-- Name: pazarlama_firmalari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pazarlama_firmalari ALTER COLUMN id SET DEFAULT nextval('public.pazarlama_firmalari_id_seq'::regclass);


--
-- Name: performans_degerlendirmeleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performans_degerlendirmeleri ALTER COLUMN id SET DEFAULT nextval('public.performans_degerlendirmeleri_id_seq'::regclass);


--
-- Name: personel id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel ALTER COLUMN id SET DEFAULT nextval('public.personel_id_seq'::regclass);


--
-- Name: personel_giris_cikis id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel_giris_cikis ALTER COLUMN id SET DEFAULT nextval('public.personel_giris_cikis_id_seq'::regclass);


--
-- Name: personel_vardiyalari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel_vardiyalari ALTER COLUMN id SET DEFAULT nextval('public.personel_vardiyalari_id_seq'::regclass);


--
-- Name: portal_kullanicilari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portal_kullanicilari ALTER COLUMN id SET DEFAULT nextval('public.portal_kullanicilari_id_seq'::regclass);


--
-- Name: saha_elemanlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saha_elemanlari ALTER COLUMN id SET DEFAULT nextval('public.saha_elemanlari_id_seq'::regclass);


--
-- Name: satin_alma_detaylari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_detaylari ALTER COLUMN id SET DEFAULT nextval('public.satin_alma_detaylari_id_seq'::regclass);


--
-- Name: satin_alma_siparisleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_siparisleri ALTER COLUMN id SET DEFAULT nextval('public.satin_alma_siparisleri_id_seq'::regclass);


--
-- Name: satin_alma_talepleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_talepleri ALTER COLUMN id SET DEFAULT nextval('public.satin_alma_talepleri_id_seq'::regclass);


--
-- Name: satis_siparisleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satis_siparisleri ALTER COLUMN id SET DEFAULT nextval('public.satis_siparisleri_id_seq'::regclass);


--
-- Name: scm_tedarikci_performans id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scm_tedarikci_performans ALTER COLUMN id SET DEFAULT nextval('public.scm_tedarikci_performans_id_seq'::regclass);


--
-- Name: sevkiyatlar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sevkiyatlar ALTER COLUMN id SET DEFAULT nextval('public.sevkiyatlar_id_seq'::regclass);


--
-- Name: siparis_detaylari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.siparis_detaylari ALTER COLUMN id SET DEFAULT nextval('public.siparis_detaylari_id_seq'::regclass);


--
-- Name: siparis_kalemleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.siparis_kalemleri ALTER COLUMN id SET DEFAULT nextval('public.siparis_kalemleri_id_seq'::regclass);


--
-- Name: sistem_ayarlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sistem_ayarlari ALTER COLUMN id SET DEFAULT nextval('public.sistem_ayarlari_id_seq'::regclass);


--
-- Name: stok_hareketleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stok_hareketleri ALTER COLUMN id SET DEFAULT nextval('public.stok_hareketleri_id_seq'::regclass);


--
-- Name: tedarikciler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tedarikciler ALTER COLUMN id SET DEFAULT nextval('public.tedarikciler_id_seq'::regclass);


--
-- Name: teklif_kalemleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teklif_kalemleri ALTER COLUMN id SET DEFAULT nextval('public.teklif_kalemleri_id_seq'::regclass);


--
-- Name: teklifler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teklifler ALTER COLUMN id SET DEFAULT nextval('public.teklifler_id_seq'::regclass);


--
-- Name: uretim_emirleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_emirleri ALTER COLUMN id SET DEFAULT nextval('public.uretim_emirleri_id_seq'::regclass);


--
-- Name: uretim_hammadde_kullanimi id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_hammadde_kullanimi ALTER COLUMN id SET DEFAULT nextval('public.uretim_hammadde_kullanimi_id_seq'::regclass);


--
-- Name: uretim_lot_kullanimi id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_lot_kullanimi ALTER COLUMN id SET DEFAULT nextval('public.uretim_lot_kullanimi_id_seq'::regclass);


--
-- Name: uretim_planlari id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_planlari ALTER COLUMN id SET DEFAULT nextval('public.uretim_planlari_id_seq'::regclass);


--
-- Name: urun_receteleri id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urun_receteleri ALTER COLUMN id SET DEFAULT nextval('public.urun_receteleri_id_seq'::regclass);


--
-- Name: urunler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urunler ALTER COLUMN id SET DEFAULT nextval('public.urunler_id_seq'::regclass);


--
-- Name: vardiyalar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vardiyalar ALTER COLUMN id SET DEFAULT nextval('public.vardiyalar_id_seq'::regclass);


--
-- Name: yoneticiler id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.yoneticiler ALTER COLUMN id SET DEFAULT nextval('public.yoneticiler_id_seq'::regclass);


--
-- Data for Name: alis_fatura_kalemleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alis_fatura_kalemleri (id, fatura_id, aciklama, miktar, birim, birim_fiyat, kdv_orani, toplam_fiyat) FROM stdin;
\.


--
-- Data for Name: alis_faturalari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alis_faturalari (id, tedarikci_id, fatura_numarasi, fatura_tarihi, vade_tarihi, toplam_tutar, kdv_tutari, genel_toplam, odeme_durumu, aciklama, kayit_tarihi) FROM stdin;
\.


--
-- Data for Name: belgeler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.belgeler (id, dosya_adi, dosya_yolu, dosya_tipi, dosya_boyutu, yukleme_tarihi, aciklama, iliski_tipi, iliski_id) FROM stdin;
\.


--
-- Data for Name: cari_hareketler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cari_hareketler (id, cari_id, islem_tipi, referans_id, borc, alacak, aciklama, tarih) FROM stdin;
\.


--
-- Data for Name: cari_hesaplar; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cari_hesaplar (id, hesap_kodu, hesap_adi, hesap_tipi, bakiye) FROM stdin;
\.


--
-- Data for Name: cari_islemler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cari_islemler (id, cari_hesap_id, fatura_id, tarih, aciklama, borc, alacak) FROM stdin;
\.


--
-- Data for Name: crm_aktiviteler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.crm_aktiviteler (id, musteri_id, firsat_id, personel_id, aktivite_tipi, tarih, notlar) FROM stdin;
\.


--
-- Data for Name: crm_firsatlar; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.crm_firsatlar (id, firsat_adi, musteri_id, sorumlu_personel_id, tahmini_tutar, asama, olusturma_tarihi, kapanis_tarihi) FROM stdin;
\.


--
-- Data for Name: destek_talepleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.destek_talepleri (id, talep_kodu, musteri_id, atanan_personel_id, konu, aciklama, durum, oncelik, olusturma_tarihi, cozulme_tarihi) FROM stdin;
\.


--
-- Data for Name: egitim_kayitlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.egitim_kayitlari (id, personel_id, egitim_adi, egitim_kurumu, baslangic_tarihi, bitis_tarihi, sertifika_path, aciklama, eklenme_tarihi) FROM stdin;
\.


--
-- Data for Name: enerji_tuketimi; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.enerji_tuketimi (id, donem, enerji_tipi, tuketim_miktari, birim) FROM stdin;
\.


--
-- Data for Name: faturalar; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.faturalar (id, fatura_no, fatura_tipi, cari_hesap_id, satis_siparisi_id, satin_alma_siparisi_id, tarih, vade_tarihi, tutar, kalan_tutar, durum) FROM stdin;
\.


--
-- Data for Name: finansal_islemler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.finansal_islemler (id, islem_tarihi, islem_tipi, aciklama, miktar, ilgili_cari_id, cari_tipi) FROM stdin;
\.


--
-- Data for Name: gelirler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.gelirler (id, aciklama, kategori, tutar, gelir_tarihi, gelir_alan_hesap_id) FROM stdin;
\.


--
-- Data for Name: giris_cikis_kayitlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.giris_cikis_kayitlari (kayit_id, personel_id, giris_zamani, cikis_zamani) FROM stdin;
1	1	2025-08-22 02:22:13.111443+03	\N
\.


--
-- Data for Name: hammadde_girisleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hammadde_girisleri (id, hammadde_id, lot_numarasi, giris_miktari, kalan_miktar, giris_tarihi, tedarikci) FROM stdin;
\.


--
-- Data for Name: hammaddeler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hammaddeler (id, hammadde_kodu, hammadde_adi, stok_miktari, birim, maliyet, kritik_stok_seviyesi, guvenlik_stogu, yeniden_siparis_noktasi) FROM stdin;
\.


--
-- Data for Name: izin_kayitlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.izin_kayitlari (id, personel_id, izin_tipi, baslangic_tarihi, bitis_tarihi, aciklama, eklenme_tarihi) FROM stdin;
\.


--
-- Data for Name: kaliplar; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.kaliplar (id, kalip_kodu, kalip_adi, goz_sayisi, cevrim_suresi_sn, garanti_baski_sayisi, mevcut_baski_sayisi, lokasyon, durum) FROM stdin;
\.


--
-- Data for Name: kalite_kontrol; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.kalite_kontrol (id, urun_id, kontrol_tarihi, kontrol_eden_personel_id, sonuc, aciklama) FROM stdin;
\.


--
-- Data for Name: kalite_kontrol_kayitlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.kalite_kontrol_kayitlari (id, uretim_emri_id, saglam_adet, fire_adet, fire_nedeni, kontrol_yapan_personel_id, kontrol_tarihi) FROM stdin;
\.


--
-- Data for Name: maas_bordrolari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.maas_bordrolari (id, personel_id, odeme_tarihi, net_maas) FROM stdin;
\.


--
-- Data for Name: maaslar; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.maaslar (id, personel_id, odeme_tarihi, net_maas, brut_maas, kesintiler, aciklama) FROM stdin;
\.


--
-- Data for Name: makine_bakim_kayitlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.makine_bakim_kayitlari (id, makine_id, personel_id, kayit_tipi, baslama_zamani, bitis_zamani, aciklama, durum) FROM stdin;
\.


--
-- Data for Name: makineler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.makineler (id, makine_adi, durum) FROM stdin;
\.


--
-- Data for Name: masraf_kayitlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.masraf_kayitlari (id, tarih, aciklama, kategori, tutar, odeme_yapan_hesap_id) FROM stdin;
\.


--
-- Data for Name: masraflar; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.masraflar (id, aciklama, kategori, tutar, tarih) FROM stdin;
\.


--
-- Data for Name: musteri_siparisleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.musteri_siparisleri (id, saha_elemani_id, musteri_adi, siparis_tarihi, toplam_tutar, durum) FROM stdin;
\.


--
-- Data for Name: musteriler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.musteriler (id, ad, adres, telefon, email, vergi_no, sorumlu_kisi, vergi_dairesi) FROM stdin;
\.


--
-- Data for Name: oyunlastirma_kayitlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.oyunlastirma_kayitlari (id, personel_id, puan, aciklama, kayit_tarihi) FROM stdin;
1	1	50	hi├ğ fre yok 	2025-08-22
\.


--
-- Data for Name: pazarlama_firmalari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pazarlama_firmalari (id, firma_adi, email, sektor, sorumlu_kisi, olusturma_tarihi) FROM stdin;
1	─░n┼şaat Firmas─▒ 1 A.┼Ş.	iletisim1@insaat.com	─░n┼şaat	\N	2025-08-24 15:02:16.748344+03
2	─░n┼şaat Firmas─▒ 2 A.┼Ş.	iletisim2@insaat.com	─░n┼şaat	\N	2025-08-24 15:02:16.750846+03
3	─░n┼şaat Firmas─▒ 3 A.┼Ş.	iletisim3@insaat.com	─░n┼şaat	\N	2025-08-24 15:02:16.751541+03
4	─░n┼şaat Firmas─▒ 4 A.┼Ş.	iletisim4@insaat.com	─░n┼şaat	\N	2025-08-24 15:02:16.752147+03
5	─░n┼şaat Firmas─▒ 5 A.┼Ş.	iletisim5@insaat.com	─░n┼şaat	\N	2025-08-24 15:02:16.753092+03
\.


--
-- Data for Name: performans_degerlendirmeleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.performans_degerlendirmeleri (id, personel_id, degerlendirme_tarihi, degerlendiren_yonetici, puan, yonetici_notlari, eklenme_tarihi) FROM stdin;
\.


--
-- Data for Name: personel; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.personel (id, ad_soyad, pozisyon, ise_giris_tarihi, aktif_mi, brut_maas, net_maas, tc_kimlik_no, dogum_tarihi, telefon, adres) FROM stdin;
\.


--
-- Data for Name: personel_giris_cikis; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.personel_giris_cikis (id, personel_id, giris_zamani, cikis_zamani) FROM stdin;
\.


--
-- Data for Name: personel_vardiyalari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.personel_vardiyalari (id, personel_id, vardiya_id, tarih) FROM stdin;
\.


--
-- Data for Name: portal_kullanicilari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.portal_kullanicilari (id, kullanici_adi, sifre_hash, rol, musteri_id, tedarikci_id, aktif_mi, olusturulma_tarihi) FROM stdin;
\.


--
-- Data for Name: saha_elemanlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.saha_elemanlari (id, kullanici_adi, sifre_hash, ad_soyad, aktif, olusturma_tarihi) FROM stdin;
\.


--
-- Data for Name: satin_alma_detaylari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.satin_alma_detaylari (id, siparis_id, hammadde_id, miktar, birim_fiyat) FROM stdin;
\.


--
-- Data for Name: satin_alma_siparisleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.satin_alma_siparisleri (id, siparis_kodu, tedarikci_id, siparis_tarihi, beklenen_teslim_tarihi, durum, kargo_takip_no, tahmini_varis_tarihi) FROM stdin;
\.


--
-- Data for Name: satin_alma_talepleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.satin_alma_talepleri (id, hammadde_id, talep_edilen_miktar, birim, talep_tarihi, durum, aciklama) FROM stdin;
\.


--
-- Data for Name: satis_siparisleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.satis_siparisleri (id, siparis_kodu, durum, siparis_tarihi, musteri_id, toplam_tutar, kdv_tutari, genel_toplam) FROM stdin;
\.


--
-- Data for Name: scm_tedarikci_performans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scm_tedarikci_performans (id, tedarikci_id, degerlendirme_tarihi, kalite_puani, teslimat_hizi_puani, fiyat_puani, genel_puan, notlar) FROM stdin;
\.


--
-- Data for Name: sevkiyatlar; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sevkiyatlar (id, satis_siparis_id, kargo_firmasi, takip_numarasi, sevk_tarihi, durum, kargo_fisi_path, notlar, kayit_tarihi) FROM stdin;
\.


--
-- Data for Name: siparis_detaylari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.siparis_detaylari (id, siparis_id, urun_id, miktar) FROM stdin;
\.


--
-- Data for Name: siparis_kalemleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.siparis_kalemleri (id, siparis_id, urun_id, miktar, birim, birim_fiyat, toplam_fiyat, kdv_orani) FROM stdin;
\.


--
-- Data for Name: sistem_ayarlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sistem_ayarlari (id, ayar_anahtari, ayar_degeri, aciklama) FROM stdin;
1	firma_adi	D├╝─şmeci Makina San. ve Tic. A.┼Ş.	Fi┼ş ve faturalarda g├Âr├╝necek resmi firma ad─▒
2	firma_adresi	Organize Sanayi B├Âlgesi, 12. Cadde No: 34, Kayseri	Firman─▒n tam adresi
3	firma_telefon	0352 123 45 67	Firman─▒n telefon numaras─▒
4	firma_email	info@dugmecimakina.com	Firman─▒n e-posta adresi
5	firma_logo_yolu	/static/logo.png	Fi┼şlerde kullan─▒lacak firma logosunun yolu
6	firma_yetkili_kisi	Ak─▒n S├╝mengen	Tekliflerde g├Âr├╝necek yetkili ki┼şi ad─▒
8	firma_website	https://www.google.com	QR Kod i├ğin kullan─▒lacak web sitesi adresi
9	birim_maliyet_elektrik	4.55	Elektrik i├ğin kWh ba┼ş─▒na maliyet (TL)
10	birim_maliyet_dogalgaz	12.80	Do─şalgaz i├ğin m┬│ ba┼ş─▒na maliyet (TL)
11	birim_maliyet_su	9.75	Su i├ğin m┬│ ba┼ş─▒na maliyet (TL)
7	maas_sifresi	656514	Maa┼ş y├Ânetimi sayfas─▒na eri┼şim ┼şifresi
\.


--
-- Data for Name: stok_hareketleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.stok_hareketleri (id, hareket_tipi, urun_id, hammadde_id, miktar, tarih, aciklama) FROM stdin;
\.


--
-- Data for Name: tedarikciler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tedarikciler (id, firma_adi, yetkili_kisi, email, telefon, vergi_dairesi, vergi_no) FROM stdin;
\.


--
-- Data for Name: teklif_kalemleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.teklif_kalemleri (id, teklif_id, aciklama, urun_id, miktar, birim, birim_fiyat, kdv_orani, toplam_fiyat) FROM stdin;
\.


--
-- Data for Name: teklifler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.teklifler (id, teklif_kodu, musteri_id, teklif_tarihi, gecerlilik_tarihi, durum, toplam_tutar, kdv_tutari, genel_toplam, notlar) FROM stdin;
\.


--
-- Data for Name: uretim_emirleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.uretim_emirleri (id, is_emri_kodu, urun_id, hedef_miktar, uretilen_miktar, durum, olusturma_tarihi, baslama_tarihi, bitis_tarihi, atanan_makine_id, sorumlu_personel_id, tahmini_baslama_tarihi, tahmini_bitis_tarihi, toplam_maliyet, arsivlendi, atanan_kalip_id) FROM stdin;
\.


--
-- Data for Name: uretim_hammadde_kullanimi; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.uretim_hammadde_kullanimi (id, uretim_emri_id, hammadde_giris_id, kullanilan_miktar) FROM stdin;
\.


--
-- Data for Name: uretim_lot_kullanimi; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.uretim_lot_kullanimi (id, uretim_emri_id, hammadde_giris_id, kullanilan_miktar, kayit_tarihi) FROM stdin;
\.


--
-- Data for Name: uretim_planlari; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.uretim_planlari (id, plan_adi, satis_id, olusturma_tarihi, baslangic_tarihi, bitis_tarihi, durum) FROM stdin;
\.


--
-- Data for Name: urun_receteleri; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.urun_receteleri (id, urun_id, hammadde_id, miktar) FROM stdin;
\.


--
-- Data for Name: urunler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.urunler (id, urun_kodu, urun_adi, stok_miktari, birim_fiyat) FROM stdin;
\.


--
-- Data for Name: vardiyalar; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.vardiyalar (id, vardiya_adi, baslangic_saati, bitis_saati) FROM stdin;
\.


--
-- Data for Name: yoneticiler; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.yoneticiler (id, kullanici_adi, sifre_hash, ad_soyad, email, aktif, olusturma_tarihi) FROM stdin;
1	admin	$2b$12$gYm/o228x8508fW8yp2G6eI7bWq.v0pEBwLd6k/9yZ4.G7a60p5.2	Ak─▒n S├╝mergen	akin.sumengenn@gmail.com	t	2025-08-26 04:01:36.391851+03
\.


--
-- Name: alis_fatura_kalemleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.alis_fatura_kalemleri_id_seq', 1, false);


--
-- Name: alis_faturalari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.alis_faturalari_id_seq', 1, false);


--
-- Name: belgeler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.belgeler_id_seq', 1, false);


--
-- Name: cari_hareketler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cari_hareketler_id_seq', 1, false);


--
-- Name: cari_hesaplar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cari_hesaplar_id_seq', 1, false);


--
-- Name: cari_islemler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cari_islemler_id_seq', 1, false);


--
-- Name: crm_aktiviteler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.crm_aktiviteler_id_seq', 1, false);


--
-- Name: crm_firsatlar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.crm_firsatlar_id_seq', 1, false);


--
-- Name: destek_talepleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.destek_talepleri_id_seq', 1, false);


--
-- Name: egitim_kayitlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.egitim_kayitlari_id_seq', 1, false);


--
-- Name: enerji_tuketimi_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.enerji_tuketimi_id_seq', 1, false);


--
-- Name: faturalar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.faturalar_id_seq', 1, false);


--
-- Name: finansal_islemler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.finansal_islemler_id_seq', 1, false);


--
-- Name: gelirler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.gelirler_id_seq', 1, false);


--
-- Name: giris_cikis_kayitlari_kayit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.giris_cikis_kayitlari_kayit_id_seq', 1, true);


--
-- Name: hammadde_girisleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.hammadde_girisleri_id_seq', 1, false);


--
-- Name: hammaddeler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.hammaddeler_id_seq', 1, false);


--
-- Name: izin_kayitlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.izin_kayitlari_id_seq', 1, false);


--
-- Name: kaliplar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.kaliplar_id_seq', 1, false);


--
-- Name: kalite_kontrol_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.kalite_kontrol_id_seq', 1, false);


--
-- Name: kalite_kontrol_kayitlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.kalite_kontrol_kayitlari_id_seq', 1, false);


--
-- Name: maas_bordrolari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.maas_bordrolari_id_seq', 1, false);


--
-- Name: maaslar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.maaslar_id_seq', 1, false);


--
-- Name: makine_bakim_kayitlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.makine_bakim_kayitlari_id_seq', 1, false);


--
-- Name: makineler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.makineler_id_seq', 1, false);


--
-- Name: masraf_kayitlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.masraf_kayitlari_id_seq', 1, false);


--
-- Name: masraflar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.masraflar_id_seq', 1, true);


--
-- Name: musteri_siparisleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.musteri_siparisleri_id_seq', 1, false);


--
-- Name: musteriler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.musteriler_id_seq', 1, false);


--
-- Name: oyunlastirma_kayitlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.oyunlastirma_kayitlari_id_seq', 1, true);


--
-- Name: pazarlama_firmalari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pazarlama_firmalari_id_seq', 5, true);


--
-- Name: performans_degerlendirmeleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.performans_degerlendirmeleri_id_seq', 1, false);


--
-- Name: personel_giris_cikis_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.personel_giris_cikis_id_seq', 1, false);


--
-- Name: personel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.personel_id_seq', 1, false);


--
-- Name: personel_vardiyalari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.personel_vardiyalari_id_seq', 1, false);


--
-- Name: portal_kullanicilari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.portal_kullanicilari_id_seq', 1, false);


--
-- Name: saha_elemanlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.saha_elemanlari_id_seq', 1, false);


--
-- Name: satin_alma_detaylari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.satin_alma_detaylari_id_seq', 1, false);


--
-- Name: satin_alma_siparisleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.satin_alma_siparisleri_id_seq', 1, false);


--
-- Name: satin_alma_talepleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.satin_alma_talepleri_id_seq', 1, false);


--
-- Name: satis_siparisleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.satis_siparisleri_id_seq', 1, false);


--
-- Name: scm_tedarikci_performans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.scm_tedarikci_performans_id_seq', 1, false);


--
-- Name: sevkiyatlar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sevkiyatlar_id_seq', 1, false);


--
-- Name: siparis_detaylari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.siparis_detaylari_id_seq', 1, false);


--
-- Name: siparis_kalemleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.siparis_kalemleri_id_seq', 1, false);


--
-- Name: sistem_ayarlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sistem_ayarlari_id_seq', 22, true);


--
-- Name: stok_hareketleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.stok_hareketleri_id_seq', 1, false);


--
-- Name: tedarikciler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tedarikciler_id_seq', 1, false);


--
-- Name: teklif_kalemleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.teklif_kalemleri_id_seq', 1, false);


--
-- Name: teklifler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.teklifler_id_seq', 1, false);


--
-- Name: uretim_emirleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.uretim_emirleri_id_seq', 1, false);


--
-- Name: uretim_hammadde_kullanimi_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.uretim_hammadde_kullanimi_id_seq', 1, false);


--
-- Name: uretim_lot_kullanimi_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.uretim_lot_kullanimi_id_seq', 1, false);


--
-- Name: uretim_planlari_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.uretim_planlari_id_seq', 1, false);


--
-- Name: urun_receteleri_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.urun_receteleri_id_seq', 1, false);


--
-- Name: urunler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.urunler_id_seq', 1, false);


--
-- Name: vardiyalar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.vardiyalar_id_seq', 1, false);


--
-- Name: yoneticiler_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.yoneticiler_id_seq', 1, true);


--
-- Name: alis_fatura_kalemleri alis_fatura_kalemleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alis_fatura_kalemleri
    ADD CONSTRAINT alis_fatura_kalemleri_pkey PRIMARY KEY (id);


--
-- Name: alis_faturalari alis_faturalari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alis_faturalari
    ADD CONSTRAINT alis_faturalari_pkey PRIMARY KEY (id);


--
-- Name: belgeler belgeler_dosya_yolu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.belgeler
    ADD CONSTRAINT belgeler_dosya_yolu_key UNIQUE (dosya_yolu);


--
-- Name: belgeler belgeler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.belgeler
    ADD CONSTRAINT belgeler_pkey PRIMARY KEY (id);


--
-- Name: cari_hareketler cari_hareketler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_hareketler
    ADD CONSTRAINT cari_hareketler_pkey PRIMARY KEY (id);


--
-- Name: cari_hesaplar cari_hesaplar_hesap_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_hesaplar
    ADD CONSTRAINT cari_hesaplar_hesap_kodu_key UNIQUE (hesap_kodu);


--
-- Name: cari_hesaplar cari_hesaplar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_hesaplar
    ADD CONSTRAINT cari_hesaplar_pkey PRIMARY KEY (id);


--
-- Name: cari_islemler cari_islemler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_islemler
    ADD CONSTRAINT cari_islemler_pkey PRIMARY KEY (id);


--
-- Name: crm_aktiviteler crm_aktiviteler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_aktiviteler
    ADD CONSTRAINT crm_aktiviteler_pkey PRIMARY KEY (id);


--
-- Name: crm_firsatlar crm_firsatlar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_firsatlar
    ADD CONSTRAINT crm_firsatlar_pkey PRIMARY KEY (id);


--
-- Name: destek_talepleri destek_talepleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destek_talepleri
    ADD CONSTRAINT destek_talepleri_pkey PRIMARY KEY (id);


--
-- Name: destek_talepleri destek_talepleri_talep_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.destek_talepleri
    ADD CONSTRAINT destek_talepleri_talep_kodu_key UNIQUE (talep_kodu);


--
-- Name: egitim_kayitlari egitim_kayitlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.egitim_kayitlari
    ADD CONSTRAINT egitim_kayitlari_pkey PRIMARY KEY (id);


--
-- Name: enerji_tuketimi enerji_tuketimi_donem_enerji_tipi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enerji_tuketimi
    ADD CONSTRAINT enerji_tuketimi_donem_enerji_tipi_key UNIQUE (donem, enerji_tipi);


--
-- Name: enerji_tuketimi enerji_tuketimi_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enerji_tuketimi
    ADD CONSTRAINT enerji_tuketimi_pkey PRIMARY KEY (id);


--
-- Name: faturalar faturalar_fatura_no_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faturalar
    ADD CONSTRAINT faturalar_fatura_no_key UNIQUE (fatura_no);


--
-- Name: faturalar faturalar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faturalar
    ADD CONSTRAINT faturalar_pkey PRIMARY KEY (id);


--
-- Name: finansal_islemler finansal_islemler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finansal_islemler
    ADD CONSTRAINT finansal_islemler_pkey PRIMARY KEY (id);


--
-- Name: gelirler gelirler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gelirler
    ADD CONSTRAINT gelirler_pkey PRIMARY KEY (id);


--
-- Name: giris_cikis_kayitlari giris_cikis_kayitlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.giris_cikis_kayitlari
    ADD CONSTRAINT giris_cikis_kayitlari_pkey PRIMARY KEY (kayit_id);


--
-- Name: hammadde_girisleri hammadde_girisleri_lot_numarasi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hammadde_girisleri
    ADD CONSTRAINT hammadde_girisleri_lot_numarasi_key UNIQUE (lot_numarasi);


--
-- Name: hammadde_girisleri hammadde_girisleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hammadde_girisleri
    ADD CONSTRAINT hammadde_girisleri_pkey PRIMARY KEY (id);


--
-- Name: hammaddeler hammaddeler_hammadde_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hammaddeler
    ADD CONSTRAINT hammaddeler_hammadde_kodu_key UNIQUE (hammadde_kodu);


--
-- Name: hammaddeler hammaddeler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hammaddeler
    ADD CONSTRAINT hammaddeler_pkey PRIMARY KEY (id);


--
-- Name: izin_kayitlari izin_kayitlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.izin_kayitlari
    ADD CONSTRAINT izin_kayitlari_pkey PRIMARY KEY (id);


--
-- Name: kaliplar kaliplar_kalip_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kaliplar
    ADD CONSTRAINT kaliplar_kalip_kodu_key UNIQUE (kalip_kodu);


--
-- Name: kaliplar kaliplar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kaliplar
    ADD CONSTRAINT kaliplar_pkey PRIMARY KEY (id);


--
-- Name: kalite_kontrol_kayitlari kalite_kontrol_kayitlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kalite_kontrol_kayitlari
    ADD CONSTRAINT kalite_kontrol_kayitlari_pkey PRIMARY KEY (id);


--
-- Name: kalite_kontrol_kayitlari kalite_kontrol_kayitlari_uretim_emri_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kalite_kontrol_kayitlari
    ADD CONSTRAINT kalite_kontrol_kayitlari_uretim_emri_id_key UNIQUE (uretim_emri_id);


--
-- Name: kalite_kontrol kalite_kontrol_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kalite_kontrol
    ADD CONSTRAINT kalite_kontrol_pkey PRIMARY KEY (id);


--
-- Name: maas_bordrolari maas_bordrolari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maas_bordrolari
    ADD CONSTRAINT maas_bordrolari_pkey PRIMARY KEY (id);


--
-- Name: maaslar maaslar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maaslar
    ADD CONSTRAINT maaslar_pkey PRIMARY KEY (id);


--
-- Name: makine_bakim_kayitlari makine_bakim_kayitlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.makine_bakim_kayitlari
    ADD CONSTRAINT makine_bakim_kayitlari_pkey PRIMARY KEY (id);


--
-- Name: makineler makineler_makine_adi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.makineler
    ADD CONSTRAINT makineler_makine_adi_key UNIQUE (makine_adi);


--
-- Name: makineler makineler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.makineler
    ADD CONSTRAINT makineler_pkey PRIMARY KEY (id);


--
-- Name: masraf_kayitlari masraf_kayitlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.masraf_kayitlari
    ADD CONSTRAINT masraf_kayitlari_pkey PRIMARY KEY (id);


--
-- Name: masraflar masraflar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.masraflar
    ADD CONSTRAINT masraflar_pkey PRIMARY KEY (id);


--
-- Name: musteri_siparisleri musteri_siparisleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.musteri_siparisleri
    ADD CONSTRAINT musteri_siparisleri_pkey PRIMARY KEY (id);


--
-- Name: musteriler musteriler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.musteriler
    ADD CONSTRAINT musteriler_pkey PRIMARY KEY (id);


--
-- Name: oyunlastirma_kayitlari oyunlastirma_kayitlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oyunlastirma_kayitlari
    ADD CONSTRAINT oyunlastirma_kayitlari_pkey PRIMARY KEY (id);


--
-- Name: pazarlama_firmalari pazarlama_firmalari_firma_adi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pazarlama_firmalari
    ADD CONSTRAINT pazarlama_firmalari_firma_adi_key UNIQUE (firma_adi);


--
-- Name: pazarlama_firmalari pazarlama_firmalari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pazarlama_firmalari
    ADD CONSTRAINT pazarlama_firmalari_pkey PRIMARY KEY (id);


--
-- Name: performans_degerlendirmeleri performans_degerlendirmeleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performans_degerlendirmeleri
    ADD CONSTRAINT performans_degerlendirmeleri_pkey PRIMARY KEY (id);


--
-- Name: personel_giris_cikis personel_giris_cikis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel_giris_cikis
    ADD CONSTRAINT personel_giris_cikis_pkey PRIMARY KEY (id);


--
-- Name: personel personel_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel
    ADD CONSTRAINT personel_pkey PRIMARY KEY (id);


--
-- Name: personel_vardiyalari personel_vardiyalari_personel_id_tarih_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel_vardiyalari
    ADD CONSTRAINT personel_vardiyalari_personel_id_tarih_key UNIQUE (personel_id, tarih);


--
-- Name: personel_vardiyalari personel_vardiyalari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel_vardiyalari
    ADD CONSTRAINT personel_vardiyalari_pkey PRIMARY KEY (id);


--
-- Name: portal_kullanicilari portal_kullanicilari_kullanici_adi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portal_kullanicilari
    ADD CONSTRAINT portal_kullanicilari_kullanici_adi_key UNIQUE (kullanici_adi);


--
-- Name: portal_kullanicilari portal_kullanicilari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portal_kullanicilari
    ADD CONSTRAINT portal_kullanicilari_pkey PRIMARY KEY (id);


--
-- Name: saha_elemanlari saha_elemanlari_kullanici_adi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saha_elemanlari
    ADD CONSTRAINT saha_elemanlari_kullanici_adi_key UNIQUE (kullanici_adi);


--
-- Name: saha_elemanlari saha_elemanlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.saha_elemanlari
    ADD CONSTRAINT saha_elemanlari_pkey PRIMARY KEY (id);


--
-- Name: satin_alma_detaylari satin_alma_detaylari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_detaylari
    ADD CONSTRAINT satin_alma_detaylari_pkey PRIMARY KEY (id);


--
-- Name: satin_alma_siparisleri satin_alma_siparisleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_siparisleri
    ADD CONSTRAINT satin_alma_siparisleri_pkey PRIMARY KEY (id);


--
-- Name: satin_alma_siparisleri satin_alma_siparisleri_siparis_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_siparisleri
    ADD CONSTRAINT satin_alma_siparisleri_siparis_kodu_key UNIQUE (siparis_kodu);


--
-- Name: satin_alma_talepleri satin_alma_talepleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_talepleri
    ADD CONSTRAINT satin_alma_talepleri_pkey PRIMARY KEY (id);


--
-- Name: satis_siparisleri satis_siparisleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satis_siparisleri
    ADD CONSTRAINT satis_siparisleri_pkey PRIMARY KEY (id);


--
-- Name: satis_siparisleri satis_siparisleri_siparis_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satis_siparisleri
    ADD CONSTRAINT satis_siparisleri_siparis_kodu_key UNIQUE (siparis_kodu);


--
-- Name: scm_tedarikci_performans scm_tedarikci_performans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scm_tedarikci_performans
    ADD CONSTRAINT scm_tedarikci_performans_pkey PRIMARY KEY (id);


--
-- Name: sevkiyatlar sevkiyatlar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sevkiyatlar
    ADD CONSTRAINT sevkiyatlar_pkey PRIMARY KEY (id);


--
-- Name: siparis_detaylari siparis_detaylari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.siparis_detaylari
    ADD CONSTRAINT siparis_detaylari_pkey PRIMARY KEY (id);


--
-- Name: siparis_kalemleri siparis_kalemleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.siparis_kalemleri
    ADD CONSTRAINT siparis_kalemleri_pkey PRIMARY KEY (id);


--
-- Name: sistem_ayarlari sistem_ayarlari_ayar_anahtari_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sistem_ayarlari
    ADD CONSTRAINT sistem_ayarlari_ayar_anahtari_key UNIQUE (ayar_anahtari);


--
-- Name: sistem_ayarlari sistem_ayarlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sistem_ayarlari
    ADD CONSTRAINT sistem_ayarlari_pkey PRIMARY KEY (id);


--
-- Name: stok_hareketleri stok_hareketleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stok_hareketleri
    ADD CONSTRAINT stok_hareketleri_pkey PRIMARY KEY (id);


--
-- Name: tedarikciler tedarikciler_firma_adi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tedarikciler
    ADD CONSTRAINT tedarikciler_firma_adi_key UNIQUE (firma_adi);


--
-- Name: tedarikciler tedarikciler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tedarikciler
    ADD CONSTRAINT tedarikciler_pkey PRIMARY KEY (id);


--
-- Name: teklif_kalemleri teklif_kalemleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teklif_kalemleri
    ADD CONSTRAINT teklif_kalemleri_pkey PRIMARY KEY (id);


--
-- Name: teklifler teklifler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teklifler
    ADD CONSTRAINT teklifler_pkey PRIMARY KEY (id);


--
-- Name: teklifler teklifler_teklif_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teklifler
    ADD CONSTRAINT teklifler_teklif_kodu_key UNIQUE (teklif_kodu);


--
-- Name: maas_bordrolari unique_personel_donem; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maas_bordrolari
    ADD CONSTRAINT unique_personel_donem UNIQUE (personel_id, odeme_tarihi);


--
-- Name: alis_faturalari uq_tedarikci_fatura; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alis_faturalari
    ADD CONSTRAINT uq_tedarikci_fatura UNIQUE (tedarikci_id, fatura_numarasi);


--
-- Name: uretim_emirleri uretim_emirleri_is_emri_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_emirleri
    ADD CONSTRAINT uretim_emirleri_is_emri_kodu_key UNIQUE (is_emri_kodu);


--
-- Name: uretim_emirleri uretim_emirleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_emirleri
    ADD CONSTRAINT uretim_emirleri_pkey PRIMARY KEY (id);


--
-- Name: uretim_hammadde_kullanimi uretim_hammadde_kullanimi_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_hammadde_kullanimi
    ADD CONSTRAINT uretim_hammadde_kullanimi_pkey PRIMARY KEY (id);


--
-- Name: uretim_lot_kullanimi uretim_lot_kullanimi_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_lot_kullanimi
    ADD CONSTRAINT uretim_lot_kullanimi_pkey PRIMARY KEY (id);


--
-- Name: uretim_planlari uretim_planlari_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_planlari
    ADD CONSTRAINT uretim_planlari_pkey PRIMARY KEY (id);


--
-- Name: urun_receteleri urun_receteleri_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urun_receteleri
    ADD CONSTRAINT urun_receteleri_pkey PRIMARY KEY (id);


--
-- Name: urun_receteleri urun_receteleri_urun_id_hammadde_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urun_receteleri
    ADD CONSTRAINT urun_receteleri_urun_id_hammadde_id_key UNIQUE (urun_id, hammadde_id);


--
-- Name: urunler urunler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urunler
    ADD CONSTRAINT urunler_pkey PRIMARY KEY (id);


--
-- Name: urunler urunler_urun_kodu_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urunler
    ADD CONSTRAINT urunler_urun_kodu_key UNIQUE (urun_kodu);


--
-- Name: vardiyalar vardiyalar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vardiyalar
    ADD CONSTRAINT vardiyalar_pkey PRIMARY KEY (id);


--
-- Name: vardiyalar vardiyalar_vardiya_adi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vardiyalar
    ADD CONSTRAINT vardiyalar_vardiya_adi_key UNIQUE (vardiya_adi);


--
-- Name: yoneticiler yoneticiler_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.yoneticiler
    ADD CONSTRAINT yoneticiler_email_key UNIQUE (email);


--
-- Name: yoneticiler yoneticiler_kullanici_adi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.yoneticiler
    ADD CONSTRAINT yoneticiler_kullanici_adi_key UNIQUE (kullanici_adi);


--
-- Name: yoneticiler yoneticiler_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.yoneticiler
    ADD CONSTRAINT yoneticiler_pkey PRIMARY KEY (id);


--
-- Name: idx_belgeler_iliski; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_belgeler_iliski ON public.belgeler USING btree (iliski_tipi, iliski_id);


--
-- Name: idx_cari_islemler_cari_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cari_islemler_cari_id ON public.cari_islemler USING btree (cari_hesap_id);


--
-- Name: idx_crm_aktiviteler_musteri_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_crm_aktiviteler_musteri_id ON public.crm_aktiviteler USING btree (musteri_id);


--
-- Name: idx_crm_firsatlar_asama; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_crm_firsatlar_asama ON public.crm_firsatlar USING btree (asama);


--
-- Name: idx_crm_firsatlar_musteri_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_crm_firsatlar_musteri_id ON public.crm_firsatlar USING btree (musteri_id);


--
-- Name: idx_destek_talepleri_durum; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destek_talepleri_durum ON public.destek_talepleri USING btree (durum);


--
-- Name: idx_destek_talepleri_musteri_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_destek_talepleri_musteri_id ON public.destek_talepleri USING btree (musteri_id);


--
-- Name: idx_faturalar_cari_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_faturalar_cari_id ON public.faturalar USING btree (cari_hesap_id);


--
-- Name: idx_unique_satis_id_in_plan; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_unique_satis_id_in_plan ON public.uretim_planlari USING btree (satis_id) WHERE (satis_id IS NOT NULL);


--
-- Name: idx_uretim_lot_kullanimi_hammadde_giris_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_uretim_lot_kullanimi_hammadde_giris_id ON public.uretim_lot_kullanimi USING btree (hammadde_giris_id);


--
-- Name: idx_uretim_lot_kullanimi_uretim_emri_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_uretim_lot_kullanimi_uretim_emri_id ON public.uretim_lot_kullanimi USING btree (uretim_emri_id);


--
-- Name: alis_fatura_kalemleri alis_fatura_kalemleri_fatura_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alis_fatura_kalemleri
    ADD CONSTRAINT alis_fatura_kalemleri_fatura_id_fkey FOREIGN KEY (fatura_id) REFERENCES public.alis_faturalari(id) ON DELETE CASCADE;


--
-- Name: alis_faturalari alis_faturalari_tedarikci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alis_faturalari
    ADD CONSTRAINT alis_faturalari_tedarikci_id_fkey FOREIGN KEY (tedarikci_id) REFERENCES public.tedarikciler(id) ON DELETE SET NULL;


--
-- Name: cari_hareketler cari_hareketler_cari_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_hareketler
    ADD CONSTRAINT cari_hareketler_cari_id_fkey FOREIGN KEY (cari_id) REFERENCES public.musteriler(id) ON DELETE CASCADE;


--
-- Name: cari_islemler cari_islemler_fatura_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cari_islemler
    ADD CONSTRAINT cari_islemler_fatura_id_fkey FOREIGN KEY (fatura_id) REFERENCES public.faturalar(id);


--
-- Name: crm_aktiviteler crm_aktiviteler_firsat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crm_aktiviteler
    ADD CONSTRAINT crm_aktiviteler_firsat_id_fkey FOREIGN KEY (firsat_id) REFERENCES public.crm_firsatlar(id);


--
-- Name: egitim_kayitlari egitim_kayitlari_personel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.egitim_kayitlari
    ADD CONSTRAINT egitim_kayitlari_personel_id_fkey FOREIGN KEY (personel_id) REFERENCES public.personel(id) ON DELETE CASCADE;


--
-- Name: faturalar faturalar_satin_alma_siparisi_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faturalar
    ADD CONSTRAINT faturalar_satin_alma_siparisi_id_fkey FOREIGN KEY (satin_alma_siparisi_id) REFERENCES public.satin_alma_siparisleri(id);


--
-- Name: finansal_islemler fk_cari; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.finansal_islemler
    ADD CONSTRAINT fk_cari FOREIGN KEY (ilgili_cari_id) REFERENCES public.musteriler(id);


--
-- Name: satis_siparisleri fk_musteri; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satis_siparisleri
    ADD CONSTRAINT fk_musteri FOREIGN KEY (musteri_id) REFERENCES public.musteriler(id);


--
-- Name: maaslar fk_personel; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maaslar
    ADD CONSTRAINT fk_personel FOREIGN KEY (personel_id) REFERENCES public.personel(id);


--
-- Name: gelirler gelirler_gelir_alan_hesap_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gelirler
    ADD CONSTRAINT gelirler_gelir_alan_hesap_id_fkey FOREIGN KEY (gelir_alan_hesap_id) REFERENCES public.cari_hesaplar(id);


--
-- Name: hammadde_girisleri hammadde_girisleri_hammadde_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hammadde_girisleri
    ADD CONSTRAINT hammadde_girisleri_hammadde_id_fkey FOREIGN KEY (hammadde_id) REFERENCES public.hammaddeler(id);


--
-- Name: izin_kayitlari izin_kayitlari_personel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.izin_kayitlari
    ADD CONSTRAINT izin_kayitlari_personel_id_fkey FOREIGN KEY (personel_id) REFERENCES public.personel(id) ON DELETE CASCADE;


--
-- Name: kalite_kontrol_kayitlari kalite_kontrol_kayitlari_uretim_emri_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kalite_kontrol_kayitlari
    ADD CONSTRAINT kalite_kontrol_kayitlari_uretim_emri_id_fkey FOREIGN KEY (uretim_emri_id) REFERENCES public.uretim_emirleri(id);


--
-- Name: kalite_kontrol kalite_kontrol_kontrol_eden_personel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kalite_kontrol
    ADD CONSTRAINT kalite_kontrol_kontrol_eden_personel_id_fkey FOREIGN KEY (kontrol_eden_personel_id) REFERENCES public.personel(id) ON DELETE SET NULL;


--
-- Name: kalite_kontrol kalite_kontrol_urun_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kalite_kontrol
    ADD CONSTRAINT kalite_kontrol_urun_id_fkey FOREIGN KEY (urun_id) REFERENCES public.urunler(id) ON DELETE CASCADE;


--
-- Name: maas_bordrolari maas_bordrolari_personel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maas_bordrolari
    ADD CONSTRAINT maas_bordrolari_personel_id_fkey FOREIGN KEY (personel_id) REFERENCES public.personel(id) ON DELETE CASCADE;


--
-- Name: maaslar maaslar_personel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maaslar
    ADD CONSTRAINT maaslar_personel_id_fkey FOREIGN KEY (personel_id) REFERENCES public.personel(id) ON DELETE CASCADE;


--
-- Name: makine_bakim_kayitlari makine_bakim_kayitlari_makine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.makine_bakim_kayitlari
    ADD CONSTRAINT makine_bakim_kayitlari_makine_id_fkey FOREIGN KEY (makine_id) REFERENCES public.makineler(id);


--
-- Name: musteri_siparisleri musteri_siparisleri_saha_elemani_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.musteri_siparisleri
    ADD CONSTRAINT musteri_siparisleri_saha_elemani_id_fkey FOREIGN KEY (saha_elemani_id) REFERENCES public.saha_elemanlari(id);


--
-- Name: performans_degerlendirmeleri performans_degerlendirmeleri_personel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performans_degerlendirmeleri
    ADD CONSTRAINT performans_degerlendirmeleri_personel_id_fkey FOREIGN KEY (personel_id) REFERENCES public.personel(id) ON DELETE CASCADE;


--
-- Name: personel_giris_cikis personel_giris_cikis_personel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel_giris_cikis
    ADD CONSTRAINT personel_giris_cikis_personel_id_fkey FOREIGN KEY (personel_id) REFERENCES public.personel(id) ON DELETE CASCADE;


--
-- Name: personel_vardiyalari personel_vardiyalari_personel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel_vardiyalari
    ADD CONSTRAINT personel_vardiyalari_personel_id_fkey FOREIGN KEY (personel_id) REFERENCES public.personel(id) ON DELETE CASCADE;


--
-- Name: personel_vardiyalari personel_vardiyalari_vardiya_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personel_vardiyalari
    ADD CONSTRAINT personel_vardiyalari_vardiya_id_fkey FOREIGN KEY (vardiya_id) REFERENCES public.vardiyalar(id);


--
-- Name: portal_kullanicilari portal_kullanicilari_musteri_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portal_kullanicilari
    ADD CONSTRAINT portal_kullanicilari_musteri_id_fkey FOREIGN KEY (musteri_id) REFERENCES public.musteriler(id) ON DELETE CASCADE;


--
-- Name: portal_kullanicilari portal_kullanicilari_tedarikci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portal_kullanicilari
    ADD CONSTRAINT portal_kullanicilari_tedarikci_id_fkey FOREIGN KEY (tedarikci_id) REFERENCES public.tedarikciler(id) ON DELETE CASCADE;


--
-- Name: satin_alma_detaylari satin_alma_detaylari_hammadde_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_detaylari
    ADD CONSTRAINT satin_alma_detaylari_hammadde_id_fkey FOREIGN KEY (hammadde_id) REFERENCES public.hammaddeler(id);


--
-- Name: satin_alma_detaylari satin_alma_detaylari_siparis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_detaylari
    ADD CONSTRAINT satin_alma_detaylari_siparis_id_fkey FOREIGN KEY (siparis_id) REFERENCES public.satin_alma_siparisleri(id);


--
-- Name: satin_alma_siparisleri satin_alma_siparisleri_tedarikci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_siparisleri
    ADD CONSTRAINT satin_alma_siparisleri_tedarikci_id_fkey FOREIGN KEY (tedarikci_id) REFERENCES public.tedarikciler(id);


--
-- Name: satin_alma_talepleri satin_alma_talepleri_hammadde_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.satin_alma_talepleri
    ADD CONSTRAINT satin_alma_talepleri_hammadde_id_fkey FOREIGN KEY (hammadde_id) REFERENCES public.hammaddeler(id) ON DELETE SET NULL;


--
-- Name: scm_tedarikci_performans scm_tedarikci_performans_tedarikci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scm_tedarikci_performans
    ADD CONSTRAINT scm_tedarikci_performans_tedarikci_id_fkey FOREIGN KEY (tedarikci_id) REFERENCES public.tedarikciler(id);


--
-- Name: sevkiyatlar sevkiyatlar_satis_siparis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sevkiyatlar
    ADD CONSTRAINT sevkiyatlar_satis_siparis_id_fkey FOREIGN KEY (satis_siparis_id) REFERENCES public.satis_siparisleri(id) ON DELETE SET NULL;


--
-- Name: siparis_detaylari siparis_detaylari_urun_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.siparis_detaylari
    ADD CONSTRAINT siparis_detaylari_urun_id_fkey FOREIGN KEY (urun_id) REFERENCES public.urunler(id);


--
-- Name: siparis_kalemleri siparis_kalemleri_siparis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.siparis_kalemleri
    ADD CONSTRAINT siparis_kalemleri_siparis_id_fkey FOREIGN KEY (siparis_id) REFERENCES public.satis_siparisleri(id) ON DELETE CASCADE;


--
-- Name: siparis_kalemleri siparis_kalemleri_urun_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.siparis_kalemleri
    ADD CONSTRAINT siparis_kalemleri_urun_id_fkey FOREIGN KEY (urun_id) REFERENCES public.urunler(id) ON DELETE CASCADE;


--
-- Name: stok_hareketleri stok_hareketleri_hammadde_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stok_hareketleri
    ADD CONSTRAINT stok_hareketleri_hammadde_id_fkey FOREIGN KEY (hammadde_id) REFERENCES public.hammaddeler(id);


--
-- Name: teklif_kalemleri teklif_kalemleri_teklif_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teklif_kalemleri
    ADD CONSTRAINT teklif_kalemleri_teklif_id_fkey FOREIGN KEY (teklif_id) REFERENCES public.teklifler(id) ON DELETE CASCADE;


--
-- Name: teklif_kalemleri teklif_kalemleri_urun_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teklif_kalemleri
    ADD CONSTRAINT teklif_kalemleri_urun_id_fkey FOREIGN KEY (urun_id) REFERENCES public.urunler(id);


--
-- Name: teklifler teklifler_musteri_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teklifler
    ADD CONSTRAINT teklifler_musteri_id_fkey FOREIGN KEY (musteri_id) REFERENCES public.musteriler(id);


--
-- Name: uretim_emirleri uretim_emirleri_atanan_kalip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_emirleri
    ADD CONSTRAINT uretim_emirleri_atanan_kalip_id_fkey FOREIGN KEY (atanan_kalip_id) REFERENCES public.kaliplar(id);


--
-- Name: uretim_emirleri uretim_emirleri_atanan_makine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_emirleri
    ADD CONSTRAINT uretim_emirleri_atanan_makine_id_fkey FOREIGN KEY (atanan_makine_id) REFERENCES public.makineler(id);


--
-- Name: uretim_hammadde_kullanimi uretim_hammadde_kullanimi_hammadde_giris_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_hammadde_kullanimi
    ADD CONSTRAINT uretim_hammadde_kullanimi_hammadde_giris_id_fkey FOREIGN KEY (hammadde_giris_id) REFERENCES public.hammadde_girisleri(id);


--
-- Name: uretim_hammadde_kullanimi uretim_hammadde_kullanimi_uretim_emri_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_hammadde_kullanimi
    ADD CONSTRAINT uretim_hammadde_kullanimi_uretim_emri_id_fkey FOREIGN KEY (uretim_emri_id) REFERENCES public.uretim_emirleri(id);


--
-- Name: uretim_lot_kullanimi uretim_lot_kullanimi_hammadde_giris_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_lot_kullanimi
    ADD CONSTRAINT uretim_lot_kullanimi_hammadde_giris_id_fkey FOREIGN KEY (hammadde_giris_id) REFERENCES public.hammadde_girisleri(id);


--
-- Name: uretim_lot_kullanimi uretim_lot_kullanimi_uretim_emri_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_lot_kullanimi
    ADD CONSTRAINT uretim_lot_kullanimi_uretim_emri_id_fkey FOREIGN KEY (uretim_emri_id) REFERENCES public.uretim_emirleri(id);


--
-- Name: uretim_planlari uretim_planlari_satis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.uretim_planlari
    ADD CONSTRAINT uretim_planlari_satis_id_fkey FOREIGN KEY (satis_id) REFERENCES public.satis_siparisleri(id);


--
-- Name: urun_receteleri urun_receteleri_hammadde_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.urun_receteleri
    ADD CONSTRAINT urun_receteleri_hammadde_id_fkey FOREIGN KEY (hammadde_id) REFERENCES public.hammaddeler(id);


--
-- PostgreSQL database dump complete
--

\unrestrict zqf8YLO1qBazbHIsPp9CKvzFSV7kjECd0PHG9LDYB0DIGfAk1uvBtoEt5aVFvet

