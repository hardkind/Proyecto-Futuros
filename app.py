from flask import Flask, render_template
import time

import requests
import hmac
from hashlib import sha256
from binance.client import Client

import locale  # Para añadir separador de miles a valor COP

# Configuración de las claves API
binance_api_key = 'Ah1AuzkMqrKpjiVnlTItUgxZKtk71IYmnmei2yhwNIVBVcLLLaRoCpCo3cFbZBuJ'
binance_api_secret = 'StnwM0pXye73G92NZjvXTkdVu0FrC09mCrNI4sWEVZ1WUElBnHHVtiouxAc8JV3K'

bingx_api_key = 'FhliYtRJbkP4ciWYGaFpe1Eq699GUmd5GRDjF7kLlfDyQEzaVBF6k1SOf8isiTha95tVYVpaRuAW8JCEwBg'
bingx_secret_key = 'scLGA9JBOHFre2MFu1zenWA34JBL34JVGOWIPEuN5qDZrEgErLd5K0qSvu5nM4rSm6mnSDrhldnJCXRxYbg'
APIURL = "https://open-api.bingx.com"

# Inicializa el cliente de Binance
client = Client(binance_api_key, binance_api_secret)

def get_open_positions_bingx():
    path = '/openApi/swap/v2/user/positions'
    method = "GET"
    timestamp = int(time.time() * 1000)
    paramsMap = {
        "timestamp": timestamp
    }
    paramsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, {})

def get_sign(api_secret, payload):
    return hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()

def send_request(method, path, urlpa, payload):
    url = f"{APIURL}{path}?{urlpa}&signature={get_sign(bingx_secret_key, urlpa)}"
    headers = {
        'X-BX-APIKEY': bingx_api_key,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.json()

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    return "&".join([f"{x}={paramsMap[x]}" for x in sortedKeys])

# Calcula el porcentaje de ganancia
def calculate_percentage(pnl, initial_margin):
    if initial_margin != 0:
        return round((pnl / initial_margin) * 100, 2)
    return 0

# Crear la aplicación Flask
app = Flask(__name__)

# Ruta principal que muestra la página web
@app.route('/')
def index():
    # Obtener las posiciones abiertas de Binance
    total_pnl_binance = 0
    positions_binance = client.futures_account()['positions']
    positions_data_binance = []

    for position in positions_binance:
        if float(position['positionAmt']) != 0:
            symbol = position['symbol']
            pnl = round(float(position['unrealizedProfit']), 2)
            initial_margin = float(position['initialMargin'])  # Añadir esta línea para obtener el margen inicial
            percentage = calculate_percentage(pnl, initial_margin)
            positions_data_binance.append({'symbol': symbol, 'pnl': pnl, 'percentage': percentage})
            total_pnl_binance += pnl

    total_pnl_binance = round(total_pnl_binance, 2)

    # Obtener las posiciones abiertas de BingX
    total_pnl_bingx = 0
    positions_bingx = get_open_positions_bingx()
    positions_data_bingx = []

    if positions_bingx.get("code") == 0:
        for position in positions_bingx.get("data", []):
            if float(position['positionAmt']) != 0:
                symbol = position['symbol']
                pnl = round(float(position['unrealizedProfit']), 2)
                initial_margin = float(position['initialMargin'])  # Añadir esta línea para obtener el margen inicial
                percentage = calculate_percentage(pnl, initial_margin)
                positions_data_bingx.append({'symbol': symbol, 'pnl': pnl, 'percentage': percentage})
                total_pnl_bingx += pnl

        total_pnl_bingx = round(total_pnl_bingx, 2)
    else:
        print(f"Error en la API de BingX: {positions_bingx.get('msg')}")

    # SUMA TOTALES PNL BIANANCE Y BINGX
    total_pnl_combined = round(total_pnl_binance + total_pnl_bingx, 2)

    # CONVERTIMOS TOTAL PNL BINANCE Y BING DE USDT A COP
    total_pnl_combined_cop = round(total_pnl_combined * 4210, 2)
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')     # Formatea el valor, para añadir separador de miles
    total_pnl_combined_cop_formateado = locale.format_string("%0.2f", total_pnl_combined_cop, grouping=True)

    return render_template('index.html', 
                           positions_binance = positions_data_binance, 
                           total_pnl_binance = total_pnl_binance,
                           positions_bingx = positions_data_bingx, 
                           total_pnl_bingx = total_pnl_bingx,
                           total_pnl_combined = total_pnl_combined,
                           total_pnl_combined_cop = total_pnl_combined_cop_formateado)

