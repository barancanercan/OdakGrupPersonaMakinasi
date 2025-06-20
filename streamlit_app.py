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
from random import choice
import random
import sys

# Import main modules with error handling
try:
    import main
    from main import simulator
    MAIN_AVAILABLE = True
except Exception as e:
    st.error(f"❌ Ana modül yüklenemedi: {e}")
    st.info("🔧 main.py dosyasını ve bağımlılıkları kontrol edin")
    MAIN_AVAILABLE = False
    simulator = None

# Sayfa yapılandırması
st.set_page_config(
    page_title="Odak Grup Simülasyonu",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern CSS stilleri
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Variables */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --dark-bg: #0a0e1a;
        --card-bg: rgba(15, 23, 42, 0.8);
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #64748b;
        --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        --shadow-xl: 0 35px 60px -12px rgba(0, 0, 0, 0.35);
    }
    
    /* Body & App */
    .stApp {
        background: var(--dark-bg);
        background-image: 
            radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(240, 147, 251, 0.05) 0%, transparent 50%);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main Container */
    .main .block-container {
        padding: 3rem 2rem;
        max-width: 1400px;
    }
    
    /* Glass morphism containers */
    .glass-container {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-lg);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-container:hover {
        background: rgba(255, 255, 255, 0.08);
        box-shadow: var(--shadow-xl);
        transform: translateY(-2px);
    }
    
    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
        margin-bottom: 3rem;
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 32px;
        border: 1px solid var(--glass-border);
        position: relative;
        overflow: hidden;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: var(--primary-gradient);
        opacity: 0.1;
        z-index: -1;
    }
    
    /* Typography */
    h1 {
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: clamp(2.5rem, 5vw, 4rem);
        font-weight: 700;
        margin-bottom: 1rem;
        letter-spacing: -0.025em;
    }
    
    h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        position: relative;
        padding-bottom: 0.5rem;
    }
    
    h2::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 3px;
        background: var(--primary-gradient);
        border-radius: 2px;
    }
    
    .subtitle {
        color: var(--text-secondary);
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    
    /* Modern Buttons */
    .stButton > button {
        width: 100%;
        margin: 0.75rem 0;
        padding: 1rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        background: var(--primary-gradient);
        color: var(--text-primary);
        border: none;
        border-radius: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
        color: var(--text-muted);
        box-shadow: none;
        transform: none;
        cursor: not-allowed;
    }
    
    /* Secondary Button Style */
    .secondary-button {
        background: var(--glass-bg) !important;
        border: 2px solid var(--glass-border) !important;
        backdrop-filter: blur(10px);
    }
    
    .secondary-button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(102, 126, 234, 0.5) !important;
    }
    
    /* File Uploader */
    .stFileUploader {
        background: var(--glass-bg);
        border: 2px dashed var(--glass-border);
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .stFileUploader::before {
        content: '📁';
        font-size: 3rem;
        display: block;
        margin-bottom: 1rem;
        opacity: 0.7;
    }
    
    .stFileUploader:hover {
        border-color: rgba(102, 126, 234, 0.6);
        background: rgba(255, 255, 255, 0.08);
        transform: scale(1.02);
    }
    
    .stFileUploader label {
        color: var(--text-secondary) !important;
        font-weight: 500;
    }
    
    /* Status Cards */
    .status-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .status-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: var(--primary-gradient);
    }
    
    .status-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    /* Message Bubbles */
    .message-bubble {
        margin: 1.5rem 0;
        padding: 0;
        border-radius: 24px;
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        overflow: hidden;
        transition: all 0.3s ease;
        animation: slideInUp 0.5s ease;
    }
    
    .message-bubble:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .message-header {
        display: flex;
        align-items: center;
        padding: 1.5rem 2rem 1rem 2rem;
        background: rgba(255, 255, 255, 0.03);
        border-bottom: 1px solid var(--glass-border);
    }
    
    .profile-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        margin-right: 1rem;
        object-fit: cover;
        border: 3px solid transparent;
        background: var(--primary-gradient);
        background-clip: padding-box;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .profile-avatar::before {
        content: '';
        position: absolute;
        inset: -3px;
        border-radius: 50%;
        background: var(--primary-gradient);
        z-index: -1;
    }
    
    .profile-avatar:hover {
        transform: scale(1.1) rotate(5deg);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    .message-info {
        flex: 1;
    }
    
    .speaker-name {
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
        font-size: 1.1rem;
    }
    
    .message-time {
        color: var(--text-muted);
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .message-content {
        padding: 1.5rem 2rem 2rem 2rem;
        color: var(--text-secondary);
        line-height: 1.7;
        font-size: 1rem;
    }
    
    .moderator-message {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
        border-left: 4px solid #3b82f6;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: var(--primary-gradient);
        border-radius: 10px;
        height: 12px;
        transition: all 0.3s ease;
    }
    
    .stProgress > div {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    
    /* Info Boxes */
    .stInfo, .stSuccess, .stError, .stWarning {
        border-radius: 16px !important;
        border: none !important;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%) !important;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%) !important;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%) !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%) !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: var(--card-bg);
        backdrop-filter: blur(20px);
        border-right: 1px solid var(--glass-border);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--glass-bg) !important;
        border-radius: 12px !important;
        border: 1px solid var(--glass-border) !important;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        transform: translateY(-1px);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--glass-bg);
        border-radius: 16px;
        padding: 0.5rem;
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        margin: 0 0.25rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-gradient) !important;
        color: white;
    }
    
    /* Metrics */
    .metric-card {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        margin: 0.5rem 0;
    }
    
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Animations */
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: calc(200px + 100%) 0; }
    }
    
    .loading-shimmer {
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        background-size: 200px 100%;
        animation: shimmer 1.5s infinite;
    }
    
    /* Status Indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        backdrop-filter: blur(10px);
    }
    
    .status-running {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-stopped {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .status-loading {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.2) 100%);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-gradient);
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 2rem 1rem;
        }
        
        .glass-container {
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        h1 {
            font-size: 2.5rem;
        }
        
        .hero-section {
            padding: 3rem 1.5rem;
        }
        
        .profile-avatar {
            width: 40px;
            height: 40px;
        }
        
        .message-header {
            padding: 1rem 1.5rem 0.75rem 1.5rem;
        }
        
        .message-content {
            padding: 1rem 1.5rem 1.5rem 1.5rem;
        }
    }
    
    @media (max-width: 480px) {
        .stButton > button {
            padding: 0.875rem 1.5rem;
            font-size: 0.9rem;
        }
        
        .glass-container {
            padding: 1rem;
        }
        
        .stFileUploader {
            padding: 2rem 1rem;
        }
    }
    
    /* Dark mode specific adjustments */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: var(--dark-bg);
        }
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .glass-container {
            border: 2px solid var(--text-primary);
        }
        
        .stButton > button {
            border: 2px solid transparent;
        }
    }
    
    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Utility functions (same as before)
