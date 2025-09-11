import asyncio
import json
import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UsernameInvalidError, UsernameNotOccupiedError
from telethon.tl.types import MessageEntityHashtag, MessageEntityUrl, MessageEntityMention

# ---------------------------
# CONFIG - edit as needed
# ---------------------------
ACCOUNTS = [
    # {"session": "anon1", "api_id": 28887666, "api_hash": "1e01869b2b510bfecb4462d08b529b72"},
    # {"session": "anon2", "api_id": 24972105, "api_hash": "c57ebdb04dbb2c6983f3e3ddd7b8aedd"},
    # {"session": "anon3", "api_id": 20549861, "api_hash": "90146ca2ac1a20152804462baf976e85"},
    {"session": "anon4", "api_id": 16850912, "api_hash": "a6aefe94cd56f0c66c9fc406ad36aba9"},
    # {"session": "anon5", "api_id": 22893596, "api_hash": "099e03188484d2041f7168abd7db8c8f"},
]
LARAVEL_API = "https://api-searchkid.zakari.site/api/messages/import"
IMPORT_TOKEN = "loveyoutenthousand"

# File names
SUSPENDED_FILE = "suspended.json"         # { "anon1": 169xyz, ... } unix ts suspended until
FAILED_FILE = "failed_channels.json"      # list of failed channels to retry later
LAST_ID_TEMPLATE = "last_id_{}.json"      # per-account last id file
CHANNELS_TEMPLATE = "{}_channels.json"    # per-account channels file, e.g. anon2_channels.json

# Behavior
BATCH_SIZE = 100
REQUEST_TIMEOUT = 30
MAX_ATTEMPTS = 3   # per-channel transient retry attempts (we requeue only in-memory)

# ---------------------------
# Stats (accumulated for run)
# ---------------------------
stats = {"public": {"channels": 0, "messages": 0, "created": 0, "updated": 0}}

# ---------------------------
# JSON helpers
# ---------------------------
def load_json(path: str, default: Any):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        # If file is corrupted, return default (don't crash)
        pass
    return default


def save_json(path: str, data: Any):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


# ---------------------------
# Suspension management (persisted between runs)
# ---------------------------
def load_suspended() -> Dict[str, float]:
    return load_json(SUSPENDED_FILE, {})


def save_suspended(data: Dict[str, float]):
    save_json(SUSPENDED_FILE, data)


# ---------------------------
# Per-account last-id helpers
# ---------------------------
def load_last_ids_for(session_name: str) -> Dict[str, int]:
    path = LAST_ID_TEMPLATE.format(session_name)
    return load_json(path, {})


def save_last_ids_for(session_name: str, data: Dict[str, int]):
    path = LAST_ID_TEMPLATE.format(session_name)
    save_json(path, data)


# ---------------------------
# Failed channels
# ---------------------------
def save_failed_channels(failed: List[Dict[str, Any]]):
    if failed:
        save_json(FAILED_FILE, failed)
    else:
        if os.path.exists(FAILED_FILE):
            os.remove(FAILED_FILE)


# ---------------------------
# Utility helpers
# ---------------------------
def now_ts() -> float:
    return time.time()


def iso_from_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def get_replies_count(msg) -> int:
    try:
        r = getattr(msg, "replies", None)
        if r is None:
            return 0
        if isinstance(r, int):
            return r
        if hasattr(r, "replies"):
            return int(r.replies or 0)
    except Exception:
        pass
    return 0


# ---------------------------
# Load channels for a given account session
# Expected filename: "<session>_channels.json"
# ---------------------------
def load_account_channels(session_name: str) -> List[Dict[str, Any]]:
    path = CHANNELS_TEMPLATE.format(session_name)
    return load_json(path, [])


