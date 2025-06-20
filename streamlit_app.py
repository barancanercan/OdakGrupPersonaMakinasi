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

# Import your main simulation components
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

# Modern CSS stilleri
def load_css():
    """Modern CSS stilleri yükle"""
    css_content = """
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global App Styling */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif !important;
        min-height: 100vh;
    }
    
    /* Main container styling */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1200px;
    }
    
    /* Header and text styling */
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
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    p, div, span, label {
        color: #cbd5e1 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3) !important;
        width: 100% !important;
        height: 3rem !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(99, 102, 241, 0.4) !important;
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%) !important;
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #374151 0%, #4b5563 100%) !important;
        color: #6b7280 !important;
        border-color: #374151 !important;
        transform: none !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }
    
    /* File uploader styling */
    .stFileUploader {
        border: 2px dashed #6366f1 !important;
        border-radius: 15px !important;
        padding: 2rem !important;
        background: rgba(51, 65, 85, 0.5) !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader:hover {
        border-color: #8b5cf6 !important;
        background: rgba(139, 92, 246, 0.1) !important;
    }
    
    /* Status cards */
    .status-card {
        background: rgba(30, 41, 59, 0.8) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        border: 1px solid rgba(100, 116, 139, 0.2) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(15px) !important;
    }
    
    .success-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #f0fdf4 !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.2) !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }
    
    .error-card {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: #fef2f2 !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 20px rgba(239, 68, 68, 0.2) !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }
    
    .info-card {
        background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%) !important;
        color: #f0f9ff !important;
        border: 1px solid rgba(14, 165, 233, 0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 20px rgba(14, 165, 233, 0.2) !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }
    
    /* Chat styling */
    .chat-container {
        background: rgba(15, 23, 42, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        max-height: 600px;
        overflow-y: auto;
        border: 1px solid rgba(100, 116, 139, 0.3);
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
        width: 100%;
        box-sizing: border-box;
    }
    
    .message-bubble {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #6366f1;
        color: #e2e8f0;
    }
    
    .moderator-bubble {
        border-left-color: #ec4899;
        background: rgba(236, 72, 153, 0.1);
    }
    
    /* Streamlit-specific components */
    .stSuccess {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #f0fdf4 !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: #fef2f2 !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%) !important;
        color: #f0f9ff !important;
        border: 1px solid rgba(14, 165, 233, 0.3) !important;
        border-radius: 12px !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(99, 102, 241, 0.3);
        border-top: 3px solid #6366f1;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
        }
        
        .status-card {
            padding: 1rem !important;
        }
    }
    """
    
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

# CSS'i yükle
load_css()

# Initialize session state
def initialize_session_state():
    """Initialize session state variables"""
    if 'simulation_running' not in st.session_state:
        st.session_state.simulation_running = False
    if 'stop_simulation' not in st.session_state:
        st.session_state.stop_simulation = False
    if 'simulation_data' not in st.session_state:
        st.session_state.simulation_data = {}
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = ""
    if 'agenda_loaded' not in st.session_state:
        st.session_state.agenda_loaded = False
    if 'expert_analysis_result' not in st.session_state:
        st.session_state.expert_analysis_result = ""
    if 'discussion_duration' not in st.session_state:
        st.session_state.discussion_duration = 15

# Helper functions
def get_persona_pic(persona_name: str) -> Optional[str]:
    """Get persona profile picture path"""
    if persona_name.strip().lower() in ["moderatör", "moderator"]:
        mod_path = Path('personas_pp/moderator.png')
        if mod_path.exists():
            return str(mod_path)
        else:
            return None
    pp_dir = Path('personas_pp')
    if not pp_dir.exists():
        return None
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', persona_name.lower().replace(' ', '_'))
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
    # HTML etiketlerini temizle
    text = re.sub(r'<[^>]+>', '', text)
    # HTML entitilerini çöz
    text = html.unescape(text)
    # Fazla boşlukları temizle
    text = ' '.join(text.split())
    text = text.strip()
    
    return text

# Main app
def main():
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎯 Odak Grup Persona Makinası</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📋 Kontrol Paneli")
        
        # Persona bilgileri
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
        
        # API İstatistikleri
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
    main_tabs = st.tabs(["🚀 Simülasyon", "📊 Analiz", "📄 Rapor"])
    
    with main_tabs[0]:
        display_simulation_tab()
    
    with main_tabs[1]:
        display_analysis_tab()
    
    with main_tabs[2]:
        display_report_tab()

