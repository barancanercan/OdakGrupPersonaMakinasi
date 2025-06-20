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

# Enhanced CSS styles with dark theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling - Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    .main > div {
        background: rgba(30, 41, 59, 0.95);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(100, 116, 139, 0.2);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
    }
    
    /* Text colors for dark theme */
    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
    }
    
    p, div, span {
        color: #cbd5e1;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    /* Card styling - Dark Theme */
    .info-card {
        background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: #f8fafc;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        border: 1px solid rgba(124, 58, 237, 0.3);
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(124, 58, 237, 0.3);
    }
    
    .status-card {
        background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: #f8fafc;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        border: 1px solid rgba(14, 165, 233, 0.3);
    }
    
    .success-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: #f0fdf4;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .error-card {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: #fef2f2;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Button styling - Dark Theme */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: #f8fafc;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(99, 102, 241, 0.4);
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
        color: #6b7280;
        border-color: #374151;
        transform: none;
        box-shadow: none;
    }
    
    /* Message styling - Dark Theme */
    .message-container {
        background: rgba(51, 65, 85, 0.8);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        border: 1px solid rgba(100, 116, 139, 0.2);
        border-left: 4px solid;
    }
    
    .persona-message {
        border-left-color: #6366f1;
        background: rgba(51, 65, 85, 0.9);
    }
    
    .moderator-message {
        border-left-color: #ec4899;
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
    }
    
    .message-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(100, 116, 139, 0.3);
    }
    
    .profile-pic {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        margin-right: 1rem;
        object-fit: cover;
        border: 3px solid #6366f1;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    
    .speaker-name {
        font-weight: 600;
        font-size: 1.1rem;
        color: #f1f5f9;
    }
    
    .message-time {
        margin-left: auto;
        color: #94a3b8;
        font-size: 0.875rem;
        background: rgba(99, 102, 241, 0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    .message-text {
        color: #e2e8f0;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    /* Sidebar styling - Dark Theme */
    .css-1d391kg {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    }
    
    /* Streamlit component overrides */
    .stSidebar {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    }
    
    .stSelectbox > div > div {
        background-color: #334155;
        color: #e2e8f0;
        border: 1px solid #475569;
    }
    
    .stTextInput > div > div > input {
        background-color: #334155;
        color: #e2e8f0;
        border: 1px solid #475569;
    }
    
    .stCheckbox > label {
        color: #e2e8f0;
    }
    
    /* Progress bar - Dark Theme */
    .progress-bar {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        height: 8px;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    /* Stats styling - Dark Theme */
    .stat-item {
        background: rgba(51, 65, 85, 0.8);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 1px solid rgba(100, 116, 139, 0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .stat-label {
        font-weight: 500;
        color: #cbd5e1;
    }
    
    .stat-value {
        font-weight: 700;
        color: #6366f1;
        font-size: 1.2rem;
    }
    
    /* File uploader styling - Dark Theme */
    .stFileUploader {
        border: 2px dashed #6366f1;
        border-radius: 15px;
        padding: 2rem;
        background: rgba(51, 65, 85, 0.5);
        text-align: center;
    }
    
    .stFileUploader label {
        color: #e2e8f0 !important;
    }
    
    /* Expandable sections - Dark Theme */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: #f8fafc;
        border-radius: 10px;
        padding: 0.5rem 1rem;
    }
    
    .streamlit-expanderContent {
        background: rgba(51, 65, 85, 0.5);
        border: 1px solid rgba(100, 116, 139, 0.2);
        border-radius: 0 0 10px 10px;
    }
    
    /* Tabs styling - Dark Theme */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #cbd5e1;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: #f8fafc;
    }
    
    /* Metrics styling - Dark Theme */
    .metric-container {
        background: rgba(51, 65, 85, 0.8);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(100, 116, 139, 0.2);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.3); }
        50% { box-shadow: 0 0 30px rgba(99, 102, 241, 0.6); }
    }
    
    .glow {
        animation: glow 2s ease-in-out infinite;
    }
    
    /* Loading spinner - Dark Theme */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #334155;
        border-top: 3px solid #6366f1;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Scrollbar styling - Dark Theme */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
    }
</style>
""", unsafe_allow_html=True)

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

def create_enhanced_pdf(conversation: List[Dict], analysis: str, personas: List) -> FPDF:
    """Create enhanced PDF with better formatting and full Unicode support"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    # Font paths
    font_path = 'DejaVuSans.ttf'
    bold_font_path = 'DejaVuSans-Bold.ttf'
    if not (os.path.exists(font_path) and os.path.exists(bold_font_path)):
        st.error('PDF için DejaVuSans.ttf ve DejaVuSans-Bold.ttf dosyaları gereklidir. Lütfen bu fontları proje dizinine ekleyin.')
        raise RuntimeError('PDF için Unicode font dosyaları eksik.')
    pdf.add_font('DejaVu', '', font_path)
    pdf.add_font('DejaVu', 'B', bold_font_path)
    pdf.set_font('DejaVu', '', 16)
    pdf.cell(0, 15, 'Odak Grup Simülasyonu Raporu', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(0, 8, f'Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    if personas:
        pdf.cell(0, 8, 'Katılımcılar:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for persona in personas:
            pdf.cell(0, 6, f'  • {persona.name} ({persona.role})', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
    pdf.set_font('DejaVu', 'B', 14)
    pdf.cell(0, 10, 'Tartışma Geçmişi:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.set_font('DejaVu', '', 10)
    for entry in conversation:
        timestamp = format_message_time(entry['timestamp'])
        speaker = entry['speaker']
        message = entry['message'][:200] + "..." if len(entry['message']) > 200 else entry['message']
        pdf.set_font('DejaVu', 'B', 10)
        pdf.cell(0, 6, f"{speaker} [{timestamp}]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('DejaVu', '', 10)
        pdf.multi_cell(0, 5, message)
        pdf.ln(2)
    if analysis:
        pdf.add_page()
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(0, 10, 'Analiz Raporu:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        pdf.set_font('DejaVu', '', 10)
        pdf.multi_cell(0, 5, analysis)
    return pdf

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
                    for bio_item in persona.bio[:3]:  # İlk 3 bio item
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
    
    # Main content
    main_tabs = st.tabs(["🚀 Simülasyon", "📊 Analiz", "📄 Rapor"])
    
    with main_tabs[0]:
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
                st.session_state.stop_simulation = True
                st.session_state.simulation_running = False
                stop_simulation()
                st.success("Simülasyon durduruldu")
        
        with button_col3:
            if st.button("🔄 Sıfırla", key="reset_btn"):
                reset_simulation()
                st.success("Simülasyon sıfırlandı")
        
        # Simulation display
        display_simulation_content()
    
    with main_tabs[1]:
        display_analysis_tab()
    
    with main_tabs[2]:
        display_report_tab()

# --- Simülasyon başlatma fonksiyonu ---
def run_simulation():
    """Odak grup simülasyonunu başlat"""
    if not simulator.agenda_items:
        st.error("Gündem maddesi bulunamadı!")
        return
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    memory_placeholder = st.empty()
    discussion_placeholder = st.empty()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def simulation_runner():
            status_placeholder.markdown('<div class="status-card">🚀 Simülasyon başlatılıyor...</div>', unsafe_allow_html=True)
            await simulator.prepare_agenda_analysis()
            display_agenda_scores()
            await simulator.start_simulation()
            st.session_state.simulation_running = False
            status_placeholder.markdown('<div class="success-card">✅ Simülasyon tamamlandı!</div>', unsafe_allow_html=True)
            progress_placeholder.progress(1.0)
            update_discussion_display(discussion_placeholder)
            update_memory_display(memory_placeholder)
        loop.run_until_complete(simulation_runner())
    except Exception as e:
        st.session_state.simulation_running = False
        st.error(f"Simülasyon hatası: {str(e)}")
    finally:
        try:
            loop.close()
        except:
            pass

# --- Gündem puanları ve bellek özetleri ---
def display_agenda_scores():
    if not simulator.agenda_items or not simulator.personas:
        return
    st.markdown("### 📊 Gündem Puanları ve Bellek Özetleri")
    for agenda_item in simulator.agenda_items:
        with st.expander(f"📝 {agenda_item.title}", expanded=True):
            # Skorlar
            if agenda_item.persona_scores:
                score_cols = st.columns(len(simulator.personas))
                for idx, persona in enumerate(simulator.personas):
                    with score_cols[idx]:
                        score = agenda_item.persona_scores.get(persona.name, "Hesaplanıyor...")
                        if isinstance(score, (int, float)):
                            color = "#10b981" if score >= 7 else "#f59e0b" if score >= 4 else "#ef4444"
                            st.markdown(f"""
                            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, {color}22 0%, {color}11 100%); border: 2px solid {color}44; border-radius: 10px; margin: 0.5rem 0;">
                                <div style="font-weight: bold; color: #e2e8f0; margin-bottom: 0.5rem;">{persona.name}</div>
                                <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{score}/10</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.metric(persona.name, score)
                if agenda_item.persona_scores:
                    avg_score = sum([v for v in agenda_item.persona_scores.values() if isinstance(v, (int, float))]) / max(1, len([v for v in agenda_item.persona_scores.values() if isinstance(v, (int, float))]))
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: 1rem; padding: 0.5rem; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 8px; color: white; font-weight: bold;">Ortalama Puan: {avg_score:.1f}/10</div>
                    """, unsafe_allow_html=True)
            else:
                st.info("⏳ Puanlar henüz hesaplanıyor...")
            # Bellek özetleri
            st.markdown("**🧠 Persona Belleklerinde Kalanlar:**")
            memory_found = False
            for persona in simulator.personas:
                memory = agenda_item.persona_memories.get(persona.name)
                if memory:
                    st.markdown(f"**{persona.name}:** {memory[:150]}...")
                    memory_found = True
            if not memory_found:
                st.markdown("*Henüz bellek özetleri oluşturulmadı.*")

def update_discussion_display(placeholder):
    """Update discussion display"""
    if not simulator.discussion_log:
        return
    
    discussion_html = ""
    
    for entry in simulator.discussion_log[-10:]:  # Show last 10 messages
        timestamp = format_message_time(entry['timestamp'])
        speaker = entry['speaker']
        message = html.escape(entry['message'][:300])  # Truncate long messages
        
        is_moderator = speaker == 'Moderatör'
        
        pic_path = get_persona_pic(speaker)
        pic_html = ""
        
        if pic_path:
            pic_base64 = get_base64_from_file(pic_path)
            pic_html = f'<img src="data:image/png;base64,{pic_base64}" class="profile-pic">'
        
        css_class = "moderator-message" if is_moderator else "persona-message"
        
        discussion_html += f"""
        <div class="message-container {css_class} fade-in">
            <div class="message-header">
                {pic_html}
                <div class="speaker-name">{speaker}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            <div class="message-text">{message}</div>
        </div>
        """
    
    placeholder.markdown(discussion_html, unsafe_allow_html=True)

def update_memory_display(placeholder):
    """Update memory display using agenda_item.persona_memories"""
    if not simulator.agenda_items or not simulator.personas:
        placeholder.markdown("**🧠 Persona Belleği:** Henüz bellek verisi yok.")
        return
    memory_found = False
    with placeholder:
        st.markdown("### 🧠 Persona Belleği")
        for agenda_item in simulator.agenda_items:
            if not agenda_item.persona_memories:
                continue
            with st.expander(f"📝 {agenda_item.title}"):
                for persona in simulator.personas:
                    memory = agenda_item.persona_memories.get(persona.name)
                    if memory:
                        st.markdown(f"**{persona.name}:** {memory[:300]}..." if len(memory) > 300 else f"**{persona.name}:** {memory}")
                        memory_found = True
    if not memory_found:
        placeholder.markdown("**🧠 Persona Belleği:** Henüz bellek verisi yok.")

def display_simulation_content():
    """Display simulation content area"""
    if st.session_state.simulation_running or simulator.discussion_log:
        st.markdown("### 💬 Canlı Tartışma")
        discussion_container = st.container()
        with discussion_container:
            if simulator.discussion_log:
                for entry in simulator.discussion_log:
                    # Sadece boş olmayan ve 0 olmayan mesajları göster
                    msg = str(entry.get('message', '')).strip()
                    if not msg or msg == '0':
                        continue
                    display_single_message(entry)
            else:
                st.info("Tartışma henüz başlamadı...")

def display_single_message(entry):
    """Display a single message in the discussion"""
    timestamp = format_message_time(entry['timestamp'])
    speaker = entry['speaker']
    message = str(entry['message']).strip()
    if not message or message == '0':
        return  # Boş veya 0 mesajları gösterme
    is_moderator = speaker == 'Moderatör'
    with st.container():
        col1, col2 = st.columns([1, 20])
        with col1:
            pic_path = get_persona_pic(speaker)
            if pic_path:
                st.image(pic_path, width=50)
            else:
                st.markdown("🎙️" if is_moderator else "👤")
        with col2:
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                speaker_emoji = "🎙️" if is_moderator else "👤"
                st.markdown(f"**{speaker_emoji} {speaker}**")
            with header_col2:
                st.markdown(f"*{timestamp}*")
            bubble_style = (
                "background: linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%); border-left: 4px solid #ec4899; "
                if is_moderator else
                "background: rgba(51, 65, 85, 0.8); border-left: 4px solid #6366f1; min-height: 60px; "
            )
            bubble_style += "padding: 1rem; border-radius: 0 10px 10px 0; margin: 0.5rem 0; color: #e2e8f0; word-break: break-word; overflow-wrap: break-word; white-space: pre-wrap; max-width: 100%;"
            # Only escape once, and allow HTML
            st.markdown(f"""
            <div style='{bubble_style}'>
            {html.escape(message)}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

async def generate_expert_research_analysis():
    """Generate comprehensive expert research analysis with thinking layer"""
    
    with st.spinner("🔬 Uzman araştırmacı analiz ediyor... Bu süreç birkaç dakika sürebilir."):
        try:
            # Create expert researcher with thinking capability
            research_analysis_placeholder = st.empty()
            
            # Step 1: Thinking Phase
            research_analysis_placeholder.markdown("""
            <div class="status-card">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div class="loading-spinner"></div>
                    <div>
                        <strong>🧠 Araştırmacı Düşünüyor...</strong><br>
                        <small>Tartışma verilerini analiz ediyor, kalıpları tespit ediyor</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Prepare discussion data
            full_discussion = ""
            for entry in simulator.discussion_log:
                timestamp = entry['timestamp'].strftime("%H:%M:%S")
                speaker = entry['speaker']
                message = entry['message']
                full_discussion += f"[{timestamp}] {speaker}: {message}\n"
            
            # Thinking prompt
            thinking_prompt = f"""[SİSTEM MESAJI]
Sen "Prof. Dr. Araştırmacı" adında sosyoloji ve siyaset bilimi alanında uzmanlaşmış bir akademisyensin. Sana bir odak grup tartışmasının tam transkripti verilecek. Bu tartışmayı derinlemesine analiz etmeden önce, düşüncelerini aşama aşama organize et.

[TARTIŞMA TRANSKRİPTİ]
{full_discussion}

[DÜŞÜNCE AŞAMALARI]
Lütfen analiz yapmadan önce şu aşamaları takip et:

1. **İlk İzlenim**: Tartışmayı genel olarak nasıl değerlendiriyorsun?
2. **Katılımcı Profilleri**: Her katılımcının karakteristik özelliklerini nasıl gözlemliyorsun?
3. **Tema Tespiti**: Hangi ana temalar ve alt konular ortaya çıkıyor?
4. **Etkileşim Kalıpları**: Katılımcılar arasındaki etkileşim nasıl gelişiyor?
5. **Sosyolojik Bulgular**: Hangi toplumsal dinamikleri fark ediyorsun?
6. **Politik Boyutlar**: Siyasi eğilimler ve görüş farklılıkları nasıl?

Bu düşünce aşamalarını detaylandır ve sonrasında analiz aşamasına geç.
"""
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            thinking_response = await simulator.llm_client.call_llm(thinking_prompt)
            
            # Show thinking process
            research_analysis_placeholder.markdown(f"""
            ### 🧠 Araştırmacının Düşünce Süreci
            
            <div style="
                background: rgba(51, 65, 85, 0.8);
                border-left: 4px solid #8b5cf6;
                padding: 1.5rem;
                border-radius: 0 10px 10px 0;
                margin: 1rem 0;
                color: #e2e8f0;
                white-space: pre-wrap;
            ">
            {thinking_response}
            </div>
            """, unsafe_allow_html=True)
            
            await asyncio.sleep(2)
            
            # Step 2: Detailed Analysis Phase
            st.markdown("---")
            analysis_placeholder = st.empty()
            
            analysis_placeholder.markdown("""
            <div class="status-card">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div class="loading-spinner"></div>
                    <div>
                        <strong>📊 Detaylı Analiz Yapılıyor...</strong><br>
                        <small>Sosyolojik ve politik bulgular raporlanıyor</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Comprehensive analysis prompt
            analysis_prompt = f"""[SİSTEM MESAJI]
Sen "Prof. Dr. Araştırmacı" adında sosyoloji ve siyaset bilimi alanında uzmanlaşmış bir akademisyensin. Düşünce sürecini tamamladın, şimdi kapsamlı bir araştırma raporu hazırla.

[ÖNCEDEN YAPILAN DÜŞÜNCE SÜRECİ]
{thinking_response}

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
- Dominant karakteristik özellikler
- Grup içindeki rolleri (lider, takipçi, muhalif, vb.)

**3. TEMA VE İÇERİK ANALİZİ**
- Ortaya çıkan ana temalar ve alt konular
- En çok tartışılan konular
- Uzlaşma ve çelişki alanları
- Değinilmeyen ama önemli olan konular

**4. ETKİLEŞİM DİNAMİKLERİ**
- Katılımcılar arası etkileşim kalıpları
- İttifak ve karşıtlık ilişkileri
- Söz alma sıklığı ve süresi analizi
- Moderatörün etkisi ve yönlendirmeleri

**5. SOSYOLOJİK BULGULAR**
- Toplumsal sınıf, yaş, cinsiyet etkilerinin analizi
- Kültürel sermaye farklılıkları
- Sosyal kimlik ve aidiyetlerin etkisi
- Grup dinamikleri ve sosyal baskı

**6. POLİTİK BOYUT ANALİZİ**
- Siyasi eğilimler ve ideolojik konumlanmalar
- Parti bağlılığı ve siyasi kimlik etkileri
- Polarizasyon ve kutuplaşma seviyeleri
- Demokratik katılım ve müzakere kalitesi

**7. SÖYLEM ANALİZİ**
- Kullanılan dil ve retorik stratejiler
- Metaforlar, semboller ve anlam çerçeveleri
- Duygusal ve rasyonel argüman dengeleri
- İkna teknikleri ve retorik gücü

**8. SOSYAL PSİKOLOJİK BOYUTLAR**
- Grup düşüncesi (groupthink) eğilimleri
- Sosyal onay arayışı ve uyum davranışları
- Önyargılar ve stereotiplerin etkisi
- Duygusal zeka ve empati seviyeleri

**9. SONUÇ VE ÖNERİLER**
- Araştırmanın temel bulguları
- Toplumsal ve politik çıkarımlar
- Politika yapıcılar için öneriler
- Gelecek araştırmalar için yönlendirmeler

**10. METODOLOJİK DEĞERLENDİRME**
- Odak grup tekniğinin etkinliği
- Veri kalitesi ve güvenilirlik
- Sınırlılıklar ve önyargı riskleri
- Genellenebilirlik düzeyi

Raporunu akademik standartlarda, objektif ve bilimsel bir dille yaz. Somut örneklerle destekle ve eleştirel bir yaklaşım sergile.
"""
            
            comprehensive_analysis = await simulator.llm_client.call_llm(analysis_prompt)
            
            # Store analysis result
            st.session_state.expert_analysis_result = comprehensive_analysis
            
            # Display the comprehensive analysis
            analysis_placeholder.markdown(f"""
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
            
            # Add download options
            st.markdown("### 📥 Araştırma Raporunu İndir")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 PDF Rapor İndir", key="download_research_pdf"):
                    generate_research_pdf_report(thinking_response, comprehensive_analysis)
            
            with col2:
                if st.button("📋 Metin Rapor İndir", key="download_research_txt"):
                    generate_research_text_report(thinking_response, comprehensive_analysis)
            
        except Exception as e:
            st.error(f"Araştırma analizi oluşturma hatası: {str(e)}")
        finally:
            try:
                loop.close()
            except:
                pass

def generate_research_pdf_report(thinking_process, analysis):
    """Generate detailed research PDF report"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Try to use Unicode font
        try:
            pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
            pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
            pdf.set_font('DejaVu', 'B', 16)
        except:
            pdf.set_font('Arial', 'B', 16)
        
        # Title
        pdf.cell(0, 15, 'UZMAN ARAŞTIRMACI ANALİZ RAPORU', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(10)
        
        # Date and info
        try:
            pdf.set_font('DejaVu', '', 12)
        except:
            pdf.set_font('Arial', '', 12)
        
        pdf.cell(0, 8, f'Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f'Araştırmacı: Prof. Dr. Sosyoloji & Siyaset Uzmanı', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)
        
        # Thinking Process
        try:
            pdf.set_font('DejaVu', 'B', 14)
        except:
            pdf.set_font('Arial', 'B', 14)
        
        pdf.cell(0, 10, 'DÜŞÜNCE SÜRECİ', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        try:
            pdf.set_font('DejaVu', '', 10)
        except:
            pdf.set_font('Arial', '', 10)
        
        pdf.multi_cell(0, 6, thinking_process[:1500] + "..." if len(thinking_process) > 1500 else thinking_process)
        pdf.ln(5)
        
        # Analysis
        try:
            pdf.set_font('DejaVu', 'B', 14)
        except:
            pdf.set_font('Arial', 'B', 14)
        
        pdf.cell(0, 10, 'DETAYLI ANALİZ RAPORU', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        try:
            pdf.set_font('DejaVu', '', 10)
        except:
            pdf.set_font('Arial', '', 10)
        
        # Split analysis into pages if needed
        analysis_text = analysis
        while len(analysis_text) > 0:
            chunk = analysis_text[:2000]  # 2000 character chunks
            pdf.multi_cell(0, 5, chunk)
            analysis_text = analysis_text[2000:]
            
            if len(analysis_text) > 0:
                pdf.add_page()
        
        # Download
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
            pdf.output(tmpfile.name)
            
            with open(tmpfile.name, 'rb') as f:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'uzman_arastirmaci_analizi_{timestamp}.pdf'
                
                st.download_button(
                    label="📥 Araştırma Raporu PDF İndir",
                    data=f.read(),
                    file_name=filename,
                    mime='application/pdf',
                    key="download_expert_pdf"
                )
        
        st.success("✅ PDF raporu hazır!")
        
    except Exception as e:
        st.error(f"PDF oluşturma hatası: {str(e)}")

def generate_research_text_report(thinking_process, analysis):
    """Generate detailed research text report"""
    try:
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        report_text = f"""
========================================
UZMAN ARAŞTIRMACI ANALİZ RAPORU
========================================

Tarih: {timestamp}
Araştırmacı: Prof. Dr. Sosyoloji & Siyaset Uzmanı
Analiz Türü: Odak Grup Tartışması Derinlemesine Analizi

========================================
DÜŞÜNCE SÜRECİ
========================================

{thinking_process}

========================================
DETAYLI ANALİZ RAPORU
========================================

{analysis}

========================================
RAPOR SONU
========================================

Bu rapor, yapay zeka destekli odak grup simülasyonu 
analizi sonucu oluşturulmuştur.
        """
        
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'uzman_arastirmaci_analizi_{timestamp_file}.txt'
        
        st.download_button(
            label="📋 Araştırma Raporu TXT İndir",
            data=report_text,
            file_name=filename,
            mime='text/plain',
            key="download_expert_txt"
        )
        
        st.success("✅ Metin raporu hazır!")
        
    except Exception as e:
        st.error(f"Metin raporu oluşturma hatası: {str(e)}")

def display_analysis_tab():
    st.markdown("### 📊 Analiz")
    if st.button("📊 Analiz Et"):
        st.info("Analiz oluşturuluyor...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(simulator.generate_analysis())
            st.session_state['analysis_result'] = analysis
            st.markdown(analysis)
            st.success("Analiz tamamlandı.")
        except Exception as e:
            st.error(f"Analiz oluşturma hatası: {str(e)}")
        finally:
            try:
                loop.close()
            except:
                pass
    elif st.session_state.get('analysis_result'):
        st.markdown(st.session_state['analysis_result'])

def display_report_tab():
    """Display report tab content"""
    st.markdown("### 📄 Rapor ve Dışa Aktarma")
    
    if not simulator.discussion_log:
        st.markdown('<div class="info-card">ℹ️ Rapor oluşturmak için önce bir simülasyon çalıştırın</div>', unsafe_allow_html=True)
        return
    
    # Report options
    st.markdown("#### ⚙️ Rapor Ayarları")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_analysis = st.checkbox("Analiz Dahil Et", value=True, key="include_analysis")
        include_timestamps = st.checkbox("Zaman Damgaları", value=True, key="include_timestamps")
    
    with col2:
        include_photos = st.checkbox("Profil Fotoğrafları", value=True, key="include_photos")
        include_stats = st.checkbox("İstatistikler", value=True, key="include_stats")
    
    with col3:
        report_language = st.selectbox("Dil", ["Türkçe", "English"], key="report_language")
        report_format = st.selectbox("Format", ["PDF", "Word", "HTML"], key="report_format")
    
    # Generate report
    st.markdown("#### 📋 Rapor Oluşturma")
    
    report_col1, report_col2 = st.columns([2, 1])
    
    with report_col1:
        if st.button("📄 Rapor Oluştur", key="generate_report"):
            generate_report(include_analysis, include_timestamps, include_photos, include_stats, report_format)
    
    with report_col2:
        if st.button("📧 E-posta Gönder", key="email_report", disabled=True):
            st.info("E-posta özelliği yakında aktif olacak")
    
    # Preview section
    if simulator.discussion_log:
        st.markdown("#### 👀 Rapor Önizleme")
        
        with st.expander("Rapor İçeriğini Görüntüle"):
            preview_report(include_analysis, include_timestamps, include_stats)

def generate_report(include_analysis, include_timestamps, include_photos, include_stats, report_format):
    """Generate and download report"""
    try:
        with st.spinner(f"{report_format} raporu oluşturuluyor..."):
            if report_format == "PDF":
                # Generate PDF
                analysis_text = st.session_state.analysis_result if include_analysis else ""
                pdf = create_enhanced_pdf(simulator.discussion_log, analysis_text, simulator.personas)
                
                # Create download
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
                
            elif report_format == "HTML":
                # Generate HTML report
                html_content = generate_html_report(include_analysis, include_timestamps, include_stats)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'odak_grup_raporu_{timestamp}.html'
                
                st.download_button(
                    label="📥 HTML İndir",
                    data=html_content,
                    file_name=filename,
                    mime='text/html',
                    key="download_html"
                )
                
                st.success("✅ HTML raporu hazır!")
            
            else:
                st.warning(f"{report_format} formatı henüz desteklenmiyor")
                
    except Exception as e:
        st.error(f"Rapor oluşturma hatası: {str(e)}")

def generate_html_report(include_analysis, include_timestamps, include_stats):
    """Generate HTML report"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Odak Grup Simülasyonu Raporu</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; text-align: center; border-bottom: 3px solid #667eea; padding-bottom: 20px; }}
            h2 {{ color: #667eea; margin-top: 30px; }}
            .message {{ margin: 20px 0; padding: 15px; border-radius: 8px; background: #f8f9fa; border-left: 4px solid #667eea; }}
            .moderator {{ border-left-color: #f093fb; background: #fef7ff; }}
            .speaker {{ font-weight: bold; color: #333; }}
            .timestamp {{ color: #666; font-size: 0.9em; float: right; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: #667eea; color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Odak Grup Simülasyonu Raporu</h1>
            <p><strong>Tarih:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            
            <h2>👥 Katılımcılar</h2>
            <ul>
    """
    
    # Add participants
    for persona in simulator.personas:
        html_content += f"<li><strong>{persona.name}</strong> - {persona.role}</li>"
    
    html_content += "</ul>"
    
    # Add statistics if requested
    if include_stats:
        total_messages = len(simulator.discussion_log)
        persona_messages = len([entry for entry in simulator.discussion_log if entry['speaker'] != 'Moderatör'])
        total_words = sum(len(entry['message'].split()) for entry in simulator.discussion_log)
        
        html_content += f"""
            <h2>📊 İstatistikler</h2>
            <div class="stats">
                <div class="stat-card">
                    <h3>{total_messages}</h3>
                    <p>Toplam Mesaj</p>
                </div>
                <div class="stat-card">
                    <h3>{persona_messages}</h3>
                    <p>Persona Mesajları</p>
                </div>
                <div class="stat-card">
                    <h3>{total_words}</h3>
                    <p>Toplam Kelime</p>
                </div>
            </div>
        """
    
    # Add conversation
    html_content += "<h2>💬 Tartışma</h2>"
    
    for entry in simulator.discussion_log:
        speaker = entry['speaker']
        message = html.escape(entry['message'])
        timestamp = format_message_time(entry['timestamp']) if include_timestamps else ""
        
        css_class = "moderator" if speaker == "Moderatör" else ""
        timestamp_html = f'<span class="timestamp">{timestamp}</span>' if timestamp else ""
        
        html_content += f"""
            <div class="message {css_class}">
                <div class="speaker">{speaker}</div>
                {timestamp_html}
                <div>{message}</div>
            </div>
        """
    
    # Add analysis if requested
    if include_analysis and st.session_state.analysis_result:
        analysis_html = html.escape(st.session_state.analysis_result).replace('\n', '<br>')
        html_content += f"""
            <h2>📊 Analiz</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; line-height: 1.6;">
                {analysis_html}
            </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    return html_content

def preview_report(include_analysis, include_timestamps, include_stats):
    """Preview report content"""
    st.markdown("**📋 Rapor İçeriği:**")
    
    # Basic info
    st.write(f"📅 **Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    st.write(f"👥 **Katılımcı Sayısı:** {len(simulator.personas)}")
    st.write(f"💬 **Toplam Mesaj:** {len(simulator.discussion_log)}")
    
    if include_stats:
        st.write("📊 **İstatistikler dahil edilecek**")
    
    if include_analysis:
        st.write("🔍 **Analiz dahil edilecek**")
    
    if include_timestamps:
        st.write("⏰ **Zaman damgaları dahil edilecek**")
    
    # Sample messages
    st.write("**💬 Mesaj Örnekleri:**")
    for entry in simulator.discussion_log[:3]:
        timestamp = f" ({format_message_time(entry['timestamp'])})" if include_timestamps else ""
        st.write(f"• **{entry['speaker']}**{timestamp}: {entry['message'][:100]}...")

def reset_simulation():
    """Reset simulation state"""
    st.session_state.simulation_running = False
    st.session_state.stop_simulation = False
    st.session_state.analysis_result = ""
    st.session_state.agenda_loaded = False
    
    # Clear simulator data
    simulator.discussion_log = []
    simulator.memory = {}
    simulator.mcp_logs = []
    simulator.agenda_items = []

if __name__ == "__main__":
    main()