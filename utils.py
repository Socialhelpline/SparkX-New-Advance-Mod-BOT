from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid, MessageNotModified
from info import  *
from imdbkit import IMDBKit 
import asyncio
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from typing import Union, Optional, Dict, Any
from Script import script
import pytz
import random 
import re
import os
import time as time_module
from datetime import datetime, date, time, timedelta
import string
from typing import List
from database.users_chats_db import db
from bs4 import BeautifulSoup
import aiohttp
from shortzy import Shortzy
import http.client
import json
from logging_helper import LOGGER
from rapidfuzz import fuzz

BTN_URL_REGEX = re.compile(
    r"(\[([^\[]+?)\]\((buttonurl|buttonalert):(?:/{0,2})(.+?)(:same)?\))"
)

BAD_WORDS_REGEX = re.compile('|'.join(map(re.escape, sorted(BAD_WORDS, key=len, reverse=True))), flags=re.IGNORECASE) if BAD_WORDS else None

imdb = IMDBKit() 
BANNED = {}
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)


class temp(object):   
    BANNED_USERS = []
    BANNED_CHATS = []
    SETTINGS = {}
    SETTINGS_EXPIRY = {}
    ME = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    B_USERS_CANCEL = False
    B_GROUPS_CANCEL = False 
    MELCOW = {}
    U_NAME = None
    B_NAME = None
    B_LINK = None
    GETALL = {}
    SHORT = {}
    IMDB_CAP = {}
    VERIFICATIONS = {}

    
async def is_check_admin(bot, chat_id, user_id):
    if chat_id == 0:
        return user_id in ADMINS or str(user_id) in ADMINS
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except Exception:
        return False
    