# ---------------------------
# Core: fetch messages for a single channel using a given TelegramClient
# Returns a report dict with status and counts
# ---------------------------
async def fetch_channel_messages(
    client: TelegramClient,
    session_name: str,
    channel: Dict[str, Any],
    last_ids: Dict[str, int],
) -> Dict[str, Any]:
    username = channel.get("username")
    is_adults = bool(channel.get("is_adults", False))
    report = {"status": "unknown", "fetched": 0, "created": 0, "updated": 0}

    if not username:
        report.update({"status": "not_found", "reason": "no_username"})
        return report

    last_id = int(last_ids.get(username, 0) or 0)
    total_fetched = 0
    total_created = 0
    total_updated = 0

    try:
        entity = await client.get_entity(username)

        # loop to page through older/newer messages until none left
        while True:
            # min_id returns messages with id > min_id (newer than last_id)
            msgs = [m async for m in client.iter_messages(entity, limit=BATCH_SIZE, min_id=last_id)]
            if not msgs:
                break

            # ensure order oldest -> newest so last_id advances correctly
            msgs.sort(key=lambda m: m.id)

            payloads = []
            max_id_in_batch = last_id

            for msg in msgs:
                # obtain text safely
                text = getattr(msg, "text", getattr(msg, "message", "")) or ""

                # entities extraction
                ent_list = []
                if getattr(msg, "entities", None):
                    for ent in msg.entities:
                        try:
                            if isinstance(ent, MessageEntityHashtag) and text:
                                ent_list.append({"entity_type": "hashtag", "entity_value": text[ent.offset: ent.offset + ent.length]})
                            elif isinstance(ent, MessageEntityUrl) and text:
                                ent_list.append({"entity_type": "url", "entity_value": text[ent.offset: ent.offset + ent.length]})
                            elif isinstance(ent, MessageEntityMention) and text:
                                ent_list.append({"entity_type": "mention", "entity_value": text[ent.offset: ent.offset + ent.length]})
                        except Exception:
                            # ignore slicing errors
                            continue

                # detect message type
                mtype = "text"
                try:
                    if getattr(msg, "photo", None):
                        mtype = "photo"
                    elif getattr(msg, "video", None):
                        mtype = "video"
                    elif getattr(msg, "document", None):
                        mtype = "document"
                    elif getattr(msg, "voice", None):
                        mtype = "voice"
                    elif getattr(msg, "audio", None):
                        mtype = "audio"
                    elif getattr(msg, "sticker", None):
                        mtype = "sticker"
                except Exception:
                    mtype = "text"

                media_link = f"https://t.me/{username}/{msg.id}" if getattr(entity, "username", None) else None

                payloads.append({
                    "message": {
                        "telegram_id": msg.id,
                        "message_type": mtype,
                        "content_text": text,
                        "media_file_path": media_link,
                        "views": getattr(msg, "views", 0),
                        "forwards": getattr(msg, "forwards", 0),
                        "replies_count": get_replies_count(msg),
                        "posted_at": str(getattr(msg, "date", None)),
                    },
                    "channel": {
                        "telegram_id": getattr(entity, "id", None),
                        "title": getattr(entity, "title", None),
                        "username": getattr(entity, "username", None),
                        "type": entity.__class__.__name__ if entity else None,
                        "is_private": False,
                        "is_adults": is_adults,
                        "description": getattr(entity, "about", None) if hasattr(entity, "about") else None,
                        "members_count": getattr(entity, "participants_count", None) if hasattr(entity, "participants_count") else None,
                        "photo_url": None
                    },
                    "sender": {
                        "telegram_id": getattr(msg, "sender_id", 0),
                        "username": getattr(msg.sender, "username", None) if getattr(msg, "sender", None) else None,
                        "display_name": getattr(msg.sender, "first_name", None) if getattr(msg, "sender", None) else None,
                        "is_bot": getattr(msg.sender, "bot", False) if getattr(msg, "sender", None) else False,
                        "photo_url": None
                    },
                    "entities": ent_list
                })

                if msg.id > max_id_in_batch:
                    max_id_in_batch = msg.id

            # send payloads to Laravel
            if payloads:
                try:
                    headers = {"Authorization": f"Bearer {IMPORT_TOKEN}", "Content-Type": "application/json"}
                    resp = requests.post(LARAVEL_API, headers=headers, json=payloads, timeout=REQUEST_TIMEOUT)
                    # parse created/updated if present
                    try:
                        jr = resp.json() if resp.content else {}
                        created = int(jr.get("created", 0) or 0)
                        updated = int(jr.get("updated", 0) or 0)
                    except Exception:
                        created = 0
                        updated = 0
                    total_created += created
                    total_updated += updated
                except RequestException as e:
                    return {"status": "error", "reason": f"network:{e}"}

            total_fetched += len(payloads)

            # update last_id persistently (move forward)
            if max_id_in_batch > last_id:
                last_id = max_id_in_batch
                last_ids[username] = last_id
                save_last_ids_for(session_name, last_ids)

            # if fewer than batch, done for this channel
            if len(msgs) < BATCH_SIZE:
                break
            # otherwise, continue loop to fetch next batch

        report.update({"status": "ok", "fetched": total_fetched, "created": total_created, "updated": total_updated})
        return report

    except FloodWaitError as e:
        secs = int(getattr(e, "seconds", 0) or 0)
        return {"status": "flood", "seconds": secs}
    except (UsernameInvalidError, UsernameNotOccupiedError, ValueError) as e:
        # Telethon sometimes raises ValueError("No user has ...")
        msg = str(e)
        if isinstance(e, ValueError) and msg.startswith("No user has"):
            return {"status": "not_found", "reason": msg}
        return {"status": "not_found", "reason": msg}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


