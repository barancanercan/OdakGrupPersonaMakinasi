import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from dataclasses import dataclass, asdict
import google.generativeai as genai
from dotenv import load_dotenv
import re
import time
import base64

# Streamlit import - deployment için
try:
    import streamlit as st
except ImportError:
    st = None

# CAMEL imports - deployment için kontrol
try:
    from camel.agents import ChatAgent
    from camel.messages import BaseMessage
    from camel.types import RoleType
    CAMEL_AVAILABLE = True
except ImportError:
    CAMEL_AVAILABLE = False
    logging.warning("CAMEL-AI not available. Some features may be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

mcp_logs = []

def get_api_key():
    """API anahtarını güvenli şekilde al"""
    # Streamlit secrets öncelikli
    if st and hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
        return st.secrets['GEMINI_API_KEY']
    # Environment variable fallback
    return os.getenv('GEMINI_API_KEY')

def get_api_key_2():
    """İkinci API anahtarını güvenli şekilde al"""
    if st and hasattr(st, 'secrets') and 'GEMINI_API_KEY_2' in st.secrets:
        return st.secrets['GEMINI_API_KEY_2']
    return os.getenv('GEMINI_API_KEY_2')

def check_required_files():
    """Deployment için gerekli dosyaları kontrol et"""
    required_files = [
        'personas/elif.json',
        'personas/hatice_teyze.json',
        'personas/kenan_bey.json',
        'personas/tugrul_bey.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Eksik dosyalar: {missing_files}")
        if st:
            st.error(f"❌ Eksik dosyalar: {missing_files}")
            st.info("📁 Lütfen şu klasörlerin var olduğundan emin olun: personas/, personas_pp/")
            st.stop()
        return False
    return True

@dataclass
class Persona:
    name: str
    bio: list
    lore: list
    knowledge: list
    topics: list
    style: dict
    adjectives: list
    modelProvider: str = None
    clients: list = None
    profile_pic: str = None
    role: str = None
    personality: str = None

    @classmethod
    def from_json(cls, json_file: str):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Persona dosyası bulunamadı: {json_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse hatası {json_file}: {e}")
            raise
            
        name = data.get('name')
        if not name:
            raise ValueError(f"Persona adı eksik: {json_file}")
            
        # Profil fotoğrafı dosya adını oluştur
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().replace(' ', '_'))
        
        # Türkçe karakter dönüşümü
        char_map = {'ç':'c', 'ğ':'g', 'ı':'i', 'ö':'o', 'ş':'s', 'ü':'u'}
        ascii_name = safe_name
        for tr_char, en_char in char_map.items():
            ascii_name = ascii_name.replace(tr_char, en_char)
        
        base_path = 'personas_pp/'
        profile_pic = None
        
        # Önce orijinal isimle dene
        for ext in ['.jpg', '.png', '.jpeg']:
            pic_path = f"{base_path}{safe_name}{ext}"
            if os.path.exists(pic_path):
                profile_pic = pic_path
                break
        
        # Bulamazsa ASCII versiyonla dene
        if not profile_pic:
            for ext in ['.jpg', '.png', '.jpeg']:
                pic_path = f"{base_path}{ascii_name}{ext}"
                if os.path.exists(pic_path):
                    profile_pic = pic_path
                    break
        
        return cls(
            name=name,
            bio=data.get('bio', []),
            lore=data.get('lore', []),
            knowledge=data.get('knowledge', []),
            topics=data.get('topics', []),
            style=data.get('style', {}),
            adjectives=data.get('adjectives', []),
            modelProvider=data.get('modelProvider'),
            clients=data.get('clients'),
            profile_pic=profile_pic,
            role=data.get('role', 'Katılımcı'),
            personality=data.get('personality', 'Nötr')
        )

@dataclass
class AgendaItem:
    type: str
    link: str
    title: str
    content: str
    comments: str
    score: float = 0.0

class LLMClient:
    def __init__(self):
        self.api_key = get_api_key()
        self.api_key_2 = get_api_key_2()
        
        if not self.api_key:
            error_msg = "🔑 GEMINI_API_KEY bulunamadı!"
            logger.error(error_msg)
            if st:
                st.error(error_msg)
                st.info("📝 API anahtarını Streamlit secrets veya .env dosyasında tanımlayın")
            raise ValueError("API key not found")
            
        self.current_api_key = self.api_key
        self.last_switch_time = time.time()
        self.switch_interval = 30
        self.retry_delay = 15
        self.max_retries = 3
        self.request_count = 0
        self.last_request_time = time.time()
        self.min_request_interval = 4
        self.request_log = []

    def _switch_api_key(self):
        """API anahtarları arasında geçiş yapar"""
        if not self.api_key_2:
            return
            
        current_time = time.time()
        if current_time - self.last_switch_time >= self.switch_interval:
            self.current_api_key = self.api_key_2 if self.current_api_key == self.api_key else self.api_key
            self.last_switch_time = current_time
            logger.info(f"API anahtarı değiştirildi")
            self.request_count = 0

    def _log_request(self, success: bool, error: str = None):
        """İstek loglarını tutar"""
        log_entry = {
            'timestamp': datetime.now(),
            'api_key': self.current_api_key[:10] + '...' if self.current_api_key else 'None',
            'request_count': self.request_count,
            'success': success,
            'error': error
        }
        self.request_log.append(log_entry)
        
        # Son 100 logu tut
        if len(self.request_log) > 100:
            self.request_log = self.request_log[-100:]

    async def call_llm(self, prompt: str, max_retries: int = 3) -> str:
        """Call the LLM with retry logic and API key switching"""
        if not self.current_api_key:
            return "API anahtarı bulunamadı."
            
        for attempt in range(max_retries):
            try:
                # İstekler arası minimum süre kontrolü
                current_time = time.time()
                time_since_last_request = current_time - self.last_request_time
                if time_since_last_request < self.min_request_interval:
                    wait_time = self.min_request_interval - time_since_last_request
                    logger.info(f"İstekler arası bekleme: {wait_time:.1f} saniye")
                    await asyncio.sleep(wait_time)

                self._switch_api_key()
                self.request_count += 1
                self.last_request_time = time.time()
                
                logger.info(f"LLM isteği gönderiliyor (Deneme {attempt + 1}/{max_retries}, İstek #{self.request_count})")
                
                genai.configure(api_key=self.current_api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=3072,
                    )
                )
                
                if response.text:
                    self._log_request(success=True)
                    return response.text
                else:
                    logger.warning("Empty response from LLM")
                    self._log_request(success=False, error="Empty response")
                    return "Üzgünüm, şu anda yanıt veremiyorum."
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"LLM call failed: {error_msg}")
                self._log_request(success=False, error=error_msg)
                
                if "429" in error_msg or "quota" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)
                        logger.warning(f"Rate limit aşıldı. {wait_time} saniye bekleniyor...")
                        if st:
                            st.warning(f"⏳ API kotası doldu, {wait_time} saniye bekleniyor...")
                        await asyncio.sleep(wait_time)
                        continue
                
                if "network" in error_msg.lower() or "connection" in error_msg.lower():
                    if st:
                        st.error("🌐 İnternet bağlantısı sorunu")
                
                if attempt == max_retries - 1:
                    if st:
                        st.error("❌ LLM servisine ulaşılamıyor")
                    return "Üzgünüm, şu anda yanıt veremiyorum. Lütfen daha sonra tekrar deneyin."
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    def get_request_stats(self) -> dict:
        """İstek istatistiklerini döndürür"""
        total_requests = len(self.request_log)
        successful_requests = sum(1 for log in self.request_log if log['success'])
        failed_requests = total_requests - successful_requests
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'current_request_count': self.request_count,
            'last_request_time': self.last_request_time
        }

