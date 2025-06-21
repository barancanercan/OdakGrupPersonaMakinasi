import os
import re
import json
import asyncio
import pandas as pd
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
    """Modern CSS stilleri yükle"""
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
    
    .chat-container {
        background: rgba(15, 23, 42, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        height: 600px;
        overflow-y: auto;
        border: 1px solid rgba(100, 116, 139, 0.3);
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
    }
    
    .chat-message {
        display: flex;
        align-items: flex-start;
        margin: 1.5rem 0;
        animation: messageSlideIn 0.5s ease-out;
    }
    
    .chat-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        margin-right: 1rem;
        border: 2px solid #6366f1;
        object-fit: cover;
    }
    
    .chat-bubble {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 18px;
        padding: 1rem 1.5rem;
        max-width: 70%;
    }
    
    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .chat-speaker {
        font-weight: 600;
        color: #f1f5f9;
    }
    
    .chat-time {
        font-size: 0.75rem;
        color: #94a3b8;
        background: rgba(100, 116, 139, 0.2);
        padding: 0.2rem 0.6rem;
        border-radius: 10px;
    }
    
    .chat-content {
        color: #e2e8f0;
        line-height: 1.6;
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
    
    @keyframes messageSlideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
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

def get_persona_pic(persona_name: str) -> Optional[str]:
    """Get persona profile picture path"""
    if persona_name.strip().lower() in ["moderatör", "moderator"]:
        mod_path = Path('personas_pp/moderator.png')
        if mod_path.exists():
            return str(mod_path)
        return None
    
    pp_dir = Path('personas_pp')
    if not pp_dir.exists():
        return None
    
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', persona_name.lower().replace(' ', '_'))
    
    # Specific mappings
    file_mappings = {
        'elif': 'elif.jpg',
        'hatice_teyze': 'hatice_teyze.jpg',
        'kenan_bey': 'kenan_bey.jpg',
        'tugrul_bey': 'tugrul_bey.jpg'
    }
    
    if safe_name in file_mappings:
        pic_path = pp_dir / file_mappings[safe_name]
        if pic_path.exists():
            return str(pic_path)
    
    # Fallback
    for ext in ['.jpg', '.png', '.jpeg']:
        pic_path = pp_dir / f"{safe_name}{ext}"
        if pic_path.exists():
            return str(pic_path)
    
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
    """Clean HTML tags and format text properly"""
    if not text:
        return ""
    
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = ' '.join(text.split())
    text = text.strip()
    
    return text

def display_modern_chat():
    """Display modern chat interface"""
    if not simulator.discussion_log:
        st.markdown('<div class="info-card">💬 Henüz tartışma başlamadı...</div>', unsafe_allow_html=True)
        return
    
    chat_html = '<div class="chat-container">'
    
    for entry in simulator.discussion_log:
        timestamp = format_message_time(entry['timestamp'])
        speaker = entry['speaker']
        message = clean_html_and_format_text(entry['message'])
        
        if not message or message == '0':
            continue
        
        is_moderator = speaker == 'Moderatör'
        pic_path = get_persona_pic(speaker)
        
        # Prepare avatar
        avatar_html = ""
        if pic_path:
            try:
                base64_img = get_base64_from_file(pic_path)
                avatar_html = f'<img src="data:image/jpeg;base64,{base64_img}" class="chat-avatar" alt="{speaker}">'
            except:
                avatar_html = f'<div class="chat-avatar" style="background: {"#ec4899" if is_moderator else "#6366f1"}; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">{speaker[0]}</div>'
        else:
            avatar_html = f'<div class="chat-avatar" style="background: {"#ec4899" if is_moderator else "#6366f1"}; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">{speaker[0]}</div>'
        
        # Create message HTML
        chat_html += f"""
        <div class="chat-message">
            {avatar_html}
            <div class="chat-bubble">
                <div class="chat-header">
                    <span class="chat-speaker">{speaker}</span>
                    <span class="chat-time">{timestamp}</span>
                </div>
                <div class="chat-content">{html.escape(message)}</div>
            </div>
        </div>
        """
    
    chat_html += """
    </div>
    <script>
        setTimeout(function() {
            var chatContainer = document.querySelector('.chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }, 100);
    </script>
    """
    
    st.markdown(chat_html, unsafe_allow_html=True)

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
        discussion_duration = st.slider(
            "🕒 Tartışma Süresi (dakika)", 
            min_value=5, 
            max_value=60, 
            value=15,
            step=5,
            help="Tartışmanın ne kadar süreceğini belirleyin (5-60 dakika arası)"
        )
        st.session_state['discussion_duration'] = discussion_duration
        st.info(f"Seçilen süre: {discussion_duration} dakika (~{discussion_duration//5} tur tartışma)")
    
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
    main_tabs = st.tabs(["🚀 Simülasyon", "💬 Chat Görünümü", "📋 Liste Görünümü", "📊 Analiz", "📄 Rapor"])
    
    with main_tabs[0]:
        display_simulation_tab()
    
    with main_tabs[1]:
        st.markdown("### 💬 Modern Chat Görünümü")
        display_modern_chat()
        if SIMULATION_STATE['running']:
            time.sleep(2)
            st.rerun()
    
    with main_tabs[2]:
        st.markdown("### 📋 Detaylı Liste Görünümü")
        display_conversation_list()
        if SIMULATION_STATE['running']:
            time.sleep(3)
            st.rerun()
    
    with main_tabs[3]:
        display_analysis_tab()
    
    with main_tabs[4]:
        display_report_tab()

if __name__ == "__main__":
    main()