def display_simulation_tab():
    """Display simulation tab content"""
    # File upload section
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
            # Save file
            os.makedirs('data', exist_ok=True)
            file_path = f"data/{uploaded_file.name}"
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            # Load and validate data
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            is_valid, message = validate_agenda_file(df)
            
            if is_valid:
                if simulator.load_agenda_data(file_path):
                    st.session_state.agenda_loaded = True
                    st.markdown(f'<div class="success-card">✅ {len(simulator.agenda_items)} gündem maddesi başarıyla yüklendi!</div>', unsafe_allow_html=True)
                    
                    # Show preview
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
    
    # Tartışma süresi seçimi
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
            # API anahtarı kontrolü
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
    
    # Simulation status display
    display_simulation_status()
    
    # Ana içeriğin sonunda konuşmalar bölümünü göster
    display_conversation_section()

def start_simulation():
    """Start simulation synchronously"""
    try:
        if not simulator.agenda_items:
            st.error("❌ Gündem maddesi bulunamadı!")
            return
            
        # Prepare and run simulation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Step 1: Prepare agenda analysis
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        
        status_placeholder.markdown('<div class="info-card">📊 Gündem analizi başlatılıyor...</div>', unsafe_allow_html=True)
        progress_placeholder.progress(0.1)
        
        try:
            loop.run_until_complete(simulator.prepare_agenda_analysis())
            status_placeholder.markdown('<div class="success-card">✅ Gündem analizi tamamlandı!</div>', unsafe_allow_html=True)
            progress_placeholder.progress(0.3)
            
            # Show scores immediately
            if simulator.agenda_items and any(item.persona_scores for item in simulator.agenda_items):
                st.markdown("#### 📊 Gündem Puanları Hesaplandı")
                display_agenda_scores()
            
        except Exception as e:
            status_placeholder.markdown(f'<div class="error-card">❌ Gündem analizi hatası: {str(e)}</div>', unsafe_allow_html=True)
            SIMULATION_STATE['running'] = False
            return
        
        # Step 2: Start discussion
        status_placeholder.markdown('<div class="info-card">💬 Tartışma başlatılıyor...</div>', unsafe_allow_html=True)
        progress_placeholder.progress(0.5)
        
        # Discussion container
        discussion_container = st.empty()
        
        try:
            async def run_discussion():
                discussion_duration_minutes = st.session_state.get('discussion_duration', 5)
                start_time = time.time()
                end_time = start_time + (discussion_duration_minutes * 60)  # Convert to seconds
                
                message_count = 0
                
                status_placeholder.markdown(f'<div class="info-card">💬 {discussion_duration_minutes} dakikalık tartışma başlatılıyor...</div>', unsafe_allow_html=True)
                
                async def on_new_message():
                    nonlocal message_count
                    message_count += 1
                    
                    # Calculate time-based progress
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    progress = min(elapsed_time / (discussion_duration_minutes * 60), 1.0)
                    progress_percentage = 0.5 + (progress * 0.4)
                    progress_placeholder.progress(progress_percentage)
                    
                    # Update status with time remaining
                    time_remaining = max(0, (end_time - current_time) / 60)
                    status_placeholder.markdown(f'<div class="info-card">💬 Tartışma devam ediyor... Kalan süre: {time_remaining:.1f} dakika</div>', unsafe_allow_html=True)
                    
                    # Check time limit
                    if current_time >= end_time:
                        simulator.stop_simulation()
                        return
                    
                    # Check stop condition
                    if SIMULATION_STATE['stop_requested']:
                        simulator.stop_simulation()
                        return
                        
                    await asyncio.sleep(0.5)
                
                # Start simulation with extended time
                await simulator.start_simulation(max_rounds=10, on_new_message=on_new_message)
            
            loop.run_until_complete(run_discussion())
            
            # Final status
            if SIMULATION_STATE['stop_requested']:
                status_placeholder.markdown('<div class="info-card">⏹️ Simülasyon kullanıcı tarafından durduruldu</div>', unsafe_allow_html=True)
            else:
                status_placeholder.markdown('<div class="success-card">✅ Simülasyon başarıyla tamamlandı!</div>', unsafe_allow_html=True)
            
            progress_placeholder.progress(1.0)
            
        except Exception as e:
            status_placeholder.markdown(f'<div class="error-card">❌ Tartışma hatası: {str(e)}</div>', unsafe_allow_html=True)
            logger.error(f"Discussion error: {e}")
        
        # Final update
        if simulator.discussion_log:
            # Show a simple message count update instead of HTML
            st.info(f"💬 Simülasyon tamamlandı. {len(simulator.discussion_log)} mesaj oluşturuldu.")
        
        SIMULATION_STATE['running'] = False
        st.rerun()
        
    except Exception as e:
        SIMULATION_STATE['running'] = False
        st.error(f"Simülasyon genel hatası: {str(e)}")
        logger.error(f"General simulation error: {e}")
        
        # Debug information
        st.markdown("### 🔍 Debug Bilgileri")
        st.write(f"**Hata:** {str(e)}")
        st.write(f"**Gündem sayısı:** {len(simulator.agenda_items) if simulator.agenda_items else 0}")
        st.write(f"**Persona sayısı:** {len(simulator.personas) if simulator.personas else 0}")
        
        # API durumu
        if hasattr(simulator, 'llm_client'):
            stats = simulator.llm_client.get_request_stats()
            st.write(f"**API İstatistikleri:** {stats}")
            
    finally:
        try:
            loop.close()
        except:
            pass