class MCPThinkingAgent:
    def __init__(self, llm_client: LLMClient, simulator=None):
        self.llm_client = llm_client
        self.simulator = simulator
    
    async def score_agenda_item(self, persona: Persona, item: AgendaItem) -> float:
        """Score an agenda item based on persona's perspective"""
        prompt = f"""[SİSTEM MESAJI]
Sen bir "İçerik Puanlama Uzmanı"sın. Sana bir persona profili ve bir gündem maddesi verilecektir. Bu persona rolüne bürünerek, gündem maddesine 1'den 10'a kadar bir "ilgi ve hatırlama" puanı ver.

[PERSONA PROFİLİ]
İsim: {persona.name}
Rol: {persona.role}
Kişilik: {persona.personality}
Biyo: {persona.bio}
Geçmiş: {persona.lore}
Bilgi: {persona.knowledge}
Konular: {persona.topics}
Stil: {persona.style}
Sıfatlar: {persona.adjectives}

[GÜNDEM MADDESİ]
Başlık: {item.title}
İçerik: {item.content}
Yorumlar: {item.comments}

[TALİMATLAR]
1. Yukarıdaki persona profilini ve gündem maddesini dikkatlice oku.
2. Personanın rolü, kişiliği ve diğer özelliklerini referans alarak, bu gündem maddesinin persona için ne kadar alakalı ve önemli olduğunu değerlendir.
3. Yanıtın sadece 1 ile 10 arasında bir sayı olsun. Başka hiçbir metin veya açıklama ekleme.
"""
        
        response = await self.llm_client.call_llm(prompt)
        try:
            # Extract the first number from the response
            score_match = re.search(r'\d+', response)
            if score_match:
                score = float(score_match.group())
                return min(max(score, 1), 10)
            else:
                logger.warning(f"Score parsing failed for response: {response}")
                return 5.0
        except Exception as e:
            logger.error(f"Score parsing error: {e}")
            return 5.0
    
    async def validate_response(self, persona: Persona, context: str, response_draft: str) -> str:
        """Validate and improve persona response for consistency"""
        prompt = f"""[SİSTEM MESAJI]
Sen bir "Karakter Tutarlılık Kontrolörü"sün. Sana bir persona profili, mevcut tartışma bağlamı ve personanın olası bir yanıt taslağı verilecektir. Bu taslağın personanın karakterine, tarzına ve önceki yorumlarına tam olarak uygun olup olmadığını değerlendir. Gerektiğinde taslağı iyileştirerek daha tutarlı bir yanıt oluştur.

[PERSONA PROFİLİ]
İsim: {persona.name}
Biyo: {persona.bio}
Geçmiş: {persona.lore}
Bilgi: {persona.knowledge}
Konular: {persona.topics}
Stil: {persona.style}
Sıfatlar: {persona.adjectives}

[TARTIŞMA BAĞLAMI]
{context}

[PERSONANIN Olası YANITI (TASLAK)]
{response_draft}

[TALİMATLAR]
1. Personanın "bio", "lore", "knowledge", "topics", "style" ve "adjectives" alanlarını referans alarak, taslağın bu özelliklere uygunluğunu değerlendir.
2. Taslak, personanın mevcut bilgi birikimi veya görüşleriyle çelişiyor mu?
3. Taslak, personanın tanımlanmış konuşma tarzına ("all", "chat", "post") ve sıfatlarına uygun mu?
4. Taslak, tartışmanın genel akışına ve mantığına uygun mu?
5. Eğer taslak tutarlı ve uygunsa, taslağı olduğu gibi tekrar et.
6. Eğer taslak tutarsızsa veya geliştirilmesi gerekiyorsa, personanın karakterine tam olarak uygun, mantıklı ve bağlamla uyumlu yeni bir yanıt oluştur. Yanıt, sadece personanın söyleyeceği sözler olmalıdır, başka bir açıklama veya ekleme yapma.
"""
        response = await self.llm_client.call_llm(prompt)
        log_entry = {"type": "validate", "prompt": prompt, "response": response}
        mcp_logs.append(log_entry)
        if self.simulator is not None and hasattr(self.simulator, 'mcp_logs'):
            self.simulator.mcp_logs.append(log_entry)
        return response.strip()

    async def summarize_for_persona(self, persona, agenda_item, score):
        prompt = f"""[SİSTEM MESAJI]
Sen bir \"Hatırlama Uzmanı\"sın. Sana bir persona profili, bir haber ve bu personanın haberi okuma dikkat seviyesi (1-10) verilecek. Lütfen, bu persona bu haberi bu dikkat seviyesiyle okusa, neleri hatırlar, neleri unutur, hangi ana fikri aklında tutar, özetle. Yanıtın sadece persona'nın aklında kalanlar olsun.

[PERSONA PROFİLİ]
İsim: {persona.name}
Biyo: {persona.bio}
Geçmiş: {persona.lore}
Bilgi: {persona.knowledge}
Konular: {persona.topics}
Stil: {persona.style}
Sıfatlar: {persona.adjectives}

[GÜNDEM MADDESİ]
Başlık: {agenda_item.title}
İçerik: {agenda_item.content}
Yorumlar: {agenda_item.comments}

[DİKKAT SEVİYESİ]: {score}

[TALİMATLAR]
- Dikkat seviyesi düşükse, önemli detayları atla veya unut.
- Dikkat seviyesi ortaysa, ana fikri ve bazı detayları hatırla.
- Dikkat seviyesi yüksekse, çoğu detayı ve ana fikri hatırla.
- Yanıtın sadece persona'nın aklında kalanlar olsun, başka açıklama ekleme.
"""
        response = await self.llm_client.call_llm(prompt)
        log_entry = {"type": "memory", "prompt": prompt, "response": response}
        mcp_logs.append(log_entry)
        if self.simulator is not None and hasattr(self.simulator, 'mcp_logs'):
            self.simulator.mcp_logs.append(log_entry)
        return response.strip()

