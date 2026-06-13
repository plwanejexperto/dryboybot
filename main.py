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

def format_timestamp(ts):
	dt = datetime.fromisoformat(ts)
	try:
		return dt.strftime("Date and time: %B %-d, %Y, at %-I:%M %p SGT")
	except ValueError:
		return dt.strftime("Date and time: %B %#d, %Y, at %#I:%M %p SGT")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	global latest_rainfall_data, latest_temperature_data
	latest_rainfall_data = get_rainfall_data()
	latest_temperature_data = get_temperature_data()
	stations = latest_rainfall_data['data']['stations']

	buttons = []
	row = []
	for i, station in enumerate(stations, start=1):
		row.append(InlineKeyboardButton(station['name'], callback_data=station['id']))
		if i % 3 == 0:
			buttons.append(row)
			row = []
	if row:
		buttons.append(row)

	reply_markup = InlineKeyboardMarkup(buttons)

	await update.message.reply_text(
		"Welcome! Please choose a rainfall station:",
		reply_markup=reply_markup
	)
	return CHOOSING_STATION

async def handle_station_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	
	station_id = query.data
	stations = latest_rainfall_data['data']['stations']
	station_map = {s['id']: s['name'] for s in stations}
	
	readings_rainfall = latest_rainfall_data['data']['readings'][0]['data']
	readings_temperature = latest_temperature_data['data']['readings'][0]['data']
	
	rainfall_value = next((r['value'] for r in readings_rainfall if r['stationId'] == station_id), None)
	temperature_value = next((t['value'] for t in readings_temperature if t['stationId'] == station_id), None)
	
	if rainfall_value is None:
		rainfall_value = "N/A"
	if temperature_value is None:
		temperature_value = "N/A"
	
	timestamp_rainfall = latest_rainfall_data['data']['readings'][0]['timestamp']
	formatted_time = format_timestamp(timestamp_rainfall)
	
	# Compose the reply text
	reply = (
		f"Rainfall reading for {station_map[station_id]} ({station_id})\n"
		f"at {formatted_time}:\n"
		f"🌧 Rainfall: {rainfall_value} {latest_rainfall_data['data']['readingUnit']}\n"
	)
	
	if temperature_value != "N/A":
		reply += f"🌡 Temperature: {temperature_value} {latest_temperature_data['data']['readingUnit']}\n"
	
	reply += "\nChoose another station if you want:"
	
	# Prepare buttons again for re-selection
	buttons = []
	row = []
	for i, station in enumerate(stations, start=1):
		row.append(InlineKeyboardButton(station['name'], callback_data=station['id']))
		if i % 3 == 0:
			buttons.append(row)
			row = []
	if row:
		buttons.append(row)
	reply_markup = InlineKeyboardMarkup(buttons)
	
	await query.edit_message_text(text=reply, reply_markup=reply_markup)
	
	# Stay in the same conversation state so user can pick again
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