def update_discussion_display_simple(placeholder):
    """Simple discussion display for real-time updates"""
    if not simulator.discussion_log:
        placeholder.info("💬 Tartışma henüz başlamadı...")
        return

    # Show last 5 messages for performance
    recent_messages = simulator.discussion_log[-5:]
    
    messages_html = """
    <div style="
        background: rgba(15, 23, 42, 0.95);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid rgba(100, 116, 139, 0.3);
    ">
    """
    
    for entry in recent_messages:
        timestamp = format_message_time(entry['timestamp'])
        speaker = entry['speaker']
        message = clean_html_and_format_text(entry['message'])
        
        if not message or message == '0':
            continue
            
        is_moderator = speaker == 'Moderatör'
        
        # Simple message bubble
        bubble_color = "#ec4899" if is_moderator else "#6366f1"
        
        messages_html += f"""
        <div style="
            margin: 0.8rem 0;
            padding: 1rem;
            border-left: 4px solid {bubble_color};
            background: rgba(30, 41, 59, 0.8);
            border-radius: 8px;
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5rem;
            ">
                <strong style="color: {'#fbbf24' if is_moderator else '#a5b4fc'};">{speaker}</strong>
                <span style="font-size: 0.8rem; color: #94a3b8;">{timestamp}</span>
            </div>
            <div style="color: #e2e8f0; line-height: 1.5;">
                {html.escape(message)}
            </div>
        </div>
        """
    
    messages_html += "</div>"
    
    placeholder.markdown(messages_html, unsafe_allow_html=True)

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

def display_simulation_status():
    """Display simulation status"""
    if SIMULATION_STATE['running'] or simulator.discussion_log:
        st.markdown("### 📊 Simülasyon Durumu")
        
        # Status display
        if SIMULATION_STATE['running']:
            st.markdown('<div class="info-card">🔄 Simülasyon çalışıyor...</div>', unsafe_allow_html=True)
        elif simulator.discussion_log:
            st.markdown('<div class="success-card">✅ Simülasyon tamamlandı</div>', unsafe_allow_html=True)
        
        # Display scores if available
        if simulator.agenda_items and any(item.persona_scores for item in simulator.agenda_items):
            display_agenda_scores()

def display_agenda_scores():
    """Display agenda scores and memory summaries"""
    st.markdown("#### 📊 Gündem Puanları")
    
    for agenda_item in simulator.agenda_items:
        if not agenda_item.persona_scores:
            continue
            
        with st.expander(f"📝 {agenda_item.title}"):
            # Scores section
            st.markdown("**🎯 İlgi Puanları:**")
            
            score_cols = st.columns(min(len(simulator.personas), 4))
            
            for i, persona in enumerate(simulator.personas):
                with score_cols[i % len(score_cols)]:
                    score = agenda_item.persona_scores.get(persona.name, "Hesaplanıyor...")
                    
                    if isinstance(score, (int, float)):
                        # Color coding
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
            
            # Memory summaries
            st.markdown("**🧠 Persona Belleklerinde Kalanlar:**")
            
            for persona in simulator.personas:
                memory = agenda_item.persona_memories.get(persona.name)
                if memory:
                    st.markdown(f"**{persona.name}:** {memory[:200]}{'...' if len(memory) > 200 else ''}")

