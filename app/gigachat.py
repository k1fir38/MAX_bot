import re
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from app.config import settings

# --- НАСТРОЙКИ РОЛЕЙ ---
BASE_FORMATTING = (
    "\n\nВАЖНО ПО ОФОРМЛЕНИЮ:"
    "1. НИКОГДА не используй LaTeX ($...$). "
    "2. Пиши формулы Unicode символами (x², √, Δ). "
    "3. Используй эмодзи, чтобы текст выглядел живым."
)

ROLES = {
    "default": "Ты полезный и краткий помощник.",
    
    "coder": (
        "Ты — Senior Developer. "
        "Твои ответы должны быть строгими и техническими. "
        "Пиши эффективный код, добавляй комментарии. "
        "Если видишь ошибку в коде — объясни, почему так делать нельзя."
    ),
    
    "teacher": (
        "Ты — терпеливый школьный учитель математики и физики. "
        "Твоя цель — не просто дать ответ, а ОБЪЯСНИТЬ решение пошагово. "
        "Будь вежлив, хвали ученика за успехи."
    ),
    
    "english": (
        "Ты — репетитор по английскому языку. "
        "Общайся с пользователем на английском. "
        "Если пользователь пишет на русском — переводи на английский и объясняй грамматику."
    ),
    
    "friend": (
        "Ты — лучший друг пользователя. "
        "Общайся неформально, используй сленг (в меру), шути, поддерживай. "
        "Можешь обращаться на 'ты'."
    )
}

class GigaChatService:
    def __init__(self):
        # Инициализация клиента. 
        # verify_ssl_certs=False важен, если не установлены сертификаты МинЦифры
        self.giga = GigaChat(
            credentials=settings.API_KEY,
            scope=settings.SCOPE,
            verify_ssl_certs=False,
            model=settings.MODEL
        )
        
        # Хранилище истории диалогов
        self.histories = {}
        # Хранилище выбранных ролей
        self.user_roles = {}
        self.current_ai_roles = {} 


    def _clean_markdown(self, text):
        """Очистка текста от разметки, которую плохо переваривает мессенджер"""
        if not text: return ""
        # Убираем жирный шрифт, курсив, LaTeX
        text = text.replace("**", "").replace("__", "").replace("$", "")
        # Убираем заголовки Markdown (# Заголовок)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        return text.strip()

    def change_role(self, user_id: int, role_key: str):
        """Меняет роль пользователя и сбрасывает историю"""
        if role_key in ROLES:
            self.user_roles[user_id] = role_key
            self.clear_history(user_id)
            return True
        return False
    
    def set_ai_role(self, user_id: int, role_key: str):
        """Устанавливает роль для текущей AI сессии и сбрасывает историю."""
        if role_key in ROLES:
            self.current_ai_roles[user_id] = role_key
            # Сбрасываем историю, чтобы начать новый контекст с новым системным промптом
            self.clear_history(user_id) 
            return True
        return False

    def _get_system_prompt(self, user_id):
        """Формирует системное сообщение на основе выбранной роли AI СЕССИИ"""
        # ИСПОЛЬЗУЕМ НОВУЮ РОЛЬ СЕССИИ, если она есть, иначе default
        role_key = self.current_ai_roles.get(user_id, self.user_roles.get(user_id, 'default'))
        role_text = ROLES[role_key]
        full_instruction = role_text + BASE_FORMATTING
        return Messages(role=MessagesRole.SYSTEM, content=full_instruction)

    def clear_history(self, user_id: int):
        """Полная очистка памяти диалога"""
        if user_id in self.histories:
            del self.histories[user_id]
            return True
        return False

    def _get_system_prompt(self, user_id):
        """Формирует системное сообщение на основе выбранной роли"""
        role_key = self.user_roles.get(user_id, 'default')
        role_text = ROLES[role_key]
        full_instruction = role_text + BASE_FORMATTING
        return Messages(role=MessagesRole.SYSTEM, content=full_instruction)

    def generate_response(self, user_id: int, user_text: str) -> str:
        try:
            # 1. Если истории нет, создаем её и добавляем системный промпт
            if user_id not in self.histories:
                self.histories[user_id] = [self._get_system_prompt(user_id)]
            
            # 2. Добавляем сообщение пользователя в историю
            self.histories[user_id].append(
                Messages(role=MessagesRole.USER, content=user_text)
            )

            # 3. Отправляем запрос в GigaChat
            payload = Chat(
                messages=self.histories[user_id],
                temperature=0.7,
                max_tokens=1000, # Ограничение длины ответа
            )
            
            response = self.giga.chat(payload)
            
            # 4. Получаем ответ
            answer_text = response.choices[0].message.content
            
            # 5. Сохраняем ответ бота в историю (чтобы он помнил контекст)
            self.histories[user_id].append(
                Messages(role=MessagesRole.ASSISTANT, content=answer_text)
            )
            
            return self._clean_markdown(answer_text)

        except Exception as e:
            # Если токен протух или ошибка сети
            return f"⚠️ Ошибка GigaChat: {e}"

# Создаем экземпляр сервиса
ai_service = GigaChatService()