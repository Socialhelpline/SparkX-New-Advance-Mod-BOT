import asyncio
from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors import UserIsBlocked, PeerIdInvalid, MessageNotModified, FloodWait
from info import *
from utils import get_settings, save_group_settings, delete_group_setting, MAX_B_TN, temp, is_check_admin
from Script import script
from logging_helper import LOGGER
from database.users_chats_db import db
import time
import datetime

async def group_setting_buttons(grp_id):
    settings = await get_settings(grp_id)
    join_hider_status = "✅" if settings.get("join_hider", False) else "❌"
    
    buttons = [[
                InlineKeyboardButton('ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ', callback_data=f'setgs#button#{settings.get("button")}#{grp_id}',),
                InlineKeyboardButton('ʙᴜᴛᴛᴏɴ' if settings.get("button") else 'ᴛᴇxᴛ', callback_data=f'setgs#button#{settings.get("button")}#{grp_id}',),
            ],[
                InlineKeyboardButton('ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ', callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',),
                InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["file_secure"] else 'ᴅɪꜱᴀʙʟᴇ', callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',),
            ],[
                InlineKeyboardButton('ɪᴍᴅʙ ᴘᴏꜱᴛᴇʀ', callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',),
                InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["imdb"] else 'ᴅɪꜱᴀʙʟᴇ', callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',),
            ],[
                InlineKeyboardButton('ꜱᴘᴇʟʟ ᴄʜᴇᴄᴋ', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',),
                InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["spell_check"] else 'ᴅɪꜱᴀʙʟᴇ', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',),
            ],[
                InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',),
                InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["auto_delete"] else 'ᴅɪꜱᴀʙʟᴇ', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',),
            ],[
                InlineKeyboardButton('ᴍᴀx ʙᴜᴛᴛᴏɴꜱ', callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',),
                InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_B_TN}', callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',),
            ],[
                InlineKeyboardButton('ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ', callback_data=f'verification_setgs#{grp_id}',),
            ],[
                InlineKeyboardButton('ʟᴏɢ ᴄʜᴀɴɴᴇʟ', callback_data=f'log_setgs#{grp_id}',),
                InlineKeyboardButton('ꜱᴇᴛ ᴄᴀᴘᴛɪᴏɴ', callback_data=f'caption_setgs#{grp_id}',),
            ],[
                InlineKeyboardButton('ᴄᴜꜱᴛᴏᴍ ꜰꜱᴜʙ', callback_data=f'fsub_setgs#{grp_id}',),
            ],[
                InlineKeyboardButton('🚫 ꜰɪʟᴛᴇʀ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ', callback_data='gfm_menu_open')
            ]]

    # Welcome message is group-only (makes no sense in PM)
    if str(grp_id) != "0":
        buttons.insert(3, [
                InlineKeyboardButton('ᴡᴇʟᴄᴏᴍᴇ ᴍꜱɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',),
                InlineKeyboardButton('ᴇɴᴀʙʟᴇ' if settings["welcome"] else 'ᴅɪꜱᴀʙʟᴇ', callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',),
        ])

    # Only add group-specific buttons if grp_id is not 0 (0 means PM)
    if str(grp_id) != "0":
        buttons[-1].append(InlineKeyboardButton('ᴅᴇʟᴇᴛᴇ ɢʀᴏᴜᴘ', callback_data=f'delete_group_check#{grp_id}'))
        buttons.extend([
            [
                InlineKeyboardButton(f"Join/Left Hider {join_hider_status}", callback_data=f"set_join_hider#{grp_id}")
            ],[
                InlineKeyboardButton('🚀 ᴍᴇᴍʙᴇʀ ʙᴏᴏꜱᴛᴇʀ', callback_data=f'booster_setgs#{grp_id}'),
            ]
        ])

    buttons.append([
        InlineKeyboardButton('⇋ ᴄʟᴏꜱᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ⇋', callback_data='close_data')
    ])
    
    return buttons

async def get_main_settings_text(grp_id, title):
    settings = await get_settings(grp_id)
    verify_status = settings.get('is_verify', IS_VERIFY)
    verify_text = "ᴏɴ" if verify_status else "ᴏꜰꜰ"
    log_channel = settings.get('log')   
    log_text = f"<code>{log_channel}</code>" if log_channel else "ɴᴏᴛ ꜱᴇᴛ"
    fsub_ids = settings.get('fsub_id')
    if fsub_ids:
        if isinstance(fsub_ids, list):
            fsub_text = ", ".join([f"<code>{id}</code>" for id in fsub_ids])
        else:
            fsub_text = f"<code>{fsub_ids}</code>"
    else:
        fsub_text = "ɴᴏᴛ ꜱᴇᴛ"
    text = (
        f"<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ ⚙\n\n"
        f"✅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ : {verify_text}\n"
        f"📝 ʟᴏɢ ᴄʜᴀɴɴᴇʟ : {log_text}\n"
        f"🚫 ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ : {fsub_text}</b>"
    )
    return text

@Client.on_callback_query(filters.regex(r'^opnsetgrp'))
async def open_settings_group(client, query):
    ident, grp_id = query.data.split("#")
    userid = query.from_user.id if query.from_user else None
    if str(grp_id) == "0":
        if str(userid) not in ADMINS and userid not in ADMINS:
            await query.answer("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ !", show_alert=True)
            return
        title = "PM Verification Settings"
    else:
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ !", show_alert=True)
            return
        title = query.message.chat.title
    btn = await group_setting_buttons(int(grp_id))
    text = await get_main_settings_text(int(grp_id), title)
    try:
        await query.message.edit_text(
                text=text,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(btn)
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit_text(
                text=text,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^opnsetpm'))
async def open_settings_pm(client, query):
    ident, grp_id = query.data.split("#")
    userid = query.from_user.id if query.from_user else None
    
    if str(grp_id) == "0":
        if str(userid) not in ADMINS and userid not in ADMINS:
            await query.answer("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴀɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ !", show_alert=True)
            return
    else:
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ꜱᴜꜰꜰɪᴄɪᴀɴᴛ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ !", show_alert=True)
            return
    title = query.message.chat.title
    btn2 = [[
             InlineKeyboardButton("ᴄʜᴇᴄᴋ ᴍʏ ᴅᴍ 🗳️", url=f"telegram.me/{temp.U_NAME}")
           ]]
    reply_markup = InlineKeyboardMarkup(btn2)
    try:
        await query.message.edit_text(
            f"<b>ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ꜰᴏʀ {title} ʜᴀꜱ ʙᴇᴇɴ ꜱᴇɴᴛ ᴛᴏ ʏᴏᴜ ʙʏ ᴅᴍ.</b>",
            reply_markup=reply_markup
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit_text(
            f"<b>ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ꜰᴏʀ {title} ʜᴀꜱ ʙᴇᴇɴ ꜱᴇɴᴛ ᴛᴏ ʏᴏᴜ ʙʏ ᴅᴍ.</b>",
            reply_markup=reply_markup
        )
    except MessageNotModified:
        pass

    btn = await group_setting_buttons(int(grp_id))
    text = await get_main_settings_text(int(grp_id), title)
    await client.send_message(
        chat_id=userid,
        text=text,
        reply_markup=InlineKeyboardMarkup(btn),
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML,
        reply_to_message_id=query.message.id
    )

@Client.on_callback_query(filters.regex(r'^grp_pm'))
async def group_pm_settings(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)
    btn = await group_setting_buttons(int(grp_id))
    if str(grp_id) == "0":
        title = "PM Verification Settings"
    else:
        try:
            silentx = await client.get_chat(int(grp_id))
            title = silentx.title
        except Exception:
            title = "Group"
    text = await get_main_settings_text(int(grp_id), title)
    try:
        await query.message.edit(text=text, reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(text=text, reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^verification_setgs'))
async def verification_settings(client, query):
    grp_id = query.data.split("#")[-1]
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)

    settings = await get_settings(int(grp_id))
    verify_status = settings.get('is_verify', IS_VERIFY)
    verify_text = "ᴏɴ" if verify_status else "ᴏꜰꜰ"

    btn = [[
        InlineKeyboardButton('ᴛᴜʀɴ ᴏꜰꜰ' if verify_status else 'ᴛᴜʀɴ ᴏɴ', callback_data=f'toggleverify#is_verify#{verify_status}#{grp_id}'),
    ],[
        InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ', callback_data=f'changeshortner#{grp_id}'),
    ],[
        InlineKeyboardButton('ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ɢᴀᴘ', callback_data=f'changetime#{grp_id}'),
    ],[
        InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ', callback_data=f'changetutorial#{grp_id}')
    ],[
        InlineKeyboardButton('🔄 ɢʟᴏʙᴀʟ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ʀᴇꜱᴇᴛ', callback_data=f'global_reset_verify#{grp_id}')
    ],[
        InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
    ]]

    text = (
        "<b>ᴀᴅᴠᴀɴᴄᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴏᴅᴇ 📳\n\n"
        "ʏᴏᴜ ᴄᴀɴ ᴄᴜꜱᴛᴏᴍɪᴢᴇᴅ ꜱʜᴏʀᴛɴᴇʀ ᴠᴀʟᴜᴇꜱ ᴀɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ɢᴀᴘ ꜰʀᴏᴍ ʜᴇʀᴇ ✅\n"
        "ᴄʜᴏᴏꜱᴇ ꜰʀᴏᴍ ʙᴇʟᴏᴡ 👇\n\n"
        f"✅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ꜱᴛᴀᴛᴜꜱ : {verify_text}</b>"
    )

    try:
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^global_reset_verify'))
async def global_reset_verify(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)
    
    await db.misc.delete_many({})
    await query.answer("✅ ɢʟᴏʙᴀʟ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ʀᴇꜱᴇᴛ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ! ᴀʟʟ ᴜꜱᴇʀꜱ ᴍᴜꜱᴛ ᴠᴇʀɪꜰʏ ᴀɢᴀɪɴ.", show_alert=True)

@Client.on_callback_query(filters.regex(r'^log_setgs'))
async def log_settings(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)

    settings = await get_settings(int(grp_id))
    log_channel = settings.get('log')
    log_text = f"<code>{log_channel}</code>" if log_channel else "ɴᴏᴛ ꜱᴇᴛ"

    btn = [[
        InlineKeyboardButton('ᴄʜᴀɴɢᴇ ʟᴏɢ', callback_data=f'changelog#{grp_id}'),
        InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ ʟᴏɢ', callback_data=f'removelog#{grp_id}'),
    ],[
        InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
    ]]

    text = (
        "<b>ᴀᴅᴠᴀɴᴄᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴏᴅᴇ 📳\n\n"
        "ʏᴏᴜ ᴄᴀɴ ᴄᴜꜱᴛᴏᴍɪᴢᴇᴅ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ᴠᴀʟᴜᴇ ꜰʀᴏᴍ ʜᴇʀᴇ ✅\n"
        "ᴄʜᴏᴏꜱᴇ ꜰʀᴏᴍ ʙᴇʟᴏᴡ 👇\n\n"
        f"📝 ʟᴏɢ ᴄʜᴀɴɴᴇʟ : {log_text}</b>"
    )
    try:
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^fsub_setgs'))
async def fsub_settings(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)

    settings = await get_settings(int(grp_id))
    fsub_ids = settings.get('fsub_id')
    if fsub_ids and isinstance(fsub_ids, list):
         fsub_text = "\n".join([f"<code>{id}</code>" for id in fsub_ids])
    elif fsub_ids:
         fsub_text = f"<code>{fsub_ids}</code>"
    else:
         fsub_text = "ɴᴏᴛ ꜱᴇᴛ"

    btn = [[
        InlineKeyboardButton('ꜱᴇᴛ ꜰꜱᴜʙ', callback_data=f'set_fsub_ui#{grp_id}'),
        InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ ꜰꜱᴜʙ', callback_data=f'remove_fsub_ui#{grp_id}'),
    ],[
        InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
    ]]

    text = (
        "<b>ᴀᴅᴠᴀɴᴄᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴏᴅᴇ 📳\n\n"
        "ʏᴏᴜ ᴄᴀɴ ᴄᴜꜱᴛᴏᴍɪᴢᴇᴅ ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ ᴠᴀʟᴜᴇ ꜰʀᴏᴍ ʜᴇʀᴇ ✅\n"
        "ᴄʜᴏᴏꜱᴇ ꜰʀᴏᴍ ʙᴇʟᴏᴡ 👇\n\n"
        f"🚫 ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ : \n{fsub_text}</b>"
    )
    try:
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^caption_setgs'))
async def caption_settings(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)

    settings = await get_settings(int(grp_id))
    caption = settings.get('caption')
    caption_text = f"<code>{caption}</code>" if caption else "ɴᴏᴛ ꜱᴇᴛ"

    btn = [[
        InlineKeyboardButton('ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ', callback_data=f'changecaption#{grp_id}'),
        InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ ᴄᴀᴘᴛɪᴏɴ', callback_data=f'removecaption#{grp_id}'),
    ],[
        InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
    ]]

    text = (
        "<b>ᴀᴅᴠᴀɴᴄᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴏᴅᴇ 📳\n\n"
        "ʏᴏᴜ ᴄᴀɴ ᴄᴜꜱᴛᴏᴍɪᴢᴇᴅ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴠᴀʟᴜᴇꜱ ꜰʀᴏᴍ ʜᴇʀᴇ ✅\n"
        "ᴄʜᴏᴏꜱᴇ ꜰʀᴏᴍ ʙᴇʟᴏᴡ 👇\n\n"
        f"📂 ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ : {caption_text}</b>"
    )
    try:
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^removelog'))
async def remove_log(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)
    await delete_group_setting(int(grp_id), 'log')
    await query.answer("ʟᴏɢ ᴄʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ!", show_alert=True)
    await log_settings(client, query)

@Client.on_callback_query(filters.regex(r'^set_fsub_ui'))
async def set_fsub_ui(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)

    m = await query.message.reply("<b>ꜱᴇɴᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴛᴏ ꜱᴇᴛ ᴀꜱ ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ (ᴇx: -100xxxxxxx) ᴏʀ <code>/cancel</code></b>")

    try:
        msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if not msg.text:
            await m.delete()
            await query.message.reply("<b>⚠️ ᴇʀʀᴏʀ: ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛᴇxᴛ ᴏɴʟʏ.</b>")
            return
        if msg.text == "/cancel":
            await m.delete()
            await fsub_settings(client, query)
            return

        try:
            channel_id = int(msg.text)
        except ValueError:
             await m.delete()
             await query.message.reply('<b>ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴇ ɪᴅ ɪꜱ ᴀɴ ɪɴᴛᴇɢᴇʀ.</b>')
             return

        try:
            chat = await client.get_chat(channel_id)
        except Exception as e:
            await m.delete()
            return await query.message.reply(f"<b><code>{channel_id}</code> ɪꜱ ɪɴᴠᴀʟɪᴅ. ᴍᴀᴋᴇ ꜱᴜʀᴇ ʙᴏᴛ ɪꜱ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ</b>")

        if chat.type != enums.ChatType.CHANNEL:
            await m.delete()
            return await query.message.reply(f"<b><code>{channel_id}</code> ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ᴄʜᴀɴɴᴇʟ.</b>")

        settings = await get_settings(int(grp_id))
        current_fsub = settings.get('fsub_id', [])
        if not isinstance(current_fsub, list):
             if current_fsub:
                 current_fsub = [current_fsub]
             else:
                 current_fsub = []
        if channel_id not in current_fsub:
            current_fsub.append(channel_id)

        await save_group_settings(int(grp_id), 'fsub_id', current_fsub)
        await m.delete()
        await msg.delete()

        btn = [[InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'fsub_setgs#{grp_id}')]]
        try:
            await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ ꜰᴏʀᴄᴇ ꜱᴜʙ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ ɢʀᴏᴜᴘ\n\nᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ - {chat.title}\nɪᴅ - <code>{channel_id}</code></b>", reply_markup=InlineKeyboardMarkup(btn))
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ ꜰᴏʀᴄᴇ ꜱᴜʙ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ ɢʀᴏᴜᴘ\n\nᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ - {chat.title}\nɪᴅ - <code>{channel_id}</code></b>", reply_markup=InlineKeyboardMarkup(btn))
        except MessageNotModified:
            pass
    except Exception as e:
        LOGGER.error(e)
        await query.message.reply(f"ᴇʀʀᴏʀ: {e}")

@Client.on_callback_query(filters.regex(r'^remove_fsub_ui'))
async def remove_fsub_ui(client, query):
     _, grp_id = query.data.split("#")
     user_id = query.from_user.id if query.from_user else None
     if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)
     await delete_group_setting(int(grp_id), 'fsub_id')
     await query.answer("ꜰꜱᴜʙ ʀᴇᴍᴏᴠᴇᴅ!", show_alert=True)
     await fsub_settings(client, query)

@Client.on_callback_query(filters.regex(r'^changelog'))
async def change_log(client, query):
    grp_id = query.data.split("#")[1]
    user_id = query.from_user.id if query.from_user else None
    silentx = await client.get_chat(int(grp_id))
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
    settings = await get_settings(int(grp_id))
    log_channel = settings.get(f'log')
    log_text = f"<code>{log_channel}</code>" if log_channel else "ɴᴏᴛ ꜱᴇᴛ"
    try:
        await query.message.edit(f'<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ʟᴏɢ ᴄʜᴀɴɴᴇʟ.\n\nʟᴏɢ ᴄʜᴀɴɴᴇʟ: {log_text}.<b>')
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f'<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ʟᴏɢ ᴄʜᴀɴɴᴇʟ.\n\nʟᴏɢ ᴄʜᴀɴɴᴇʟ: {log_text}.<b>')
    except MessageNotModified:
        pass

    m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ɪᴅ ( ᴇxᴀᴍᴘʟᴇ: -100123569303) ᴏʀ ᴜꜱᴇ <code>/cancel</code> ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>")
    while True:
        log_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if log_msg.text == "/cancel":
            await m.delete()
            await log_settings(client, query)
            return
        if log_msg.text.startswith("-100") and log_msg.text[4:].isdigit() and len(log_msg.text) >= 10:
            try:
                int(log_msg.text)
                break
            except ValueError:
                await query.message.reply("<b>ɪɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ! ᴍᴜꜱᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ ꜱᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ -100 (ᴇxᴀᴍᴘʟᴇ: -100123456789)</b>")
        else:
            await query.message.reply("<b>ɪɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ! ᴍᴜꜱᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ ꜱᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ -100 (ᴇxᴀᴍᴘʟᴇ: -100123456789)</b>")
    await m.delete()
    await log_msg.delete()
    await save_group_settings(int(grp_id), f'log', int(log_msg.text))
    await client.send_message(LOG_API_CHANNEL, f"#Set_Log_Channel\n\nɢʀᴏᴜᴘ ɴᴀᴍᴇ : {silentx.title}\n\nɢʀᴏᴜᴘ ɪᴅ: {grp_id}\nɪɴᴠɪᴛᴇ ʟɪɴᴋ : {invite_link}\n\nᴜᴘᴅᴀᴛᴇᴅ ʙʏ : {query.from_user.username}")
    btn = [
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'log_setgs#{grp_id}')]
    ]
    try:
        await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ᴠᴀʟᴜᴇ ✅\nʟᴏɢ ᴄʜᴀɴɴᴇʟ: <code>{log_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ᴠᴀʟᴜᴇ ✅\nʟᴏɢ ᴄʜᴀɴɴᴇʟ: <code>{log_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^removecaption'))
async def remove_caption(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)
    await delete_group_setting(int(grp_id), 'caption')
    await query.answer("ᴄᴀᴘᴛɪᴏɴ ʀᴇᴍᴏᴠᴇᴅ!", show_alert=True)

    # Redirect back to caption settings
    await caption_settings(client, query)

@Client.on_callback_query(filters.regex(r'^changecaption'))
async def change_caption(client, query):
    grp_id = query.data.split("#")[1]
    user_id = query.from_user.id if query.from_user else None
    silentx = await client.get_chat(int(grp_id))
    invite_link = await client.export_chat_invite_link(grp_id)
    title = silentx.title
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
    settings = await get_settings(int(grp_id))
    current_caption = settings.get(f'caption')
    caption_text = f"<code>{current_caption}</code>" if current_caption else "ɴᴏᴛ ꜱᴇᴛ"

    try:
        await query.message.edit(f'<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ.\n\nᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ: {caption_text}.</b>')
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f'<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ.\n\nᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ: {caption_text}.</b>')
    except MessageNotModified:
        pass

    m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ\n\nᴄᴀᴘᴛɪᴏɴ ꜰᴏʀᴍᴀᴛ:\nꜰɪʟᴇ ɴᴀᴍᴇ -<code>{file_name}</code>\nꜰɪʟᴇ ᴄᴀᴘᴛɪᴏɴ - <code>{file_caption}</code>\n<code>ꜰɪʟᴇ ꜱɪᴢᴇ - {file_size}</code>\n\nᴏʀ ᴜꜱᴇ <code>/cancel</code> ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>")
    caption_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
    if caption_msg.text == "/cancel":
        await m.delete()
        await caption_settings(client, query)
        return
    await m.delete()
    await caption_msg.delete()
    await save_group_settings(int(grp_id), f'caption', caption_msg.text)
    await client.send_message(LOG_API_CHANNEL, f"#Set_Caption\n\nɢʀᴏᴜᴘ ɴᴀᴍᴇ : {title}\n\nɢʀᴏᴜᴘ ɪᴅ: {grp_id}\nɪɴᴠɪᴛᴇ ʟɪɴᴋ : {invite_link}\n\nᴜᴘᴅᴀᴛᴇᴅ ʙʏ : {query.from_user.username}")
    btn = [
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'caption_setgs#{grp_id}')]
    ]
    try:
        await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴠᴀʟᴜᴇꜱ ✅\n\nᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ: <code>{caption_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴠᴀʟᴜᴇꜱ ✅\n\nᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ: <code>{caption_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^toggleverify'))
async def toggle_verify(client, query):
    _, set_type, status, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
    new_status = not (status == "True")
    await save_group_settings(int(grp_id), set_type, new_status)

    # Reload verification settings menu
    await verification_settings(client, query)

@Client.on_callback_query(filters.regex(r'^changeshortner'))
async def change_shortener(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
    btn = [
        [InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 1', callback_data=f'shortner_menu#1#{grp_id}')],
        [InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 2', callback_data=f'shortner_menu#2#{grp_id}')],
        [InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 3', callback_data=f'shortner_menu#3#{grp_id}')],
        [InlineKeyboardButton('ꜱʜᴏʀᴛɴᴇʀ 4', callback_data=f'shortner_menu#4#{grp_id}')],
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
    ]
    try:
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ꜱʜᴏʀᴛɴᴇʀ ᴛᴏ ᴍᴀɴᴀɢᴇ:</b>", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ꜱʜᴏʀᴛɴᴇʀ ᴛᴏ ᴍᴀɴᴀɢᴇ:</b>", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^shortner_menu'))
async def shortener_menu_handler(client, query):
    _, num, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)

    settings = await get_settings(int(grp_id))
    suffix = "" if num == "1" else f"_{'two' if num == '2' else 'three' if num == '3' else 'four'}"
    current_url = settings.get(f'shortner{suffix}')
    current_api = settings.get(f'api{suffix}')

    text = f"<b>ꜱʜᴏʀᴛᴇɴᴇʀ {num} ꜱᴇᴛᴛɪɴɢꜱ:</b>\n\n🌐 ᴅᴏᴍᴀɪɴ: {current_url or 'ɴᴏᴛ ꜱᴇᴛ'}\n🔗 ᴀᴘɪ: {current_api or 'ɴᴏᴛ ꜱᴇᴛ'}"

    set_text = "ꜱᴇᴛ"

    btn = [
        [InlineKeyboardButton(set_text, callback_data=f'set_verify{num}#{grp_id}')],
        [InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ', callback_data=f'rm_verify{num}#{grp_id}')],
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'changeshortner#{grp_id}')]
    ]
    try:
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^rm_verify'))
async def remove_shortener(client, query):
    shortner_num = query.data.split("#")[0][-1]
    grp_id = query.data.split("#")[1]
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)
    suffix = "" if shortner_num == "1" else f"_{'two' if shortner_num == '2' else 'three' if shortner_num == '3' else 'four'}"
    await delete_group_setting(int(grp_id), f'shortner{suffix}')
    await delete_group_setting(int(grp_id), f'api{suffix}')
    await query.answer(f"ꜱʜᴏʀᴛᴇɴᴇʀ {shortner_num} ʀᴇᴍᴏᴠᴇᴅ!", show_alert=True)
    query.data = f'shortner_menu#{shortner_num}#{grp_id}'
    await shortener_menu_handler(client, query)

@Client.on_callback_query(filters.regex(r'^set_verify'))
async def set_shortener(client, query):
    shortner_num = query.data.split("#")[0][-1]
    grp_id = query.data.split("#")[1]
    user_id = query.from_user.id if query.from_user else None
    silentx = await client.get_chat(int(grp_id))
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
    settings = await get_settings(int(grp_id))
    suffix = "" if shortner_num == "1" else f"_{'two' if shortner_num == '2' else 'three' if shortner_num == '3' else 'four'}"
    current_url = settings.get(f'shortner{suffix}', "ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇᴛ ᴀɴᴅ ᴠᴀʟᴜᴇ ꜱᴏ ᴜꜱɪɴɢ ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ")
    current_api = settings.get(f'api{suffix}', "ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇᴛ ᴀɴᴅ ᴠᴀʟᴜᴇ ꜱᴏ ᴜꜱɪɴɢ ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ")

    # Set query.data for back handling
    query.data = f'shortner_menu#{shortner_num}#{grp_id}'

    try:
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ꜱʜᴏʀᴛɴᴇʀ {shortner_num}:\n🌐 ᴡᴇʙꜱɪᴛᴇ: <code>{current_url}</code>\n🔗 ᴀᴘɪ: <code>{current_api}</code></b>")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ꜱʜᴏʀᴛɴᴇʀ {shortner_num}:\n🌐 ᴡᴇʙꜱɪᴛᴇ: <code>{current_url}</code>\n🔗 ᴀᴘɪ: <code>{current_api}</code></b>")
    except MessageNotModified:
        pass

    m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ꜱʜᴏʀᴛɴᴇʀ ᴡᴇʙꜱɪᴛᴇ ᴏʀ ᴜꜱᴇ <code>/cancel</code> ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>")
    url_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
    if url_msg.text == "/cancel":
        await m.delete()
        await shortener_menu_handler(client, query)
        return
    await m.delete()
    await url_msg.delete()
    n = await query.message.reply("<b>ɴᴏᴡ ꜱᴇɴᴅ ꜱʜᴏʀᴛɴᴇʀ ᴀᴘɪ ᴏʀ ᴜꜱᴇ <code>/cancel</code> ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>")
    key_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
    if key_msg.text == "/cancel":
        await n.delete()
        await shortener_menu_handler(client, query)
        return
    await n.delete()
    await key_msg.delete()
    await save_group_settings(int(grp_id), f'shortner{suffix}', url_msg.text)
    await save_group_settings(int(grp_id), f'api{suffix}', key_msg.text)
    log_message = f"#New_Shortner_Set\n\n ꜱʜᴏʀᴛɴᴇʀ ɴᴏ - {shortner_num}\nɢʀᴏᴜᴘ ʟɪɴᴋ - `{invite_link}`\n\nɢʀᴏᴜᴘ ɪᴅ : `{grp_id}`\nᴀᴅᴅᴇᴅ ʙʏ - `{user_id}`\nꜱʜᴏʀᴛɴᴇʀ ꜱɪᴛᴇ - {url_msg.text}\nꜱʜᴏʀᴛɴᴇʀ ᴀᴘɪ - `{key_msg.text}`"
    await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)

    btn = [
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'shortner_menu#{shortner_num}#{grp_id}')]
    ]
    try:
        await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ꜱʜᴏʀᴛɴᴇʀ {shortner_num} ᴠᴀʟᴜᴇꜱ ✅\n\nᴡᴇʙꜱɪᴛᴇ: <code>{url_msg.text}</code>\nᴀᴘɪ: <code>{key_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ꜱʜᴏʀᴛɴᴇʀ {shortner_num} ᴠᴀʟᴜᴇꜱ ✅\n\nᴡᴇʙꜱɪᴛᴇ: <code>{url_msg.text}</code>\nᴀᴘɪ: <code>{key_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^changetime'))
async def change_time(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
    btn = [
        [InlineKeyboardButton('ᴛɪᴍᴇ 1', callback_data=f'time_menu#1#{grp_id}')],
        [InlineKeyboardButton('ᴛɪᴍᴇ 2', callback_data=f'time_menu#2#{grp_id}')],
        [InlineKeyboardButton('ᴛɪᴍᴇ 3', callback_data=f'time_menu#3#{grp_id}')],
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
    ]
    try:
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ᴛᴏ ᴍᴀɴᴀɢᴇ:</b>", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ᴛᴏ ᴍᴀɴᴀɢᴇ:</b>", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^time_menu'))
async def time_menu_handler(client, query):
    _, num, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)

    settings = await get_settings(int(grp_id))
    # Mapping: 1->verify_time (old 2nd), 2->third_verify_time (old 3rd)
    if num == "1":
        key = "verify_time"
    elif num == "2":
        key = "third_verify_time"
    elif num == "3":
        key = "fourth_verify_time"
    else:
        return await query.answer("Invalid Time Selection")

    val = settings.get(key)
    set_text = "ꜱᴇᴛ"

    btn = [
        [InlineKeyboardButton(set_text, callback_data=f'set_time{num}#{grp_id}')],
        [InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ', callback_data=f'rm_time{num}#{grp_id}')],
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'changetime#{grp_id}')]
    ]
    try:
        await query.message.edit(f"<b>⏰ Time {num} Settings:</b>\n\n⏱️ Value: {val or 'Not Set'}", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>⏰ Time {num} Settings:</b>\n\n⏱️ Value: {val or 'Not Set'}", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^rm_time'))
async def remove_time(client, query):
    time_num = query.data.split("#")[0][-1]
    grp_id = query.data.split("#")[1]
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)

    if time_num == "1":
        key = "verify_time"
    elif time_num == "2":
        key = "third_verify_time"
    else:
        return await query.answer("Invalid Time Selection")

    await delete_group_setting(int(grp_id), key)
    await query.answer(f"ᴛɪᴍᴇ {time_num} ʀᴇᴍᴏᴠᴇᴅ!", show_alert=True)

    query.data = f'time_menu#{time_num}#{grp_id}'
    await time_menu_handler(client, query)

@Client.on_callback_query(filters.regex(r'^set_time'))
async def set_time(client, query):
    time_num = query.data.split("#")[0][-1]
    grp_id = query.data.split("#")[1]
    user_id = query.from_user.id if query.from_user else None
    silentx = await client.get_chat(int(grp_id))
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)

    settings = await get_settings(int(grp_id))
    if time_num == "1":
        key = "verify_time"
    elif time_num == "2":
        key = "third_verify_time"
    else:
        return await query.answer("Invalid Time Selection")

    current_time = settings.get(key, 'Not set')

    # Set query.data for back handling
    query.data = f'time_menu#{time_num}#{grp_id}'

    try:
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ {time_num} ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ:\n\n⏱️ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ: {current_time}</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ {time_num} ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ:\n\n⏱️ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ: {current_time}</b>")
    except MessageNotModified:
        pass

    m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ (ɪɴ sᴇᴄᴏɴᴅs) ᴏʀ ᴜꜱᴇ <code>/cancel</code> ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ.</b>")
    while True:
        time_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if time_msg.text == "/cancel":
            await m.delete()
            await time_menu_handler(client, query)
            return
        if time_msg.text.isdigit() and int(time_msg.text) > 0:
            break
        else:
            await query.message.reply("<b>ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ! ᴍᴜꜱᴛ ʙᴇ ᴀ ᴘᴏꜱɪᴛɪᴠᴇ ɴᴜᴍʙᴇʀ (ᴇxᴀᴍᴘʟᴇ: 60)</b>")
    await m.delete()
    await time_msg.delete()
    await save_group_settings(int(grp_id), key, int(time_msg.text))
    log_message = f"#New_Time_Set\n\n ᴛɪᴍᴇ ɴᴏ - {time_num}\nɢʀᴏᴜᴘ ʟɪɴᴋ - `{invite_link}`\n\nɢʀᴏᴜᴘ ɪᴅ : `{grp_id}`\nᴀᴅᴅᴇᴅ ʙʏ - `{user_id}`\nᴛɪᴍᴇ - {time_msg.text}"
    await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)

    btn = [
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'time_menu#{time_num}#{grp_id}')]
    ]
    try:
        await query.message.edit(f"<b>{time_num} ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ᴜᴘᴅᴀᴛᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\nᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ: {time_msg.text}</b>", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>{time_num} ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ ᴜᴘᴅᴀᴛᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\nᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ: {time_msg.text}</b>", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^changetutorial'))
async def change_tutorial(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
    btn = [
        [InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 1', callback_data=f'tutorial_menu#1#{grp_id}')],
        [InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 2', callback_data=f'tutorial_menu#2#{grp_id}')],
        [InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 3', callback_data=f'tutorial_menu#3#{grp_id}')],
        [InlineKeyboardButton('ᴛᴜᴛᴏʀɪᴀʟ 4', callback_data=f'tutorial_menu#4#{grp_id}')],
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'verification_setgs#{grp_id}')]
    ]
    try:
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴛᴜᴛᴏʀɪᴀʟ ᴛᴏ ᴍᴀɴᴀɢᴇ:</b>", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit("<b>ᴄʜᴏᴏꜱᴇ ᴛᴜᴛᴏʀɪᴀʟ ᴛᴏ ᴍᴀɴᴀɢᴇ:</b>", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^tutorial_menu'))
async def tutorial_menu_handler(client, query):
    _, num, grp_id = query.data.split("#")
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)

    settings = await get_settings(int(grp_id))
    suffix = "" if num == "1" else f"_{'2' if num == '2' else '3' if num == '3' else '4'}"
    val = settings.get(f'tutorial{suffix}')
    set_text = "ꜱᴇᴛ"

    btn = [
        [InlineKeyboardButton(set_text, callback_data=f'set_tutorial{num}#{grp_id}')],
        [InlineKeyboardButton('ʀᴇᴍᴏᴠᴇ', callback_data=f'rm_tutorial{num}#{grp_id}')],
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'changetutorial#{grp_id}')]
    ]
    try:
        await query.message.edit(f"<b>📹 Tutorial {num} Settings:</b>\n\n🔗 Value: {val or 'Not Set'}", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>📹 Tutorial {num} Settings:</b>\n\n🔗 Value: {val or 'Not Set'}", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^rm_tutorial'))
async def remove_tutorial(client, query):
    tutorial_num = query.data.split("#")[0][-1]
    grp_id = query.data.split("#")[1]
    user_id = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)

    suffix = "" if tutorial_num == "1" else f"_{'2' if tutorial_num == '2' else '3' if tutorial_num == '3' else '4'}"

    await delete_group_setting(int(grp_id), f'tutorial{suffix}')
    await query.answer(f"ᴛᴜᴛᴏʀɪᴀʟ {tutorial_num} ʀᴇᴍᴏᴠᴇᴅ!", show_alert=True)

    query.data = f'tutorial_menu#{tutorial_num}#{grp_id}'
    await tutorial_menu_handler(client, query)