def display_conversation_section():
    """Display conversation section at the bottom"""
    if simulator.discussion_log:
        st.markdown("---")
        st.markdown("### 💬 Tartışma Konuşmaları")
        
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
        
        # Display messages using simple text approach
        st.markdown("#### 📝 Konuşma Detayları")
        
        # Show recent messages in a simple format
        recent_messages = simulator.discussion_log[-10:]  # Son 10 mesaj
        
        for entry in recent_messages:
            timestamp = format_message_time(entry['timestamp'])
            speaker = entry['speaker']
            message = clean_html_and_format_text(entry['message'])
            
            if not message or message == '0':
                continue
            
            is_moderator = speaker == 'Moderatör'
            
            # Use Streamlit's built-in chat message
            with st.chat_message("assistant" if is_moderator else "user"):
                st.markdown(f"**{speaker}** - {timestamp}")
                st.write(message)
        
        # Auto-refresh if simulation is running (less aggressive)
        if SIMULATION_STATE['running']:
            time.sleep(3)
            st.rerun()

def display_analysis_tab():
    """Display analysis tab with both basic and expert analysis"""
    st.markdown("### 📊 Tartışma Analizi")
    
    if not simulator.discussion_log:
        st.markdown('<div class="info-card">ℹ️ Analiz için önce bir simülasyon çalıştırın</div>', unsafe_allow_html=True)
        return
    
    # Analysis options
    analysis_col1, analysis_col2 = st.columns(2)
    
    with analysis_col1:
        if st.button("📊 Temel Analiz", key="basic_analysis"):
            generate_basic_analysis()
    
    with analysis_col2:
        if st.button("🔬 Uzman Araştırmacı Analizi", key="expert_analysis"):
            generate_expert_analysis()
    
    # Show existing analysis if available
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
            # Prepare discussion data
            full_discussion = ""
            for entry in simulator.discussion_log:
                timestamp = entry['timestamp'].strftime("%H:%M:%S")
                speaker = entry['speaker']
                message = clean_html_and_format_text(entry['message'])
                full_discussion += f"[{timestamp}] {speaker}: {message}\n"
            
            # Prepare persona info
            persona_info = ""
            if simulator.personas:
                for persona in simulator.personas:
                    persona_info += f"- {persona.name}: {persona.role}, {persona.personality}\n"
            
            # Prepare agenda info
            agenda_info = ""
            if simulator.agenda_items:
                for i, item in enumerate(simulator.agenda_items, 1):
                    agenda_info += f"{i}. {item.title}\n"
            
            # Basic analysis prompt
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
            # Prepare discussion data
            full_discussion = ""
            for entry in simulator.discussion_log:
                timestamp = entry['timestamp'].strftime("%H:%M:%S")
                speaker = entry['speaker']
                message = clean_html_and_format_text(entry['message'])
                full_discussion += f"[{timestamp}] {speaker}: {message}\n"
            
            # Prepare persona info
            persona_info = ""
            if simulator.personas:
                for persona in simulator.personas:
                    persona_info += f"- {persona.name}: {persona.role}, {persona.personality}\n"
            
            # Prepare agenda info
            agenda_info = ""
            if simulator.agenda_items:
                for i, item in enumerate(simulator.agenda_items, 1):
                    agenda_info += f"{i}. {item.title}\n"
            
            # Expert analysis prompt
            analysis_prompt = f"""[SİSTEM MESAJI]
Sen "Prof. Dr. Araştırmacı" adında sosyoloji ve siyaset bilimi alanında uzmanlaşmış bir akademisyensin. Sana bir odak grup tartışmasının tam transkripti verilecek. Kapsamlı bir araştırma raporu hazırla.

[KATILIMCILAR]
{persona_info}

[TARTIŞILAN KONULAR]
{agenda_info}

[TARTIŞMA TRANSKRİPTİ]
{full_discussion}

[ARAŞTIRMA RAPORU TALİMATLARI]
Aşağıdaki başlıkları kullanarak akademik düzeyde, detaylı bir analiz raporu hazırla:

**1. YÖNETİCİ ÖZETİ**
- Araştırmanın amacı ve kapsamı
- Ana bulgular (3-4 madde)
- Önemli sonuçlar ve öneriler

**2. KATILIMCI ANALİZİ**
- Her katılımcının demografik ve psikografik profili
- Konuşma tarzları ve dil kullanımları
- Grup içindeki rolleri

**3. TEMA VE İÇERİK ANALİZİ**
- Ortaya çıkan ana temalar
- En çok tartışılan konular
- Uzlaşma ve çelişki alanları

**4. ETKİLEŞİM DİNAMİKLERİ**
- Katılımcılar arası etkileşim kalıpları
- İttifak ve karşıtlık ilişkileri
- Moderatörün etkisi

**5. SOSYOLOJİK BULGULAR**
- Toplumsal sınıf, yaş, cinsiyet etkileri
- Kültürel sermaye farklılıkları
- Grup dinamikleri

**6. POLİTİK BOYUT ANALİZİ**
- Siyasi eğilimler ve ideolojik konumlanmalar
- Polarizasyon seviyeleri
- Demokratik katılım kalitesi

**7. SONUÇ VE ÖNERİLER**
- Temel bulgular
- Toplumsal ve politik çıkarımlar
- Politika önerileri

Raporunu akademik standartlarda, objektif ve bilimsel bir dille yaz.
"""
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            comprehensive_analysis = loop.run_until_complete(simulator.llm_client.call_llm(analysis_prompt))
            
            # Store analysis result
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
    
    # PDF creation function
    def create_enhanced_pdf(conversation: List[Dict], analysis: str, personas: List) -> FPDF:
        """Create enhanced PDF with Helvetica font"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Use Helvetica font (built-in)
        pdf.set_font('Helvetica', 'B', 16)
        
        # Title
        pdf.cell(0, 15, 'Odak Grup Simulasyonu Raporu', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(10)
        
        # Date and info
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 8, f'Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        # Participants
        if personas:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, 'Katilimcilar:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font('Helvetica', '', 10)
            for persona in personas:
                name = clean_text_for_pdf(persona.name)
                role = clean_text_for_pdf(persona.role)
                pdf.cell(0, 6, f'  * {name} ({role})', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
        
        # Discussion section
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'Tartisma Gecmisi:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        # Add conversation with cleaning
        for entry in conversation:
            timestamp = format_message_time(entry['timestamp'])
            speaker = clean_text_for_pdf(entry['speaker'])
            message = clean_text_for_pdf(clean_html_and_format_text(str(entry['message'])))
            
            # Truncate if too long
            if len(message) > 200:
                message = message[:200] + "..."
            
            # Speaker name
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, f"{speaker} [{timestamp}]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Message content
            pdf.set_font('Helvetica', '', 9)
            try:
                # Split message into lines to avoid width issues
                max_chars_per_line = 80
                lines = [message[i:i+max_chars_per_line] for i in range(0, len(message), max_chars_per_line)]
                for line in lines:
                    if line.strip():
                        pdf.cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            except:
                pdf.cell(0, 5, "Mesaj görüntülenemiyor", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.ln(2)
        
        # Analysis section
        if analysis:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, 'Analiz Raporu:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            
            # Clean analysis
            analysis_clean = clean_text_for_pdf(clean_html_and_format_text(analysis))
            
            # Split into manageable chunks
            pdf.set_font('Helvetica', '', 9)
            max_chars_per_line = 80
            lines = [analysis_clean[i:i+max_chars_per_line] for i in range(0, len(analysis_clean), max_chars_per_line)]
            
            for line in lines[:100]:  # Limit to first 100 lines
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
        
        # Turkish character mapping
        char_map = {
            'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U',
            'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I',
            'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
        }
        
        for tr_char, en_char in char_map.items():
            text = text.replace(tr_char, en_char)
        
        # Remove problematic characters
        text = ''.join(char for char in text if ord(char) < 128)
        
        return text
    
    # Report generation
    if st.button('📄 PDF Raporu Oluştur', key="generate_pdf"):
        try:
            with st.spinner("PDF oluşturuluyor..."):
                analysis_text = st.session_state.get('analysis_result', '') or st.session_state.get('expert_analysis_result', '')
                pdf = create_enhanced_pdf(simulator.discussion_log, analysis_text, simulator.personas)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
                    pdf.output(tmpfile.name)
                    
                    with open(tmpfile.name, 'rb') as f:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f'odak_grup_raporu_{timestamp}.pdf'
                        
                        st.download_button(
                            label="📥 PDF İndir",
                            data=f.read(),
                            file_name=filename,
                            mime='application/pdf',
                            key="download_pdf"
                        )
                
                st.success("✅ PDF raporu hazır!")
                
        except Exception as e:
            st.error(f"PDF oluşturma hatası: {str(e)}")

def reset_simulation():
    """Reset simulation state"""
    # Stop any running simulation
    simulator.stop_simulation()
    
    # Reset global state
    SIMULATION_STATE['running'] = False
    SIMULATION_STATE['stop_requested'] = False
    
    # Reset session state
    st.session_state.analysis_result = ""
    st.session_state.expert_analysis_result = ""
    st.session_state.agenda_loaded = False
    
    # Clear simulator data
    simulator.discussion_log = []
    simulator.mcp_logs = []
    simulator.agenda_items = []
    simulator.memory = {}
    
    st.success("🔄 Simülasyon sıfırlandı!")
    st.rerun()

if __name__ == "__main__":
    main()