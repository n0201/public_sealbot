import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup   #pip install python-telegram-bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext, JobQueue, CallbackQueryHandler
import random
import sys
from datetime import time as dtime
import time
import json
from pathlib import Path
import requests
from PIL import Image, ImageFile
from io import BytesIO

ImageFile.LOAD_TRUNCATED_IMAGES = True
MAX_BYTES = 10485760
QUALITY_STEP = 5

my_secret = os.environ['SEALBOT_SECRET']

picturespath = sys.path[0]+"/pictures"

# get all available pics in this directory
types = ('*.jpg', '*.gif', '*.png', '*.mp4', '*.webm', '*.mov')
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
            if context.args[0].split(".", 1)[1] in ("jpg", "png"):
                await context.bot.send_photo(chat_id=update.effective_chat.id,
                                            photo=open(os.path.join(picturespath, context.args[0]), "rb"),
                                            reply_to_message_id=update.message.message_id)
            elif context.args[0].split(".", 1)[1] in ("gif"):
                await context.bot.send_animation(chat_id=update.effective_chat.id,
                                                animation=open(os.path.join(picturespath, context.args[0]), "rb"),
                                                reply_to_message_id=update.message.message_id)
            elif context.args[0].split(".", 1)[1] in ("mp4", "webm", "mov"):
                await context.bot.send_video(chat_id=update.effective_chat.id,
                                            video=open(os.path.join(picturespath, context.args[0]), "rb"),
                                            reply_to_message_id=update.message.message_id)
        else:
            random_choice = random.choice(availablepics)
            if random_choice.split(".", 1)[1] in ("jpg", "png"):
                await context.bot.send_photo(chat_id=update.effective_chat.id,
                                            photo=open(os.path.join(picturespath, random_choice), "rb"),
                                            reply_to_message_id=update.message.message_id)
            elif random_choice.split(".", 1)[1] in ("gif"):
                await context.bot.send_animation(chat_id=update.effective_chat.id,
                                                animation=open(os.path.join(picturespath, random_choice), "rb"),
                                                reply_to_message_id=update.message.message_id)
            elif random_choice.split(".", 1)[1] in ("mp4", "webm", "mov"):
                await context.bot.send_video(chat_id=update.effective_chat.id,
                                            video=open(os.path.join(picturespath, random_choice), "rb"),
                                            reply_to_message_id=update.message.message_id)
    except:
        random_choice = random.choice(availablepics)
        if random_choice.split(".", 1)[1] in ("jpg", "png"):
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

# doesn't work yet
async def build_update_keyboard() -> InlineKeyboardMarkup:
    url = f"intent://open/#Intent;launchFlags=0x10000000;component=org.lineageos.updater/org.lineageos.updater.UpdatesActivity;end"
    keyboardPm = [[InlineKeyboardButton("Open los updater", url=url)]]
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
        elif fname.lower().endswith('.png'):
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



# TODO: Add inline keyboard to open LOS updater app
async def send_update_message(context: CallbackContext, chat_id=os.environ['SEALBOT_UPDATE_CHATID']):
    update_date = ""
    file_path = sys.path[0]+"/ota/ota.json"
    if os.path.exists(file_path):
        with open(file_path) as f:
            data = json.load(f)
            update_date = data["response"][0]["datetime"]
    

    os.system(f"rm {file_path}")
    os.system(f"curl -L --insecure -o {os.path.dirname(file_path)}/ota.json https://nextcloud.cakestwix.com/public.php/dav/files/4TZfePNyzm7Bpw9")
    while not os.path.exists(file_path):
        print("it is not there yet")
        time.sleep(1)
    else:
        if os.path.exists(file_path):
            with open(file_path) as f:
                data = json.load(f)
                update_date_cache = data["response"][0]["datetime"]
                version = data["response"][0]["version"]
        if update_date != update_date_cache:
            await context.bot.send_message(chat_id=chat_id, text=f"New LOS {version} update is available!\n\nKeep in mind: this bot only tracks dream2lte!"
                                            )


