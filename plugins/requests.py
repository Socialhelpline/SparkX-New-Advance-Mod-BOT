import asyncio
import random
import base64
from database.users_chats_db import db
from utils import clean_filename
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import LOG_CHANNEL

async def check_and_fulfill_requests(bot, file_name, file_id, pending_reqs=None):
    """
    Checks if an uploaded file satisfies any pending requests.
    If yes, sends a single 'Download Now' DM. When clicked, it expands to show all files.
    """
    if not file_name:
        return
        
    normalized_name = clean_filename(file_name).lower()
    
    if pending_reqs is None:
        pending_reqs = await db.get_all_pending_requests()
    
    if not pending_reqs:
        return
    
    fulfilled_count = 0
    fulfilled_users = []
    
    for req in list(pending_reqs):
        keyword = req['keyword']
        
        if all(word in normalized_name for word in keyword.split()):
            # Mark fulfilled instantly so subsequent files in batch don't trigger duplicate DMs
            await db.mark_request_fulfilled(req['_id'])
            pending_reqs.remove(req) 
            
            # Truncate keyword to safely fit in 64-byte callback_data limit
            kw = keyword
            if len(kw) > 30:
                kw = kw[:30].rsplit(' ', 1)[0]
                
            encoded_kw = base64.urlsafe_b64encode(kw.encode('utf-8')).decode().rstrip('=')
            
            btn = [[InlineKeyboardButton("📥 Download Now", callback_data=f"reqdl#{req['chat_id']}#{encoded_kw}")]]
            
            try:
                await bot.send_message(
                    chat_id=req['user_id'],
                    text=f"🎉 **Good news!**\n\nThe movie you requested (`{keyword}`) is now available!\n\nClick below to get it.",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                fulfilled_count += 1
                fulfilled_users.append(str(req['user_id']))
            except Exception as e:
                import logging
                logging.error(f"Fulfillment DM error for {keyword}: {e}")
                
    if fulfilled_count > 0:
        try:
            await bot.send_message(
                chat_id=LOG_CHANNEL,
                text=f"✅ **Auto-Fulfillment Log**\n\nThe file `{file_name}` automatically fulfilled requests for {fulfilled_count} users.\nIDs: {', '.join(fulfilled_users)}",
                disable_notification=True
            )
        except Exception:
            pass
