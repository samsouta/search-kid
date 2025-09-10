#!/usr/bin/env python3
"""
Robust Telegram crawler (improved)
- Multi-account worker pool
- Per-account last_id files
- Failed channels saved
- Handles FloodWait, missing usernames, and transient errors
- Detailed, advanced logging (includes flood wake times, retry/backoff, counts)
"""

import asyncio
import json
import os
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests
from requests.exceptions import RequestException
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UsernameInvalidError, UsernameNotOccupiedError
from telethon.tl.types import MessageEntityHashtag, MessageEntityUrl, MessageEntityMention

# ---------------------------
# CONFIG - edit these values
# ---------------------------
ACCOUNTS = [
    {"session": "anon1", "api_id": 28887666, "api_hash": "1e01869b2b510bfecb4462d08b529b72"},
    {"session": "anon2", "api_id": 24972105, "api_hash": "c57ebdb04dbb2c6983f3e3ddd7b8aedd"},
    {"session": "anon3", "api_id": 20549861, "api_hash": "90146ca2ac1a20152804462baf976e85"},
    {"session": "anon4", "api_id": 16850912, "api_hash": "a6aefe94cd56f0c66c9fc406ad36aba9"},
    # new session aung aung 
    {"session": "anon4", "api_id": 22922095, "api_hash": "f665afaafdb33f7fd9944dc9680345a5"},
    # samsouta88
    {"session": "anon5", "api_id": 22893596, "api_hash": "099e03188484d2041f7168abd7db8c8f"},
]

LARAVEL_API = "https://api-searchkid.zakari.site/api/messages/import"
IMPORT_TOKEN = "loveyoutenthousand"

CHANNELS_FILE = "channels.json"          # JSON array of {"username":"...", "is_adults": true/false}
FAILED_FILE = "failed_channels.json"
BATCH_SIZE = 10
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT = 30

# ---------------------------
# Shared runtime state & stats
# ---------------------------
stats = {
    "public": {"channels": 0, "messages": 0, "created": 0, "updated": 0},
}
# Per-account suspended-until timestamps (when floodwait occurs)
account_suspended_until: Dict[str, float] = {}

# ---------------------------
# Simple JSON helpers
# ---------------------------
def load_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json(path: str, data: Any):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


# ---------------------------
# Channels / last_id helpers
# ---------------------------
def load_channels() -> List[Dict[str, Any]]:
    channels = load_json(CHANNELS_FILE, [])
    # Merge failed list so we retry them
    failed = load_json(FAILED_FILE, [])
    usernames = {c["username"] for c in channels if "username" in c}
    for ch in failed:
        if ch.get("username") and ch["username"] not in usernames:
            channels.append(ch)
    return channels


def load_last_ids_for(account_session: str) -> Dict[str, int]:
    path = f"last_id_{account_session}.json"
    return load_json(path, {})


def save_last_ids_for(account_session: str, data: Dict[str, int]):
    path = f"last_id_{account_session}.json"
    save_json(path, data)


# ---------------------------
# Utility helpers
# ---------------------------
def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def fmt_timedelta_seconds(s: int) -> str:
    return str(timedelta(seconds=s))


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
# Fetch messages for one channel (returns a report)
# report fields: status: ok/flood/not_found/error, fetched, created, updated
# ---------------------------
async def fetch_channel_messages(client: TelegramClient, account_session: str, channel: Dict[str, Any], last_ids: Dict[str, int]):
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

        while True:
            # fetch messages with id > last_id (min_id)
            msgs = [m async for m in client.iter_messages(entity, limit=BATCH_SIZE, min_id=last_id)]
            if not msgs:
                break

            # sort ascending (oldest first) so we update last_id forward
            msgs.sort(key=lambda m: m.id)

            payloads = []
            max_id_in_batch = last_id

            for msg in msgs:
                # text / message content
                text = getattr(msg, "text", getattr(msg, "message", "")) or ""

                # collect entities (hashtags, urls, mentions)
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
                            continue

                # message type detection
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
                        "type": entity.__class__.__name__,
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
                    # parse response if it contains created/updated numbers
                    try:
                        jr = resp.json() if resp.content else {}
                        created = int(jr.get("created", 0) or 0)
                        updated = int(jr.get("updated", 0) or 0)
                        total_created += created
                        total_updated += updated
                    except Exception:
                        # ignore parse errors
                        pass
                except RequestException as e:
                    return {"status": "error", "reason": f"network:{e}"}

            total_fetched += len(payloads)

            # update last_id persistently
            if max_id_in_batch > last_id:
                last_id = max_id_in_batch
                last_ids[username] = last_id
                save_last_ids_for(account_session, last_ids)

            # if fewer than batch, we reached the end
            if len(msgs) < BATCH_SIZE:
                break
            # otherwise continue next batch

        report.update({"status": "ok", "fetched": total_fetched, "created": total_created, "updated": total_updated})
        return report

    except FloodWaitError as e:
        seconds = int(getattr(e, "seconds", 0) or 0)
        return {"status": "flood", "seconds": seconds}
    except (UsernameInvalidError, UsernameNotOccupiedError):
        return {"status": "not_found"}
    except ValueError as ve:
        # Telethon raises ValueError("No user has ...") in some cases
        if str(ve).startswith("No user has"):
            return {"status": "not_found"}
        return {"status": "error", "reason": str(ve)}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


