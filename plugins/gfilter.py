import asyncio
from pyrogram import Client, filters, StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import ADMINS
from utils import gfilterparser
from database.gfilters_mdb import gfilter_db

GLOBAL_FILTERS_CACHE = {}
IS_GFILTER_ENABLED = True

# State machine for step-by-step listening
GFILTER_ADD_STATE = {}

async def load_gfilters():
    global GLOBAL_FILTERS_CACHE, IS_GFILTER_ENABLED
    all_filters = await gfilter_db.get_all_gfilters()
    GLOBAL_FILTERS_CACHE.clear()
    for f in all_filters:
        GLOBAL_FILTERS_CACHE[f['keyword']] = f['text']
    IS_GFILTER_ENABLED = await gfilter_db.is_gfilter_enabled()

# Load filters will be called from bot.py on startup


# --- INTERACTIVE DASHBOARD ---

@Client.on_message(filters.command("filter_menu") & filters.user(ADMINS))
async def filter_menu_command(client, message):
    await send_filter_dashboard(message)

async def send_filter_dashboard(message_or_query):
    status = "✅ ENABLED" if IS_GFILTER_ENABLED else "❌ DISABLED"
    text = f"<b>⚙️ Restricted Filter Management</b>\n\nCurrent Status: <b>{status}</b>\nTotal Filters: <b>{len(GLOBAL_FILTERS_CACHE)}</b>"
    
    buttons = [
        [InlineKeyboardButton("➕ Add Filter", callback_data="gfm_add")],
        [InlineKeyboardButton("📋 List Filters", callback_data="gfm_list"),
         InlineKeyboardButton("🗑️ Delete Filter", callback_data="gfm_delete_menu")],
        [InlineKeyboardButton("⚙️ Toggle ON/OFF", callback_data="gfm_toggle")]
    ]
    
    if hasattr(message_or_query, "data"):
        await message_or_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message_or_query.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^gfm_") & filters.user(ADMINS))
async def gfm_callbacks(client, query):
    action = query.data.split("_")[1]
    
    if action == "menu":
        await send_filter_dashboard(query)
        
    elif action == "add":
        GFILTER_ADD_STATE[query.from_user.id] = {"step": 1}
        await query.message.edit_text(
            "<b>➕ Add New Filter</b>\n\nStep 1: Send the <b>keyword</b> or <b>movie name</b> you want to restrict.\n\n<i>(Type /cancel to abort)</i>"
        )
        
    elif action == "list":
        if not GLOBAL_FILTERS_CACHE:
            await query.answer("No active filters.", show_alert=True)
            return
        text = "<b>🌍 Global Restricted Filters:</b>\n\n"
        for keyword in GLOBAL_FILTERS_CACHE.keys():
            text += f"- <code>{keyword}</code>\n"
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="gfm_back")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        
    elif action == "delete":
        # Check if it's the delete menu or a specific deletion
        parts = query.data.split("_")
        if len(parts) == 3 and parts[2] == "menu":
            if not GLOBAL_FILTERS_CACHE:
                await query.answer("No active filters to delete.", show_alert=True)
                return
            
            buttons = []
            for keyword in GLOBAL_FILTERS_CACHE.keys():
                buttons.append([InlineKeyboardButton(f"🗑️ {keyword}", callback_data=f"gfm_delete_{keyword}")])
            buttons.append([InlineKeyboardButton("💥 Delete ALL", callback_data="gfm_delete_all")])
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="gfm_back")])
            
            await query.message.edit_text("<b>🗑️ Select a filter to delete:</b>", reply_markup=InlineKeyboardMarkup(buttons))
            
        elif len(parts) >= 3 and parts[2] == "all":
            await gfilter_db.delete_all_gfilters()
            GLOBAL_FILTERS_CACHE.clear()
            await query.answer("All filters deleted!", show_alert=True)
            await send_filter_dashboard(query)
            
        elif len(parts) >= 3:
            keyword = query.data.split("_", 2)[2]
            if keyword in GLOBAL_FILTERS_CACHE:
                await gfilter_db.delete_gfilter(keyword)
                del GLOBAL_FILTERS_CACHE[keyword]
                await query.answer(f"Deleted filter: {keyword}", show_alert=True)
            await send_filter_dashboard(query)

    elif action == "toggle":
        global IS_GFILTER_ENABLED
        IS_GFILTER_ENABLED = not IS_GFILTER_ENABLED
        await gfilter_db.toggle_gfilter(IS_GFILTER_ENABLED)
        await send_filter_dashboard(query)
        
    elif action == "back":
        await send_filter_dashboard(query)


# --- STATE MACHINE LISTENER (Group=-1 to run before pm_filter) ---