def run_async_function(async_func):
    """Async fonksiyonları güvenli şekilde çalıştır"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(async_func)
    except Exception as e:
        st.error(f"❌ Async execution error: {str(e)}")
        return None
    finally:
        pass

def safe_file_operations(uploaded_file):
    """Dosya işlemlerini güvenli şekilde yap"""
    try:
        temp_dir = tempfile.gettempdir()
        data_dir = os.path.join(temp_dir, 'streamlit_focus_group')
        os.makedirs(data_dir, exist_ok=True)
        
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', uploaded_file.name)
        file_path = os.path.join(data_dir, safe_filename)
        
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        return file_path
    except Exception as e:
        st.error(f"❌ Dosya işlemi hatası: {str(e)}")
        return None

def get_base64_from_file(file_path):
    """Dosyayı base64'e çevir"""
    try:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        st.error(f"❌ Görsel kodlama hatası {file_path}: {e}")
        return None

def get_persona_pic_safe(persona_name):
    """Persona profil fotoğrafını güvenli şekilde al"""
    pp_dir = 'personas_pp'
    if not os.path.exists(pp_dir):
        return None

    base_name = persona_name.lower().replace(' ', '_')
    char_map = {'ç':'c', 'ğ':'g', 'ı':'i', 'ö':'o', 'ş':'s', 'ü':'u'}
    ascii_name = base_name
    for tr_char, en_char in char_map.items():
        ascii_name = ascii_name.replace(tr_char, en_char)

    for ext in ['.jpg', '.png', '.jpeg']:
        pic_path = os.path.join(pp_dir, f"{base_name}{ext}")
        if os.path.exists(pic_path):
            return pic_path
        
        pic_path = os.path.join(pp_dir, f"{ascii_name}{ext}")
        if os.path.exists(pic_path):
            return pic_path

    return None

