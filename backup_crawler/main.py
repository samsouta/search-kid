import asyncio
import json
import os
import random
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException, ConnectionError, Timeout
from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError, UsernameInvalidError, UsernameNotOccupiedError,
    ChannelPrivateError, ChatAdminRequiredError, AuthKeyUnregisteredError,
    SessionPasswordNeededError, RPCError, ConnectionError as TelethonConnectionError
)
from telethon.tl.types import MessageEntityHashtag, MessageEntityUrl, MessageEntityMention

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
SUSPENDED_FILE = "suspended.json"
FAILED_FILE = "failed_channels.json"
LAST_ID_TEMPLATE = "last_id_{}.json"
CHANNELS_TEMPLATE = "{}_channels.json"

# Behavior - More conservative to avoid bans
BATCH_SIZE = 50  # Reduced from 100
REQUEST_TIMEOUT = 60  # Increased timeout
MAX_ATTEMPTS = 2  # Reduced retry attempts
MIN_DELAY_BETWEEN_CHANNELS = 2.0  # Minimum delay between channels
MAX_DELAY_BETWEEN_CHANNELS = 5.0  # Maximum delay between channels
MIN_DELAY_BETWEEN_MESSAGES = 0.1  # Small delay between message processing
MAX_DELAY_BETWEEN_MESSAGES = 0.5
API_REQUEST_DELAY = 1.0  # Delay after each API request
MAX_MESSAGES_PER_CHANNEL = 1000  # Limit messages per channel per run

# ---------------------------
# Stats
# ---------------------------
stats = {"public": {"channels": 0, "messages": 0, "created": 0, "updated": 0, "errors": 0}}

# ---------------------------
# JSON helpers with better error handling
# ---------------------------
def load_json(path: str, default: Any):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    logger.warning(f"Empty file {path}, using default")
                    return default
                return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {path}: {e}")
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
    return default

def save_json(path: str, data: Any):
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        logger.debug(f"Saved data to {path}")
    except Exception as e:
        logger.error(f"Error saving to {path}: {e}")
        raise

# ---------------------------
# Suspension management
# ---------------------------
def load_suspended() -> Dict[str, float]:
    return load_json(SUSPENDED_FILE, {})

def save_suspended(data: Dict[str, float]):
    # Clean expired suspensions
    current_time = now_ts()
    cleaned_data = {k: v for k, v in data.items() if v > current_time}
    save_json(SUSPENDED_FILE, cleaned_data)

def is_account_suspended(session_name: str) -> tuple[bool, float]:
    suspended = load_suspended()
    suspended_until = suspended.get(session_name, 0)
    if suspended_until > now_ts():
        return True, suspended_until
    return False, 0

# ---------------------------
# Per-account helpers
# ---------------------------
def load_last_ids_for(session_name: str) -> Dict[str, int]:
    path = LAST_ID_TEMPLATE.format(session_name)
    return load_json(path, {})

def save_last_ids_for(session_name: str, data: Dict[str, int]):
    path = LAST_ID_TEMPLATE.format(session_name)
    save_json(path, data)

# ---------------------------
# Failed channels management
# ---------------------------
def save_failed_channels(failed: List[Dict[str, Any]]):
    if failed:
        # Remove duplicates based on username
        seen = set()
        unique_failed = []
        for item in failed:
            username = item.get('username')
            if username and username not in seen:
                seen.add(username)
                unique_failed.append(item)
        save_json(FAILED_FILE, unique_failed)
    else:
        if os.path.exists(FAILED_FILE):
            try:
                os.remove(FAILED_FILE)
            except Exception as e:
                logger.warning(f"Could not remove {FAILED_FILE}: {e}")

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

def sanitize_text(text: str) -> str:
    """Sanitize text to prevent issues with special characters"""
    if not isinstance(text, str):
        return ""
    # Remove null bytes and control characters except newlines and tabs
    return ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')

# ---------------------------
# Load channels with validation
# ---------------------------
def load_account_channels(session_name: str) -> List[Dict[str, Any]]:
    path = CHANNELS_TEMPLATE.format(session_name)
    channels = load_json(path, [])
    
    # Validate and clean channels
    valid_channels = []
    for ch in channels:
        if isinstance(ch, dict) and ch.get('username'):
            # Clean username
            username = ch['username'].strip().lstrip('@')
            if username:
                ch['username'] = username
                valid_channels.append(ch)
            else:
                logger.warning(f"Invalid username in channel: {ch}")
        else:
            logger.warning(f"Invalid channel format: {ch}")
    
    logger.info(f"Loaded {len(valid_channels)} valid channels for {session_name}")
    return valid_channels