@Client.on_message(filters.user(ADMINS) & filters.text, group=-1)
async def gfilter_state_machine(client, message):
    user_id = message.from_user.id
    if user_id not in GFILTER_ADD_STATE:
        return # Not in state machine, let pm_filter handle it
        
    if message.text.lower() == "/cancel":
        del GFILTER_ADD_STATE[user_id]
        await message.reply_text("❌ Filter creation cancelled.")
        raise StopPropagation
        
    state = GFILTER_ADD_STATE[user_id]
    
    if state["step"] == 1:
        state["keyword"] = message.text.lower().strip()
        state["step"] = 2
        await message.reply_text(
            f"<b>Keyword:</b> <code>{state['keyword']}</code>\n\n"
            "Step 2: Send the <b>Reply Text</b>.\n"
            "<i>(You can use basic markdown. We will add buttons in the next step.)</i>\n\n"
            "<i>(Type /cancel to abort)</i>"
        )
        raise StopPropagation
        
    elif state["step"] == 2:
        state["text"] = message.text.markdown
        state["step"] = 3
        await message.reply_text(
            f"<b>Keyword:</b> <code>{state['keyword']}</code>\n"
            f"<b>Text:</b> {state['text']}\n\n"
            "Step 3: Send the <b>Buttons</b> formatting.\n"
            "Example: <code>[Check Updates](buttonurl:https://t.me/yourchannel)</code>\n\n"
            "<i>(If you don't want buttons, just send <code>none</code> or type /cancel to abort)</i>"
        )
        raise StopPropagation
        
    elif state["step"] == 3:
        button_text = message.text.strip()
        if button_text.lower() == "none":
            final_text = state["text"]
        else:
            final_text = state["text"] + "\n" + message.text.markdown.strip()
            
        keyword = state["keyword"]
        await gfilter_db.add_gfilter(keyword, final_text)
        GLOBAL_FILTERS_CACHE[keyword] = final_text
        
        del GFILTER_ADD_STATE[user_id]
        await message.reply_text(f"✅ <b>Successfully added filter for:</b> <code>{keyword}</code>\n\nYou can manage this in /filter_menu")
        raise StopPropagation


# --- FALLBACK / FAST COMMANDS ---

@Client.on_message(filters.command("gfilter") & filters.user(ADMINS))
async def add_gfilter_fast(client, message):
    if len(message.command) == 1:
        # Trigger interactive setup if no arguments
        GFILTER_ADD_STATE[message.from_user.id] = {"step": 1}
        await message.reply_text(
            "<b>➕ Add New Filter</b>\n\nStep 1: Send the <b>keyword</b> or <b>movie name</b> you want to restrict.\n\n<i>(Type /cancel to abort)</i>"
        )
        return

    keyword = message.command[1].lower().strip()
    if message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text.markdown
    elif len(message.command) >= 3:
        text = message.text.markdown.split(None, 2)[2]
    else:
        await message.reply_text("Please provide the reply text or reply to a text message.")
        return

    await gfilter_db.add_gfilter(keyword, text)
    GLOBAL_FILTERS_CACHE[keyword] = text
    await message.reply_text(f"✅ <b>Global Restricted Filter added for:</b> <code>{keyword}</code>")


@Client.on_message(filters.command("gfilters") & filters.user(ADMINS))
async def list_gfilters_fast(client, message):
    await send_filter_dashboard(message)

@Client.on_message(filters.command("delg") & filters.user(ADMINS))
async def delete_gfilter_fast(client, message):
    if len(message.command) < 2:
        await message.reply_text("<b>Usage:</b>\n/delg [keyword]")
        return
    keyword = message.command[1].lower().strip()
    if keyword not in GLOBAL_FILTERS_CACHE:
        await message.reply_text(f"❌ <b>Filter not found for:</b> <code>{keyword}</code>")
        return
    await gfilter_db.delete_gfilter(keyword)
    del GLOBAL_FILTERS_CACHE[keyword]
    await message.reply_text(f"✅ <b>Global Restricted Filter deleted for:</b> <code>{keyword}</code>")

@Client.on_message(filters.command("delallg") & filters.user(ADMINS))
async def delete_all_gfilters_fast(client, message):
    await gfilter_db.delete_all_gfilters()
    GLOBAL_FILTERS_CACHE.clear()
    await message.reply_text("✅ <b>All Global Restricted Filters have been deleted.</b>")

@Client.on_message(filters.command(["gfilterson", "gfiltersoff"]) & filters.user(ADMINS))
async def toggle_gfilters_fast(client, message):
    global IS_GFILTER_ENABLED
    IS_GFILTER_ENABLED = message.command[0] == "gfilterson"
    await gfilter_db.toggle_gfilter(IS_GFILTER_ENABLED)
    status = "ENABLED" if IS_GFILTER_ENABLED else "DISABLED"
    await message.reply_text(f"Status changed to: <b>{status}</b>")


# --- ALERT CALLBACK HANDLER ---

@Client.on_callback_query(filters.regex(r"^gfilteralert:"))
async def gfilter_alert_cb(client, query):
    _, index_str, keyword = query.data.split(":", 2)
    index = int(index_str)
    
    if keyword not in GLOBAL_FILTERS_CACHE:
        await query.answer("This alert is no longer available.", show_alert=True)
        return
        
    raw_text = GLOBAL_FILTERS_CACHE[keyword]
    _, _, alerts = gfilterparser(raw_text, keyword)
    
    if alerts and len(alerts) > index:
        await query.answer(alerts[index], show_alert=True)
    else:
        await query.answer("Alert not found.", show_alert=True)