# CAMEL-AI kullanılamıyorsa basit bir agent sınıfı
class SimpleChatAgent:
    def __init__(self, system_message):
        self.system_message = system_message

class FocusGroupAgent:
    def __init__(self, persona: Persona, llm_client: LLMClient, mcp_agent: MCPThinkingAgent):
        self.persona = persona
        self.llm_client = llm_client
        self.mcp_agent = mcp_agent
        self.conversation_history = []
        
        # Create system message for persona
        self.system_message = self._create_system_message()
        
        # CAMEL-AI varsa kullan, yoksa basit versiyona geç
        if CAMEL_AVAILABLE:
            try:
                from camel.agents import ChatAgent
                from camel.messages import BaseMessage
                # CAMEL agent'ı başlatmaya çalış
                pass
            except Exception as e:
                logger.warning(f"CAMEL agent başlatılamadı: {e}")
    
    def _create_system_message(self) -> str:
        content = f"""[SİSTEM MESAJI]
Sen {self.persona.name} adlı personasın. Sana ait tüm kişisel bilgiler, geçmiş, bilgi alanları, konuşma tarzı ve sıfatlar aşağıda verilmiştir. Odak grup tartışmasında, bu karakterine tamamen uygun bir şekilde hareket etmeli ve konuşmalısın.

[PERSONA PROFİLİ]
İsim: {self.persona.name}
Biyo: {self.persona.bio}
Geçmiş: {self.persona.lore}
Bilgi: {self.persona.knowledge}
Konular: {self.persona.topics}
Stil: {self.persona.style}
Sıfatlar: {self.persona.adjectives}

[TALİMATLAR]
1. "bio", "lore", "knowledge", "topics", "style" ve "adjectives" alanlarını her yanıtında içselleştir.
2. Yanıtların, personanın yaşından, eğitiminden, sosyo-ekonomik durumundan ve inançlarından etkilenmiş olmalıdır.
3. "style" (all, chat, post) ve "adjectives" (örneğin "Teknolojiden bi haber", "Saf ve cahil", "Kolay Kandırılabilir") özelliklerini konuşma tarzına ve kelime seçimine yansıt.
4. Gündem maddesine ve diğer personaların yorumlarına, kendi personanın bakış açısıyla tepki ver.
5. Yanıtların doğal ve gerçekçi olmalı, yapay zeka tarafından üretildiği anlaşılmamalıdır.
6. Sadece personanın söyleyeceği sözleri yaz. Açıklama veya meta-yorum yapma.
"""
        return content
    
    async def generate_response(self, context: str, agenda_item: AgendaItem) -> str:
        """Generate persona response with MCP validation"""
        # Persona'nın bu haber için belleğindeki özeti kullan
        try:
            from main import simulator
            memory_key = (self.persona.name, agenda_item.title)
            memory_summary = simulator.memory.get(memory_key, None)
        except:
            memory_summary = None
            
        if memory_summary:
            prompt = f"""{self.system_message}

[TARTIŞMA BAĞLAMI]
{context}
Şu anki gündem maddesi (senin hatırladığın kadarıyla): {memory_summary}

[TALİMATLAR]
1. "bio", "lore", "knowledge", "topics", "style" ve "adjectives" alanlarını her yanıtında içselleştir.
2. Yanıtların, personanın yaşından, eğitiminden, sosyo-ekonomik durumundan ve inançlarından etkilenmiş olmalıdır.
3. "style" (all, chat, post) ve "adjectives" (örneğin "Teknolojiden bi haber", "Saf ve cahil", "Kolay Kandırılabilir") özelliklerini konuşma tarzına ve kelime seçimine yansıt.
4. Gündem maddesine ve diğer personaların yorumlarına, kendi personanın bakış açısıyla tepki ver.
5. Diğer personaları ikna etmeye çalış. Fikir ayrılığı olduğunda karşı çık, gerekirse duygusal tepki ver, kız, yüksel. Tartışmacı ve canlı bir üslup kullan.
6. Yanıtların doğal ve gerçekçi olmalı, yapay zeka tarafından üretildiği anlaşılmamalıdır.
7. Sadece personanın söyleyeceği sözleri yaz. Açıklama veya meta-yorum yapma.
"""
        else:
            # Bellek yoksa eski davranış
            prompt = f"""{self.system_message}

[TARTIŞMA BAĞLAMI]
{context}
Şu anki gündem maddesi: {agenda_item.title} - {agenda_item.content}
"""
        
        response = await self.llm_client.call_llm(prompt)
        return response.strip()

class ModeratorAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.conversation_history = []
    
    async def start_discussion(self, agenda_item: AgendaItem, first_persona: str) -> str:
        """Start the discussion"""
        prompt = f"""[SİSTEM MESAJI]
Sen bir "Odak Grup Moderatörü"sün. Amacın, sana verilen gündem maddesi etrafında personalar arasında verimli ve adil bir tartışma ortamı sağlamaktır. Tarafsız kalmalı, tüm personalara eşit söz hakkı tanımalı ve tartışmanın belirlenen gündemden sapmamasını sağlamalısın.

[GÜNDEM MADDESİ]
Başlık: {agenda_item.title}
İçerik: {agenda_item.content}

Tartışmayı "Merhaba, bugün [{agenda_item.title}] konusunu konuşmak üzere toplandık. Bu konuda ilk sözü {first_persona}'ya vermek istiyorum." gibi bir cümleyle başlat.
"""
        
        response = await self.llm_client.call_llm(prompt)
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'speaker': 'Moderatör',
            'message': response
        })
        return response
    
    async def give_turn(self, previous_persona: str, next_persona: str) -> str:
        """Give turn to next persona"""
        prompt = f"""Sen moderatörsün. {previous_persona} konuştu, şimdi sırayı {next_persona}'ya ver. Kısa ve öz bir geçiş cümlesi söyle."""
        
        response = await self.llm_client.call_llm(prompt)
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'speaker': 'Moderatör',
            'message': response
        })
        return response

class OverseerAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def analyze_discussion(self, full_discussion: str) -> str:
        """Analyze the complete discussion"""
        prompt = f"""[SİSTEM MESAJI]
Sen bir "Siyaset ve Sosyoloji Uzmanı"sın. Sana bir odak grup tartışmasının tam metni verilecektir. Bu metni derinlemesine analiz et ve aşağıdaki kriterlere göre kapsamlı bir rapor oluştur.

[ODAK GRUP TARTIŞMA METNİ]
{full_discussion}

[RAPOR TALİMATLARI]
Aşağıdaki başlıkları kullanarak detaylı bir rapor hazırla:

1. **Giriş:** Tartışmanın konusu ve katılımcıların (personaların) kısa tanıtımı.
2. **Ana Tartışma Noktaları ve Temalar:** Tartışmada öne çıkan ana konular, alt başlıklar ve tekrar eden temalar nelerdi?
3. **Persona Bazlı Katkılar ve Bakış Açıları:**
   * Her bir personanın tartışmaya nasıl bir katkı sağladığını ve hangi bakış açılarını temsil ettiğini detaylandır.
   * Personaların kendi karakter özellikleriyle ne kadar tutarlı davrandığını değerlendir.
4. **İnteraksiyon Analizi:**
   * Personalar arasında belirgin anlaşmazlık veya fikir birliği noktaları nelerdi?
   * Hangi personalar birbirini destekledi, hangileri karşı çıktı? Neden?
   * Moderatörün rolü tartışmayı nasıl etkiledi?
5. **Sosyolojik ve Politik Analizler:**
   * Tartışmada gözlemlenen sosyal veya kültürel eğilimler nelerdir?
   * Katılımcıların politik görüşleri ve bu görüşlerin tartışmaya yansımaları nasıl oldu?
   * Ortaya çıkan genel kamuoyu eğilimleri veya toplumsal hassasiyetler var mıydı?
6. **Beklenmedik Bulgular / Aykırı Görüşler:** Beklenenin dışında ortaya çıkan yorumlar veya bakış açıları oldu mu?
7. **Sonuç ve Öneriler:** Tartışmanın genel özeti ve elde edilen ana bulgular. Gelecekteki araştırmalar veya politika belirleme için olası çıkarımlar ve öneriler.

Raporunu akademik ve objektif bir dille yaz. Analizlerini somut örneklerle destekle.
"""
        
        analysis = await self.llm_client.call_llm(prompt)
        return analysis

