# i lowk speedcoded ts at 5 am so if something breaks just dm xritura_01 on discord or xritura01 on telegram 
# Dont enter bot token . you need real user tokens for this to work . Token must be in both servers (you want to clone / where you want to clone to)
# Also make sure your account has admin permissions in server you want to clone in / paste in 
# put user token in data/token.txt file
# here is yt tutorial on how to get token : https://youtu.be/GUqSNoJ28aU?si=-J1QNKuS4wJDpkrz

import os
import sys
import time
import json
import base64
import shutil
import requests
import threading
import urllib3
import random 
import tls_client
from pystyle import Colorate, Colors
from discord import Permissions
from colorama import Fore, init, Style
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import SSLError

urllib3.disable_warnings()
init(autoreset=True)

def gradient_text_success(text, speed=1):
    return Colorate.Horizontal(Colors.green_to_white, text, speed)

def gradient_text_options(text: str, start_rgb=(100, 100, 100), end_rgb=(255, 255, 255)) -> str:
    length = len(text)
    result = ""

    for i, char in enumerate(text):
        if char == " ":
            result += char
            continue
        factor = i / max(length - 1, 1)
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * factor)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * factor)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * factor)
        result += f"\033[38;2;{r};{g};{b}m{char}"

    return result + Style.RESET_ALL

def gradient_text_failer(text, speed=1):
    return Colorate.Horizontal(Colors.red_to_white, text, speed)

def gradient_text_ascii(text, speed=1):
    return Colorate.Horizontal(Colors.purple_to_red, text, speed)

def safe_post(session, url, headers, json_data):
    tries = 0
    while tries < 3:
        try:
            return session.post(url, headers=headers, json=json_data)
        except Exception as e:
            print(gradient_text_failer(f"[ERROR] Retrying... ({e})"))
            tries += 1
            time.sleep(1.5)
    return None

class UtilityClonerFunctions:
    def __init__(self, token, source_guild_id, target_guild_id):
        self.token = token
        self.source_guild_id = source_guild_id
        self.target_guild_id = target_guild_id
        self.session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_ext=True
        )
        self.headers = self.get_headers()
        self.category_map = {}
        os.makedirs("backups", exist_ok=True)