async def users_broadcast(user_id, message, is_pin):
    try:
        m=await message.copy(chat_id=user_id)
        if is_pin:
            await m.pin(both_sides=True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(getattr(e, 'value', getattr(e, 'x', 5)))
        return await users_broadcast(user_id, message, is_pin)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        LOGGER.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        LOGGER.info(f"{user_id} -Blocked the bot.")
        await db.delete_user(user_id)
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        LOGGER.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def groups_broadcast(chat_id, message, is_pin):
    try:
        m = await message.copy(chat_id=chat_id)
        if is_pin:
            try:
                await m.pin()
            except Exception:
                pass
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(getattr(e, 'value', getattr(e, 'x', 5)))
        return await groups_broadcast(chat_id, message, is_pin)
    except Exception as e:
        await db.delete_chat(chat_id)
        return "Error"

async def junk_group(chat_id, message):
    try:
        kk = await message.copy(chat_id=chat_id)
        await kk.delete(True)
        return True, "Succes", 'mm'
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await junk_group(chat_id, message)
    except Exception as e:
        await db.delete_chat(int(chat_id))       
        LOGGER.info(f"{chat_id} - PeerIdInvalid")
        return False, "deleted", f'{e}\n\n'
    

async def clear_junk(user_id, message):
    try:
        key = await message.copy(chat_id=user_id)
        await key.delete(True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await clear_junk(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        LOGGER.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        LOGGER.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        LOGGER.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"
    
async def delete_after_delay(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

async def remove_buttons_after_delay(message, delay):
    """Wait for delay and then remove the inline keyboard, keeping the text."""
    await asyncio.sleep(delay)
    try:
        await message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

async def get_status(bot_id):
    try:
        return await db.movie_update_status(bot_id) or False  
    except Exception as e:
        LOGGER.error(f"Error in get_movie_update_status: {e}")
        return False  

def listx_to_str(k):
    if k is None or k == "":
        return "N/A"
    
    # Handle non-iterable types first
    if not hasattr(k, '__iter__') or isinstance(k, (str, int, float)):
        return str(k)
    
    result = []
    for elem in k:
        if elem and str(elem).strip():
            result.append(str(elem).strip())
    
    if MAX_LIST_ELM and len(result) > MAX_LIST_ELM:
        result = result[:int(MAX_LIST_ELM)]
    
    return ', '.join(result) if result else "N/A"

async def fetch_tmdb_search(query):
    if not TMDB_API_KEY:
        LOGGER.error("[TMDB ERROR] TMDB_API_KEY is missing!")
        return []
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("results", [])
                else:
                    LOGGER.error(f"[TMDB ERROR] search_multi returned status {resp.status}")
    except Exception as e:
        LOGGER.error(f"[TMDB ERROR] Exception in fetch_tmdb_search: {e}")
    return []

async def fetch_tmdb_details(media_type, tmdb_id):
    if not TMDB_API_KEY:
        return None
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=external_ids,credits"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    LOGGER.error(f"[TMDB ERROR] get_details returned status {resp.status}")
    except Exception as e:
        LOGGER.error(f"[TMDB ERROR] Exception in fetch_tmdb_details: {e}")
    return None

async def fetch_omdb_search(query):
    if not OMDB_API_KEY:
        LOGGER.error("[OMDB ERROR] OMDB_API_KEY is missing!")
        return []
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("Search", [])
                else:
                    LOGGER.error(f"[OMDB ERROR] search returned status {resp.status}")
    except Exception as e:
        LOGGER.error(f"[OMDB ERROR] Exception in fetch_omdb_search: {e}")
    return []

async def fetch_omdb_details(imdb_id):
    if not OMDB_API_KEY:
        return None
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}&plot=full"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("Response") == "True":
                        return data
                else:
                    LOGGER.error(f"[OMDB ERROR] get_details returned status {resp.status}")
    except Exception as e:
        LOGGER.error(f"[OMDB ERROR] Exception in fetch_omdb_details: {e}")
    return None

async def get_poster(query, bulk=False, id=False, file=None):
    LOGGER.info(f"[API CHECK] get_poster called. Active API_PROVIDER: {API_PROVIDER.upper()}")
    if API_PROVIDER.upper() == "TMDB":
        if not id:
            query = (query.strip()).lower()
            title = query
            year_val = None
            
            year_list = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
            if year_list:
                year_val = year_list[0]
                title = (query.replace(year_val, "")).strip()
            elif file is not None:
                year_list = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
                if year_list:
                    year_val = year_list[0]
            
            results = await fetch_tmdb_search(title)
            if not results:
                words = title.split()
                if len(words) >= 2:
                    seen_ids = set()
                    for i in range(len(words)):
                        partial = " ".join(words[:i] + words[i+1:]).strip()
                        if partial:
                            partial_res = await fetch_tmdb_search(partial)
                            for r in (partial_res or []):
                                r_id = r.get("id")
                                if r_id not in seen_ids:
                                    results.append(r)
                                    seen_ids.add(r_id)
                    if not results and len(words) >= 3:
                        for i in range(1, len(words)):
                            pair_q = f"{words[0]} {words[i]}"
                            pair_res = await fetch_tmdb_search(pair_q)
                            for r in (pair_res or []):
                                r_id = r.get("id")
                                if r_id not in seen_ids:
                                    results.append(r)
                                    seen_ids.add(r_id)
                if not results and words:
                    longest_word = max(words, key=len)
                    if len(longest_word) >= 3:
                        results = await fetch_tmdb_search(longest_word) or []
            if not results:
                LOGGER.info(f"[TMDB DEBUG] No suggestions found for '{title}'.")
                return None
            
            # TMDB returns a list of dicts. Filter them.
            movie_list = results[:MAX_LIST_ELM]
            
            if year_val:
                filtered = []
                for m in movie_list:
                    release = m.get('release_date') or m.get('first_air_date') or ""
                    if release.startswith(str(year_val)):
                        filtered.append(m)
                if not filtered:
                    filtered = movie_list
            else:
                filtered = movie_list
                
            if bulk:
                # Return all suggestions returned by TMDB for user confirmation
                class DummyMovie:
                    def __init__(self, t, i):
                        self.title = t
                        self.imdb_id = i
                
                bulk_res = []
                for m in movie_list[:MAX_LIST_ELM]:
                    m_title = m.get('title') or m.get('name')
                    if m_title:
                        media_t = m.get('media_type', 'movie')
                        bulk_res.append(DummyMovie(m_title, f"tmdb_{media_t}_{m.get('id')}"))
                return bulk_res
                
            kind_filter = ['movie', 'tv']
            filtered_kind = [m for m in filtered if m.get('media_type') in kind_filter]
            if not filtered_kind:
                filtered_kind = filtered

            # Rank items by fuzzy match to the user's title
            filtered_kind.sort(
                key=lambda m: fuzz.token_sort_ratio(title, m.get('title') or m.get('name') or ''),
                reverse=True
            )
                
            if not filtered_kind:
                return None
                
            movie_brief = filtered_kind[0]
            tmdb_id_str = f"tmdb_{movie_brief.get('media_type', 'movie')}_{movie_brief.get('id')}"
        else:
            tmdb_id_str = query
            
        # Extract media type and id from our custom format
        if tmdb_id_str.startswith("tmdb_"):
            parts = tmdb_id_str.split("_")
            media_type = parts[1]
            tmdb_id = parts[2]
        else:
            # Fallback if it's an imdb id (maybe user passed tt12345)
            # Actually, TMDB has a /find endpoint, but let's assume standard flow
            media_type = "movie"
            tmdb_id = tmdb_id_str
            
        movie = await fetch_tmdb_details(media_type, tmdb_id)
        if not movie:
            LOGGER.info(f"[TMDB DEBUG] get_details returned None for ID '{tmdb_id}'")
            return None
            
        date = movie.get('release_date') or movie.get('first_air_date') or "N/A"
        year = date[:4] if date != "N/A" else "N/A"
        plot = movie.get('overview', "")
        if len(plot) > 800:
            plot = plot[:800] + "..."
            
        # Get IMDB ID from external_ids
        ext_ids = movie.get('external_ids', {})
        imdb_id = ext_ids.get('imdb_id', f"tmdb{tmdb_id}")
        if imdb_id and not imdb_id.startswith("tt"):
            imdb_id = f"tt{imdb_id}"
            
        # Get Cast and Crew
        credits = movie.get('credits', {})
        cast_list = [c.get('name') for c in credits.get('cast', [])[:5]]
        crew = credits.get('crew', [])
        directors = [c.get('name') for c in crew if c.get('job') == 'Director']
        writers = [c.get('name') for c in crew if c.get('job') in ['Screenplay', 'Writer']]
        
        genres = [g.get('name') for g in movie.get('genres', [])]
        
        poster_path = movie.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        
        return {
            'title': movie.get('title') or movie.get('name'),
            'votes': movie.get('vote_count', "N/A"),
            "aka": "N/A",
            "seasons": movie.get('number_of_seasons', "N/A"),
            "box_office": movie.get('revenue', "N/A"),
            'localized_title': movie.get('title') or movie.get('name'),
            'kind': "movie" if media_type == "movie" else "tv series",
            "imdb_id": imdb_id,
            "cast": listx_to_str(cast_list),
            "runtime": listx_to_str([movie.get('runtime', "N/A")]),
            "countries": listx_to_str([c.get('name') for c in movie.get('production_countries', [])]),
            "certificates": "N/A",
            "languages": listx_to_str(movie.get('spoken_languages', [])),
            "director": listx_to_str(directors),
            "writer": listx_to_str(writers),
            "producer": "N/A",
            "composer": "N/A",
            "cinematographer": "N/A",
            "music_team": "N/A",
            "distributors": "N/A",        
            'release_date': date,
            'year': year,
            'genres': listx_to_str(genres),
            'poster': poster_url,
            'plot': plot,
            'rating': str(movie.get('vote_average', "N/A")),
            "url": f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
        }

    # === OMDB FALLBACK ===
    elif API_PROVIDER.upper() == "OMDB":
        if not id:
            query = (query.strip()).lower()
            title = query
            year_val = None
            
            year_list = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
            if year_list:
                year_val = year_list[0]
                title = (query.replace(year_val, "")).strip()
            elif file is not None:
                year_list = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
                if year_list:
                    year_val = year_list[0]
            
            results = await fetch_omdb_search(title)
            if not results:
                words = title.split()
                if len(words) >= 2:
                    seen_ids = set()
                    for i in range(len(words)):
                        partial = " ".join(words[:i] + words[i+1:]).strip()
                        if partial:
                            partial_res = await fetch_omdb_search(partial)
                            for r in (partial_res or []):
                                r_id = r.get("imdbID")
                                if r_id not in seen_ids:
                                    results.append(r)
                                    seen_ids.add(r_id)
                    if not results and len(words) >= 3:
                        for i in range(1, len(words)):
                            pair_q = f"{words[0]} {words[i]}"
                            pair_res = await fetch_omdb_search(pair_q)
                            for r in (pair_res or []):
                                r_id = r.get("imdbID")
                                if r_id not in seen_ids:
                                    results.append(r)
                                    seen_ids.add(r_id)
                if not results and words:
                    longest_word = max(words, key=len)
                    if len(longest_word) >= 3:
                        results = await fetch_omdb_search(longest_word) or []
            if not results:
                LOGGER.info(f"[OMDB DEBUG] No suggestions found for '{title}'.")
                return None
            
            movie_list = results[:MAX_LIST_ELM]
            
            if year_val:
                filtered = [m for m in movie_list if str(m.get("Year", "")).startswith(str(year_val))]
                if not filtered:
                    filtered = movie_list
            else:
                filtered = movie_list
                
            kind_filter = ['movie', 'series']
            filtered_kind = [m for m in filtered if m.get("Type", "movie") in kind_filter]
            if not filtered_kind:
                filtered_kind = filtered

            # Rank items by fuzzy match to the user's title
            filtered_kind.sort(
                key=lambda m: fuzz.token_sort_ratio(title, m.get('Title') or ''),
                reverse=True
            )
                
            if bulk:
                class DummyMovie:
                    def __init__(self, t, i):
                        self.title = t
                        self.imdb_id = i
                
                bulk_res = []
                for m in filtered_kind[:MAX_LIST_ELM]:
                    bulk_res.append(DummyMovie(m.get("Title"), m.get("imdbID")))
                return bulk_res
                
            if not filtered_kind:
                return None
                
            movie_brief = filtered_kind[0]
            imdb_id_str = movie_brief.get("imdbID")
        else:
            imdb_id_str = query
            
        movie = await fetch_omdb_details(imdb_id_str)
        if not movie:
            LOGGER.info(f"[OMDB DEBUG] get_details returned None for ID '{imdb_id_str}'")
            return None
            
        date = movie.get("Released", "N/A")
        year = movie.get("Year", "N/A")
        plot = movie.get("Plot", "")
        if len(plot) > 800:
            plot = plot[:800] + "..."
            
        imdb_id = movie.get("imdbID", imdb_id_str)
        if imdb_id and not imdb_id.startswith("tt"):
            imdb_id = f"tt{imdb_id}"
            
        poster_url = movie.get("Poster")
        if poster_url == "N/A":
            poster_url = None
            
        return {
            'title': movie.get("Title", "N/A"),
            'votes': movie.get("imdbVotes", "N/A"),
            "aka": "N/A",
            "seasons": movie.get("totalSeasons", "N/A"),
            "box_office": movie.get("BoxOffice", "N/A"),
            'localized_title': movie.get("Title", "N/A"),
            'kind': "tv series" if movie.get("Type") == "series" else "movie",
            "imdb_id": imdb_id,
            "cast": movie.get("Actors", "N/A"),
            "runtime": movie.get("Runtime", "N/A"),
            "countries": movie.get("Country", "N/A"),
            "certificates": movie.get("Rated", "N/A"),
            "languages": movie.get("Language", "N/A"),
            "director": movie.get("Director", "N/A"),
            "writer": movie.get("Writer", "N/A"),
            "producer": "N/A",
            "composer": "N/A",
            "cinematographer": "N/A",
            "music_team": "N/A",
            "distributors": "N/A",        
            'release_date': date,
            'year': year,
            'genres': movie.get("Genre", "N/A"),
            'poster': poster_url,
            'plot': plot,
            'rating': movie.get("imdbRating", "N/A"),
            "url": f"https://www.imdb.com/title/{imdb_id}"
        }

    # === IMDB FALLBACK ===
    if not id:
        query = (query.strip()).lower()
        title = query
        year_val = None
        
        year_list = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
        if year_list:
            year_val = year_list[0]
            title = (query.replace(year_val, "")).strip()
        elif file is not None:
            year_list = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
            if year_list:
                year_val = year_list[0]
        
        try:
            search_result = await asyncio.to_thread(imdb.search_movie, title.lower())
        except Exception as e:
            LOGGER.error(f"[IMDb API ERROR] search_movie failed for '{title.lower()}': {e}")
            return None

        if not search_result or not search_result.titles:
            LOGGER.info(f"[IMDb DEBUG] No suggestions found for '{title.lower()}'. Likely gibberish or not in IMDb database.")
            return None
        
        movie_list = search_result.titles[:MAX_LIST_ELM]
        
        if year_val:
            filtered = [m for m in movie_list if m.year and str(m.year) == str(year_val)]
            if not filtered:
                filtered = movie_list
        else:
            filtered = movie_list
            
        kind_filter = ['movie', 'tv series', 'tvSeries', 'tvMiniSeries', 'tvMovie']
        filtered_kind = [m for m in filtered if m.kind and m.kind in kind_filter]
        
        if not filtered_kind:
            filtered_kind = filtered
        
        if bulk:
            return filtered_kind[:MAX_LIST_ELM]
            
        if not filtered_kind:
            return None
            
        movie_brief = filtered_kind[0]
        movieid_str = movie_brief.imdb_id 
    else:
        movieid_str = query

    try:
        movie = await asyncio.to_thread(imdb.get_movie, movieid_str)
    except Exception as e:
        LOGGER.error(f"[IMDb API ERROR] get_movie failed for ID '{movieid_str}': {e}")
        return None

    if not movie:
        LOGGER.info(f"[IMDb DEBUG] get_movie returned None for ID '{movieid_str}'")
        return None

    if movie.release_date:
        date = movie.release_date
    elif movie.year:
        date = str(movie.year)
    else:
        date = "N/A"
        
    plot = movie.plot[0] if isinstance(movie.plot, list) else movie.plot or ""
    if len(plot) > 800:
        plot = plot[:800] + "..."
    imdb_id = movie.imdb_id
    
    if not imdb_id.startswith("tt"):
        imdb_id = f"tt{imdb_id}"
        
    return {
        'title': movie.title,
        'votes': movie.votes,
        "aka": listx_to_str(movie.title_akas),
        "seasons": (
            len(movie.info_series.display_seasons)
            if getattr(movie, "info_series", None)
            and getattr(movie.info_series, "display_seasons", None)
            else "N/A"
        ),
        "box_office": movie.worldwide_gross,
        'localized_title': movie.title_localized,
        'kind': movie.kind,
        "imdb_id": imdb_id,
        "cast": listx_to_str(movie.stars),
        "runtime": listx_to_str(movie.duration),
        "countries": listx_to_str(movie.countries),
        "certificates": listx_to_str(movie.certificates),
        "languages": listx_to_str(movie.languages),
        "director": listx_to_str(movie.directors),
        "writer": listx_to_str([p.name for p in movie.writers]),
        "producer": listx_to_str([p.name for p in movie.producers]),
        "composer": listx_to_str([p.name for p in movie.composers]),
        "cinematographer": listx_to_str([p.name for p in movie.cinematographers]),
        "music_team": listx_to_str([p.name for p in movie.music_team]),
        "distributors": listx_to_str([c.name for c in movie.distributors]),        
        'release_date': date,
        'year': movie.year,
        'genres': listx_to_str(movie.genres),
        'poster': movie.cover_url,
        'plot': plot,
        'rating': str(movie.rating),
        "url": movie.url or f"https://www.imdb.com/title/{imdb_id}"
    }

async def fetch_tmdb_data(title: str, year: str = None) -> Optional[Dict[str, Any]]:
    base_url = "https://image.silentxbotz.tech/api/v2/poster"
    params = {"title": title.strip()}
    if year:
        params["year"] = year
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=25)) as response:
                if response.status != 200:
                    return None
                data = await response.json()

                raw_director = data.get("director")
                if isinstance(raw_director, list):
                    director = ", ".join([str(x) for x in raw_director if x])
                elif isinstance(raw_director, str):
                    director = raw_director
                else:
                    director = None

                director = director if director else ""    
                
                return {
                    "id": data.get("id"),
                    "title": data.get("title", title),
                    "original_title": data.get("original_title", ""),
                    "original_language": data.get("original_language", "en"),
                    "kind": data.get("type", "Movie").upper(),
                    "director": director,
                    "release_date": data.get("release_date", ""),
                    "vote_average": f"{data['vote_average']:.1f}" if data.get("vote_average") else "N/A",
                    "vote_count": f"{data['vote_count']:,}" if data.get("vote_count") else "0",
                    "genres": data.get("genres", []),
                    "imdb_id": data.get("imdb_id", ""),
                    "imdb_url": f"https://www.imdb.com/title/{data.get('imdb_id')}/" if data.get("imdb_id") else "",
                    "overview": data.get("overview", ""),
                    "poster_url": data.get("poster_url", ""),
                    "backdrop_url": data.get("backdrop_url", ""),
                    "backdrops": data.get("backdrops", {}),
                    "posters": data.get("posters", {}),
                    "cast": data.get("cast", [])[:5],
                    "videos": data.get("videos", []),
                }
                
    except Exception as e:
        LOGGER.error(f"API Fetch Error: {str(e)}")
        return None

async def get_best_visual(tmdb_data: Dict) -> Optional[str]:
    backdrops = tmdb_data.get("backdrops", {})
    by_language = backdrops.get("by_language", {})    
    original_lang = tmdb_data.get("original_language")
    if original_lang and by_language.get(original_lang):
        return by_language[original_lang][0]["url"]    
    indian_langs = [
        "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu", "pa", "or", "as", 
        "ur", "ne"
    ]
    for lang in indian_langs:
        if by_language.get(lang):
            return by_language[lang][0]["url"]    
    if by_language.get("en"):
        return by_language["en"][0]["url"]
    if by_language.get("unknown"):
        return by_language["unknown"][0]["url"]    
    if backdrops.get("all") and backdrops["all"]:
        return backdrops["all"][0]["url"]
    return None
    
async def get_shortlink(link, grp_id, is_second_shortener=False, is_third_shortener=False, is_fourth_shortener=False):
    settings = await get_settings(grp_id)
    if is_fourth_shortener:             
        api, site = settings['api_four'], settings['shortner_four']
    elif is_third_shortener:             
        api, site = settings['api_three'], settings['shortner_three']
    else:
        if is_second_shortener:
            api, site = settings['api_two'], settings['shortner_two']
        else:
            api, site = settings['api'], settings['shortner']
    shortzy = Shortzy(api, site)
    try:
        link = await shortzy.convert(link)
    except Exception as e:
        link = await shortzy.get_quick_link(link)
    return link

async def get_settings(group_id):
    settings = temp.SETTINGS.get(group_id)
    expiry = temp.SETTINGS_EXPIRY.get(group_id, 0)
    current_time = time_module.time()

    # Cache settings for 5 minutes (300 seconds)
    if settings and current_time < expiry:
        return settings

    settings = await db.get_settings(group_id)
    temp.SETTINGS[group_id] = settings
    temp.SETTINGS_EXPIRY[group_id] = current_time + 300
    return settings
    
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})
    temp.SETTINGS[group_id] = current
    temp.SETTINGS_EXPIRY[group_id] = time_module.time() + 300
    await db.update_settings(group_id, current)

