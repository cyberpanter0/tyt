import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import io
import os
import fpdf2

# Groq AI Client - Hata kontrolü ile
@st.cache_resource
def init_groq_client():
    try:
        from groq import Groq
        api_key = st.secrets.get("GROQ_API_KEY", "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")
        return Groq(api_key=api_key)
    except ImportError:
        st.error("Groq kütüphanesi yüklenemedi. AI özellikler devre dışı.")
        return None
    except Exception as e:
        st.error(f"Groq client başlatılamadı: {str(e)}")
        return None

client = init_groq_client()

# Konu verileri
KONU_VERILERI = {
    "Türkçe": {
        "Paragraf": {"zorluk": "Zor", "ortalama_soru": 23},
        "Cümlede Anlam": {"zorluk": "Orta", "ortalama_soru": 3},
        "Sözcükte Anlam": {"zorluk": "Kolay", "ortalama_soru": 2},
        "Anlatım Bozukluğu": {"zorluk": "Orta", "ortalama_soru": 2},
        "Yazım Kuralları": {"zorluk": "Kolay", "ortalama_soru": 1},
        "Noktalama İşaretleri": {"zorluk": "Kolay", "ortalama_soru": 1},
        "Dil Bilgisi": {"zorluk": "Orta", "ortalama_soru": 6},
        "Sözel Mantık": {"zorluk": "Zor", "ortalama_soru": 2}
    },
    "Matematik": {
        "Temel Kavramlar": {"zorluk": "Kolay", "ortalama_soru": 2},
        "Sayı Basamakları": {"zorluk": "Kolay", "ortalama_soru": 1},
        "Bölme / Bölünebilme": {"zorluk": "Kolay", "ortalama_soru": 1},
        "EBOB – EKOK": {"zorluk": "Orta", "ortalama_soru": 1},
        "Rasyonel / Kök / Üslü Sayılar": {"zorluk": "Orta", "ortalama_soru": 4},
        "Denklem Çözme": {"zorluk": "Orta", "ortalama_soru": 3},
        "Oran – Orantı": {"zorluk": "Kolay", "ortalama_soru": 2},
        "Problemler": {"zorluk": "Zor", "ortalama_soru": 9},
        "Kümeler, Mantık": {"zorluk": "Orta", "ortalama_soru": 3},
        "Fonksiyon": {"zorluk": "Orta", "ortalama_soru": 2},
        "Permütasyon, Kombinasyon, Olasılık": {"zorluk": "Zor", "ortalama_soru": 3},
        "Veri – Grafik": {"zorluk": "Kolay", "ortalama_soru": 1}
    },
    "Geometri": {
        "Temel Kavramlar, Açılar": {"zorluk": "Kolay", "ortalama_soru": 1},
        "Üçgenler": {"zorluk": "Orta", "ortalama_soru": 3},
        "Çokgenler & Dörtgenler": {"zorluk": "Orta", "ortalama_soru": 2},
        "Çember & Daire": {"zorluk": "Zor", "ortalama_soru": 2},
        "Analitik Geometri": {"zorluk": "Zor", "ortalama_soru": 1},
        "Katı Cisimler": {"zorluk": "Orta", "ortalama_soru": 1}
    },
    "Fizik": {
        "Fizik Bilimine Giriş": {"zorluk": "Kolay", "ortalama_soru": 1},
        "Kuvvet – Hareket": {"zorluk": "Orta", "ortalama_soru": 2},
        "Enerji – İş – Güç": {"zorluk": "Orta", "ortalama_soru": 1},
        "Basınç – Kaldırma": {"zorluk": "Zor", "ortalama_soru": 1},
        "Elektrik – Manyetizma": {"zorluk": "Zor", "ortalama_soru": 1},
        "Optik – Dalgalar": {"zorluk": "Zor", "ortalama_soru": 1}
    },
    "Kimya": {
        "Kimya Bilimi, Atom": {"zorluk": "Kolay", "ortalama_soru": 1},
        "Periyodik Sistem, Bileşikler": {"zorluk": "Orta", "ortalama_soru": 2},
        "Kimyasal Türler & Etkileşim": {"zorluk": "Orta", "ortalama_soru": 1},
        "Karışımlar, Asit – Baz – Tuz": {"zorluk": "Orta", "ortalama_soru": 1},
        "Kimyasal Hesaplamalar": {"zorluk": "Zor", "ortalama_soru": 2}
    },
    "Biyoloji": {
        "Canlıların Temel Bileşenleri": {"zorluk": "Kolay", "ortalama_soru": 1},
        "Hücre – Organeller": {"zorluk": "Orta", "ortalama_soru": 1},
        "Hücre Zarından Madde Geçişi": {"zorluk": "Zor", "ortalama_soru": 1},
        "Canlı Sınıflandırma – Sistemler": {"zorluk": "Orta", "ortalama_soru": 2},
        "Ekosistem, Madde Döngüleri": {"zorluk": "Orta", "ortalama_soru": 1}
    },
    "Tarih": {
        "İlk ve Orta Çağ Uygarlıkları": {"zorluk": "Orta", "ortalama_soru": 1},
        "Osmanlı Tarihi": {"zorluk": "Orta", "ortalama_soru": 1},
        "Kurtuluş Savaşı – Atatürk İlkeleri": {"zorluk": "Zor", "ortalama_soru": 2},
        "Çağdaş Türkiye, İnkılaplar": {"zorluk": "Orta", "ortalama_soru": 1}
    },
    "Coğrafya": {
        "Harita Bilgisi": {"zorluk": "Kolay", "ortalama_soru": 1},
        "İklim – Yer Şekilleri": {"zorluk": "Orta", "ortalama_soru": 2},
        "Beşeri ve Ekonomik Coğrafya": {"zorluk": "Orta", "ortalama_soru": 2}
    },
    "Felsefe": {
        "Bilgi – Varlık – Ahlak": {"zorluk": "Zor", "ortalama_soru": 3},
        "Siyaset – Din – Sanat": {"zorluk": "Zor", "ortalama_soru": 2}
    },
    "Din Kültürü": {
        "İnanç, İbadet, Ahlak": {"zorluk": "Kolay", "ortalama_soru": 3},
        "Hz. Muhammed & İslam Düşüncesi": {"zorluk": "Orta", "ortalama_soru": 2}
    }
}

