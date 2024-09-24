import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from dotenv import load_dotenv
import sqlite3
import google.generativeai as genai


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)


def conectar_banco():
    conn = sqlite3.connect('bot_data.db')
    return conn

# Função para criar a tabela de preferências de clima, se não existir
def criar_tabela():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS preferencias_clima 
                      (user_id INTEGER PRIMARY KEY, cidade TEXT)''')
    conn.commit()
    conn.close()

# Mensagem de início
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Olá! Eu sou o Bot do Tempo 🌑🌎🌕\n 🌠Pergunte-me sobre o clima de uma cidade digitando /clima [cidade].\n🌠Exemplo: /clima Manaus")

# Obter informações do OpenWeather
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=pt_br"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        description = data['weather'][0]['description']
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']

        # Mensagem formatada
        weather_message = (
            f"O clima em *{city}* é:\n\n"
            f"🌡️ *Temperatura*: {temp}°C\n"
            f"🌤️ *Condições*: {description}\n"
            f"💧 *Umidade*: {humidity}%\n"
            f"🌬️ *Vento*: {wind_speed} km/h\n\n"
            "Tenha um ótimo dia! ☀️"
        )
        return weather_message
    else:
        return "😥 Desculpe, não consegui obter o clima. Tente novamente."

# Obter informações do Gemini
def get_gemini_info(city):
    prompt = f"Me dê informações sobre o clima na cidade de {city} como épocas de chuva e seca, temperatura mínima e máxima, possibilidade de enchentes e incendio, no formato de tópicos e não utilize texto em negrito na sua resposta."
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text if response else "Não consegui obter mais informações no momento."

# Função 'Mais Informações'
def mais_informacoes(update: Update, context: CallbackContext):
    query = update.callback_query
    city = query.data.split(':')[1]  # Extrair a cidade da callback data
    gemini_info = get_gemini_info(city)
    query.edit_message_text(text=f"Mais informações sobre {city}:\n\n{gemini_info}")

# /clima
def clima(update: Update, context: CallbackContext):
    if context.args:
        city = ' '.join(context.args)
        weather_message = get_weather(city)

        # Botão para 'Mais Informações'
        keyboard = [
            [InlineKeyboardButton("Mais Informações", callback_data=f"mais_info:{city}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(weather_message, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        update.message.reply_text("🌠 Por favor, forneça o nome de uma cidade após o comando /clima.\nExemplo: /clima Manaus")

def main():
    criar_tabela()
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    
    # Comandos
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("clima", clima))
    dispatcher.add_handler(CallbackQueryHandler(mais_informacoes, pattern=r"^mais_info:"))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
