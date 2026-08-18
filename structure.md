# Bot Structure & Advanced Flow Documentation

## 1. End-to-End Search & Verification Flow
This section explains how the bot handles a movie search from start to finish, and how the link shortener verification logic intercepts the flow.

### Flow Breakdown
1. **User Request (`pm_filter.py`)**: 
   - A user types a query (e.g., "Drishyam").
   - The bot intercepts it via `pm_text` (for PM) or `give_filter` (for Groups).
   - It triggers `auto_filter()`.
2. **Database Search & Spelling Check**:
   - `get_search_results()` is called to fetch matches from the MongoDB file database.
   - If no results are found, `ai_spell_check()` runs, providing "Did you mean...?" suggestions.
3. **Displaying Results**:
   - The bot replies with an inline keyboard where each matching movie is a button (e.g., Callback Data: `file#<file_id>`).
4. **Processing the Request (`commands.py`)**:
   - When the user clicks the file, it generates a `/start` payload URL like `/start file_{grp_id}_{file_id}`.
5. **Verification Gateway Check**:
   - Before delivering the file, the bot checks `get_settings(grp_id)` (PM mode uses `grp_id = 0`).
   - It checks:
     - `db.is_user_verified(user_id)`: Has the user completed the 1st verification today?
     - `db.use_second_shortener(user_id, time)`: Has enough time passed to require the 2nd verification?
     - `db.use_third_shortener(user_id, time)`: Has enough time passed to require the 3rd verification?
   - If any verification is required, it generates a `notcopy` / `sendall` verification payload and sends the user through the link shortener.
   - If no verification is needed, the bot delivers the file.

### The Timezone Verification Bug (Resolved)
**Past Bug Profile**: MongoDB stores `datetime` objects in naive UTC. When the bot read them, Python `astimezone()` assumed the naive time was in local time (IST on Windows). This skewed the calculation by +5.5 hours, making the bot immediately think the verification gap (e.g., 3 hours) had already passed, causing an infinite verification loop.
**Resolution**: We patched `database/users_chats_db.py` to strictly enforce `pytz.utc.localize(pastDate)` before casting to IST, ensuring cross-platform stability.

---

## 2. Advanced Customization & Admin Settings
The bot possesses an advanced `/settings` menu designed for Group Admins (or Bot Owners configuring PM settings). 

### A. Verification Customization
The verification system (Link Shortener) is highly advanced and features a **3-Tier Verification System**. It allows admins to force users to verify multiple times a day through different shorteners.

*   **Turn ON/OFF**: Global switch to enable or disable verification for the specific group.
*   **3 Distinct Shortener Configurations**:
    *   **Shortener 1**: API Key and Website Domain for the first click.
    *   **Shortener 2**: API Key and Website Domain for the second verification.
    *   **Shortener 3**: API Key and Website Domain for the third verification.
*   **Customizable Time Gaps**:
    *   `verify_time` (Gap 1): How much time must pass (e.g., 3 hours) before the bot asks for the 2nd verification.
    *   `third_verify_time` (Gap 2): How much time must pass before the 3rd verification is triggered.
*   **Custom Tutorials**: Admins can map 3 different YouTube "How to Download" links for each of the 3 shortener stages so users aren't confused if the UI of the shortener changes.

### B. Force Subscription (FSUB)
*   **Custom FSUB**: Instead of a global forced channel, admins can set **group-specific** channels that users must join.
*   **Multiple Channels**: The bot supports forcing users to join *multiple* channels before getting files.

### C. Member Booster (Growth Feature)
*   **Enforce Referrals**: Admins can force new users to add a specific number of their friends (e.g., 5 members) to the group before the bot will process their movie requests.
*   **Bypass & Auto-Reset**: Admins can whitelist specific users and configure the bot to auto-reset booster scores on a weekly or monthly basis.

### D. General Group UI/UX Features
*   **Result Page (Button vs Text)**: Deliver search results cleanly as inline buttons or as standard text links.
*   **File Secure**: Prevents users from forwarding the movie files outside the group.
*   **Auto-Delete**: Automatically wipes the delivered movie file from the chat after a few minutes (e.g., 5 mins) to prevent Telegram copyright strikes.
*   **Join Hider**: Automatically deletes "User joined the group" service messages to prevent chat spam.
*   **IMDb Posters**: Automatically scrapes IMDb to attach a rich synopsis and poster to the search results.
*   **Log Channel**: Admins can attach a custom log channel where every search query made by users in their group is privately recorded.
