# streamlit_app.py dosyasının EN BAŞI - Import bölümü

import os
import re
import json
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import time
import base64
import html
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import tempfile
import random
from typing import Dict, List, Optional
import logging
from pathlib import Path
import streamlit as st

# Import simulation components
try:
    from main import simulator, FocusGroupSimulator
except ImportError:
    st.error("⚠️ Ana simülasyon modülleri bulunamadı. main.py dosyasının mevcut olduğundan emin olun.")
    st.stop()

# Global simulation control variables
SIMULATION_STATE = {
    'running': False,
    'stop_requested': False
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="🎯 Odak Grup Persona Makinası",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    """Sadece gerekli CSS stilleri - Chat CSS'leri kaldırıldı"""
    css_content = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif !important;
    }
    
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1400px;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin-bottom: 2rem !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        height: 3rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(99, 102, 241, 0.4) !important;
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #374151 0%, #4b5563 100%) !important;
        color: #6b7280 !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Native chat message styling */
    .stChatMessage {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 15px !important;
        margin: 1rem 0 !important;
    }
    
    /* Moderatör mesajları için özel renk */
    .stChatMessage[data-testid="chat-message-Moderatör"] {
        border-color: rgba(236, 72, 153, 0.5) !important;
        background: rgba(236, 72, 153, 0.1) !important;
    }
    
    .success-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #f0fdf4 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }
    
    .error-card {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: #fef2f2 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }
    
    .info-card {
        background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%) !important;
        color: #f0f9ff !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    """
    
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'stop_simulation' not in st.session_state:
        st.session_state.stop_simulation = False
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = ""
    if 'agenda_loaded' not in st.session_state:
        st.session_state.agenda_loaded = False
    if 'expert_analysis_result' not in st.session_state:
        st.session_state.expert_analysis_result = ""
    if 'discussion_duration' not in st.session_state:
        st.session_state.discussion_duration = 15
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    # YENİ EKLEMELER - Analiz ve Rapor için:
    if 'basic_analysis_result' not in st.session_state:
        st.session_state.basic_analysis_result = ""
    if 'expert_analysis_result' not in st.session_state:
        st.session_state.expert_analysis_result = ""

def get_persona_pic(persona_name: str) -> Optional[str]:
    """Moderatör dahil tüm persona resimlerini bul"""
    if not persona_name:
        return None
        
    # Moderatör için özel kontrol - TÜM VARYASYONLAR
    moderator_names = ["moderatör", "moderator", "mod"]
    if persona_name.strip().lower() in moderator_names:
        moderator_paths = [
            '/home/baran/Desktop/OdakGrupMakinası/personas_pp/moderator.png',  # Tam yol
            'personas_pp/moderator.png',
            'personas_pp/moderator.jpg',
            'personas_pp/moderatör.png',
            'personas_pp/moderatör.jpg',
            'personas_pp/mod.png',
            'personas_pp/mod.jpg'
        ]
        
        for path in moderator_paths:
            if os.path.exists(path):
                logger.info(f"Moderatör resmi bulundu: {path}")
                return path
        
        logger.warning(f"Moderatör resmi bulunamadı. Aranan yollar: {moderator_paths}")
        return None
    
    pp_dir = Path('personas_pp')
    if not pp_dir.exists():
        logger.warning(f"Personas_pp directory not found: {pp_dir}")
        return None
    
    # Detaylı eşleştirme tablosu
    file_mappings = {
        # Elif için
        'elif': ['elif.jpg', 'elif.png', 'elif.jpeg'],
        
        # Hatice Teyze için - tüm varyasyonlar
        'hatice teyze': ['hatice_teyze.jpg', 'hatice_teyze.png', 'hatice_teyze.jpeg'],
        'hatice_teyze': ['hatice_teyze.jpg', 'hatice_teyze.png', 'hatice_teyze.jpeg'],
        'hatice': ['hatice_teyze.jpg', 'hatice_teyze.png', 'hatice_teyze.jpeg'],
        
        # Kenan Bey için - tüm varyasyonlar
        'kenan bey': ['kenan_bey.jpg', 'kenan_bey.png', 'kenan_bey.jpeg'],
        'kenan_bey': ['kenan_bey.jpg', 'kenan_bey.png', 'kenan_bey.jpeg'],
        'kenan': ['kenan_bey.jpg', 'kenan_bey.png', 'kenan_bey.jpeg'],
        
        # Tuğrul Bey için - tüm varyasyonlar
        'tuğrul bey': ['tugrul_bey.jpg', 'tugrul_bey.png', 'tugrul_bey.jpeg'],
        'tugrul bey': ['tugrul_bey.jpg', 'tugrul_bey.png', 'tugrul_bey.jpeg'],
        'tugrul_bey': ['tugrul_bey.jpg', 'tugrul_bey.png', 'tugrul_bey.jpeg'],
        'tuğrul_bey': ['tugrul_bey.jpg', 'tugrul_bey.png', 'tugrul_bey.jpeg'],
        'tugrul': ['tugrul_bey.jpg', 'tugrul_bey.png', 'tugrul_bey.jpeg'],
        'tuğrul': ['tugrul_bey.jpg', 'tugrul_bey.png', 'tugrul_bey.jpeg']
    }
    
    # İsmi normalize et
    name_lower = persona_name.lower().strip()
    
    # Direkt eşleştirme dene
    if name_lower in file_mappings:
        for filename in file_mappings[name_lower]:
            pic_path = pp_dir / filename
            if pic_path.exists():
                logger.info(f"Persona resmi bulundu: {persona_name} -> {pic_path}")
                return str(pic_path)
    
    # Güvenli isim dönüşümü ile dene
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name_lower.replace(' ', '_'))
    if safe_name in file_mappings:
        for filename in file_mappings[safe_name]:
            pic_path = pp_dir / filename
            if pic_path.exists():
                logger.info(f"Persona resmi bulundu (safe_name): {persona_name} -> {pic_path}")
                return str(pic_path)
    
    # Genel arama - tüm uzantıları dene
    for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG', '.JPEG']:
        # Orijinal isim ile
        pic_path = pp_dir / f"{name_lower}{ext}"
        if pic_path.exists():
            logger.info(f"Persona resmi bulundu (extension): {persona_name} -> {pic_path}")
            return str(pic_path)
            
        # Güvenli isim ile
        pic_path = pp_dir / f"{safe_name}{ext}"
        if pic_path.exists():
            logger.info(f"Persona resmi bulundu (safe+ext): {persona_name} -> {pic_path}")
            return str(pic_path)
    
    # Hiçbir şey bulunamazsa
    logger.warning(f"Persona resmi bulunamadı: {persona_name}")
    logger.debug(f"Mevcut dosyalar: {list(pp_dir.glob('*')) if pp_dir.exists() else 'Directory yok'}")
    
    return None

def get_base64_from_file(file_path: str) -> str:
    """Convert file to base64 string"""
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        logger.error(f"Error converting file to base64: {e}")
        return ""

def format_message_time(timestamp: datetime) -> str:
    """Format message timestamp"""
    return timestamp.strftime("%H:%M:%S")

def validate_agenda_file(df: pd.DataFrame) -> tuple[bool, str]:
    """Validate agenda file structure"""
    required_columns = ['TYPE', 'LINK', 'TITLE', 'CONTENT', 'COMMENTS']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Eksik sütunlar: {', '.join(missing_columns)}"
    
    if df.empty:
        return False, "Dosya boş"
    
    return True, "Dosya başarıyla doğrulandı"

def check_api_keys():
    """Check if API keys are available"""
    return (hasattr(simulator, 'llm_client') and 
            simulator.llm_client.api_key is not None and 
            simulator.llm_client.api_key.strip() != '')