@Client.on_callback_query(filters.regex(r'^set_tutorial'))
async def set_tutorial(client, query):
    tutorial_num = query.data.split("#")[0][-1]
    grp_id = query.data.split("#")[1]
    user_id = query.from_user.id if query.from_user else None
    silentx = await client.get_chat(int(grp_id))
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
    settings = await get_settings(int(grp_id))
    suffix = "" if tutorial_num == "1" else f"_{'2' if tutorial_num == '2' else '3' if tutorial_num == '3' else '4'}"
    tutorial_url = settings.get(f'tutorial{suffix}', "ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇᴛ ᴀɴᴅ ᴠᴀʟᴜᴇ ꜱᴏ ᴜꜱɪɴɢ ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ")

    # Set query.data for back handling
    query.data = f'tutorial_menu#{tutorial_num}#{grp_id}'

    try:
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ᴛᴜᴛᴏʀɪᴀʟ {tutorial_num}:\n\n🔗 ᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ: {tutorial_url}.</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>📌 ᴅᴇᴛᴀɪʟꜱ ᴏꜰ ᴛᴜᴛᴏʀɪᴀʟ {tutorial_num}:\n\n🔗 ᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ: {tutorial_url}.</b>")
    except MessageNotModified:
        pass

    m = await query.message.reply("<b>ꜱᴇɴᴅ ɴᴇᴡ ᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ ᴏʀ ᴜꜱᴇ <code>/cancel</code> ᴛᴏ ᴄᴀɴᴄᴇʟ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ</b>")
    tutorial_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
    if tutorial_msg.text == "/cancel":
        await m.delete()
        await tutorial_menu_handler(client, query)
        return
    await m.delete()
    await tutorial_msg.delete()
    await save_group_settings(int(grp_id), f'tutorial{suffix}', tutorial_msg.text)
    log_message = f"#New_Tutorial_Set\n\n ᴛᴜᴛᴏʀɪᴀʟ ɴᴏ - {tutorial_num}\nɢʀᴏᴜᴘ ʟɪɴᴋ - `{invite_link}`\n\nɢʀᴏᴜᴘ ɪᴅ : `{grp_id}`\nᴀᴅᴅᴇᴅ ʙʏ - `{user_id}`\nᴛᴜᴛᴏʀɪᴀʟ - {tutorial_msg.text}"
    await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)

    btn = [
        [InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'tutorial_menu#{tutorial_num}#{grp_id}')]
    ]
    try:
        await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴜᴛᴏʀɪᴀʟ {tutorial_num} ᴠᴀʟᴜᴇꜱ ✅\n\nᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ: {tutorial_msg.text}</b>", reply_markup=InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴜᴛᴏʀɪᴀʟ {tutorial_num} ᴠᴀʟᴜᴇꜱ ✅\n\nᴛᴜᴛᴏʀɪᴀʟ ᴜʀʟ: {tutorial_msg.text}</b>", reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r'^setgs'))