def create_pdf_with_fonts(conversation, analysis, personas):
    """PDF oluştur - geliştirilmiş font desteği ile"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    font_paths = {
        'dejavu': './DejaVuSans.ttf',
        'dejavu_bold': './DejaVuSans-Bold.ttf',
        'system_dejavu': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'system_dejavu_bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    }
    
    font_available = False
    
    for path_type in ['dejavu', 'system_dejavu']:
        regular_path = font_paths[path_type]
        bold_path = font_paths[path_type + '_bold'] if path_type == 'dejavu' else font_paths['system_dejavu_bold']
        
        if os.path.exists(regular_path) and os.path.exists(bold_path):
            try:
                pdf.add_font('DejaVu', '', regular_path, uni=True)
                pdf.add_font('DejaVu', 'B', bold_path, uni=True)
                pdf.set_font('DejaVu', '', 16)
                font_available = True
                break
            except Exception as e:
                continue
    
    if not font_available:
        try:
            pdf.set_font('Arial', '', 16)
        except:
            pdf.set_font('Times', '', 16)
    
    # PDF content generation...
    pdf.cell(0, 10, 'Odak Grup Simülasyonu Raporu', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)
    
    pdf.set_font_size(12)
    pdf.cell(0, 8, f'Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    
    if personas:
        pdf.set_font_size(14)
        pdf.cell(0, 10, 'Katılımcılar:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font_size(12)
        for persona in personas:
            pdf.cell(0, 8, f'• {persona.name} ({persona.role})', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)
    
    return pdf

def render_status_indicator(status):
    """Modern durum göstergesini render et"""
    status_config = {
        'running': ('🟢', 'status-running', 'Çalışıyor'),
        'stopped': ('🔴', 'status-stopped', 'Durduruldu'),
        'paused': ('🟡', 'status-loading', 'Beklemede'),
        'error': ('❌', 'status-stopped', 'Hata'),
        'loading': ('🔄', 'status-loading', 'Yükleniyor')
    }
    
    icon, css_class, text = status_config.get(status, ('⚪', 'status-stopped', status.title()))
    
    return f'<div class="status-indicator {css_class}">{icon} <span>{text}</span></div>'

def format_api_stats(stats):
    """API istatistiklerini modern formatta göster"""
    if not stats:
        return "📊 İstatistik yok"
    
    success_rate = stats.get('success_rate', 0)
    total_requests = stats.get('total_requests', 0)
    successful_requests = stats.get('successful_requests', 0)
    failed_requests = stats.get('failed_requests', 0)
    
    return f"""
    <div class="metric-card">
        <div class="metric-value">{success_rate:.1f}%</div>
        <div class="metric-label">Başarı Oranı</div>
    </div>
    
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
        <div class="metric-card">
            <div class="metric-value">{total_requests}</div>
            <div class="metric-label">Toplam</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{successful_requests}</div>
            <div class="metric-label">Başarılı</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{failed_requests}</div>
            <div class="metric-label">Başarısız</div>
        </div>
    </div>
    """