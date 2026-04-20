import os, requests
from flask import Flask, request
from datetime import datetime
import pytz
 
app = Flask(__name__)
 
TOKEN       = os.environ['BOT_TOKEN']
CHAT_ID     = os.environ['CHAT_ID']
COUPLE_CODE = os.environ['COUPLE_CODE']
FIREBASE    = os.environ['FIREBASE_URL']
TZ          = pytz.timezone('America/Argentina/Buenos_Aires')
API         = f'https://api.telegram.org/bot{TOKEN}'
 
def tg(method, **kwargs):
    return requests.post(f'{API}/{method}', json=kwargs)
 
def ya_se_tomo_hoy():
    now      = datetime.now(TZ)
    date_key = now.strftime('%m-%d')
    year     = now.year
    url      = f'{FIREBASE}/parejas/{COUPLE_CODE}/{year}/{date_key}.json'
    r = requests.get(url)
    return r.json() == True
 
@app.route('/')
def index():
    return '💊 Bot activo y funcionando!'
 
@app.route('/send-reminder')
def send_reminder():
    if ya_se_tomo_hoy():
        return 'Ya se tomo la pastilla hoy, no se envia recordatorio.'
 
    now      = datetime.now(TZ)
    date_key = now.strftime('%m-%d')
 
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
 
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True) or {}
 
    if 'callback_query' in data:
        cq      = data['callback_query']
        cq_id   = cq['id']
        chat_id = cq['message']['chat']['id']
        msg_id  = cq['message']['message_id']
        cb_data = cq['data']
 
        tg('answerCallbackQuery', callback_query_id=cq_id)
 
        if cb_data.startswith('taken_'):
            date_key = cb_data.replace('taken_', '')
            year     = datetime.now(TZ).year
 
            url = f'{FIREBASE}/parejas/{COUPLE_CODE}/{year}/{date_key}.json'
            requests.put(url, json=True)
 
            tg('editMessageText',
               chat_id=chat_id,
               message_id=msg_id,
               text='✅ ¡Perfecto! Pastilla marcada en la página 💊❤️')
 
        else:
            tg('editMessageText',
               chat_id=chat_id,
               message_id=msg_id,
               text='⏰ ¡No te olvides! Te voy a recordar en 10 minutos.')
 
    return 'ok'
 
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 
