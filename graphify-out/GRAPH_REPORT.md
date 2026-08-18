# Graph Report - .  (2026-08-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 505 nodes · 1077 edges · 25 communities (22 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- info.py
- pm_filter.py
- commands.py
- settings.py
- env
- Database
- utils.py
- ia_filterdb.py
- keywords
- p_ttishow.py
- ByteStreamer
- file_store.py
- Premium.py
- extra.py
- license.py
- UserTracker
- human_size

## God Nodes (most connected - your core abstractions)
1. `Database` - 64 edges
2. `is_check_admin()` - 37 edges
3. `get_settings()` - 31 edges
4. `save_group_settings()` - 22 edges
5. `auto_filter()` - 20 edges
6. `env` - 14 edges
7. `start()` - 14 edges
8. `keywords` - 12 edges
9. `temp` - 12 edges
10. `ByteStreamer` - 11 edges

## Surprising Connections (you probably didn't know these)
- `SilentXBot` --uses--> `temp`  [INFERRED]
  Lucia/Bot/__init__.py → utils.py
- `media_streamer()` --calls--> `ByteStreamer`  [EXTRACTED]
  plugins/route.py → Lucia/util/custom_dl.py
- `temp` --uses--> `script`  [INFERRED]
  utils.py → Script.py
- `get_search_results()` --calls--> `get_settings()`  [EXTRACTED]
  database/ia_filterdb.py → utils.py
- `get_search_results()` --calls--> `save_group_settings()`  [EXTRACTED]
  database/ia_filterdb.py → utils.py

## Import Cycles
- None detected.

## Communities (25 total, 3 thin omitted)

### Community 0 - "info.py"
Cohesion: 0.06
Nodes (37): silentx_plugins_handler(), SilentXBotz_start(), ChatJoinRequest, get, initialize_clients(), Client, Iterate through a chat sequentially. This convenience method does the same as…, SilentXBot (+29 more)

### Community 1 - "pm_filter.py"
Cohesion: 0.11
Nodes (44): get_bad_files(), get_file_details(), get_regex_pattern(), get_search_results(), get_file_ids(), get_hash(), get_media_file_size(), get_media_from_message() (+36 more)

### Community 2 - "commands.py"
Cohesion: 0.08
Nodes (39): Database, admin_commands(), all_settings(), back_to_start_cb(), commands_menu_cb(), connect_group(), delete(), delete_all_index() (+31 more)

### Community 3 - "settings.py"
Cohesion: 0.17
Nodes (45): booster_message_interceptor(), booster_bypass(), booster_cycle_reset(), booster_manual_reset(), booster_reset_menu(), booster_settings(), caption_settings(), change_caption() (+37 more)

### Community 4 - "env"
Cohesion: 0.05
Nodes (41): description, required, description, required, description, required, description, required (+33 more)

### Community 6 - "utils.py"
Cohesion: 0.09
Nodes (24): broadcast_cancel(), broadcast_group(), broadcast_users(), junk_clear_group(), on_callback_query, on_message, remove_junkuser__db(), on_message (+16 more)

### Community 7 - "ia_filterdb.py"
Cohesion: 0.12
Nodes (29): check_db_size(), encode_file_id(), encode_file_ref(), save_file(), silentxbotz_clean_title(), siletxbotz_fetch_media(), siletxbotz_get_movies(), siletxbotz_get_series() (+21 more)

### Community 8 - "keywords"
Cohesion: 0.08
Nodes (23): addons, buildpacks, description, formation, worker, keywords, name, repository (+15 more)

### Community 9 - "p_ttishow.py"
Cohesion: 0.14
Nodes (23): ChatMemberUpdated, Media, Media2, Meta, Document, on_chat_member_updated, ban_a_user(), booster_score_tracker() (+15 more)

### Community 10 - "ByteStreamer"
Cohesion: 0.14
Nodes (14): InputDocumentFileLocation, InputPeerPhotoFileLocation, InputPhotoFileLocation, ByteStreamer, Client, FileId, Returns the file location for the media file., A custom class that holds the cache of a specific client and class functions.… (+6 more)

### Community 11 - "file_store.py"
Cohesion: 0.24
Nodes (16): Exception, batch_callbacks(), batch_generator(), finalize_batch(), gen_hash(), get_admin_buttons(), inline_revoke_cb(), list_active_links() (+8 more)

### Community 12 - "Premium.py"
Cohesion: 0.19
Nodes (16): on_pre_checkout_query, cancel_premium(), get_premium(), give_premium_cmd_handler(), myplan(), plan(), pre_checkout_handler(), premium_button() (+8 more)

### Community 13 - "extra.py"
Cohesion: 0.27
Nodes (11): calculate_latency(), check_alive(), format_time(), get_size(), get_system_info(), ping(), on_message, Convert seconds to H:M:S format. (+3 more)

### Community 14 - "license.py"
Cohesion: 0.44
Nodes (8): all_codes_cmd(), clear_codes_cmd(), generate_code(), generate_code_cmd(), hash_code(), parse_duration(), on_message, redeem_code_cmd()

## Knowledge Gaps
- **47 isolated node(s):** `name`, `description`, `stack`, `telegram`, `auto-filter` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Database` connect `Database` to `info.py`, `.get_notcopy_user`, `.get_bot_setting`, `.update_bot_setting`, `.get_user`, `.add_chat`, `.add_user`, `.remove_premium_access`?**
  _High betweenness centrality (0.200) - this node is a cross-community bridge._
- **Why does `ByteStreamer` connect `ByteStreamer` to `info.py`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **What connects `name`, `description`, `stack` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `info.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06229508196721312 - nodes in this community are weakly interconnected._
- **Should `pm_filter.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10628019323671498 - nodes in this community are weakly interconnected._
- **Should `commands.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08019323671497584 - nodes in this community are weakly interconnected._
- **Should `env` be split into smaller, more focused modules?**
  _Cohesion score 0.04878048780487805 - nodes in this community are weakly interconnected._