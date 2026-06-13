# 🌦️ Singapore Weather Telegram Bot

A Telegram bot that provides **real-time rainfall, temperature, and 2-hour weather forecasts in Singapore** using the official Data.gov.sg APIs.

Users can select locations via inline buttons to view localized weather conditions.

---

## ✨ Features

- 📍 Location-based weather selection (e.g., Ang Mo Kio, Bishan, Changi)
- 🌧️ Real-time rainfall readings (station-based)
- 🌡️ Temperature data from nearby stations
- 🌦️ 2-hour weather forecast per region
- 📊 “Show All Rainfall” overview mode
- 🧭 Interactive inline keyboard UI (Telegram buttons)
- 🔄 Auto-refresh on each `/start`
- ✅ PythonAnywhere Ready: Structured to be easily deployed on cloud hosting services.

---

## 🗺️ Data Sources

This bot uses official Singapore government APIs:

- Rainfall API  
  https://api-open.data.gov.sg/v2/real-time/api/rainfall

- Air Temperature API  
  https://api-open.data.gov.sg/v2/real-time/api/air-temperature

- 2-hour Forecast API  
  https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast

---

## 🚀 Setup Instructions

### 📋 Prerequisites
Before you begin, ensure you have the following:

Python 3.10+ installed on your system.
A Telegram Bot Token (Create one via @BotFather on Telegram).
pip for installing dependencies.

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/singapore-weather-bot.git
cd singapore-weather-bot
```

### 2. Create virtual environment (recommended)
```
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```
pip install python-telegram-bot requests python-dotenv
```


### 3. Create .env file
```
TELEGRAM_TOKEN=your_telegram_bot_token_here
```
Get your token from: https://t.me/BotFather

### 5. Run the bot
If you are running the bot locally, run this
```
python main.py
```
Otherwise, you can deploy it on pythonanywhere.

## 🧠 How It Works
### Flow:
1. User sends /start
2. Bot fetches latest:
- rainfall data
- temperature data
3. Bot builds station mapping
4. User selects a location
5. Bot:
- maps location → weather stations
- extracts rainfall + temperature
- fetches 2-hour forecast
6. Bot responds with formatted summary

### 📍 Location Mapping
Each button maps to:
```
"Location Name": {
    "forecast_area": "Data.gov.sg area name",
    "stations": ["Station IDs"]
}
```
Example:
- Bishan → S217, S08
- Changi → S208, S224, S24
- Clementi → S50, S230

### 📊 Example Output
```
📍 Bishan
⏰ 14 Jun 2026, 3:10PM SGT
🌦️ Forecast: Partly Cloudy
🌧️ Rainfall:
Bishan (S217): 0.2 mm
🌡️ Temperature:
Bishan (S217): 29.4°C
```
