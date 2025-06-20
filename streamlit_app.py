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
    
    /* Progress indicators */
    .progress-indicator {
        background: rgba(30, 41, 59, 0.8) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        border: 1px solid rgba(100, 116, 139, 0.2) !important;
        text-align: center !important;
    }
    
    .progress-step {
        display: inline-block !important;
        width: 12px !important;
        height: 12px !important;
        border-radius: 50% !important;
        margin: 0 0.5rem !important;
        background: #374151 !important;
        transition: all 0.3s ease !important;
    }
    
    .progress-step.active {
        background: #6366f1 !important;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.5) !important;
    }
    
    .progress-step.completed {
        background: #10b981 !important;
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

def clean_html_and_format_text(text):
    """Clean HTML tags and format text properly"""
    if not text:
        return ""
    
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
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
    
    button_col1, button_col2, button_col3 = st.columns(3)
    
    with button_col1:
        start_enabled = st.session_state.agenda_loaded and not st.session_state.simulation_running
        if st.button("▶️ Simülasyonu Başlat", disabled=not start_enabled, key="start_btn"):
            st.session_state.simulation_running = True
            st.session_state.stop_simulation = False
            run_simulation()
    
    with button_col2:
        if st.button("⏹️ Durdur", disabled=not st.session_state.simulation_running, key="stop_btn"):
            stop_simulation()
    
    with button_col3:
        if st.button("🔄 Sıfırla", key="reset_btn"):
            reset_simulation()
    
    # Simulation display
    display_simulation_content()

def run_simulation():
    """Odak grup simülasyonunu başlat"""
    if not simulator.agenda_items:
        st.error("Gündem maddesi bulunamadı!")
        return
    
    # Placeholders for dynamic updates
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    scores_placeholder = st.empty()
    discussion_placeholder = st.empty()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def simulation_runner():
            # Status updates
            status_placeholder.markdown('<div class="status-card">🚀 Simülasyon başlatılıyor...</div>', unsafe_allow_html=True)
            
            # Step 1: Agenda analysis
            progress_placeholder.markdown("""
            <div class="progress-indicator">
                <div class="progress-step active"></div>
                <span>📊 Gündem analizi yapılıyor...</span>
            </div>
            """, unsafe_allow_html=True)
            
            await simulator.prepare_agenda_analysis()
            
            # Show scores
            display_agenda_scores(scores_placeholder)
            
            # Step 2: Start discussion
            progress_placeholder.markdown("""
            <div class="progress-indicator">
                <div class="progress-step completed"></div>
                <div class="progress-step active"></div>
                <span>💬 Tartışma başlatılıyor...</span>
            </div>
            """, unsafe_allow_html=True)
            
            async def on_new_message():
                """Callback for new messages"""
                update_discussion_display(discussion_placeholder)
                await asyncio.sleep(0.1)
            
            # Start simulation
            st.session_state.simulation_running = True
            await simulator.start_simulation(max_rounds=2, on_new_message=on_new_message)
            st.session_state.simulation_running = False
            
            # Completed
            progress_placeholder.markdown("""
            <div class="progress-indicator">
                <div class="progress-step completed"></div>
                <div class="progress-step completed"></div>
                <div class="progress-step completed"></div>
                <span>✅ Simülasyon tamamlandı!</span>
            </div>
            """, unsafe_allow_html=True)
            
            status_placeholder.markdown('<div class="success-card">✅ Simülasyon başarıyla tamamlandı!</div>', unsafe_allow_html=True)
            update_discussion_display(discussion_placeholder)
        
        loop.run_until_complete(simulation_runner())
        
    except Exception as e:
        st.session_state.simulation_running = False
        status_placeholder.markdown(f'<div class="error-card">❌ Simülasyon hatası: {str(e)}</div>', unsafe_allow_html=True)
        logger.error(f"Simulation error: {e}")
    finally:
        try:
            loop.close()
        except:
            pass

def display_agenda_scores(placeholder):
    """Display agenda scores and memory summaries"""
    if not simulator.agenda_items or not simulator.personas:
        return
    
    with placeholder.container():
        st.markdown("### 📊 Gündem Puanları ve Bellek Özetleri")
        
        for agenda_item in simulator.agenda_items:
            with st.expander(f"📝 {agenda_item.title}", expanded=True):
                
                # Scores section
                if agenda_item.persona_scores:
                    st.markdown("#### 🎯 İlgi Puanları")
                    
                    # Display scores in a responsive grid
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
                                    background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                                    border: 2px solid {color}44;
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
                    
                    # Average score
                    valid_scores = [v for v in agenda_item.persona_scores.values() if isinstance(v, (int, float))]
                    if valid_scores:
                        avg_score = sum(valid_scores) / len(valid_scores)
                        st.markdown(f"""
                        <div style="
                            text-align: center; 
                            margin: 1rem 0; 
                            padding: 0.8rem; 
                            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
                            border-radius: 12px; 
                            color: white; 
                            font-weight: bold;
                        ">
                            📊 Ortalama İlgi Puanı: {avg_score:.1f}/10
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("⏳ Puanlar henüz hesaplanıyor...")
                
                # Memory summaries
                st.markdown("#### 🧠 Persona Belleklerinde Kalanlar")
                
                memory_found = False
                for persona in simulator.personas:
                    memory = agenda_item.persona_memories.get(persona.name)
                    if memory:
                        st.markdown(f"""
                        <div style="
                            background: rgba(139, 92, 246, 0.1);
                            border-left: 4px solid #8b5cf6;
                            padding: 1rem;
                            border-radius: 0 12px 12px 0;
                            margin: 0.5rem 0;
                        ">
                            <div style='font-weight: bold; color: #a855f7; margin-bottom: 0.8rem;'>
                                🧠 {persona.name}
                            </div>
                            <div style='color: #e2e8f0; line-height: 1.5;'>
                                {html.escape(memory[:150])}{'...' if len(memory) > 150 else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        memory_found = True
                
                if not memory_found:
                    st.markdown("*🔄 Bellek özetleri oluşturuluyor...*")

def update_discussion_display(placeholder):
    """Update discussion display with improved chat design"""
    if not simulator.discussion_log:
        placeholder.info("💬 Tartışma henüz başlamadı...")
        return

    # Show last 12 messages for better performance
    recent_messages = simulator.discussion_log[-12:]

    chat_html = """
<div style="
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
">
"""
    
    for entry in recent_messages:
        timestamp = format_message_time(entry['timestamp'])
        speaker = entry['speaker']
        message = clean_html_and_format_text(entry['message'])
        
        if not message or message == '0':
            continue
            
        is_moderator = speaker == 'Moderatör'
        
        # Get profile picture
        pic_path = get_persona_pic(speaker)
        if pic_path:
            pic_base64 = get_base64_from_file(pic_path)
            avatar_html = f'<img src="data:image/png;base64,{pic_base64}" style="width: 50px; height: 50px; border-radius: 50%; margin-right: 1rem; object-fit: cover; border: 3px solid {"#ec4899" if is_moderator else "#6366f1"}; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); flex-shrink: 0;">'
        else:
            avatar_color = "#ec4899" if is_moderator else "#6366f1"
            avatar_html = f'<div style="width: 50px; height: 50px; border-radius: 50%; margin-right: 1rem; background: {avatar_color}; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; flex-shrink: 0; border: 3px solid {avatar_color}; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);">{speaker[0].upper()}</div>'
        
        # Styling based on speaker type
        if is_moderator:
            bubble_bg = "linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%)"
            border_color = "#ec4899"
            name_color = "#fbbf24"
        else:
            bubble_bg = "linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%)"
            border_color = "#6366f1"
            name_color = "#a5b4fc"
        
        message_escaped = html.escape(message)
        
        chat_html += f'''
        <div style="
            display: flex;
            align-items: flex-start;
            margin: 1.5rem 0;
            padding: 1.5rem;
            border-radius: 18px;
            background: {bubble_bg};
            border: 1px solid {border_color}44;
            word-wrap: break-word;
            overflow-wrap: break-word;
            animation: fadeIn 0.5s ease-out;
            max-width: 100%;
            box-sizing: border-box;
        ">
            {avatar_html}
            <div style="flex: 1; min-width: 0;">
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 0.8rem;
                ">
                    <div style="
                        font-weight: 600;
                        font-size: 1.1rem;
                        color: {name_color};
                    ">
                        {speaker}
                    </div>
                    <div style="
                        font-size: 0.85rem;
                        color: #94a3b8;
                        background: rgba(100, 116, 139, 0.2);
                        padding: 0.3rem 0.8rem;
                        border-radius: 12px;
                    ">
                        {timestamp}
                    </div>
                </div>
                <div style="
                    color: #e2e8f0;
                    line-height: 1.6;
                    font-size: 1rem;
                    white-space: pre-wrap;
                    word-break: break-word;
                ">
                    {message_escaped}
                </div>
            </div>
        </div>
        '''
    
    chat_html += "</div>"
    
    placeholder.markdown(chat_html, unsafe_allow_html=True)

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
            st.info("Temel analiz oluşturuluyor...")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                analysis = loop.run_until_complete(simulator.generate_analysis())
                st.session_state['analysis_result'] = analysis
                
                st.markdown(f"""
                <div style="
                    background: rgba(30, 41, 59, 0.95);
                    border: 1px solid rgba(100, 116, 139, 0.3);
                    padding: 2rem;
                    border-radius: 15px;
                    margin: 1rem 0;
                    color: #e2e8f0;
                    white-space: pre-wrap;
                    line-height: 1.6;
                ">
                {analysis}
                </div>
                """, unsafe_allow_html=True)
                
                st.success("✅ Temel analiz tamamlandı!")
            except Exception as e:
                st.error(f"Analiz oluşturma hatası: {str(e)}")
            finally:
                try:
                    loop.close()
                except:
                    pass
    
    with analysis_col2:
        if st.button("🔬 Uzman Araştırmacı Analizi", key="expert_analysis"):
            asyncio.run(generate_expert_research_analysis())
    
    # Show existing analysis if available
    if st.session_state.get('analysis_result'):
        st.markdown("#### 📋 Temel Analiz Sonucu")
        with st.expander("Analiz Detayları", expanded=False):
            st.markdown(st.session_state['analysis_result'])
    
    if st.session_state.get('expert_analysis_result'):
        st.markdown("#### 🔬 Uzman Araştırmacı Analizi")
        with st.expander("Detaylı Araştırma Raporu", expanded=False):
            st.markdown(st.session_state['expert_analysis_result'])

async def generate_expert_research_analysis():
    """Generate comprehensive expert research analysis"""
    with st.spinner("🔬 Uzman araştırmacı analiz ediyor..."):
        try:
            # Prepare discussion data
            full_discussion = ""
            for entry in simulator.discussion_log:
                timestamp = entry['timestamp'].strftime("%H:%M:%S")
                speaker = entry['speaker']
                message = entry['message']
                full_discussion += f"[{timestamp}] {speaker}: {message}\n"
            
            # Expert analysis prompt
            analysis_prompt = f"""[SİSTEM MESAJI]
Sen "Prof. Dr. Araştırmacı" adında sosyoloji ve siyaset bilimi alanında uzmanlaşmış bir akademisyensin. Sana bir odak grup tartışmasının tam transkripti verilecek. Kapsamlı bir araştırma raporu hazırla.

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
            
            comprehensive_analysis = await simulator.llm_client.call_llm(analysis_prompt)
            
            # Store analysis result
            st.session_state.expert_analysis_result = comprehensive_analysis
            
            # Display the analysis
            st.markdown(f"""
            ### 📊 Uzman Araştırmacı Analiz Raporu
            
            <div style="
                background: rgba(30, 41, 59, 0.95);
                border: 1px solid rgba(100, 116, 139, 0.3);
                padding: 2rem;
                border-radius: 15px;
                margin: 1rem 0;
                color: #e2e8f0;
                white-space: pre-wrap;
                line-height: 1.6;
            ">
            {comprehensive_analysis}
            </div>
            """, unsafe_allow_html=True)
            
            st.success("✅ Uzman araştırmacı analizi tamamlandı!")
            
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
        """Create enhanced PDF with basic Arial font"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Use basic Arial font
        pdf.set_font('Arial', 'B', 16)
        
        # Title
        pdf.cell(0, 15, 'Odak Grup Simulasyonu Raporu', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(10)
        
        # Date and info
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f'Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        # Participants
        if personas:
            pdf.cell(0, 8, 'Katilimcilar:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for persona in personas:
                name = persona.name.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ı', 'i').replace('ö', 'o').replace('ç', 'c')
                role = persona.role.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ı', 'i').replace('ö', 'o').replace('ç', 'c')
                pdf.cell(0, 6, f'  * {name} ({role})', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
        
        # Discussion section
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Tartisma Gecmisi:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 10)
        
        # Add conversation with cleaning
        for entry in conversation:
            timestamp = format_message_time(entry['timestamp'])
            speaker = entry['speaker']
            message = str(entry['message'])
            
            # Clean Turkish characters
            speaker = speaker.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ı', 'i').replace('ö', 'o').replace('ç', 'c')
            speaker = speaker.replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('İ', 'I').replace('Ö', 'O').replace('Ç', 'C')
            
            # Clean message
            message = re.sub(r'<[^>]+>', '', message)  # Remove HTML tags
            message = message.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ı', 'i').replace('ö', 'o').replace('ç', 'c')
            message = message.replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('İ', 'I').replace('Ö', 'O').replace('Ç', 'C')
            
            # Truncate if too long
            if len(message) > 250:
                message = message[:250] + "..."
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 6, f"{speaker} [{timestamp}]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.set_font('Arial', '', 10)
            try:
                message_clean = message.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, message_clean)
            except:
                message_ascii = message.encode('ascii', 'replace').decode('ascii')
                pdf.multi_cell(0, 5, message_ascii)
            
            pdf.ln(2)
        
        # Analysis section
        if analysis:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Analiz Raporu:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(5)
            
            pdf.set_font('Arial', '', 10)
            
            # Clean analysis
            analysis_clean = re.sub(r'<[^>]+>', '', analysis)
            analysis_clean = analysis_clean.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ı', 'i').replace('ö', 'o').replace('ç', 'c')
            analysis_clean = analysis_clean.replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('İ', 'I').replace('Ö', 'O').replace('Ç', 'C')
            
            # Split into chunks
            chunk_size = 1500
            for i in range(0, len(analysis_clean), chunk_size):
                chunk = analysis_clean[i:i+chunk_size]
                try:
                    chunk_safe = chunk.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 5, chunk_safe)
                except:
                    chunk_ascii = chunk.encode('ascii', 'replace').decode('ascii')
                    pdf.multi_cell(0, 5, chunk_ascii)
        
        return pdf
    
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

def display_simulation_content():
    """Display simulation status and chat at the bottom"""
    if st.session_state.simulation_running or simulator.discussion_log:
        st.markdown("---")
        st.markdown("### 📊 Simülasyon Durumu")
        
        # Status metrics
        if simulator.discussion_log:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💬 Toplam Mesaj", len(simulator.discussion_log))
            
            with col2:
                persona_messages = len([entry for entry in simulator.discussion_log if entry['speaker'] != 'Moderatör'])
                st.metric("👥 Persona Mesajları", persona_messages)
            
            with col3:
                if simulator.discussion_log:
                    last_speaker = simulator.discussion_log[-1]['speaker']
                    st.metric("🎤 Son Konuşan", last_speaker)
            
            with col4:
                status_text = "🟢 Aktif" if st.session_state.simulation_running else "⏹️ Tamamlandı"
                st.metric("⏱️ Durum", status_text)

def reset_simulation():
    """Reset simulation state"""
    st.session_state.simulation_running = False
    st.session_state.stop_simulation = False
    st.session_state.analysis_result = ""
    st.session_state.expert_analysis_result = ""
    st.session_state.agenda_loaded = False
    
    # Clear simulator data
    simulator.discussion_log = []
    simulator.mcp_logs = []
    simulator.agenda_items = []
    
    st.success("🔄 Simülasyon sıfırlandı!")
    st.rerun()

def stop_simulation():
    """Stop the running simulation"""
    try:
        simulator.stop_simulation()
        st.session_state.simulation_running = False
        st.session_state.stop_simulation = True
        st.warning("⏹️ Simülasyon durduruldu")
    except Exception as e:
        st.error(f"Simülasyon durdurulurken hata: {str(e)}")

if __name__ == "__main__":
    main()