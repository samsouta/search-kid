import requests
import json
import os
from telethon import TelegramClient
from telethon.tl.types import (
    MessageEntityHashtag,
    MessageEntityUrl,
    MessageEntityMention
)

# 🔑 Telegram API
api_id = 28887666
api_hash = "1e01869b2b510bfecb4462d08b529b72"
client = TelegramClient("anon", api_id, api_hash)

# 🔗 Laravel API
LARAVEL_API = "http://host.docker.internal:8000/api/messages/import"
IMPORT_TOKEN = "loveyoutenthousand"

# 📂 Load channels from external JSON file
CHANNELS_FILE = "channels.json"

# 📊 Stats counters
stats = {"public": {"channels": 0, "messages": 0}}

# 📂 File to store last fetched message IDs
LAST_ID_FILE = "last_id.json"


def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r") as f:
            return json.load(f)
    return []


CHANNELS = load_channels()


def load_last_ids():
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as f:
            return json.load(f)
    return {}


def save_last_ids(data):
    with open(LAST_ID_FILE, "w") as f:
        json.dump(data, f, indent=4)


async def fetch_and_send(channel_ref):
    """
    channel_ref comes from channels.json:
    {
      "username": "luowux",
      "is_adults": true
    }
    """
    channel_username = channel_ref["username"]
    is_adults = channel_ref.get("is_adults", False)

    last_ids = load_last_ids()
    last_id = last_ids.get(channel_username, 0)  # default 0 if first time
    batch_size = 500

    try:
        channel = await client.get_entity(channel_username)
        batch = []

        async for message in client.iter_messages(channel, limit=batch_size, offset_id=last_id):
            if message.id > last_id:
                last_id = message.id

            # 🔎 Detect entities (hashtags, urls, mentions)
            entities = []
            if message.entities:
                for ent in message.entities:
                    if isinstance(ent, MessageEntityHashtag):
                        entities.append({
                            "entity_type": "hashtag",
                            "entity_value": message.text[ent.offset: ent.offset + ent.length]
                        })
                    elif isinstance(ent, MessageEntityUrl):
                        entities.append({
                            "entity_type": "url",
                            "entity_value": message.text[ent.offset: ent.offset + ent.length]
                        })
                    elif isinstance(ent, MessageEntityMention):
                        entities.append({
                            "entity_type": "mention",
                            "entity_value": message.text[ent.offset: ent.offset + ent.length]
                        })

            # 🔎 Detect message type & build media link
            message_type = "text"
            media_file_path = None

            if message.photo:
                message_type = "photo"
            elif message.video:
                message_type = "video"
            elif message.document:
                message_type = "document"
            elif message.voice:
                message_type = "voice"
            elif message.audio:
                message_type = "audio"
            elif message.sticker:
                message_type = "sticker"

            # For public channels with username, build t.me link
            if channel.username:
                media_file_path = f"https://t.me/{channel.username}/{message.id}"

            payload = {
                "message": {
                    "telegram_id": message.id,
                    "message_type": message_type,
                    "content_text": message.text,
                    "media_file_path": media_file_path,
                    "views": message.views,
                    "forwards": message.forwards,
                    "replies_count": message.replies.replies if message.replies else 0,
                    "posted_at": str(message.date),
                },
                "channel": {
                    "telegram_id": channel.id,
                    "title": getattr(channel, "title", None),
                    "username": getattr(channel, "username", None),
                    "type": channel.__class__.__name__,
                    "is_private": False,
                    "is_adults": is_adults,  # ✅ send adult flag
                    "description": getattr(channel, "about", None) if hasattr(channel, "about") else None,
                    "members_count": getattr(channel, "participants_count", None)
                    if hasattr(channel, "participants_count") else None,
                    "photo_url": None
                },
                "sender": {
                    "telegram_id": message.sender_id or 0,
                    "username": getattr(message.sender, "username", None) if message.sender else None,
                    "display_name": getattr(message.sender, "first_name", None) if message.sender else None,
                    "is_bot": getattr(message.sender, "bot", False) if message.sender else False,
                    "photo_url": None
                },
                "entities": entities
            }
            batch.append(payload)

        # 🚀 Send to Laravel API
        if batch:
            headers = {"Authorization": f"Bearer {IMPORT_TOKEN}", "Content-Type": "application/json"}
            response = requests.post(LARAVEL_API, headers=headers, data=json.dumps(batch))
            print(f"✅ Sent {len(batch)} messages from {channel.title} (adults={is_adults})")
            try:
                print("Response from Laravel:", response.json())
            except Exception:
                print("Response from Laravel:", response.text)

            stats["public"]["channels"] += 1
            stats["public"]["messages"] += len(batch)

            last_ids[channel_username] = last_id
            save_last_ids(last_ids)
        else:
            print(f"⚠️ No new messages in {channel_username}")

    except Exception as e:
        print(f"❌ Error fetching {channel_username}: {e}")


async def main():
    for ch in CHANNELS:
        await fetch_and_send(ch)

    # 📊 Print final summary
    print("\n📊 Import Summary:")
    print(f"Public Channels: {stats['public']['channels']} | Messages: {stats['public']['messages']}")
    print("✅ Import completed!")


with client:
    client.loop.run_until_complete(main())
