import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from groq import Groq

# Groq AI Client
@st.cache_resource
def init_groq_client():
    try:
        api_key = st.secrets.get("GROQ_API_KEY", "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")
        return Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Groq client başlatılamadı: {str(e)}")
        return None

client = init_groq_client()

# Konu verileri
KONU_VERILERI = {
    "Türkçe": {
        "Paragraf": {"zorluk": "Zor", "ortalama_soru": 23, "kategori": "Dil"},
        "Cümlede Anlam": {"zorluk": "Orta", "ortalama_soru": 3, "kategori": "Dil"},
        "Sözcükte Anlam": {"zorluk": "Kolay", "ortalama_soru": 2, "kategori": "Dil"},
        "Anlatım Bozukluğu": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Dil"},
        "Yazım Kuralları": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Ezber"},
        "Noktalama İşaretleri": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Ezber"},
        "Dil Bilgisi": {"zorluk": "Orta", "ortalama_soru": 6, "kategori": "Ezber"},
        "Sözel Mantık": {"zorluk": "Zor", "ortalama_soru": 2, "kategori": "Zor"}
    },
    "Matematik": {
        "Temel Kavramlar": {"zorluk": "Kolay", "ortalama_soru": 2, "kategori": "Zor"},
        "Sayı Basamakları": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Zor"},
        "Bölme / Bölünebilme": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Zor"},
        "EBOB – EKOK": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Zor"},
        "Rasyonel / Kök / Üslü Sayılar": {"zorluk": "Orta", "ortalama_soru": 4, "kategori": "Zor"},
        "Denklem Çözme": {"zorluk": "Orta", "ortalama_soru": 3, "kategori": "Zor"},
        "Oran – Orantı": {"zorluk": "Kolay", "ortalama_soru": 2, "kategori": "Zor"},
        "Problemler": {"zorluk": "Zor", "ortalama_soru": 9, "kategori": "Zor"},
        "Kümeler, Mantık": {"zorluk": "Orta", "ortalama_soru": 3, "kategori": "Zor"},
        "Fonksiyon": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Zor"},
        "Permütasyon, Kombinasyon, Olasılık": {"zorluk": "Zor", "ortalama_soru": 3, "kategori": "Zor"},
        "Veri – Grafik": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Zor"}
    },
    "Geometri": {
        "Temel Kavramlar, Açılar": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Zor"},
        "Üçgenler": {"zorluk": "Orta", "ortalama_soru": 3, "kategori": "Zor"},
        "Çokgenler & Dörtgenler": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Zor"},
        "Çember & Daire": {"zorluk": "Zor", "ortalama_soru": 2, "kategori": "Zor"},
        "Analitik Geometri": {"zorluk": "Zor", "ortalama_soru": 1, "kategori": "Zor"},
        "Katı Cisimler": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Zor"}
    },
    "Fizik": {
        "Fizik Bilimine Giriş": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Zor"},
        "Kuvvet – Hareket": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Zor"},
        "Enerji – İş – Güç": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Zor"},
        "Basınç – Kaldırma": {"zorluk": "Zor", "ortalama_soru": 1, "kategori": "Zor"},
        "Elektrik – Manyetizma": {"zorluk": "Zor", "ortalama_soru": 1, "kategori": "Zor"},
        "Optik – Dalgalar": {"zorluk": "Zor", "ortalama_soru": 1, "kategori": "Zor"}
    },
    "Kimya": {
        "Kimya Bilimi, Atom": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Orta"},
        "Periyodik Sistem, Bileşikler": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Orta"},
        "Kimyasal Türler & Etkileşim": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Orta"},
        "Karışımlar, Asit – Baz – Tuz": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Orta"},
        "Kimyasal Hesaplamalar": {"zorluk": "Zor", "ortalama_soru": 2, "kategori": "Orta"}
    },
    "Biyoloji": {
        "Canlıların Temel Bileşenleri": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Orta"},
        "Hücre – Organeller": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Orta"},
        "Hücre Zarından Madde Geçişi": {"zorluk": "Zor", "ortalama_soru": 1, "kategori": "Orta"},
        "Canlı Sınıflandırma – Sistemler": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Orta"},
        "Ekosistem, Madde Döngüleri": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Orta"}
    },
    "Tarih": {
        "İlk ve Orta Çağ Uygarlıkları": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Kolay"},
        "Osmanlı Tarihi": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Kolay"},
        "Kurtuluş Savaşı – Atatürk İlkeleri": {"zorluk": "Zor", "ortalama_soru": 2, "kategori": "Kolay"},
        "Çağdaş Türkiye, İnkılaplar": {"zorluk": "Orta", "ortalama_soru": 1, "kategori": "Kolay"}
    },
    "Coğrafya": {
        "Harita Bilgisi": {"zorluk": "Kolay", "ortalama_soru": 1, "kategori": "Kolay"},
        "İklim – Yer Şekilleri": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Kolay"},
        "Beşeri ve Ekonomik Coğrafya": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Kolay"}
    },
    "Felsefe": {
        "Bilgi – Varlık – Ahlak": {"zorluk": "Zor", "ortalama_soru": 3, "kategori": "Kolay"},
        "Siyaset – Din – Sanat": {"zorluk": "Zor", "ortalama_soru": 2, "kategori": "Kolay"}
    },
    "Din Kültürü": {
        "İnanç, İbadet, Ahlak": {"zorluk": "Kolay", "ortalama_soru": 3, "kategori": "Kolay"},
        "Hz. Muhammed & İslam Düşüncesi": {"zorluk": "Orta", "ortalama_soru": 2, "kategori": "Kolay"}
    }
}

