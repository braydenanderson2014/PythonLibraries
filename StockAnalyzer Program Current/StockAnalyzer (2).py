import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
from datetime import datetime, timedelta, timezone
import time
from requests import Session
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter
import os
import warnings
import json
import threading
import schedule
import smtplib
from twilio.rest import Client
import random
import string
import queue
import time
from collections import deque
import socket
import smtplib
import ssl
from mailjet_rest import Client
import pytz
import requests
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import sys
import joblib
from typing import List, Optional
from requests.exceptions import RequestException
from pyrate_limiter.exceptions import BucketFullException

# Suppress specific sklearn warning
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.base")

def standardize_datetime(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

# Function to clear the screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Set up caching and rate limiting
class CachedLimiterSession(LimiterMixin, Session):
    pass

session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND*5)),  # max 2 requests per 5 seconds
    bucket_class=MemoryQueueBucket
)
session.headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'


# Set up persistent cache
yf.set_tz_cache_location("./.yfinance_cache")

class Console:
    def __init__(self, console_widget, max_messages=50):
        self.queue = queue.Queue()
        self.messages = deque(maxlen=max_messages)  # Store recent messages
        self.console_widget = console_widget
        self.console_widget.after(100, self._process_queue)

    def log(self, message):
        self.queue.put(message)

    def _process_queue(self):
        while not self.queue.empty():
            message = self.queue.get_nowait()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"[{timestamp}] {message}"
            self.console_widget.insert(tk.END, f"\n[CONSOLE] {full_message}")
            self.console_widget.see(tk.END)
            self.messages.append(full_message)
        self.console_widget.after(100, self._process_queue)

    def get_recent_messages(self, n=10):
        return list(self.messages)[-n:]

    def clear_messages(self):
        self.messages.clear()

    def set_max_messages(self, max_messages):
        self.messages = deque(self.messages, maxlen=max_messages)

    def get_max_messages(self):
        return self.messages.maxlen
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.text_widget.after(100, self._process_queue)

    def write(self, message):
        self.queue.put(message)

    def _process_queue(self):
        while not self.queue.empty():
            message = self.queue.get_nowait()
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
        self.text_widget.after(100, self._process_queue)

    def flush(self):
        pass  # Required for compatibility with Python's sys.stdout and sys.stderr

class StockAnalyzerModel:
    def __init__(self, stock_list, model_path='stock_model.joblib', update_interval=86400):
        self.stock_list = stock_list
        self.update_interval = update_interval
        self.model_path = model_path
        self.model = self.load_model() or RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.predictions = {}
        self.accuracy = {}
        self.thread = threading.Thread(target=self.run_analysis, daemon=True)
        self.stop_event = threading.Event()
        self.errors = {}
    
    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()

    def run_analysis(self):
        while not self.stop_event.is_set():
            self.analyze_stocks()
            self.save_model()
            time.sleep(self.update_interval)
    def load_model(self):
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)
        return None

    def save_model(self):
        joblib.dump(self.model, self.model_path)
        print(f"Model saved to {self.model_path}")

    def analyze_stocks(self):
        features, targets = self.extract_features_and_targets()
        if features.empty:
            print("No features extracted. Skipping analysis.")
            return

        X = self.scaler.fit_transform(features)
        y = targets

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        mape = mean_absolute_percentage_error(y_test, y_pred)
        self.accuracy['overall'] = 1 - mape

        for stock in self.stock_list:
            self.predict(stock)

        print("Analysis completed. Predictions updated.")

    def extract_features_and_targets(self):
        all_features = []
        all_targets = []

        for stock in self.stock_list:
            stock_data = self.prepare_stock_data(stock)
            if stock_data.empty:
                continue

            features = stock_data.drop(['open', 'close'], axis=1)
            targets = stock_data[['open', 'close']]

            all_features.append(features)
            all_targets.append(targets)

        if not all_features:
            return pd.DataFrame(), pd.DataFrame()

        return pd.concat(all_features), pd.concat(all_targets)
    def prepare_stock_data(self, stock):
        if not stock.data.historical_Dates:
            return pd.DataFrame()

        # Ensure all lists have the same length
        min_length = min(len(stock.data.historical_Dates),
                         len(stock.data.historical_Stock_Prices) // 2)

        # Convert all datetimes to naive UTC for consistency
        dates = [d.replace(tzinfo=None) for d in stock.data.historical_Dates[:min_length]]

        df = pd.DataFrame({
            'date': dates,
            'open': stock.data.historical_Stock_Prices[:2*min_length:2],
            'close': stock.data.historical_Stock_Prices[1:2*min_length:2],
            'volume': [stock.data.Volume] * min_length,  # Use the single Volume value for all entries
            'market_cap': [stock.data.MarketCapIntraday] * min_length,
            'pe_ratio': [stock.data.TrailingPE] * min_length,
            'peg_ratio': [stock.data.PEGRatio] * min_length,
            'price_to_book': [stock.data.PriceToBook] * min_length,
            'dividend_yield': [stock.data.trailingAnnualDividendYield] * min_length,
            'debt_to_equity': [stock.data.totalDebtToEquity] * min_length,
            'free_cash_flow': [stock.data.LeveredFreeCashFlow] * min_length,
            'profit_margin': [stock.data.profitMargins] * min_length,
            'roa': [stock.data.returnOnAssets] * min_length,
            'roe': [stock.data.returnOnEquity] * min_length,
        })

        # Add derived features
        df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        df['month'] = pd.to_datetime(df['date']).dt.month
        df['year'] = pd.to_datetime(df['date']).dt.year

        for col in ['open', 'close', 'volume']:
            for lag in [1, 2, 3, 5, 10]:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)

        for col in ['open', 'close', 'volume']:
            for window in [5, 10, 20]:
                df[f'{col}_rolling_{window}'] = df[col].rolling(window=window).mean()

        df['rsi'] = self.calculate_rsi(df['close'])
        df['macd'] = self.calculate_macd(df['close'])

        df.dropna(inplace=True)

        return df


    def prepare_next_day_features(self, features):
        next_day_features = features.iloc[-1:].copy()
        next_day_features['day_of_week'] = (next_day_features['day_of_week'] + 1) % 7
        next_day_features['month'] = next_day_features['month']
        next_day_features['year'] = next_day_features['year']
        
        for col in ['open', 'close', 'volume']:
            for lag in [1, 2, 3, 5, 10]:
                next_day_features[f'{col}_lag_{lag}'] = features[col].iloc[-lag]

        return pd.concat([next_day_features] * 2, ignore_index=True)


    def calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, prices, slow=26, fast=12, signal=9):
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signal, adjust=False).mean()
        return macd - signal

    def get_prediction(self, symbol):
        return self.predictions.get(symbol)

    def get_all_predictions(self):
        return self.predictions

    def get_accuracy(self):
        return self.accuracy

    def train(self):
        pass
    def predict(self, stock):
        features = self.prepare_stock_data(stock)
        if features.empty:
            print(f"Unable to predict for {stock.symbol} due to lack of historical data")
            return None

        next_day_features = self.prepare_next_day_features(features)
        next_day_predictions = self.model.predict(self.scaler.transform(next_day_features))

        self.predictions[stock.symbol] = {
            'next_open': next_day_predictions[0],
            'next_close': next_day_predictions[1]
        }

        return self.predictions[stock.symbol]

    def update_error(self, symbol, error):
        if symbol not in self.errors:
            self.errors[symbol] = []
        self.errors[symbol].append(error)
        if len(self.errors[symbol]) > 100:
            self.errors[symbol] = self.errors[symbol][-100:]
    def adjust_model(self):
        # Implement logic to adjust the model based on recent errors
        pass

    def to_dict(self):
        return {
            'model_path': self.model_path,
            'predictions': self.predictions,
            'accuracy': self.accuracy,
            'errors': self.errors
        }

    @classmethod
    def from_dict(cls, data_dict, stock_list):
        model = cls(stock_list, data_dict['model_path'])
        model.predictions = data_dict['predictions']
        model.accuracy = data_dict['accuracy']
        model.errors = data_dict['errors']
        return model


class Data:
    def __init__(self):
        self.currentPrice: float = 0.0
        self.currentDate: datetime = datetime.now()

        # Financial Metrics
        self.MarketCapIntraday: float = 0.0
        self.EnterpriseValue: float = 0.0
        self.TrailingPE: float = 0.0
        self.ForwardPE: float = 0.0
        self.PEGRatio: float = 0.0
        self.PriceToSales: float = 0.0
        self.PriceToBook: float = 0.0
        self.EVToRevenue: float = 0.0
        self.EVToEBITDA: float = 0.0

        # Stock Performance Metrics
        self.Beta: float = 0.0
        self.FiftyTwoWeekChange: float = 0.0
        self.SandP52WeekChange: float = 0.0
        self.FiftyTwoWeekHigh: float = 0.0
        self.FiftyTwoWeekLow: float = 0.0
        self.FiftyDayAverage: float = 0.0
        self.TwoHundredDayAverage: float = 0.0

        # Volume and Share Statistics
        self.avgVolThreeMonth: int = 0
        self.avgVolTenDay: int = 0
        self.sharesOutstanding: int = 0
        self.ImpliedSharesOutstanding: int = 0
        self.floatShares: int = 0
        self.percentInsiders: float = 0.0
        self.percentInstitutions: float = 0.0
        self.sharesShort: int = 0
        self.shortRatio: float = 0.0
        self.shortPercentOfFloat: float = 0.0
        self.shortPercentOfSharesOutstanding: float = 0.0
        self.sharesShortPriorMonth: int = 0

        # Dividend Information
        self.forwardAnnualDividendRate: float = 0.0
        self.forwardAnnualDividendYield: float = 0.0
        self.trailingAnnualDividendRate: float = 0.0
        self.trailingAnnualDividendYield: float = 0.0
        self.fiveYearAverageDividendYield: float = 0.0
        self.payoutRatio: float = 0.0
        self.dividendDate: Optional[datetime] = None
        self.exDividendDate: Optional[datetime] = None
        self.lastSplitFactor: Optional[str] = None
        self.lastSplitDate: Optional[datetime] = None

        # Financial Dates
        self.FiscalYearEnd: Optional[datetime] = None
        self.MostRecentQuarter: Optional[datetime] = None

        # Profitability Metrics
        self.profitMargins: float = 0.0
        self.operatingMargins: float = 0.0
        self.returnOnAssets: float = 0.0
        self.returnOnEquity: float = 0.0

        # Financial Statement Items
        self.revenue: float = 0.0
        self.revenuePerShare: float = 0.0
        self.quarterlyRevenueGrowth: float = 0.0
        self.grossProfit: float = 0.0
        self.ebitda: float = 0.0
        self.netIncomeAvlToCommon: float = 0.0
        self.dilutedEPS: float = 0.0
        self.quarterlyEarningsGrowth: float = 0.0
        self.totalCash: float = 0.0
        self.totalCashPerShare: float = 0.0
        self.totalDebt: float = 0.0
        self.totalDebtToEquity: float = 0.0
        self.currentRatio: float = 0.0
        self.bookValue: float = 0.0
        self.OperatingCashFlow: float = 0.0
        self.LeveredFreeCashFlow: float = 0.0

        # Additional Metrics
        self.currentDividend: float = 0.0
        self.currentYield: float = 0.0
        self.differencePercentage: float = 0.0
        self.currentTrend: str = "Neutral"
        self.TrendTypes: List[str] = ["Hourly", "Daily", "Weekly", "Monthly", "Yearly", "Lifetime"]
        self.Trends: dict = {
            "Hourly": "Neutral",
            "Daily": "Neutral",
            "Weekly": "Neutral",
            "Monthly": "Neutral",
            "Yearly": "Neutral",
            "Lifetime": "Neutral"
        }
        self.previousClose: float = 0.0
        self.openPrice: float = 0.0
        self.Volume: int = 0
        self.AvgVolume3M: int = 0
        self.PEratio: float = 0.0
        self.MarketCap: float = 0.0
        self.ForwardDividend: float = 0.0
        self.oneYearTarget: float = 0.0

        # Historical Data
        self.historical_Stock_Prices: List[float] = []
        self.historical_Dates: List[datetime] = []
        self.historical_Trends: List[str] = []

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def __getitem__(self, key):
        return getattr(self, key)

    def get_latest_data(self):
        return {
            'price': self.currentPrice,
            'date': self.currentDate,
            'volume': self.Volume,
            'trend': self.currentTrend
        }