# ---------------------------
# Enhanced message fetching with better rate limiting
# ---------------------------
async def fetch_channel_messages(
    client: TelegramClient,
    session_name: str,
    channel: Dict[str, Any],
    last_ids: Dict[str, int],
) -> Dict[str, Any]:
    username = channel.get("username", "").strip().lstrip('@')
    is_adults = bool(channel.get("is_adults", False))
    report = {"status": "unknown", "fetched": 0, "created": 0, "updated": 0}

    if not username:
        report.update({"status": "not_found", "reason": "no_username"})
        return report

    last_id = int(last_ids.get(username, 0) or 0)
    total_fetched = 0
    total_created = 0
    total_updated = 0
    messages_processed = 0

    try:
        # Add delay before getting entity
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        try:
            entity = await client.get_entity(username)
        except Exception as e:
            if "No user has" in str(e) or "Username not found" in str(e):
                return {"status": "not_found", "reason": f"entity_not_found: {str(e)[:100]}"}
            raise

        # Additional safety check for channel type
        if not hasattr(entity, 'id'):
            return {"status": "error", "reason": "invalid_entity"}

        logger.info(f"[{session_name}] Processing {username} (last_id: {last_id})")

        # Fetch messages with rate limiting
        while messages_processed < MAX_MESSAGES_PER_CHANNEL:
            try:
                # Add delay before each batch
                await asyncio.sleep(random.uniform(MIN_DELAY_BETWEEN_MESSAGES, MAX_DELAY_BETWEEN_MESSAGES))
                
                msgs = []
                async for m in client.iter_messages(entity, limit=BATCH_SIZE, min_id=last_id):
                    msgs.append(m)
                    # Small delay between message processing
                    if len(msgs) % 10 == 0:
                        await asyncio.sleep(0.1)
                
                if not msgs:
                    break

                msgs.sort(key=lambda m: m.id)
                payloads = []
                max_id_in_batch = last_id

                for msg in msgs:
                    try:
                        # Get text safely
                        text = getattr(msg, "text", getattr(msg, "message", "")) or ""
                        text = sanitize_text(text)

                        # Extract entities
                        ent_list = []
                        if getattr(msg, "entities", None) and text:
                            for ent in msg.entities:
                                try:
                                    start_pos = getattr(ent, 'offset', 0)
                                    length = getattr(ent, 'length', 0)
                                    
                                    if 0 <= start_pos < len(text) and start_pos + length <= len(text):
                                        entity_text = text[start_pos:start_pos + length]
                                        
                                        if isinstance(ent, MessageEntityHashtag):
                                            ent_list.append({"entity_type": "hashtag", "entity_value": entity_text})
                                        elif isinstance(ent, MessageEntityUrl):
                                            ent_list.append({"entity_type": "url", "entity_value": entity_text})
                                        elif isinstance(ent, MessageEntityMention):
                                            ent_list.append({"entity_type": "mention", "entity_value": entity_text})
                                except Exception as e:
                                    logger.debug(f"Entity extraction error: {e}")
                                    continue

                        # Detect message type more safely
                        mtype = "text"
                        try:
                            if getattr(msg, "photo", None):
                                mtype = "photo"
                            elif getattr(msg, "video", None):
                                mtype = "video"
                            elif getattr(msg, "document", None):
                                doc = msg.document
                                if hasattr(doc, 'mime_type'):
                                    mime = doc.mime_type or ""
                                    if mime.startswith('audio/'):
                                        mtype = "audio"
                                    elif mime.startswith('video/'):
                                        mtype = "video"
                                    else:
                                        mtype = "document"
                                else:
                                    mtype = "document"
                            elif getattr(msg, "voice", None):
                                mtype = "voice"
                            elif getattr(msg, "audio", None):
                                mtype = "audio"
                            elif getattr(msg, "sticker", None):
                                mtype = "sticker"
                        except Exception:
                            mtype = "text"

                        # Create media link safely
                        media_link = None
                        try:
                            if getattr(entity, "username", None):
                                media_link = f"https://t.me/{entity.username}/{msg.id}"
                        except Exception:
                            pass

                        # Get message date safely
                        msg_date = getattr(msg, "date", None)
                        posted_at = str(msg_date) if msg_date else None

                        payloads.append({
                            "message": {
                                "telegram_id": msg.id,
                                "message_type": mtype,
                                "content_text": text[:10000],  # Limit text length
                                "media_file_path": media_link,
                                "views": int(getattr(msg, "views", 0) or 0),
                                "forwards": int(getattr(msg, "forwards", 0) or 0),
                                "replies_count": get_replies_count(msg),
                                "posted_at": posted_at,
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
                                "telegram_id": int(getattr(msg, "sender_id", 0) or 0),
                                "username": getattr(msg.sender, "username", None) if getattr(msg, "sender", None) else None,
                                "display_name": getattr(msg.sender, "first_name", None) if getattr(msg, "sender", None) else None,
                                "is_bot": bool(getattr(msg.sender, "bot", False)) if getattr(msg, "sender", None) else False,
                                "photo_url": None
                            },
                            "entities": ent_list
                        })

                        if msg.id > max_id_in_batch:
                            max_id_in_batch = msg.id

                    except Exception as e:
                        logger.warning(f"Error processing message {getattr(msg, 'id', 'unknown')}: {e}")
                        continue

                # Send to Laravel API with retry logic
                if payloads:
                    created, updated = await send_to_api(payloads, session_name, username)
                    if created is None:  # API error
                        return {"status": "error", "reason": "api_error"}
                    
                    total_created += created
                    total_updated += updated
                    
                    # Add delay after API request
                    await asyncio.sleep(API_REQUEST_DELAY)

                total_fetched += len(payloads)
                messages_processed += len(msgs)

                # Update last_id
                if max_id_in_batch > last_id:
                    last_id = max_id_in_batch
                    last_ids[username] = last_id
                    save_last_ids_for(session_name, last_ids)

                # Break if fewer messages than batch size
                if len(msgs) < BATCH_SIZE:
                    break
                    
            except FloodWaitError as e:
                # Re-raise FloodWaitError to be handled by outer try-catch
                raise e
            except Exception as e:
                logger.warning(f"Error in message batch processing: {e}")
                # Continue with next batch instead of failing completely
                await asyncio.sleep(2.0)
                continue

        report.update({
            "status": "ok", 
            "fetched": total_fetched, 
            "created": total_created, 
            "updated": total_updated
        })
        return report

    except FloodWaitError as e:
        secs = int(getattr(e, "seconds", 3600))
        logger.warning(f"[{session_name}] FloodWait {secs}s for {username}")
        return {"status": "flood", "seconds": secs}
    
    except (UsernameInvalidError, UsernameNotOccupiedError) as e:
        return {"status": "not_found", "reason": f"username_error: {str(e)[:100]}"}
    
    except ChannelPrivateError:
        return {"status": "not_found", "reason": "channel_private"}
    
    except ChatAdminRequiredError:
        return {"status": "not_found", "reason": "admin_required"}
    
    except AuthKeyUnregisteredError:
        return {"status": "auth_error", "reason": "auth_key_unregistered"}
    
    except TelethonConnectionError as e:
        return {"status": "connection_error", "reason": f"connection: {str(e)[:100]}"}
    
    except RPCError as e:
        return {"status": "rpc_error", "reason": f"rpc: {str(e)[:100]}"}
    
    except ValueError as e:
        msg = str(e)
        if "No user has" in msg or "Username not found" in msg:
            return {"status": "not_found", "reason": f"value_error: {msg[:100]}"}
        return {"status": "error", "reason": f"value_error: {msg[:100]}"}
    
    except Exception as e:
        logger.error(f"Unexpected error in fetch_channel_messages: {e}")
        return {"status": "error", "reason": f"unexpected: {str(e)[:100]}"}

