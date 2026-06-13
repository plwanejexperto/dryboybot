import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
	ApplicationBuilder, CommandHandler, CallbackQueryHandler,
	ContextTypes, ConversationHandler
)

logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSING_STATION = 1

latest_rainfall_data = None
latest_temperature_data = None
latest_station_map = {}

LOCATION_MAP = {
	"Ang Mo Kio": {
		"forecast_area": "Ang Mo Kio",
		"stations": ["S126", "S109", "S219"]
	},
	"Marine Parade": {
		"forecast_area": "Marine Parade",
		"stations": ["S214", "S107", "S113"]
	},
	"Sembawang": {
		"forecast_area": "Sembawang",
		"stations": ["S227", "S104"]
	},
	"Sentosa": {
		"forecast_area": "Sentosa",
		"stations": ["S60"]
	},
	"Clementi": {
		"forecast_area": "Clementi",
		"stations": ["S50", "S230"]
	},
	"NTU": {  # Button name for Jalan Bahar area
		"forecast_area": "Jalan Bahar",
		"stations": ["S44"]
	},
	"Paya Lebar": {
		"forecast_area": "Paya Lebar",
		"stations": ["S43"]
	},
	"Changi": {
		"forecast_area": "Changi",
		"stations": ["S208", "S224", "S24"]
	},
	"Dempsey": {  # Button name for Tanglin area
		"forecast_area": "Tanglin",
		"stations": ["S111"]
	},
	"Bishan": {
		"forecast_area": "Bishan",
		"stations": ["S217", "S08"]
	},
	"Boon Lay": {
		"forecast_area": "Boon Lay",
		"stations": ["S33"]
	},
	"Bukit Batok": {
		"forecast_area": "Bukit Batok",
		"stations": ["S201"]
	},
	"Telok Blangah": {  # Button name for Bukit Merah area
		"forecast_area": "Bukit Merah",
		"stations": ["S2222", "S226", "S77"]
	},
	"Bukit Panjang": {
		"forecast_area": "Bukit Panjang",
		"stations": ["S64"]
	},
	"Bukit Timah": {
		"forecast_area": "Bukit Timah",
		"stations": ["S90"]
	},
	"Central Water Catchment": {
		"forecast_area": "Central Water Catchment",
		"stations": ["S69"]
	},
	"Fort Canning": {  # Button name for City area
		"forecast_area": "City",
		"stations": ["S79"]
	},
	"Geylang": {
		"forecast_area": "Geylang",
		"stations": ["S215", "S78"]
	},
	"Hougang": {
		"forecast_area": "Hougang",
		"stations": ["S221"]
	},
	"Jurong Island": {
		"forecast_area": "Jurong Island",
		"stations": ["S117"]
	},
	"Jurong West": {
		"forecast_area": "Jurong West",
		"stations": ["S228", "S229"]
	},
	"Kallang": {
		"forecast_area": "Kallang",
		"stations": ["S119", "S123", "S108"]
	},
	"Mandai": {
		"forecast_area": "Mandai",
		"stations": ["S40"]
	},
	"Mount Pleasant": {
		"forecast_area": "Novena",
		"stations": ["S213", "S07"]
	},
	"Pasir Ris": {
		"forecast_area": "Pasir Ris",
		"stations": ["S94"]
	},
	"Pulau Ubin": {
		"forecast_area": "Pulau Ubin",
		"stations": ["S106"]
	},
	"Punggol": {
		"forecast_area": "Punggol",
		"stations": ["S81"]
	},
	"Kent Ridge": {  # Button name for Queenstown area
		"forecast_area": "Queenstown",
		"stations": ["S203", "S92", "S223", "S71"]
	},
	"Seletar": {
		"forecast_area": "Seletar",
		"stations": ["S900"]
	},
	"Buangkok": {
		"forecast_area": "Sengkang",
		"stations": ["S220"]
	},
	"Sungei Kadut": {
		"forecast_area": "Sungei Kadut",
		"stations": ["S211", "S66"]
	},
	"Tampines": {
		"forecast_area": "Tampines",
		"stations": ["S84"]
	},
	"Toa Payoh": {
		"forecast_area": "Toa Payoh",
		"stations": ["S88"]
	},
	"Tuas": {
		"forecast_area": "Tuas",
		"stations": ["S115"]
	},
	"Western Islands": {
		"forecast_area": "Western Islands",
		"stations": ["S102"]
	},
	"Western Water Catchment": {
		"forecast_area": "Western Water Catchment",
		"stations": ["S112"]
	},
	"Woodlands": {
		"forecast_area": "Woodlands",
		"stations": ["S210"]
	},
	"Yishun": {
		"forecast_area": "Yishun",
		"stations": ["S209"]
	},
	# Forecast areas without rainfall stations
	"Bedok": {
		"forecast_area": "Bedok",
		"stations": []
	},
	"Choa Chu Kang": {
		"forecast_area": "Choa Chu Kang",
		"stations": []
	},
	"Jurong East": {
		"forecast_area": "Jurong East",
		"stations": []
	},
	"Lim Chu Kang": {
		"forecast_area": "Lim Chu Kang",
		"stations": []
	},
	"Pioneer": {
		"forecast_area": "Pioneer",
		"stations": []
	},
	"Serangoon": {
		"forecast_area": "Serangoon",
		"stations": []
	},
	"Tengah": {
		"forecast_area": "Tengah",
		"stations": []
	},
	"Pulau Tekong": {
		"forecast_area": "Pulau Tekong",
		"stations": []
	},
	"Southern Islands": {
		"forecast_area": "Southern Islands",
		"stations": []
	},
}