# ---------------------------
# Per-account runner: process only that account's channels file, then exit
# ---------------------------
async def run_account(account: Dict[str, Any]):
    session_name = account["session"]
    api_id = account["api_id"]
    api_hash = account["api_hash"]

    # check suspend file
    suspended = load_suspended()
    suspended_ts = suspended.get(session_name)
    if suspended_ts and suspended_ts > now_ts():
        remain = int(suspended_ts - now_ts())
        print(f"[{session_name}] SUSPENDED until {iso_from_ts(suspended_ts)} (remaining {remain}s). Skipping this run.")
        return {"skipped": True}

    channels = load_account_channels(session_name)
    if not channels:
        print(f"[{session_name}] No channel file found or empty ({CHANNELS_TEMPLATE.format(session_name)}). Skipping.")
        return {"skipped": True}

    # load per-account last IDs
    last_ids = load_last_ids_for(session_name)

    client = TelegramClient(session_name, api_id, api_hash, connection_retries=5)
    try:
        await client.start()
    except Exception as e:
        print(f"[{session_name}] Failed to start Telethon client: {e}")
        return {"error": str(e)}

    print(f"[{session_name}] logged in, processing {len(channels)} channels")

    failed_local: List[Dict[str, Any]] = []
    account_counts = {"channels": 0, "messages": 0, "created": 0, "updated": 0}

    try:
        for ch in channels:
            ch.setdefault("_attempts", 0)
            username = ch.get("username", "<unknown>")

            # small random jitter before each channel to reduce burstiness
            await asyncio.sleep(random.uniform(0.2, 1.0))

            report = await fetch_channel_messages(client, session_name, ch, last_ids)

            if report.get("status") == "ok":
                fetched = report.get("fetched", 0)
                created = report.get("created", 0)
                updated = report.get("updated", 0)
                account_counts["channels"] += 1
                account_counts["messages"] += fetched
                account_counts["created"] += created
                account_counts["updated"] += updated
                print(f"[{session_name}] {username} -> fetched {fetched} (created {created}, updated {updated})")

            elif report.get("status") == "flood":
                secs = int(report.get("seconds", 0) or 0)
                wake_ts = now_ts() + secs + 5
                suspended = load_suspended()
                suspended[session_name] = wake_ts
                save_suspended(suspended)
                # requeue the channel into failed list for later retry
                ch_reason = {"username": username, "is_adults": bool(ch.get("is_adults", False)), "reason": f"flood_{secs}s"}
                failed_local.append(ch_reason)
                print(f"[{session_name}] FloodWait {secs}s on {username}. Suspending account until {iso_from_ts(wake_ts)}. Saved channel to failed list.")
                # stop processing more channels for this account (suspended)
                break

            elif report.get("status") == "not_found":
                failed_local.append({"username": username, "is_adults": bool(ch.get("is_adults", False)), "reason": report.get("reason", "not_found")})
                print(f"[{session_name}] {username} not found -> saved to failed")

            else:
                # transient error - allow some retries in-memory
                reason = report.get("reason", "unknown")
                ch["_attempts"] = ch.get("_attempts", 0) + 1
                if ch["_attempts"] >= MAX_ATTEMPTS:
                    failed_local.append({"username": username, "is_adults": bool(ch.get("is_adults", False)), "reason": reason})
                    print(f"[{session_name}] {username} permanently failed: {reason}")
                else:
                    # try again after a backoff
                    backoff = random.randint(3, 10) + ch["_attempts"] * 5
                    print(f"[{session_name}] {username} transient error: {reason}. Retrying after {backoff}s (attempt {ch['_attempts']})")
                    await asyncio.sleep(backoff)
                    # do one immediate retry
                    report2 = await fetch_channel_messages(client, session_name, ch, last_ids)
                    if report2.get("status") == "ok":
                        fetched = report2.get("fetched", 0)
                        created = report2.get("created", 0)
                        updated = report2.get("updated", 0)
                        account_counts["channels"] += 1
                        account_counts["messages"] += fetched
                        account_counts["created"] += created
                        account_counts["updated"] += updated
                        print(f"[{session_name}] (retry) {username} -> fetched {fetched} (created {created}, updated {updated})")
                    else:
                        failed_local.append({"username": username, "is_adults": bool(ch.get("is_adults", False)), "reason": reason})
                        print(f"[{session_name}] (retry failed) {username} -> saved to failed")

    finally:
        try:
            save_last_ids_for(session_name, last_ids)
        except Exception:
            pass
        try:
            await client.disconnect()
        except Exception:
            pass
        print(f"[{session_name}] disconnected")

    # persist failed_local to global failed file (merge safely)
    global_failed = load_json(FAILED_FILE, [])
    # merge without duplicates
    existing_usernames = {f.get("username") for f in global_failed}
    for f in failed_local:
        if f.get("username") not in existing_usernames:
            global_failed.append(f)
            existing_usernames.add(f.get("username"))
    save_failed_channels(global_failed)

    # update global stats
    stats["public"]["channels"] += account_counts["channels"]
    stats["public"]["messages"] += account_counts["messages"]
    stats["public"]["created"] += account_counts["created"]
    stats["public"]["updated"] += account_counts["updated"]

    return {"skipped": False, "counts": account_counts, "failed": failed_local}


# ---------------------------
# Entry point
# ---------------------------
async def main():
    print("Crawler starting")
    suspended = load_suspended()
    # run accounts one by one (each account reads its own channels file and exits)
    for account in ACCOUNTS:
        session_name = account["session"]
        print(f"--- Account: {session_name} ---")
        result = await run_account(account)
        # small pause between accounts
        await asyncio.sleep(random.uniform(0.5, 2.0))

    # final summary
    print("\n📊 Import Summary:")
    print(f"Public Channels fetched: {stats['public']['channels']}")
    print(f"Public Messages fetched: {stats['public']['messages']}")
    print(f"Laravel created: {stats['public']['created']}, updated: {stats['public']['updated']}")
    print("Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
