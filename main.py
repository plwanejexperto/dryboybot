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

latest_data = None

def get_rainfall_data(date=None):
	base_url = "https://api-open.data.gov.sg/v2/real-time/api/rainfall"
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
	global latest_data
	latest_data = get_rainfall_data()
	stations = latest_data['data']['stations']

	# Prepare buttons in rows of 3 (adjust as needed)
	buttons = []
	row = []
	for i, station in enumerate(stations, start=1):
		# Use station id as callback_data so we know which one was clicked
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
	await query.answer()  # Acknowledge callback query to remove "loading"

	station_id = query.data
	stations = latest_data['data']['stations']
	station_map = {s['id']: s['name'] for s in stations}

	readings = latest_data['data']['readings'][0]
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
		f"{rainfall_value} {latest_data['data']['readingUnit']}"
	)
	await query.edit_message_text(reply)

	return ConversationHandler.END

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
