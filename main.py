import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup   #pip install python-telegram-bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, JobQueue, CallbackQueryHandler
import random
import sys
from datetime import time as dtime
import asyncio
import json
from pathlib import Path
import requests


my_secret = os.environ['SEALBOT_SECRET']

picturespath = sys.path[0]+"/pictures"

# get all available pics in this directory
types = ('*.jpg', '*.gif')
images = []
for files in types:
    images += Path(picturespath).glob(files)
availablepics = [p.name for p in images]
availablepics.sort()

sealbot_admins = os.environ["SEALBOT_ADMINS"].split(",")


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


async def seal(update: Update, context: CallbackContext):
    try:
        if context.args[0] in availablepics:
            if "jpg" in context.args[0].split(".", 1):
                await context.bot.send_photo(chat_id=update.effective_chat.id,
                                            photo=open(os.path.join(picturespath, context.args[0]), "rb"),
                                            reply_to_message_id=update.message.message_id)
            else:
                await context.bot.send_animation(chat_id=update.effective_chat.id,
                                                animation=open(os.path.join(picturespath, context.args[0]), "rb"),
                                                reply_to_message_id=update.message.message_id)
        else:
            random_choice = random.choice(availablepics)
            if "jpg" in random_choice.split(".", 1):
                await context.bot.send_photo(chat_id=update.effective_chat.id,
                                            photo=open(os.path.join(picturespath, random_choice), "rb"),
                                            reply_to_message_id=update.message.message_id)
            else:
                await context.bot.send_animation(chat_id=update.effective_chat.id,
                                                animation=open(os.path.join(picturespath, random_choice), "rb"),
                                                reply_to_message_id=update.message.message_id)
    except:
        random_choice = random.choice(availablepics)
        if "jpg" in random_choice.split(".", 1):
            await context.bot.send_photo(chat_id=update.effective_chat.id,
                                        photo=open(os.path.join(picturespath, random_choice), "rb"),
                                        reply_to_message_id=update.message.message_id)
        else:
            await context.bot.send_animation(chat_id=update.effective_chat.id,
                                            animation=open(os.path.join(picturespath, random_choice), "rb"),
                                            reply_to_message_id=update.message.message_id)

async def seallist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type in ("group", "supergroup"):
        keyboardPm = await build_pm_keyboard((await context.bot.get_me()).username)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text="This command is meant for private messages.",
                                        reply_markup=keyboardPm,
                                        reply_to_message_id=update.message.message_id if update.message else None)
    else:
        keyboard = await build_list_keyboard(page=0)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text=f"Number of pictures available: {len(availablepics)}\nPage: 1 / {len(availablepics) // 8 + 1}\n Choose a picture:",
                                        reply_markup=keyboard,
                                        reply_to_message_id=update.message.message_id if update.message else None)
    return


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0]:
        if context.args and context.args[0] == "seallist":
            await seallist(update, context)
            return
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                            text="Hello! I'm SealBot. Use /seal to get a random seal picture or /seallist to choose one from the list.",
                                            reply_to_message_id=update.message.message_id if update.message else None)
        return

async def build_pm_keyboard(me) -> InlineKeyboardMarkup:
    url = f"https://t.me/{me}?start=seallist"
    keyboardPm = [[InlineKeyboardButton("open PM", url=url)]]
    return InlineKeyboardMarkup(keyboardPm)

async def build_list_keyboard(page: int = 0, page_size: int = 8) -> InlineKeyboardMarkup:
    start_idx = page * page_size
    chunk = availablepics[start_idx:start_idx + page_size]
    buttons = [[InlineKeyboardButton(name, callback_data=f"send:{name}")] for name in chunk]

    nav = []
    if start_idx > 0:
        nav.append(InlineKeyboardButton("⟨ Prev", callback_data=f"page:{page-1}"))
    if start_idx + page_size < len(availablepics):
        nav.append(InlineKeyboardButton("Next ⟩", callback_data=f"page:{page+1}"))
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(buttons)


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""

    if data.startswith("send:"):
        fname = data.split(":", 1)[1]
        path = os.path.join(picturespath, fname)
        if not os.path.exists(path):
            await context.bot.send_message(chat_id=query.message.chat.id, text="File not found.")
            return
        if fname.lower().endswith('.jpg'):
            await context.bot.send_photo(chat_id=query.message.chat.id, photo=open(path, "rb"))
        else:
            await context.bot.send_animation(chat_id=query.message.chat.id, animation=open(path, "rb"))

    elif data.startswith("page:"):
        try:
            page = int(data.split(":", 1)[1])
        except:
            page = 0
        keyboard = await build_list_keyboard(page=page)
        # edit the message to show the new page
        try:
            await query.message.edit_text(text=f"Number of pictures available: {len(availablepics)}\nPage: {page+1} / {len(availablepics) // 8 + 1}\n Choose a picture:", reply_markup=keyboard)
        except:
            # fallback: send a new message if edit fails
            await context.bot.send_message(chat_id=query.message.chat.id, text=f"Number of pictures available: {len(availablepics)}\nPage: {page+1} / {len(availablepics) // 8 + 1}\n Choose a picture:", reply_markup=keyboard)