# Just saying before hand if you try to use these headers for a joiner or something 
# These might work but wont be undetectable since they are made for a cloner and not a joiner so yeah dont do that
# i just made these for the cloner so they arent detailed much blah bah 
    def get_headers(self):
        build_num = random.randint(265000, 267000)
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        props = base64.b64encode(json.dumps({
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": ua,
            "browser_version": "120.0.0.0",
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": build_num,
            "client_event_source": None
        }).encode()).decode()

        return {
            "authority": "discord.com",
            "method": "GET",
            "path": "/api/v9/users/@me",
            "scheme": "https",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "authorization": self.token,
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": "https://discord.com/channels/@me",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": ua,
            "x-debug-options": "bugReporterEnabled",
            "x-discord-locale": "en-US",
            "x-discord-timezone": "America/New_York",
            "x-super-properties": props
        }

    def fetch_source_channels(self):
        url = f"https://discord.com/api/v9/guilds/{self.source_guild_id}/channels"
        r = self.session.get(url, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        else:
            print(gradient_text_failer(f"[x] Failed to fetch source channels: {r.text}"))
            return []

    def create_category_in_target(self, category):
        payload = {
            "name": category['name'],
            "type": 4,
            "position": category['position']
        }

        url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}/channels"
        r = safe_post(self.session, url, headers=self.headers, json_data=payload)

        if r.status_code == 201:
            new_cat_id = r.json()['id']
            self.category_map[category['id']] = new_cat_id
            print(gradient_text_success(f"[+] Created category: {category['name']}"))
        elif r.status_code == 429:
            print(gradient_text_failer("[RATELIMIT] Api is in mood clearly"))
            retry_after = r.json().get("retry_after", 1)
            time.sleep(retry_after + 0.5)
            self.create_category_in_target(category)
        else:
            print(gradient_text_failer(f"[x] Failed to create category {category['name']}: {r.text}"))

        time.sleep(0.10)

    def create_channel_in_target(self, channel):
        if channel['type'] == 4:
            return

        parent_id = self.category_map.get(channel.get('parent_id'))

        payload = {
            "name": channel['name'],
            "type": channel['type'],
            "topic": channel.get('topic'),
            "nsfw": channel.get('nsfw', False),
            "bitrate": channel.get('bitrate'),
            "user_limit": channel.get('user_limit'),
            "rate_limit_per_user": channel.get('rate_limit_per_user', 0),
            "position": channel['position'],
            "parent_id": parent_id
        }

        url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}/channels"
        r = self.session.post(url, headers=self.headers, json=payload)

        if r.status_code == 201:
            print(gradient_text_success(f"[+] Created channel: {channel['name']}"))
        elif r.status_code == 429:
            print(gradient_text_failer("[RATELIMIT] Api is in mood clearly"))
            retry_after = r.json().get("retry_after", 1)
            time.sleep(retry_after + 0.5)
            self.create_channel_in_target(channel)
        else:
            print(gradient_text_failer(f"[x] Failed to create channel {channel['name']}: {r.text}"))

        time.sleep(0.10)

    def clone_channels(self):
        channels = self.fetch_source_channels()
        if not channels:
            return

        categories = [c for c in channels if c["type"] == 4]
        others = [c for c in channels if c["type"] != 4]

        print(gradient_text_success(f"[~] Creating {len(categories)} categories first..."))
        for category in categories:
            self.create_category_in_target(category)

        print(gradient_text_success(f"[~] Creating {len(others)} channels with hierarchy..."))
        with ThreadPoolExecutor(max_workers=3) as executor:
            for channel in others:
                executor.submit(self.create_channel_in_target, channel)

    def clone_server_details(self):
        print(gradient_text_ascii("[~] Cloning server name and icon..."))

        url = f"https://discord.com/api/v9/guilds/{self.source_guild_id}"
        r = self.session.get(url, headers=self.headers)
        if r.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch source guild: {r.text}"))
            return

        guild = r.json()
        name = guild.get("name", "Cloned Server")
        icon_hash = guild.get("icon")

        icon_payload = None
        if icon_hash:
            icon_url = f"https://cdn.discordapp.com/icons/{self.source_guild_id}/{icon_hash}.png"
            try:
                icon_data = requests.get(icon_url).content
                icon_base64 = base64.b64encode(icon_data).decode("utf-8")
                icon_payload = f"data:image/png;base64,{icon_base64}"
            except Exception as e:
                print(gradient_text_failer(f"[x] Failed to fetch or encode icon: {e}"))

        payload = {"name": name}
        if icon_payload:
            payload["icon"] = icon_payload

        patch_url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}"
        r = self.session.patch(patch_url, headers=self.headers, json=payload)

        if r.status_code == 200:
            print(gradient_text_success(f"[✓] Server name and icon cloned successfully!"))
        else:
            print(gradient_text_failer(f"[x] Failed to update server: {r.text}"))

    def clone_roles(self):
        print(gradient_text_ascii("[~] Cloning roles with hierarchy and permissions..."))

        url = f"https://discord.com/api/v9/guilds/{self.source_guild_id}/roles"
        r = self.session.get(url, headers=self.headers)
        if r.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch source roles: {r.text}"))
            return

        roles = r.json()
        roles = sorted(roles, key=lambda x: x["position"], reverse=True)

        created_roles = []

        for role in roles:
            if role["name"] == "@everyone":
                continue

            payload = {
                "name": role["name"],
                "permissions": role["permissions"],
                "color": role["color"],
                "hoist": role["hoist"],
                "mentionable": role["mentionable"]
            }

            url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}/roles"
            r = self.session.post(url, headers=self.headers, json=payload)

            if r.status_code == 200 or r.status_code == 201:
                created = r.json()
                created_roles.append(created)
                print(gradient_text_success(f"[+] Created role: {role['name']}"))
            elif r.status_code == 429:
                print(gradient_text_failer("[RATELIMIT] Too fast. Retrying..."))
                retry_after = r.json().get("retry_after", 1)
                time.sleep(retry_after + 0.5)
                roles.insert(0, role) 
            else:
                print(gradient_text_failer(f"[x] Failed to create role {role['name']}: {r.text}"))

            time.sleep(0.25)

        if created_roles:
            patch_url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}/roles"
            role_positions = [{"id": r["id"], "position": r["position"]} for r in created_roles]
            r = self.session.patch(patch_url, headers=self.headers, json=role_positions)
            if r.status_code in [200, 204]:
                print(gradient_text_success("[✓] Role positions updated"))
            else:
                print(gradient_text_failer(f"[x] Failed to set role positions: {r.text}"))

    def clone_emojis(self):
        print(gradient_text_ascii("[~] Cloning emojis from source server..."))

        fetch_url = f"https://discord.com/api/v9/guilds/{self.source_guild_id}/emojis"
        r = self.session.get(fetch_url, headers=self.headers)
        if r.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch source emojis: {r.text}"))
            return

        emojis = r.json()
        if not emojis:
            print(gradient_text_failer("[x] No emojis found in source server"))
            return

        for emoji in emojis:
            emoji_name = emoji["name"]
            image_url = f"https://cdn.discordapp.com/emojis/{emoji['id']}.{'gif' if emoji['animated'] else 'png'}"

            try:
                img_data = requests.get(image_url).content
                b64_image = f"data:image/{'gif' if emoji['animated'] else 'png'};base64,{base64.b64encode(img_data).decode()}"
            except Exception as e:
                print(gradient_text_failer(f"[x] Failed to fetch emoji {emoji_name}: {e}"))
                continue

            payload = {
                "name": emoji_name,
                "image": b64_image
            }

            upload_url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}/emojis"
            r = self.session.post(upload_url, headers=self.headers, json=payload)

            if r.status_code in [200, 201]:
                print(gradient_text_success(f"[+] Cloned emoji: {emoji_name}"))
            elif r.status_code == 400 and "maximum number of emojis" in r.text.lower():
                print(gradient_text_failer("[x] No more emoji slots left! Stopping clone."))
                break
            elif r.status_code == 429:
                retry_after = r.json().get("retry_after", 1)
                print(gradient_text_failer("[RATELIMIT] Sleeping before retry..."))
                time.sleep(retry_after + 0.5)
                continue
            else:
                print(gradient_text_failer(f"[x] Failed to upload emoji {emoji_name}: {r.text}"))

            time.sleep(0.25)
            
    def create_backup(self):
        if not self.source_guild_id:
            print(gradient_text_failer("[x] No source guild ID provided"))
            return

        backup = {}
        guild_url = f"https://discord.com/api/v9/guilds/{self.source_guild_id}"
        r = self.session.get(guild_url, headers=self.headers)
        if r.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch guild: {r.text}"))
            return
        guild = r.json()
        icon_base64 = None
        if guild.get("icon"):
            icon_url = f"https://cdn.discordapp.com/icons/{self.source_guild_id}/{guild['icon']}.png"
            try:
                icon_data = requests.get(icon_url).content
                icon_base64 = f"data:image/png;base64,{base64.b64encode(icon_data).decode()}"
            except:
                pass
        backup["server_details"] = {
            "name": guild.get("name", "Cloned Server"),
            "icon": icon_base64
        }

        roles_url = f"{guild_url}/roles"
        r = self.session.get(roles_url, headers=self.headers)
        if r.status_code == 200:
            roles = [role for role in r.json() if role["name"] != "@everyone"]
            backup["roles"] = [{
                "name": role["name"],
                "permissions": role["permissions"],
                "color": role["color"],
                "hoist": role["hoist"],
                "mentionable": role["mentionable"],
                "position": role["position"]
            } for role in roles]
        else:
            backup["roles"] = []

        channels_url = f"{guild_url}/channels"
        r = self.session.get(channels_url, headers=self.headers)
        if r.status_code == 200:
            channels = r.json()
            backup["categories"] = [{
                "id": c["id"],
                "name": c["name"],
                "position": c["position"]
            } for c in channels if c["type"] == 4]

            backup["channels"] = [{
                "name": c["name"],
                "type": c["type"],
                "topic": c.get("topic"),
                "nsfw": c.get("nsfw", False),
                "bitrate": c.get("bitrate"),
                "user_limit": c.get("user_limit"),
                "rate_limit_per_user": c.get("rate_limit_per_user", 0),
                "position": c["position"],
                "parent_id": c.get("parent_id")
            } for c in channels if c["type"] != 4]
        else:
            backup["categories"], backup["channels"] = [], []

        emoji_url = f"{guild_url}/emojis"
        r = self.session.get(emoji_url, headers=self.headers)
        if r.status_code == 200:
            emojis = []
            for e in r.json():
                try:
                    img_url = f"https://cdn.discordapp.com/emojis/{e['id']}.{'gif' if e['animated'] else 'png'}"
                    img_data = requests.get(img_url).content
                    img_b64 = f"data:image/{'gif' if e['animated'] else 'png'};base64,{base64.b64encode(img_data).decode()}"
                    emojis.append({"name": e["name"], "image": img_b64})
                except:
                    pass
            backup["emojis"] = emojis
        else:
            backup["emojis"] = []

        backup_path = f"backups/{self.source_guild_id}.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(backup, f, indent=4)

        print(gradient_text_success(f"[✓] Backup saved to {backup_path}"))

    def restore_from_backup(self, backup_filename):
        backups_dir = "backups"
        backup_file_path = os.path.join(backups_dir, backup_filename)

        if not os.path.isfile(backup_file_path):
            print(gradient_text_failer(f"[x] Backup file not found: {backup_filename}"))
            return

        with open(backup_file_path, "r", encoding="utf-8") as f:
            backup = json.load(f)
        payload = {"name": backup["server_details"]["name"]}
        if backup["server_details"].get("icon"):
            payload["icon"] = backup["server_details"]["icon"]

        patch_url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}"
        r = self.session.patch(patch_url, headers=self.headers, json=payload)
        if r.status_code in [200, 201]:
            print(gradient_text_success("[✓] Server details restored"))
        else:
            print(gradient_text_failer(f"[x] Failed to restore server details: {r.text}"))

        for role in sorted(backup["roles"], key=lambda x: x["position"], reverse=True):
            r = self.session.post(
                f"https://discord.com/api/v9/guilds/{self.target_guild_id}/roles",
                headers=self.headers,
                json=role
            )
            if r.status_code in [200, 201]:
                print(gradient_text_success(f"[+] Role created: {role['name']}"))
            else:
                print(gradient_text_failer(f"[x] Failed to create role {role['name']}: {r.text}"))
            time.sleep(0.5)
        self.category_map = {}
        for cat in backup["categories"]:
            payload = {"name": cat["name"], "type": 4, "position": cat["position"]}
            r = self.session.post(
                f"https://discord.com/api/v9/guilds/{self.target_guild_id}/channels",
                headers=self.headers,
                json=payload
            )
            if r.status_code == 201:
                new_cat_id = r.json()["id"]
                self.category_map[cat["id"]] = new_cat_id
                print(gradient_text_success(f"[+] Category created: {cat['name']}"))
            else:
                print(gradient_text_failer(f"[x] Failed to create category {cat['name']}: {r.text}"))
            time.sleep(0.5)
        for ch in backup["channels"]:
            payload = ch.copy()
            if ch.get("parent_id") in self.category_map:
                payload["parent_id"] = self.category_map[ch["parent_id"]]
            r = self.session.post(
                f"https://discord.com/api/v9/guilds/{self.target_guild_id}/channels",
                headers=self.headers,
                json=payload
            )
            if r.status_code == 201:
                print(gradient_text_success(f"[+] Channel created: {ch['name']}"))
            else:
                print(gradient_text_failer(f"[x] Failed to create channel {ch['name']}: {r.text}"))
            time.sleep(0.5)
        for emoji in backup["emojis"]:
            r = self.session.post(
                f"https://discord.com/api/v9/guilds/{self.target_guild_id}/emojis",
                headers=self.headers,
                json=emoji
            )
            if r.status_code in [200, 201]:
                print(gradient_text_success(f"[+] Emoji restored: {emoji['name']}"))
            elif r.status_code == 400 and "maximum number" in r.text.lower():
                print(gradient_text_failer("[x] Emoji slots full!"))
                break
            else:
                print(gradient_text_failer(f"[x] Failed to restore emoji {emoji['name']}: {r.text}"))
            time.sleep(0.5)

        print(gradient_text_success("[✓] Backup restoration complete"))

    def clone_nsfw_flags(self):
        src_url = f"https://discord.com/api/v9/guilds/{self.source_guild_id}/channels"
        tgt_url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}/channels"

        r = self.session.get(src_url, headers=self.headers)
        if r.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch source channels: {r.text}"))
            return

        source_channels = r.json()
        tr = self.session.get(tgt_url, headers=self.headers)
        if tr.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch target channels: {tr.text}"))
            return

        target_channels = tr.json()
        name_map = {ch['name']: ch['id'] for ch in target_channels}

        for src_ch in source_channels:
            if src_ch.get('nsfw') is not None:
                tgt_id = name_map.get(src_ch['name'])
                if tgt_id:
                    patch_data = {"nsfw": src_ch['nsfw']}
                    pr = self.session.patch(f"{tgt_url}/{tgt_id}", headers=self.headers, json=patch_data)
                    if pr.status_code == 200:
                        print(gradient_text_success(f"[✓] Set NSFW flag for: {src_ch['name']}"))
                    else:
                        print(gradient_text_failer(f"[x] Failed to set NSFW for {src_ch['name']}: {pr.text}"))
                    time.sleep(1.5)

    def clone_webhooks(self):
        src_channels_url = f"https://discord.com/api/v9/guilds/{self.source_guild_id}/channels"
        tgt_channels_url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}/channels"

        src_ch_resp = self.session.get(src_channels_url, headers=self.headers)
        if src_ch_resp.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch source channels: {src_ch_resp.text}"))
            return

        tgt_ch_resp = self.session.get(tgt_channels_url, headers=self.headers)
        if tgt_ch_resp.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch target channels: {tgt_ch_resp.text}"))
            return

        source_channels = src_ch_resp.json()
        target_channels = tgt_ch_resp.json()
        tgt_name_map = {ch['name']: ch['id'] for ch in target_channels}

        for src_ch in source_channels:
            ch_id = src_ch['id']
            ch_name = src_ch['name']
            wh_resp = self.session.get(f"https://discord.com/api/v9/channels/{ch_id}/webhooks", headers=self.headers)
            if wh_resp.status_code != 200:
                continue
            webhooks = wh_resp.json()
            for wh in webhooks:
                target_ch_id = tgt_name_map.get(ch_name)
                if target_ch_id:
                    data = {
                        "name": wh['name'],
                        "avatar": wh.get('avatar'),
                    }
                    cr = self.session.post(f"https://discord.com/api/v9/channels/{target_ch_id}/webhooks",
                                    headers=self.headers, json=data)
                    if cr.status_code == 200:
                        print(gradient_text_success(f"[✓] Cloned webhook '{wh['name']}' in {ch_name}"))
                    else:
                        print(gradient_text_failer(f"[x] Failed to clone webhook '{wh['name']}': {cr.text}"))
                    time.sleep(1.5)

    def clone_stickers(self):
        print(gradient_text_ascii("[~] Cloning stickers..."))

        url = f"https://discord.com/api/v9/guilds/{self.source_guild_id}/stickers"
        r = self.session.get(url, headers=self.headers)
        if r.status_code != 200:
            print(gradient_text_failer(f"[x] Failed to fetch source stickers: {r.text}"))
            return

        stickers = r.json()
        if not stickers:
            print(gradient_text_failer("[~] No stickers found in source server."))
            return

        for sticker in stickers:
            try:
                name = sticker.get("name", "sticker")
                description = sticker.get("description", "")
                tags = sticker.get("tags", "")

                sticker_url = f"https://cdn.discordapp.com/stickers/{sticker['id']}.png"
                if sticker.get("format_type") == 2:  
                    sticker_url = f"https://cdn.discordapp.com/stickers/{sticker['id']}.png"
                elif sticker.get("format_type") == 3: 
                    sticker_url = f"https://cdn.discordapp.com/stickers/{sticker['id']}.json"

                sticker_data = requests.get(sticker_url).content
                file_base64 = base64.b64encode(sticker_data).decode("utf-8")

                payload = {
                    "name": name,
                    "description": description,
                    "tags": tags,
                    "file": f"data:image/png;base64,{file_base64}"
                }

                create_url = f"https://discord.com/api/v9/guilds/{self.target_guild_id}/stickers"
                resp = self.session.post(create_url, headers=self.headers, json=payload)

                if resp.status_code == 201:
                    print(gradient_text_success(f"[+] Cloned sticker: {name}"))
                elif resp.status_code == 429:
                    print(gradient_text_failer("[RATELIMIT] API is in mood clearly"))
                    retry_after = resp.json().get("retry_after", 1)
                    time.sleep(retry_after + 0.5)
                    self.clone_stickers()  
                    return
                else:
                    error_json = resp.json()
                    if error_json.get("code") == 30039:
                        print(gradient_text_failer("[x] All sticker slots are already filled in the target server!"))
                        return
                    else:
                        print(gradient_text_failer(f"[x] Failed to create sticker {name}: {resp.text}"))

                time.sleep(1.0) 

            except Exception as e:
                print(gradient_text_failer(f"[x] Error cloning sticker: {e}"))



