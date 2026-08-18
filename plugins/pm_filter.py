import asyncio
import re
import ast
import math
import random
import pytz
from datetime import datetime, timedelta, date, time
from database.users_chats_db import db
from database.refer import referdb
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, WebAppInfo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import *
from rapidfuzz import process, fuzz
from database.users_chats_db import db
from database.ia_filterdb import Media, Media2, get_file_details, get_search_results, get_bad_files, get_fuzzy_db_candidates
from logging_helper import LOGGER
from urllib.parse import quote_plus
from Lucia.util.file_properties import get_name, get_hash, get_media_file_size
from database.topdb import silentdb
import requests
import string
import tracemalloc
import atexit

tracemalloc.start()
atexit.register(tracemalloc.stop)

TIMEZONE = "Asia/Kolkata"
BUTTON = {}
BUTTONS = {}
FRESH = {}
SPELL_CHECK = {}
lock = asyncio.Lock()

@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    # --- BOOSTER KILL SWITCH ---
    booster_settings = await get_settings(message.chat.id)
    if booster_settings.get("member_booster", False):
        req_count = booster_settings.get("booster_count", 1)
        bypassed = booster_settings.get("booster_bypass", [])
        u_id = message.from_user.id
        
        if u_id not in ADMINS and u_id not in bypassed:
            is_admin = await is_check_admin(client, message.chat.id, u_id)
            if not is_admin:
                curr_count = await db.get_booster_count(message.chat.id, u_id)
                if curr_count < req_count:
                    return # Kill the spellchecker entirely, let p_ttishow handle the mute
    # ---------------------------
    if not message.from_user:
        return
        
    bot_id = client.me.id
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS))
        except Exception:
            pass
    maintenance_mode = await db.get_maintenance_status(bot_id)
    if maintenance_mode and message.from_user.id not in ADMINS:
        await message.reply_text("ɪ ᴀᴍ ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ 🛠️. ɪ ᴡɪʟʟ ʙᴇ ʙᴀᴄᴋ ꜱᴏᴏɴ 🔜")
        return
    await silentdb.update_top_messages(message.from_user.id, message.text)
    if message.chat.id != SUPPORT_CHAT_ID:
        settings = await get_settings(message.chat.id)
        if settings['auto_ffilter']:
            if re.search(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
                if await is_check_admin(client, message.chat.id, message.from_user.id):
                    return
                return await message.delete()   
            await auto_filter(client, message)
    else:
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        else:
            return await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ✅\n\n📂 ꜰɪʟᴇꜱ ꜰᴏᴜɴᴅ : {str(total_results)}\n🔍 ꜱᴇᴀʀᴄʜ :</b> <code>{search}</code>\n\n<b>‼️ ᴛʜɪs ɪs ᴀ <u>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</u> sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...\n\n📝 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ : 👇</b>",   
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 ᴊᴏɪɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)]]))


@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    bot_id = bot.me.id
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS))
        except Exception:
            pass
    maintenance_mode = await db.get_maintenance_status(bot_id)
    if maintenance_mode and message.from_user.id not in ADMINS:
        await message.reply_text("ɪ ᴀᴍ ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ 🛠️. ɪ ᴡɪʟʟ ʙᴇ ʙᴀᴄᴋ ꜱᴏᴏɴ 🔜")
        return
    if content.startswith(("/", "#")):
        return  
    try:
        await silentdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)
        if pm_search:
            await auto_filter(bot, message)
        else:
            await message.reply_text(
             text=f"<b><i>ɪ ᴀᴍ ɴᴏᴛ ᴡᴏʀᴋɪɴɢ ʜᴇʀᴇ 🚫.\nᴊᴏɪɴ ᴍʏ ɢʀᴏᴜᴘ ꜰʀᴏᴍ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ᴛʜᴇʀᴇ !</i></b>",   
             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ ", url=GRP_LNK)]])
            )
    except Exception as e:
        LOGGER.error(f"An error occurred: {str(e)}")


