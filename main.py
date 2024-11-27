import os
import logging
from telegram import Update  #pip install python-telegram-bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, JobQueue
import random
import sys
from datetime import datetime
import time
import threading
import asyncio
import json
from pathlib import Path

my_secret = os.environ['SEALBOT_SECRET']

picturespath = sys.path[0]+"/pictures"

# get all available pics in this directory
images = Path(picturespath).glob("*.jpg")
availablepics = [p.name for p in images]
availablepics.sort()

sealbot_admins = os.environ["SEALBOT_ADMINS"].split(",")


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


async def seal(update: Update, context: CallbackContext):
    try:
        if context.args[0] in availablepics:
            await context.bot.send_photo(chat_id=update.effective_chat.id,
                                        photo=open(os.path.join(picturespath, context.args[0]), "rb"),
                                         reply_to_message_id=update.message.message_id)
        else:
            await context.bot.send_photo(chat_id=update.effective_chat.id,
                                         photo=open(os.path.join(picturespath, random.choice(availablepics)), "rb"),
                                         reply_to_message_id=update.message.message_id)
    except:
        await context.bot.send_photo(chat_id=update.effective_chat.id,
                                     photo=open(os.path.join(picturespath, random.choice(availablepics)), "rb"),
                                     reply_to_message_id=update.message.message_id)

async def seallist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fileslist = "\n"
    for n in range(len(availablepics) - 1):
        fileslist += availablepics[n] + "\n" 
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Available pictures:"+ fileslist
                                   , reply_to_message_id=update.message.message_id)


async def send_update_message(context: CallbackContext):
    file_path = sys.path[0]+"/ota/dreamlte.json"
    if os.path.exists(file_path):
        with open(file_path) as f:
            data = json.load(f)
            update_date = data["response"][0]["datetime"]
    first_time = True
    while True:
        if (datetime.now().hour == 18 or datetime.now().hour == 12) and datetime.now().minute == 0 and first_time == True:
            os.system(f"rm {file_path}")
            os.system(f"curl -LJO --output-dir {os.path.dirname(file_path)} https://raw.githubusercontent.com/ivanmeler/ota_provider/master/21.0/dreamlte.json")
            while not os.path.exists(file_path):
                print("it is not there yet")
                time.sleep(1)
            else:
                if os.path.exists(file_path):
                    with open(file_path) as f:
                        data = json.load(f)
                        update_date_cache = data["response"][0]["datetime"]
                sending_error = False
                if update_date != update_date_cache:
                    while sending_error == False:
                        try:
                            await context.bot.send_message(chat_id=os.environ['SEALBOT_UPDATE_CHATID'], text="New update available!") # CHAT ID MISSING
                            sending_error = True
                        except:
                            pass
                first_time = False
                update_date = update_date_cache
        elif datetime.now().minute == 1 and (datetime.now().hour == 18 or datetime.now().hour == 12):
            first_time = True
        await asyncio.sleep(45)

async def add(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    if update.message.reply_to_message.photo and str(user_id) in sealbot_admins:
        print("valid")
        photo_message = update.message.reply_to_message
        file_id = photo_message.photo[-1].file_id
        new_file = await context.bot.get_file(file_id)
        
        await new_file.download_to_drive(os.path.join(picturespath, f'{file_id}.jpg'))

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your picture has been saved as {file_id}.jpg'
                                        , reply_to_message_id=update.message.message_id)
        
        #reload available pictures
        images = Path(picturespath).glob("*.jpg")
        availablepics = [p.name for p in images]
        availablepics.sort()

if __name__ == '__main__':
    application = ApplicationBuilder().token(my_secret).build()

    start_handler = CommandHandler('seal', seal)
    application.add_handler(start_handler)

    list_handler = CommandHandler("seallist", seallist)
    application.add_handler(list_handler)

    add_handler = CommandHandler("add", add)
    application.add_handler(add_handler)

    # Start the send_update_message function in a new thread
    threading.Thread(target=asyncio.run, args=(send_update_message(application),)).start()

    application.run_polling()