def get_rainfall_data(date=None):
	base_url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
	params = {}
	if date:
		params['date'] = date
	
	response = requests.get(base_url, params=params)
	response.raise_for_status()
	return response.json()

def get_temperature_data(date=None):
	base_url = "https://api-open.data.gov.sg/v2/real-time/api/air-temperature"
	params = {}
	if date:
		params['date'] = date
	
	response = requests.get(base_url, params=params)
	response.raise_for_status()
	return response.json()
	
def get_forecast_data(date=None):
	base_url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
	params = {}
	if date:
		params['date'] = date
	response = requests.get(base_url, params=params)
	response.raise_for_status()
	return response.json()

def format_timestamp(ts):
	dt = datetime.fromisoformat(ts)
	try:
		return dt.strftime("%d %b %Y, %-I:%M%p SGT")
	except ValueError:
		return dt.strftime("%d %b %Y, %#I:%M%p SGT")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
		global latest_rainfall_data, latest_temperature_data, latest_station_map
		latest_rainfall_data = get_rainfall_data()
		latest_temperature_data = get_temperature_data()
		
		# Build the global station ID → name map
		latest_station_map = {station['id'].strip().upper(): station['name'] for station in latest_rainfall_data['data']['stations']}
		
		# Build custom location buttons
		buttons = []
		row = []
		for i, location in enumerate(LOCATION_MAP.keys(), start=1):
			row.append(InlineKeyboardButton(location, callback_data=location))
			if i % 2 == 0:  # 2 buttons per row for better readability
				buttons.append(row)
				row = []
		if row:
			buttons.append(row)
		buttons.append([InlineKeyboardButton("Show All Rainfall", callback_data="SHOW_ALL")])
		
		reply_markup = InlineKeyboardMarkup(buttons)
		await update.message.reply_text(
			"Welcome! Please choose a location. You may click this link to view the map of the locations: https://www.google.com/maps/d/u/0/edit?mid=1EXDQiXeSiNkbfT6LaXIpT5nv-2n1ErQ&usp=sharing",
			reply_markup=reply_markup
		)
		return CHOOSING_STATION