@Client.on_callback_query(filters.regex(r"^reffff"))
async def refercall(bot, query):
    btn = [[
        InlineKeyboardButton('ɪɴᴠɪᴛᴇ ɪɪɴᴋ', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(f'⏳ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point'),
        InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='premium')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await bot.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto("https://graph.org/file/1a2e64aee3d4d10edd930.jpg")
        )
    await query.message.edit_text(
        text=f'Hay Your refer link:\n\nhttps://t.me/{bot.me.username}?start=reff_{query.from_user.id}\n\nShare this link with your friends, Each time they join,  you will get 10 refferal points and after 100 points you will get 1 month premium subscription.',
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
        )
    await query.answer()
	
async def build_pagination_buttons(btn, total_results, current_offset, next_offset, req, key, settings):
    limit = 10 if settings.get('max_btn') else int(MAX_B_TN)
    total_pages = math.ceil(total_results / limit)
    current_page = math.ceil(current_offset / limit) + 1
    pagination_row = []
    if current_offset > 0:
        prev_offset = max(0, current_offset - limit)
        pagination_row.append(InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{prev_offset}"))
    pagination_row.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))
    if next_offset is not None and next_offset != 0 and next_offset < total_results:
         pagination_row.append(InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{next_offset}"))
    elif next_offset == 0 and current_offset + limit < total_results:
         pass
    if len(pagination_row) == 1 and pagination_row[0].text.startswith(str(current_page)):
         if total_pages > 1:
             btn.append(pagination_row)
         else:
             btn.append([InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭", callback_data="pages")])
    else:
         btn.append(pagination_row)

async def generic_filter_handler(client, query, key, offset, search_query):
    chat_id = query.message.chat.id
    # In PM, use settings ID 0 (PM Verification Settings) instead of user's chat ID
    settings_id = 0 if query.message.chat.type == enums.ChatType.PRIVATE else chat_id
    files, n_offset, total_results = await get_search_results(settings_id, search_query, offset=offset, filter=True)
    if not files:
        await query.answer("🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫", show_alert=1)
        return
    temp.GETALL[key] = files
    settings = await get_settings(settings_id)
    req = query.from_user.id
    btn = []
    if settings.get('button'):
        for file in files:
            btn.append([InlineKeyboardButton(
                text=f"{silent_size(file.file_size)} | {extract_tag(file.file_name)} {clean_filename(file.file_name)}",
                callback_data=f'file#{file.file_id}'
            )])
    btn.insert(0, [
        InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
        InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
        InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
    ])
    btn.insert(1, [InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")])
    await build_pagination_buttons(btn, total_results, offset, n_offset, req, key, settings)
    cap = ""
    if not settings.get('button'):
        curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search_query, offset)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except MessageNotModified:
            pass

async def open_category_handler(client, query, items, prefix, title_text):
    try:
        if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
             return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\nʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass
    _, key, offset = query.data.split("#")
    btn = []
    for i in range(0, len(items)-1, 2):
        btn.append([
            InlineKeyboardButton(
                text=items[i].title(),
                callback_data=f"{prefix}#{items[i].lower()}#{key}#0"
            ),
            InlineKeyboardButton(
                text=items[i+1].title(),
                callback_data=f"{prefix}#{items[i+1].lower()}#{key}#0"
            ),
        ])
    btn.insert(0, [InlineKeyboardButton(text=f"⇊ {title_text} ⇊", callback_data="ident")])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭", callback_data=f"{prefix}#homepage#{key}#0")])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))

async def filter_selection_handler(client, query, prefix):
    _, value, key, offset = query.data.split("#")
    if not value:
        await query.answer()
        return
    offset = int(offset)
    if value == "homepage":
        search = FRESH.get(key)
    else:
        search = BUTTONS.get(key) if BUTTONS.get(key) else FRESH.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return
    search = search.replace("_", " ")
    search = re.sub(r'\s+', ' ', search).strip()
    if value != "homepage":
        category_list = []
        if prefix == "fq":
            category_list = [x for x in QUALITIES if x]
        elif prefix == "fl":
            category_list = [x for x in LANGUAGES if x]
        elif prefix == "fs":
            category_list = [x for x in SEASONS if x]
        is_present = False
        match_pattern = ""
        if prefix == "fs":
            season_search = re.search(r"(?i)season\s*(\d+)", value)
            if season_search:
                season_num = int(season_search.group(1))
                added_regex = f"(s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                pattern_combined = re.escape(added_regex)
                if re.search(pattern_combined, search):
                    is_present = True
                    match_pattern = pattern_combined
            else:
                pattern = r'(?i)\b' + re.escape(value) + r'\b'
                if re.search(pattern, search):
                    is_present = True
                    match_pattern = pattern
        elif value.lower().startswith("s") and value[1:].isdigit() and len(value) > 1:
             if value.lower().startswith("s0") and len(value) == 3:
                 short_val = "s" + str(int(value[1:]))
                 added_regex = f"s0?{short_val[1:]}(?:e\\d+)?"
                 pattern_combined = re.escape(added_regex)
                 if re.search(pattern_combined, search):
                     is_present = True
                     match_pattern = pattern_combined
             else:
                pattern = r'(?i)\b' + re.escape(value) + r'\b'
                if re.search(pattern, search):
                    is_present = True
                    match_pattern = pattern
        else:
            pattern = r'(?i)\b' + re.escape(value) + r'\b'
            if re.search(pattern, search):
                is_present = True
                match_pattern = pattern
        if is_present:
            search = re.sub(match_pattern, '', search, count=1)
        else:
            for item in category_list:
                if item.lower() == value.lower():
                    continue
                item_val = item
                if prefix == "fs":
                     season_search = re.search(r"(?i)season\s*(\d+)", item_val)
                     if season_search:
                         season_num = int(season_search.group(1))
                         added_regex = f"(s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                         pattern_combined = re.escape(added_regex)
                         search = re.sub(pattern_combined, '', search)
                     elif item_val.lower().startswith("s0") and len(item_val) == 3:
                         short_val = "s" + str(int(item_val[1:]))
                         added_regex = f"s0?{short_val[1:]}(?:e\\d+)?"
                         pattern_combined = re.escape(added_regex)
                         search = re.sub(pattern_combined, '', search)
                     else:
                        pattern = r'(?i)\b' + re.escape(item_val) + r'\b'
                        search = re.sub(pattern, '', search)
                else:
                    pattern = r'(?i)\b' + re.escape(item_val) + r'\b'
                    search = re.sub(pattern, '', search)
            if prefix == "fs":
                 season_search = re.search(r"(?i)season\s*(\d+)", value)
                 if season_search:
                     season_num = int(season_search.group(1))
                     search = f"{search} (s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                 else:
                     search = f"{search} {value}"
            elif value.lower().startswith("s") and value[1:].isdigit() and len(value) > 1:
                 if value.lower().startswith("s0") and len(value) == 3:
                     short_val = "s" + str(int(value[1:]))
                     search = f"{search} s0?{short_val[1:]}(?:e\\d+)?"
                 else:
                     search = f"{search} {value}"
            else:
                search = f"{search} {value}"
    search = re.sub(r'\s+', ' ', search).strip()
    BUTTONS[key] = search
    await generic_filter_handler(client, query, key, offset, search)

async def handle_alert_status(client, query, status_text, alert_message, log_hashtag, is_hindi=False):
    ident, from_user = query.data.split("#")
    btn = [[InlineKeyboardButton(status_text, callback_data=f"{ident}alert#{from_user}")]]
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
        invite_url = link.invite_link
    except Exception:
        invite_url = GRP_LNK
    btn2 = [[
        InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=invite_url),
        InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
    ]]
    if is_hindi or "Available" in status_text or "Uploaded" in status_text:
         btn2.append([InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)])
    if query.from_user.id in ADMINS:
        user = await client.get_users(from_user)
        reply_markup = InlineKeyboardMarkup(btn)
        content = query.message.text
        await query.message.edit_text(f"<b><strike>{content}</strike></b>")
        await query.message.edit_reply_markup(reply_markup)
        simple_status = status_text.replace("•", "").strip()
        await query.answer(f"Sᴇᴛ ᴛᴏ {simple_status} !")
        content = extract_request_content(query.message.text)
        alert_text = alert_message.format(user_mention=user.mention, content=content)
        try:
            await client.send_message(
                chat_id=int(from_user),
                text=f"{alert_text}\n\n{log_hashtag}",
                reply_markup=InlineKeyboardMarkup(btn2)
            )
        except UserIsBlocked:
             await client.send_message(
                chat_id=int(SUPPORT_CHAT_ID),
                text=f"{alert_text}\n\n{log_hashtag}\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small>",
                reply_markup=InlineKeyboardMarkup(btn2)
            )
    else:
        await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        ident, req, key, offset = query.data.split("_")
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        try:
            offset = int(offset)
        except (ValueError, TypeError):
            offset = 0

        if BUTTONS.get(key)!=None:
            search = BUTTONS.get(key)
        else:
            search = FRESH.get(key)

        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
            return

        await generic_filter_handler(bot, query, key, offset, search)
        await query.answer()
    except Exception as e:
        LOGGER.error(f"Error In Next Function - {e}")


@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, QUALITIES, "fq", "ꜱᴇʟᴇᴄᴛ ǫᴜᴀʟɪᴛʏ")

@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fq")

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, LANGUAGES, "fl", "ꜱᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ")