def clean_html_and_format_text(text):
    """Metin temizleme - Native chat için optimize edildi"""
    if not text:
        return ""
    
    # String'e çevir
    text = str(text)
    
    # HTML taglerini kaldır
    text = re.sub(r'<[^>]+>', '', text)
    
    # HTML entity'lerini decode et
    text = html.unescape(text)
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text)
    
    # Başlangıç ve bitiş boşluklarını kaldır
    text = text.strip()
    
    # Çok uzun metinleri kısalt (Streamlit chat için)
    if len(text) > 800:
        text = text[:797] + "..."
    
    # Boş string kontrolü
    if not text or text == "0":
        return ""
    
    return text

def display_modern_chat():
    """Native Streamlit chat - İsim ve moderatör resmi sorunları düzeltildi"""
    if not simulator.discussion_log:
        st.info("💬 Henüz tartışma başlamadı...")
        return
    
    # Sabit yükseklikli container
    with st.container(height=600):
        for entry in simulator.discussion_log:
            speaker = entry['speaker']
            message = clean_html_and_format_text(entry['message'])
            timestamp = format_message_time(entry['timestamp'])
            
            # Boş mesajları atla
            if not message or message == '0' or len(message.strip()) == 0:
                continue
            
            # Moderatör kontrolü
            is_moderator = speaker.lower().strip() == 'moderatör'
            
            # Avatar belirleme - HER DURUM İÇİN
            avatar = None
            
            # Profil resmi ara - Moderatör dahil
            pic_path = get_persona_pic(speaker)
            if pic_path and os.path.exists(pic_path):
                try:
                    # Base64 encode
                    with open(pic_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                    avatar = f"data:image/jpeg;base64,{img_data}"
                    logger.info(f"Avatar yüklendi: {speaker} -> {pic_path}")
                except Exception as e:
                    logger.error(f"Avatar yükleme hatası ({speaker}): {e}")
                    avatar = "🎤" if is_moderator else speaker[0].upper()
            else:
                # Resim yoksa emoji/harf
                avatar = "🎤" if is_moderator else speaker[0].upper()
                logger.warning(f"Avatar bulunamadı, varsayılan kullanılıyor: {speaker}")
            
            # Native Streamlit chat message kullan
            with st.chat_message(speaker, avatar=avatar):
                # İSİM VE MESAJ AYRI SATIRLARDA GÖSTER
                
                # 1. Konuşan kişinin ismi (büyük, kalın)
                st.markdown(f"**🗣️ {speaker}**")
                
                # 2. Zaman damgası
                st.caption(f"🕐 {timestamp}")
                
                # 3. Mesaj içeriği
                st.markdown(f"💬 {message}")
                
                # 4. Moderatör için özel işaret
                if is_moderator:
                    st.markdown("---")
                    st.markdown("*🎯 Moderatör Mesajı*")
                
                # 5. Debug bilgisi (geliştirme aşamasında)
                if st.session_state.get('debug_mode', False):
                    st.caption(f"Debug: speaker={speaker}, is_mod={is_moderator}, pic_path={pic_path}")
        
        # Auto scroll için JavaScript
        st.markdown("""
        <script>
        setTimeout(function() {
            const containers = document.querySelectorAll('[data-testid="stVerticalBlock"]');
            if (containers.length > 0) {
                const chatContainer = containers[containers.length - 1];
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }, 500);
        </script>
        """, unsafe_allow_html=True)

def display_conversation_list():
    """Display conversation in a list format for easier reading"""
    if not simulator.discussion_log:
        st.info("💬 Henüz tartışma başlamadı...")
        return
    
    st.markdown("#### 📋 Konuşma Listesi")
    
    # Show conversation metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💬 Toplam Mesaj", len(simulator.discussion_log))
    with col2:
        persona_messages = len([entry for entry in simulator.discussion_log if entry['speaker'] != 'Moderatör'])
        st.metric("👥 Persona Mesajları", persona_messages)
    with col3:
        if simulator.discussion_log:
            last_speaker = simulator.discussion_log[-1]['speaker']
            st.metric("🎤 Son Konuşan", last_speaker)
    
    # Display all messages in expandable sections
    for i, entry in enumerate(simulator.discussion_log):
        timestamp = format_message_time(entry['timestamp'])
        speaker = entry['speaker']
        message = clean_html_and_format_text(entry['message'])
        
        if not message or message == '0':
            continue
        
        is_moderator = speaker == 'Moderatör'
        
        with st.expander(f"{'🎤' if is_moderator else '👤'} {speaker} - {timestamp}", expanded=False):
            pic_path = get_persona_pic(speaker)
            if pic_path:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.image(pic_path, width=80)
                with col2:
                    st.write(message)
            else:
                st.write(message)

def display_simulation_tab():
    """Display simulation tab content"""
    st.markdown("### 📁 Gündem Dosyası Yükleme")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Gündem dosyanızı seçin",
            type=['csv', 'xlsx', 'xls'],
            help="CSV veya Excel formatında gündem dosyası yükleyebilirsiniz"
        )
    
    with col2:
        if uploaded_file:
            st.markdown('<div class="success-card">✅ Dosya Seçildi</div>', unsafe_allow_html=True)
    
    # File processing
    if uploaded_file is not None:
        try:
            os.makedirs('data', exist_ok=True)
            file_path = f"data/{uploaded_file.name}"
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            is_valid, message = validate_agenda_file(df)
            
            if is_valid:
                if simulator.load_agenda_data(file_path):
                    st.session_state.agenda_loaded = True
                    st.markdown(f'<div class="success-card">✅ {len(simulator.agenda_items)} gündem maddesi başarıyla yüklendi!</div>', unsafe_allow_html=True)
                    
                    with st.expander("📋 Gündem Önizleme"):
                        for i, item in enumerate(simulator.agenda_items[:3], 1):
                            st.markdown(f"**{i}. {item.title}**")
                            st.write(item.content[:200] + "..." if len(item.content) > 200 else item.content)
                            st.divider()
                else:
                    st.markdown('<div class="error-card">❌ Dosya yüklenemedi. Lütfen format kontrolü yapın.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-card">❌ {message}</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f'<div class="error-card">❌ Dosya işleme hatası: {str(e)}</div>', unsafe_allow_html=True)
    
    # Control buttons
    st.markdown("### 🎮 Simülasyon Kontrolü")
    
    col_duration, col_spacer = st.columns([2, 2])
    
    with col_duration:
        col_slider, col_input = st.columns([2, 1])
        
        with col_slider:
            discussion_duration = st.slider(
                "🕒 Tartışma Süresi (dakika)", 
                min_value=5, 
                max_value=30, 
                value=st.session_state.get('discussion_duration', 15),
                step=5,
                help="Tartışmanın ne kadar süreceğini belirleyin"
            )
        
        with col_input:
            custom_duration = st.number_input(
                "Manuel Giriş", 
                min_value=1, 
                max_value=120, 
                value=discussion_duration,
                step=1,
                help="Özel süre girin (1-120 dakika)"
            )
            
        # Use custom input if it differs from slider
        final_duration = custom_duration if custom_duration != discussion_duration else discussion_duration
        st.session_state['discussion_duration'] = final_duration
        st.info(f"Seçilen süre: {final_duration} dakika (~{final_duration//5} tur tartışma)")
    
    button_col1, button_col2, button_col3 = st.columns(3)
    
    with button_col1:
        start_enabled = st.session_state.agenda_loaded and not SIMULATION_STATE['running']
        if st.button("▶️ Simülasyonu Başlat", disabled=not start_enabled, key="start_btn"):
            if not check_api_keys():
                st.error("❌ API anahtarları bulunamadı! Lütfen .env dosyasında GEMINI_API_KEY tanımlayın.")
                return
                
            SIMULATION_STATE['running'] = True
            SIMULATION_STATE['stop_requested'] = False
            start_simulation()
    
    with button_col2:
        if st.button("⏹️ Durdur", disabled=not SIMULATION_STATE['running'], key="stop_btn"):
            stop_simulation()
    
    with button_col3:
        if st.button("🔄 Sıfırla", key="reset_btn"):
            reset_simulation()
    
    display_simulation_status()

def start_simulation():
    """Start simulation synchronously"""
    try:
        if not simulator.agenda_items:
            st.error("❌ Gündem maddesi bulunamadı!")
            return
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        
        status_placeholder.markdown('<div class="info-card">📊 Gündem analizi başlatılıyor...</div>', unsafe_allow_html=True)
        progress_placeholder.progress(0.1)
        
        try:
            loop.run_until_complete(simulator.prepare_agenda_analysis())
            status_placeholder.markdown('<div class="success-card">✅ Gündem analizi tamamlandı!</div>', unsafe_allow_html=True)
            progress_placeholder.progress(0.3)
            
            if simulator.agenda_items and any(item.persona_scores for item in simulator.agenda_items):
                st.markdown("#### 📊 Gündem Puanları Hesaplandı")
                display_agenda_scores()
            
        except Exception as e:
            status_placeholder.markdown(f'<div class="error-card">❌ Gündem analizi hatası: {str(e)}</div>', unsafe_allow_html=True)
            SIMULATION_STATE['running'] = False
            return
        
        status_placeholder.markdown('<div class="info-card">💬 Tartışma başlatılıyor...</div>', unsafe_allow_html=True)
        progress_placeholder.progress(0.5)
        
        try:
            async def run_discussion():
                discussion_duration_minutes = st.session_state.get('discussion_duration', 5)
                start_time = time.time()
                end_time = start_time + (discussion_duration_minutes * 60)
                
                message_count = 0
                
                status_placeholder.markdown(f'<div class="info-card">💬 {discussion_duration_minutes} dakikalık tartışma başlatılıyor...</div>', unsafe_allow_html=True)
                
                async def on_new_message():
                    nonlocal message_count
                    message_count += 1
                    
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    progress = min(elapsed_time / (discussion_duration_minutes * 60), 1.0)
                    progress_percentage = 0.5 + (progress * 0.4)
                    progress_placeholder.progress(progress_percentage)
                    
                    time_remaining = max(0, (end_time - current_time) / 60)
                    status_placeholder.markdown(f'<div class="info-card">💬 Tartışma devam ediyor... Kalan süre: {time_remaining:.1f} dakika</div>', unsafe_allow_html=True)
                    
                    if current_time >= end_time:
                        simulator.stop_simulation()
                        return
                    
                    if SIMULATION_STATE['stop_requested']:
                        simulator.stop_simulation()
                        return
                        
                    await asyncio.sleep(0.5)
                
                await simulator.start_simulation(max_rounds=10, on_new_message=on_new_message)
            
            loop.run_until_complete(run_discussion())
            
            if SIMULATION_STATE['stop_requested']:
                status_placeholder.markdown('<div class="info-card">⏹️ Simülasyon kullanıcı tarafından durduruldu</div>', unsafe_allow_html=True)
            else:
                status_placeholder.markdown('<div class="success-card">✅ Simülasyon başarıyla tamamlandı!</div>', unsafe_allow_html=True)
            
            progress_placeholder.progress(1.0)
            
        except Exception as e:
            status_placeholder.markdown(f'<div class="error-card">❌ Tartışma hatası: {str(e)}</div>', unsafe_allow_html=True)
            logger.error(f"Discussion error: {e}")
        
        if simulator.discussion_log:
            st.info(f"💬 Simülasyon tamamlandı. {len(simulator.discussion_log)} mesaj oluşturuldu.")
        
        SIMULATION_STATE['running'] = False
        st.rerun()
        
    except Exception as e:
        SIMULATION_STATE['running'] = False
        st.error(f"Simülasyon genel hatası: {str(e)}")
        logger.error(f"General simulation error: {e}")
        
    finally:
        try:
            loop.close()
        except:
            pass

def stop_simulation():
    """Stop the running simulation"""
    try:
        SIMULATION_STATE['stop_requested'] = True
        simulator.stop_simulation()
        SIMULATION_STATE['running'] = False
        st.warning("⏹️ Simülasyon durduruldu")
        st.rerun()
    except Exception as e:
        st.error(f"Simülasyon durdurulurken hata: {str(e)}")

def reset_simulation():
    """Reset simulation state"""
    simulator.stop_simulation()
    
    SIMULATION_STATE['running'] = False
    SIMULATION_STATE['stop_requested'] = False
    
    st.session_state.analysis_result = ""
    st.session_state.expert_analysis_result = ""
    st.session_state.agenda_loaded = False
    
    simulator.discussion_log = []
    simulator.mcp_logs = []
    simulator.agenda_items = []
    simulator.memory = {}
    
    st.success("🔄 Simülasyon sıfırlandı!")
    st.rerun()

def display_simulation_status():
    """Display simulation status"""
    if SIMULATION_STATE['running'] or simulator.discussion_log:
        st.markdown("### 📊 Simülasyon Durumu")
        
        if SIMULATION_STATE['running']:
            st.markdown('<div class="info-card">🔄 Simülasyon çalışıyor...</div>', unsafe_allow_html=True)
        elif simulator.discussion_log:
            st.markdown('<div class="success-card">✅ Simülasyon tamamlandı</div>', unsafe_allow_html=True)
        
        if simulator.agenda_items and any(item.persona_scores for item in simulator.agenda_items):
            display_agenda_scores()

def display_agenda_scores():
    """Display agenda scores and memory summaries"""
    st.markdown("#### 📊 Gündem Puanları")
    
    for agenda_item in simulator.agenda_items:
        if not agenda_item.persona_scores:
            continue
            
        with st.expander(f"📝 {agenda_item.title}"):
            st.markdown("**🎯 İlgi Puanları:**")
            
            score_cols = st.columns(min(len(simulator.personas), 4))
            
            for i, persona in enumerate(simulator.personas):
                with score_cols[i % len(score_cols)]:
                    score = agenda_item.persona_scores.get(persona.name, "Hesaplanıyor...")
                    
                    if isinstance(score, (int, float)):
                        if score >= 7:
                            color = "#10b981"
                            icon = "🔥"
                        elif score >= 4:
                            color = "#f59e0b" 
                            icon = "⚡"
                        else:
                            color = "#ef4444"
                            icon = "💤"
                        
                        st.markdown(f"""
                        <div style="
                            background: rgba(30, 41, 59, 0.8);
                            border: 2px solid {color};
                            text-align: center;
                            padding: 1rem;
                            border-radius: 12px;
                            margin: 0.5rem 0;
                        ">
                            <div style='font-weight: bold; color: #e2e8f0; margin-bottom: 0.5rem;'>
                                {persona.name}
                            </div>
                            <div style='font-size: 1.5rem; margin: 0.3rem 0;'>
                                {icon}
                            </div>
                            <div style='font-size: 1.4rem; font-weight: bold; color: {color};'>
                                {score}/10
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.metric(persona.name, score)
            
            st.markdown("**🧠 Persona Belleklerinde Kalanlar:**")
            
            for persona in simulator.personas:
                memory = agenda_item.persona_memories.get(persona.name)
                if memory:
                    st.markdown(f"**{persona.name}:** {memory[:200]}{'...' if len(memory) > 200 else ''}")

def display_analysis_tab():
    """Display analysis tab with both basic and expert analysis"""
    st.markdown("### 📊 Tartışma Analizi")
    
    if not simulator.discussion_log:
        st.markdown('<div class="info-card">ℹ️ Analiz için önce bir simülasyon çalıştırın</div>', unsafe_allow_html=True)
        return
    
    analysis_col1, analysis_col2 = st.columns(2)
    
    with analysis_col1:
        if st.button("📊 Temel Analiz", key="basic_analysis"):
            generate_basic_analysis()
    
    with analysis_col2:
        if st.button("🔬 Uzman Araştırmacı Analizi", key="expert_analysis"):
            generate_expert_analysis()
    
    if st.session_state.get('analysis_result'):
        st.markdown("#### 📋 Temel Analiz Sonucu")
        with st.expander("Analiz Detayları", expanded=False):
            st.markdown(st.session_state['analysis_result'])
    
    if st.session_state.get('expert_analysis_result'):
        st.markdown("#### 🔬 Uzman Araştırmacı Analizi")
        with st.expander("Detaylı Araştırma Raporu", expanded=False):
            st.markdown(st.session_state['expert_analysis_result'])

def generate_basic_analysis():
    """Generate basic analysis"""
    with st.spinner("📊 Temel analiz oluşturuluyor..."):
        try:
            full_discussion = ""
            for entry in simulator.discussion_log:
                timestamp = entry['timestamp'].strftime("%H:%M:%S")
                speaker = entry['speaker']
                message = clean_html_and_format_text(entry['message'])
                full_discussion += f"[{timestamp}] {speaker}: {message}\n"
            
            persona_info = ""
            if simulator.personas:
                for persona in simulator.personas:
                    persona_info += f"- {persona.name}: {persona.role}, {persona.personality}\n"
            
            agenda_info = ""
            if simulator.agenda_items:
                for i, item in enumerate(simulator.agenda_items, 1):
                    agenda_info += f"{i}. {item.title}\n"
            
            analysis_prompt = f"""[SİSTEM MESAJI]
Sen bir "Sosyal Araştırmacı"sın. Sana bir odak grup tartışmasının transkripti verilecek. Temel bir analiz raporu hazırla.

[KATILIMCILAR]
{persona_info}

[TARTIŞILAN KONULAR]
{agenda_info}

[TARTIŞMA TRANSKRİPTİ]
{full_discussion}

[TEMEL ANALİZ TALİMATLARI]
Aşağıdaki başlıkları kullanarak temel bir analiz raporu hazırla:

**1. GENEL DEĞERLENDİRME**
- Tartışmanın genel atmosferi
- Katılım düzeyi

**2. ANA GÖRÜŞLER**
- Ortaya çıkan temel görüşler
- Uzlaşma ve ayrışma noktaları

**3. KATILIMCI DAVRANIŞLARI**
- Her katılımcının genel tutumu
- Etkileşim şekilleri

**4. ÖZET**
- Ana çıkarımlar
- Önemli bulgular

Raporunu anlaşılır ve özet bir dille yaz.
"""
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(simulator.llm_client.call_llm(analysis_prompt))
            st.session_state['analysis_result'] = analysis
            st.success("✅ Temel analiz tamamlandı!")
            st.rerun()
        except Exception as e:
            st.error(f"Analiz oluşturma hatası: {str(e)}")
        finally:
            try:
                loop.close()
            except:
                pass

def generate_expert_analysis():
    """Generate expert analysis"""
    with st.spinner("🔬 Uzman araştırmacı analiz ediyor..."):
        try:
            full_discussion = ""
            for entry in simulator.discussion_log:
                timestamp = entry['timestamp'].strftime("%H:%M:%S")
                speaker = entry['speaker']
                message = clean_html_and_format_text(entry['message'])
                full_discussion += f"[{timestamp}] {speaker}: {message}\n"
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            comprehensive_analysis = loop.run_until_complete(simulator.generate_analysis())
            
            st.session_state.expert_analysis_result = comprehensive_analysis
            st.success("✅ Uzman araştırmacı analizi tamamlandı!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Araştırma analizi oluşturma hatası: {str(e)}")
        finally:
            try:
                loop.close()
            except:
                pass

def display_report_tab():
    """Display report tab content"""
    st.markdown("### 📄 Rapor ve Dışa Aktarma")
    
    if not simulator.discussion_log:
        st.markdown('<div class="info-card">ℹ️ Rapor oluşturmak için önce bir simülasyon çalıştırın</div>', unsafe_allow_html=True)
        return
    
    def create_complete_pdf(conversation: List[Dict], analysis: str, personas: List) -> FPDF:
        """Create complete PDF with all conversation data"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.set_font('Helvetica', 'B', 16)
        
        pdf.cell(0, 15, 'Odak Grup Simulasyonu - Tam Rapor', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(10)
        
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 8, f'Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f'Toplam Mesaj Sayisi: {len(conversation)}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        if personas:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, 'Katilimcilar:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font('Helvetica', '', 10)
            for persona in personas:
                name = clean_text_for_pdf(persona.name)
                role = clean_text_for_pdf(persona.role)
                pdf.cell(0, 6, f'  * {name} ({role})', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
        
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'TAM TARTISMA GECMISI:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        for entry_num, entry in enumerate(conversation, 1):
            timestamp = format_message_time(entry['timestamp'])
            speaker = clean_text_for_pdf(entry['speaker'])
            message = clean_text_for_pdf(clean_html_and_format_text(str(entry['message'])))
            
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, f"[{entry_num}] {speaker} - {timestamp}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.set_font('Helvetica', '', 9)
            try:
                max_chars_per_line = 90
                if len(message) > max_chars_per_line:
                    words = message.split()
                    lines = []
                    current_line = ""
                    
                    for word in words:
                        if len(current_line + " " + word) <= max_chars_per_line:
                            current_line += " " + word if current_line else word
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word
                    
                    if current_line:
                        lines.append(current_line)
                    
                    for line in lines:
                        if line.strip():
                            pdf.cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                else:
                    pdf.cell(0, 5, message, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            except Exception as e:
                pdf.cell(0, 5, f"Mesaj görüntülenemiyor: {str(e)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.ln(3)
        
        if analysis:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, 'DETAYLI ANALIZ RAPORU:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            
            analysis_clean = clean_text_for_pdf(clean_html_and_format_text(analysis))
            
            pdf.set_font('Helvetica', '', 9)
            max_chars_per_line = 90
            
            words = analysis_clean.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line + " " + word) <= max_chars_per_line:
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            for line in lines:
                if line.strip():
                    try:
                        pdf.cell(0, 4, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    except:
                        continue
        
        return pdf
    
    def clean_text_for_pdf(text):
        """Clean text for PDF compatibility"""
        if not text:
            return ""
        
        text = str(text)
        
        char_map = {
            'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U',
            'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I',
            'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
        }
        
        for tr_char, en_char in char_map.items():
            text = text.replace(tr_char, en_char)
        
        text = ''.join(char for char in text if ord(char) < 128 or char in '.,!?;:()[]{}')
        
        return text
    
    st.markdown("#### 📥 İndirme Seçenekleri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button('📄 Tam PDF Raporu Oluştur', key="generate_complete_pdf"):
            try:
                with st.spinner("Tam PDF raporu oluşturuluyor..."):
                    analysis_text = st.session_state.get('expert_analysis_result', '') or st.session_state.get('analysis_result', '')
                    pdf = create_complete_pdf(simulator.discussion_log, analysis_text, simulator.personas)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
                        pdf.output(tmpfile.name)
                        
                        with open(tmpfile.name, 'rb') as f:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f'odak_grup_tam_rapor_{timestamp}.pdf'
                            
                            st.download_button(
                                label="📥 Tam PDF İndir",
                                data=f.read(),
                                file_name=filename,
                                mime='application/pdf',
                                key="download_complete_pdf"
                            )
                    
                    st.success("✅ Tam PDF raporu hazır!")
                    
            except Exception as e:
                st.error(f"PDF oluşturma hatası: {str(e)}")
    
    with col2:
        if st.button('📊 JSON Export', key="export_json"):
            try:
                export_data = {
                    "simulation_info": {
                        "date": datetime.now().isoformat(),
                        "total_messages": len(simulator.discussion_log),
                        "participants": [{"name": p.name, "role": p.role, "personality": p.personality} for p in simulator.personas]
                    },
                    "agenda_items": [
                        {
                            "title": item.title,
                            "content": item.content,
                            "scores": item.persona_scores,
                            "memories": item.persona_memories
                        } for item in simulator.agenda_items
                    ],
                    "conversation": [
                        {
                            "timestamp": entry['timestamp'].isoformat(),
                            "speaker": entry['speaker'],
                            "message": clean_html_and_format_text(entry['message'])
                        } for entry in simulator.discussion_log
                    ],
                    "analysis": {
                        "basic": st.session_state.get('analysis_result', ''),
                        "expert": st.session_state.get('expert_analysis_result', '')
                    }
                }
                
                json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'odak_grup_data_{timestamp}.json'
                
                st.download_button(
                    label="📥 JSON İndir",
                    data=json_str.encode('utf-8'),
                    file_name=filename,
                    mime='application/json',
                    key="download_json"
                )
                
                st.success("✅ JSON export hazır!")
                
            except Exception as e:
                st.error(f"JSON export hatası: {str(e)}")
    
    if simulator.discussion_log:
        st.markdown("#### 📊 Konuşma İstatistikleri")
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            st.metric("💬 Toplam Mesaj", len(simulator.discussion_log))
        
        with stats_col2:
            persona_msgs = len([m for m in simulator.discussion_log if m['speaker'] != 'Moderatör'])
            st.metric("👥 Persona Mesajları", persona_msgs)
        
        with stats_col3:
            moderator_msgs = len([m for m in simulator.discussion_log if m['speaker'] == 'Moderatör'])
            st.metric("🎤 Moderatör Mesajları", moderator_msgs)
        
        with stats_col4:
            if simulator.discussion_log:
                start_time = simulator.discussion_log[0]['timestamp']
                end_time = simulator.discussion_log[-1]['timestamp']
                duration = end_time - start_time
                st.metric("⏱️ Süre", f"{duration.seconds//60}:{duration.seconds%60:02d}")

def main():
    initialize_session_state()
    load_css()
    
    st.markdown('<h1 class="main-header">🎯 Odak Grup Persona Makinası</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📋 Kontrol Paneli")
        
        st.markdown("### 👥 Personalar")
        if simulator.personas:
            for persona in simulator.personas:
                with st.expander(f"{persona.name}"):
                    pic_path = get_persona_pic(persona.name)
                    if pic_path:
                        st.image(pic_path, width=100)
                    st.write(f"**Rol:** {persona.role}")
                    st.write(f"**Kişilik:** {persona.personality}")
                    st.write("**Bio:**")
                    for bio_item in persona.bio[:3]:
                        st.write(f"• {bio_item}")
        else:
            st.warning("Henüz persona yüklenmemiş")
        
        st.markdown("### 📊 API Durumu")
        if hasattr(simulator, 'llm_client'):
            stats = simulator.llm_client.get_request_stats()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Toplam İstek", stats['total_requests'])
                st.metric("Başarı Oranı", f"{stats['success_rate']:.1f}%")
            with col2:
                st.metric("Başarılı", stats['successful_requests'])
                st.metric("Başarısız", stats['failed_requests'])
    
    # Main content tabs
    # Main content tabs - Chat görünümü için güncelleme
    main_tabs = st.tabs(["🚀 Simülasyon", "💬 Chat Görünümü", "📋 Liste Görünümü", "📊 Analiz", "📄 Rapor"])
    
    with main_tabs[0]:
        display_simulation_tab()
    
    with main_tabs[1]:
        st.markdown("### 💬 Modern Chat Görünümü")
        
        # Debug modu kontrolü - session_state'i ÖNCE initialize et
        if 'debug_mode' not in st.session_state:
            st.session_state['debug_mode'] = False
        
        col_debug, col_info = st.columns([1, 3])
        with col_debug:
            debug_mode = st.checkbox("🔍 Debug Mode", value=st.session_state['debug_mode'], key="debug_mode_checkbox")
            # Session state'i güncelle
            if debug_mode != st.session_state['debug_mode']:
                st.session_state['debug_mode'] = debug_mode
        
        with col_info:
            if simulator.discussion_log:
                st.info(f"📊 {len(simulator.discussion_log)} mesaj görüntüleniyor")
            else:
                st.info("💭 Tartışma henüz başlamadı")
        
        # Chat bilgi paneli
        if simulator.discussion_log:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💬 Toplam Mesaj", len(simulator.discussion_log))
            with col2:
                persona_msgs = len([m for m in simulator.discussion_log if m['speaker'] != 'Moderatör'])
                st.metric("👥 Persona Mesajları", persona_msgs)
            with col3:
                if simulator.discussion_log:
                    last_speaker = simulator.discussion_log[-1]['speaker']
                    st.metric("🎤 Son Konuşan", last_speaker)
        
        # Debug bilgileri
        if st.session_state.get('debug_mode', False):
            with st.expander("🔍 Debug Bilgileri"):
                st.markdown("**Persona Resim Durumu:**")
                for persona in simulator.personas:
                    pic_path = get_persona_pic(persona.name)
                    status = "✅ Var" if pic_path and os.path.exists(pic_path) else "❌ Yok"
                    st.text(f"{persona.name}: {status} ({pic_path})")
                
                # Moderatör resmi kontrolü
                mod_pic = get_persona_pic("Moderatör")
                mod_status = "✅ Var" if mod_pic and os.path.exists(mod_pic) else "❌ Yok"
                st.text(f"Moderatör: {mod_status} ({mod_pic})")
        
        # Chat görünümünü göster
        display_modern_chat()
        
        # Otomatik yenileme kontrolü
        if SIMULATION_STATE['running']:
            with st.spinner("💬 Yeni mesajlar bekleniyor..."):
                time.sleep(2)
                st.rerun()
        
        # Manuel yenileme butonu
        if st.button("🔄 Chat'i Yenile", key="refresh_chat"):
            st.rerun()

    with main_tabs[2]:  # Liste Görünümü
        st.markdown("### 📋 Detaylı Liste Görünümü")
        
        if not simulator.discussion_log:
            st.info("💭 Henüz tartışma başlamadı...")
        else:
            # İstatistikler
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💬 Toplam Mesaj", len(simulator.discussion_log))
            with col2:
                persona_messages = len([entry for entry in simulator.discussion_log if entry['speaker'] != 'Moderatör'])
                st.metric("👥 Persona Mesajları", persona_messages)
            with col3:
                moderator_messages = len([entry for entry in simulator.discussion_log if entry['speaker'] == 'Moderatör'])
                st.metric("🎤 Moderatör Mesajları", moderator_messages)
            with col4:
                if len(simulator.discussion_log) > 1:
                    start_time = simulator.discussion_log[0]['timestamp']
                    end_time = simulator.discussion_log[-1]['timestamp']
                    duration = end_time - start_time
                    st.metric("⏱️ Süre", f"{duration.seconds//60}:{duration.seconds%60:02d}")
                else:
                    st.metric("⏱️ Süre", "0:00")
            
            st.markdown("---")
            
            # Filtreleme seçenekleri
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                all_speakers = list(set([entry['speaker'] for entry in simulator.discussion_log]))
                speaker_filter = st.selectbox(
                    "🗣️ Konuşmacı Filtresi:",
                    ["Tümü"] + all_speakers,
                    key="speaker_filter_list"
                )
            
            with col_filter2:
                show_timestamps = st.checkbox("🕐 Zaman Damgalarını Göster", value=True, key="show_timestamps_list")
            
            # Mesajları filtrele
            filtered_messages = simulator.discussion_log
            if speaker_filter != "Tümü":
                filtered_messages = [entry for entry in simulator.discussion_log if entry['speaker'] == speaker_filter]
            
            st.markdown(f"### 📝 Mesajlar ({len(filtered_messages)} adet)")
            
            # Sayfalama için
            messages_per_page = 10
            total_pages = (len(filtered_messages) + messages_per_page - 1) // messages_per_page
            
            if total_pages > 1:
                current_page = st.number_input(
                    f"Sayfa (1-{total_pages}):", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=1, 
                    key="current_page_list"
                )
                
                start_idx = (current_page - 1) * messages_per_page
                end_idx = start_idx + messages_per_page
                page_messages = filtered_messages[start_idx:end_idx]
            else:
                page_messages = filtered_messages
                current_page = 1
            
            # Mesajları listele
            for i, entry in enumerate(page_messages, 1):
                speaker = entry['speaker']
                message = clean_html_and_format_text(entry['message'])
                timestamp = format_message_time(entry['timestamp'])
                
                if not message or len(message.strip()) == 0:
                    continue
                
                # Profil resmi al
                pic_path = get_persona_pic(speaker)
                is_moderator = speaker.lower().strip() == 'moderatör'
                
                # Global mesaj numarası
                global_idx = ((current_page - 1) * messages_per_page) + i
                
                # Mesaj container'ı
                with st.container():
                    # Header kısmı
                    col_avatar, col_content = st.columns([1, 8])
                    
                    with col_avatar:
                        if pic_path and os.path.exists(pic_path):
                            try:
                                st.image(pic_path, width=60)
                            except Exception as e:
                                avatar_emoji = "🎤" if is_moderator else "👤"
                                st.markdown(f"<div style='font-size:40px;text-align:center;'>{avatar_emoji}</div>", unsafe_allow_html=True)
                        else:
                            avatar_emoji = "🎤" if is_moderator else "👤"
                            st.markdown(f"<div style='font-size:40px;text-align:center;'>{avatar_emoji}</div>", unsafe_allow_html=True)
                    
                    with col_content:
                        # İsim ve zaman
                        header_text = f"**#{global_idx} - {speaker}**"
                        if show_timestamps:
                            header_text += f" • *{timestamp}*"
                        st.markdown(header_text)
                        
                        # Mesaj içeriği
                        if is_moderator:
                            st.info(f"🎯 {message}")
                        else:
                            st.write(f"💬 {message}")
                        
                        # Mesaj detayları
                        col_details1, col_details2 = st.columns(2)
                        with col_details1:
                            st.caption(f"📏 {len(message)} karakter")
                        with col_details2:
                            st.caption(f"📝 {len(message.split())} kelime")
                    
                    st.markdown("---")
            
            # Sayfalama gösterimi
            if total_pages > 1:
                st.info(f"📄 Sayfa {current_page} / {total_pages} • Toplam {len(filtered_messages)} mesaj")
            
            # Export seçenekleri
            st.markdown("### 📤 Dışa Aktar")
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                if st.button("📋 Kopyalanabilir Metin", key="copy_text_list"):
                    text_content = ""
                    for idx, entry in enumerate(filtered_messages, 1):
                        speaker = entry['speaker']
                        message = clean_html_and_format_text(entry['message'])
                        timestamp = format_message_time(entry['timestamp'])
                        text_content += f"[{idx}] [{timestamp}] {speaker}: {message}\n\n"
                    
                    st.text_area("📋 Kopyala:", value=text_content, height=200, key="copyable_text_list")
            
            with col_export2:
                if st.button("💾 CSV İndir", key="download_csv_list"):
                    try:
                        import io
                        import csv
                        
                        csv_buffer = io.StringIO()
                        writer = csv.writer(csv_buffer)
                        writer.writerow(["Sira", "Zaman", "Konusmaci", "Mesaj", "Karakter_Sayisi", "Kelime_Sayisi"])
                        
                        for idx, entry in enumerate(filtered_messages, 1):
                            speaker = entry['speaker']
                            message = clean_html_and_format_text(entry['message'])
                            timestamp = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                            char_count = len(message)
                            word_count = len(message.split())
                            writer.writerow([idx, timestamp, speaker, message, char_count, word_count])
                        
                        csv_data = csv_buffer.getvalue()
                        
                        st.download_button(
                            label="📥 CSV Dosyasını İndir",
                            data=csv_data.encode('utf-8'),
                            file_name=f'tartisma_listesi_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                            mime='text/csv',
                            key="download_csv_button_list"
                        )
                        
                    except Exception as e:
                        st.error(f"CSV oluşturma hatası: {str(e)}")
        
        # Otomatik yenileme
        if SIMULATION_STATE['running']:
            time.sleep(3)
            st.rerun()        

    with main_tabs[3]:  # Analiz
        st.markdown("### 📊 Tartışma Analizi")
        
        if not simulator.discussion_log:
            st.markdown('<div class="info-card">ℹ️ Analiz için önce bir simülasyon çalıştırın</div>', unsafe_allow_html=True)
        else:
            # Analiz türü seçimi
            analysis_type = st.radio(
                "📈 Analiz Türü Seçin:",
                ["📊 Temel İstatistikler", "🔬 AI Analizi", "📈 Detaylı Rapor"],
                horizontal=True,
                key="analysis_type"
            )
            
            if analysis_type == "📊 Temel İstatistikler":
                st.markdown("#### 📊 Temel İstatistikler")
                
                # İstatistik metrikleri
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_messages = len(simulator.discussion_log)
                    st.metric("💬 Toplam Mesaj", total_messages)
                
                with col2:
                    total_words = sum(len(clean_html_and_format_text(entry['message']).split()) 
                                    for entry in simulator.discussion_log)
                    st.metric("📝 Toplam Kelime", total_words)
                
                with col3:
                    avg_message_length = total_words / total_messages if total_messages > 0 else 0
                    st.metric("📏 Ortalama Uzunluk", f"{avg_message_length:.1f} kelime")
                
                with col4:
                    unique_speakers = len(set(entry['speaker'] for entry in simulator.discussion_log))
                    st.metric("👥 Konuşmacı Sayısı", unique_speakers)
                
                # Konuşmacı bazlı analiz
                st.markdown("#### 🗣️ Konuşmacı Bazlı Analiz")
                
                speaker_stats = {}
                for entry in simulator.discussion_log:
                    speaker = entry['speaker']
                    message = clean_html_and_format_text(entry['message'])
                    word_count = len(message.split())
                    
                    if speaker not in speaker_stats:
                        speaker_stats[speaker] = {'count': 0, 'words': 0, 'chars': 0}
                    
                    speaker_stats[speaker]['count'] += 1
                    speaker_stats[speaker]['words'] += word_count
                    speaker_stats[speaker]['chars'] += len(message)
                
                # Tablo olarak göster
                import pandas as pd
                # Tablo olarak göster
                try:
                    df_stats = pd.DataFrame.from_dict(speaker_stats, orient='index')
                    df_stats['avg_words'] = df_stats['words'] / df_stats['count']
                    df_stats.columns = ['Mesaj Sayısı', 'Toplam Kelime', 'Toplam Karakter', 'Ort. Kelime/Mesaj']
                    
                    st.dataframe(df_stats, use_container_width=True)
                except Exception as e:
                    st.error(f"Tablo oluşturma hatası: {str(e)}")
                    st.write("**Konuşmacı İstatistikleri:**")
                    for speaker, stats in speaker_stats.items():
                        avg_words = stats['words'] / stats['count']
                        st.write(f"- **{speaker}:** {stats['count']} mesaj, {stats['words']} kelime (ort. {avg_words:.1f} kelime/mesaj)")
                
                # Grafik gösterimi
                try:
                    import matplotlib.pyplot as plt
                    import matplotlib
                    matplotlib.use('Agg')
                    
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                    fig.patch.set_facecolor('#0f0f23')
                    
                    # Mesaj sayısı grafiği
                    speakers = list(speaker_stats.keys())
                    message_counts = [speaker_stats[s]['count'] for s in speakers]
                    
                    colors1 = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
                    ax1.bar(speakers, message_counts, color=colors1[:len(speakers)])
                    ax1.set_title('Konuşmacı Başına Mesaj Sayısı', color='white')
                    ax1.set_ylabel('Mesaj Sayısı', color='white')
                    ax1.tick_params(colors='white')
                    ax1.set_facecolor('#1a1a2e')
                    
                    # X etiketlerini döndür
                    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
                    
                    # Kelime sayısı grafiği
                    word_counts = [speaker_stats[s]['words'] for s in speakers]
                    colors2 = ['#ff9f43', '#10ac84', '#ee5a24', '#0abde3']
                    ax2.bar(speakers, word_counts, color=colors2[:len(speakers)])
                    ax2.set_title('Konuşmacı Başına Kelime Sayısı', color='white')
                    ax2.set_ylabel('Kelime Sayısı', color='white')
                    ax2.tick_params(colors='white')
                    ax2.set_facecolor('#1a1a2e')
                    
                    # X etiketlerini döndür
                    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                except ImportError:
                    st.warning("📊 Grafik gösterimi için matplotlib kütüphanesi gerekli")
                except Exception as e:
                    st.error(f"Grafik oluşturma hatası: {str(e)}")
                
            elif analysis_type == "🔬 AI Analizi":
                st.markdown("#### 🔬 AI Destekli Analiz")
                
                col_basic, col_expert = st.columns(2)
                
                with col_basic:
                    if st.button("📊 Temel AI Analizi", key="basic_ai_analysis"):
                        with st.spinner("🔄 AI analiz ediyor..."):
                            try:
                                # Temel analiz
                                full_discussion = ""
                                for entry in simulator.discussion_log:
                                    timestamp = entry['timestamp'].strftime("%H:%M:%S")
                                    speaker = entry['speaker']
                                    message = clean_html_and_format_text(entry['message'])
                                    full_discussion += f"[{timestamp}] {speaker}: {message}\n"
                                
                                analysis_prompt = f"""Sen bir sosyal araştırmacısın. Bu odak grup tartışmasını analiz et:

TARTIŞMA:
{full_discussion[:3000]}...

Şu başlıklarda kısa bir analiz yap:
1. GENEL ATMOSFER: Tartışmanın tonu nasıl?
2. ANA KONULAR: Hangi konular öne çıktı?
3. KATILIMCI DAVRANIŞI: Kimler nasıl davrandı?
4. UZLAŞMA/ÇATIŞMA: Anlaştıkları ve çatıştıkları noktalar?
5. ÖNEMLİ BULGULAR: En dikkat çekici 3 nokta?

Maksimum 500 kelime ile analiz et."""

                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                analysis = loop.run_until_complete(simulator.llm_client.call_llm(analysis_prompt))
                                
                                st.session_state['basic_analysis_result'] = analysis
                                st.success("✅ Temel analiz tamamlandı!")
                                
                            except Exception as e:
                                st.error(f"❌ Analiz hatası: {str(e)}")
                            finally:
                                try:
                                    loop.close()
                                except:
                                    pass
                
                with col_expert:
                    if st.button("🎓 Uzman Analizi", key="expert_ai_analysis"):
                        with st.spinner("🔬 Uzman araştırmacı analiz ediyor..."):
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                                comprehensive_analysis = loop.run_until_complete(simulator.generate_analysis())
                                st.session_state['expert_analysis_result'] = comprehensive_analysis
                                st.success("✅ Uzman analizi tamamlandı!")
                                
                            except Exception as e:
                                st.error(f"❌ Uzman analiz hatası: {str(e)}")
                            finally:
                                try:
                                    loop.close()
                                except:
                                    pass
                
                # Analiz sonuçlarını göster
                if st.session_state.get('basic_analysis_result'):
                    st.markdown("#### 📋 Temel Analiz Sonucu")
                    st.markdown(st.session_state['basic_analysis_result'])
                
                if st.session_state.get('expert_analysis_result'):
                    st.markdown("#### 🎓 Uzman Analiz Sonucu")
                    with st.expander("Detaylı Uzman Raporu", expanded=False):
                        st.markdown(st.session_state['expert_analysis_result'])
            
            elif analysis_type == "📈 Detaylı Rapor":
                st.markdown("#### 📈 Detaylı Analiz Raporu")
                
                # Zaman bazlı analiz
                st.markdown("##### ⏱️ Zaman Bazlı Analiz")
                
                if len(simulator.discussion_log) > 1:
                    time_analysis = []
                    for i, entry in enumerate(simulator.discussion_log):
                        time_analysis.append({
                            'Mesaj No': i+1,
                            'Zaman': entry['timestamp'].strftime("%H:%M:%S"),
                            'Konuşmacı': entry['speaker'],
                            'Kelime Sayısı': len(clean_html_and_format_text(entry['message']).split()),
                            'Karakter Sayısı': len(clean_html_and_format_text(entry['message']))
                        })
                    
                    df_time = pd.DataFrame(time_analysis)
                    st.dataframe(df_time, use_container_width=True)
                
                # Konu analizi
                st.markdown("##### 🎯 Gündem Maddeleri Analizi")
                
                if simulator.agenda_items:
                    for i, item in enumerate(simulator.agenda_items, 1):
                        with st.expander(f"📋 Gündem {i}: {item.title}"):
                            st.write(f"**İçerik:** {item.content[:200]}...")
                            
                            if hasattr(item, 'persona_scores') and item.persona_scores:
                                st.write("**Persona İlgi Puanları:**")
                                for persona_name, score in item.persona_scores.items():
                                    st.write(f"• {persona_name}: {score}/10")
                            
                            if hasattr(item, 'persona_memories') and item.persona_memories:
                                st.write("**Persona Belleklerindeki Özetler:**")
                                for persona_name, memory in item.persona_memories.items():
                                    st.write(f"• **{persona_name}:** {memory[:150]}...")
                
                # Etkileşim analizi
                st.markdown("##### 🔄 Etkileşim Analizi")
                
                interaction_data = {}
                previous_speaker = None
                
                for entry in simulator.discussion_log:
                    current_speaker = entry['speaker']
                    if previous_speaker and previous_speaker != current_speaker:
                        pair = f"{previous_speaker} → {current_speaker}"
                        interaction_data[pair] = interaction_data.get(pair, 0) + 1
                    previous_speaker = current_speaker
                
                if interaction_data:
                    st.write("**En Sık Etkileşimler:**")
                    sorted_interactions = sorted(interaction_data.items(), key=lambda x: x[1], reverse=True)
                    for pair, count in sorted_interactions[:10]:
                        st.write(f"• {pair}: {count} kez")
        
        # Session state'e analiz sonuçlarını initialize et
        if 'basic_analysis_result' not in st.session_state:
            st.session_state['basic_analysis_result'] = ""
        if 'expert_analysis_result' not in st.session_state:
            st.session_state['expert_analysis_result'] = ""
    
    with main_tabs[4]:  # Rapor
        st.markdown("### 📄 Rapor ve Dışa Aktarma")
        
        if not simulator.discussion_log:
            st.markdown('<div class="info-card">ℹ️ Rapor oluşturmak için önce bir simülasyon çalıştırın</div>', unsafe_allow_html=True)
        else:
            # Rapor türü seçimi
            report_type = st.radio(
                "📋 Rapor Türü:",
                ["📊 Özet Rapor", "📄 Tam Rapor", "🔢 İstatistik Raporu"],
                horizontal=True,
                key="report_type"
            )
            
            # Rapor seçenekleri
            col_options1, col_options2 = st.columns(2)
            
            with col_options1:
                include_timestamps = st.checkbox("🕐 Zaman Damgaları Dahil Et", value=True, key="include_timestamps")
                include_analysis = st.checkbox("📊 Analiz Sonuçları Dahil Et", value=True, key="include_analysis")
            
            with col_options2:
                include_statistics = st.checkbox("📈 İstatistikler Dahil Et", value=True, key="include_statistics")
                include_agenda_scores = st.checkbox("🎯 Gündem Puanları Dahil Et", value=True, key="include_agenda_scores")
            
            st.markdown("---")
            
            # Rapor önizlemesi
            st.markdown("#### 👁️ Rapor Önizlemesi")
            
            # Rapor içeriğini oluştur
            report_content = f"""# 🎯 Odak Grup Simülasyonu Raporu

## 📅 Genel Bilgiler
- **Tarih:** {datetime.now().strftime("%d.%m.%Y %H:%M")}
- **Toplam Mesaj:** {len(simulator.discussion_log)}
- **Katılımcılar:** {len(simulator.personas)} kişi
- **Süre:** """
            
            if simulator.discussion_log:
                start_time = simulator.discussion_log[0]['timestamp']
                end_time = simulator.discussion_log[-1]['timestamp']
                duration = end_time - start_time
                report_content += f"{duration.seconds//60}:{duration.seconds%60:02d}\n\n"
            
            # Katılımcı bilgileri
            report_content += "## 👥 Katılımcılar\n"
            for persona in simulator.personas:
                report_content += f"- **{persona.name}:** {persona.role} - {persona.personality}\n"
            report_content += "\n"
            
            # Gündem maddeleri
            if simulator.agenda_items:
                report_content += "## 📋 Gündem Maddeleri\n"
                for i, item in enumerate(simulator.agenda_items, 1):
                    report_content += f"{i}. **{item.title}**\n"
                    report_content += f"   {item.content[:200]}...\n\n"
                    
                    if include_agenda_scores and hasattr(item, 'persona_scores') and item.persona_scores:
                        report_content += "   **İlgi Puanları:**\n"
                        for persona_name, score in item.persona_scores.items():
                            report_content += f"   - {persona_name}: {score}/10\n"
                        report_content += "\n"
            
            # İstatistikler
            if include_statistics:
                report_content += "## 📊 İstatistikler\n"
                
                speaker_stats = {}
                total_words = 0
                
                for entry in simulator.discussion_log:
                    speaker = entry['speaker']
                    message = clean_html_and_format_text(entry['message'])
                    word_count = len(message.split())
                    total_words += word_count
                    
                    if speaker not in speaker_stats:
                        speaker_stats[speaker] = {'count': 0, 'words': 0}
                    
                    speaker_stats[speaker]['count'] += 1
                    speaker_stats[speaker]['words'] += word_count
                
                report_content += f"- **Toplam Kelime:** {total_words}\n"
                report_content += f"- **Ortalama Mesaj Uzunluğu:** {total_words/len(simulator.discussion_log):.1f} kelime\n\n"
                
                report_content += "### 🗣️ Konuşmacı Bazlı İstatistikler\n"
                for speaker, stats in speaker_stats.items():
                    avg_words = stats['words'] / stats['count']
                    report_content += f"- **{speaker}:** {stats['count']} mesaj, {stats['words']} kelime (ort. {avg_words:.1f} kelime/mesaj)\n"
                report_content += "\n"
            
            # Tartışma içeriği
            if report_type == "📄 Tam Rapor":
                report_content += "## 💬 Tam Tartışma Geçmişi\n\n"
                for i, entry in enumerate(simulator.discussion_log, 1):
                    speaker = entry['speaker']
                    message = clean_html_and_format_text(entry['message'])
                    timestamp = format_message_time(entry['timestamp'])
                    
                    if include_timestamps:
                        report_content += f"**[{i}] {speaker} - {timestamp}**\n"
                    else:
                        report_content += f"**[{i}] {speaker}**\n"
                    
                    report_content += f"{message}\n\n"
            
            elif report_type == "📊 Özet Rapor":
                report_content += "## 📝 Özet\n"
                report_content += "Bu rapor, odak grup simülasyonunun temel bulgularını içermektedir.\n\n"
                
                # Son 5 mesajı göster
                report_content += "### 🔚 Son Mesajlar\n"
                for entry in simulator.discussion_log[-5:]:
                    speaker = entry['speaker']
                    message = clean_html_and_format_text(entry['message'])[:100] + "..."
                    report_content += f"- **{speaker}:** {message}\n"
                report_content += "\n"
            
            # Analiz sonuçları
            if include_analysis:
                basic_analysis = st.session_state.get('basic_analysis_result', '')
                expert_analysis = st.session_state.get('expert_analysis_result', '')
                
                if basic_analysis:
                    report_content += "## 📊 Temel Analiz\n"
                    report_content += basic_analysis + "\n\n"
                
                if expert_analysis:
                    report_content += "## 🎓 Uzman Analizi\n"
                    report_content += expert_analysis + "\n\n"
            
            # Önizleme göster
            with st.expander("👁️ Rapor İçeriği Önizlemesi", expanded=False):
                st.markdown(report_content[:2000] + "\n\n*... (devamı download'da)*")
            
            st.markdown("---")
            
            # İndirme seçenekleri
            st.markdown("### 📥 İndirme Seçenekleri")
            
            col_download1, col_download2, col_download3 = st.columns(3)
            
            with col_download1:
                # Markdown dosyası
                if st.button("📝 Markdown İndir", key="download_md"):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f'odak_grup_raporu_{timestamp}.md'
                    
                    st.download_button(
                        label="📥 MD Dosyasını İndir",
                        data=report_content.encode('utf-8'),
                        file_name=filename,
                        mime='text/markdown',
                        key="download_md_button"
                    )
            
            with col_download2:
                # TXT dosyası
                if st.button("📄 TXT İndir", key="download_txt"):
                    # Markdown işaretlerini temizle
                    import re
                    clean_content = re.sub(r'[#*_`]', '', report_content)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f'odak_grup_raporu_{timestamp}.txt'
                    
                    st.download_button(
                        label="📥 TXT Dosyasını İndir",
                        data=clean_content.encode('utf-8'),
                        file_name=filename,
                        mime='text/plain',
                        key="download_txt_button"
                    )
            
            with col_download3:
                # JSON export
                if st.button("🔢 JSON İndir", key="download_json"):
                    export_data = {
                        "simulation_info": {
                            "date": datetime.now().isoformat(),
                            "total_messages": len(simulator.discussion_log),
                            "participants": [
                                {
                                    "name": p.name, 
                                    "role": p.role, 
                                    "personality": p.personality
                                } for p in simulator.personas
                            ]
                        },
                        "agenda_items": [
                            {
                                "title": item.title,
                                "content": item.content,
                                "scores": getattr(item, 'persona_scores', {}),
                                "memories": getattr(item, 'persona_memories', {})
                            } for item in simulator.agenda_items
                        ],
                        "conversation": [
                            {
                                "timestamp": entry['timestamp'].isoformat(),
                                "speaker": entry['speaker'],
                                "message": clean_html_and_format_text(entry['message'])
                            } for entry in simulator.discussion_log
                        ],
                        "analysis": {
                            "basic": st.session_state.get('basic_analysis_result', ''),
                            "expert": st.session_state.get('expert_analysis_result', '')
                        },
                        "statistics": speaker_stats if 'speaker_stats' in locals() else {}
                    }
                    
                    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")    

if __name__ == "__main__":
    main()