# Zaman dilimleri
ZAMAN_DILIMLERI = {
    "Zor": ["08:00-10:30", "16:00-18:00"],
    "Orta": ["10:30-12:30", "19:00-21:00"],
    "Kolay": ["13:30-15:30", "21:00-22:30"],
    "Dil": ["06:30-08:00", "22:30-23:30"],
    "Ezber": ["07:00-08:30", "22:00-23:00"]
}

# Zorluk katsayıları
ZORLUK_KATSAYILARI = {
    "Kolay": 0.5,
    "Orta": 1,
    "Zor": 2
}

# Geliştirilmiş AI Öneri Sistemi
def get_ai_suggestion(konu_analizi, gunluk_saat, gun_sayisi):
    """Geliştirilmiş ve daha detaylı AI önerisi"""
    if not client:
        return "AI hizmeti şu anda kullanılamıyor. Lütfen manuel olarak öncelikli konulara odaklanın."
    
    try:
        sorted_topics = sorted(konu_analizi.items(), key=lambda x: x[1]['oncelik_puani'], reverse=True)
        kotu_konular = sorted_topics[:8]
        orta_konular = sorted_topics[8:16] if len(sorted_topics) > 8 else []
        iyi_konular = sorted_topics[-5:]
        
        # Ders bazında analiz
        ders_analizi = {}
        for konu, info in konu_analizi.items():
            ders = info['ders']
            if ders not in ders_analizi:
                ders_analizi[ders] = {'toplam_puan': 0, 'konu_sayisi': 0, 'zayif_konular': 0}
            ders_analizi[ders]['toplam_puan'] += info['oncelik_puani']
            ders_analizi[ders]['konu_sayisi'] += 1
            if info['oncelik_puani'] > 5:
                ders_analizi[ders]['zayif_konular'] += 1
        
        for ders in ders_analizi:
            ders_analizi[ders]['ortalama'] = ders_analizi[ders]['toplam_puan'] / ders_analizi[ders]['konu_sayisi']
            ders_analizi[ders]['zayiflik_orani'] = ders_analizi[ders]['zayif_konular'] / ders_analizi[ders]['konu_sayisi']
        
        en_zayif_ders = max(ders_analizi.items(), key=lambda x: x[1]['ortalama'])
        
        # Hedef belirleme
        toplam_saat = gunluk_saat * gun_sayisi
        kritik_konu_sayisi = len([k for k, v in konu_analizi.items() if v['oncelik_puani'] > 5])
        
        prompt = f"""
        Sen TYT'de uzman bir eğitim koçusun. Öğrencinin detaylı performans analizini yapıp, kişiselleştirilmiş {gun_sayisi} günlük strateji hazırlayacaksın.

        📊 ÖĞRENCİ PROFİLİ:
        • Toplam çalışma süresi: {toplam_saat} saat ({gun_sayisi} gün x {gunluk_saat} saat)
        • Kritik durumdaki konu sayısı: {kritik_konu_sayisi}
        • En zayıf alan: {en_zayif_ders[0]} (Risk skoru: {en_zayif_ders[1]['ortalama']:.1f})
        
        🔴 ACİL MÜDAHALE GEREKTİREN KONULAR:
        {chr(10).join([f"• {konu.split(' - ')[1]} ({konu.split(' - ')[0]}) - Risk: {info['oncelik_puani']:.1f}/10" for konu, info in kotu_konular])}
        
        🟡 GELİŞTİRİLMESİ GEREKEN KONULAR:
        {chr(10).join([f"• {konu.split(' - ')[1]} ({konu.split(' - ')[0]}) - Risk: {info['oncelik_puani']:.1f}/10" for konu, info in orta_konular])}
        
        🟢 GÜÇLÜ ALANLAR (Koruma altında):
        {chr(10).join([f"• {konu.split(' - ')[1]} ({konu.split(' - ')[0]}) - Risk: {info['oncelik_puani']:.1f}/10" for konu, info in iyi_konular])}
        
        📈 DERS BAZLI ZAYIFLIK ANALİZİ:
        {chr(10).join([f"• {ders}: %{data['zayiflik_orani']*100:.0f} zayıf konu oranı" for ders, data in ders_analizi.items()])}
        
        GÖREV: Aşağıdaki kriterlere göre {gun_sayisi} günlük DETAYLI strateji hazırla (en az 800 kelime):
        1. Kritik konular için haftalık çalışma planı (konu bazlı)
        2. Her kritik konu için özel çalışma teknikleri
        3. Zaman yönetimi stratejileri
        4. Kaynak önerileri (kitap, video, uygulama)
        5. Motivasyon teknikleri ve başarı hikayeleri
        6. Deneme sınavı takvimi
        7. Ölçme-değerlendirme yöntemleri
        8. Uyku ve beslenme düzeni önerileri
        9. Stres yönetimi teknikleri
        10. Son hafta için özel taktikler
        
        Çıktıyı başlıklar halinde düzenle ve her bölüm için en az 3-5 madde içeren detaylı açıklamalar yap.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "Sen TYT'de uzman, analitik düşünen ve öğrenci psikolojisini iyi bilen bir eğitim koçusun. Veriye dayalı, kişiselleştirilmiş ve motive edici stratejiler sunuyorsun. Önerilerin en az 800 kelime olmalı ve tüm detayları kapsamalı."
                },
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            max_tokens=4000,
            temperature=0.7
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI önerisi alınırken hata oluştu: {str(e)}"

# PDF Karneden Veri Çıkarma Fonksiyonu
def extract_data_from_pdf(pdf_file):
    """PDF karnesinden veri çıkar"""
    try:
        # PDF'den metin çıkar
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # AI ile metni analiz et ve verileri çıkar
        prompt = f"""
        Aşağıda bir TYT deneme sınavı karnesinden çıkarılmış metin bulunmaktadır. 
        Bu metinden dersler ve konular bazında doğru, yanlış ve boş sayılarını çıkar.
        
        Çıktı formatı JSON olmalı ve aşağıdaki yapıda olmalı:
        {{
          "Türkçe": {{
            "Paragraf": {{"dogru": sayı, "yanlis": sayı, "bos": sayı, "gercek_soru": sayı}},
            "Cümlede Anlam": {{...}},
            ...
          }},
          "Matematik": {{...}},
          ...
        }}
        
        Dersler: Türkçe, Matematik, Geometri, Fizik, Kimya, Biyoloji, Tarih, Coğrafya, Felsefe, Din Kültürü
        Konular: Sistemde tanımlı olan konu isimlerini kullan
        
        METİN:
        {text[:10000]}  # İlk 10,000 karakteri al
        
        Sadece JSON formatında cevap ver, başka hiçbir şey yazma.
        """
        
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "Sadece istenen JSON formatında çıktı ver."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        json_str = response.choices[0].message.content
        
        # JSON'u temizle
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_str)
        
        return data
    except Exception as e:
        st.error(f"PDF analiz hatası: {str(e)}")
        return None

def hesapla_oncelik_puani(dogru, yanlis, bos, zorluk, ortalama_soru):
    """Geliştirilmiş öncelik puanı hesapla"""
    zorluk_katsayisi = ZORLUK_KATSAYILARI[zorluk]
    
    # Temel puan
    puan = (yanlis * 2) + (bos * 1.5) + (zorluk_katsayisi * 3)
    
    # Konu önem ağırlığı
    toplam_ortalama_soru = sum(sum(konu['ortalama_soru'] for konu in ders.values()) for ders in KONU_VERILERI.values())
    onem_agirligi = (ortalama_soru / toplam_ortalama_soru) * 10
    
    # Final puan
    oncelik_puani = puan * onem_agirligi
    
    return oncelik_puani

def analiz_et(veriler):
    """Tüm verileri analiz et"""
    analiz = {}
    for ders, konular in veriler.items():
        for konu, sonuclar in konular.items():
            if sonuclar['dogru'] + sonuclar['yanlis'] + sonuclar['bos'] > 0:
                konu_bilgi = KONU_VERILERI[ders][konu]
                
                oncelik_puani = hesapla_oncelik_puani(
                    sonuclar['dogru'], 
                    sonuclar['yanlis'], 
                    sonuclar['bos'],
                    konu_bilgi['zorluk'],
                    konu_bilgi['ortalama_soru']
                )
                
                analiz[f"{ders} - {konu}"] = {
                    'ders': ders,
                    'konu': konu,
                    'oncelik_puani': oncelik_puani,
                    'dogru': sonuclar['dogru'],
                    'yanlis': sonuclar['yanlis'],
                    'bos': sonuclar['bos'],
                    'zorluk': konu_bilgi['zorluk'],
                    'kategori': konu_bilgi['kategori'],
                    'gercek_soru': sonuclar['gercek_soru']
                }
    return analiz

def program_olustur_zaman_dilimli(analiz, baslangic_tarihi, gun_sayisi, gunluk_saat):
    """Zaman dilimli çalışma programı oluştur"""
    sorted_konular = sorted(analiz.items(), key=lambda x: x[1]['oncelik_puani'], reverse=True)
    
    program = []
    current_date = baslangic_tarihi
    
    # Kategorilere göre konuları ayır
    kategoriler = {
        "Zor": [],
        "Orta": [],
        "Kolay": [],
        "Dil": [],
        "Ezber": []
    }
    
    for konu_adi, bilgi in sorted_konular:
        kategori = bilgi['kategori']
        kategoriler[kategori].append((konu_adi, bilgi))
    
    # Her gün için program oluştur
    for gun in range(gun_sayisi):
        tarih = current_date + timedelta(days=gun)
        
        # Günlük saate göre zaman dilimlerini belirle
        if gunluk_saat <= 2:
            secilen_dilimler = ["08:00-10:30"]
        elif gunluk_saat <= 4:
            secilen_dilimler = ["08:00-10:30", "16:00-18:00"]
        elif gunluk_saat <= 6:
            secilen_dilimler = ["08:00-10:30", "10:30-12:30", "19:00-21:00"]
        else:
            secilen_dilimler = ["08:00-10:30", "10:30-12:30", "16:00-18:00", "19:00-21:00"]
        
        # Her zaman dilimine konu ata
        for zaman_dilimi in secilen_dilimler:
            # Öncelikli konu bul
            secilen_konu = None
            for kategori, konular in kategoriler.items():
                if konular:
                    secilen_konu = konular.pop(0)
                    break
            
            if secilen_konu:
                konu_adi, bilgi = secilen_konu
                
                program.append({
                    'Gün': gun + 1,
                    'Tarih': tarih.strftime('%d.%m.%Y'),
                    'Zaman': zaman_dilimi,
                    'Ders': bilgi['ders'],
                    'Konu': bilgi['konu'],
                    'Öncelik Puanı': bilgi['oncelik_puani'],
                    'Zorluk': bilgi['zorluk'],
                    'Kategori': bilgi['kategori'],
                    'Doğru': bilgi['dogru'],
                    'Yanlış': bilgi['yanlis'],
                    'Boş': bilgi['bos']
                })
    
    return program

def excel_export_professional(program_df):
    """Profesyonel Excel çıktısı"""
    output = io.BytesIO()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "TYT Çalışma Programı"
    
    # Başlık stilleri
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="2F4F4F", end_color="2F4F4F", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Kenarlık
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Koşullu biçimlendirme renkleri
    high_priority_fill = PatternFill(start_color="FFE4E1", end_color="FFE4E1", fill_type="solid")
    hard_topic_fill = PatternFill(start_color="FFF8DC", end_color="FFF8DC", fill_type="solid")
    
    # Başlıkları ekle
    for col, header in enumerate(program_df.columns, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Verileri ekle
    for row_idx, row in enumerate(dataframe_to_rows(program_df, index=False, header=False), 2):
        for col_idx, value in enumerate(row, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Koşullu biçimlendirme
            if col_idx == 6:  # Öncelik Puanı sütunu
                if isinstance(value, (int, float)) and value > 5:
                    cell.fill = high_priority_fill
                    cell.font = Font(bold=True, color="8B0000")
            
            if col_idx == 7:  # Zorluk sütunu
                if value == "Zor":
                    cell.fill = hard_topic_fill
                    cell.font = Font(bold=True, color="FF8C00")
    
    # Sütun genişliklerini ayarla
    column_widths = {
        'A': 8,   # Gün
        'B': 12,  # Tarih
        'C': 15,  # Zaman
        'D': 12,  # Ders
        'E': 35,  # Konu
        'F': 15,  # Öncelik Puanı
        'G': 12,  # Zorluk
        'H': 12,  # Kategori
        'I': 8,   # Doğru
        'J': 8,   # Yanlış
        'K': 8    # Boş
    }
    
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width
    
    # Dosyayı kaydet
    wb.save(output)
    output.seek(0)
    
    return output.getvalue()

# Streamlit arayüzü
def main():
    st.set_page_config(page_title="TYT Hazırlık Uygulaması", layout="wide")
    st.title("🎯 TYT Hazırlık Uygulaması")
    st.markdown("---")

# Sidebar - AI Koç
with st.sidebar:
    st.header("🤖 AI Koçun")
    
    # Çalışma parametreleri
    st.subheader("📚 Çalışma Ayarları")
    gunluk_saat = st.slider("Günlük Çalışma Saati", 1, 12, 4)
    gun_sayisi = st.number_input("Kaç Gün Çalışacaksınız?", min_value=1, max_value=365, value=30)
    
    if client:
        if st.button("🔥 Kişisel Strateji Al"):
            if 'analiz_sonucu' in st.session_state:
                with st.spinner("AI senin için özel strateji hazırlıyor..."):
                    suggestion = get_ai_suggestion(st.session_state['analiz_sonucu'], gunluk_saat, gun_sayisi)
                    st.success("🎯 **Senin İçin Özel Strateji:**")
                    st.info(suggestion)
            else:
                st.warning("⚠️ Önce veri giriş yapın!")
    else:
        st.warning("AI hizmeti şu anda kullanılamıyor.")

# Define ders_gruplari before using it
ders_gruplari = {
    "Temel Matematik": ["Matematik"],
    "Fen Bilimleri": ["Fizik", "Kimya", "Biyoloji"],
    "Sosyal Bilimler": ["Tarih", "Coğrafya", "Felsefe"],
    "Dil ve Edebiyat": ["Türkçe", "Türk Dili ve Edebiyatı"]
}

# Ana içerik
tab1, tab2, tab3, tab4 = st.tabs(["📊 Veri Giriş", "📈 Analiz", "📅 Program", "📚 Kaynaklar"])

# Define ders_gruplari before using it
ders_gruplari = {
    "Temel Matematik": ["Matematik"],
    "Fen Bilimleri": ["Fizik", "Kimya", "Biyoloji"],
    "Sosyal Bilimler": ["Tarih", "Coğrafya", "Felsefe"],
    "Dil ve Edebiyat": ["Türkçe", "Türk Dili ve Edebiyatı"]
}

# Ana içerik
tab1, tab2, tab3, tab4 = st.tabs(["📊 Veri Giriş", "📈 Analiz", "📅 Program", "📚 Kaynaklar"])

with tab1:
    st.header("Deneme Sonuçlarını Girin")
    
    # PDF'den Veri Çekme Bölümü
    with st.expander("📄 PDF Karneden Otomatik Veri Çek", expanded=False):
        uploaded_file = st.file_uploader("Deneme Sonuç Karnesi (PDF) Yükle", type="pdf")
        
        if uploaded_file is not None:
            if st.button("PDF'den Verileri Çek ve Uygula"):
                with st.spinner("PDF analiz ediliyor..."):
                    pdf_data = extract_data_from_pdf(uploaded_file)
                    
                    if pdf_data:
                        # Mevcut verilerle birleştir
                        if 'veriler' not in st.session_state:
                            st.session_state.veriler = {}
                        
                        for ders, konular in pdf_data.items():
                            if ders not in st.session_state.veriler:
                                st.session_state.veriler[ders] = {}
                            
                            for konu, sonuclar in konular.items():
                                # Sadece geçerli konuları işle
                                if konu in KONU_VERILERI.get(ders, {}):
                                    st.session_state.veriler[ders][konu] = {
                                        'dogru': sonuclar.get('dogru', 0),
                                        'yanlis': sonuclar.get('yanlis', 0),
                                        'bos': sonuclar.get('bos', 0),
                                        'gercek_soru': sonuclar.get('gercek_soru', KONU_VERILERI[ders][konu]['ortalama_soru'])
                                    }
                        
                        st.success("PDF'den veriler başarıyla çekildi ve uygulandı!")
                        st.json(pdf_data)
                    else:
                        st.error("PDF analiz edilemedi. Lütfen manuel giriş yapın.")

    # Session state'i başlat
    if 'veriler' not in st.session_state:
        st.session_state.veriler = {}
    
    for grup_adi, dersler in ders_gruplari.items():
        with st.expander(f"📚 {grup_adi}", expanded=False):
            for ders in dersler:
                # Dersin KONU_VERILERI'nde olup olmadığını kontrol et
                if ders not in KONU_VERILERI:
                    st.warning(f"⚠️ {ders} dersi için konu verileri tanımlanmamış!")
                    continue
                    
                st.subheader(f"{ders}")
                
                if ders not in st.session_state.veriler:
                    st.session_state.veriler[ders] = {}
                
                cols = st.columns(3)
                for i, (konu, bilgi) in enumerate(KONU_VERILERI[ders].items()):
                    col_idx = i % 3
                    
                    with cols[col_idx]:
                        st.markdown(f"**{konu}**")
                        st.caption(f"Zorluk: {bilgi['zorluk']} | Ortalama: {bilgi['ortalama_soru']} soru")
                        
                        if konu not in st.session_state.veriler[ders]:
                            st.session_state.veriler[ders][konu] = {
                                'dogru': 0, 'yanlis': 0, 'bos': 0, 'gercek_soru': bilgi['ortalama_soru']
                            }
                        
                        # Gerçek soru sayısı
                        gercek_soru = st.number_input(
                            f"Denemede Bu Konudan Kaç Soru Vardı?",
                            min_value=0,
                            max_value=50,
                            key=f"{ders}_{konu}_gercek",
                            value=st.session_state.veriler[ders][konu]['gercek_soru']
                        )
                        
                        # Doğru
                        dogru = st.number_input(
                            f"Doğru", 
                            min_value=0, 
                            max_value=gercek_soru,
                            key=f"{ders}_{konu}_dogru", 
                            value=st.session_state.veriler[ders][konu]['dogru']
                        )
                        
                        # Yanlış
                        yanlis = st.number_input(
                            f"Yanlış", 
                            min_value=0, 
                            max_value=max(0, gercek_soru - dogru),
                            key=f"{ders}_{konu}_yanlis",
                            value=st.session_state.veriler[ders][konu]['yanlis']
                        )
                        
                        # Boş otomatik hesapla
                        bos = max(0, gercek_soru - dogru - yanlis)
                        
                        st.text_input(
                            f"Boş (Otomatik)", 
                            value=str(bos),
                            key=f"{ders}_{konu}_bos_display",
                            disabled=True
                        )
                        
                        st.session_state.veriler[ders][konu] = {
                            'dogru': dogru,
                            'yanlis': yanlis,
                            'bos': bos,
                            'gercek_soru': gercek_soru
                        }
                        
                        # Kontrol
                        toplam = dogru + yanlis + bos
                        if toplam == gercek_soru:
                            st.success(f"✅ Toplam: {toplam}")
                        else:
                            st.error(f"❌ Toplam: {toplam}/{gercek_soru}")
with tab2:
    st.header("📊 Analiz Sonuçları")
    
    if st.button("🔍 Analiz Et"):
        analiz_sonucu = analiz_et(st.session_state.veriler)
        st.session_state.analiz_sonucu = analiz_sonucu
        
        if analiz_sonucu:
            sorted_analiz = sorted(analiz_sonucu.items(), key=lambda x: x[1]['oncelik_puani'], reverse=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔴 Öncelikli Konular")
                for i, (konu, bilgi) in enumerate(sorted_analiz[:10]):
                    st.error(f"{i+1}. {konu} (Puan: {bilgi['oncelik_puani']:.1f})")
            
            with col2:
                st.subheader("🟢 İyi Durumda Olan Konular")
                for i, (konu, bilgi) in enumerate(sorted_analiz[-10:]):
                    st.success(f"{i+1}. {konu} (Puan: {bilgi['oncelik_puani']:.1f})")
            
            df_analiz = pd.DataFrame([
                {
                    'Konu': konu,
                    'Öncelik Puanı': bilgi['oncelik_puani'],
                    'Ders': bilgi['ders'],
                    'Zorluk': bilgi['zorluk']
                }
                for konu, bilgi in analiz_sonucu.items()
            ])
            
            fig = px.bar(df_analiz.head(20), 
                        x='Öncelik Puanı', 
                        y='Konu',
                        color='Ders',
                        title='En Öncelikli 20 Konu')
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Analiz için veri bulunamadı!")

with tab3:
    st.header("📅 Çalışma Programı")
    
    if 'analiz_sonucu' in st.session_state:
        col1, col2 = st.columns(2)
        
        with col1:
            baslangic_tarihi = st.date_input("Başlangıç Tarihi", datetime.now())
        
        if st.button("📋 Zaman Dilimli Program Oluştur"):
            with st.spinner("Biyolojik saatinize uygun program hazırlanıyor..."):
                program = program_olustur_zaman_dilimli(
                    st.session_state.analiz_sonucu, 
                    baslangic_tarihi, 
                    gun_sayisi, 
                    gunluk_saat
                )
                program_df = pd.DataFrame(program)
                st.session_state.program_df = program_df
                
                st.dataframe(program_df, use_container_width=True)
                
                # İlerleme takibi
                st.subheader("📊 İlerleme Takibi")
                ders_ilerleme = program_df.groupby('Ders').size().reset_index(name='Konu Sayısı')
                ders_ilerleme['Tamamlanma Oranı'] = ders_ilerleme['Konu Sayısı'] / len(program_df) * 100
                
                fig = px.pie(ders_ilerleme, 
                            names='Ders', 
                            values='Konu Sayısı',
                            title='Derslere Göre Konu Dağılımı',
                            hole=0.3)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Önce analiz yapın!")
        # Kaynak önerme modülü - tab4 olarak eklenecek

# KITAP VERİLERİ
KITAP_ONERILERI = {
    "Türkçe": {
        "Kolay": [
            "3D Türkçe Soru Bankası (Başlangıç)",
            "Tonguç Paragrafik",
            "Palme Türkçe Konu Anlatımlı",
            "Karekök 0 Türkçe",
            "Bilgiseli Türkçe"
        ],
        "Orta": [
            "Limit Yayınları TYT Türkçe",
            "ÜçDörtBeş TYT Paragraf Soru Bankası",
            "Hız ve Renk Türkçe",
            "Apotemi Türkçe Soru Bankası (TYT için uyarlanmış hali)",
            "Benim Hocam TYT Türkçe Video Ders Defteri"
        ]
    },
    "Matematik": {
        "Kolay": [
            "Karekök 0 Matematik",
            "Tonguç Kampüs TYT Matematik (ilk seviye)",
            "3D Matematik Konu Anlatımı",
            "Kolay Matematik Serisi (Birey A)",
            "Palme TYT Temel Matematik"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Matematik Soru Bankası",
            "Limit Matematik (Kırmızı Seri)",
            "Bilgiseli TYT Matematik",
            "Apotemi TYT Matematik Başlangıç Serisi",
            "Endemik TYT Matematik"
        ]
    },
    "Geometri": {
        "Kolay": [
            "Karekök 0 Matematik",
            "Tonguç Kampüs TYT Matematik (ilk seviye)",
            "3D Matematik Konu Anlatımı",
            "Kolay Matematik Serisi (Birey A)",
            "Palme TYT Temel Matematik"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Matematik Soru Bankası",
            "Limit Matematik (Kırmızı Seri)",
            "Bilgiseli TYT Matematik",
            "Apotemi TYT Matematik Başlangıç Serisi",
            "Endemik TYT Matematik"
        ]
    },
    "Fizik": {
        "Kolay": [
            "3D TYT Fizik",
            "Palme Fen Bilimleri Konu Anlatımlı Set",
            "Karekök 0 Fen Serisi",
            "Birey A Fen Bilimleri",
            "Kolay Fen Bilimleri – Kampüs Yayınları"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Fen Bilimleri Soru Bankası",
            "Apotemi TYT Fen Bilimleri Modüler Set",
            "Hız ve Renk TYT Fen Bilimleri",
            "Aydın TYT Fen Bilimleri Soru Bankası",
            "Benim Hocam Video Ders Defteri (Fen Seti)"
        ]
    },
    "Kimya": {
        "Kolay": [
            "3D TYT Kimya",
            "Palme Fen Bilimleri Konu Anlatımlı Set",
            "Karekök 0 Fen Serisi",
            "Birey A Fen Bilimleri",
            "Kolay Fen Bilimleri – Kampüs Yayınları"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Fen Bilimleri Soru Bankası",
            "Apotemi TYT Fen Bilimleri Modüler Set",
            "Hız ve Renk TYT Fen Bilimleri",
            "Aydın TYT Fen Bilimleri Soru Bankası",
            "Benim Hocam Video Ders Defteri (Fen Seti)"
        ]
    },
    "Biyoloji": {
        "Kolay": [
            "3D TYT Biyoloji",
            "Palme Fen Bilimleri Konu Anlatımlı Set",
            "Karekök 0 Fen Serisi",
            "Birey A Fen Bilimleri",
            "Kolay Fen Bilimleri – Kampüs Yayınları"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Fen Bilimleri Soru Bankası",
            "Apotemi TYT Fen Bilimleri Modüler Set",
            "Hız ve Renk TYT Fen Bilimleri",
            "Aydın TYT Fen Bilimleri Soru Bankası",
            "Benim Hocam Video Ders Defteri (Fen Seti)"
        ]
    },
    "Tarih": {
        "Kolay": [
            "Karekök 0 Sosyal Bilimler",
            "3D TYT Sosyal Bilimler Soru Bankası",
            "Tonguç TYT Sosyal Konu Anlatımlı",
            "Palme Sosyal Bilimler",
            "Hız ve Renk TYT Sosyal Bilimler (Kolay Seviye)"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Sosyal Bilimler",
            "Limit Yayınları TYT Sosyal",
            "Bilgiseli Sosyal Bilimler Soru Bankası",
            "Endemik Sosyal Bilimler",
            "Karekök Sosyal Bilimler (standart seviye)"
        ]
    },
    "Coğrafya": {
        "Kolay": [
            "Karekök 0 Sosyal Bilimler",
            "3D TYT Sosyal Bilimler Soru Bankası",
            "Tonguç TYT Sosyal Konu Anlatımlı",
            "Palme Sosyal Bilimler",
            "Hız ve Renk TYT Sosyal Bilimler (Kolay Seviye)"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Sosyal Bilimler",
            "Limit Yayınları TYT Sosyal",
            "Bilgiseli Sosyal Bilimler Soru Bankası",
            "Endemik Sosyal Bilimler",
            "Karekök Sosyal Bilimler (standart seviye)"
        ]
    },
    "Felsefe": {
        "Kolay": [
            "Karekök 0 Sosyal Bilimler",
            "3D TYT Sosyal Bilimler Soru Bankası",
            "Tonguç TYT Sosyal Konu Anlatımlı",
            "Palme Sosyal Bilimler",
            "Hız ve Renk TYT Sosyal Bilimler (Kolay Seviye)"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Sosyal Bilimler",
            "Limit Yayınları TYT Sosyal",
            "Bilgiseli Sosyal Bilimler Soru Bankası",
            "Endemik Sosyal Bilimler",
            "Karekök Sosyal Bilimler (standart seviye)"
        ]
    },
    "Din Kültürü": {
        "Kolay": [
            "Karekök 0 Sosyal Bilimler",
            "3D TYT Sosyal Bilimler Soru Bankası",
            "Tonguç TYT Sosyal Konu Anlatımlı",
            "Palme Sosyal Bilimler",
            "Hız ve Renk TYT Sosyal Bilimler (Kolay Seviye)"
        ],
        "Orta": [
            "ÜçDörtBeş TYT Sosyal Bilimler",
            "Limit Yayınları TYT Sosyal",
            "Bilgiseli Sosyal Bilimler Soru Bankası",
            "Endemik Sosyal Bilimler",
            "Karekök Sosyal Bilimler (standart seviye)"
        ]
    }
}

# YouTube kanalları ve genel öneriler
YOUTUBE_KANALLARI = {
    "Türkçe": [
        "Benim Hocam",
        "Tonguç Akademi",
        "Ders Vakti",
        "Matematik Sevdası",
        "Öğretmen Akademisi"
    ],
    "Matematik": [
        "Tonguç Akademi",
        "Matematik Sevdası",
        "Benim Hocam",
        "Ders Vakti",
        "Matematik Dünyası"
    ],
    "Geometri": [
        "Tonguç Akademi",
        "Matematik Sevdası",
        "Benim Hocam",
        "Ders Vakti",
        "Geometri Dünyası"
    ],
    "Fizik": [
        "Benim Hocam",
        "Tonguç Akademi",
        "Ders Vakti",
        "Fizik Dünyası",
        "Fen Bilimleri Akademisi"
    ],
    "Kimya": [
        "Benim Hocam",
        "Tonguç Akademi",
        "Ders Vakti",
        "Kimya Dünyası",
        "Fen Bilimleri Akademisi"
    ],
    "Biyoloji": [
        "Benim Hocam",
        "Tonguç Akademi",
        "Ders Vakti",
        "Biyoloji Dünyası",
        "Fen Bilimleri Akademisi"
    ],
    "Tarih": [
        "Benim Hocam",
        "Tonguç Akademi",
        "Ders Vakti",
        "Tarih Dünyası",
        "Sosyal Bilimler Akademisi"
    ],
    "Coğrafya": [
        "Benim Hocam",
        "Tonguç Akademi",
        "Ders Vakti",
        "Coğrafya Dünyası",
        "Sosyal Bilimler Akademisi"
    ],
    "Felsefe": [
        "Benim Hocam",
        "Tonguç Akademi",
        "Ders Vakti",
        "Felsefe Dünyası",
        "Sosyal Bilimler Akademisi"
    ],
    "Din Kültürü": [
        "Benim Hocam",
        "Tonguç Akademi",
        "Ders Vakti",
        "Din Kültürü Akademisi",
        "Sosyal Bilimler Akademisi"
    ]
}

def hesapla_ders_basari_orani(analiz_sonucu):
    """Her ders için başarı oranını hesapla"""
    ders_analizi = {}
    
    for konu_adi, bilgi in analiz_sonucu.items():
        ders = bilgi['ders']
        if ders not in ders_analizi:
            ders_analizi[ders] = {
                'toplam_puan': 0,
                'konu_sayisi': 0,
                'ortalama_puan': 0
            }
        
        ders_analizi[ders]['toplam_puan'] += bilgi['oncelik_puani']
        ders_analizi[ders]['konu_sayisi'] += 1
    
    # Ortalama hesapla ve seviye belirle
    for ders in ders_analizi:
        ortalama = ders_analizi[ders]['toplam_puan'] / ders_analizi[ders]['konu_sayisi']
        ders_analizi[ders]['ortalama_puan'] = ortalama
        
        # Seviye belirleme
        if ortalama >= 5:
            ders_analizi[ders]['seviye'] = 'Orta'
        else:
            ders_analizi[ders]['seviye'] = 'Kolay'
    
    return ders_analizi

def youtube_video_ara(ders_adi, konu_adi):
    """YouTube'dan video ara"""
    try:
        # YouTube API yerine genel öneriler
        return [
            f"TYT {ders_adi} {konu_adi} Konu Anlatımı",
            f"TYT {ders_adi} {konu_adi} Soru Çözümü",
            f"TYT {ders_adi} {konu_adi} Test Çözümü",
            f"{ders_adi} {konu_adi} Örnekler",
            f"{ders_adi} {konu_adi} Pratik Yöntemler"
        ]
    except Exception:
        return [f"TYT {ders_adi} {konu_adi} videolarını YouTube'da arayın"]