def get_ai_suggestion(konu_analizi):
    """Groq AI'dan çalışma önerisi al"""
    if not client:
        return "AI hizmeti şu anda kullanılamıyor. Lütfen manuel olarak öncelikli konulara odaklanın."
    
    try:
        # En düşük puanlı (en iyi) 3 konu ve en yüksek puanlı (en kötü) 3 konu
        sorted_topics = sorted(konu_analizi.items(), key=lambda x: x[1]['oncelik_puani'])
        iyi_konular = sorted_topics[:3]
        kotu_konular = sorted_topics[-3:]
        
        prompt = f"""
        Bir TYT öğrencisine çalışma önerisi ver. Analiz sonuçları:
        
        EN İYİ KONULAR:
        {', '.join([f"{konu} (Puan: {info['oncelik_puani']:.1f})" for konu, info in iyi_konular])}
        
        EN KÖTÜ KONULAR:
        {', '.join([f"{konu} (Puan: {info['oncelik_puani']:.1f})" for konu, info in kotu_konular])}
        
        Kısa ve öz bir öneri ver (maksimum 150 kelime).
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen bir TYT koçusun. Öğrencilere kısa ve pratik çalışma önerileri veriyorsun."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            max_tokens=200,
            temperature=0.7
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI önerisi alınırken hata oluştu: {str(e)}"

def hesapla_oncelik_puani(dogru, yanlis, bos):
    """Öncelik puanını hesapla"""
    return (yanlis * 1.5) + (bos * 1.2) - (dogru * 0.5)

def analiz_et(veriler):
    """Tüm verileri analiz et"""
    analiz = {}
    for ders, konular in veriler.items():
        for konu, sonuclar in konular.items():
            if sonuclar['dogru'] + sonuclar['yanlis'] + sonuclar['bos'] > 0:
                oncelik_puani = hesapla_oncelik_puani(
                    sonuclar['dogru'], 
                    sonuclar['yanlis'], 
                    sonuclar['bos']
                )
                analiz[f"{ders} - {konu}"] = {
                    'ders': ders,
                    'konu': konu,
                    'oncelik_puani': oncelik_puani,
                    'dogru': sonuclar['dogru'],
                    'yanlis': sonuclar['yanlis'],
                    'bos': sonuclar['bos'],
                    'zorluk': KONU_VERILERI[ders][konu]['zorluk']
                }
    return analiz

def program_olustur(analiz, baslangic_tarihi, gun_sayisi):
    """Çalışma programı oluştur"""
    sorted_konular = sorted(analiz.items(), key=lambda x: x[1]['oncelik_puani'], reverse=True)
    
    program = []
    gun_basina_konu = max(1, len(sorted_konular) // gun_sayisi)
    
    for i, (konu_adi, bilgi) in enumerate(sorted_konular):
        gun_no = min(i // gun_basina_konu, gun_sayisi - 1)
        tarih = baslangic_tarihi + timedelta(days=gun_no)
        
        program.append({
            'Tarih': tarih.strftime('%d.%m.%Y'),
            'Gün': gun_no + 1,
            'Ders': bilgi['ders'],
            'Konu': bilgi['konu'],
            'Öncelik Puanı': bilgi['oncelik_puani'],
            'Zorluk': bilgi['zorluk'],
            'Doğru': bilgi['dogru'],
            'Yanlış': bilgi['yanlis'],
            'Boş': bilgi['bos']
        })
    
    return program

def excel_export(program_df):
    """Excel dosyası oluştur"""
    output = io.BytesIO()
    
    try:
        # xlsxwriter kullanmaya çalış
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            program_df.to_excel(writer, sheet_name='Çalışma Programı', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Çalışma Programı']
            
            # Sütun genişliklerini ayarla
            worksheet.set_column('A:A', 12)  # Tarih
            worksheet.set_column('B:B', 8)   # Gün
            worksheet.set_column('C:C', 15)  # Ders
            worksheet.set_column('D:D', 30)  # Konu
            worksheet.set_column('E:E', 15)  # Öncelik Puanı
            worksheet.set_column('F:F', 10)  # Zorluk
            worksheet.set_column('G:I', 8)   # Doğru, Yanlış, Boş
    except ImportError:
        # xlsxwriter yoksa openpyxl kullan
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            program_df.to_excel(writer, sheet_name='Çalışma Programı', index=False)
    
    return output.getvalue()

def simple_pdf_export(program_df):
    """Basit PDF raporu oluştur"""
    try:
        from fpdf import FPDF
        
        class PDF(FPDF):
            def __init__(self):
                super().__init__()
                self.add_font('Arial', '', 'arial.ttf', uni=True)
                self.add_font('Arial', 'B', 'arialbd.ttf', uni=True)
                self.add_font('Arial', 'I', 'ariali.ttf', uni=True)
                
            def header(self):
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, 'TYT Çalışma Programı', 0, 1, 'C')
                self.ln(10)
            
            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')
        
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 10)
        
        pdf.cell(0, 10, f'Rapor Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}', 0, 1)
        pdf.ln(5)
        
        for _, row in program_df.iterrows():
            pdf.cell(0, 8, f"{row['Tarih']} - {row['Ders']} - {row['Konu']}", 0, 1)
        
        return pdf.output(dest='S').encode('latin-1')
    except ImportError:
        return None
    except Exception:
        # Fallback - font dosyaları yoksa basit metin
        try:
            from fpdf2 import FPDF
            
            class SimplePDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 16)
                    self.cell(0, 10, 'TYT Calisma Programi', 0, 1, 'C')
                    self.ln(10)
                
                def footer(self):
                    self.set_y(-15)
                    self.set_font('Arial', 'I', 8)
                    self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')
            
            pdf = SimplePDF()
            pdf.add_page()
            pdf.set_font('Arial', '', 10)
            
            pdf.cell(0, 10, f'Rapor Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}', 0, 1)
            pdf.ln(5)
            
            for _, row in program_df.iterrows():
                # Unicode karakterleri ASCII'ye çevir
                ders = str(row['Ders']).replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i').replace('ö', 'o').replace('ş', 's').replace('ü', 'u')
                konu = str(row['Konu']).replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i').replace('ö', 'o').replace('ş', 's').replace('ü', 'u').replace('–', '-')
                pdf.cell(0, 8, f"{row['Tarih']} - {ders} - {konu}", 0, 1)
            
            return pdf.output(dest='S').encode('latin-1')
        except Exception:
            return None

# Streamlit arayüzü
st.set_page_config(page_title="TYT Hazırlık Uygulaması", layout="wide")

st.title("🎯 TYT Hazırlık Uygulaması")
st.markdown("---")

# Sidebar - AI Koç
with st.sidebar:
    st.header("🤖 AI Koçun")
    if client:
        if st.button("AI Önerisi Al"):
            if 'analiz_sonucu' in st.session_state:
                with st.spinner("AI analiz yapıyor..."):
                    suggestion = get_ai_suggestion(st.session_state['analiz_sonucu'])
                    st.info(suggestion)
            else:
                st.warning("Önce veri giriş yapın!")
    else:
        st.warning("AI hizmeti şu anda kullanılamıyor.")

# Ana içerik
tab1, tab2, tab3 = st.tabs(["📊 Veri Giriş", "📈 Analiz", "📅 Program"])

with tab1:
    st.header("Deneme Sonuçlarını Girin")
    
    # Veri depolama
    if 'veriler' not in st.session_state:
        st.session_state.veriler = {}
    
    # Ders grupları
    ders_gruplari = {
        "Türkçe": ["Türkçe"],
        "Matematik": ["Matematik", "Geometri"],
        "Fen Bilimleri": ["Fizik", "Kimya", "Biyoloji"],
        "Sosyal Bilimler": ["Tarih", "Coğrafya", "Felsefe", "Din Kültürü"]
    }
    
    for grup_adi, dersler in ders_gruplari.items():
        with st.expander(f"📚 {grup_adi}", expanded=False):
            for ders in dersler:
                st.subheader(f"{ders}")
                
                if ders not in st.session_state.veriler:
                    st.session_state.veriler[ders] = {}
                
                cols = st.columns(4)
                for i, (konu, bilgi) in enumerate(KONU_VERILERI[ders].items()):
                    col_idx = i % 4
                    
                    with cols[col_idx]:
                        st.markdown(f"**{konu}**")
                        st.caption(f"Zorluk: {bilgi['zorluk']}")
                        
                        if konu not in st.session_state.veriler[ders]:
                            st.session_state.veriler[ders][konu] = {'dogru': 0, 'yanlis': 0, 'bos': 0}
                        
                        dogru = st.number_input(f"Doğru", min_value=0, key=f"{ders}_{konu}_dogru", 
                                              value=st.session_state.veriler[ders][konu]['dogru'])
                        yanlis = st.number_input(f"Yanlış", min_value=0, key=f"{ders}_{konu}_yanlis",
                                               value=st.session_state.veriler[ders][konu]['yanlis'])
                        bos = st.number_input(f"Boş", min_value=0, key=f"{ders}_{konu}_bos",
                                            value=st.session_state.veriler[ders][konu]['bos'])
                        
                        st.session_state.veriler[ders][konu] = {
                            'dogru': dogru,
                            'yanlis': yanlis,
                            'bos': bos
                        }

with tab2:
    st.header("📊 Analiz Sonuçları")
    
    if st.button("Analiz Et"):
        analiz_sonucu = analiz_et(st.session_state.veriler)
        st.session_state.analiz_sonucu = analiz_sonucu
        
        if analiz_sonucu:
            # Öncelik sıralaması
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
            
            # Grafik
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
        
        with col2:
            gun_sayisi = st.number_input("Kaç Gün Çalışacaksınız?", min_value=1, max_value=365, value=30)
        
        if st.button("Program Oluştur"):
            program = program_olustur(st.session_state.analiz_sonucu, baslangic_tarihi, gun_sayisi)
            program_df = pd.DataFrame(program)
            st.session_state.program_df = program_df
            
            st.dataframe(program_df, use_container_width=True)
            
            # İlerleme takibi
            st.subheader("📊 İlerleme Takibi")
            dersler = program_df['Ders'].unique()
            
            for ders in dersler:
                ders_konular = program_df[program_df['Ders'] == ders]
                tamamlama_orani = 100 - (len(ders_konular) / len(program_df) * 100)
                
                st.progress(tamamlama_orani / 100)
                st.text(f"{ders}: {len(ders_konular)} konu - %{tamamlama_orani:.1f} hedef")
    else:
        st.warning("Önce analiz yapın!")

# Export butonları
if 'program_df' in st.session_state:
    st.markdown("---")
    st.subheader("📁 Dışa Aktarma")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Excel'e Aktar"):
            try:
                excel_data = excel_export(st.session_state.program_df)
                st.download_button(
                    label="Excel Dosyasını İndir",
                    data=excel_data,
                    file_name=f"tyt_program_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Excel export hatası: {str(e)}")
    
    with col2:
        if st.button("📄 PDF'e Aktar"):
            try:
                pdf_data = simple_pdf_export(st.session_state.program_df)
                if pdf_data:
                    st.download_button(
                        label="PDF Dosyasını İndir",
                        data=pdf_data,
                        file_name=f"tyt_rapor_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("PDF export için fpdf2 kütüphanesi gerekli.")
            except Exception as e:
                st.error(f"PDF export hatası: {str(e)}")

# Footer
st.markdown("---")
st.markdown("💡 **İpucu:** Düzenli olarak deneme sonuçlarınızı güncelleyin ve programınızı yenileyin!")
