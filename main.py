import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable
import pandas as pd
from dataclasses import dataclass
import google.generativeai as genai
from dotenv import load_dotenv
import re
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

mcp_logs = []

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
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        name = data.get('name')
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().replace(' ', '_'))
        base_path = 'personas_pp/'
        pic_path_jpg = f"{base_path}{safe_name}.jpg"
        pic_path_png = f"{base_path}{safe_name}.png"
        if os.path.exists(pic_path_jpg):
            profile_pic = pic_path_jpg
        elif os.path.exists(pic_path_png):
            profile_pic = pic_path_png
        else:
            profile_pic = None
        return cls(
            name=name,
            bio=data.get('bio'),
            lore=data.get('lore'),
            knowledge=data.get('knowledge'),
            topics=data.get('topics'),
            style=data.get('style'),
            adjectives=data.get('adjectives'),
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
    persona_scores: Dict[str, float] = None
    persona_memories: Dict[str, str] = None
    
    def __post_init__(self):
        if self.persona_scores is None:
            self.persona_scores = {}
        if self.persona_memories is None:
            self.persona_memories = {}

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.api_key_2 = os.getenv('GEMINI_API_KEY_2')
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
        current_time = time.time()
        if current_time - self.last_switch_time >= self.switch_interval:
            if self.api_key_2:
                self.current_api_key = self.api_key_2 if self.current_api_key == self.api_key else self.api_key
            self.last_switch_time = current_time
            logger.info(f"API anahtarı değiştirildi: {self.current_api_key[:10]}...")
            self.request_count = 0

    def _log_request(self, success: bool, error: str = None):
        log_entry = {
            'timestamp': datetime.now(),
            'api_key': self.current_api_key[:10] + '...' if self.current_api_key else 'None',
            'request_count': self.request_count,
            'success': success,
            'error': error
        }
        self.request_log.append(log_entry)
        if len(self.request_log) > 100:
            self.request_log = self.request_log[-100:]

    async def call_llm(self, prompt: str, max_retries: int = 3) -> str:
        for attempt in range(max_retries):
            try:
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
                
                if not self.current_api_key:
                    self._log_request(success=False, error="API key not found")
                    return "API anahtarı bulunamadı. Lütfen .env dosyasını kontrol edin."
                
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
                
                if "429" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = self.retry_delay
                        logger.warning(f"Rate limit aşıldı. {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                
                if attempt == max_retries - 1:
                    return "Üzgünüm, şu anda yanıt veremiyorum. Lütfen daha sonra tekrar deneyin."
                
                await asyncio.sleep(1)

    def get_request_stats(self) -> dict:
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
            score = float(re.search(r'\d+', response).group())
            return min(max(score, 1), 10)
        except:
            return 5.0

    async def summarize_for_persona(self, persona, agenda_item, score):
        prompt = f"""[SİSTEM MESAJI]
Sen bir "Hatırlama Uzmanı"sın. Sana bir persona profili, bir haber ve bu personanın haberi okuma dikkat seviyesi (1-10) verilecek. Lütfen, bu persona bu haberi bu dikkat seviyesiyle okusa, neleri hatırlar, neleri unutur, hangi ana fikri aklında tutar, özetle. Yanıtın sadece persona'nın aklında kalanlar olsun.

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

class FocusGroupAgent:
    def __init__(self, persona: Persona, llm_client: LLMClient, mcp_agent: MCPThinkingAgent):
        self.persona = persona
        self.llm_client = llm_client
        self.mcp_agent = mcp_agent
        self.conversation_history = []
    
    async def generate_response(self, context: str, agenda_item: AgendaItem) -> str:
        memory_summary = agenda_item.persona_memories.get(self.persona.name, None)
        
        if memory_summary:
            prompt = f"""[SİSTEM MESAJI]
Sen {self.persona.name} adlı personasın. Sana ait tüm kişisel bilgiler, geçmiş, bilgi alanları, konuşma tarzı ve sıfatlar aşağıda verilmiştir. Odak grup tartışmasında, bu karakterine tamamen uygun bir şekilde hareket etmeli ve konuşmalısın.

[PERSONA PROFİLİ]
İsim: {self.persona.name}
Biyo: {self.persona.bio}
Geçmiş: {self.persona.lore}
Bilgi: {self.persona.knowledge}
Konular: {self.persona.topics}
Stil: {self.persona.style}
Sıfatlar: {self.persona.adjectives}

[TARTIŞMA BAĞLAMI]
{context}
Şu anki gündem maddesi (senin hatırladığın kadarıyla): {memory_summary}

[TALİMATLAR]
1. "bio", "lore", "knowledge", "topics", "style" ve "adjectives" alanlarını her yanıtında içselleştir.
2. Yanıtların, personanın yaşından, eğitiminden, sosyo-ekonomik durumundan ve inançlarından etkilenmiş olmalıdır.
3. "style" (all, chat, post) ve "adjectives" özelliklerini konuşma tarzına ve kelime seçimine yansıt.
4. Gündem maddesine ve diğer personaların yorumlarına, kendi personanın bakış açısıyla tepki ver.
5. Diğer personaları ikna etmeye çalış. Fikir ayrılığı olduğunda karşı çık, gerekirse duygusal tepki ver, kız, yüksel. Tartışmacı ve canlı bir üslup kullan.
6. Yanıtların doğal ve gerçekçi olmalı, yapay zeka tarafından üretildiği anlaşılmamalıdır.
7. Sadece personanın söyleyeceği sözleri yaz. Açıklama veya meta-yorum yapma.
"""
        else:
            prompt = f"""[SİSTEM MESAJI]
Sen {self.persona.name} adlı personasın. Sana ait tüm kişisel bilgiler, geçmiş, bilgi alanları, konuşma tarzı ve sıfatlar aşağıda verilmiştir. Odak grup tartışmasında, bu karakterine tamamen uygun bir şekilde hareket etmeli ve konuşmalısın.

[PERSONA PROFİLİ]
İsim: {self.persona.name}
Biyo: {self.persona.bio}
Geçmiş: {self.persona.lore}
Bilgi: {self.persona.knowledge}
Konular: {self.persona.topics}
Stil: {self.persona.style}
Sıfatlar: {self.persona.adjectives}

[TARTIŞMA BAĞLAMI]
{context}
Şu anki gündem maddesi: {agenda_item.title} - {agenda_item.content}

[TALİMATLAR]
1. "bio", "lore", "knowledge", "topics", "style" ve "adjectives" alanlarını her yanıtında içselleştir.
2. Yanıtların, personanın yaşından, eğitiminden, sosyo-ekonomik durumundan ve inançlarından etkilenmiş olmalıdır.
3. "style" ve "adjectives" özelliklerini konuşma tarzına ve kelime seçimine yansıt.
4. Gündem maddesine ve diğer personaların yorumlarına, kendi personanın bakış açısıyla tepki ver.
5. Yanıtların doğal ve gerçekçi olmalı, yapay zeka tarafından üretildiği anlaşılmamalıdır.
6. Sadece personanın söyleyeceği sözleri yaz. Açıklama veya meta-yorum yapma.
"""
        
        response = await self.llm_client.call_llm(prompt)
        return response.strip()

class ModeratorAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.conversation_history = []
    
    async def start_discussion(self, agenda_item: AgendaItem, first_persona: str) -> str:
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
    
    async def analyze_discussion(self, full_discussion: str, personas: List[Persona], agenda_items: List[AgendaItem]) -> str:
        # Prepare persona info
        persona_info = ""
        if personas:
            for persona in personas:
                persona_info += f"- {persona.name}: {persona.role}, {persona.personality}\n"
        
        # Prepare agenda info
        agenda_info = ""
        if agenda_items:
            for i, item in enumerate(agenda_items, 1):
                agenda_info += f"{i}. {item.title}\n"
        
        prompt = f"""[SİSTEM MESAJI]
Sen "Prof. Dr. Araştırmacı" - sosyoloji ve siyaset bilimi alanında uzmanlaşmış bir akademisyensin. Sana bir odak grup tartışmasının tam transkripti verilecek. Bu tartışmayı derinlemesine analiz et.

[KATILIMCILAR]
{persona_info}

[TARTIŞILAN KONULAR]
{agenda_info}

[TARTIŞMA TRANSKRİPTİ]
{full_discussion}

[ARAŞTIRMA RAPORU TALİMATLARI]
Kapsamlı bir akademik analiz raporu hazırla:

**1. YÖNETİCİ ÖZETİ**
- Ana bulgular ve sonuçlar

**2. KATILIMCI ANALİZİ**
- Her katılımcının profil analizi
- Konuşma tarzları ve karakteristik özellikleri
- Grup içindeki rolleri

**3. TARTIŞMA DİNAMİKLERİ**
- Ana temalar ve tartışma noktaları
- Katılımcılar arası etkileşimler
- Anlaşmazlık ve uzlaşma alanları

**4. SOSYOLOJİK BULGULAR**
- Toplumsal sınıf, yaş, cinsiyet etkilerinin analizi
- Kültürel ve sosyal kimlik etkileri
- Grup dinamikleri

**5. POLİTİK BOYUT ANALİZİ**
- Siyasi eğilimler ve ideolojik konumlar
- Polarizasyon seviyeleri
- Demokratik tartışma kalitesi

**6. SÖYLEM ANALİZİ**
- Kullanılan dil ve retorik
- İkna stratejileri
- Duygusal ve rasyonel argümanlar

**7. TÜRKİYEDEKİ KÜSKÜN-KARARSIZ SEÇMENİN SİYASİ VE SOSYOLOJİK DURUMU**
- Türkiye'deki küskün-kararsız seçmenin önemli politik özellikleri
- Türkiye'deki küskün-kararsız seçmenin önemli sosyolojik özellikleri
- Türkiye'deki küskün-kararsiz seçmenin liderlere bakişi ve aktif popüler liderleri

**8. STRATEJİK ÖNERİLER**
- Küskün-kararsız seçmenin algı değişimi
- Aktif liderlerin bu seçmen kitlesini kazanma stratejileri
- Bu personalara hitap eden gündem maddeleri önerileri

**9. SONUÇ VE ÖNERİLER**
- Temel bulgular
- Toplumsal çıkarımlar
- Politik öneriler

Objektif, bilimsel ve eleştirel bir yaklaşım sergile. Somut örneklerle destekle.
"""
        
        analysis = await self.llm_client.call_llm(prompt)
        return analysis

class FocusGroupSimulator:
    def __init__(self):
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
        
        self.load_personas()
        os.makedirs("personas_pp", exist_ok=True)
    
    def load_personas(self):
        persona_files = [
            'personas/elif.json',
            'personas/hatice_teyze.json',
            'personas/kenan_bey.json',
            'personas/tugrul_bey.json'
        ]
        
        for file_path in persona_files:
            if os.path.exists(file_path):
                try:
                    persona = Persona.from_json(file_path)
                    self.personas.append(persona)
                    agent = FocusGroupAgent(persona, self.llm_client, self.mcp_agent)
                    self.agents.append(agent)
                    logger.info(f"Loaded persona: {persona.name}")
                except Exception as e:
                    logger.error(f"Failed to load persona from {file_path}: {e}")
    
    def load_agenda_data(self, file_path: str):
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False

            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path}")
                return False

            required_columns = ['TYPE', 'LINK', 'TITLE', 'CONTENT', 'COMMENTS']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False

            self.agenda_items = []
            for _, row in df.iterrows():
                item = AgendaItem(
                    type=str(row.get('TYPE', '')),
                    link=str(row.get('LINK', '')),
                    title=str(row.get('TITLE', '')),
                    content=str(row.get('CONTENT', '')),
                    comments=str(row.get('COMMENTS', ''))
                )
                self.agenda_items.append(item)

            if not self.agenda_items:
                logger.error("No valid agenda items found in file")
                return False

            logger.info(f"Successfully loaded {len(self.agenda_items)} agenda items")
            return True

        except Exception as e:
            logger.error(f"Failed to load agenda data: {str(e)}")
            return False
    
    async def prepare_agenda_analysis(self):
        """Gündem maddelerini analiz et ve puanları hesapla"""
        await self.score_agenda_items()
    
    async def score_agenda_items(self):
        """Score all agenda items for all personas"""
        for item in self.agenda_items:
            scores = []
            for persona in self.personas:
                score = await self.mcp_agent.score_agenda_item(persona, item)
                scores.append(score)
                # Store individual scores
                item.persona_scores[persona.name] = score
                # Create memory summary
                summary = await self.mcp_agent.summarize_for_persona(persona, item, score)
                item.persona_memories[persona.name] = summary
                # Also store in old memory format for backward compatibility
                self.memory[(persona.name, item.title)] = summary
            item.score = sum(scores) / len(scores)  # Average score
    
    async def start_simulation(self, max_rounds=3, on_new_message: Optional[Callable] = None):
        """Start the focus group simulation"""
        if not self.agenda_items:
            raise ValueError("No agenda items loaded")
        
        self.is_running = True
        self.discussion_log = []
        round_count = 0
        
        import random
        
        while self.is_running and round_count < max_rounds:
            for agenda_item in self.agenda_items:
                if not self.is_running:
                    break
                
                # Moderatör girişi
                first_persona = self.personas[0].name if self.personas else "katılımcı"
                moderator_intro = await self.moderator.start_discussion(agenda_item, first_persona)
                self.discussion_log.append({
                    'timestamp': datetime.now(),
                    'speaker': 'Moderatör',
                    'message': moderator_intro
                })
                
                if on_new_message:
                    await on_new_message()
                
                await asyncio.sleep(2)
                
                # Her persona konuşsun (random sırayla)
                agent_indices = list(range(len(self.agents)))
                random.shuffle(agent_indices)
                
                for i in agent_indices:
                    if not self.is_running:
                        break
                    
                    agent = self.agents[i]
                    
                    # Moderatör sıradaki kişiye söz versin
                    if i < len(self.agents) - 1:
                        next_persona = agent.persona.name
                        moderator_transition = await self.moderator.give_turn(
                            "önceki konuşmacı", next_persona
                        )
                        self.discussion_log.append({
                            'timestamp': datetime.now(),
                            'speaker': 'Moderatör',
                            'message': moderator_transition
                        })
                        
                        if on_new_message:
                            await on_new_message()
                        
                        await asyncio.sleep(2)
                    
                    # Persona konuşur
                    context = self._build_context()
                    response = await agent.generate_response(context, agenda_item)
                    self.discussion_log.append({
                        'timestamp': datetime.now(),
                        'speaker': agent.persona.name,
                        'message': response
                    })
                    
                    if on_new_message:
                        await on_new_message()
                    
                    await asyncio.sleep(3)
                
                # Tur sonunda moderatör yorum yapsın
                end_comments = [
                    "Teşekkürler, bu konuda çok değerli görüşler ortaya çıktı.",
                    "Farklı bakış açıları ile zengin bir tartışma oldu.",
                    "Bu konudaki görüşleriniz için hepinize teşekkür ederim."
                ]
                moderator_comment = random.choice(end_comments)
                self.discussion_log.append({
                    'timestamp': datetime.now(),
                    'speaker': 'Moderatör',
                    'message': moderator_comment
                })
                
                if on_new_message:
                    await on_new_message()
                
                await asyncio.sleep(2)
            
            round_count += 1
        
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
    
    async def generate_analysis(self) -> str:
        """Generate final analysis report"""
        full_discussion = self._build_full_discussion()
        analysis = await self.overseer.analyze_discussion(full_discussion, self.personas, self.agenda_items)
        return analysis
    
    def _build_full_discussion(self) -> str:
        """Build complete discussion text"""
        discussion_parts = []
        for entry in self.discussion_log:
            timestamp = entry['timestamp'].strftime("%H:%M:%S")
            discussion_parts.append(f"[{timestamp}] {entry['speaker']}: {entry['message']}")
        return "\n".join(discussion_parts)

# Global simulator instance
simulator = FocusGroupSimulator()