# ---------------------------
# Worker loop (per account)
# ---------------------------
async def worker_loop(account: Dict[str, Any], queue: asyncio.Queue, failed_list: List[Dict[str, Any]], stats_ref: Dict[str, Any]):
    session_name = account["session"]
    api_id = account["api_id"]
    api_hash = account["api_hash"]

    client = TelegramClient(session_name, api_id, api_hash, connection_retries=5)
    try:
        await client.start()
    except Exception as e:
        print(f"[{session_name}] start failed: {e}")
        return

    print(f"[{session_name}] logged in")
    last_ids = load_last_ids_for(session_name)

    try:
        while True:
            # check suspension due to floodwait
            suspended_until = account_suspended_until.get(session_name)
            if suspended_until:
                remain = suspended_until - time.time()
                if remain > 0:
                    wake_at = datetime.utcfromtimestamp(suspended_until).isoformat() + "Z"
                    print(f"[{session_name}] SUSPENDED until {wake_at} (remaining {int(remain)}s). Sleeping.")
                    await asyncio.sleep(min(remain, 60))  # sleep in chunks so we remain responsive
                    continue
                else:
                    # suspension expired
                    account_suspended_until.pop(session_name, None)
                    print(f"[{session_name}] Suspension expired, resuming.")

            item = await queue.get()
            if item is None:
                queue.task_done()
                break

            item.setdefault("_attempts", 0)
            username = item.get("username", "<unknown>")

            res = await fetch_channel_messages(client, session_name, item, last_ids)

            if res.get("status") == "ok":
                fetched = res.get("fetched", 0)
                created = res.get("created", 0)
                updated = res.get("updated", 0)
                print(f"[{session_name}] {username} -> fetched {fetched} (created {created}, updated {updated})")
                stats_ref["public"]["messages"] += fetched
                stats_ref["public"]["channels"] += 1
                stats_ref["public"]["created"] += created
                stats_ref["public"]["updated"] += updated

            elif res.get("status") == "flood":
                secs = int(res.get("seconds", 0) or 0)
                # set suspension for this account
                wake_ts = time.time() + secs + 5
                account_suspended_until[session_name] = wake_ts
                wake_iso = datetime.utcfromtimestamp(wake_ts).isoformat() + "Z"
                item["_attempts"] += 1

                # requeue the channel so other workers can try it
                if item["_attempts"] < MAX_ATTEMPTS:
                    await queue.put(item)
                    print(f"[{session_name}] FloodWait {secs}s on {username}. Requeued (attempt {item['_attempts']}). Account suspended until {wake_iso}.")
                else:
                    failed_list.append({"username": username, "is_adults": bool(item.get("is_adults", False)), "reason": f"flood_after_{item['_attempts']}"})
                    print(f"[{session_name}] FloodWait fatal for {username}: attempts={item['_attempts']}. Saved to failed list.")

                # wait a short time here to reduce hammering other requests
                await asyncio.sleep(min(secs + 3, 60))

            elif res.get("status") == "not_found":
                failed_list.append({"username": username, "is_adults": bool(item.get("is_adults", False)), "reason": "not_found"})
                print(f"[{session_name}] {username} not found -> saved to failed")

            else:
                # transient error -> backoff & requeue up to MAX_ATTEMPTS
                reason = res.get("reason", "unknown")
                item["_attempts"] += 1
                if item["_attempts"] >= MAX_ATTEMPTS:
                    failed_list.append({"username": username, "is_adults": bool(item.get("is_adults", False)), "reason": reason})
                    print(f"[{session_name}] {username} permanently failed: {reason}")
                else:
                    backoff = random.randint(5, 20) + item["_attempts"] * 5
                    await queue.put(item)
                    print(f"[{session_name}] {username} transient error: {reason}. Requeued (attempt {item['_attempts']}). Backoff {backoff}s")
                    await asyncio.sleep(backoff)

            queue.task_done()
            # small jitter to avoid being too aggressive
            await asyncio.sleep(random.uniform(0.5, 2.0))
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


# ---------------------------
# Main runner
# ---------------------------
async def main():
    channels = load_channels()
    if not channels:
        print("No channels in channels.json")
        return

    queue: asyncio.Queue = asyncio.Queue()
    for ch in channels:
        ch.setdefault("_attempts", 0)
        await queue.put(ch)

    # add sentinel None for each worker (shutdown signal)
    num_workers = len(ACCOUNTS)
    for _ in range(num_workers):
        await queue.put(None)

    failed: List[Dict[str, Any]] = []
    # spawn workers
    workers = [asyncio.create_task(worker_loop(ACCOUNTS[i], queue, failed, stats)) for i in range(num_workers)]

    # wait for completion
    await asyncio.gather(*workers)

    # save failed channels with minimal info
    if failed:
        to_save = [{"username": f.get("username"), "is_adults": f.get("is_adults", False), "reason": f.get("reason")} for f in failed]
        save_json(FAILED_FILE, to_save)
        print(f"Saved {len(to_save)} failed channels to {FAILED_FILE}")
    else:
        if os.path.exists(FAILED_FILE):
            os.remove(FAILED_FILE)

    # final summary
    print("\n📊 Import Summary:")
    print(f"Public Channels fetched: {stats['public']['channels']}")
    print(f"Public Messages fetched: {stats['public']['messages']}")
    print(f"Laravel created: {stats['public']['created']}, updated: {stats['public']['updated']}")
    print("✅ Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
