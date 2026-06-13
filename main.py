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
		
		buttons.append([InlineKeyboardButton("Show All Rainfall", callback_data="SHOW_ALL")])
		
		reply_markup = InlineKeyboardMarkup(buttons)
		
		await update.message.reply_text(
			"Welcome! Please choose a rainfall station or view all rainfall data:",
			reply_markup=reply_markup
		)
		return CHOOSING_STATION

async def handle_station_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
		query = update.callback_query
		await query.answer()  # Acknowledge callback query
		
		station_id = query.data
		
		if station_id == "SHOW_ALL":
			stations = latest_rainfall_data['data']['stations']
			readings = latest_rainfall_data['data']['readings'][0]
		
			station_map = {s['id']: s['name'] for s in stations}
			rainfall_map = {r['stationId']: r['value'] for r in readings['data']}
		
			lines = [f"Rainfall readings at {format_timestamp(readings['timestamp'])} (only stations with rainfall):\n"]
			count_rain = 0
			for sid, name in station_map.items():
				rain = rainfall_map.get(sid, 0)
				if rain > 0:
					lines.append(f"{name} ({sid}): {rain} {latest_rainfall_data['data']['readingUnit']}")
					count_rain += 1
		
			if count_rain == 0:
				await query.edit_message_text("No stations are currently reporting rainfall greater than 0 mm.")
			else:
				message_text = "\n".join(lines)
				# Telegram max message length is ~4096, chunk if needed
				if len(message_text) > 4000:
					for i in range(0, len(lines), 30):
						await query.message.reply_text("\n".join(lines[i:i+30]))
					await query.edit_message_text("Displayed all rainfall readings above.")
				else:
					await query.edit_message_text(message_text)
		
			# Rebuild buttons to let user pick again
			buttons = []
			row = []
			for i, station in enumerate(latest_rainfall_data['data']['stations'], start=1):
				row.append(InlineKeyboardButton(station['name'], callback_data=station['id']))
				if i % 3 == 0:
					buttons.append(row)
					row = []
			if row:
				buttons.append(row)
			buttons.append([InlineKeyboardButton("Show All Rainfall", callback_data="SHOW_ALL")])
			reply_markup = InlineKeyboardMarkup(buttons)
		
			await query.message.reply_text(
				"Choose a rainfall station or view all rainfall data:",
				reply_markup=reply_markup
			)
		
			return CHOOSING_STATION
		
		# Single station logic
		stations = latest_rainfall_data['data']['stations']
		station_map = {s['id']: s['name'] for s in stations}
		
		readings = latest_rainfall_data['data']['readings'][0]
		rainfall_value = None
		for reading in readings['data']:
			if reading['stationId'] == station_id:
				rainfall_value = reading['value']
				break
		
		if rainfall_value is None:
			await query.edit_message_text(f"No rainfall data found for station {station_id}.")
			return ConversationHandler.END
		
		formatted_time = format_timestamp(readings['timestamp'])
		
		reply = (
			f"Rainfall reading for {station_map[station_id]} ({station_id})\n"
			f"at {formatted_time}:\n"
			f"{rainfall_value} {latest_rainfall_data['data']['readingUnit']}\n\n"
			"Choose another station or press /cancel to stop."
		)
		
		# Rebuild buttons so user can choose again
		buttons = []
		row = []
		for i, station in enumerate(latest_rainfall_data['data']['stations'], start=1):
			row.append(InlineKeyboardButton(station['name'], callback_data=station['id']))
			if i % 3 == 0:
				buttons.append(row)
				row = []
		if row:
			buttons.append(row)
		buttons.append([InlineKeyboardButton("Show All Rainfall", callback_data="SHOW_ALL")])
		reply_markup = InlineKeyboardMarkup(buttons)
		
		await query.edit_message_text(reply, reply_markup=reply_markup)
		
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