# TAB4 İÇERİĞİ
with tab4:
    st.header("📚 Akıllı Kaynak Önerileri")
    
    if 'analiz_sonucu' in st.session_state:
        ders_basari = hesapla_ders_basari_orani(st.session_state.analiz_sonucu)
        
        # Genel durum
        st.subheader("🎯 Genel Durum Analizi")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            zayif_dersler = [ders for ders, bilgi in ders_basari.items() if bilgi['ortalama_puan'] >= 5]
            st.metric("Zayıf Dersler", len(zayif_dersler))
        
        with col2:
            iyi_dersler = [ders for ders, bilgi in ders_basari.items() if bilgi['ortalama_puan'] < 5]
            st.metric("İyi Dersler", len(iyi_dersler))
        
        with col3:
            ortalama_risk = sum(bilgi['ortalama_puan'] for bilgi in ders_basari.values()) / len(ders_basari)
            st.metric("Genel Risk Skoru", f"{ortalama_risk:.1f}")
        
        st.markdown("---")
        
        # Ders bazlı öneriler
        for ders, bilgi in sorted(ders_basari.items(), key=lambda x: x[1]['ortalama_puan'], reverse=True):
            with st.expander(f"📖 {ders} - Risk Skoru: {bilgi['ortalama_puan']:.1f} ({'🔴 Acil' if bilgi['ortalama_puan'] >= 5 else '🟡 Orta' if bilgi['ortalama_puan'] >= 3 else '🟢 İyi'})", expanded=bilgi['ortalama_puan'] >= 5):
                
                # Kitap önerileri
                st.subheader(f"📚 {ders} için Kitap Önerileri")
                
                seviye = bilgi['seviye']
                if ders in KITAP_ONERILERI:
                    kitaplar = KITAP_ONERILERI[ders][seviye]
                    
                    cols = st.columns(2)
                    for i, kitap in enumerate(kitaplar):
                        with cols[i % 2]:
                            st.info(f"📖 {kitap}")
                
                # YouTube kanalları
                st.subheader(f"🎥 {ders} için YouTube Kanalları")
                if ders in YOUTUBE_KANALLARI:
                    kanallar = YOUTUBE_KANALLARI[ders]
                    
                    cols = st.columns(3)
                    for i, kanal in enumerate(kanallar):
                        with cols[i % 3]:
                            st.success(f"📺 {kanal}")
                
                # Bu dersteki zayıf konular
                st.subheader(f"🔍 {ders} - Zayıf Konular")
                ders_zayif_konular = [
                    (konu_adi, konu_bilgi) for konu_adi, konu_bilgi in st.session_state.analiz_sonucu.items()
                    if konu_bilgi['ders'] == ders and konu_bilgi['oncelik_puani'] >= 3
                ]
                
                if ders_zayif_konular:
                    sorted_zayif = sorted(ders_zayif_konular, key=lambda x: x[1]['oncelik_puani'], reverse=True)
                    
                    for konu_adi, konu_bilgi in sorted_zayif[:5]:  # En zayıf 5 konu
                        konu_adi_clean = konu_adi.split(' - ')[1]
                        
                        with st.container():
                            st.write(f"**{konu_adi_clean}** (Risk: {konu_bilgi['oncelik_puani']:.1f})")
                            
                            # Video önerileri
                            video_onerileri = youtube_video_ara(ders, konu_adi_clean)
                            
                            cols = st.columns(2)
                            with cols[0]:
                                st.write("🎬 **Video Önerileri:**")
                                for video in video_onerileri[:3]:
                                    st.write(f"• {video}")
                            
                            with cols[1]:
                                st.write("📝 **Çalışma Önerileri:**")
                                if konu_bilgi['zorluk'] == 'Zor':
                                    st.write("• Temel kavramları tekrar edin")
                                    st.write("• Bol örnek çözün")
                                    st.write("• Günde 30 dk ayırın")
                                elif konu_bilgi['zorluk'] == 'Orta':
                                    st.write("• Soru bankası çözün")
                                    st.write("• Testler yapın")
                                    st.write("• Günde 20 dk ayırın")
                                else:
                                    st.write("• Kısa tekrarlar yapın")
                                    st.write("• Formülleri ezberleyin")
                                    st.write("• Günde 10 dk ayırın")
                            
                            st.markdown("---")
                else:
                    st.info(f"🎉 {ders} dersinde kritik zayıflık yok!")
        
        # Genel öneriler
        st.markdown("---")
        st.subheader("💡 Genel Strateji Önerileri")
        
        risk_skoru = ortalama_risk
        
        if risk_skoru >= 5:
            st.error("🚨 **Acil Durum Stratejisi:**")
            st.write("• Temel konulara odaklanın")
            st.write("• Günde en az 6 saat çalışın")
            st.write("• Kolay kitaplardan başlayın")
            st.write("• YouTube'dan konu anlatımları izleyin")
        elif risk_skoru >= 3:
            st.warning("⚠️ **Orta Seviye Strateji:**")
            st.write("• Zayıf konulara ağırlık verin")
            st.write("• Günde 4-5 saat çalışın")
            st.write("• Soru bankası çözmeye odaklanın")
            st.write("• Düzenli testler yapın")
        else:
            st.success("✅ **Pekiştirme Stratejisi:**")
            st.write("• Tüm konuları dengeli çalışın")
            st.write("• Günde 3-4 saat çalışın")
            st.write("• Deneme sınavlarına odaklanın")
            st.write("• Hızınızı artırmaya çalışın")
    
    else:
        st.warning("⚠️ Kaynak önerileri için önce analiz yapın!")

# Export butonu
if 'program_df' in st.session_state:
    st.markdown("---")
    st.subheader("📁 Dışa Aktarma")
    
    if st.button("💾 Profesyonel Excel Oluştur"):
        try:
            excel_data = excel_export_professional(st.session_state.program_df)
            st.download_button(
                label="Excel Dosyasını İndir",
                data=excel_data,
                file_name=f"tyt_program_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Excel export hatası: {str(e)}")

st.markdown("---")
st.markdown("💡 **İpucu:** Düzenli olarak deneme sonuçlarınızı güncelleyin ve programınızı yenileyin!")