class FocusGroupSimulator:
    def __init__(self):
        try:
            self.llm_client = LLMClient()
            self.mcp_agent = MCPThinkingAgent(self.llm_client, self)
            self.moderator = ModeratorAgent(self.llm_client)
            self.overseer = OverseerAgent(self.llm_client)
            
            self.personas: List[Persona] = []
            self.agents: List[FocusGroupAgent] = []
            self.agenda_items: List[AgendaItem] = []
            self.discussion_log = []
            self.is_running = False
            self.memory = {}
            self.mcp_logs = []
            
            # Create necessary directories
            os.makedirs("personas", exist_ok=True)
            os.makedirs("personas_pp", exist_ok=True)
            os.makedirs("data", exist_ok=True)
            
            # Load personas if files exist
            self.load_personas()
            
        except Exception as e:
            logger.error(f"Simulator initialization failed: {e}")
            if st:
                st.error(f"❌ Simulator başlatılamadı: {e}")
            raise
    
    def load_personas(self):
        """Load personas from JSON files"""
        persona_files = [
            'personas/elif.json',
            'personas/hatice_teyze.json',
            'personas/kenan_bey.json',
            'personas/tugrul_bey.json'
        ]
        
        loaded_count = 0
        for file_path in persona_files:
            if os.path.exists(file_path):
                try:
                    persona = Persona.from_json(file_path)
                    self.personas.append(persona)
                    agent = FocusGroupAgent(persona, self.llm_client, self.mcp_agent)
                    self.agents.append(agent)
                    loaded_count += 1
                    logger.info(f"Loaded persona: {persona.name}")
                except Exception as e:
                    logger.error(f"Failed to load persona from {file_path}: {e}")
                    if st:
                        st.warning(f"⚠️ {file_path} yüklenemedi: {e}")
            else:
                logger.warning(f"Persona dosyası bulunamadı: {file_path}")
                
        if loaded_count == 0:
            logger.warning("Hiç persona yüklenemedi!")
            if st:
                st.warning("⚠️ Hiç persona dosyası bulunamadı. personas/ klasörünü kontrol edin.")
        else:
            logger.info(f"{loaded_count} persona başarıyla yüklendi")
    
    def load_agenda_data(self, file_path: str):
        """Load agenda data from CSV/Excel with improved error handling"""
        try:
            # Dosya var mı kontrol et
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                if st:
                    st.error(f"📁 Dosya bulunamadı: {file_path}")
                return False

            # Dosya formatını kontrol et ve oku
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.csv':
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin-1')
                    except:
                        df = pd.read_csv(file_path, encoding='cp1254')
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file format: {file_extension}")
                if st:
                    st.error(f"❌ Desteklenmeyen dosya formatı: {file_extension}")
                return False

            if df.empty:
                logger.error("File is empty")
                if st:
                    st.error("📄 Dosya boş!")
                return False

            # Sütun adlarını temizle (boşlukları kaldır)
            df.columns = df.columns.str.strip()
            
            # Gerekli sütunları kontrol et (büyük/küçük harf duyarsız)
            required_columns = ['TYPE', 'LINK', 'TITLE', 'CONTENT', 'COMMENTS']
            df_columns_upper = [col.upper() for col in df.columns]
            
            missing_columns = []
            column_mapping = {}
            
            for req_col in required_columns:
                found = False
                for i, df_col in enumerate(df_columns_upper):
                    if req_col == df_col:
                        column_mapping[req_col] = df.columns[i]
                        found = True
                        break
                if not found:
                    missing_columns.append(req_col)
            
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                if st:
                    st.error(f"❌ Eksik sütunlar: {missing_columns}")
                    st.info(f"📋 Mevcut sütunlar: {list(df.columns)}")
                    st.info(f"🔍 Gerekli sütunlar: {required_columns}")
                return False

            # Verileri yükle
            self.agenda_items = []
            loaded_items = 0
            
            for index, row in df.iterrows():
                try:
                    # Boş satırları atla
                    if pd.isna(row[column_mapping['TITLE']]) or str(row[column_mapping['TITLE']]).strip() == '':
                        continue
                        
                    item = AgendaItem(
                        type=str(row.get(column_mapping['TYPE'], '')),
                        link=str(row.get(column_mapping['LINK'], '')),
                        title=str(row.get(column_mapping['TITLE'], '')),
                        content=str(row.get(column_mapping['CONTENT'], '')),
                        comments=str(row.get(column_mapping['COMMENTS'], ''))
                    )
                    self.agenda_items.append(item)
                    loaded_items += 1
                except Exception as e:
                    logger.warning(f"Satır {index + 1} atlandı: {e}")
                    continue

            if loaded_items == 0:
                logger.error("No valid agenda items found")
                if st:
                    st.error("📋 Geçerli gündem maddesi bulunamadı!")
                return False

            logger.info(f"Successfully loaded {loaded_items} agenda items")
            if st:
                st.success(f"✅ {loaded_items} gündem maddesi başarıyla yüklendi!")
            return True

        except Exception as e:
            logger.error(f"Failed to load agenda data: {str(e)}")
            if st:
                st.error(f"❌ Gündem yükleme hatası: {str(e)}")
            return False
    
    async def score_agenda_items(self):
        """Score all agenda items for all personas with progress tracking"""
        if not self.agenda_items or not self.personas:
            return
            
        total_operations = len(self.agenda_items) * len(self.personas)
        completed_operations = 0
        
        if st:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        for item in self.agenda_items:
            scores = []
            for persona in self.personas:
                try:
                    if st:
                        status_text.text(f"🎯 {persona.name} için {item.title} puanlanıyor...")
                    
                    score = await self.mcp_agent.score_agenda_item(persona, item)
                    scores.append(score)
                    
                    summary = await self.mcp_agent.summarize_for_persona(persona, item, score)
                    self.memory[(persona.name, item.title)] = summary
                    
                    completed_operations += 1
                    if st:
                        progress_bar.progress(completed_operations / total_operations)
                        
                except Exception as e:
                    logger.error(f"Error scoring {item.title} for {persona.name}: {e}")
                    scores.append(5.0)  # Default score
                    completed_operations += 1
                    if st:
                        progress_bar.progress(completed_operations / total_operations)
            
            item.score = sum(scores) / len(scores) if scores else 0.0
        
        if st:
            status_text.text("✅ Puanlama tamamlandı!")
            progress_bar.empty()
            status_text.empty()
    
    async def start_simulation(self, max_rounds=10):
        """Start the focus group simulation with improved error handling"""
        if not self.agenda_items:
            raise ValueError("Gündem maddeleri yüklenmemiş!")
        
        if not self.personas:
            raise ValueError("Hiç persona yüklenmemiş!")
            
        self.is_running = True
        self.discussion_log = []
        round_count = 0
        
        try:
            while self.is_running and round_count < max_rounds:
                for agenda_item in self.agenda_items:
                    if not self.is_running:
                        break
                    
                    # Moderatör girişi
                    first_persona = self.personas[0].name if self.personas else "katılımcı"
                    try:
                        moderator_intro = await self.moderator.start_discussion(agenda_item, first_persona)
                        self.discussion_log.append({
                            'timestamp': datetime.now(),
                            'speaker': 'Moderatör',
                            'message': moderator_intro
                        })
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"Moderator intro failed: {e}")
                        continue
                    
                    # Her persona konuşsun
                    for i, agent in enumerate(self.agents):
                        if not self.is_running:
                            break
                        
                        try:
                            context = self._build_context()
                            response = await agent.generate_response(context, agenda_item)
                            self.discussion_log.append({
                                'timestamp': datetime.now(),
                                'speaker': agent.persona.name,
                                'message': response
                            })
                            await asyncio.sleep(3)
                            
                            # Moderatör sıradaki kişiye söz versin (sonuncu hariç)
                            if i < len(self.agents) - 1:
                                next_persona = self.agents[i + 1].persona.name
                                moderator_transition = await self.moderator.give_turn(
                                    agent.persona.name, next_persona
                                )
                                self.discussion_log.append({
                                    'timestamp': datetime.now(),
                                    'speaker': 'Moderatör',
                                    'message': moderator_transition
                                })
                                await asyncio.sleep(2)
                        except Exception as e:
                            logger.error(f"Agent response failed for {agent.persona.name}: {e}")
                            # Hata durumunda varsayılan yanıt ekle
                            self.discussion_log.append({
                                'timestamp': datetime.now(),
                                'speaker': agent.persona.name,
                                'message': f"Özür dilerim, şu anda fikrimi ifade edemiyorum."
                            })
                
                round_count += 1
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            self.is_running = False
            raise
        finally:
            self.is_running = False
        
        return self.discussion_log
    
    def _build_context(self) -> str:
        """Build conversation context from discussion log"""
        context_parts = []
        for entry in self.discussion_log[-5:]:  # Son 5 mesaj
            context_parts.append(f"{entry['speaker']}: {entry['message']}")
        return "\n".join(context_parts)
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.is_running = False
        logger.info("Simulation stopped by user")
    
    async def generate_analysis(self) -> str:
        """Generate final analysis report"""
        if not self.discussion_log:
            return "Analiz edilecek tartışma bulunamadı."
            
        full_discussion = self._build_full_discussion()
        if not full_discussion.strip():
            return "Boş tartışma - analiz edilecek içerik yok."
            
        try:
            analysis = await self.overseer.analyze_discussion(full_discussion)
            return analysis
        except Exception as e:
            logger.error(f"Analysis generation failed: {e}")
            return f"Analiz oluşturulurken hata oluştu: {str(e)}"
    
    def _build_full_discussion(self) -> str:
        """Build complete discussion text"""
        discussion_parts = []
        for entry in self.discussion_log:
            timestamp = entry['timestamp'].strftime("%H:%M:%S")
            discussion_parts.append(f"[{timestamp}] {entry['speaker']}: {entry['message']}")
        return "\n".join(discussion_parts)

# Global simulator instance with error handling
try:
    simulator = FocusGroupSimulator()
    logger.info("Simulator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize simulator: {e}")
    simulator = None

if __name__ == "__main__":
    print("main.py loaded successfully")
    print(f"Simulator available: {simulator is not None}")
    if simulator:
        print(f"Personas loaded: {len(simulator.personas)}")
    else:
        print("Simulator initialization failed - check API keys and dependencies")