async def send_update_message(context: CallbackContext):
    update_date = ""
    file_path = sys.path[0]+"/ota/dreamlte.json"
    if os.path.exists(file_path):
        with open(file_path) as f:
            data = json.load(f)
            update_date = data["response"][0]["datetime"]
    

    os.system(f"rm {file_path}")
    os.system(f"curl -LJO --insecure --output-dir {os.path.dirname(file_path)} https://raw.githubusercontent.com/ivanmeler/ota_provider/master/21.0/dreamlte.json")
    while not os.path.exists(file_path):
        print("it is not there yet")
        asyncio.sleep(1)
    else:
        if os.path.exists(file_path):
            with open(file_path) as f:
                data = json.load(f)
                update_date_cache = data["response"][0]["datetime"]
                version = data["response"][0]["version"]
        if update_date != update_date_cache:
            await context.bot.send_message(chat_id=os.environ['SEALBOT_UPDATE_CHATID'], text=f"New LOS {version} update is available!\n\nKeep in mind: this bot only tracks dreamlte!")


# powered by reddit and meme-api :)
async def post_of_the_day(context: CallbackContext):

    r = requests.get("https://meme-api.com/gimme/seals").json()
    photo_url = r['url']
    text = r['title']
    post_url = r['postLink']
    nsfw = r['nsfw']
    while nsfw:
        r = requests.get("https://meme-api.com/gimme/seals").json()
        photo_url = r['url']
        text = r['title']
        post_url = r['postLink']
        nsfw = r['nsfw']

    # convert imgur links so they work properly
    if "imgur.com" in photo_url and not photo_url.endswith((".jpg", ".png", ".gif")):
        photo_url = photo_url.replace("imgur.com/", "i.imgur.com/") + ".jpg"

    print("sending:", photo_url)
    await context.bot.send_photo(
        chat_id=os.environ['SEALBOT_UPDATE_CHATID'],
        photo=photo_url,
        caption=text+f'\n\n<a href="{post_url}">link to post</a>',
        parse_mode="HTML"
        )

# random seals from r/seals (usable for admins only - for now)
async def rseal(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if str(user_id) in sealbot_admins:
        await post_of_the_day(context)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="only available for seally admins - for now.")

async def oscar(update: Update, context: CallbackContext):
    response = requests.get("https://files.nerv.run/oscar", allow_redirects=True)
    final_url = response.url
    await context.bot.send_photo(chat_id=update.effective_chat.id,
                                photo=final_url,
                                reply_to_message_id=update.message.message_id)

async def add(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if str(user_id) in sealbot_admins:
        try:
            global images
            global availablepics

            if update.message.reply_to_message.photo:
                photo_message = update.message.reply_to_message
                file_id = photo_message.photo[-1].file_id
                new_file = await context.bot.get_file(file_id)
                
            elif update.message.reply_to_message.animation:
                animation_message = update.message.reply_to_message
                file_id = animation_message.animation.file_id
                new_file = await context.bot.get_file(file_id)
            
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Wrong input. \nusage: react to a picture with /add filename (don't forget the file extension type!)"
                                            , reply_to_message_id=update.message.message_id)
                return

            await new_file.download_to_drive(os.path.join(picturespath, context.args[0]))
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your picture has been saved as {context.args[0]}'
                                            , reply_to_message_id=update.message.message_id)

            #reload available pictures
            images = []
            availablepics = []
            for files in types:
                images += Path(picturespath).glob(files)
            availablepics = [p.name for p in images]
            availablepics.sort()
        except:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Wrong input. \nusage: react to a picture with /add filename (don't forget the file extension type!)"
                                            , reply_to_message_id=update.message.message_id)

async def remove(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if str(user_id) in sealbot_admins:
        global images
        global availablepics
        try:
            os.remove(os.path.join(picturespath, context.args[0]))
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'The picture {context.args[0]}. has been removed'
                                            , reply_to_message_id=update.message.message_id)
            
            #reload available pictures
            images = []
            availablepics = []
            for files in types:
                images += Path(picturespath).glob(files)
            availablepics = [p.name for p in images]
            availablepics.sort()
        except:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Wrong input. \nusage: /remove filename (with file extension type) "
                                            , reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    application = ApplicationBuilder().token(my_secret).build()

    start_handler = CommandHandler('seal', seal)
    application.add_handler(start_handler)

    list_handler = CommandHandler("seallist", seallist)
    application.add_handler(list_handler)

    add_handler = CommandHandler("add", add)
    application.add_handler(add_handler)

    remove_handler = CommandHandler("remove", remove)
    application.add_handler(remove_handler)

    rseal_handler = CommandHandler("rseal", rseal)
    application.add_handler(rseal_handler)

    oscar_handler = CommandHandler("oscar", oscar)
    application.add_handler(oscar_handler)

    # register callback query handler for inline keyboard interactions
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Start the send_update_message function in a new thread
    application.job_queue.run_daily(send_update_message, time=dtime(hour=16, minute=0))

    # Start the post_of_the_day function in a new thread
    application.job_queue.run_daily(post_of_the_day, time=dtime(hour=12, minute=0))

    application.run_polling()