class UtilityClonerMenu:
    def __init__(self):
        self.size = shutil.get_terminal_size().columns
        self.clear()
        self.render_ascii()
        self.main_menu()

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def render_ascii(self):
        ascii_art = "\n".join([
            ' ____ ___          _________   .__                            ____   ____________  ',
            '|    |   \\         \\_   ___ \\  |  |   ____   ____   __________\\   \\ /   /\\_____  \\ ',
            '|    |   /  ______ /    \\  \\/  |  |  /  _ \\ /    \\_/ __ \\_  __ \\   Y   /  /  ____/ ',
            '|    |  /  /_____/ \\     \\____ |  |_(  <_> )   |  \\  ___/|  | \\/\\     /  /       \\ ',
            '|______/            \\______  / |____/\\____/|___|  /\\___  >__|   \\\___/   \\__ _____\\',
            '                           \\/                   \\/     \\/                        \\/',
            '',
            ''
        ])
        for line in ascii_art.splitlines():
            print(gradient_text_ascii(line.center(self.size)))

    def cloner_options(self):
        options_block = f"""

{'   || 1  || ~ Clone Server Name&Logo    || 2  || ~ Clone Roles       '.center(self.size)}
{'   || 3  || ~ Clone Emojis              || 4  || ~ Clone Categories  '.center(self.size)}
{'   || 5  || ~ Clone Channels            || 6  || ~ CReate A Backup   '.center(self.size)}
{'   || 7  || ~ Clone NSFW Flags          || 8  || ~ Clone Stickers    '.center(self.size)}
{'   || 9  || ~ Clone Webhooks            || 10 || ~ Discord&Credits   '.center(self.size)}
{'---------------------------------------------------------------------'.center(self.size)}
{'||*|| ~ FULL CLONE           ||$|| ~ Call A Backup '.center(self.size)}
"""
        for line in options_block.splitlines():
            print(gradient_text_options(line))

    def show_credits(self):
        credits = [
            "Discord ~ discord.gg/utilitytools",
            "Owner & Dev ~ xritura01",
            "Ui ~ resil1x",
            "Thank you for using our script",
            "Hope you have a nice day!"
        ]
        print("\n")
        for line in credits:
            print(gradient_text_ascii(line.center(self.size)))
        print("\n" * 2)
        input(gradient_text_ascii("Press Enter to return..."))

    def main_menu(self):
        while True:
            self.clear()
            self.render_ascii()
            self.cloner_options()
            choice = input(gradient_text_ascii("\n ~ ")).strip()

            if choice == "1":

                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                    cloner.clone_server_details()
                    input(gradient_text_ascii("\n[✓] Cloning complete. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "2":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                    cloner.clone_roles()
                    input(gradient_text_ascii("\n[✓] Roles cloned. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "3":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                    cloner.clone_emojis()
                    input(gradient_text_ascii("\n[✓] Emoji cloning complete. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "4":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                    channels = cloner.fetch_source_channels()
                    categories = [c for c in channels if c["type"] == 4]
                    for category in categories:
                        cloner.create_category_in_target(category)
                    input(gradient_text_ascii("\n[✓] Categories cloned. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "5":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                    cloner.clone_channels()
                    input(gradient_text_ascii("\n[✓] Cloning complete. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "6":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, None)
                    cloner.create_backup()
                    input(gradient_text_ascii("\n[✓] Backup created. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "7":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                    cloner.clone_nsfw_flags()
                    input(gradient_text_ascii("\n[✓] NSFW flags cloned. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "8":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                    cloner.clone_stickers()
                    input(gradient_text_ascii("\n[✓] Sticker cloning complete. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "9":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                    cloner.clone_webhooks()
                    input(gradient_text_ascii("\n[✓] Webhooks cloned. Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "10":
                self.clear()
                self.render_ascii()
                self.show_credits()

            elif choice == "*":
                try:
                    with open("data/token.txt", "r") as f:
                        token = f.read().strip()
                    source_id = input(gradient_text_ascii("Enter Source Guild ID ~ ")).strip()
                    target_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                    
                    confirm = input(gradient_text_failer("WARNING: This will overwrite server! Continue? (y/n) ")).lower()
                    if confirm != 'y':
                        continue
                        
                    cloner = UtilityClonerFunctions(token, source_id, target_id)
                                 
                    cloner.clone_server_details()
                    cloner.clone_channels()
                    cloner.clone_roles()
                    cloner.clone_stickers()
                    cloner.clone_emojis()
                    cloner.clone_nsfw_flags()
                    cloner.clone_webhooks()
                    
                    input(gradient_text_ascii("\n[✓] FULL CLONE complete! Press Enter to return..."))
                except Exception as e:
                    print(gradient_text_failer(f"[x] Error: {e}"))
                    input(gradient_text_ascii("\nPress Enter to return..."))

            elif choice == "$":
                backups = [f for f in os.listdir("backups") if f.endswith(".json")]
                if not backups:
                    print(gradient_text_failer("[x] No backups found"))
                else:
                    print(gradient_text_ascii("[~] Available Backups:"))
                    for i, backup in enumerate(backups, 1):
                        print(f"{i}. {backup}")

                    try:
                        backup_num = int(input(gradient_text_ascii("Select backup number ~ ")).strip())
                        if not (1 <= backup_num <= len(backups)):
                            print(gradient_text_failer("[x] Invalid backup number"))
                        else:
                            target_guild_id = input(gradient_text_ascii("Enter Target Guild ID ~ ")).strip()
                            
                            confirm = input(gradient_text_failer("WARNING: This will overwrite server! Continue? (y/n) ")).lower()
                            if confirm != 'y':
                                continue
                                
                            with open("data/token.txt", "r") as f:
                                token = f.read().strip()
               
                            cloner = UtilityClonerFunctions(
                                token=token,
                                source_guild_id=None,
                                target_guild_id=target_guild_id
                            )
                            cloner.restore_from_backup(backups[backup_num - 1])
                    except ValueError:
                        print(gradient_text_failer("[x] Please enter a valid number"))

                input(gradient_text_success("[✓] Press Enter to return..."))

            else:
                print(gradient_text_ascii(f"\n[!] Invalid option: {choice}"))
                input(gradient_text_ascii("Press Enter to return..."))

if __name__ == "__main__":
    UtilityClonerMenu()
