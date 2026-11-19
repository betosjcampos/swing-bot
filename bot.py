import yfinance as yf
import requests
import threading
import time
import random
from flask import Flask
from datetime import datetime
import pytz

TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"
TELEGRAM_CHAT_ID = "SEU_ID_AQUI"
ACOES = ["PETR4.SA","VALE3.SA","ITUB4.SA","BBDC4.SA","WEGE3.SA","MGLU3.SA","BBAS3.SA","PRIO3.SA","JBSS3.SA","RAIL3.SA"]
estado = {}
FUSO = pytz.timezone("America/Sao_Paulo")

app = Flask(__name__)
@app.route('/')
def home():
    return "Robo swing trade rodando!"

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
    except: pass

def get_preco_com_retry(ticker_str):
    for tentativa in range(3):
        try:
            t = yf.Ticker(ticker_str)
            # tenta pegar 5 minutos pra evitar bloqueio
            hist = t.history(period="5d", interval="1m")
            if not hist.empty:
                return float(hist['Close'].dropna().iloc[-1])
            time.sleep(2 + random.random()*2)
        except Exception as e:
            print(f"Tentativa {tentativa+1} falhou {ticker_str}: {e}")
            time.sleep(5)
    return None

def monitorar():
    print("Robo iniciado")
    while True:
        for ativo in ACOES:
            preco = get_preco_com_retry(ativo)
            if preco is None:
                continue
            if ativo not in estado:
                estado[ativo] = preco
                print(f"{ativo} inicial {preco}")
                continue
            ultimo = estado[ativo]
            if ultimo - preco >= 0.25:
                agora = datetime.now(FUSO).strftime("%d/%m %H:%M")
                msg = f"Queda R$0,25+ {ativo} De R${ultimo:.2f} -> R${preco:.2f} {agora}"
                print(msg)
                enviar_telegram(msg)
                estado[ativo] = preco
            if preco > ultimo + 1:
                estado[ativo] = preco
        time.sleep(70)

threading.Thread(target=monitorar, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
