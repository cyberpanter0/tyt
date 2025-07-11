import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import io

# Groq AI Client
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

# Zorluk katsayıları
ZORLUK_KATSAYILARI = {
    "Kolay": 0.5,
    "Orta": 1,
    "Zor": 2
}

def get_ai_suggestion(konu_analizi):
    """Groq AI'dan çalışma önerisi al"""
    if not client:
        return "AI hizmeti şu anda kullanılamıyor. Lütfen manuel olarak öncelikli konulara odaklanın."
    
    try:
        sorted_topics = sorted(konu_analizi.items(), key=lambda x: x[1]['oncelik_puani'], reverse=True)
        kotu_konular = sorted_topics[:5]
        iyi_konular = sorted_topics[-3:]
        
        ders_analizi = {}
        for konu, info in konu_analizi.items():
            ders = info['ders']
            if ders not in ders_analizi:
                ders_analizi[ders] = {'toplam_puan': 0, 'konu_sayisi': 0}
            ders_analizi[ders]['toplam_puan'] += info['oncelik_puani']
            ders_analizi[ders]['konu_sayisi'] += 1
        
        for ders in ders_analizi:
            ders_analizi[ders]['ortalama'] = ders_analizi[ders]['toplam_puan'] / ders_analizi[ders]['konu_sayisi']
        
        en_kotu_ders = max(ders_analizi.items(), key=lambda x: x[1]['ortalama'])
        
        prompt = f"""
        Sen deneyimli bir TYT koçusun. Bir öğrencinin performans analizi şu şekilde:
        
        🔴 ÖNCELIKLI KONULAR (En kötü 5):
        {chr(10).join([f"• {konu.split(' - ')[1]} ({konu.split(' - ')[0]}) - Puan: {info['oncelik_puani']:.1f}" for konu, info in kotu_konular])}
        
        🟢 İYI DURUMDA (En iyi 3):
        {chr(10).join([f"• {konu.split(' - ')[1]} ({konu.split(' - ')[0]}) - Puan: {info['oncelik_puani']:.1f}" for konu, info in iyi_konular])}
        
        📊 EN PROBLEMLI DERS: {en_kotu_ders[0]} (Ortalama: {en_kotu_ders[1]['ortalama']:.1f})
        
        Kısa ve özgün bir çalışma stratejisi öner. Maksimum 200 kelime.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sen uzman bir TYT koçusun. Öğrencilere kişiselleştirilmiş, pratik ve motive edici çalışma stratejileri veriyorsun."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            max_tokens=250,
            temperature=0.8
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI önerisi alınırken hata oluştu: {str(e)}"

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
                    'gercek_soru': sonuclar['gercek_soru']
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
            'Boş': bilgi['bos'],
            'Gerçek Soru': bilgi['gercek_soru']
        })
    
    return program

def excel_export(program_df):
    """Excel dosyası oluştur"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            program_df.to_excel(writer, sheet_name='Çalışma Programı', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Çalışma Programı']
            
            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 8)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 30)
            worksheet.set_column('E:E', 15)
            worksheet.set_column('F:F', 10)
            worksheet.set_column('G:J', 8)
    except ImportError:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            program_df.to_excel(writer, sheet_name='Çalışma Programı', index=False)
    
    return output.getvalue()

# Streamlit arayüzü
st.set_page_config(page_title="TYT Hazırlık Uygulaması", layout="wide")

st.title("🎯 TYT Hazırlık Uygulaması")
st.markdown("---")

# Sidebar - AI Koç
with st.sidebar:
    st.header("🤖 AI Koçun")
    if client:
        if st.button("🔥 Kişisel Strateji Al"):
            if 'analiz_sonucu' in st.session_state:
                with st.spinner("AI senin için özel strateji hazırlıyor..."):
                    suggestion = get_ai_suggestion(st.session_state['analiz_sonucu'])
                    st.success("🎯 **Senin İçin Özel Strateji:**")
                    st.info(suggestion)
            else:
                st.warning("⚠️ Önce veri giriş yapın!")
    else:
        st.warning("AI hizmeti şu anda kullanılamıyor.")

# Ana içerik
tab1, tab2, tab3 = st.tabs(["📊 Veri Giriş", "📈 Analiz", "📅 Program"])

with tab1:
    st.header("Deneme Sonuçlarını Girin")
    
    if 'veriler' not in st.session_state:
        st.session_state.veriler = {}
    
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
        
        with col2:
            gun_sayisi = st.number_input("Kaç Gün Çalışacaksınız?", min_value=1, max_value=365, value=30)
        
        if st.button("📋 Program Oluştur"):
            program = program_olustur(st.session_state.analiz_sonucu, baslangic_tarihi, gun_sayisi)
            program_df = pd.DataFrame(program)
            st.session_state.program_df = program_df
            
            st.dataframe(program_df, use_container_width=True)
            
            st.subheader("📊 İlerleme Takibi")
            dersler = program_df['Ders'].unique()
            
            for ders in dersler:
                ders_konular = program_df[program_df['Ders'] == ders]
                tamamlama_orani = len(ders_konular) / len(program_df) * 100
                
                st.progress(tamamlama_orani / 100)
                st.text(f"{ders}: {len(ders_konular)} konu - %{tamamlama_orani:.1f}")
    else:
        st.warning("Önce analiz yapın!")

# Export butonu
if 'program_df' in st.session_state:
    st.markdown("---")
    st.subheader("📁 Dışa Aktarma")
    
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

st.markdown("---")
st.markdown("💡 **İpucu:** Düzenli olarak deneme sonuçlarınızı güncelleyin ve programınızı yenileyin!")