# powered by reddit and meme-api :)
async def post_of_the_week(context: CallbackContext, chat_id=os.environ['SEALBOT_UPDATE_CHATID']):

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
    if "imgur.com" in photo_url and not photo_url.endswith((".jpg", ".png")):
        photo_url = photo_url.replace("imgur.com/", "i.imgur.com/") + ".jpg"

    if photo_url.endswith(".gifv"):
        photo_url = photo_url[:-1]  # change .gifv to .gif

    if photo_url.endswith((".png", ".jpg", ".webp")):
        print("sending:", photo_url)
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=text+f'\n\n<a href="{post_url}">link to post</a>',
            parse_mode="HTML"
        )
    elif photo_url.endswith((".gif")):
        print("sending:", photo_url)
        await context.bot.send_animation(
            chat_id=chat_id,
            animation=photo_url,
            caption=text+f'\n\n<a href="{post_url}">link to post</a>',
            parse_mode="HTML"
        )
    
    elif photo_url.endswith((".mp4", ".webm", ".mov")):
        print("sending:", photo_url)
        await context.bot.send_video(
            chat_id=chat_id,
            video=photo_url,
            caption=text+f'\n\n<a href="{post_url}">link to post</a>',
            parse_mode="HTML"
        )

# random seals from r/seals (usable for admins only - for now)
async def rseal(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if str(user_id) in sealbot_admins:
        await post_of_the_week(context, chat_id=update.effective_chat.id)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="only available for seally admins - for now.")

async def update_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if str(user_id) in sealbot_admins:
        await send_update_message(context, chat_id=update.effective_chat.id)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="only available for seally admins - for now.")

async def oscar(update: Update, context: CallbackContext):

    response = requests.get("https://files.nerv.run/oscar", allow_redirects=True, timeout=20, stream=True)

    # fetch actual image bytes
    img_resp = response
    img_resp.raise_for_status()
    if img_resp.headers["Content-Type"].split("/", 1)[1] in ("jpg", "png"):
        src_buf = BytesIO(img_resp.content)
        src_buf.seek(0)

        img = Image.open(src_buf)

        out = BytesIO()
        fmt = (img.format or "").upper()
        img.save(out, format=fmt)
        while out.getbuffer().nbytes > MAX_BYTES:
            if fmt == "JPEG":
                out.seek(0); out.truncate(0)
                img.save(out, format="JPEG", quality=90)
            elif fmt == "PNG":
                out.seek(0); out.truncate(0)
                img.save(out, format="PNG", optimize=True, compress_level=9)
            else:
                out.seek(0); out.truncate(0)
                img.save(out, format=fmt)

        else:
            out.seek(0); out.truncate(0)
            img.save(out, format=fmt)
            out.seek(0)

        await context.bot.send_photo(chat_id=update.effective_chat.id,
                                    photo=out,
                                    reply_to_message_id=update.message.message_id)
    else:
        await context.bot.send_video(chat_id=update.effective_chat.id,
                                        video=BytesIO(img_resp.content),
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
                type_of_file = "photo"
                
            elif update.message.reply_to_message.animation:
                animation_message = update.message.reply_to_message
                file_id = animation_message.animation.file_id
                new_file = await context.bot.get_file(file_id)
                type_of_file = "animation"

            elif update.message.reply_to_message.video:
                video_message = update.message.reply_to_message
                file_id = video_message.video.file_id
                new_file = await context.bot.get_file(file_id)
                type_of_file = "video"
            
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Wrong input. \nusage: react to a picture/animation/gif/video with /add filename (don't forget the file extension type!)"
                                            , reply_to_message_id=update.message.message_id)
                return

            await new_file.download_to_drive(os.path.join(picturespath, context.args[0]))
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your {type_of_file} has been saved as {context.args[0]}'
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
    application = ApplicationBuilder().token(my_secret).read_timeout(60).write_timeout(60).build()

    start_handler = CommandHandler('seal', seal)
    application.add_handler(start_handler)

    list_handler = CommandHandler("seallist", seallist)
    application.add_handler(list_handler)

    add_handler = CommandHandler("add", add)
    application.add_handler(add_handler)

    remove_handler = CommandHandler("remove", remove)
    application.add_handler(remove_handler)

    #update_command = CommandHandler("update", update_command)  # manual trigger for testing
    #application.add_handler(update_command)

    rseal_handler = CommandHandler("rseal", rseal)
    application.add_handler(rseal_handler)

#    oscar_handler = CommandHandler("oscar", oscar)
#    application.add_handler(oscar_handler)

    # register callback query handler for inline keyboard interactions
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.job_queue.run_daily(send_update_message, time=dtime(hour=16, minute=0))

    application.job_queue.run_daily(post_of_the_week, time=dtime(hour=12, minute=0), days=([1]))

    application.run_polling()
