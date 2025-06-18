import streamlit as st
import os
import re
import main
import json
from main import simulator
import asyncio
import pandas as pd
from datetime import datetime
import time
import base64
import html
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import tempfile
from random import choice

# Sayfa yapılandırması
st.set_page_config(
    page_title="Odak Grup Simülasyonu",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS stilleri
st.markdown("""
<style>
    /* Genel tema ayarları */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Başlık ve alt başlıklar */
    h1, h2, h3 {
        color: #FAFAFA !important;
    }
    
    /* Butonlar */
    .stButton>button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 0.8rem;
        font-size: 1.1rem;
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #4B4B4B;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #3B3B3B;
        border-color: #6B6B6B;
    }
    
    .stButton>button:disabled {
        background-color: #1E1E1E;
        color: #666666;
        border-color: #333333;
    }
    
    /* Mesaj kutuları */
    .persona-message, .moderator-message {
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 8px;
        background-color: #2d3748;
    }
    
    .moderator-message {
        background-color: #1a365d;
    }
    
    .message-header {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .profile-pic {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .message-time {
        margin-left: auto;
        color: #a0aec0;
        font-size: 0.875rem;
    }
    
    .message-content {
        margin-left: 3rem;
    }
    
    .message-text {
        color: #e2e8f0;
        line-height: 1.5;
    }
    
    /* Başarı ve hata mesajları */
    .stSuccess {
        background-color: #1E3A5F !important;
        color: #FAFAFA !important;
    }
    
    .stError {
        background-color: #4B1E1E !important;
        color: #FAFAFA !important;
    }
    
    /* Dosya yükleyici */
    .stFileUploader {
        background-color: #262730;
        border: 1px solid #4B4B4B;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Alt başlıklar */
    .stSubheader {
        color: #FAFAFA !important;
        border-bottom: 2px solid #4B4B4B;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Persona adını profile_pic yoluna eşleyecek bir yardımcı fonksiyon
def get_persona_pic(persona_name):
    pp_dir = 'personas_pp'
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', persona_name.lower().replace(' ', '_'))
    pic_path_jpg = f"{pp_dir}/{safe_name}.jpg"
    pic_path_png = f"{pp_dir}/{safe_name}.png"
    if os.path.exists(pic_path_jpg):
        return pic_path_jpg
    elif os.path.exists(pic_path_png):
        return pic_path_png
    else:
        return None

# Sayfa başlığı
st.title("🎯 Odak Grup Simülasyonu")

# İki sütunlu layout
col1, col2 = st.columns([2, 1])

with col1:
    # Gündem dosyası yükleme
    uploaded_file = st.file_uploader("Gündem Dosyası Yükle (CSV/Excel)", type=['csv', 'xlsx', 'xls'])
    if uploaded_file is not None:
        # Dosyayı kaydet
        os.makedirs('data', exist_ok=True)
        file_path = f"data/{uploaded_file.name}"
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # Veriyi yükle
        if simulator.load_agenda_data(file_path):
            st.success(f"{len(simulator.agenda_items)} gündem maddesi yüklendi.")
        else:
            st.error("Dosya yüklendi ancak veri okunamadı. Lütfen dosya formatını kontrol edin.")

    # Kontrol butonları
    control_col1, control_col2 = st.columns(2)
    with control_col1:
        # Simülasyonun durdurulup durdurulmadığını session_state ile takip et
        if 'stop_simulation' not in st.session_state:
            st.session_state['stop_simulation'] = False
        start_button = st.button("▶️ Odak Grup Makinasını Başlat", 
                               disabled=not (uploaded_file is not None or simulator.agenda_items))
    with control_col2:
        stop_button = st.button("⏹️ Durdur")

with col2:
    # Simülasyon durumu
    st.subheader("📊 Simülasyon Durumu")
    status_placeholder = st.empty()
    
    # İstek istatistikleri
    st.subheader("📈 API İstek İstatistikleri")
    stats_placeholder = st.empty()

# Simülasyonun durdurulup durdurulmadığını session_state ile takip et
if 'stop_simulation' not in st.session_state:
    st.session_state['stop_simulation'] = False

# Simülasyonu başlat
if start_button and (uploaded_file is not None or simulator.agenda_items):
    st.info("Simülasyon başlatılıyor...")
    simulator.is_running = True
    st.session_state['stop_simulation'] = False
    
    # Bellek ve log alanları
    st.subheader("🧠 Hatırlanan Özetler (Persona Belleği)")
    memory_placeholder = st.empty()
    
    st.subheader("🤔 Thinking Agent (MCP) Logları")
    mcp_logs_placeholder = st.empty()
    
    # Tartışma alanı
    st.subheader("💬 Tartışma:")
    discussion_placeholder = st.empty()
    
    # Hata mesajı alanı
    error_placeholder = st.empty()
    
    # Simülasyonu başlat
    try:
        # Yeni bir event loop oluştur
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Bellek ve logları güncelle
        def update_memory_and_logs():
            try:
                memory_text = "Henüz özetlenmiş bir bellek yok."
                if simulator.memory:
                    memory_text = "\n\n".join([f"{k[0]} - {k[1]}: {v}" for k, v in simulator.memory.items()])
                memory_placeholder.text(memory_text)
                
                # MCP loglarını güncelle
                if hasattr(simulator, 'mcp_logs'):
                    mcp_logs_text = "\n\n".join([f"{log['type']}: {log['prompt'][:100]}... -> {log['response'][:100]}..." for log in simulator.mcp_logs])
                    mcp_logs_placeholder.text(mcp_logs_text)
                else:
                    mcp_logs_placeholder.text("Henüz MCP logu yok.")
                
                # İstek istatistiklerini güncelle
                stats = simulator.llm_client.get_request_stats()
                stats_text = f"""
                📊 **API İstek İstatistikleri**
                - Toplam İstek: {stats['total_requests']}
                - Başarılı İstek: {stats['successful_requests']}
                - Başarısız İstek: {stats['failed_requests']}
                - Başarı Oranı: {stats['success_rate']:.1f}%
                - Mevcut İstek: {stats['current_request_count']}
                - Son İstek: {datetime.fromtimestamp(stats['last_request_time']).strftime('%H:%M:%S')}
                """
                stats_placeholder.markdown(stats_text)
            except Exception as e:
                error_placeholder.error(f"Güncelleme hatası: {str(e)}")
        
        # Tartışmayı güncelle
        def update_discussion():
            try:
                discussion_text = ""
                for entry in simulator.discussion_log:
                    timestamp = entry['timestamp'].strftime("%H:%M:%S")
                    speaker = entry['speaker']
                    message = entry['message']

                    # Mesajı temizle
                    if isinstance(message, str):
                        msg = message.strip()
                        # Kod bloğu karakterlerini ve gereksiz boşlukları kaldır
                        msg = msg.replace('```', '').replace('\n', ' ').replace('\r', '')
                        msg = html.escape(msg)
                    else:
                        msg = str(message)

                    # Profil fotoğrafı varsa göster
                    pic_path = get_persona_pic(speaker)
                    if pic_path:
                        discussion_text += f'''
                        <div class="{'moderator-message' if speaker == 'Moderatör' else 'persona-message'}">
                            <div class="message-header">
                                <img src="data:image/png;base64,{get_base64_from_file(pic_path)}" class="profile-pic">
                                <strong>{speaker}</strong>
                                <span class="message-time">{timestamp}</span>
                            </div>
                            <div class="message-content">
                                <div class="message-text">{msg}</div>
                            </div>
                        </div>
                        '''
                    else:
                        discussion_text += f'''
                        <div class="{'moderator-message' if speaker == 'Moderatör' else 'persona-message'}">
                            <div class="message-header">
                                <strong>{speaker}</strong>
                                <span class="message-time">{timestamp}</span>
                            </div>
                            <div class="message-content">
                                <div class="message-text">{msg}</div>
                            </div>
                        </div>
                        '''
                discussion_placeholder.markdown(discussion_text, unsafe_allow_html=True)
            except Exception as e:
                error_placeholder.error(f"Tartışma güncelleme hatası: {str(e)}")
        
        # Simülasyon durumunu güncelle
        def update_status(current_round, total_rounds, current_agenda, current_speaker, error=None):
            try:
                status_text = f"""
                <div class="status-box">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">🔄</span>
                        <strong style="font-size: 1.2rem;">Simülasyon Durumu</strong>
                    </div>
                    <div style="margin-left: 2rem;">
                        <div style="margin: 0.5rem 0;">📊 Tur: {current_round}/{total_rounds}</div>
                        <div style="margin: 0.5rem 0;">📝 Gündem Maddesi: {current_agenda}</div>
                        <div style="margin: 0.5rem 0;">👤 Konuşan: {current_speaker}</div>
                        <div style="margin: 0.5rem 0;">{'🟢 Çalışıyor' if simulator.is_running else '🔴 Durduruldu'}</div>
                    </div>
                """
                if error:
                    status_text += f"""
                    <div style="margin-top: 1rem; padding: 0.5rem; background-color: #4B1E1E; border-radius: 8px;">
                        ❌ <strong>Hata:</strong> {error}
                    </div>
                    """
                status_text += "</div>"
                status_placeholder.markdown(status_text, unsafe_allow_html=True)
            except Exception as e:
                error_placeholder.error(f"Durum güncelleme hatası: {str(e)}")
        
        # Profil fotoğrafını base64'e çevir
        def get_base64_from_file(file_path):
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        
        # Simülasyonu başlat ve periyodik olarak güncelle
        async def run_simulation():
            try:
                st.session_state['stop_simulation'] = False
                simulator.is_running = True
                # Gündem maddelerini puanla
                update_status(0, 1, "Başlatılıyor", "Sistem")
                await simulator.score_agenda_items()
                
                # Simülasyonu başlat
                round_count = 0
                max_rounds = 1  # Herkes bir kez konuşacak, sonra moderatör yönlendirecek
                for agenda_item in simulator.agenda_items:
                    if st.session_state['stop_simulation']:
                        simulator.is_running = False
                        update_status(0, 1, "Durduruldu", "-")
                        st.warning("Simülasyon kullanıcı tarafından durduruldu.")
                        return
                    # Moderatör girişini ekle
                    update_status(round_count + 1, max_rounds, agenda_item.title, "Moderatör")
                    first_persona = simulator.personas[0].name if simulator.personas else "katılımcı"
                    moderator_intro = await simulator.moderator.start_discussion(agenda_item, first_persona)
                    simulator.discussion_log.append({
                        'timestamp': datetime.now(),
                        'speaker': 'Moderatör',
                        'message': moderator_intro
                    })
                    update_discussion()
                    update_memory_and_logs()
                    await asyncio.sleep(2)
                    # Her persona bir kez konuşsun
                    for i, agent in enumerate(simulator.agents):
                        if st.session_state['stop_simulation']:
                            simulator.is_running = False
                            update_status(round_count + 1, max_rounds, agenda_item.title, agent.persona.name)
                            st.warning("Simülasyon kullanıcı tarafından durduruldu.")
                            return
                        update_status(round_count + 1, max_rounds, agenda_item.title, agent.persona.name)
                        context = simulator._build_context()
                        response = await agent.generate_response(context, agenda_item)
                        simulator.discussion_log.append({
                            'timestamp': datetime.now(),
                            'speaker': agent.persona.name,
                            'message': response
                        })
                        update_discussion()
                        update_memory_and_logs()
                        await asyncio.sleep(3)
                        # Moderatör geçişi
                        if i < len(simulator.agents) - 1:
                            update_status(round_count + 1, max_rounds, agenda_item.title, "Moderatör")
                            next_persona = simulator.agents[i + 1].persona.name
                            moderator_transition = await simulator.moderator.give_turn(
                                agent.persona.name, next_persona
                            )
                            simulator.discussion_log.append({
                                'timestamp': datetime.now(),
                                'speaker': 'Moderatör',
                                'message': moderator_transition
                            })
                            update_discussion()
                            update_memory_and_logs()
                            await asyncio.sleep(2)
                    # Herkes konuştu, moderatör tartışmayı özetlesin veya minik bir yorum yapsın
                    yorumlar = [
                        "Gerçekten ilginç görüşler ortaya çıktı! Katılımcılarımıza teşekkürler.",
                        "Tartışma oldukça hareketli geçti, herkesin katkısı çok değerliydi.",
                        "Farklı bakış açılarıyla zenginleşen bir tartışma oldu.",
                        "Her birinizin yorumu tartışmaya ayrı bir renk kattı!"
                    ]
                    moderator_comment = choice(yorumlar)
                    simulator.discussion_log.append({
                        'timestamp': datetime.now(),
                        'speaker': 'Moderatör',
                        'message': moderator_comment
                    })
                    update_discussion()
                    update_memory_and_logs()
                    await asyncio.sleep(2)
                simulator.is_running = False
                update_status(1, 1, "Tamamlandı", "-")
                st.success("Simülasyon tamamlandı.")
            except Exception as e:
                simulator.is_running = False
                error_msg = f"Simülasyon hatası: {str(e)}"
                update_status(1, 1, "Hata", "-", error_msg)
                error_placeholder.error(error_msg)
                st.error("Simülasyon beklenmedik bir hata ile karşılaştı.")
        
        # Simülasyonu başlat
        loop.run_until_complete(run_simulation())
    except Exception as e:
        st.error(f"Simülasyon başlatma hatası: {str(e)}")
    finally:
        # Event loop'u temizle
        try:
            loop.close()
        except:
            pass

# Simülasyonu durdur
if stop_button:
    st.session_state['stop_simulation'] = True
    simulator.is_running = False
    try:
        simulator.stop_simulation()
        update_status(0, 1, "Durduruldu", "-")
        st.warning("Simülasyon durduruldu.")
    except Exception as e:
        st.error(f"Simülasyon durdurma hatası: {str(e)}")

# Analiz raporu
if st.button("📊 Analiz Et") and simulator.discussion_log:
    st.info("Analiz oluşturuluyor...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analysis = loop.run_until_complete(simulator.generate_analysis())
        st.markdown(analysis)
        st.success("Analiz tamamlandı.")
    except Exception as e:
        st.error(f"Analiz oluşturma hatası: {str(e)}")
    finally:
        try:
            loop.close()
        except:
            pass

def create_pdf(conversation, analysis, personas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    # Normal font
    font_path = "DejaVuSans.ttf"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    # Bold font
    bold_font_path = "DejaVuSans-Bold.ttf"
    if not os.path.exists(bold_font_path):
        bold_font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    pdf.add_font('DejaVu', '', font_path)
    pdf.add_font('DejaVu', 'B', bold_font_path)
    pdf.set_font('DejaVu', '', 16)
    pdf.cell(0, 10, 'Odak Grup Simülasyonu', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(0, 10, 'Konuşma Geçmişi:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    for entry in conversation:
        timestamp = entry['timestamp'].strftime('%H:%M:%S')
        speaker = entry['speaker']
        message = entry['message']
        pdf.set_font('DejaVu', 'B', 12)
        pdf.cell(0, 8, f"{speaker} [{timestamp}]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('DejaVu', '', 12)
        pdf.multi_cell(0, 8, message)
        pdf.ln(2)
    pdf.ln(5)
    if analysis:
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(0, 10, 'Analiz:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('DejaVu', '', 12)
        pdf.multi_cell(0, 8, analysis)
    return pdf

# PDF indirme butonu
if st.button('📄 PDF Olarak İndir'):
    pdf = create_pdf(simulator.discussion_log, st.session_state.get('analysis', ''), simulator.personas)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
        pdf.output(tmpfile.name)
        with open(tmpfile.name, 'rb') as f:
            st.download_button('PDF Dosyasını İndir', f, file_name='odak_grup_simulasyonu.pdf', mime='application/pdf') 