@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fl")
        
@Client.on_callback_query(filters.regex(r"^seasons#"))
async def season_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, SEASONS, "fs", "ꜱᴇʟᴇᴄᴛ Sᴇᴀsᴏɴ")

@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_season_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fs")

@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if id.startswith("db_"):
        movie = id[3:].replace("_", " ")
    else:
        movies = await get_poster(id, id=True)
        movie = movies.get('title') if (movies and isinstance(movies, dict)) else None
        if not movie and id.startswith("tmdb_"):
            parts = id.split("_")
            if len(parts) >= 3:
                try:
                    from utils import fetch_tmdb_details
                    d = await fetch_tmdb_details(parts[1], parts[2])
                    if d:
                        movie = d.get('title') or d.get('name')
                except Exception:
                    pass
        if not movie:
            movie = id.replace("_", " ")
    if not movie:
        return await query.answer("Could not resolve movie title.", show_alert=True)
    movie = re.sub(r"[:-]", " ", movie)
    movie = re.sub(r"\s+", " ", movie).strip()
    await query.answer(script.TOP_ALRT_MSG)
    settings_id = 0 if query.message.chat.type == enums.ChatType.PRIVATE else query.message.chat.id
    files, offset, total_results = await get_search_results(settings_id, movie, offset=0, filter=True)
    if files:
        k = (movie, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        reqstr1 = query.from_user.id if query.from_user else 0
        reqstr = await bot.get_users(reqstr1)
        if NO_RESULTS_MSG:
            try:
                await bot.send_message(chat_id=BIN_CHANNEL, text=script.NORSLTS.format(reqstr.id, reqstr.mention, movie))
                print(f"[DEBUG] Successfully sent #NoResults to BIN_CHANNEL: {BIN_CHANNEL}")
            except Exception as e:
                print(f"[DEBUG] ERROR sending to BIN_CHANNEL ({BIN_CHANNEL}): {e}")
        google = movie.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔍 ᴄʜᴇᴄᴋ sᴘᴇʟʟɪɴɢ ᴏɴ ɢᴏᴏɢʟᴇ 🔍", url=f"https://www.google.com/search?q={google}")
        ], [
            InlineKeyboardButton("🛎️ Rᴇǫᴜᴇsᴛ Tʜɪs Mᴏᴠɪᴇ", callback_data=f"reqm#{movie[:45]}")
        ]]
        k = await query.message.edit(script.I_CUDNT.format(movie), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await query.message.delete()
        except Exception:
            pass
@Client.on_callback_query(filters.regex(r"^reqm#"))
async def request_movie(bot, query):
    _, keyword = query.data.split("#", 1)
    user_id = query.from_user.id
    chat_id = temp.SHORT.get(user_id, query.message.chat.id)
    if chat_id > 0:
        chat_id = 0
    
    # Check if user has too many pending requests (e.g. max 5)
    pending_count = await db.get_user_pending_requests(user_id)
    if pending_count >= 5:
        return await query.answer("You already have 5 pending requests! Please wait for them to be fulfilled.", show_alert=True)
    
    added = await db.add_request(user_id, chat_id, keyword)
    if not added:
        return await query.answer("⚠️ You have already requested this exact movie! Please wait for it to be uploaded.", show_alert=True)
        
    await query.answer("✅ Your request has been logged! I will DM you as soon as it is uploaded.", show_alert=True)
    
    # Log to BIN_CHANNEL
    if NO_RESULTS_MSG:
        try:
            reqstr = await bot.get_users(user_id)
            await bot.send_message(chat_id=BIN_CHANNEL, text=script.REQUEST_TXT.format(reqstr.id, reqstr.mention, keyword))
            print(f"[DEBUG] Successfully sent #Requested to BIN_CHANNEL: {BIN_CHANNEL}")
        except Exception as e:
            print(f"[DEBUG] ERROR sending #Requested to BIN_CHANNEL ({BIN_CHANNEL}): {e}")
    # Optionally, remove the request button so they don't spam it
    try:
        markup = query.message.reply_markup
        new_keyboard = []
        for row in markup.inline_keyboard:
            new_row = [btn for btn in row if "reqm#" not in (btn.callback_data or "")]
            if new_row:
                new_keyboard.append(new_row)
        await query.message.edit_reply_markup(InlineKeyboardMarkup(new_keyboard))
    except Exception:
        pass
        

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    lazyData = query.data
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
    except Exception:
        pass
    if query.data == "close_data":
        await query.message.delete()     
        
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        user = query.message.reply_to_message.from_user.id if query.message.reply_to_message else query.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        grp_id = query.message.chat.id
        if query.message.chat.type == enums.ChatType.PRIVATE:
            grp_id = 0
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{grp_id}_{file_id}")          
                            
    elif query.data.startswith("reqdl#"):
        ident, chat_id, encoded_kw = query.data.split("#")
        import base64
        import random
        from database.ia_filterdb import get_search_results
        
        keyword = base64.urlsafe_b64decode(encoded_kw + "=" * (-len(encoded_kw) % 4)).decode('utf-8')
        chat_id = int(chat_id)
        
        try:
            # In PM, use settings ID 0 (PM Verification Settings)
            settings_id = 0 if query.message.chat.type == enums.ChatType.PRIVATE else chat_id
            files, offset, total_results = await get_search_results(settings_id, keyword, offset=0, filter=True)
            if files:
                key = f"{query.from_user.id}-{random.randint(10000, 99999)}"
                FRESH[key] = keyword
                temp.GETALL[key] = files
                
                settings = await get_settings(settings_id)
                btn = []
                
                if settings.get('button', True):
                    for file in files:
                        btn.append([InlineKeyboardButton(
                            text=f"{silent_size(file.file_size)} | {extract_tag(file.file_name)} {clean_filename(file.file_name)}",
                            callback_data=f'file#{file.file_id}'
                        )])
                
                btn.insert(0, [
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ])
                btn.insert(1, [InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")])
                
                await build_pagination_buttons(btn, total_results, 0, offset, query.from_user.id, key, settings)
                
                msg = await query.message.edit_text(
                    text=f"📁 **Here I Found For Your Search** {keyword}",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                
                if settings.get('auto_delete'):
                    from utils import remove_buttons_after_delay
                    from info import AUTO_DELETE_TIME
                    delete_time = settings.get('auto_del_time', AUTO_DELETE_TIME)
                    asyncio.create_task(remove_buttons_after_delay(msg, delete_time))
            else:
                await query.answer("No files found! They might have been deleted.", show_alert=True)
        except Exception as e:
            import logging
            logging.error(f"Error in reqdl callback: {e}")
            await query.answer("An error occurred.", show_alert=True)

    elif query.data.startswith("sendfiles"):
        clicked = query.from_user.id
        ident, key = query.data.split("#") 
        try:
            grp_id = query.message.chat.id
            if query.message.chat.type == enums.ChatType.PRIVATE:
                grp_id = 0
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=allfiles_{grp_id}_{key}")
            return
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            LOGGER.error(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")
            
    elif query.data.startswith("del"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                LOGGER.error(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")

    elif query.data == "pages":
        await query.answer()    
    
    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text("<b>ꜰɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇꜱꜱ ᴡɪʟʟ ꜱᴛᴀʀᴛ ɪɴ 5 ꜱᴇᴄᴏɴᴅꜱ !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if not result.deleted_count and MULTIPLE_DB:
                        result = await Media2.collection.delete_one({
                            '_id': file_ids,
                        })
                    if result.deleted_count:
                        LOGGER.info(f'ꜰɪʟᴇ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}! ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀꜱᴇ.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>ᴘʀᴏᴄᴇꜱꜱ ꜱᴛᴀʀᴛᴇᴅ ꜰᴏʀ ᴅᴇʟᴇᴛɪɴɢ ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ. ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword} !\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                LOGGER.error(f"Error In killfiledq -{e}")
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ꜰᴏʀ ꜰɪʟᴇ ᴅᴇʟᴇᴛᴀᴛɪᴏɴ !\n\nꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ꜰɪʟᴇꜱ ꜰʀᴏᴍ ᴅʙ ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}.</b>")
    
    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("• ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("• ᴜᴘʟᴏᴀᴅᴇᴅ •", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("• ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"already_available#{from_user}")
             ],[
                InlineKeyboardButton("• ɴᴏᴛ ʀᴇʟᴇᴀꜱᴇᴅ •", callback_data=f"Not_Released#{from_user}"),
                InlineKeyboardButton("• ᴛʏᴘᴇ ᴄᴏʀʀᴇᴄᴛ ꜱᴘᴇʟʟɪɴɢ •", callback_data=f"Type_Correct_Spelling#{from_user}")
             ],[
                InlineKeyboardButton("• ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ʜɪɴᴅɪ •", callback_data=f"Not_Available_In_The_Hindi#{from_user}")
             ]]
        if query.from_user.id in ADMINS:
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Hᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴs !")
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        
    elif query.data.startswith("unavailable"):
        await handle_alert_status(client, query, "• ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ •",
                                  "<b>Hᴇʏ {user_mention},</b>\n\n<u>{content}</u> Hᴀs Bᴇᴇɴ Mᴀʀᴋᴇᴅ Aᴅ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ...💔",
                                  "#Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️")

    elif query.data.startswith("Not_Released"):
        await handle_alert_status(client, query, "📌 Not Released 📌",
                                  "<b>Hᴇʏ {user_mention}\n\n<code>{content}</code>, ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ɴᴏᴛ ʙᴇᴇɴ ʀᴇʟᴇᴀꜱᴇᴅ ʏᴇᴛ</b>",
                                  "#CᴏᴍɪɴɢSᴏᴏɴ...🕊️✌️")

    elif query.data.startswith("Type_Correct_Spelling"):
        await handle_alert_status(client, query, "♨️ Type Correct Spelling ♨️",
                                  "<b>Hᴇʏ {user_mention}\n\nWᴇ Dᴇᴄʟɪɴᴇᴅ Yᴏᴜʀ Rᴇǫᴜᴇsᴛ <code>{content}</code>, Bᴇᴄᴀᴜsᴇ Yᴏᴜʀ Sᴘᴇʟʟɪɴɢ Wᴀs Wʀᴏɴɢ 😢</b>",
                                  "#Wʀᴏɴɢ_Sᴘᴇʟʟɪɴɢ 😑")

    elif query.data.startswith("Not_Available_In_The_Hindi"):
        await handle_alert_status(client, query, " Not Available In The Hindi ",
                                  "<b>Hᴇʏ {user_mention}\n\nYᴏᴜʀ Rᴇǫᴜᴇsᴛ <code>{content}</code> ɪs Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ʀɪɢʜᴛ ɴᴏᴡ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ</b>",
                                  "#Hɪɴᴅɪ_ɴᴏᴛ_ᴀᴠᴀɪʟᴀʙʟᴇ ❌", is_hindi=True)

    elif query.data.startswith("uploaded"):
        await handle_alert_status(client, query, "• ᴜᴘʟᴏᴀᴅᴇᴅ •",
                                  "<b>Hᴇʏ {user_mention},\n\n<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs.\nKɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>",
                                  "#Uᴘʟᴏᴀᴅᴇᴅ✅")

    elif query.data.startswith("already_available"):
        await handle_alert_status(client, query, "• ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ •",
                                  "<b>Hᴇʏ {user_mention},\n\n<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴏᴜʀ ʙᴏᴛ'ꜱ ᴅᴀᴛᴀʙᴀꜱᴇ.\nKɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>",
                                  "#Aᴠᴀɪʟᴀʙʟᴇ 💗")
            
    
    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ ✅", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Uᴘʟᴏᴀᴅᴇᴅ 🔼", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇǫᴜᴇꜱᴛ ɪꜱ Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("hnalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Tʜɪꜱ ɪꜱ Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ❌", show_alert=True)
        else:
            await query.answer("Nᴏᴛ ᴀʟʟᴏᴡᴇᴅ — ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʀᴇǫᴜᴇꜱᴛᴇʀ ❌", show_alert=True)

    elif query.data.startswith("nralert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Tʜᴇ Mᴏᴠɪᴇ/ꜱʜᴏᴡ ɪꜱ Nᴏᴛ Rᴇʟᴇᴀꜱᴇᴅ Yᴇᴛ 🆕", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴄᴀɴ'ᴛ ᴅᴏ ᴛʜɪꜱ ᴀꜱ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ʀᴇǫᴜᴇꜱᴛᴇʀ ❌", show_alert=True)

    elif query.data.startswith("wsalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇǫᴜᴇꜱᴛ ᴡᴀꜱ ʀᴇᴊᴇᴄᴛᴇᴅ ᴅᴜᴇ ᴛᴏ ᴡʀᴏɴɢ sᴘᴇʟʟɪɴɢ ❗", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ sᴇᴇ ᴛʜɪꜱ ❌", show_alert=True)

    
    elif lazyData.startswith("streamfile"):
        _, file_id = lazyData.split(":")
        try:
            user_id = query.from_user.id
            is_premium_user = await db.has_premium_access(user_id)
            if PAID_STREAM and not is_premium_user:
                premiumbtn = [[InlineKeyboardButton("𝖡𝗎𝗒 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 ♻️", callback_data='buy')]]
                await query.answer("<b>📌 ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ᴏɴʟʏ ꜰᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ</b>", show_alert=True)
                await query.message.reply("<b>📌 ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ᴏɴʟʏ ꜰᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ. ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ᴛᴏ ᴀᴄᴄᴇꜱꜱ ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ✅</b>", reply_markup=InlineKeyboardMarkup(premiumbtn))
                return
            username =  query.from_user.mention 
            silent_msg = await client.send_cached_media(
                chat_id=BIN_CHANNEL,
                file_id=file_id,
            )
            fileName = {quote_plus(get_name(silent_msg))}
            silent_stream = f"{URL}watch/{str(silent_msg.id)}/{quote_plus(get_name(silent_msg))}?hash={get_hash(silent_msg)}"
            silent_download = f"{URL}{str(silent_msg.id)}/{quote_plus(get_name(silent_msg))}?hash={get_hash(silent_msg)}"
            btn= [[
                InlineKeyboardButton("𝖲𝗍𝗋𝖾𝖺𝗆", url=silent_stream),
                InlineKeyboardButton("𝖣𝗈𝗐𝗇𝗅𝗈𝖺𝖽", url=silent_download)        
	    ]]
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
	    )
            await silent_msg.reply_text(
                text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                quote=True,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(btn)
	    )                
        except Exception as e:
            LOGGER.error(e)
            await query.answer(f"⚠️ SOMETHING WENT WRONG \n\n{e}", show_alert=True)
            return
           
    
    elif query.data == "pagesn1":
        await query.answer(text=script.PAGE_TXT, show_alert=True)

    elif query.data == "start":
        buttons = [[
                    InlineKeyboardButton('+ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ +', url=f'http://telegram.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('🧧 ᴛʀᴇɴᴅɪɴɢ ', callback_data="topsearch"),
                    InlineKeyboardButton('🎟️ ᴜᴘɢʀᴀᴅᴇ ', callback_data="premium"),
                ],[
                    InlineKeyboardButton('♻️ ᴅᴍᴄᴀ', callback_data='disclaimer'),
                    InlineKeyboardButton('👤 ᴀʙᴏᴜᴛ ', callback_data='me')
                ],[
                    InlineKeyboardButton('🚫 ᴇᴀʀɴ ᴍᴏɴᴇʏ ᴡɪᴛʜ ʙᴏᴛ 🚫', callback_data="earn")
                ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
  
    elif query.data == "give_trial":
        try:
            user_id = query.from_user.id
            has_free_trial = await db.check_trial_status(user_id)
            if has_free_trial:
                await query.answer("🚸 ʏᴏᴜ'ᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ꜰʀᴇᴇ ᴛʀɪᴀʟ ᴏɴᴄᴇ !\n\n📌 ᴄʜᴇᴄᴋᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ ʙʏ : /plan", show_alert=True)
                return
            else:            
                await db.give_free_trial(user_id)
                await query.message.reply_text(
                    text="<b>🥳 ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴꜱ\n\n🎉 ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ <u>5 ᴍɪɴᴜᴛᴇs</u> ꜰʀᴏᴍ ɴᴏᴡ !</b>",
                    quote=False,
                    disable_web_page_preview=True,                  
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 ᴄʜᴇᴄᴋᴏᴜᴛ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ 💸", callback_data='seeplans')]]))
                return    
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "premium":
        try:
            btn = [[
                InlineKeyboardButton('🧧 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ 🧧', callback_data='buy'),
            ],[
                InlineKeyboardButton('👥 ʀᴇꜰᴇʀ ꜰʀɪᴇɴᴅꜱ', callback_data='reffff'),
                InlineKeyboardButton('🈚 ꜰʀᴇᴇ ᴛʀɪᴀʟ', callback_data='give_trial')
            ],[            
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)                        
            await client.edit_message_media(                
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))                       
            )
            await query.message.edit_text(
                text=script.BPREMIUM_TXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "buy":
        try:
            btn = [[ 
                InlineKeyboardButton('ꜱᴛᴀʀ', callback_data='star'),
                InlineKeyboardButton('ᴜᴘɪ', callback_data='upi')
            ],[
                InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='premium')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(SUBSCRIPTION)
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_TEXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "upi":
        try:
            btn = [[ 
                InlineKeyboardButton('📱 ꜱᴇɴᴅ  ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ', url=OWNER_LNK),
            ],[
                InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='buy')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(SUBSCRIPTION)
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_UPI_TEXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "star":
        try:
            btn = [
                InlineKeyboardButton(f"{stars}⭐", callback_data=f"buy_{stars}")
                for stars, days in STAR_PREMIUM_PLANS.items()
            ]
            buttons = [btn[i:i + 2] for i in range(0, len(btn), 2)]
            buttons.append([InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data="buy")])
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
			)
            await query.message.edit_text(
                text=script.PREMIUM_STAR_TEXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
        )
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "earn":
        try:
            btn = [[ 
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=script.EARN_INFO.format(temp.B_LINK),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
			)
        except Exception as e:
            LOGGER.error(e)
                    
    elif query.data == "me":
        buttons = [[
            InlineKeyboardButton ('🎁 sᴏᴜʀᴄᴇ', callback_data='source'),
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME, OWNER_LNK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ 📜', url='https://t.me/MR_TechRobot'),
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='me')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "ref_point":
        await query.answer(f'You Have: {referdb.get_refer_points(query.from_user.id)} Refferal points.', show_alert=True)
    
    
    elif query.data == "disclaimer":
            btn = [[
                    InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="start")
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.DISCLAIMER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML 
            )
		
    await query.answer(MSG_ALRT)

    
async def auto_filter(client, msg, spoll=False):
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if not spoll:
        message = msg
        if message.text.startswith("/"): return
        if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = await replace_words(message.text)
            search = search.lower()
            search = search.replace("-", " ")
            search = search.replace(":", "")
            search = search.replace("'", "")
            search = re.sub(r'\s+', ' ', search).strip()
            
            from plugins import gfilter
            from utils import gfilterparser
            
            if gfilter.IS_GFILTER_ENABLED and search in gfilter.GLOBAL_FILTERS_CACHE:
                text, buttons, alerts = gfilterparser(gfilter.GLOBAL_FILTERS_CACHE[search], search)
                await message.reply_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
                    quote=True,
                    disable_web_page_preview=True
                )
                return

            m=await message.reply_text(f'<b>Wait {message.from_user.mention} Searching Your Query: <i>{search}...</i></b>', reply_to_message_id=message.id)
            # In PM, use settings ID 0 (PM Verification Settings) for IMDB, spell_check, etc.
            settings_id = 0 if message.chat.type == enums.ChatType.PRIVATE else message.chat.id
            files, offset, total_results = await get_search_results(settings_id ,search, offset=0, filter=True)
            settings = await get_settings(settings_id)
            if not files:
                if settings["spell_check"]:
                    ai_sts = await m.edit('🤖 ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ, ᴀɪ ɪꜱ ᴄʜᴇᴄᴋɪɴɢ ʏᴏᴜʀ ꜱᴘᴇʟʟɪɴɢ...')
                    is_misspelled = await ai_spell_check(chat_id = message.chat.id,wrong_name=search)
                    if is_misspelled:
                        await ai_sts.edit(f'<b><i>✅ Aɪ Sᴜɢɢᴇsᴛᴇᴅ ᴍᴇ<code> {is_misspelled}</code> \nSᴏ Iᴍ Sᴇᴀʀᴄʜɪɴɢ ғᴏʀ <code>{is_misspelled}</code></i></b>')
                        await asyncio.sleep(2)
                        message.text = is_misspelled
                        await ai_sts.delete()
                        return await auto_filter(client, message)
                    await ai_sts.delete()
                
                # Call advantage_spell_chok if spell_check is disabled, or if AI found no misspelling
                return await advantage_spell_chok(client, message)
        else:
            return
    else:
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
        m=await message.reply_text(f'<b>Wait {message.from_user.mention} Searching You Query:<i>{search}...</i></b>', reply_to_message_id=message.id)
        settings_id = 0 if message.chat.type == enums.ChatType.PRIVATE else message.chat.id
        settings = await get_settings(settings_id)
        await msg.message.delete()
    
    key = f"{message.chat.id}-{message.id}"
    FRESH[key] = search
    temp.GETALL[key] = files
    temp.SHORT[message.from_user.id] = message.chat.id
    btn = []
    
    if settings.get('button'):
        for file in files:
            btn.append([InlineKeyboardButton(
                text=f"{silent_size(file.file_size)} | {extract_tag(file.file_name)} {clean_filename(file.file_name)}",
                callback_data=f'file#{file.file_id}'
            )])
    
    btn.insert(0, [
        InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
        InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
        InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
    ])
    btn.insert(1, [InlineKeyboardButton("📥 Sᴇɴᴅ Aʟʟ 📥", callback_data=f"sendfiles#{key}")])

    if offset != "":
        req = message.from_user.id if message.from_user else 0
        await build_pagination_buttons(btn, total_results, 0, offset, req, key, settings)
    else:
        btn.append([InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",callback_data="pages")])
    
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    DELETE_TIME = settings.get("auto_del_time", AUTO_DELETE_TIME)
    TEMPLATE = script.IMDB_TEMPLATE_TXT    
    poster_url = None
    if imdb:
        if IS_LANDSCAPE_POSTER:
            tmdb_data = await fetch_tmdb_data(search, imdb.get('year'))
            if tmdb_data:
                backdrop_url = await get_best_visual(tmdb_data)
                if backdrop_url:
                    poster_url = backdrop_url        
            if not poster_url:
                poster_url = imdb.get('poster')  
        else:
            poster_url = imdb.get('poster')
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
        temp.IMDB_CAP[message.from_user.id] = cap
        if not settings.get('button'):
            for file_num, file in enumerate(files, start=1):
                cap += f"\n\n<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}</a></b>"
    else:
        if settings.get('button'):
            cap = f"<b><blockquote>Hᴇʏ,{message.from_user.mention}</blockquote>\n\n📂 Hᴇʀᴇ I Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜʀ Sᴇᴀʀᴄʜ <code>{search}</code></b>\n\n"
        else:
            cap = f"<b><blockquote>Hᴇʏ,{message.from_user.mention}</blockquote>\n\n📂 Hᴇʀᴇ I Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜʀ Sᴇᴀʀᴄʜ <code>{search}</code></b>\n\n"            
            for file_num, file in enumerate(files, start=1):
                cap += f"<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}\n\n</a></b>"                  
    try:
        if imdb and poster_url:
            try:
                hehe = await message.reply_photo(
                    photo=poster_url,
                    caption=cap, 
                    reply_markup=InlineKeyboardMarkup(btn), 
                    parse_mode=enums.ParseMode.HTML
                )
                await m.delete()
                if settings['auto_delete']:
                    asyncio.create_task(delete_after_delay(hehe, DELETE_TIME))
                    asyncio.create_task(delete_after_delay(message, DELETE_TIME))
            except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
                pic = imdb.get('poster')
                if pic:
                    poster = pic.replace('.jpg', "._V1_UX360.jpg")
                    hmm = await message.reply_photo(
                        photo=poster, 
                        caption=cap, 
                        reply_markup=InlineKeyboardMarkup(btn), 
                        parse_mode=enums.ParseMode.HTML
                    )
                    await m.delete()
                    if settings['auto_delete']:
                        asyncio.create_task(delete_after_delay(hmm, DELETE_TIME))
                        asyncio.create_task(delete_after_delay(message, DELETE_TIME))
                else:
                    fek = await m.edit_text(
                        text=cap, 
                        reply_markup=InlineKeyboardMarkup(btn), 
                        parse_mode=enums.ParseMode.HTML
                    )
                    if settings['auto_delete']:
                        asyncio.create_task(delete_after_delay(fek, DELETE_TIME))
                        asyncio.create_task(delete_after_delay(message, DELETE_TIME))
            except Exception as e:
                LOGGER.error(e)
                fek = await m.edit_text(
                    text=cap, 
                    reply_markup=InlineKeyboardMarkup(btn), 
                    parse_mode=enums.ParseMode.HTML
                )
                if settings['auto_delete']:
                    asyncio.create_task(delete_after_delay(fek, DELETE_TIME))
                    asyncio.create_task(delete_after_delay(message, DELETE_TIME))
        else:
            fuk = await m.edit_text(
                text=cap, 
                reply_markup=InlineKeyboardMarkup(btn), 
                disable_web_page_preview=True, 
                parse_mode=enums.ParseMode.HTML
            )
            if settings['auto_delete']:
                asyncio.create_task(delete_after_delay(fuk, DELETE_TIME))
                asyncio.create_task(delete_after_delay(message, DELETE_TIME))
    except KeyError:
        await save_group_settings(message.chat.id, 'auto_delete', True)
        pass

def smart_movie_scorer(query: str, title: str) -> float:
    q_clean = query.strip().lower()
    t_clean = title.strip().lower()
    
    score_sort = fuzz.token_sort_ratio(q_clean, t_clean)
    score_set = fuzz.token_set_ratio(q_clean, t_clean)
    score_ratio = fuzz.ratio(q_clean, t_clean)
    score_partial = fuzz.partial_ratio(q_clean, t_clean)
    
    tokens = re.findall(r'\b\w+\b', t_clean)
    token_max = max([fuzz.ratio(q_clean, tok) for tok in tokens] or [0]) if len(q_clean) <= 5 else 0
    acronym = "".join([tok[0] for tok in tokens if tok])
    acronym_score = fuzz.ratio(q_clean, acronym) if len(acronym) >= 2 else 0

    if len(q_clean) <= 5:
        return float(max(score_sort, score_set, score_ratio, score_partial, token_max, acronym_score))
    else:
        return float(max(score_sort, (score_set * 0.7 + score_sort * 0.3)))


async def ai_spell_check(chat_id, wrong_name):
    async def search_movie(wrong_name):
        LOGGER.info(f"[API CHECK] ai_spell_check called. Active API_PROVIDER: {API_PROVIDER.upper()}")
        if API_PROVIDER.upper() == "TMDB":
            try:
                from utils import fetch_tmdb_search
                results = await fetch_tmdb_search(wrong_name)
                if not results:
                    return []
                # Return list of titles
                return [m.get('title') or m.get('name') for m in results if m.get('title') or m.get('name')]
            except Exception as e:
                LOGGER.error(f"Error in ai_spell_check (TMDB): {e}")
                return []
        elif API_PROVIDER.upper() == "OMDB":
            try:
                from utils import fetch_omdb_search
                results = await fetch_omdb_search(wrong_name)
                if not results:
                    return []
                return [m.get('Title') for m in results if m.get('Title')]
            except Exception as e:
                LOGGER.error(f"Error in ai_spell_check (OMDB): {e}")
                return []
        else:
            try:
                search_results = await asyncio.wait_for(asyncio.to_thread(imdb.search_movie, wrong_name), timeout=5.0)
                if not search_results or not getattr(search_results, 'titles', None):
                    return []
                movie_list = [movie.title for movie in search_results.titles]
                return movie_list
            except asyncio.TimeoutError:
                LOGGER.error("ai_spell_check: imdb.search_movie timed out.")
                return []
            except Exception as e:
                LOGGER.error(f"Error in ai_spell_check: {e}")
                return []
    # 1. Fetch fuzzy candidates from local MongoDB
    db_candidates = await get_fuzzy_db_candidates(wrong_name, limit=10)
    LOGGER.info(f"[SPELL DEBUG] Input: '{wrong_name}' -> Local DB returned {len(db_candidates)} titles: {db_candidates}")

    # 2. Fetch TMDb / external API candidates
    movie_list = await search_movie(wrong_name)
    LOGGER.info(f"[SPELL DEBUG] Input: '{wrong_name}' -> TMDb returned {len(movie_list)} titles: {movie_list[:10]}")
    if not movie_list:
        # Smart retry: TMDb can't handle typos in multi-word queries.
        words = wrong_name.split()
        if len(words) >= 2:
            LOGGER.info(f"[SPELL DEBUG] 0 results for full query. Trying 1-word drop on {len(words)} words...")
            seen_titles = set()
            for i in range(len(words)):
                partial = " ".join(words[:i] + words[i+1:])
                if not partial.strip():
                    continue
                partial_results = await search_movie(partial)
                if partial_results:
                    for title in partial_results:
                        if title not in seen_titles:
                            movie_list.append(title)
                            seen_titles.add(title)
            # If still no results and >= 3 words, try 2-word anchor pairs (e.g. first word + other words)
            if not movie_list and len(words) >= 3:
                LOGGER.info(f"[SPELL DEBUG] 0 results from 1-word drop. Trying 2-word anchor pairs...")
                for i in range(1, len(words)):
                    pair_q = f"{words[0]} {words[i]}"
                    pair_results = await search_movie(pair_q)
                    if pair_results:
                        for title in pair_results:
                            if title not in seen_titles:
                                movie_list.append(title)
                                seen_titles.add(title)
            # Also try just the longest word alone (e.g. "spiderman")
            if not movie_list:
                longest_word = max(words, key=len)
                if len(longest_word) >= 3:
                    LOGGER.info(f"[SPELL DEBUG] Trying longest word alone: '{longest_word}'")
                    longest_results = await search_movie(longest_word)
                    if longest_results:
                        movie_list.extend(longest_results)

    # Combine DB candidates first, followed by external API candidates (deduplicated)
    all_candidates = []
    seen = set()
    for t in (db_candidates + movie_list):
        t_clean = t.strip().lower()
        if t_clean and t_clean not in seen:
            all_candidates.append(t.strip())
            seen.add(t_clean)

    if not all_candidates:
        LOGGER.info(f"[SPELL DEBUG] No candidates returned from DB or TMDb, giving up.")
        return

    scored_candidates = [(cand, smart_movie_scorer(wrong_name, cand)) for cand in all_candidates]
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Only auto-correct without asking if we are VERY SURE (score >= 85%)
    if not scored_candidates or scored_candidates[0][1] < 85:
        LOGGER.info(f"[SPELL DEBUG] Best candidate score {scored_candidates[0][1] if scored_candidates else 'None'} is below 85% certainty threshold. Showing suggestions to user.")
        return None
        
    closest_match = scored_candidates[0]
    LOGGER.info(f"[SPELL DEBUG] High confidence match (>=85%) -> '{closest_match[0]}' with score {closest_match[1]}")
    movie = closest_match[0]
    
    # Try exact title first
    files, offset, total_results = await get_search_results(chat_id=settings_id, query=movie)
    LOGGER.info(f"[SPELL DEBUG] DB search '{movie}' -> found {len(files)} files")
    if not files:
        # Try normalized version (strip special chars like : - ' etc.)
        cleaned = re.sub(r"[:\-'()]", " ", movie)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned != movie:
            files, offset, total_results = await get_search_results(chat_id=settings_id, query=cleaned)
            LOGGER.info(f"[SPELL DEBUG] DB search normalized '{cleaned}' -> found {len(files)} files")
    if files:
        LOGGER.info(f"[SPELL DEBUG] [SUCCESS] Returning corrected title: '{movie}'")
        return movie
        
    # Top match is not in DB -> DO NOT degrade into random weak DB matches!
    LOGGER.info(f"[SPELL DEBUG] Top match '{movie}' not in DB. Showing suggestions and request options to user.")
    return None

async def advantage_spell_chok(client, message):
    mv_id = message.id
    search = message.text
    chat_id = message.chat.id
    # In PM, use settings ID 0 (PM Verification Settings)
    settings_id = 0 if message.chat.type == enums.ChatType.PRIVATE else chat_id
    settings = await get_settings(settings_id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", message.text, flags=re.IGNORECASE)
    query = query.strip()
    clean_search = query if query else search

    class DummyMovie:
        def __init__(self, t, i):
            self.title = t
            self.imdb_id = i

    combined_movies = []
    seen_titles = set()

    # 1. Get fuzzy movie candidates from local MongoDB
    try:
        db_candidates = await get_fuzzy_db_candidates(clean_search, limit=5)
        for t in db_candidates:
            t_lower = t.strip().lower()
            if t_lower and t_lower not in seen_titles:
                combined_movies.append(DummyMovie(t.strip(), f"db_{t.strip().replace(' ', '_')[:35]}"))
                seen_titles.add(t_lower)
    except Exception as e:
        LOGGER.error(f"get_fuzzy_db_candidates failed in advantage_spell_chok: {e}")

    # 2. Get movie suggestions from TMDb / OMDb (with smart word-drop intact)
    try:
        tmdb_movies = await get_poster(clean_search, bulk=True)
        if tmdb_movies:
            for m in tmdb_movies:
                m_title = getattr(m, 'title', None) or getattr(m, 'name', None) or ""
                m_lower = m_title.strip().lower()
                if m_title and m_lower not in seen_titles:
                    combined_movies.append(m)
                    seen_titles.add(m_lower)
    except Exception as e:
        LOGGER.error(f"get_poster failed in advantage_spell_chok: {e}")

    # Rank suggestions by smart_movie_scorer to the user's search query
    if combined_movies:
        combined_movies.sort(
            key=lambda m: smart_movie_scorer(clean_search, getattr(m, 'title', '') or ''),
            reverse=True
        )
        movies = combined_movies[:MAX_LIST_ELM]
    else:
        movies = None
        
    if not movies:
        reqstr1 = message.from_user.id if message.from_user else 0
        reqstr = await client.get_users(reqstr1)
        if NO_RESULTS_MSG:
            try:
                await client.send_message(chat_id=BIN_CHANNEL, text=script.NORSLTS.format(reqstr.id, reqstr.mention, search))
                print(f"[DEBUG] Successfully sent #NoResults to BIN_CHANNEL: {BIN_CHANNEL}")
            except Exception as e:
                print(f"[DEBUG] ERROR sending to BIN_CHANNEL ({BIN_CHANNEL}): {e}")
        google = search.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔍 ᴄʜᴇᴄᴋ sᴘᴇʟʟɪɴɢ ᴏɴ ɢᴏᴏɢʟᴇ 🔍", url=f"https://www.google.com/search?q={google}")
        ], [
            InlineKeyboardButton("🛎️ Rᴇǫᴜᴇsᴛ Tʜɪs Mᴏᴠɪᴇ", callback_data=f"reqm#{search[:45]}")
        ]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except Exception:
            pass
        return
    user = message.from_user.id if message.from_user else 0
    buttons = [[
        InlineKeyboardButton(text=movie.title, callback_data=f"spol#{movie.imdb_id}#{user}")
    ]
        for movie in movies
    ]
    buttons.append([
        InlineKeyboardButton("🛎️ Rᴇǫᴜᴇsᴛ Tʜɪs Mᴏᴠɪᴇ", callback_data=f"reqm#{search[:45]}"),
        InlineKeyboardButton(text="🚫 ᴄʟᴏsᴇ 🚫", callback_data='close_data')
    ])
    d = await message.reply_text(text=script.CUDNT_FND.format(search), reply_markup=InlineKeyboardMarkup(buttons), reply_to_message_id=message.id)
    await asyncio.sleep(60)
    await d.delete()
    try:
        await message.delete()
    except Exception:
        pass