class Stock:
    def __init__(self, symbol, session):
        self.symbol = symbol
        self.session = session
        self.company_name = self.get_company_name()
        self.data = Data()
        self.predictions = []
        self.predictionDates = []
        self.last_update = None
        self.quantity = 0
        self.investment = 0
        self.in_watchlist = False
        self.watchlist_date: Optional[datetime] = None  # Use Optional to allow None or datetime
        self.model_parameters = None

    def get_company_name(self):
        try:
            stock = yf.Ticker(self.symbol, session=self.session)
            return stock.info.get('longName', 'N/A')
        except Exception as e:
            print(f"Error fetching company name for {self.symbol}: {str(e)}")
            return 'N/A'

    def update_live_data(self):
        try:
            stock = yf.Ticker(self.symbol, session=self.session)
            info = stock.info
            history = stock.history(period="1d")

            if not history.empty:
                self.data.currentPrice = history['Close'].iloc[-1]
                self.data.currentDate = datetime.now()
                self.last_update = self.data.currentDate
                self.add_historical_data_point(self.data.currentPrice, self.data.currentDate)

            # Update Data object with fetched information
            self.data.MarketCapIntraday = info.get('marketCap', 0)
            self.data.EnterpriseValue = info.get('enterpriseValue', 0)
            self.data.TrailingPE = info.get('trailingPE', 0)
            self.data.ForwardPE = info.get('forwardPE', 0)
            self.data.PEGRatio = info.get('pegRatio', 0)
            self.data.PriceToSales = info.get('priceToSalesTrailing12Months', 0)
            self.data.PriceToBook = info.get('priceToBook', 0)
            self.data.EVToRevenue = info.get('enterpriseToRevenue', 0)
            self.data.EVToEBITDA = info.get('enterpriseToEbitda', 0)
            
            # ... Continue updating all other fields in the Data object
            
            self.calculate_trends()
        except Exception as e:
            print(f"Error fetching data for {self.symbol}: {str(e)}")

    def add_historical_data_point(self, price, date):
        self.data.historical_Stock_Prices.append(price)
        self.data.historical_Dates.append(date)
        # Keep only the last 1000 points
        if len(self.data.historical_Stock_Prices) > 1000:
            self.data.historical_Stock_Prices = self.data.historical_Stock_Prices[-1000:]
            self.data.historical_Dates = self.data.historical_Dates[-1000:]

    def predict(self, days=5):
        if len(self.data.historical_Stock_Prices) < 30:  # Ensure we have enough data
            return None

        df = pd.DataFrame({
            'date': self.data.historical_Dates,
            'price': self.data.historical_Stock_Prices
        })
        df.set_index('date', inplace=True)
        df['Prediction'] = df['price'].shift(-1)
        df = df.dropna()

        X = df[['price']]
        y = df['Prediction']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        

        last_data = X.tail(1)
        predictions = []
        prediction_dates = []
        current_date = datetime.now().date()
        for i in range(days):
            next_day = current_date + timedelta(days=i+1)
            next_day_pred = model.predict(last_data)[0]
            predictions.append(next_day_pred)
            prediction_dates.append(next_day)
            last_data = pd.DataFrame({'price': [next_day_pred]})

        self.predictions = predictions
        self.predictionDates = prediction_dates
        self.model_parameters = model.get_params()

        return list(zip(prediction_dates, predictions))

    def calculate_trends(self):
        if len(self.data.historical_Stock_Prices) < 2:
            return
        self.data.Trends = {
            'hourly': self._calculate_trend_for_period(timedelta(hours=1)),
            'daily': self._calculate_trend_for_period(timedelta(days=1)),
            'weekly': self._calculate_trend_for_period(timedelta(weeks=1)),
            'monthly': self._calculate_trend_for_period(timedelta(days=30)),
            'yearly': self._calculate_trend_for_period(timedelta(days=365)),
            'Lifetime': self._calculate_trend_for_period(None)
        }

        self.data.currentTrend = self.data.Trends['hourly']

    def _calculate_trend_for_period(self, period):
        current_time = self.data.historical_Dates[-1]
        current_price = self.data.historical_Stock_Prices[-1]
        
        if period:
            start_time = current_time - period
            start_index = next((i for i, date in enumerate(self.data.historical_Dates) if date > start_time), 0)
        else:
            start_index = 0

        if start_index < len(self.data.historical_Stock_Prices):
            start_price = self.data.historical_Stock_Prices[start_index]
            return self._calculate_trend(start_price, current_price)
        return "Neutral"

    def _calculate_trend(self, start_price, end_price):
        change = ((end_price - start_price) / start_price) * 100
        if change > 10:
            return "Strong Up"
        elif change > 2:
            return "Up"
        elif change < -10:
            return "Strong Down"
        elif change < -2:
            return "Down"
        else:
            return "Neutral"

    def get_recommendation(self):
        if not self.predictions:
            return "Insufficient data"
        
        avg_prediction = sum(self.predictions) / len(self.predictions)
        
        if avg_prediction > self.data.currentPrice * 1.05:
            return "Strong Buy"
        elif avg_prediction > self.data.currentPrice:
            return "Buy"
        elif avg_prediction < self.data.currentPrice * 0.95:
            return "Strong Sell"
        elif avg_prediction < self.data.currentPrice:
            return "Sell"
        else:
            return "Hold"

    def get_latest_data(self):
        return self.data[-1] if self.data else None # Return the latest data point

        

    def __iter__(self):
        return iter(self.data)

    @classmethod
    def from_dict(cls, data, session):
        stock = cls(data['symbol'], session)
        for key, value in data.get('data', {}).items():
            setattr(stock.data, key, value)
        return stock

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'data': {key: value for key, value in self.data}
        }