async def delete_group_setting(group_id, key):
    await db.delete_setting(group_id, key)
    if group_id in temp.SETTINGS:
        temp.SETTINGS.pop(group_id, None)
    
def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def silent_size(size):
    size = float(size)
    size_gb = size / (1024 ** 3)
    return "%.2f GB" % size_gb
                        
def extract_tag(file_name: str) -> str:
    file_name = file_name.lower()
    file_name = re.sub(r'[\._\-]+', ' ', file_name)
    patterns = [
        r'\b(?:s|season)\s*0*(\d{1,2})\s*(?:e|episode)\s*0*(\d{1,2})\b',
        r'\b(\d{1,2})\s*(?:x|episode)\s*0*(\d{1,2})\b',
        r'\bs0*(\d{1,2})e0*(\d{1,2})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, file_name)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            return f"S{season:02d}E{episode:02d} •"
    season_match = re.search(r'\b(?:s|season)\s*0*(\d{1,2})\b', file_name)
    if season_match:
        season = int(season_match.group(1))
        return f"S{season:02d} •"
    quality_match = re.search(r'\b(2160p|1080p|720p|480p|360p|4k)\b', file_name)
    if quality_match:
        return f"{quality_match.group(1)} •"
    return ""

def extract_request_content(message_text):
    match = re.search(r"<u>(.*?)</u>", message_text)
    if match:
        return match.group(1).strip()
    match = re.search(r"📝 ʀᴇǫᴜᴇꜱᴛ ?: ?(.*?)(?:\n|$)", message_text)
    if match:
        return match.group(1).strip()
    return message_text.strip()

def clean_filename(filename):
    if not filename:
        return ""
    parts = filename.rsplit('.', 1)
    if len(parts) == 2 and len(parts[1]) <= 5:
        name, ext = parts
    else:
        name, ext = filename, ""
    original_name = name
    name = re.sub(r'[_\-\.\+]', ' ', name)  
    if BAD_WORDS_REGEX:
        name = BAD_WORDS_REGEX.sub('', name)
    name = re.sub(r'@\w+\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'#\w+\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'www\.\S+\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'https?://\S+\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\[\s*', ' ', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\]', ' ', name, flags=re.IGNORECASE)
    name = re.sub(r'\(\s*', ' ', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\)', ' ', name, flags=re.IGNORECASE)
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if not name or not any(c.isalnum() for c in name):
        words = re.findall(r'[A-Za-z0-9]+', original_name)
        name = ' '.join(words) if words else "untitled"
    name = ' '.join(w.capitalize() for w in name.split())  
    final_result = f"{name}{ext}" if ext else name   
    return final_result

async def replace_words(string):
    ignorewords = sorted(IGNORE_WORDS, key=len, reverse=True)
    pattern = r'\b(?:{})\b'.format('|'.join(map(re.escape, ignorewords)))
    formatted = re.sub(pattern, '', string, flags=re.IGNORECASE)
    return formatted.replace("-", " ")
    
def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]  

def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj

def extract_user(message: Message) -> Union[int, str]:
    user_id = None
    user_first_name = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name

    elif len(message.command) > 1:
        if (
            len(message.entities) > 1 and
            message.entities[1].type == enums.MessageEntityType.TEXT_MENTION
        ):
           
            required_entity = message.entities[1]
            user_id = required_entity.user.id
            user_first_name = required_entity.user.first_name
        else:
            user_id = message.command[1]
            # don't want to make a request -_-
            user_first_name = user_id
        try:
            user_id = int(user_id)
        except ValueError:
            pass
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name
    return (user_id, user_first_name)

def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    elif MAX_LIST_ELM:
        k = k[:int(MAX_LIST_ELM)]
        return ' '.join(f'{elem}, ' for elem in k)
    else:
        return ' '.join(f'{elem}, ' for elem in k)

def clean_search_query(query):
    pattern = r'\(s0\?(\d+)\|season\\s\*(\d+)\)\(\?:e\\d\+\)\?'
    def replacer(match):
        num = match.group(1) or match.group(2)
        return f"Season {num}"
    cleaned = re.sub(pattern, replacer, query, flags=re.IGNORECASE)
    pattern2 = r's0\?(\d+)\(\?:e\\d\+\)\?'
    cleaned = re.sub(pattern2, lambda m: f"Season {m.group(1)}", cleaned, flags=re.IGNORECASE)
    return cleaned

def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "🤖 Bot :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        time += "Recently"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        time += "Within the last week"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        time += "Within the last month"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        time += "A long time ago :("
    elif from_user.status == enums.UserStatus.ONLINE:
        time += "Currently Online"
    elif from_user.status == enums.UserStatus.OFFLINE:
        time += from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
    return time


def split_quotes(text: str) -> List:
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)
    counter = 1
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
            break
        counter += 1
    else:
        return text.split(None, 1)
    key = remove_escapes(text[1:counter].strip())
    rest = text[counter + 1:].strip()
    if not key:
        key = text[0] + text[0]
    return list(filter(None, [key, rest]))

def gfilterparser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except Exception:
        return note_data, buttons, None

def parser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except Exception:
        return note_data, buttons, None

def remove_escapes(text: str) -> str:
    res = ""
    is_escaped = False
    for counter in range(len(text)):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
    return res

async def log_error(client, error_message):
    try:
        await client.send_message(
            chat_id=LOG_CHANNEL, 
            text=f"<b>⚠️ Error Log:</b>\n<code>{error_message}</code>"
        )
    except Exception as e:
        LOGGER.error(f"Failed to log error: {e}")


def get_time(seconds):
    periods = [(' ᴅᴀʏs', 86400), (' ʜᴏᴜʀ', 3600), (' ᴍɪɴᴜᴛᴇ', 60), (' sᴇᴄᴏɴᴅ', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result
    
def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def get_readable_time(seconds):
    periods = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f'{int(period_value)}{period_name}')
    return ' '.join(result)  


async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:].lstrip()
        if value:
            value = int(value)
        return value, unit
    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0
    
async def get_cap(settings, remaining_seconds, files, query, total_results, search, offset):
    search = clean_search_query(search)
    if settings["imdb"]:
        IMDB_CAP = temp.IMDB_CAP.get(query.from_user.id)
        if IMDB_CAP:
            cap = IMDB_CAP
            for file_num, file in enumerate(files, start=offset+1):
                cap += f"\n\n<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}</a></b>"
        else:
            imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
            if imdb:
                TEMPLATE = script.IMDB_TEMPLATE_TXT
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
                for file_num, file in enumerate(files, start=offset+1):
                    cap += f"\n\n<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}</a></b>"
            else:
                cap =f"<b>📂 ʜᴇʀᴇ ɪ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜʀ sᴇᴀʀᴄʜ <code>{search}</code></b>\n\n"
                for file_num, file in enumerate(files, start=offset+1):
                    cap += f"<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}\n\n</a></b>"
    else:
        cap =f"<b>📂 ʜᴇʀᴇ ɪ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜʀ sᴇᴀʀᴄʜ <code>{search}</code></b>\n\n"
        for file_num, file in enumerate(files, start=offset+1):
            cap += f"<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}\n\n</a></b>"
    return cap
