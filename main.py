import os, requests
from flask import Flask, request
from datetime import datetime
import pytz

app = Flask(__name__)

# ── Configuración (se cargan desde Render) ──────────────────────
TOKEN       = os.environ['BOT_TOKEN']
CHAT_ID     = os.environ['CHAT_ID']
COUPLE_CODE = os.environ['COUPLE_CODE']
FIREBASE    = os.environ['FIREBASE_URL']   # ej: https://pastillabianca-default-rtdb.firebaseio.com
TZ          = pytz.timezone('America/Argentina/Buenos_Aires')
API         = f'https://api.telegram.org/bot{TOKEN}'
# ────────────────────────────────────────────────────────────────

def tg(method, **kwargs):
    """Llama a la API de Telegram."""
    return requests.post(f'{API}/{method}', json=kwargs)

# ── Ruta principal (para saber que el bot está vivo) ─────────────
@app.route('/')
def index():
    return '💊 Bot activo y funcionando!'

# ── Ruta que manda el recordatorio diario ───────────────────────
# cron-job.org va a llamar a esta URL todos los días a las 11pm
@app.route('/send-reminder')
def send_reminder():
    now      = datetime.now(TZ)
    date_key = now.strftime('%m-%d')   # ej: "04-18"

    tg('sendMessage',
       chat_id=CHAT_ID,
       text='💊 ¡Hora de tu pastilla, amor!\n\n¿Ya te la tomaste?',
       reply_markup={
           'inline_keyboard': [[
               {'text': '✅ Ya me la tomé', 'callback_data': f'taken_{date_key}'},
               {'text': '❌ Aún no',        'callback_data': 'not_taken'}
           ]]
       })
    return 'Recordatorio enviado!'

# ── Webhook: Telegram llama aquí cuando ella toca un botón ──────
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True) or {}

    if 'callback_query' in data:
        cq      = data['callback_query']
        cq_id   = cq['id']
        chat_id = cq['message']['chat']['id']
        msg_id  = cq['message']['message_id']
        cb_data = cq['data']

        # Confirmar a Telegram que recibimos el toque
        tg('answerCallbackQuery', callback_query_id=cq_id)

        if cb_data.startswith('taken_'):
            date_key = cb_data.replace('taken_', '')   # ej: "04-18"
            year     = datetime.now(TZ).year            # 2026

            # ── Escribir en Firebase ────────────────────────────
            url = f'{FIREBASE}/parejas/{COUPLE_CODE}/{year}/{date_key}.json'
            requests.put(url, json=True)
            # ────────────────────────────────────────────────────

            tg('editMessageText',
               chat_id=chat_id,
               message_id=msg_id,
               text='✅ ¡Perfecto! Pastilla marcada en la página 💊❤️')

        else:  # "Aún no"
            tg('editMessageText',
               chat_id=chat_id,
               message_id=msg_id,
               text='⏰ ¡No te olvides de tomarla un poco más tarde!')

    return 'ok'

# ── Arrancar el servidor ─────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
