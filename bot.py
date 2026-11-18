import yfinance as yf
import requests
import time
import pandas as pd
from datetime import datetime
import pytz
import csv
import os

# ========= SEU TELEGRAM =========
TELEGRAM_TOKEN = "8956757137:AAHRWYaSvAvYVBjN2rGEmrebNlbvV-LGDfM"
TELEGRAM_CHAT_ID = "8889605441"

ACOES = ["PETR4.SA","VALE3.SA","ITUB4.SA","BBDC4.SA","WEGE3.SA","MGLU3.SA","BBAS3.SA","PRIO3.SA","JBSS3.SA","RAIL3.SA"]
PRECO_BOM_MANUAL = {}

ARQUIVO_LOG = "log_quedas_swing.csv"
FUSO_BR = pytz.timezone("America/Sao_Paulo")
estado_quedas = {}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def calcular_preco_bom(ticker_obj, simbolo):
    base = simbolo.replace(".SA","")
    if base in PRECO_BOM_MANUAL:
        return PRECO_BOM_MANUAL[base]
    try:
        hist = ticker_obj.history(period="100d")
        if len(hist) < 50:
            return None
        mm50 = hist['Close'][-50:].mean()
        minima_20d = hist['Low'][-20:].min()
        preco_bom = min(mm50 * 0.97, minima_20d * 1.02)
        return round(float(preco_bom), 2)
    except:
        return None

def registrar_queda(ativo, preco_antes, preco_agora):
    agora = datetime.now(FUSO_BR)
    linha = {"data": agora.strftime("%d/%m/%Y"),"hora": agora.strftime("%H:%M:%S"),"ativo": ativo,"preco_anterior": preco_antes,"preco_atual": preco_agora,"queda": round(preco_antes - preco_agora, 2)}
    existe = os.path.exists(ARQUIVO_LOG)
    with open(ARQUIVO_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=linha.keys())
        if not existe:
            writer.writeheader()
        writer.writerow(linha)
    return agora

def monitorar():
    tickers = {}
    precos_bons = {}
    print("Iniciando e calculando preco bom...")
    for ativo in ACOES:
        try:
            t = yf.Ticker(ativo)
            tickers[ativo] = t
            pb = calcular_preco_bom(t, ativo)
            precos_bons[ativo] = pb
            estado_quedas[ativo] = None
            print(f"{ativo} | Preco bom: R$ {pb}")
        except Exception as e:
            print(f"{ativo} erro: {e}")

    enviar_telegram(f"Robo PythonAnywhere iniciado! Monitorando: {', '.join(ACOES)}")
    print("\n--- MONITORANDO ---")

    while True:
        for ativo in ACOES:
            try:
                t = tickers[ativo]
                # Pega preco atual rapido
                hist_1m = t.history(period="1d", interval="1m")
                if hist_1m.empty:
                    continue
                preco_atual = float(hist_1m['Close'].iloc[-1])

                if estado_quedas[ativo] is None:
                    estado_quedas[ativo] = preco_atual
                    continue

                ultimo = estado_quedas[ativo]
                diferenca = ultimo - preco_atual

                if diferenca >= 0.25:
                    data_hora = registrar_queda(ativo, ultimo, preco_atual)
                    estado_quedas[ativo] = preco_atual
                    msg = f"Queda R$0,25+ {ativo} De: R$ {ultimo:.2f} -> R$ {preco_atual:.2f} Data: {data_hora.strftime('%d/%m/%Y %H:%M:%S')}"
                    print(msg)
                    enviar_telegram(msg)

                if preco_atual > ultimo + 1.0:
                    estado_quedas[ativo] = preco_atual

                if precos_bons[ativo] is not None and preco_atual <= precos_bons[ativo]:
                    msg_compra = f"OPORTUNIDADE DE COMPRA {ativo} Preco Atual: R$ {preco_atual:.2f} Preco Bom: R$ {precos_bons[ativo]:.2f}"
                    print(msg_compra)
                    enviar_telegram(msg_compra)
                    precos_bons[ativo] = preco_atual * 0.98

            except Exception as e:
                print(f"Erro {ativo}: {e}")
                continue
        
        time.sleep(60) # verifica a cada 1 minuto no PythonAnywhere

monitorar()
