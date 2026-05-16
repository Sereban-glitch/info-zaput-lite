import os
import google.generativeai as genai
import json
import base64

# Модель-рабочая лошадка 2026 года (из MEMORY.md)
MODEL_NAME = "gemini-2.5-flash"

# Системный промпт для голоса
VOICE_SYSTEM_PROMPT = """Ти — асистент для складання інформаційних запитів за Законом України "Про доступ до публічної інформації".
Користувач надсилає голосове повідомлення, де описує ситуацію. Твоя задача — витягнути структуровані дані для запиту.

ОБОВ'ЯЗКОВО поверни валідний JSON у такому форматі:
{
  "transcript": "повна транскрипція",
  "recipientHint": "конкретний орган або 'Офіс Генерального прокурора'",
  "subject": "тема запиту",
  "body": "сформульований предмет запиту українською, юридично грамотно",
  "deliveryMethod": "електронна на e-mail",
  "language": "uk"
}

ПРАВИЛА:
- Якщо орган не згаданий — пиши 'Офіс Генерального прокурора'.
- body має містити чіткі питання без вступних фраз.
- Якщо мова голосового не українська — body перекладай на українську.
- ПОВЕРНИ ТІЛЬКИ ЧИСТИЙ JSON."""

# Системный промпт для улучшения текста
TEXT_SYSTEM_PROMPT = """Ти — професійний юрист. Твоє завдання: сформулювати СУТЬ запиту на публічну інформацію. 
ПРАВИЛА: 
1. Тільки українська мова. 
2. КАТЕГОРИЧНО ЗАБОРОНЕНО вказувати email-адреси. Використовуй фразу: 'Відповідь прошу надіслати в електронному вигляді на адресу електронної пошти, з якої надіслано цей запит'. 
3. Поверни JSON: {"subject": "тема", "body": "текст запиту"}"""

def configure_ai():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    genai.configure(api_key=api_key)

def process_voice(audio_bytes, mime_type="audio/ogg"):
    """Транскрибация и генерация запроса из аудио через Gemini 2.5 Flash."""
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=VOICE_SYSTEM_PROMPT
    )
    
    response = model.generate_content([
        {
            "mime_type": mime_type,
            "data": audio_bytes
        },
        "Розшифруй це голосове та сформуй структурований JSON для запиту."
    ])
    
    text = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(text)

def process_text(user_text):
    """Превращение сырого текста в юридически грамотный запрос через Gemini 2.5 Flash."""
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=TEXT_SYSTEM_PROMPT
    )
    
    response = model.generate_content(f"Текст користувача: {user_text}")
    text = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(text)