async def handle_station_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	choice = query.data
	
	if choice == "SHOW_ALL":
		stations = latest_rainfall_data['data']['stations']
		readings = latest_rainfall_data['data']['readings'][0]
		# Build global station ID → name map
		station_map = {s['id'].strip().upper(): s['name'] for s in stations}
		rainfall_map = {r['stationId'].strip().upper(): r['value'] for r in readings['data']}
	
		lines = [f"Rainfall readings at {format_timestamp(readings['timestamp'])} (only stations with rainfall):\n"]
		for sid, name in station_map.items():
			rain = rainfall_map.get(sid, 0)
			if rain > 0:
				lines.append(f"{name} ({sid}): {rain} {latest_rainfall_data['data']['readingUnit']}")
	
		if len(lines) == 1:
			await query.edit_message_text("No stations are currently reporting rainfall greater than 0 mm.")
		else:
			await query.edit_message_text("\n".join(lines))
	
	else:
		location_info = LOCATION_MAP[choice]
		forecast_data = get_forecast_data()
		forecast_area = location_info["forecast_area"]
		forecast_text = None
		for item in forecast_data["data"]["items"][0]["forecasts"]:
			if item["area"] == forecast_area:
				forecast_text = item["forecast"]
				break
	
		readings = latest_rainfall_data['data']['readings'][0]
		rainfall_map = {r['stationId'].strip().upper(): r['value'] for r in readings['data']}
	
		# Build global station ID → name map once from rainfall data stations
		station_map = {s['id'].strip().upper(): s['name'] for s in latest_rainfall_data['data']['stations']}
	
		print("Rainfall stations in data:", [r['stationId'] for r in readings['data']])
		print("Rainfall map keys:", rainfall_map.keys())
		print(f"Checking rainfall for stations: {location_info['stations']}")
	
		rain_lines = []
		for sid in location_info["stations"]:
			sid_norm = sid.strip().upper()
			value = rainfall_map.get(sid_norm, 0)
			print(f"Station {sid_norm} rainfall: {value}")  # Debug
			if value > 0:
				name = station_map.get(sid_norm, sid_norm)
				rain_lines.append(f"{name} ({sid_norm}): {value} {latest_rainfall_data['data']['readingUnit']}")
	
		temp_readings = latest_temperature_data['data']['readings'][0]['data']
		temp_map = {t['stationId'].strip().upper(): t['value'] for t in temp_readings}
	
		print("Temperature stations in data:", [t['stationId'] for t in temp_readings])
		print("Temperature map keys:", temp_map.keys())
		print(f"Checking temperature for stations: {location_info['stations']}")
	
		temp_lines = []
		for sid in location_info["stations"]:
			sid_norm = sid.strip().upper()
			temp_value = temp_map.get(sid_norm)
			print(f"Station {sid_norm} temperature: {temp_value}")  # Debug
			if temp_value is not None:
				name = station_map.get(sid_norm, sid_norm)
				temp_lines.append(f"{name} ({sid_norm}): {temp_value}°C")
	
		reply_parts = [f"📍 {choice}"]
		update_time = format_timestamp(readings['timestamp'])
		reply_parts.append(f"⏰ {update_time}")
		if forecast_text:
			reply_parts.append(f"🌦️ Forecast: {forecast_text}")
		if rain_lines:
			reply_parts.append("🌧️ Rainfall:\n" + "\n".join(rain_lines))
		else:
			reply_parts.append("☀️ No rainfall reported")
		if temp_lines:
			reply_parts.append("🌡️ Temperature:\n" + "\n".join(temp_lines))
		else:
			reply_parts.append("🌡️ No temperature data available.")
	
		await query.edit_message_text("\n".join(reply_parts))
	
	# Show menu again
	buttons = []
	row = []
	for i, location in enumerate(LOCATION_MAP.keys(), start=1):
		row.append(InlineKeyboardButton(location, callback_data=location))
		if i % 2 == 0:
			buttons.append(row)
			row = []
	if row:
		buttons.append(row)
	buttons.append([InlineKeyboardButton("Show All Rainfall", callback_data="SHOW_ALL")])
	
	reply_markup = InlineKeyboardMarkup(buttons)
	await query.message.reply_text(
		"Choose another location or view all rainfall:",
		reply_markup=reply_markup
	)
	
	return CHOOSING_STATION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("Operation cancelled.")
	return ConversationHandler.END

def main():
	load_dotenv()
	bot_token = os.getenv("TELEGRAM_TOKEN")

	app = ApplicationBuilder().token(bot_token).build()

	conv_handler = ConversationHandler(
		entry_points=[CommandHandler('start', start)],
		states={
			CHOOSING_STATION: [CallbackQueryHandler(handle_station_choice)],
		},
		fallbacks=[CommandHandler('cancel', cancel)],
	)

	app.add_handler(conv_handler)

	print("Bot started...")
	app.run_polling()

if __name__ == '__main__':
	main()