# ---------------------------
# API communication with retry logic
# ---------------------------
async def send_to_api(payloads: List[Dict], session_name: str, username: str) -> tuple[int, int]:
    """Send payloads to Laravel API with retry logic. Returns (created, updated) or (None, None) on error."""
    
    for attempt in range(3):  # 3 retry attempts
        try:
            headers = {
                "Authorization": f"Bearer {IMPORT_TOKEN}", 
                "Content-Type": "application/json",
                "User-Agent": "TelegramCrawler/1.0"
            }
            
            resp = requests.post(
                LARAVEL_API, 
                headers=headers, 
                json=payloads, 
                timeout=REQUEST_TIMEOUT
            )
            
            if resp.status_code == 200:
                try:
                    jr = resp.json() if resp.content else {}
                    created = int(jr.get("created", 0) or 0)
                    updated = int(jr.get("updated", 0) or 0)
                    return created, updated
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON response from API for {username}")
                    return 0, 0
            else:
                logger.warning(f"API returned status {resp.status_code} for {username}")
                if attempt < 2:  # Don't sleep on last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
                
        except (ConnectionError, Timeout) as e:
            logger.warning(f"API connection error for {username} (attempt {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
            continue
        except RequestException as e:
            logger.error(f"API request error for {username}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected API error for {username}: {e}")
            return None, None
    
    logger.error(f"API failed after 3 attempts for {username}")
    return None, None

# ---------------------------
# Enhanced account runner
# ---------------------------
async def run_account(account: Dict[str, Any]) -> Dict[str, Any]:
    session_name = account["session"]
    api_id = account["api_id"]
    api_hash = account["api_hash"]

    # Check suspension
    is_suspended, suspended_until = is_account_suspended(session_name)
    if is_suspended:
        remain = int(suspended_until - now_ts())
        logger.info(f"[{session_name}] SUSPENDED until {iso_from_ts(suspended_until)} (remaining {remain}s)")
        return {"skipped": True, "reason": "suspended"}

    # Load channels
    channels = load_account_channels(session_name)
    if not channels:
        logger.info(f"[{session_name}] No channels found")
        return {"skipped": True, "reason": "no_channels"}

    # Load last IDs
    last_ids = load_last_ids_for(session_name)

    # Create client with better settings
    client = TelegramClient(
        session_name, 
        api_id, 
        api_hash,
        connection_retries=3,
        auto_reconnect=True,
        timeout=30
    )
    
    try:
        await client.start()
        logger.info(f"[{session_name}] Client started successfully")
    except AuthKeyUnregisteredError:
        logger.error(f"[{session_name}] Auth key unregistered - session invalid")
        return {"error": "auth_key_unregistered"}
    except SessionPasswordNeededError:
        logger.error(f"[{session_name}] 2FA required")
        return {"error": "2fa_required"}
    except Exception as e:
        logger.error(f"[{session_name}] Failed to start client: {e}")
        return {"error": str(e)}

    logger.info(f"[{session_name}] Processing {len(channels)} channels")

    failed_local: List[Dict[str, Any]] = []
    account_counts = {"channels": 0, "messages": 0, "created": 0, "updated": 0}
    
    try:
        for i, ch in enumerate(channels):
            ch.setdefault("_attempts", 0)
            username = ch.get("username", "<unknown>")
            
            # Progress logging
            logger.info(f"[{session_name}] Processing channel {i+1}/{len(channels)}: {username}")

            # Delay between channels
            delay = random.uniform(MIN_DELAY_BETWEEN_CHANNELS, MAX_DELAY_BETWEEN_CHANNELS)
            await asyncio.sleep(delay)

            report = await fetch_channel_messages(client, session_name, ch, last_ids)

            if report.get("status") == "ok":
                fetched = report.get("fetched", 0)
                created = report.get("created", 0)
                updated = report.get("updated", 0)
                account_counts["channels"] += 1
                account_counts["messages"] += fetched
                account_counts["created"] += created
                account_counts["updated"] += updated
                logger.info(f"[{session_name}] {username} -> fetched {fetched} (created {created}, updated {updated})")

            elif report.get("status") == "flood":
                secs = report.get("seconds", 3600)
                # Add some buffer time
                wake_ts = now_ts() + secs + random.randint(60, 300)
                
                suspended = load_suspended()
                suspended[session_name] = wake_ts
                save_suspended(suspended)
                
                # Save channel for retry
                failed_local.append({
                    "username": username, 
                    "is_adults": bool(ch.get("is_adults", False)), 
                    "reason": f"flood_{secs}s"
                })
                
                logger.warning(f"[{session_name}] FloodWait {secs}s on {username}. Account suspended until {iso_from_ts(wake_ts)}")
                break  # Stop processing for this account

            elif report.get("status") in ["not_found", "auth_error"]:
                failed_local.append({
                    "username": username, 
                    "is_adults": bool(ch.get("is_adults", False)), 
                    "reason": report.get("reason", "not_found")
                })
                logger.info(f"[{session_name}] {username} -> {report.get('reason', 'not_found')}")

            else:
                # Handle other errors with retry logic
                reason = report.get("reason", "unknown")
                ch["_attempts"] = ch.get("_attempts", 0) + 1
                
                if ch["_attempts"] >= MAX_ATTEMPTS:
                    failed_local.append({
                        "username": username, 
                        "is_adults": bool(ch.get("is_adults", False)), 
                        "reason": reason
                    })
                    logger.warning(f"[{session_name}] {username} permanently failed: {reason}")
                    stats["public"]["errors"] += 1
                else:
                    # Retry with exponential backoff
                    backoff = random.randint(5, 15) + (ch["_attempts"] * 10)
                    logger.info(f"[{session_name}] {username} error: {reason}. Retrying after {backoff}s")
                    await asyncio.sleep(backoff)
                    
                    # Single retry attempt
                    retry_report = await fetch_channel_messages(client, session_name, ch, last_ids)
                    if retry_report.get("status") == "ok":
                        fetched = retry_report.get("fetched", 0)
                        created = retry_report.get("created", 0)
                        updated = retry_report.get("updated", 0)
                        account_counts["channels"] += 1
                        account_counts["messages"] += fetched
                        account_counts["created"] += created
                        account_counts["updated"] += updated
                        logger.info(f"[{session_name}] {username} (retry) -> fetched {fetched}")
                    else:
                        failed_local.append({
                            "username": username, 
                            "is_adults": bool(ch.get("is_adults", False)), 
                            "reason": f"retry_failed: {reason}"
                        })
                        logger.warning(f"[{session_name}] {username} retry failed")
                        stats["public"]["errors"] += 1

    except Exception as e:
        logger.error(f"[{session_name}] Unexpected error in run_account: {e}")
        return {"error": f"unexpected: {str(e)}"}
    finally:
        # Cleanup
        try:
            save_last_ids_for(session_name, last_ids)
        except Exception as e:
            logger.error(f"Error saving last IDs: {e}")
        
        try:
            await client.disconnect()
            logger.info(f"[{session_name}] Client disconnected")
        except Exception as e:
            logger.warning(f"Error disconnecting client: {e}")

    # Update failed channels file
    if failed_local:
        try:
            global_failed = load_json(FAILED_FILE, [])
            existing_usernames = {f.get("username") for f in global_failed}
            
            for f in failed_local:
                if f.get("username") not in existing_usernames:
                    global_failed.append(f)
                    existing_usernames.add(f.get("username"))
            
            save_failed_channels(global_failed)
        except Exception as e:
            logger.error(f"Error updating failed channels: {e}")

    # Update global stats
    for key in ["channels", "messages", "created", "updated"]:
        stats["public"][key] += account_counts[key]

    return {"skipped": False, "counts": account_counts, "failed_count": len(failed_local)}

# ---------------------------
# Main entry point
# ---------------------------
async def main():
    logger.info("=== Telegram Crawler Starting ===")
    
    try:
        for account in ACCOUNTS:
            session_name = account["session"]
            logger.info(f"--- Processing Account: {session_name} ---")
            
            result = await run_account(account)
            
            if result.get("skipped"):
                reason = result.get("reason", "unknown")
                logger.info(f"[{session_name}] Skipped: {reason}")
            elif result.get("error"):
                logger.error(f"[{session_name}] Error: {result['error']}")
            else:
                counts = result.get("counts", {})
                failed_count = result.get("failed_count", 0)
                logger.info(f"[{session_name}] Completed - Channels: {counts.get('channels', 0)}, "
                           f"Messages: {counts.get('messages', 0)}, Failed: {failed_count}")

            # Longer delay between accounts
            delay = random.uniform(3.0, 8.0)
            await asyncio.sleep(delay)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return

    # Final summary
    logger.info("\n" + "="*50)
    logger.info("📊 FINAL SUMMARY:")
    logger.info(f"Channels processed: {stats['public']['channels']}")
    logger.info(f"Messages fetched: {stats['public']['messages']}")
    logger.info(f"Records created: {stats['public']['created']}")
    logger.info(f"Records updated: {stats['public']['updated']}")
    logger.info(f"Errors encountered: {stats['public']['errors']}")
    logger.info("="*50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)