class StockAnalyzer:        
    def __init__(self, root):
        self.max_retries = 5
        self.retry_delay = 10  # seconds
        self._cache = {}
        self._cache_time = {}
        self.root = root
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Console Messages")
        self.console_output = ScrolledText(self.console_window, wrap=tk.WORD, width=100, height=20)
        self.console_output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Console logger
        self.console = Console(self.console_output)

        print("Stock Analyzer Initializing...")
        self.time_zone = pytz.timezone('US/Mountain')  # Default to Mountain Time
        self.market_tz = pytz.timezone('US/Eastern')   # Market operates on Eastern Time
        # Initialize the session
        self.session = CachedLimiterSession(
            limiter=Limiter(RequestRate(2, Duration.SECOND*5)),  # max 2 requests per 5 seconds
            bucket_class=MemoryQueueBucket
        )
        self.session.headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        
        print("Initialized session.")
        print("Initializing system data...")
        self._portfolio = {}
        self._predictions = {}
        self._investments = {}
        self._cache = {}
        self._cache_time = {}
        self._company_names = {}
        self._trends = {
            'hourly': {},
            'daily': {},
            'weekly': {},
            'monthly': {},
            'yearly': {},
            'overall': {}
        }
        self._recommendations = {}
        self._watchlist = {}
        self._all_stocks = {}  # Dictionary to hold all stocks
        self._model_parameters = {}
        self.stock_models = {} # List of stock models
        self._prediction_history = {}
        self._historical_data = {}  # Store historical price data
        self._historical_reports = {}  # Store previous report data
        self._notification_settings = {
            'email': '',
            'phone': '',
            'daily_update': False,
            'real_time_alerts': False
        }
        self._settings = {
            'smtp_configured': False,
            'twilio_configured': False
        }
        self._smtp_settings = {
            'sender_email': '',
            'sender_password': '',
            'smtp_server': '',
            'smtp_port': 587
        }
        self._sms_gateways = {
            'AT&T': '@txt.att.net',
            'T-Mobile': '@tmomail.net',
            'Verizon': '@vtext.com',
            'Sprint': '@messaging.sprintpcs.com',
            'Boost Mobile': '@sms.myboostmobile.com',
            'Cricket': '@sms.cricketwireless.net',
            'Metro PCS': '@mymetropcs.com',
            'Tracfone': '@mmst5.tracfone.com',
            'U.S. Cellular': '@email.uscc.net',
            'Virgin Mobile': '@vmobl.com',
            'Visible': '@vtext.com',
            'Google Fi': '@msg.fi.google.com',
            'Consumer Cellular': '@mailmymobile.net',
            'Xfinity Mobile': '@vtext.com',
            'Mint Mobile': '@mailmymobile.net'

        }
        self._sms_settings = {
            'phone_number': '',
            'carrier': ''
        }
        self._mailjet_settings = {
            'api_key': '',
            'api_secret': '',
            'sender_email': '',
            'sender_name': 'Stock Analyzer'
        }
        self._last_alert_prices = {}
        self._last_alert_times = {}
        self.load_data()
        self.update_watchlist_company_names()
        self.background_thread = None
        self.background_thread_two = None
        self.set_time_zone('US/Mountain')
        self.is_training = False
        self.is_downloading = False
        self.startup_notification()
        self.start_background_checks()
        self.main()

    def _initialize_empty_data(self):
        self.is_training = False
        self.is_downloading = False
        self.background_thread = None
        self.background_thread_two = None
        self._trends = {
            'hourly': {},
            'daily': {},
            'weekly': {},
            'monthly': {},
            'yearly': {},
            'overall': {}
        }
        # Initialize the session
        self.session = CachedLimiterSession(
            limiter=Limiter(RequestRate(2, Duration.SECOND*5)),  # max 2 requests per 5 seconds
            bucket_class=MemoryQueueBucket
        )
        self.session.headers['User-agent'] = 'my_stock_analyzer/1.0'
        self._portfolio = {}
        self._investments = {}
        self._predictions = {}
        self._company_names = {}
        self._trends = {}
        self._recommendations = {}
        self._watchlist = {}
        self._last_alert_prices = {}
        self._last_alert_times = {}
        self._model_parameters = {}
        self._prediction_history = {}
        self.stock_models = {}

        self._historical_data = {}  # Store historical price data
        self._historical_reports = {}  # Store previous report data
        self._notification_settings = {'email': '', 'phone': '', 'daily_update': False, 'real_time_alerts': False}
        self._settings = {'smtp_configured': False, 'twilio_configured': False}
        self._smtp_settings = {'sender_email': '', 'sender_password': '', 'smtp_server': '', 'smtp_port': 587}
        self._sms_settings = {'phone_number': '', 'carrier': ''}
        self._mailjet_settings = {'api_key': '', 'api_secret': '', 'sender_email': '', 'sender_name': 'Stock Analyzer'}
        self.console.log("Initialized with empty data.")
    
    def display_console_messages(self, n=10):
        messages = self.console.get_recent_messages(n)
        if not messages:
            print("No recent console messages.")
        else:
            print("\nRecent Console Messages:")
            for message in messages:
                print(message)

    def _ensure_stock_object(self, stock_or_symbol):
        if isinstance(stock_or_symbol, str):
            if stock_or_symbol not in self._all_stocks:
                new_stock = Stock(stock_or_symbol, self.session)
                self._all_stocks[stock_or_symbol] = new_stock
                self.update_historical_data(new_stock)
            return self._all_stocks[stock_or_symbol]
        elif isinstance(stock_or_symbol, Stock):
            if stock_or_symbol.symbol not in self._all_stocks:
                self._all_stocks[stock_or_symbol.symbol] = stock_or_symbol
                self.update_historical_data(stock_or_symbol)
            return stock_or_symbol
        else:
            raise ValueError("Input must be a string symbol or Stock object")

    def add_to_tracked_stocks(self, stock_or_symbol):
        stock = self._ensure_stock_object(stock_or_symbol)
        if stock.symbol not in self._all_stocks:
            self._all_stocks[stock.symbol] = stock
            stock.update_live_data()  # This will also calculate trends
            self.console.log(f"Added {stock.symbol} to the list of tracked stocks")
        else:
            self.console.log(f"{stock.symbol} is already being tracked")

    def remove_from_tracked_stocks(self, stock_or_symbol):
        stock = self._ensure_stock_object(stock_or_symbol)
        if stock.symbol in self._all_stocks:
            del self._all_stocks[stock.symbol]
            if stock.symbol in self._portfolio:
                del self._portfolio[stock.symbol]
            if stock.symbol in self._watchlist:
                del self._watchlist[stock.symbol]
            self.console.log(f"Removed {stock.symbol} from the list of tracked stocks")
        else:
            self.console.log(f"{stock.symbol} is not in the list of tracked stocks")

    
    def add_to_watchlist(self, stock_or_symbol):
        stock = self._ensure_stock_object(stock_or_symbol)
        if stock.symbol not in self._all_stocks:
            self.add_to_tracked_stocks(stock)
        
        self._watchlist[stock.symbol] = stock
        stock.in_watchlist = True
        stock.watchlist_date = datetime.now()
        self.console.log(f"Added {stock.symbol} to watchlist")

    def remove_from_watchlist(self, stock_or_symbol):
        stock = self._ensure_stock_object(stock_or_symbol)
        if stock.symbol in self._watchlist:
            del self._watchlist[stock.symbol]
            stock.in_watchlist = False
            stock.watchlist_date = None
            self.console.log(f"Removed {stock.symbol} from watchlist")
        else:
            self.console.log(f"{stock.symbol} is not in the watchlist")

    def clear_console_messages(self):
        self.console.clear_messages()
        self.console.log("Console messages cleared.")

    def set_max_console_messages(self, max_messages):
        try:
            max_messages = int(max_messages)
            if max_messages < 1:
                raise ValueError("Maximum messages must be at least 1.")
            self.console.set_max_messages(max_messages)
            self.console.log(f"Maximum console messages set to {max_messages}.")
            self.save_data()
        except ValueError as e:
            self.console.log(f"Error setting maximum messages: {str(e)}")

    def get_max_console_messages(self):
        return self.console.get_max_messages()
    
    @property
    def portfolio(self):
        return self._portfolio

    @property
    def predictions(self):
        return self._predictions

    @property
    def investments(self):
        return self._investments

    def add_stock(self, symbol, quantity, investment):
        if symbol not in self._portfolio:
            stock = Stock(symbol, self.session)
            stock.quantity = quantity
            stock.investment = investment
            self._portfolio[symbol] = stock
            self._all_stocks[symbol] = stock
            self.update_stock_data(symbol)
            self.console.log(f"Added {quantity} shares of {symbol} to portfolio")
            return f"Added {quantity} shares of {symbol} ({stock.company_name}) to portfolio"
        else:
            self.console.log(f"{symbol} already exists in portfolio")
            return f"{symbol} already exists in portfolio"

        
    def remove_stock(self, stock_or_symbol):
        stock = self._ensure_stock_object(stock_or_symbol)
        if stock.symbol in self._portfolio:
            del self._portfolio[stock.symbol]
            self.console.log(f"Removed {stock.symbol} from portfolio")
        else:
            self.console.log(f"{stock.symbol} is not in the portfolio")

    def update_all_stocks(self):
        for symbol in self._all_stocks:
            self.update_stock_data(symbol)

    
    def predict_best_stocks(self, top_n=5):
        predictions = []
        for stock in self._all_stocks.values():
            try:
                prediction = stock.predict(days=30)  # Predict for the next 30 days
                if prediction:
                    expected_return = (prediction[-1][1] - stock.data.currentPrice) / stock.data.currentPrice
                    predictions.append((stock.symbol, expected_return))
            except Exception as e:
                self.console.log(f"Error predicting for {stock.symbol}: {str(e)}")

        # Sort stocks by expected return (descending order) and return top N
        return sorted(predictions, key=lambda x: x[1], reverse=True)[:top_n]

    def get_company_name(self, symbol):
        try:
            stock = yf.Ticker(symbol, session=session)
            return stock.info.get('longName', 'N/A')
        except Exception as e:
            print(f"Error fetching company name for {symbol}: {str(e)}")
            return 'N/A'

    def get_stock_info(self, symbol):
        try:
            stock = yf.Ticker(symbol, session=session)
            return stock.info
        except Exception as e:
            print(f"Error fetching info for {symbol}: {str(e)}")
            return None

    def get_live_data(self, symbol):
        current_time = time.time()
        if symbol in self._cache and current_time - self._cache_time.get(symbol, 0) < 300:  # Cache for 5 minutes
            return self._cache[symbol]

        retries = 0
        while retries < self.max_retries:
            try:
                stock = yf.Ticker(symbol, session=self.session)
                data = stock.history(period="1d")
                if not data.empty:
                    price = data['Close'].iloc[-1]
                    self._cache[symbol] = price
                    self._cache_time[symbol] = current_time
                    return price
                else:
                    raise ValueError(f"No data available for {symbol}")
            except (RequestException, ValueError) as e:
                retries += 1
                self.console.log(f"Error fetching live data for {symbol} (Attempt {retries}/{self.max_retries}): {str(e)}")
                if retries < self.max_retries:
                    self.console.log(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    self.console.log(f"Failed to fetch live data for {symbol} after {self.max_retries} attempts.")
                    return 0  # Return 0 if all retries fail

    def get_historical_data(self, symbol, period="20y"):
        try:
            stock = yf.Ticker(symbol, session=session)
            return stock.history(period=period)
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def add_shares(self, symbol: str, quantity: float, investment: float = 0.0):
        if symbol in self._portfolio:
            self._portfolio[symbol] += quantity
            self._investments[symbol] += investment
            message = f"Added {quantity} shares of {symbol} to your existing position. New total: {self._portfolio[symbol]} shares."
        else:
            message = f"{symbol} is not in your portfolio. Use 'Add Stock' option to add a new stock."
        self.save_data()
        self.send_notification("Shares Added", message)
        return message

    def remove_shares(self, symbol: str, quantity: float):
        if symbol in self._portfolio:
            if self._portfolio[symbol] >= quantity:
                self._portfolio[symbol] -= quantity
                removed_investment = (quantity / self._portfolio[symbol]) * self._investments[symbol]
                self._investments[symbol] -= removed_investment
                message = f"Removed {quantity} shares of {symbol}. New total: {self._portfolio[symbol]} shares."
                if self._portfolio[symbol] == 0:
                    del self._portfolio[symbol]
                    del self._investments[symbol]
                    message += f" {symbol} has been removed from your portfolio."
            else:
                message = f"Error: You don't have {quantity} shares of {symbol} to remove."
        else:
            message = f"Error: {symbol} is not in your portfolio."
        self.save_data()
        self.send_notification("Shares Removed", message)
        return message

    def override_shares(self, symbol: str, quantity: float):
       if symbol in self._portfolio:
           old_quantity = self._portfolio[symbol]
           self._portfolio[symbol] = quantity
           self._investments[symbol] = (quantity / old_quantity) * self._investments[symbol]
           message = f"Updated {symbol} shares from {old_quantity} to {quantity}."
           current_price = self.get_live_data(symbol)
           current_value = quantity * current_price
           message += f"\nCurrent value: ${current_value:.2f}"
           self.save_data()
           self.send_notification("Shares Updated", message, symbol=symbol)
           return message
       else:
           message = f"Error: {symbol} is not in your portfolio. Use 'Add Stock' option to add a new stock."
           self.console.log(message)
           return message


    def revert_last_change(self):
        backup_files = [f for f in os.listdir('.') if f.startswith('portfolio_data_backup_') and f.endswith('.json')]
        if not backup_files:
            return "No backup files found. Cannot revert changes."

        latest_backup = max(backup_files)
        try:
            with open(latest_backup, 'r') as f:
                data = json.load(f)
            
            self._portfolio = data.get('portfolio', {})
            self._investments = data.get('investments', {})
            self._predictions = data.get('predictions', {})
            self._company_names = data.get('company_names', {})
            self._trends = data.get('trends', {})
            self._recommendations = data.get('recommendations', {})
            self._watchlist = data.get('watchlist', {})
            self._model_parameters = data.get('model_parameters', {})
            self._prediction_history = data.get('prediction_history', {})
            
            # Convert watchlist dates back to datetime objects
            for symbol, watch_data in self._watchlist.items():
                if 'added_date' in watch_data:
                    watch_data['added_date'] = datetime.fromisoformat(watch_data['added_date'])

            os.remove(latest_backup)
            self.save_data()  # Save the reverted data
            return f"Successfully reverted to backup: {latest_backup}"
        except Exception as e:
            return f"Error reverting to backup: {str(e)}"
    
    # ... (previous methods remain the same)

    def predict_stock(self, stock_or_symbol, days=5):
        if self.is_training or self.is_downloading:
            print("Warning: Model is currently training or downloading data. Predictions may not be up to date.")
        
        stock = self._ensure_stock_object(stock_or_symbol)
        symbol = stock.symbol

        if symbol not in self.stock_models:
            self.console.log(f"Creating new model for {symbol}")
            self.stock_models[symbol] = StockAnalyzerModel([stock], model_path=f'models/{symbol}_model.h5')
            self.stock_models[symbol].start()

        model = self.stock_models[symbol]

        # Ensure we have the latest data
        self.update_stock_data(stock)

        # Make prediction
        predictions = model.predict(stock, days)
        
        # Store predictions
        self._predictions[symbol] = predictions
        
        # Update the stock's predictions
        stock.predictions = [pred['price'] for pred in predictions]
        stock.predictionDates = [pred['date'] for pred in predictions]

        # Save data
        self.save_data()

        return predictions

    def get_prediction_accuracy(self, symbol):
        if symbol in self.stock_models:
            return self.stock_models[symbol].accuracy.get(symbol)

    def get_next_market_predictions(self, symbol):
        if symbol in self.stock_models:
            return self.stock_models[symbol].get_prediction(symbol)
        return None

    def manage_backups(self, max_backups=10):
        backup_files = [f for f in os.listdir('.') if f.startswith('portfolio_data_backup_') and f.endswith('.json')]
        backup_files.sort(reverse=True)  # Sort in descending order (newest first)
        
        if len(backup_files) > max_backups:
            for old_backup in backup_files[max_backups:]:
                try:
                    os.remove(old_backup)
                    self.console.log(f"Removed old backup: {old_backup}")
                except Exception as e:
                    self.console.log(f"Error removing old backup {old_backup}: {str(e)}")

    def get_trend(self, symbol):
        data = self.get_historical_data(symbol, period="1mo")
        if data.empty:
            return "Unknown"

        start_price = data['Close'].iloc[0]
        end_price = data['Close'].iloc[-1]

        change = (end_price - start_price) / start_price * 100

        if change > 5:
            return "Strong Up"
        elif change > 0:
            return "Up"
        elif change < -5:
            return "Strong Down"
        elif change < 0:
            return "Down"
        else:
            return "Neutral"

    def update_watchlist_company_names(self):
        for symbol in self._watchlist:
            if 'company_name' not in self._watchlist[symbol]:
                self._watchlist[symbol]['company_name'] = self.get_company_name(symbol)
        self.save_data()

    def get_recommendation(self, current_price, predictions):
        if not predictions:
            return "Insufficient data"
        
        avg_prediction = sum(predictions) / len(predictions)
        if avg_prediction > current_price * 1.05:
            return "Strong Buy"
        elif avg_prediction > current_price:
            return "Buy"
        elif avg_prediction < current_price * 0.95:
            return "Strong Sell"
        elif avg_prediction < current_price:
            return "Sell"
        else:
            return "Hold"

    def adjust_model(self, symbol):
        if symbol not in self._prediction_history:
            return

        actual_prices = self.get_historical_data(symbol, period="20y")['Close'].tolist()
        predicted_prices = self._prediction_history[symbol][-5:]  # Last 5 predictions

        if len(actual_prices) < 5 or len(predicted_prices) < 5:
            return

        mse = np.mean((np.array(actual_prices[-5:]) - np.array(predicted_prices)) ** 2)
        
        if mse > 0.01:  # Threshold for model adjustment
            current_n_estimators = self._model_parameters[symbol].get('n_estimators', 100)
            new_n_estimators = max(50, min(500, int(current_n_estimators * (1 + mse))))
            self._model_parameters[symbol]['n_estimators'] = new_n_estimators
            self.console.log(f"Adjusted model for {symbol}. New n_estimators: {new_n_estimators}")

    def get_market_hours(self):
        # Assuming US market hours
        now = datetime.now()
        market_open = datetime(now.year, now.month, now.day, 9, 30)  # 9:30 AM
        market_close = datetime(now.year, now.month, now.day, 16, 0)  # 4:00 PM
        return market_open, market_close

    def generate_daily_report(self):
        market_open, market_close = self.get_market_hours()
        report = f"Market Open Report - {market_open.strftime('%Y-%m-%d')}\n\n"

        # Portfolio stocks
        report += "Portfolio Stocks:\n"
        for symbol in self._portfolio:
            current_price = self.get_live_data(symbol)
            predictions = self.predict_stock(symbol)
            self.calculate_trends(symbol)
            if predictions:
                projected_close = predictions[0]
                projected_next_open = predictions[1]
            else:
                projected_close = projected_next_open = "N/A"

            trend = self._trends.get(symbol, self.get_trend(symbol))
            recommendation = self.get_recommendation(current_price, predictions)

            report += f"{symbol} ({self._company_names.get(symbol, 'N/A')}):\n"
            report += f"  Current Price: ${current_price:.2f}\n"
            report += f"  Projected Close: ${projected_close:.2f}\n"
            report += f"  Projected Next Open: ${projected_next_open:.2f}\n"
            report += f"  Trend: {trend}\n"
            report += f"  Recommendation: {recommendation}\n\n"

        # Watchlist stocks
        if self._watchlist:
            report += "Watchlist Stocks:\n"
            for symbol in self._watchlist:
                current_price = self.get_live_data(symbol)
                initial_price = self._watchlist[symbol]['initial_price']
                price_change = (current_price - initial_price) / initial_price * 100
                recommendation = self.get_recommendation(current_price, self.predict_stock(symbol))

                report += f"{symbol}:\n"
                report += f"  Current Price: ${current_price:.2f}\n"
                report += f"  Price Change: {price_change:.2f}%\n"
                report += f"  Recommendation: {recommendation}\n\n"

        self.send_notification("Daily Market Open Report", report)

    def should_send_alert(self, symbol, current_price, predicted_price):
        # Check if we have sent an alert recently
        last_alert_time = self._last_alert_times.get(symbol)
        if last_alert_time and (datetime.now() - last_alert_time) < timedelta(hours=1):
            return False  # Don't send alerts more often than once per hour

        # Check if the price has changed significantly since the last alert
        last_alert_price = self._last_alert_prices.get(symbol)
        if last_alert_price:
            price_change = abs((current_price - last_alert_price) / last_alert_price)
            if price_change < 0.02:  # Less than 2% change
                return False

        # Check if the predicted price differs significantly from the current price
        price_difference = abs((current_price - predicted_price) / current_price)
        if price_difference > 0.05:  # More than 5% difference
            return True

        # Check for significant trend changes
        stock = self._portfolio.get(symbol) or self._watchlist.get(symbol)
        if stock:
            current_trend = stock.data.currentTrend
            if current_trend in ["Strong Up", "Strong Down"]:
                return True

        return False

    def update_last_alert(self, symbol, price):
        self._last_alert_prices[symbol] = price
        self._last_alert_times[symbol] = datetime.now()
        self.save_data()  # Make sure to save the updated data

        stock = self._portfolio.get(symbol) or self._watchlist.get(symbol)
        if not stock:
            return

        current_price = stock.data.currentPrice
        self.update_historical_data(symbol)  # Update historical data and trends
        predictions = stock.predictions

        if predictions:
            predicted_price = predictions[0]  # Use the first prediction

            if self.should_send_alert(symbol, current_price, predicted_price):
                price_difference = abs((current_price - predicted_price) / predicted_price) * 100

                message = f"Alert: Significant change predicted for {symbol}\n"
                message += f"Current Price: ${current_price:.2f}\n"
                message += f"Predicted Price: ${predicted_price:.2f}\n"
                message += f"Difference: {price_difference:.2f}%\n"
                message += "Trends:\n"
                for trend_type in ['Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly', 'Lifetime']:
                    trend_value = stock.data.Trends.get(trend_type, 'N/A')
                    message += f"  {trend_type}: {trend_value}\n"

                self.send_notification(f"Stock Alert - {symbol}", message)
                self.update_last_alert(symbol, current_price)
    
    def set_time_zone(self, tz_string):
        try:
            self.time_zone = pytz.timezone(tz_string)
            self.console.log(f"Time zone set to: {tz_string}")
        except pytz.exceptions.UnknownTimeZoneError:
            self.console.log(f"Unknown time zone: {tz_string}. Keeping current time zone.")

    def get_adjusted_market_time(self, hour, minute):
        market_time = self.market_tz.localize(datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0))
        local_time = market_time.astimezone(self.time_zone)
        return local_time.strftime("%H:%M")

    def background_task(self):
        while True:
            self.is_training = True
            for symbol, model in self.stock_models.items():
                model.train()
            self.is_training = False
            time.sleep(3600)  # S
    def background_tasks(self):
        open_time = self.get_adjusted_market_time(9, 30)  # 9:30 AM ET
        close_time = self.get_adjusted_market_time(16, 0)  # 4:00 PM ET

        schedule.every().monday.at(open_time).do(self.generate_market_report, "open")
        schedule.every().monday.at(close_time).do(self.generate_market_report, "close")
        schedule.every().tuesday.at(open_time).do(self.generate_market_report, "open")
        schedule.every().tuesday.at(close_time).do(self.generate_market_report, "close")
        schedule.every().wednesday.at(open_time).do(self.generate_market_report, "open")
        schedule.every().wednesday.at(close_time).do(self.generate_market_report, "close")
        schedule.every().thursday.at(open_time).do(self.generate_market_report, "open")
        schedule.every().thursday.at(close_time).do(self.generate_market_report, "close")
        schedule.every().friday.at(open_time).do(self.generate_market_report, "open")
        schedule.every().friday.at(close_time).do(self.generate_market_report, "close")

        schedule.every(15).minutes.do(self.check_for_drastic_changes)

        self.console.log(f"Scheduled market open report for {open_time} local time")
        self.console.log(f"Scheduled market close report for {close_time} local time")

        while True:
            schedule.run_pending()
            time.sleep(60)

    def generate_report(self, report_type, for_sms=False, symbol=None):
        try:
            if report_type == "startup":
                title = "Stock Analyzer System Online"
            elif report_type in ["open", "close"]:
                title = f"Market {report_type.capitalize()} Report"
            elif report_type == "update":
                title = "Stock Update"
            else:
                title = "Stock Report"

            report = f"{title} - {datetime.now(self.time_zone).strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"

            if for_sms:
                if symbol and symbol in self._portfolio:
                    self.calculate_trends(symbol)
                    current_price = self.get_live_data(symbol)
                    quantity = self._portfolio.get(symbol, 0)
                    investment = self._investments.get(symbol, 0)
                    current_value = quantity * current_price
                    profit_loss = current_value - investment
                    profit_loss_percentage = (profit_loss / investment) * 100 if investment != 0 else 0
                    report += f"{symbol} Update:\n"
                    report += f"Shares: {quantity}\n"
                    report += f"Price: ${current_price:.2f}\n"
                    report += f"Value: ${current_value:.2f}\n"
                    report += f"P/L: ${profit_loss:.2f} ({profit_loss_percentage:.2f}%)"
                else:
                    report += "Portfolio Summary:\n"
                    total_value = 0
                    total_profit_loss = 0
                    for sym in self._portfolio:
                        current_price = self.get_live_data(sym)
                        quantity = self._portfolio.get(sym, 0)
                        investment = self._investments.get(sym, 0)
                        current_value = quantity * current_price
                        profit_loss = current_value - investment
                        total_value += current_value
                        total_profit_loss += profit_loss
                        profit_loss_percentage = (profit_loss / investment * 100) if investment != 0 else 0
                        report += f"{sym}: ${current_price:.2f} ({profit_loss_percentage:.2f}%)\n"
                    report += f"\nTotal Value: ${total_value:.2f}\n"
                    total_investment = sum(self._investments.values())
                    total_profit_loss_percentage = (total_profit_loss / total_investment * 100) if total_investment != 0 else 0
                    report += f"Total P/L: ${total_profit_loss:.2f} ({total_profit_loss_percentage:.2f}%)\n"
            else:
                report += "Current Portfolio Status:\n"
                for sym in self._portfolio:
                    current_price = self.get_live_data(sym)
                    self.update_historical_data(sym)  # This will also update trends
                    quantity = self._portfolio.get(sym, 0)
                    investment = self._investments.get(sym, 0)
                    current_value = quantity * current_price

                    report += f"{sym} ({self._company_names.get(sym, 'N/A')}):\n"
                    report += f"  Shares: {quantity}\n"
                    report += f"  Current Price: ${current_price:.2f}\n"
                    report += f"  Current Value: ${current_value:.2f}\n"

                    # Add trend information
                    report += "  Trends:\n"
                    for trend_type in ['hourly', 'daily', 'weekly', 'monthly', 'yearly', 'overall']:
                        trend = self._trends.get(trend_type, {}).get(sym, 'N/A')
                        report += f"    {trend_type.capitalize()}: {trend}\n"

                    # Compare with previous reports
                    if sym in self._historical_reports:
                        last_report = self._historical_reports[sym][-1] if self._historical_reports[sym] else None
                        second_last_report = self._historical_reports[sym][-2] if len(self._historical_reports[sym]) > 1 else None

                        if last_report:
                            price_diff = current_price - last_report['price']
                            price_diff_percent = (price_diff / last_report['price']) * 100 if last_report['price'] != 0 else 0
                            report += f"  Price in last report: ${last_report['price']:.2f}\n"
                            report += f"  Change since last report: ${price_diff:.2f} ({price_diff_percent:.2f}%)\n"

                        if second_last_report:
                            price_diff = current_price - second_last_report['price']
                            price_diff_percent = (price_diff / second_last_report['price']) * 100 if second_last_report['price'] != 0 else 0
                            report += f"  Price two reports ago: ${second_last_report['price']:.2f}\n"
                            report += f"  Change since two reports ago: ${price_diff:.2f} ({price_diff_percent:.2f}%)\n"
                    report += "\n"

                # Add Watchlist information
                if self._watchlist:
                    report += "\nWatchlist:\n"
                    for sym in self._watchlist:
                        current_price = self.get_live_data(sym)
                        watchlist_item = self._watchlist.get(sym, {})
                        company_name = watchlist_item.get('company_name', 'N/A')
                        initial_price = watchlist_item.get('initial_price', 0)
                        price_change = (current_price - initial_price) / initial_price * 100 if initial_price != 0 else 0

                        report += f"{sym} ({company_name}):\n"
                        report += f"  Current Price: ${current_price:.2f}\n"
                        report += f"  Initial Price: ${initial_price:.2f}\n"
                        report += f"  Change: {price_change:.2f}%\n"

                        # Compare with previous reports for watchlist items
                        if sym in self._historical_reports:
                            last_report = self._historical_reports[sym][-1] if self._historical_reports[sym] else None
                            second_last_report = self._historical_reports[sym][-2] if len(self._historical_reports[sym]) > 1 else None

                            if last_report and second_last_report:
                                price_diff = last_report['price'] - second_last_report['price']
                                price_diff_percent = (price_diff / second_last_report['price']) * 100 if second_last_report['price'] != 0 else 0
                                report += f"  Change between last two reports: ${price_diff:.2f} ({price_diff_percent:.2f}%)\n"
                            report += "\n"

                # Update historical reports
                for sym in list(self._portfolio) + list(self._watchlist):
                    if sym not in self._historical_reports:
                        self._historical_reports[sym] = []
                    self._historical_reports[sym].append({
                        'date': datetime.now(),
                        'price': self.get_live_data(sym)
                    })
                    # Keep only the last 10 reports
                    self._historical_reports[sym] = self._historical_reports[sym][-10:]

            self.save_data()  # Save updated data
            return report
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}\nType: {type(e)}\nLine: {e.__traceback__.tb_lineno}"
            self.console.log(error_msg)
            return error_msg
    def start_background_checks(self):
        if self.background_thread is None or not self.background_thread.is_alive():
            self.background_thread = threading.Thread(target=self.background_task)
            self.background_thread.daemon = True
            self.background_thread.start()
        if self.background_thread_two is None or not self.background_thread_two.is_alive():
            self.background_thread_two = threading.Thread(target=self.download_stock_data_background)
            self.background_thread_two.daemon = True
            self.background_thread_two.start()
    def download_stock_data(self, symbol, start_date="2000-01-01"):
        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date)
        if hist.empty:
            return None
        data = {
            "symbol": symbol,
            "history": hist.to_dict(orient="records"),
            "info": stock.info,
        }
        return data

    def save_stock_data_to_json(self, data, filename="stock_data.json"):
        if os.path.exists(filename):
            with open(filename, "r") as file:
                existing_data = json.load(file)
        else:
            existing_data = {}

        symbol = data["symbol"]
        if symbol not in existing_data:
            existing_data[symbol] = data
        else:
            existing_data[symbol]["history"] = data["history"]
            existing_data[symbol]["info"] = data["info"]

        with open(filename, "w") as file:
            json.dump(existing_data, file, indent=4, cls=DateTimeEncoder)

    def download_stock_data_background(self):
        while True:
            self.is_downloading = True
            for symbol in self._all_stocks:
                self.update_historical_data(symbol)
                time.sleep(5)  # Add a small delay between each stock to avoid rate limiting
            self.is_downloading = False
            time.sleep(3600)  # Sleep for an hour before the next download cycle

    def analyze_portfolio(self):
        data = []
        for symbol, stock in self._portfolio.items():
            self.update_stock_data(symbol)
            current_value = stock.data.currentPrice * stock.quantity
            profit_loss = current_value - stock.investment
            profit_loss_percent = (profit_loss / stock.investment) * 100 if stock.investment != 0 else 0

            data.append({
                'Symbol': symbol,
                'Company Name': stock.company_name,
                'Current Price': stock.data.currentPrice,
                'Quantity': stock.quantity,
                'Current Value': current_value,
                'Investment': stock.investment,
                'Profit/Loss': profit_loss,
                'Profit/Loss %': profit_loss_percent,
                'Market Cap': stock.data.MarketCapIntraday,
                'Trend': stock.data.currentTrend,
                'Recommendation': stock.get_recommendation(),
                'Predictions': stock.predictions if stock.predictions else None,
                'Watchlist': False
            })

        for symbol, stock in self._watchlist.items():
            self.update_stock_data(symbol)
            data.append({
                'Symbol': symbol,
                'Company Name': stock.company_name,
                'Current Price': stock.data.currentPrice,
                'Initial Price': stock.data.currentPrice,  # Assuming initial price is current price when added to watchlist
                'Added Date': stock.watchlist_date,
                'Price Change %': 0,  # Calculate this if you have historical data
                'Market Cap': stock.data.MarketCapIntraday,
                'Trend': stock.data.currentTrend,
                'Recommendation': stock.get_recommendation(),
                'Predictions': stock.predictions if stock.predictions else None,
                'Watchlist': True
            })

        return pd.DataFrame(data)
    
    def display_portfolio_details(self):
        try:
            df = self.analyze_portfolio()
            print("\nPortfolio Analysis:")
            for _, row in df.iterrows():
                if not row.get('Watchlist', False):
                    print(f"\nAnalysis for {row.get('Symbol', 'N/A')} ({row.get('Company Name', 'N/A')}):")
                    print(f"Current Price: ${row.get('Current Price', 0):.2f}")
                    print(f"Market Cap: {row.get('Market Cap', 'N/A')}")
                    print(f"Current Trend: {row.get('Trend', 'N/A')}")
                    print(f"You own {row.get('Quantity', 0)} shares, valued at ${row.get('Current Value', 0):.2f}")
                    print(f"Profit/Loss: ${row.get('Profit/Loss', 0):.2f} ({row.get('Profit/Loss %', 0):.2f}%)")
                    print(f"Recommendation: {row.get('Recommendation', 'N/A')}")

                    predictions = row.get('Predictions')
                    if predictions is not None and len(predictions) > 0:
                        print("Predictions for the next 5 days:")
                        for i, pred in enumerate(predictions[:5], 1):
                            print(f"  Day {i}: ${pred:.2f}")
                    else:
                        print("Predictions not available")

            print("\nWatchlist Analysis:")
            for _, row in df.iterrows():
                if row.get('Watchlist', False):
                    print(f"\nAnalysis for {row.get('Symbol', 'N/A')} ({row.get('Company Name', 'N/A')}):")
                    print(f"Current Price: ${row.get('Current Price', 0):.2f}")

                    if pd.notna(row.get('Initial Price')):
                        print(f"Initial Price: ${row.get('Initial Price', 0):.2f}")
                        print(f"Price Change: {row.get('Price Change %', 0):.2f}%")
                    else:
                        print("Initial Price: Not available")
                        print("Price Change: Not available")

                    if pd.notna(row.get('Added Date')):
                        print(f"Added to Watchlist: {row['Added Date'].strftime('%Y-%m-%d')}")
                    else:
                        print("Added to Watchlist: Date not available")

                    print(f"Current Trend: {row.get('Trend', 'N/A')}")
                    print(f"Recommendation: {row.get('Recommendation', 'N/A')}")

                    predictions = row.get('Predictions')
                    if predictions is not None and len(predictions) > 0:
                        print("Predictions for the next 5 days:")
                        for i, pred in enumerate(predictions[:5], 1):
                            print(f"  Day {i}: ${pred:.2f}")
                    else:
                        print("Predictions not available")

            print("\nNote: Compare watchlist stocks' current prices and trends with your portfolio to identify potential buying opportunities.")
        except Exception as e:
            print(f"An error occurred while displaying portfolio details: {str(e)}")
            self.console.log(f"Error in display_portfolio_details: {str(e)}")
    def predict_investment(self, symbol: str, amount: float, duration: float):
        data = self.get_historical_data(symbol, period="10y")
        if data.empty:
            print(f"Unable to predict investment for {symbol} due to lack of historical data")
            return

        # Calculate daily returns
        data['Daily_Return'] = data['Close'].pct_change()

        # Calculate annualized return and volatility
        annual_return = data['Daily_Return'].mean() * 252
        annual_volatility = data['Daily_Return'].std() * np.sqrt(252)

        # Fetch current stock information
        stock_info = self.get_stock_info(symbol)
        current_price = self.get_live_data(symbol)

        if current_price is None:
            print(f"Unable to fetch current price for {symbol}. Using the latest available price from historical data.")
            current_price = data['Close'].iloc[-1]

        dividend_yield = stock_info.get('dividendYield', 0.0) if stock_info else 0.0

        # Calculate historical growth rate
        start_price = data['Close'].iloc[0]
        end_price = data['Close'].iloc[-1]
        total_years = len(data) / 252
        historical_growth_rate = (end_price / start_price) ** (1 / total_years) - 1

        # Define growth scenarios
        conservative_growth = max(0.0, historical_growth_rate * 0.5)
        moderate_growth = historical_growth_rate
        aggressive_growth = historical_growth_rate * 1.5

        # Monte Carlo simulation
        num_simulations = 10000
        simulation_results = []
        price_results = []

        initial_shares = amount / current_price
        simulation_days = int(duration * 252)  # Convert years to trading days

        for _ in range(num_simulations):
            portfolio_value = float(amount)
            stock_price = float(current_price)
            growth_scenario = np.random.choice([conservative_growth, moderate_growth, aggressive_growth])

            for _ in range(simulation_days):  # Daily simulation
                daily_return = np.random.normal(annual_return/252, annual_volatility/np.sqrt(252))
                stock_price *= (1 + daily_return)
                portfolio_value = initial_shares * stock_price

            # Apply growth scenario and dividend at the end of each year
            stock_price *= (1 + growth_scenario) ** duration
            portfolio_value = initial_shares * stock_price
            if dividend_yield > 0:
                portfolio_value *= (1 + dividend_yield) ** duration

            simulation_results.append(portfolio_value)
            price_results.append(stock_price)

        # Calculate statistics
        mean_result = float(np.mean(simulation_results))
        median_result = float(np.median(simulation_results))
        worst_case = float(np.percentile(simulation_results, 5))
        best_case = float(np.percentile(simulation_results, 95))

        mean_price = float(np.mean(price_results))
        median_price = float(np.median(price_results))
        worst_price = float(np.percentile(price_results, 5))
        best_price = float(np.percentile(price_results, 95))

        # Calculate CAGR (Compound Annual Growth Rate)
        cagr = (mean_result / amount) ** (1 / duration) - 1

        print(f"\nInvestment Prediction for {symbol}:")
        print(f"Investment Amount: ${amount:.2f}")
        print(f"Investment Duration: {duration:.1f} years")
        print(f"Current Stock Price: ${current_price:.2f}")
        print(f"Current Dividend Yield: {dividend_yield:.2%}")
        print(f"Historical Annual Return: {annual_return:.2%}")
        print(f"Historical Annual Volatility: {annual_volatility:.2%}")
        print(f"Historical Growth Rate: {historical_growth_rate:.2%}")
        print(f"\nGrowth Scenarios:")
        print(f"  Conservative: {conservative_growth:.2%}")
        print(f"  Moderate: {moderate_growth:.2%}")
        print(f"  Aggressive: {aggressive_growth:.2%}")
        print(f"\nSimulation Results:")
        print(f"Expected Portfolio Value (Mean): ${mean_result:.2f}")
        print(f"Median Portfolio Value: ${median_result:.2f}")
        print(f"Worst Case Portfolio Value (5th percentile): ${worst_case:.2f}")
        print(f"Best Case Portfolio Value (95th percentile): ${best_case:.2f}")
        print(f"\nPredicted Stock Price:")
        print(f"Expected Stock Price (Mean): ${mean_price:.2f}")
        print(f"Median Stock Price: ${median_price:.2f}")
        print(f"Worst Case Stock Price (5th percentile): ${worst_price:.2f}")
        print(f"Best Case Stock Price (95th percentile): ${best_price:.2f}")
        print(f"\nCompound Annual Growth Rate (CAGR): {cagr:.2%}")

        if dividend_yield == 0:
            print("\nNote: This stock does not currently pay dividends. All returns are based on price appreciation.")
        else:
            print(f"\nNote: This stock currently pays a dividend yield of {dividend_yield:.2%}.")
            print("The prediction assumes dividend reinvestment at the current yield rate.")

        print("\nThis prediction is based on historical data and simulated future scenarios.")
        print("It considers historical returns, volatility, growth rates, and current dividend yield (if applicable).")
        print("Actual results may vary significantly due to changes in company performance, market conditions, or economic factors.")
        print("Past performance does not guarantee future results.")
    
    
    def get_top_stocks(self, n=10, period="1mo"):
        try:
            print(f"\nGetting top {n} performing stocks over the last {period}...")
            print("\nThis may take a few moments depending on your internet speed.")
            # Get the list of S&P 500 stocks
            all_stocks = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
            symbols = all_stocks['Symbol'].tolist()
            print(f"Total number of stocks: {len(symbols)}")
            print("Fetching data for each stock...")
            print("This may take a few moments depending on your internet speed.")
            performance = []
            for symbol in symbols:
                try:
                    stock = yf.Ticker(symbol, session=self.session)
                    hist = stock.history(period=period)
                    if not hist.empty:
                        start_price = hist['Close'].iloc[0]
                        end_price = hist['Close'].iloc[-1]
                        percent_change = ((end_price - start_price) / start_price) * 100
                        performance.append((symbol, percent_change))
                        print(f"Fetched data for {symbol}: {percent_change:.2f}%")
                except Exception as e:
                    self.console.log(f"Error fetching data for {symbol}: {str(e)}")

            # Sort stocks by performance (descending order)
            print("\n Stocks sorted by performance:")
            top_performers = sorted(performance, key=lambda x: x[1], reverse=True)[:n]

            self.console.log(f"Top {n} performing stocks over the last {period}:")
            for symbol, change in top_performers:
                self.console.log(f"{symbol}: {change:.2f}%")

            return [stock[0] for stock in top_performers]
        except Exception as e:
            self.console.log(f"Error in get_top_stocks: {str(e)}")
            return []

    def save_data(self):
        data = {
            'portfolio': self._portfolio,
            'investments': self._investments,
            'predictions': {symbol: [
                {
                    'date': pred['date'].isoformat(),
                    'time': pred['time'],
                    'price': pred['price']
                } for pred in preds
            ] for symbol, preds in self._predictions.items()},
            'company_names': self._company_names,
            'trends': self._trends,
            'recommendations': self._recommendations,
            'notification_settings': self._notification_settings,
            'settings': self._settings,
            'smtp_settings': self._smtp_settings,
            'sms_settings': self._sms_settings,
            'mailjet_settings': self._mailjet_settings,
            'watchlist': self._watchlist,
            'model_parameters': self._model_parameters,
            'prediction_history': self._prediction_history,
            'last_alert_prices': self._last_alert_prices,
            'last_alert_times': {k: v.isoformat() for k, v in self._last_alert_times.items()},
            'max_console_messages': self.console.get_max_messages() , # Save the actual value
            'historical_data': self._historical_data,
            'historical_reports': self._historical_reports,
            'trends': self._trends 
        }

        if os.path.exists('portfolio_data.json'):
            backup_base = f'portfolio_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            counter = 0
            while True:
                backup_filename = f'{backup_base}_{counter}.json' if counter > 0 else f'{backup_base}.json'
                if not os.path.exists(backup_filename):
                    os.rename('portfolio_data.json', backup_filename)
                    self.console.log(f"Created backup: {backup_filename}")
                    break
                counter += 1

    # Save new data
        try:
            with open('portfolio_data.json', 'w') as f:
                json.dump(data, f, cls=DateTimeEncoder, indent=4)
            self.console.log("Data saved successfully.")
        except Exception as e:
            self.console.log(f"Error saving data: {str(e)}")
            if 'backup_filename' in locals():
                os.rename(backup_filename, 'portfolio_data.json')
                self.console.log("Restored from backup due to save error.")

        self.manage_backups()

    def load_from_specific_backup(self, backup_filename):
        if not os.path.exists(backup_filename):
            self.console.log(f"Backup file {backup_filename} not found.")
            return False

        try:
            with open(backup_filename, 'r') as f:
                data = json.load(f)
            
            self._portfolio = data.get('portfolio', {})
            self._investments = data.get('investments', {})
            self._predictions = data.get('predictions', {})
            self._company_names = data.get('company_names', {})
            self._trends = data.get('trends', {})
            self._recommendations = data.get('recommendations', {})
            self._watchlist = data.get('watchlist', {})
            self._model_parameters = data.get('model_parameters', {})
            self._prediction_history = data.get('prediction_history', {})
            
            # Convert watchlist dates back to datetime objects
            for symbol, watch_data in self._watchlist.items():
                if 'added_date' in watch_data:
                    watch_data['added_date'] = datetime.fromisoformat(watch_data['added_date'])

            self.console.log(f"Successfully loaded data from backup: {backup_filename}")
            self.save_data()  # Save the loaded data as current
            return True
        except Exception as e:
            self.console.log(f"Error loading from backup {backup_filename}: {str(e)}")
            return False

    def list_available_backups(self):
        backup_files = [f for f in os.listdir('.') if f.startswith('portfolio_data_backup_') and f.endswith('.json')]
        backup_files.sort(reverse=True)  # Sort in descending order (newest first)
        return backup_files

    def backup_menu(self):
        while True:
            clear_screen()
            print("\nBackup Management Menu:")
            print("1. List Available Backups")
            print("2. Load from Specific Backup")
            print("3. Revert Last Change")
            print("4. Return to Main Menu")

            choice = input("Enter your choice: ")

            if choice == '1':
                backups = self.list_available_backups()
                if backups:
                    print("\nAvailable Backups:")
                    for i, backup in enumerate(backups, 1):
                        print(f"{i}. {backup}")
                else:
                    print("No backups available.")
                input("\nPress Enter to continue...")
            elif choice == '2':
                backups = self.list_available_backups()
                if backups:
                    print("\nAvailable Backups:")
                    for i, backup in enumerate(backups, 1):
                        print(f"{i}. {backup}")
                    backup_choice = input("\nEnter the number of the backup to load (or 0 to cancel): ")
                    try:
                        backup_index = int(backup_choice) - 1
                        if 0 <= backup_index < len(backups):
                            if self.load_from_specific_backup(backups[backup_index]):
                                print("Backup loaded successfully.")
                            else:
                                print("Failed to load backup.")
                        elif backup_index == -1:
                            print("Operation cancelled.")
                        else:
                            print("Invalid backup number.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                else:
                    print("No backups available.")
                input("\nPress Enter to continue...")
            elif choice == '3':
                result = self.revert_last_change()
                print(result)
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please try again.")

    def load_data(self):
        try:
            if not os.path.exists('portfolio_data.json'):
                self.console.log("No saved data found. Starting with an empty portfolio.")
                return

            with open('portfolio_data.json', 'r') as f:
                data = json.load(f)
            max_messages = data.get('max_console_messages', 50)  # Default to 50 if not found
            print(f"Max messages: {max_messages}")
            self.console.set_max_messages(max_messages)            
            self._portfolio = data.get('portfolio', {})
            print('Portfolio Loaded')
            self._investments = data.get('investments', {})
            print('Investments Loaded')
            self._predictions = {
                symbol: [
                    {
                        'date': datetime.fromisoformat(pred['date']).date(),
                        'time': pred['time'],
                        'price': pred['price']
                    } for pred in preds
                ] for symbol, preds in data.get('predictions', {}).items()
            }            
            print('Predictions Loaded')
            self._company_names = data.get('company_names', {})
            print('Company Names Loaded')
            self._trends = data.get('trends', {})
            print('Trend Data Loaded')
            self._recommendations = data.get('recommendations', {})
            print('Recommendations Loaded')
            self._model_parameters = data.get('model_parameters', {})
            print('Model Parameters Loaded')
            self._prediction_history = data.get('prediction_history', {})
            print('Prediction History Loaded')
            self._historical_data = data.get('historical_data', {})
            print('Historical Data Loaded')
            self._historical_reports = data.get('historical_reports', {})
            print('Historical Reports Loaded')
            self._trends = data.get('trends', {
                'hourly': {},
                'daily': {},
                'weekly': {},
                'monthly': {},
                'yearly': {},
                'overall': {}
            })
            self._notification_settings = data.get('notification_settings', {
                'email': '',
                'phone': '',
                'daily_update': False,
                'real_time_alerts': False
            })
            print('Notification Settings Loaded')
            self._settings = data.get('settings', {
                'smtp_configured': False,
                'twilio_configured': False
            })
            self._smtp_settings = data.get('smtp_settings', {
                'sender_email': '',
                'sender_password': '',
                'smtp_server': '',
                'smtp_port': 587
            })
            print('SMTP Settings Loaded')
            self._sms_settings = data.get('sms_settings', {
                'phone_number': '',
                'carrier': ''
            })
            print('SMS Settings Loaded')
            self._mailjet_settings = data.get('mailjet_settings', {
                'api_key': '',
                'api_secret': '',
                'sender_email': '',
                'sender_name': 'Stock Analyzer'
            })
            print('Mailjet Settings Loaded')

            # Handle watchlist and datetime conversion
            self._watchlist = {}
            print('Watchlist Loaded')
            self.update_watchlist_company_names()
            print('Watchlist Company Names Updated')
            for symbol, watch_data in data.get('watchlist', {}).items():
                if 'added_date' in watch_data:
                    try:
                        watch_data['added_date'] = datetime.fromisoformat(watch_data['added_date'])
                    except ValueError:
                        watch_data['added_date'] = datetime.now()
                self._watchlist[symbol] = watch_data
            self._last_alert_prices = data.get('last_alert_prices', {})
            self._last_alert_times = {k: datetime.fromisoformat(v) for k, v in data.get('last_alert_times', {}).items()}
            for symbol in list(self._portfolio.keys()) + list(self._watchlist.keys()):
                self.update_historical_data(symbol)
                self.calculate_trends(symbol)
            for symbol in self._historical_data:
                for entry in self._historical_data[symbol]:
                    entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
            self.save_data()  # Save the updated trend data
            self.console.log("Data loaded and trends calculated.")
            self.console.log("All Data loaded from JSON successfully.")
            for symbol, predictions in self._predictions.items():
                for pred in predictions:
                    pred['date'] = datetime.fromisoformat(pred['date']).date()

            print('Predictions Loaded')
        except json.JSONDecodeError as e:
            self.console.log(f"Error decoding JSON: {str(e)}")
            self.console.log("Attempting to load from backup...")
            self._load_from_backup()
        except Exception as e:
            self.console.log(f"An error occurred while loading data: {str(e)}")
            self.console.log("Attempting to load from backup...")
            self._load_from_backup()


    def get_latest_prediction(self, symbol):
        predictions = self._predictions.get(symbol, [])
        if predictions:
            return max(predictions, key=lambda x: x['date'])
        return None

    def get_prediction_for_date(self, symbol, date, time='market_close'):
        predictions = self._predictions.get(symbol, [])
        for pred in predictions:
            if pred['date'] == date and pred['time'] == time:
                return pred
        return None
    def _load_from_backup(self):
        backup_files = [f for f in os.listdir('.') if f.startswith('portfolio_data_backup_') and f.endswith('.json')]
        if not backup_files:
            self.console.log("No backup files found. Starting with empty data.")
            self._initialize_empty_data()
            return

        latest_backup = max(backup_files)
        try:
            with open(latest_backup, 'r') as f:
                data = json.load(f)
            self._portfolio = data.get('portfolio', {})
            # ... (load other attributes similarly)
            self.console.log(f"Loaded data from backup: {latest_backup}")
        except Exception as e:
            self.console.log(f"Error loading from backup: {str(e)}")
            self._initialize_empty_data()


    def generate_verification_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def configure_mailjet(self):
        print("\nConfigure Mailjet Settings:")
        api_key = input("Enter Mailjet API Key: ")
        api_secret = input("Enter Mailjet API Secret: ")

        # Verify API credentials
        test_client = Client(api_key=api_key, api_secret=api_secret)
        try:
            response = test_client.sender.get()
            if response.status_code == 200:
                print("API credentials verified successfully.")
            else:
                print(f"Failed to verify API credentials. Status code: {response.status_code}")
                print("Please check your API Key and Secret and try again.")
                return
        except Exception as e:
            print(f"An error occurred while verifying API credentials: {str(e)}")
            print("Please check your API Key and Secret and try again.")
            return

        self._mailjet_settings['api_key'] = api_key
        self._mailjet_settings['api_secret'] = api_secret

        self._mailjet_settings['sender_email'] = input("Enter sender email address: ")
        self._mailjet_settings['sender_name'] = input("Enter sender name (default: Stock Analyzer): ") or "Stock Analyzer"

        self._settings['mailjet_configured'] = True
        self.save_data()
        print("Mailjet settings configured successfully.")

        verify_now = input("Would you like to send a test email to verify your configuration? (y/n): ").lower() == 'y'
        if verify_now:
            self.send_test_email()

    def update_historical_data(self, symbol):
        current_price = self.get_live_data(symbol)
        if current_price != 0:
            current_time = datetime.now(self.time_zone)
            if symbol not in self._historical_data:
                self._historical_data[symbol] = []
            self._historical_data[symbol].append((current_time, current_price))
            self._historical_data[symbol] = self._historical_data[symbol][-1000:]  # Keep last 1000 data points
            self.calculate_trends(symbol)
            self.save_data()  # Save after updating historical data and trends
            self.console.log(f"Updated historical data for {symbol}")
        else:
            self.console.log(f"Failed to update historical data for {symbol} due to data fetch failure.")

    def update_stock_data(self, stock_or_symbol):
        stock = self._ensure_stock_object(stock_or_symbol)
        self.update_historical_data(stock)
        self.predict_stock(stock)


    def calculate_trends(self, symbol):
        if symbol not in self._historical_data or len(self._historical_data[symbol]) < 2:
            return  

        data = self._historical_data[symbol]
        current_time, current_price = data[-1]

        # Ensure all time entries are datetime objects
        data = [(datetime.fromisoformat(t) if isinstance(t, str) else t, p) for t, p in data]

        # Calculate trends for different time periods
        self._trends['hourly'][symbol] = self._calculate_trend_for_period(data, timedelta(hours=1))
        self._trends['daily'][symbol] = self._calculate_trend_for_period(data, timedelta(days=1))
        self._trends['weekly'][symbol] = self._calculate_trend_for_period(data, timedelta(weeks=1))
        self._trends['monthly'][symbol] = self._calculate_trend_for_period(data, timedelta(days=30))
        self._trends['yearly'][symbol] = self._calculate_trend_for_period(data, timedelta(days=365))
        self._trends['overall'][symbol] = self._calculate_trend_for_period(data, None)  # None for overall trend


    def _calculate_trend_for_period(self, data, period):
        current_time, current_price = data[-1]
        if period:
            start_time = current_time - period
            start_data = [d for d in data if d[0] > start_time]
        else:
            start_data = data

        if start_data:
            start_price = start_data[0][1]
            return self.calculate_trend(start_price, current_price)
        return "Neutral"  # Default if no data available for the period
    def calculate_trend(self, start_price, end_price):
        change = ((end_price - start_price) / start_price) * 100
        if change > 10:
            return "Strong Up"
        elif change > 2:
            return "Up"
        elif change < -10:
            return "Strong Down"
        elif change < -2:
            return "Down"
        else:
            return "Neutral"

    def send_email_verification(self, email):
        code = self.generate_verification_code()
        subject = "Verify Your Email for Stock Analyzer"
        body = f"Your verification code is: {code}"
        if self.send_email(email, subject, body):
            return code
        return None

    def send_sms_verification(self, phone):
        code = self.generate_verification_code()
        message = f"Your Stock Analyzer verification code is: {code}"
        if self.send_sms(phone, message):
            return code
        return None


    def send_email(self, to_email, subject, body):
        if not self._settings.get('mailjet_configured'):
            self.console.log("Mailjet is not configured. Please configure Mailjet settings first.")
            return False

        self.console.log(f"Initializing Mailjet client with API Key: {self._mailjet_settings['api_key'][:5]}...")
        mailjet = Client(auth=(self._mailjet_settings['api_key'], self._mailjet_settings['api_secret']), version='v3.1')

        data = {
            'Messages': [
                {
                    "From": {
                        "Email": self._mailjet_settings['sender_email'],
                        "Name": self._mailjet_settings['sender_name']
                    },
                    "To": [
                        {
                            "Email": to_email
                        }
                    ],
                    "Subject": subject,
                    "TextPart": body
                }
            ]
        }

        self.console.log("Attempting to send email...")
        try:
            result = mailjet.send.create(data=data)
            self.console.log(f"API Response Status Code: {result.status_code}")
            self.console.log(f"API Response Content: {result.json()}")

            if result.status_code == 200:
                self.console.log("Email/SMS sent successfully")
                return True
            else:
                self.console.log(f"Failed to send email/SMS. Status code: {result.status_code}")
                self.console.log(f"Error details: {json.dumps(result.json(), indent=2)}")
                return False
        except Exception as e:
            self.console.log(f"An error occurred while sending email/SMS: {str(e)}")
            return False

    def send_test_email(self):
        if not self._settings.get('mailjet_configured'):
            self.console.log("Mailjet is not configured. Please configure Mailjet settings first.")
            return

        to_email = input("Enter the email address to send a test email to: ")
        subject = "Test Email from Stock Analyzer via Mailjet"
        body = f"This is a test email sent at {time.ctime()} using Mailjet. If you receive this, your email configuration is working."

        self.console.log("Sending test email...")
        if self.send_email(to_email, subject, body):
            self.console.log("Test email sent successfully.")
            self.console.log("Please check your inbox (and spam folder) for the test email.")
        else:
            self.console.log("Failed to send test email.")

    def send_test_sms(self):
        if not self._settings.get('mailjet_configured'):
            self.console.log("Mailjet is not configured. Please configure Mailjet settings first.")
            return

        to_phone = input("Enter the phone number to send a test SMS to (without country code, e.g., 123456789): ")
        message = f"This is a test SMS from Stock Analyzer sent at {time.ctime()} via Mailjet."

        self.console.log("Sending test SMS...")
        if self.send_sms(to_phone, message):
            self.console.log("Test SMS sent successfully.")
            self.console.log("Please check your phone for the test SMS.")
        else:
            self.console.log("Failed to send test SMS.")
    def update_smtp_settings(self):
        print("\nUpdating SMTP Settings:")

        self._smtp_settings['smtp_server'] = input("Enter SMTP server address (e.g., smtp.hostinger.com): ").strip()

        while True:
            try:
                smtp_port = int(input("Enter SMTP port (465 for SSL/TLS, 587 for STARTTLS): "))
                if smtp_port in [465, 587]:
                    self._smtp_settings['smtp_port'] = smtp_port
                    break
                else:
                    print("Please enter either 465 or 587.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        self._smtp_settings['sender_email'] = input("Enter your email address: ").strip()
        self._smtp_settings['sender_password'] = input("Enter your email password: ")

        self._settings['smtp_configured'] = all(self._smtp_settings.values())
        self.save_data()
        print("SMTP settings updated. Testing connection...")

        if self.test_smtp_connection():
            print("SMTP connection test passed successfully.")
        else:
            print("SMTP connection test failed. Please check your settings and try again.")
            print("You can run the test again from the settings menu.")
        
    def test_smtp_connection(self):
        if not self._settings['smtp_configured']:
            self.console.log("SMTP settings are not configured. Please configure them first.")
            return False

        smtp_server = self._smtp_settings['smtp_server']
        smtp_port = self._smtp_settings['smtp_port']
        sender_email = self._smtp_settings['sender_email']
        password = self._smtp_settings['sender_password']

        self.console.log(f"Testing SMTP connection to {smtp_server}:{smtp_port}")
        self.console.log(f"Using email: {sender_email}")

        try:
            if smtp_port == 465:
                self.console.log("Using SSL connection")
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=30) as server:
                    self.console.log("SSL connection established. Attempting login...")
                    server.login(sender_email, password)
                    self.console.log("Login successful")
            else:
                self.console.log("Using STARTTLS connection")
                with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                    self.console.log("Connection established. Starting TLS...")
                    server.starttls()
                    self.console.log("TLS started. Attempting login...")
                    server.login(sender_email, password)
                    self.console.log("Login successful")

            self.console.log("SMTP connection test passed successfully.")
            return True

        except socket.timeout:
            self.console.log(f"Connection timed out after 30 seconds. Check if {smtp_server}:{smtp_port} is correct and accessible.")
        except smtplib.SMTPAuthenticationError:
            self.console.log("Authentication failed. Please check your email and password.")
        except ssl.SSLError as e:
            self.console.log(f"SSL error occurred: {str(e)}. Check if the port supports SSL.")
        except smtplib.SMTPException as e:
            self.console.log(f"SMTP error occurred: {str(e)}")
        except Exception as e:
            self.console.log(f"An unexpected error occurred: {str(e)}")

        self.console.log("SMTP connection test failed.")
        return False

    def send_sms(self, to_phone, message):
        if not self._settings.get('mailjet_configured'):
            self.console.log("Mailjet is not configured. Please configure Mailjet settings first.")
            return False

        if not self._sms_settings.get('carrier'):
            self.console.log("SMS carrier is not set. Please configure SMS settings first.")
            return False

        carrier = self._sms_settings['carrier']
        if carrier not in self._sms_gateways:
            self.console.log(f"Unknown carrier: {carrier}. SMS gateway not available.")
            return False

        sms_gateway = self._sms_gateways[carrier]
        to_email = f"{to_phone}{sms_gateway}"

        self.console.log(f"Sending SMS via email to {to_email}")
        return self.send_email(to_email, "Stock Alert", message)


    def check_for_drastic_changes(self):
        try:
            for stock in self._all_stocks.values():
                current_price = stock.data.currentPrice
                predictions = stock.predictions

                if predictions:
                    predicted_price = predictions[0]  # Use the first prediction

                    if self.should_send_alert(stock.symbol, current_price, predicted_price):
                        price_difference = abs((current_price - predicted_price) / predicted_price) * 100

                        message = f"Alert: Significant change predicted for {stock.symbol}\n"
                        message += f"Current Price: ${current_price:.2f}\n"
                        message += f"Predicted Price: ${predicted_price:.2f}\n"
                        message += f"Difference: {price_difference:.2f}%\n"
                        message += "Trends:\n"
                        
                        for trend_type in ['Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly', 'Lifetime']:
                            trend_value = stock.data.Trends.get(trend_type, 'N/A')
                            message += f"  {trend_type}: {trend_value}\n"

                        self.send_notification(f"Stock Alert - {stock.symbol}", message)
                        self.update_last_alert(stock.symbol, current_price)
                else:
                    self.console.log(f"No predictions available for {stock.symbol}")
        except Exception as e:
            self.console.log(f"Error in check_for_drastic_changes: {str(e)}")
    def verify_contact_info(self, email, phone):
        email_verified = False
        phone_verified = False

        if email:
            email_code = self.send_email_verification(email)
            if email_code:
                user_email_code = input("Enter the email verification code: ")
                email_verified = (user_email_code == email_code)
            else:
                self.console.log("Failed to send email verification code.")

        if phone:
            phone_code = self.send_sms_verification(phone)
            if phone_code:
                user_phone_code = input("Enter the SMS verification code: ")
                phone_verified = (user_phone_code == phone_code)
            else:
                self.console.log("Failed to send SMS verification code.")

        return email_verified, phone_verified

    def set_notification_settings(self):
        print("\nSetting up Notification Preferences:")

        if self._settings['smtp_configured']:
            use_existing_email = input("Existing email settings found. Use these? (y/n): ").lower() == 'y'
            if use_existing_email:
                email = self._notification_settings['email']
            else:
                email = input("Enter your email address to receive notifications: ")

            if email:
                email_verified, _ = self.verify_contact_info(email, None)
                if not email_verified:
                    print("Email verification failed. Email notifications will not be enabled.")
                    email = ''
        else:
            print("SMTP not configured. Email notifications will not be available.")
            print("You can configure SMTP settings in the Settings menu.")
            email = ''

        if self._settings['sms_configured']:
            use_existing_sms = input("Existing SMS settings found. Use these? (y/n): ").lower() == 'y'
            if use_existing_sms:
                phone = self._sms_settings['phone_number']
            else:
                phone = input("Enter your phone number for SMS notifications: ")

            if phone:
                _, phone_verified = self.verify_contact_info(None, phone)
                if not phone_verified:
                    print("Phone verification failed. SMS notifications will not be enabled.")
                    phone = ''
        else:
            print("SMS settings not configured. SMS notifications will not be available.")
            print("You can configure SMS settings in the Settings menu.")
            phone = ''

        daily_update = input("Enable daily updates? (y/n): ").lower() == 'y'
        real_time_alerts = input("Enable real-time alerts? (y/n): ").lower() == 'y'

        self._notification_settings['email'] = email
        self._notification_settings['phone'] = phone
        self._notification_settings['daily_update'] = daily_update
        self._notification_settings['real_time_alerts'] = real_time_alerts

        self.save_data()

        print("\nNotification settings updated:")
        print(f"Email notifications: {'Enabled (' + email + ')' if email else 'Disabled'}")
        print(f"SMS notifications: {'Enabled (' + phone + ')' if phone else 'Disabled'}")
        print(f"Daily updates: {'Enabled' if daily_update else 'Disabled'}")
        print(f"Real-time alerts: {'Enabled' if real_time_alerts else 'Disabled'}")

        if (email or phone) and (daily_update or real_time_alerts):
            self.start_background_checks()
        else:
            print("No notifications enabled. Background checks will not be started.")
    
    def send_notification(self, subject: str, message: str, symbol: str = ""):
        email_notifications = self._notification_settings.get('email_notifications', True)
        sms_notifications = self._notification_settings.get('sms_notifications', True)

        if email_notifications:
            email = self._notification_settings.get('email')
            if email:
                self.send_email(email, subject, message)
            else:
                self.console.log("Email notification skipped: No email address configured.")

        if sms_notifications:
            phone = self._notification_settings.get('phone')
            if phone:
                if symbol:
                    sms_message = self.generate_report("update", for_sms=True, symbol=symbol)
                else:
                    sms_message = message[:160]  # Truncate message to 160 characters for SMS
                self.send_sms(phone, f"{subject}\n\n{sms_message}")
            else:
                self.console.log("SMS notification skipped: No phone number configured.")
        self.console.log(f"Notification: {subject}\n{message}")   
    
    def daily_update(self):
        df = self.analyze_portfolio()
        update = "Daily Portfolio Update:\n\n"
        for _, row in df.iterrows():
            update += f"{row['Symbol']} ({row['Company Name']}):\n"
            update += f"  Current Price: ${row['Current Price']:.2f}\n"
            update += f"  Profit/Loss: ${row['Profit/Loss']:.2f} ({row['Profit/Loss %']:.2f}%)\n"
            update += f"  Recommendation: {row['Recommendation']}\n\n"
        self.send_notification("Daily Stock Update", update)

    def check_recommendation_changes(self):
        changes = []
        for symbol in self._portfolio:
            current_price = self.get_live_data(symbol)
            new_recommendation = self.get_recommendation(current_price, self._predictions.get(symbol, []))
            if new_recommendation != self._recommendations.get(symbol):
                changes.append((symbol, self._recommendations.get(symbol), new_recommendation))
                self._recommendations[symbol] = new_recommendation

        if changes and self._notification_settings['real_time_alerts']:
            alert = "Recommendation Changes:\n\n"
            for symbol, old_rec, new_rec in changes:
                alert += f"{symbol} ({self._company_names.get(symbol, 'N/A')}):\n"
                alert += f"  Old Recommendation: {old_rec}\n"
                alert += f"  New Recommendation: {new_rec}\n\n"
            self.send_notification("Stock Recommendation Alert", alert)

        self.save_data()

    
    def compare_predictions(self):
        current_predictions = {}
        for symbol in self._portfolio:
            current_predictions[symbol] = self.predict_stock(symbol)

        print("\nPrediction Comparison:")
        for symbol, current_pred in current_predictions.items():
            old_pred = self._predictions.get(symbol)
            if old_pred:
                print(f"\n{symbol} ({self._company_names.get(symbol, 'N/A')}):")
                print("Old Predictions:")
                for i, pred in enumerate(old_pred, 1):
                    print(f"  Day {i}: ${pred:.2f}")
                print("Current Predictions:")
                for i, pred in enumerate(current_pred, 1):
                    print(f"  Day {i}: ${pred:.2f}")
                
                # Calculate average difference
                avg_diff = np.mean([current - old for current, old in zip(current_pred, old_pred)])
                print(f"Average difference: ${avg_diff:.2f}")
            else:
                print(f"\n{symbol} ({self._company_names.get(symbol, 'N/A')}): No previous predictions available.")

    def show_top_performers(self):
        df = self.analyze_portfolio()
        if df.empty:
            print("No stocks in portfolio.")
            return
        
        df_sorted = df.sort_values('Profit/Loss %', ascending=False)
        top_n = min(10, len(df))
        print(f"\nTop {top_n} Performing Stocks in Your Portfolio:")
        for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
            if i > top_n:
                break
            print(f"{i}. {row['Symbol']} ({row['Company Name']}):")
            print(f"   Profit/Loss: ${row['Profit/Loss']:.2f} ({row['Profit/Loss %']:.2f}%)")
            print(f"   Current Trend: {row['Trend']}")
            print(f"   Recommendation: {row['Recommendation']}")

    def configure_smtp(self):
        print("\nConfigure SMTP Settings:")
        self._smtp_settings['sender_email'] = input("Enter the email address to send notifications from: ")
        self._smtp_settings['sender_password'] = input("Enter the password for the sender email: ")
        self._smtp_settings['smtp_server'] = input("Enter the SMTP server (e.g., smtp.gmail.com for Gmail): ")
        self._smtp_settings['smtp_port'] = int(input("Enter the SMTP port (usually 587 for TLS): "))

        self._settings['smtp_configured'] = all(self._smtp_settings.values())
        self.save_data()
        print("SMTP settings configured successfully.")

    def configure_sms(self):
        print("\nConfigure SMS Settings:")
        print("Available carriers:")
        for i, carrier in enumerate(self._sms_gateways.keys(), 1):
            print(f"{i}. {carrier}")

        try:
            carrier_choice = int(input("Enter the number of your carrier: "))
            if carrier_choice < 1 or carrier_choice > len(self._sms_gateways):
                raise ValueError("Invalid carrier choice")
            carrier = list(self._sms_gateways.keys())[carrier_choice - 1]
        except ValueError as e:
            print(f"Error: {e}. Using default carrier (AT&T).")
            carrier = "AT&T"

        phone_number = input("Enter your phone number (numbers only, no spaces or dashes): ")

        if not phone_number.isdigit():
            print("Error: Phone number should only contain digits. SMS configuration failed.")
            return

        self._sms_settings['phone_number'] = phone_number
        self._sms_settings['carrier'] = carrier

        self._settings['sms_configured'] = bool(self._sms_settings['phone_number'] and self._sms_settings['carrier'])
        self.save_data()

        if self._settings['sms_configured']:
            print("SMS settings configured successfully.")
        else:
            print("SMS settings were not fully configured. Please try again.")

        print(f"Current SMS settings:")
        print(f"Phone number: {self._sms_settings['phone_number']}")
        print(f"Carrier: {self._sms_settings['carrier']}")
    
    def settings_menu(self):
        clear_screen()
        while True:
            print("\nSettings Menu:")
            print("1. Configure Mailjet Settings")
            print("2. Send Test Email")
            print("3. Send Test SMS")
            print("4. View Recent Console Messages")
            print("5. Clear Console Messages")
            print("6. Set Maximum Console Messages")
            print("7. Back Up Manager")
            print("8. Revert Last Change")
            print("9. Set Notification Preferences")
            print("10. Return to Main Menu")

            choice = input("Enter your choice: ")
            clear_screen()
            if choice == '1':
                self.configure_mailjet()
            elif choice == '2':
                self.send_test_email()
            elif choice == '3':
                self.send_test_sms()
            elif choice == '4':
                print(f"\nRecent Console Messages (Max: {self.console.messages.maxlen}):")
                self.display_console_messages()
                input("Press Enter to continue...")
            elif choice == '5':
                self.clear_console_messages()
                print("Console messages cleared.")
            elif choice == '6':
                max_messages = input("Enter the maximum number of console messages to display: ")
                self.set_max_console_messages(max_messages)
            elif choice == '7':
                self.backup_menu()
            elif choice == '8':
                result = self.revert_last_change()
                print(result)
            elif choice == '9':
                self.set_notification_settings()
            elif choice == '10':
                break
            else:
                print("Invalid choice. Please try again.")

    def verify_email(self):
        if not self._settings['smtp_configured']:
            self.console.log("SMTP not configured. Please configure SMTP settings first.")
            return False

        email = self._notification_settings['email']
        if not email:
            email = input("Enter your email address to verify: ")

        code = self.generate_verification_code()
        subject = "Verify Your Email for Stock Analyzer"
        body = f"Your verification code is: {code}"

        if self.send_email(email, subject, body):  # Increased timeout for verification emails
            user_code = input("Enter the verification code sent to your email: ")
            if user_code == code:
                self._notification_settings['email'] = email
                self._notification_settings['email_verified'] = True
                self.save_data()
                self.console.log("Email verified successfully.")
                return True
            else:
                self.console.log("Verification failed. Incorrect code.")
                return False
        else:
            self.console.log("Failed to send verification email.")
            return False

    def verify_phone(self):
        if not self._settings['sms_configured']:
            self.console.log("SMS not configured. Please configure SMS settings first.")
            return False
        
        phone = self._sms_settings['phone_number']
        if not phone:
            phone = input("Enter your phone number to verify: ")
        
        code = self.generate_verification_code()
        message = f"Your Stock Analyzer verification code is: {code}"
        
        if self.send_sms(phone, message):
            user_code = input("Enter the verification code sent to your phone: ")
            if user_code == code:
                self._sms_settings['phone_number'] = phone
                self._notification_settings['phone_verified'] = True
                self.save_data()
                self.console.log("Phone number verified successfully.")
                return True
            else:
                self.console.log("Verification failed. Incorrect code.")
                return False
        else:
            self.console.log("Failed to send verification SMS.")
            return False

    def watchlist_menu(self):
        clear_screen()
        while True:
            print("\nWatchlist Menu:")
            print("1. Add Stock to Watchlist")
            print("2. Remove Stock from Watchlist")
            print("3. View Watchlist")
            print("4. Return to Main Menu")
            self.display_console_messages()
            choice = input("Enter your choice: ")
            clear_screen()
            if choice == '1':
                symbol = input("Enter stock symbol to add to watchlist: ")
                self.add_to_watchlist(symbol)
            elif choice == '2':
                symbol = input("Enter stock symbol to remove from watchlist: ")
                self.remove_from_watchlist(symbol)
            elif choice == '3':
                print("\nCurrent Watchlist:")
                for symbol, data in self._watchlist.items():
                    print(f"{symbol} ({data['company_name']}): Added on {data['added_date']}, Initial Price: ${data['initial_price']:.2f}")
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please try again.")
    
    def startup_notification(self):
        report = self.generate_report("startup")
        self.send_notification("Stock Analyzer Startup Report", report)

    def generate_market_report(self, report_type):
        report = self.generate_report(report_type)
        self.send_notification(f"Daily Market {report_type.capitalize()} Report", report)
    def main(self):
        while True:
            try:
                clear_screen()
                print("\nStock Analyzer Menu:")
                print("1. Add Stock")
                print("2. Remove Stock")
                print("3. Add Shares")
                print("4. Remove Shares")
                print("5. Override Shares")
                print("6. Analyze Portfolio")
                print("7. Predict Investment")
                print("8. Show Top Stocks")
                print("9. Show Current Portfolio")
                print("10. Display Detailed Portfolio Analysis")
                print("11. Compare Predictions")
                print("12. Show Top Performers")
                print("13. Historical Data and Trends")
                print("14. Settings")
                print("15. Watchlist Menu")
                print("16. Set Time Zone")
                print("17. Graph Menu")
                print("18. Exit")        
                if self.is_training or self.is_downloading:
                    print("Warning: Model is currently training or downloading data. Some operations may be slower or use outdated information.")

                choice = input("Enter your choice: ")

                clear_screen()

                if choice == '1':
                    symbol = input("Enter stock symbol: ")
                    quantity = float(input("Enter quantity: "))
                    investment = input("Enter investment amount (leave blank to use current stock price): ")
                    investment = float(investment) if investment else 0
                    result = self.add_stock(symbol, quantity, investment)
                    print(result)
                elif choice == '2':
                    symbol = input("Enter stock symbol to remove: ")
                    self.remove_stock(symbol)
                elif choice == '3':
                    symbol = input("Enter stock symbol: ")
                    quantity = float(input("Enter number of shares to add: "))
                    investment = float(input("Enter additional investment amount: "))
                    result = self.add_shares(symbol, quantity, investment)
                    print(result)
                elif choice == '4':
                    symbol = input("Enter stock symbol: ")
                    quantity = float(input("Enter number of shares to remove: "))
                    result = self.remove_shares(symbol, quantity)
                    print(result)
                elif choice == '5':
                    symbol = input("Enter stock symbol: ")
                    quantity = float(input("Enter new total number of shares: "))
                    result = self.override_shares(symbol, quantity)
                    print(result)
                elif choice == '6':
                    if self.is_training or self.is_downloading:
                        print("Warning: Predictions may not be up to date as the model is currently training or downloading data.")
                        continue
                    df = self.analyze_portfolio()
                    print(df.to_string())
                elif choice == '7':
                    if self.is_training or self.is_downloading:
                        print("Warning: Predictions may not be up to date as the model is currently training or downloading data.")
                        continue
                    symbol = input("Enter stock symbol: ")
                    amount = float(input("Enter investment amount: "))
                    duration = float(input("Enter investment duration (years): "))
                    self.predict_investment(symbol, amount, duration)
                elif choice == '8':
                    top_stocks = self.get_top_stocks()
                    print("\nTop 10 Stocks (randomly selected for demonstration):")
                    for stock in top_stocks:
                        print(stock)
                elif choice == '9':
                    print("\nCurrent Portfolio:")
                    for symbol, quantity in self.portfolio.items():
                        print(f"{symbol}: {quantity} shares, Investment: ${self.investments[symbol]:.2f}")
                elif choice == '10':
                    if self.is_training or self.is_downloading:
                        print("Warning: Predictions may not be up to date as the model is currently training or downloading data.")
                        continue
                    self.display_portfolio_details()
                elif choice == '11':
                    if self.is_training or self.is_downloading:
                        print("Warning: Predictions may not be up to date as the model is currently training or downloading data.")
                        continue
                    self.compare_predictions()
                elif choice == '12':
                    self.show_top_performers()
                elif choice == '13':
                    print("\nHistorical Data and Trends:")
                    print("\nThis feature is not yet implemented")
                elif choice == '14':
                    self.settings_menu()
                elif choice == '15':
                    self.watchlist_menu()
                elif choice == '16':
                    new_tz = input("Enter time zone (e.g., US/Mountain, US/Eastern, US/Pacific): ")
                    self.set_time_zone(new_tz)
                elif choice == '17':
                    print("Implementation not available.")
                elif choice == '18':
                    print("Exiting...")
                    root.destroy()
                    break
                else:
                    print("Invalid choice. Please try again.")

                input("\nPress Enter to continue...")
            except KeyboardInterrupt:
                print("\nProgram interrupted. Exiting gracefully...")
                self.save_data()  # Save data before exiting
                break
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                print("The program will continue running. Press Enter to return to the main menu.")
                input()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalyzer(root)
    root.mainloop()
