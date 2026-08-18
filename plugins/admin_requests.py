from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.users_chats_db import db
from info import ADMINS
import math

ITEMS_PER_PAGE = 10

@Client.on_message(filters.command('reqs') & filters.user(ADMINS))
async def show_requests(client, message):
    total_requests = await db.get_total_pending_requests_count()
    unique_users = await db.get_unique_request_users_count()
    
    if total_requests == 0:
        return await message.reply_text("✅ **No pending movie requests!**")
        
    requests = await db.get_all_pending_requests()
    
    text, reply_markup = generate_reqs_page(requests, total_requests, unique_users, 1)
    await message.reply_text(text, reply_markup=reply_markup, disable_web_page_preview=True)

@Client.on_callback_query(filters.regex(r"^reqs_page_(\d+)$") & filters.user(ADMINS))
async def reqs_page_handler(client, query: CallbackQuery):
    page = int(query.matches[0].group(1))
    
    total_requests = await db.get_total_pending_requests_count()
    unique_users = await db.get_unique_request_users_count()
    requests = await db.get_all_pending_requests()
    
    if total_requests == 0:
        await query.message.edit_text("✅ **No pending movie requests!**", reply_markup=None)
        return await query.answer("All requests cleared.")
        
    text, reply_markup = generate_reqs_page(requests, total_requests, unique_users, page)
    await query.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await query.answer()

@Client.on_callback_query(filters.regex(r"^reqs_del_(.*)_(\d+)$") & filters.user(ADMINS))
async def reqs_del_handler(client, query: CallbackQuery):
    req_id = query.matches[0].group(1)
    page = int(query.matches[0].group(2))
    
    # Delete from DB
    await db.delete_request(req_id)
    
    # Refresh data
    total_requests = await db.get_total_pending_requests_count()
    unique_users = await db.get_unique_request_users_count()
    requests = await db.get_all_pending_requests()
    
    if total_requests == 0:
        await query.message.edit_text("✅ **No pending movie requests!**", reply_markup=None)
        return await query.answer("Request deleted! No more requests left.", show_alert=True)
        
    # Recalculate page if we deleted the last item on current page
    max_pages = math.ceil(total_requests / ITEMS_PER_PAGE)
    if page > max_pages:
        page = max_pages
        
    text, reply_markup = generate_reqs_page(requests, total_requests, unique_users, page)
    await query.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await query.answer("✅ Request deleted successfully!", show_alert=False)

def generate_reqs_page(requests, total_requests, unique_users, page):
    max_pages = math.ceil(total_requests / ITEMS_PER_PAGE)
    
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    
    current_reqs = requests[start_idx:end_idx]
    
    text = f"📊 **Pending Movie Requests**\n\n"
    text += f"👥 **Total Unique Users:** `{unique_users}`\n"
    text += f"📝 **Total Requests:** `{total_requests}`\n"
    text += f"📄 **Page:** `{page}/{max_pages}`\n\n"
    
    buttons = []
    del_row = []
    
    for i, req in enumerate(current_reqs, start=1):
        # Format the date nicely if possible
        req_date = req.get('requested_at')
        if req_date:
            try:
                date_str = req_date.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = "Unknown"
        else:
            date_str = "Unknown"
            
        keyword = req.get('keyword', 'Unknown').title()
        user_id = req.get('user_id', 'Unknown')
        
        text += f"**{i}.** `{keyword}`\n"
        text += f"👤 User: `{user_id}` | 🕒 {date_str}\n\n"
        
        # Add a delete button for this request (numbered 1-10)
        req_id = str(req.get('_id'))
        del_row.append(InlineKeyboardButton(f"❌ {i}", callback_data=f"reqs_del_{req_id}_{page}"))
        
        # Group delete buttons into rows of 5
        if len(del_row) == 5:
            buttons.append(del_row)
            del_row = []
            
    if del_row:
        buttons.append(del_row)
        
    # Navigation buttons
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"reqs_page_{page-1}"))
    if page < max_pages:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"reqs_page_{page+1}"))
        
    if nav_row:
        buttons.append(nav_row)
        
    return text, InlineKeyboardMarkup(buttons)
