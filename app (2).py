import requests
import time
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os

# Logging setup
logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# API credentials (use environment variables for security)
API_KEY = os.getenv('TD_AMERITRADE_API_KEY', 'YOUR_TD_AMERITRADE_API_KEY')
REDIRECT_URI = os.getenv('TD_REDIRECT_URI', 'YOUR_REDIRECT_URI')
REFRESH_TOKEN = os.getenv('TD_REFRESH_TOKEN', 'YOUR_REFRESH_TOKEN')
ACCOUNT_ID = os.getenv('TD_ACCOUNT_ID', 'YOUR_ACCOUNT_ID')
SECRET_KEY = os.getenv('SECRET_KEY', 'YOUR_SECRET_KEY')

# Constants for trade strategy
SYMBOL = 'AAPL'
STOP_LOSS_PERCENTAGE = 0.05  # 5% stop loss
TAKE_PROFIT_PERCENTAGE = 0.10  # 10% take profit
POSITION_SIZE = 1  # Default position size, can be calculated dynamically

# Helper function to refresh access token
def refresh_access_token():
    url = 'https://api.tdameritrade.com/v1/oauth2/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    body = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
        'client_id': f'{API_KEY}@AMER.OAUTHAP'
    }
    response = requests.post(url, headers=headers, data=body)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        logging.error('Error refreshing access token: %s', response.text)
        return None

ACCESS_TOKEN = refresh_access_token()

# Function to make API calls with retry logic
def safe_api_call(func, *args, retries=3, delay=2, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"API call failed: {e}. Retrying {attempt + 1}/{retries}...")
            time.sleep(delay)
    logging.error("All retries failed.")
    return None

# Function to get market data (candlesticks)
def get_market_data(symbol, period_type='hour', period=1, frequency_type='minute', frequency=1):
    url = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory"
    params = {
        'apikey': API_KEY,
        'periodType': period_type,
        'period': period,
        'frequencyType': frequency_type,
        'frequency': frequency
    }
    return safe_api_call(requests.get, url, params=params)

# Function to place a trade
def place_trade(symbol, action='BUY_TO_OPEN', quantity=POSITION_SIZE, price=None):
    url = f'https://api.tdameritrade.com/v1/accounts/{ACCOUNT_ID}/orders'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    order_payload = {
        "orderType": "LIMIT",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": action,
                "quantity": quantity,
                "instrument": {
                    "symbol": symbol,
                    "assetType": "EQUITY"
                }
            }
        ]
    }

    if price:
        order_payload["price"] = price

    response = requests.post(url, headers=headers, json=order_payload)
    if response.status_code == 201:
        logging.info(f"Trade placed: {action} {quantity} shares of {symbol} at {price}")
    else:
        logging.error(f"Error placing trade: {response.status_code} {response.text}")

# Additional functions for your trading strategy...