async def set_group_settings(client, query):
    ident, set_type, status, grp_id = query.data.split("#")
    userid = query.from_user.id if query.from_user else None
    if not await is_check_admin(client, int(grp_id), userid):
        await query.answer(script.ALRT_TXT, show_alert=True)
        return

    if set_type == "auto_del_time":
        new_time = 60 if status == "30" else 120 if status == "60" else AUTO_DELETE_TIME if status == "120" else 30
        await save_group_settings(int(grp_id), "auto_del_time", new_time)
        await query.answer(f"Auto Delete Time set to {new_time}s ✓")
    else:
        if status == "True":
            await save_group_settings(int(grp_id), set_type, False)
            await query.answer("ᴏꜰꜰ ✗")
        else:
            await save_group_settings(int(grp_id), set_type, True)
            await query.answer("ᴏɴ ✓")

    btn = await group_setting_buttons(int(grp_id))
    try:
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r"^delete_group_check"))
async def delete_group_check_callback(client, query):
    try:
        _, grp_id = query.data.split("#")
        userid = query.from_user.id
        if not await is_check_admin(client, int(grp_id), userid):
            await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
            return

        buttons = [
            [
                InlineKeyboardButton('ʏᴇs, ᴅᴇʟᴇᴛᴇ', callback_data=f'delete_group#{grp_id}'),
                InlineKeyboardButton('ᴄᴀɴᴄᴇʟ', callback_data=f'open_settings#{grp_id}')
            ]
        ]
        await query.message.edit_text(
            "<b>⚠️ ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜɪs ɢʀᴏᴜᴘ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ? ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ᴀʟsᴏ ʟᴇᴀᴠᴇ ᴛʜᴇ ɢʀᴏᴜᴘ.</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        LOGGER.error(f"Callback Error - {e}")
        await query.answer("An error occurred!", show_alert=True)

@Client.on_callback_query(filters.regex(r"^delete_group#"))
async def delete_group_callback(client, query):
    try:
        try:
            _, grp_id = query.data.split("#")
        except ValueError:
            return
        userid = query.from_user.id
        if not await is_check_admin(client, int(grp_id), userid):
            await query.answer("<b>ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.</b>", show_alert=True)
            return
        await db.delete_chat(int(grp_id))
        await query.answer("ɢʀᴏᴜᴘ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅", show_alert=True)
        await query.message.edit_text("<b>✅ ɢʀᴏᴜᴘ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ ᴀɴᴅ ʙᴏᴛ ʟᴇꜰᴛ ᴛʜᴇ ɢʀᴏᴜᴘ.</b>")
        try:
            await client.leave_chat(int(grp_id))
        except Exception as e:
            LOGGER.error(f"Error leaving group {grp_id}: {e}")
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        LOGGER.error(f"Callback Error - {e}")
        await query.answer("An error occurred!", show_alert=True)

@Client.on_callback_query(filters.regex(r'^booster_setgs'))
async def booster_settings(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id
    if not await is_check_admin(client, int(grp_id), user_id):
        return await query.answer("ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ✅.", show_alert=True)

    settings = await get_settings(int(grp_id))
    booster_status = settings.get('member_booster', False)
    booster_count = settings.get('booster_count', 10)
    bypassed_list = settings.get('booster_bypass', [])
    status_text = "ᴏɴ" if booster_status else "ᴏꜰꜰ"

    btn = [[
        InlineKeyboardButton('ᴛᴜʀɴ ᴏꜰꜰ' if booster_status else 'ᴛᴜʀɴ ᴏɴ', callback_data=f'setgs#member_booster#{booster_status}#{grp_id}'),
    ],[
        InlineKeyboardButton(f'🎯 ꜱᴇᴛ ᴛᴀʀɢᴇᴛ ({booster_count})', callback_data=f'set_booster_count#{grp_id}'),
    ],[
        InlineKeyboardButton('🔄 ʀᴇꜱᴇᴛ ꜱᴇᴛᴛɪɴɢꜱ', callback_data=f'booster_reset_menu#{grp_id}')
    ],[
        InlineKeyboardButton('🛡️ ᴍᴀɴᴀɢᴇ ʙʏᴘᴀꜱꜱ', callback_data=f'booster_bypass#{grp_id}')
    ],[
        InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'grp_pm#{grp_id}')
    ]]

    text = (
        "<b>🚀 ᴍᴇᴍʙᴇʀ ʙᴏᴏꜱᴛᴇʀ ꜱᴇᴛᴛɪɴɢꜱ\n\n"
        "ꜰᴏʀᴄᴇ ɴᴇᴡ ᴜꜱᴇʀꜱ ᴛᴏ ᴀᴅᴅ ᴍᴇᴍʙᴇʀꜱ ʙᴇꜰᴏʀᴇ ᴛʜᴇʏ ᴄᴀɴ ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇꜱ.\n\n"
        f"✅ ꜱᴛᴀᴛᴜꜱ : {status_text}\n"
        f"🎯 ʀᴇǫᴜɪʀᴇᴅ ᴀᴅᴅꜱ : {booster_count}\n"
        f"🛡️ ʙʏᴘᴀꜱꜱᴇᴅ ᴜꜱᴇʀꜱ : {len(bypassed_list)}</b>"
    )
    try:
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass


@Client.on_callback_query(filters.regex(r'^set_booster_count'))
async def set_booster_count(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id
    m = await query.message.reply("<b>ꜱᴇɴᴅ ᴛʜᴇ ɴᴜᴍʙᴇʀ ᴏꜰ ᴍᴇᴍʙᴇʀꜱ ᴀ ᴜꜱᴇʀ ᴍᴜꜱᴛ ᴀᴅᴅ (e.g., 10) ᴏʀ <code>/cancel</code></b>")
    
    count_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
    if count_msg.text == "/cancel":
        await m.delete()
        return await booster_settings(client, query)
        
    if count_msg.text.isdigit():
        await save_group_settings(int(grp_id), 'booster_count', int(count_msg.text))
        await query.answer(f"Target set to {count_msg.text}!", show_alert=True)
    else:
        await query.message.reply("<b>❌ Invalid number!</b>")
        
    await m.delete()
    await count_msg.delete()
    await booster_settings(client, query)

@Client.on_callback_query(filters.regex(r'^booster_bypass'))
async def booster_bypass(client, query):
    _, grp_id = query.data.split("#")
    user_id = query.from_user.id
    
    settings = await get_settings(int(grp_id))
    bypassed = settings.get('booster_bypass', [])
    bypassed_text = ", ".join([f"<code>{u}</code>" for u in bypassed]) if bypassed else "None"

    m = await query.message.reply(f"<b>Current bypassed IDs: {bypassed_text}\n\nSend a User ID to Add/Remove them from bypass, or <code>/cancel</code></b>")
    
    msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
    if msg.text != "/cancel" and msg.text.lstrip('-').isdigit():
        target_id = int(msg.text)
        if target_id in bypassed:
            bypassed.remove(target_id)
            await query.answer("User removed from bypass!", show_alert=True)
        else:
            bypassed.append(target_id)
            await query.answer("User added to bypass!", show_alert=True)
        await save_group_settings(int(grp_id), 'booster_bypass', bypassed)
        
    await m.delete()
    await msg.delete()
    await booster_settings(client, query)

@Client.on_callback_query(filters.regex(r'^check_adds_'), group=-1)
async def check_adds_callback(client, query):
    # Extract the user ID of the person who TRIGGERED the warning
    target_user_id = query.data.replace("check_adds_", "")
    
    # Security: Only let the actual restricted user click their own button
    if str(query.from_user.id) != target_user_id:
        await query.answer("This button is only for that user!", show_alert=True)
        raise StopPropagation # Stops pm_filter from showing the MSG_ALRT
        
    chat_id = query.message.chat.id
    settings = await get_settings(chat_id)
    required_count = settings.get("booster_count", 1)
    current_count = await db.get_booster_count(chat_id, query.from_user.id)
    
    # Send the pop-up alert!
    if current_count >= required_count:
        await query.answer(
            f"📊 Your Stats:\n\nUsers added: {current_count}\nRequired: {required_count}\n\n✅ Target reached! Access granted to message.", 
            show_alert=True
        )
    else:
        remaining = required_count - current_count
        await query.answer(
            f"📊 Your Stats:\n\nUsers added: {current_count}\nRequired: {required_count}\n\n⚠️ Please add {remaining} more to unlock messaging.", 
            show_alert=True
        )
    raise StopPropagation

@Client.on_callback_query(filters.regex(r'^booster_reset_menu'), group=-1)
async def booster_reset_menu(client, query):
    _, grp_id = query.data.split("#")
    settings = await get_settings(int(grp_id))
    auto_reset_cycle = settings.get('booster_auto_reset', 'OFF').upper()

    btn = [[
        InlineKeyboardButton('🗑️ ᴍᴀɴᴜᴀʟ ʀᴇꜱᴇᴛ (ᴡɪᴘᴇ ɴᴏᴡ)', callback_data=f'booster_manual_reset#{grp_id}')
    ],[
        InlineKeyboardButton(f'⏳ ᴀᴜᴛᴏ-ʀᴇꜱᴇᴛ: {auto_reset_cycle}', callback_data=f'booster_cycle_reset#{grp_id}#{auto_reset_cycle}')
    ],[
        InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data=f'booster_setgs#{grp_id}')
    ]]

    text = "<b>🔄 ꜱᴄᴏʀᴇ ʀᴇꜱᴇᴛ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ\n\nWɪᴘᴇ ᴀʟʟ ᴜsᴇʀ sᴄᴏʀᴇs ᴍᴀɴᴜᴀʟʟʏ ʀɪɢʜᴛ ɴᴏᴡ, ᴏʀ sᴇᴛ ᴀɴ ᴀᴜᴛᴏᴍᴀᴛɪᴄ sᴄʜᴇᴅᴜʟᴇ sᴏ ᴜsᴇʀs ᴍᴜsᴛ ᴀᴅᴅ ɴᴇᴡ ᴍᴇᴍʙᴇʀs ᴇᴠᴇʀʏ ᴡᴇᴇᴋ ᴏʀ ᴍᴏɴᴛʜ!</b>"
    
    try:
        await query.message.edit(text, reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass
    raise StopPropagation
    
@Client.on_callback_query(filters.regex(r'^booster_manual_reset'), group=-1)
async def booster_manual_reset(client, query):
    import time as time_module
    _, grp_id = query.data.split("#")
    
    # 1. Wipe the MongoDB collection for this group
    await db.reset_all_booster_scores(int(grp_id))
    
    # 2. Update the timestamp so Auto-Reset doesn't trigger prematurely
    await save_group_settings(int(grp_id), 'booster_last_reset', time_module.time())
    
    await query.answer("✅ ALL USER SCORES HAVE BEEN WIPED TO ZERO!", show_alert=True)
    raise StopPropagation

@Client.on_callback_query(filters.regex(r'^booster_cycle_reset'), group=-1)
async def booster_cycle_reset(client, query):
    import time as time_module
    _, grp_id, current_state = query.data.split("#")
    
    # Cycle logic: OFF -> WEEKLY -> MONTHLY -> OFF
    
    if current_state == "OFF":
        next_state = "2 MINS"
    elif current_state == "2 MINS":
        next_state = "WEEKLY"
    elif current_state == "WEEKLY":
        next_state = "MONTHLY"
    else:
        next_state = "OFF"
        
    await save_group_settings(int(grp_id), 'booster_auto_reset', next_state)
    await save_group_settings(int(grp_id), 'booster_last_reset', time_module.time())
    
    # Refresh menu to show the new state
    query.data = f"booster_reset_menu#{grp_id}"
    await booster_reset_menu(client, query)

@Client.on_callback_query(filters.regex(r'^set_join_hider#'))
async def toggle_join_hider(client, query):
    # 1. Extract the group ID from the button click
    ident, grp_id = query.data.split("#")
    userid = query.from_user.id if query.from_user else None
    
    # 2. Strict Admin Verification
    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        await query.answer("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴏ ᴛʜɪꜱ !", show_alert=True)
        return

    # 3. Toggle the Setting in the Database
    settings = await get_settings(int(grp_id))
    current_status = settings.get("join_hider", False)
    new_status = not current_status
    
    # Save the new status (Adjust 'save_group_settings' to match your bot's exact db save function if it differs)
    await save_group_settings(int(grp_id), "join_hider", new_status) 
    
    # Alert the admin
    status_text = "ON" if new_status else "OFF"
    await query.answer(f"🧹 Built-in Join Hider is now {status_text}!", show_alert=True)

    # 4. Refresh the Settings Menu UI dynamically
    title = query.message.chat.title
    btn = await group_setting_buttons(int(grp_id))
    text = await get_main_settings_text(int(grp_id), title)
    
    try:
        await query.message.edit_text(
            text=text,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await query.message.edit_text(
            text=text,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass    