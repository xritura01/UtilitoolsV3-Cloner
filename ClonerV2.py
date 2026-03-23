import os
import re
import sys
import time
import json
import base64
import shutil
import requests
import urllib3
import tls_client
from os import get_terminal_size
from pystyle import Colorate, Colors
from colorama import Fore, init, Style
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings()
init(autoreset=True)

def gradient_text(text):
    return Colorate.Horizontal(Colors.green_to_cyan, text, 1)

def get_time():
    return time.strftime("%H:%M:%S")

def clear():
    os.system("cls" if os.name == "nt" else "clear")


class UtilityLogger:
    def __init__(self):
        self._o = gradient_text("[")
        self._c = gradient_text("]")
        self._arrow = gradient_text("~>")

    def _bracket(self, inner):
        return f"{self._o} {inner} {self._c}"

    def _time_b(self):
        return self._bracket(f"{Fore.WHITE}{get_time()}{Style.RESET_ALL}")

    def _brand_b(self):
        return self._bracket(f"{Fore.WHITE}UtilityToolsV2{Style.RESET_ALL}")

    def success(self, text, detail=None):
        sym = f"{Fore.GREEN} + {Style.RESET_ALL}"
        status = f"{Fore.LIGHTGREEN_EX}Action was Successful{Style.RESET_ALL}"
        det = f" {Fore.WHITE}| {Fore.LIGHTGREEN_EX}{detail}{Style.RESET_ALL}" if detail else ""
        print(f"      {self._time_b()} {sym} {Fore.WHITE}{text}{Style.RESET_ALL}{det} {self._arrow} {status}")

    def error(self, text, detail=None):
        sym = f"{Fore.RED} ! {Style.RESET_ALL}"
        status = f"{Fore.LIGHTRED_EX}Action Failed{Style.RESET_ALL}"
        det = f" {Fore.WHITE}| {Fore.LIGHTRED_EX}{detail}{Style.RESET_ALL}" if detail else ""
        print(f"      {self._time_b()} {sym} {Fore.WHITE}{text}{Style.RESET_ALL}{det} {self._arrow} {status}")

    def info(self, text, detail=None):
        sym = f"{Fore.CYAN} * {Style.RESET_ALL}"
        det = f" {Fore.WHITE}| {Fore.LIGHTCYAN_EX}{detail}{Style.RESET_ALL}" if detail else ""
        print(f"      {self._time_b()} {sym} {Fore.WHITE}{text}{Style.RESET_ALL}{det}")

    def clone(self, kind, name, response):
        sym = f"{Fore.CYAN} * {Style.RESET_ALL}"
        print(
            f"      {self._time_b()} {sym} "
            f"{Fore.LIGHTCYAN_EX}{kind}{Style.RESET_ALL} {self._arrow} "
            f"{Fore.WHITE}{name}{Style.RESET_ALL} "
            f"{Fore.WHITE}|{Style.RESET_ALL} "
            f"{Fore.GREEN}{response}{Style.RESET_ALL} cloned"
        )

    def ratelimit(self, seconds):
        sym = f"{Fore.YELLOW} ~ {Style.RESET_ALL}"
        print(f"      {self._time_b()} {sym} {Fore.YELLOW}Rate limited — sleeping {seconds:.1f}s{Style.RESET_ALL}")

    def input(self, text_label=None):
        txt = f"{Fore.WHITE}{text_label}{Style.RESET_ALL} " if text_label else ""
        return input(f"      {self._brand_b()} {txt}{self._arrow} ").strip()

    def confirm(self, text_label=None):
        choices = f"{Fore.WHITE}({Fore.GREEN}y{Fore.WHITE}/{Fore.RED}n{Fore.WHITE}){Style.RESET_ALL}"
        txt = f"{Fore.WHITE}{text_label}{Style.RESET_ALL} " if text_label else ""
        return input(f"      {self._brand_b()} {txt}{choices} {self._arrow} ").strip().lower() == "y"

    def wait(self):
        input(f"      {self._brand_b()} {Fore.WHITE}Press Enter to return...{Style.RESET_ALL} {self._arrow} ")


log = UtilityLogger()


def set_title(title):
    if os.name == "nt":
        os.system(f"title {title}")
    else:
        sys.stdout.write(f"\033]0;{title}\007")
        sys.stdout.flush()


def validate_token(token):
    try:
        r = requests.get(
            "https://discord.com/api/v9/users/@me",
            headers={"Authorization": token},
            timeout=8
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def load_or_prompt_token():
    os.makedirs("data", exist_ok=True)
    token_path = "data/token.txt"

    if os.path.isfile(token_path):
        with open(token_path, "r") as f:
            token = f.read().strip()
        if token:
            log.info("Token found, validating...")
            user = validate_token(token)
            if user:
                return token, user
            log.error("Saved token is invalid or expired")

    while True:
        print()
        token = log.input("Enter your Discord token")
        if not token:
            log.error("Token cannot be empty")
            continue
        log.info("Validating token...")
        user = validate_token(token)
        if user:
            with open(token_path, "w") as f:
                f.write(token)
            log.success("Token saved to data/token.txt")
            return token, user
        log.error("Invalid token", detail="Check the token and try again")


def safe_request(fn, *args, retries=3, **kwargs):
    for _ in range(retries):
        try:
            r = fn(*args, **kwargs)
            if r.status_code == 429:
                wait = r.json().get("retry_after", 1) + 0.5
                log.ratelimit(wait)
                time.sleep(wait)
                continue
            return r
        except Exception as e:
            log.error("Request failed", detail=str(e))
            time.sleep(1.5)
    return None


class UtilityClonerFunctions:
    def __init__(self, token, source_guild_id, target_guild_id):
        self.token = token
        self.source_guild_id = source_guild_id
        self.target_guild_id = target_guild_id
        self.session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True,
            ja3_string="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0",
            h2_settings={
                "HEADER_TABLE_SIZE": 65536,
                "MAX_CONCURRENT_STREAMS": 1000,
                "INITIAL_WINDOW_SIZE": 6291456,
                "MAX_FRAME_SIZE": 16384,
                "MAX_HEADER_LIST_SIZE": 262144
            },
            h2_settings_order=[
                "HEADER_TABLE_SIZE", "MAX_CONCURRENT_STREAMS",
                "INITIAL_WINDOW_SIZE", "MAX_FRAME_SIZE", "MAX_HEADER_LIST_SIZE"
            ],
            supported_signature_algorithms=[
                "ECDSAWithP256AndSHA256", "PSSWithSHA256", "PKCS1WithSHA256",
                "ECDSAWithP384AndSHA384", "PSSWithSHA384", "PKCS1WithSHA384",
                "PSSWithSHA512", "PKCS1WithSHA512"
            ],
            supported_versions=["GREASE", "1.3", "1.2"],
            key_share_curves=["GREASE", "X25519"],
            cert_compression_algo="brotli",
            pseudo_header_order=[":method", ":authority", ":scheme", ":path"],
            connection_flow=15663105
        )
        self.session.headers = self._get_headers()
        self.category_map = {}
        os.makedirs("backups", exist_ok=True)

    def _build_super_props(self):
        return {
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "browser_version": "120.0.0.0",
            "os_version": "10",
            "referrer": "https://discord.com/",
            "referring_domain": "discord.com",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 267860,
            "client_event_source": None,
            "design_id": 0,
            "native_build_number": None,
            "client_performance_cpu_cores": 8,
            "client_performance_memory": 16384,
            "accessibility_features": 0,
            "has_ever_used_accessibility_features": False,
            "has_client_mods": False
        }

    def _get_headers(self):
        encoded = base64.b64encode(
            json.dumps(self._build_super_props(), separators=(",", ":")).encode()
        ).decode()
        return {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "authorization": self.token,
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": f"https://discord.com/channels/{self.source_guild_id}/@home",
            "sec-ch-ua": '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-locale": "en-US",
            "x-discord-timezone": "America/New_York",
            "x-super-properties": encoded
        }

    def _get(self, path):
        return safe_request(self.session.get, f"https://discord.com/api/v9{path}")

    def _post(self, path, payload):
        return safe_request(self.session.post, f"https://discord.com/api/v9{path}", json=payload)

    def _patch(self, path, payload):
        return safe_request(self.session.patch, f"https://discord.com/api/v9{path}", json=payload)

    def fetch_source_channels(self):
        r = self._get(f"/guilds/{self.source_guild_id}/channels")
        if r and r.status_code == 200:
            return r.json()
        log.error("Fetch source channels", detail=r.text if r else "no response")
        return []

    def create_category_in_target(self, category):
        r = self._post(f"/guilds/{self.target_guild_id}/channels", {
            "name": category["name"], "type": 4, "position": category["position"]
        })
        if r and r.status_code == 201:
            self.category_map[category["id"]] = r.json()["id"]
            log.clone("Category", category["name"], 201)
        else:
            log.error(f"Category {category['name']}", detail=r.text if r else "no response")
        time.sleep(0.10)

    def create_channel_in_target(self, channel):
        if channel["type"] == 4:
            return
        r = self._post(f"/guilds/{self.target_guild_id}/channels", {
            "name": channel["name"],
            "type": channel["type"],
            "topic": channel.get("topic"),
            "nsfw": channel.get("nsfw", False),
            "bitrate": channel.get("bitrate"),
            "user_limit": channel.get("user_limit"),
            "rate_limit_per_user": channel.get("rate_limit_per_user", 0),
            "position": channel["position"],
            "parent_id": self.category_map.get(channel.get("parent_id"))
        })
        if r and r.status_code == 201:
            log.clone("Channel", channel["name"], 201)
        else:
            log.error(f"Channel {channel['name']}", detail=r.text if r else "no response")
        time.sleep(0.10)

    def clone_channels(self):
        channels = self.fetch_source_channels()
        if not channels:
            return
        categories = sorted([c for c in channels if c["type"] == 4], key=lambda x: x["position"])
        others = sorted([c for c in channels if c["type"] != 4], key=lambda x: x["position"])
        log.info(f"Creating {len(categories)} categories")
        for cat in categories:
            self.create_category_in_target(cat)
        log.info(f"Creating {len(others)} channels")
        with ThreadPoolExecutor(max_workers=1) as ex:
            for ch in others:
                ex.submit(self.create_channel_in_target, ch)

    def clone_server_details(self):
        log.info("Cloning server name and icon")
        r = self._get(f"/guilds/{self.source_guild_id}")
        if not r or r.status_code != 200:
            log.error("Fetch source guild", detail=r.text if r else "no response")
            return
        guild = r.json()
        payload = {"name": guild.get("name", "Cloned Server")}
        if guild.get("icon"):
            try:
                data = requests.get(
                    f"https://cdn.discordapp.com/icons/{self.source_guild_id}/{guild['icon']}.png"
                ).content
                payload["icon"] = f"data:image/png;base64,{base64.b64encode(data).decode()}"
            except Exception as e:
                log.error("Fetch icon", detail=str(e))
        r = self._patch(f"/guilds/{self.target_guild_id}", payload)
        if r and r.status_code == 200:
            log.clone("Server", guild.get("name", "?"), 200)
        else:
            log.error("Update server details", detail=r.text if r else "no response")

    def clone_roles(self):
        log.info("Cloning roles")
        r = self._get(f"/guilds/{self.source_guild_id}/roles")
        if not r or r.status_code != 200:
            log.error("Fetch source roles", detail=r.text if r else "no response")
            return
        roles = sorted([ro for ro in r.json() if ro["name"] != "@everyone"], key=lambda x: x["position"], reverse=True)
        created = []
        for role in roles:
            r = self._post(f"/guilds/{self.target_guild_id}/roles", {
                "name": role["name"], "permissions": role["permissions"],
                "color": role["color"], "hoist": role["hoist"], "mentionable": role["mentionable"]
            })
            if r and r.status_code in [200, 201]:
                created.append(r.json())
                log.clone("Role", role["name"], r.status_code)
            else:
                log.error(f"Role {role['name']}", detail=r.text if r else "no response")
            time.sleep(0.25)
        if created:
            r = self._patch(f"/guilds/{self.target_guild_id}/roles",
                            [{"id": ro["id"], "position": ro["position"]} for ro in created])
            if r and r.status_code in [200, 204]:
                log.success("Role positions updated")

    def clone_emojis(self):
        log.info("Cloning emojis")
        r = self._get(f"/guilds/{self.source_guild_id}/emojis")
        if not r or r.status_code != 200:
            log.error("Fetch source emojis", detail=r.text if r else "no response")
            return
        for emoji in r.json():
            ext = "gif" if emoji["animated"] else "png"
            try:
                data = requests.get(f"https://cdn.discordapp.com/emojis/{emoji['id']}.{ext}").content
                b64 = f"data:image/{ext};base64,{base64.b64encode(data).decode()}"
            except Exception as e:
                log.error(f"Fetch emoji {emoji['name']}", detail=str(e))
                continue
            r2 = self._post(f"/guilds/{self.target_guild_id}/emojis", {"name": emoji["name"], "image": b64})
            if r2 and r2.status_code in [200, 201]:
                log.clone("Emoji", emoji["name"], r2.status_code)
            elif r2 and r2.status_code == 400 and "maximum number of emojis" in r2.text.lower():
                log.error("Emoji slots full — stopping")
                break
            else:
                log.error(f"Upload emoji {emoji['name']}", detail=r2.text if r2 else "no response")
            time.sleep(0.25)

    def clone_stickers(self):
        log.info("Cloning stickers")
        r = self._get(f"/guilds/{self.source_guild_id}/stickers")
        if not r or r.status_code != 200:
            log.error("Fetch source stickers", detail=r.text if r else "no response")
            return
        for sticker in r.json():
            name = sticker.get("name", "sticker")
            ext = "json" if sticker.get("format_type") == 3 else "png"
            try:
                data = requests.get(f"https://cdn.discordapp.com/stickers/{sticker['id']}.{ext}").content
                b64 = f"data:image/png;base64,{base64.b64encode(data).decode()}"
            except Exception as e:
                log.error(f"Fetch sticker {name}", detail=str(e))
                continue
            r2 = self._post(f"/guilds/{self.target_guild_id}/stickers", {
                "name": name, "description": sticker.get("description", ""),
                "tags": sticker.get("tags", ""), "file": b64
            })
            if r2 and r2.status_code == 201:
                log.clone("Sticker", name, 201)
            elif r2 and r2.json().get("code") == 30039:
                log.error("Sticker slots full — stopping")
                return
            else:
                log.error(f"Upload sticker {name}", detail=r2.text if r2 else "no response")
            time.sleep(1.0)

    def clone_nsfw_flags(self):
        log.info("Cloning NSFW flags")
        src = self._get(f"/guilds/{self.source_guild_id}/channels")
        tgt = self._get(f"/guilds/{self.target_guild_id}/channels")
        if not src or src.status_code != 200 or not tgt or tgt.status_code != 200:
            log.error("Fetch channels for NSFW clone")
            return
        name_map = {ch["name"]: ch["id"] for ch in tgt.json()}
        for ch in src.json():
            tgt_id = name_map.get(ch["name"])
            if tgt_id and ch.get("nsfw") is not None:
                r = self._patch(f"/channels/{tgt_id}", {"nsfw": ch["nsfw"]})
                if r and r.status_code == 200:
                    log.clone("NSFW", ch["name"], 200)
                else:
                    log.error(f"NSFW {ch['name']}", detail=r.text if r else "no response")
                time.sleep(1.5)

    def clone_webhooks(self):
        log.info("Cloning webhooks")
        src = self._get(f"/guilds/{self.source_guild_id}/channels")
        tgt = self._get(f"/guilds/{self.target_guild_id}/channels")
        if not src or src.status_code != 200 or not tgt or tgt.status_code != 200:
            log.error("Fetch channels for webhook clone")
            return
        name_map = {ch["name"]: ch["id"] for ch in tgt.json()}
        for ch in src.json():
            wh_r = self._get(f"/channels/{ch['id']}/webhooks")
            if not wh_r or wh_r.status_code != 200:
                continue
            for wh in wh_r.json():
                tgt_id = name_map.get(ch["name"])
                if tgt_id:
                    r = self._post(f"/channels/{tgt_id}/webhooks", {"name": wh["name"], "avatar": wh.get("avatar")})
                    if r and r.status_code == 200:
                        log.clone("Webhook", wh["name"], 200)
                    else:
                        log.error(f"Webhook {wh['name']}", detail=r.text if r else "no response")
                    time.sleep(1.5)

    def create_backup(self):
        log.info(f"Creating backup for {self.source_guild_id}")
        r = self._get(f"/guilds/{self.source_guild_id}")
        if not r or r.status_code != 200:
            log.error("Fetch guild for backup", detail=r.text if r else "no response")
            return
        guild = r.json()
        backup = {}
        icon_b64 = None
        if guild.get("icon"):
            try:
                data = requests.get(
                    f"https://cdn.discordapp.com/icons/{self.source_guild_id}/{guild['icon']}.png"
                ).content
                icon_b64 = f"data:image/png;base64,{base64.b64encode(data).decode()}"
            except:
                pass
        backup["server_details"] = {"name": guild.get("name", "Cloned Server"), "icon": icon_b64}

        r = self._get(f"/guilds/{self.source_guild_id}/roles")
        backup["roles"] = [
            {k: ro[k] for k in ["name", "permissions", "color", "hoist", "mentionable", "position"]}
            for ro in (r.json() if r and r.status_code == 200 else [])
            if ro["name"] != "@everyone"
        ]

        r = self._get(f"/guilds/{self.source_guild_id}/channels")
        channels = r.json() if r and r.status_code == 200 else []
        backup["categories"] = [{"id": c["id"], "name": c["name"], "position": c["position"]} for c in channels if c["type"] == 4]
        backup["channels"] = [{
            "name": c["name"], "type": c["type"], "topic": c.get("topic"),
            "nsfw": c.get("nsfw", False), "bitrate": c.get("bitrate"),
            "user_limit": c.get("user_limit"), "rate_limit_per_user": c.get("rate_limit_per_user", 0),
            "position": c["position"], "parent_id": c.get("parent_id")
        } for c in channels if c["type"] != 4]

        r = self._get(f"/guilds/{self.source_guild_id}/emojis")
        emojis = []
        for e in (r.json() if r and r.status_code == 200 else []):
            try:
                ext = "gif" if e["animated"] else "png"
                data = requests.get(f"https://cdn.discordapp.com/emojis/{e['id']}.{ext}").content
                emojis.append({"name": e["name"], "image": f"data:image/{ext};base64,{base64.b64encode(data).decode()}"})
            except:
                pass
        backup["emojis"] = emojis

        path = f"backups/{self.source_guild_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(backup, f, indent=4)
        log.success("Backup saved", detail=path)

    def restore_from_backup(self, filename):
        path = os.path.join("backups", filename)
        if not os.path.isfile(path):
            log.error("Backup file not found", detail=filename)
            return
        with open(path, "r", encoding="utf-8") as f:
            backup = json.load(f)
        payload = {"name": backup["server_details"]["name"]}
        if backup["server_details"].get("icon"):
            payload["icon"] = backup["server_details"]["icon"]
        r = self._patch(f"/guilds/{self.target_guild_id}", payload)
        if r and r.status_code in [200, 201]:
            log.success("Server details restored")
        else:
            log.error("Restore server details", detail=r.text if r else "no response")
        for role in sorted(backup["roles"], key=lambda x: x["position"], reverse=True):
            r = self._post(f"/guilds/{self.target_guild_id}/roles", role)
            if r and r.status_code in [200, 201]:
                log.clone("Role", role["name"], r.status_code)
            else:
                log.error(f"Restore role {role['name']}", detail=r.text if r else "no response")
            time.sleep(0.5)
        self.category_map = {}
        for cat in backup["categories"]:
            r = self._post(f"/guilds/{self.target_guild_id}/channels", {"name": cat["name"], "type": 4, "position": cat["position"]})
            if r and r.status_code == 201:
                self.category_map[cat["id"]] = r.json()["id"]
                log.clone("Category", cat["name"], 201)
            else:
                log.error(f"Restore category {cat['name']}", detail=r.text if r else "no response")
            time.sleep(0.5)
        for ch in backup["channels"]:
            payload = ch.copy()
            if ch.get("parent_id") in self.category_map:
                payload["parent_id"] = self.category_map[ch["parent_id"]]
            r = self._post(f"/guilds/{self.target_guild_id}/channels", payload)
            if r and r.status_code == 201:
                log.clone("Channel", ch["name"], 201)
            else:
                log.error(f"Restore channel {ch['name']}", detail=r.text if r else "no response")
            time.sleep(0.5)
        for emoji in backup["emojis"]:
            r = self._post(f"/guilds/{self.target_guild_id}/emojis", emoji)
            if r and r.status_code in [200, 201]:
                log.clone("Emoji", emoji["name"], r.status_code)
            elif r and r.status_code == 400 and "maximum number" in r.text.lower():
                log.error("Emoji slots full — stopping")
                break
            else:
                log.error(f"Restore emoji {emoji['name']}", detail=r.text if r else "no response")
            time.sleep(0.5)
        log.success("Backup restoration complete")


class UtilityClonerMenu:
    def __init__(self):
        self.size = get_terminal_size().columns
        self.current_page = 1
        self.total_pages = 2
        self.token = None
        self.username = None
        self.pages_content = {
            1: [
                (" 1", "Server Name&Logo", " 2", "Clone Roles",      " 3", "Clone Emojis"),
                (" 4", "Clone Categories", " 5", "Clone Channels",   " 6", "Create Backup"),
                (" 7", "NSFW Flags",       " 8", "Clone Stickers",   " 9", "Clone Webhooks"),
                ("10", "Discord&Credits",  " *", "Full Clone",       " $", "Restore Backup"),
            ],
            2: [
                ("nigger")
            ]
        }
        self._authenticate()
        self.main_menu()

    def _authenticate(self):
        clear()
        self._print_banner()
        print()
        self.token, user = load_or_prompt_token()
        tag = user.get("username") or user.get("global_name") or "Unknown"
        discrim = user.get("discriminator", "0")
        self.username = f"{tag}#{discrim}" if discrim != "0" else tag
        set_title(f"UtilityToolsV2 | ClonerV3 | Logged in as {self.username}")
        log.success(f"Logged in as {self.username}")
        time.sleep(0.8)

    def _print_banner(self):
        banner = r"""
  __  ____  _ ___ __       _______                       ____
 / / / / /_(_) (_) /___ __/ ___/ /__  ___  ___ _____  __|_  /
/ /_/ / __/ / / / __/ // / /__/ / _ \/ _ \/ -_) __/ |/ //_ < 
\____/\__/_/_/_/\__/\_, /\___/_/\___/_//_/\__/_/  |___/____/ 
                   /___/                                     
"""
        for line in banner.splitlines():
            print(gradient_text(line.center(self.size)))

    def get_visible_length(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return len(ansi_escape.sub('', text))

    def center_text(self, text):
        visible_len = self.get_visible_length(text)
        padding = max(0, (self.size - visible_len) // 2)
        return " " * padding + text

    def pad_visible(self, text, width):
        return text + (" " * max(0, width - self.get_visible_length(text)))

    def format_option(self, num, label):
        return f"{Fore.WHITE}{num}{Style.RESET_ALL}{gradient_text(' ~>')} {Fore.LIGHTCYAN_EX}{label}{Style.RESET_ALL}"

    def format_row(self, n1, l1, n2, l2, n3, l3):
        col_w = 32
        c1 = self.pad_visible(self.format_option(n1, l1) if n1.strip() else "", col_w)
        c2 = self.pad_visible(self.format_option(n2, l2) if n2.strip() else "", col_w)
        c3 = self.pad_visible(self.format_option(n3, l3) if n3.strip() else "", col_w)
        return self.center_text(f"{c1} {c2} {c3}")

    def format_nav_row(self):
        col_w = 32
        total = col_w * 3 + 2
        has_prev = self.current_page > 1
        has_next = self.current_page < self.total_pages
        prev = gradient_text("<< Prev") if has_prev else ""
        nxt = gradient_text("Next >>") if has_next else ""
        pv = self.get_visible_length(prev)
        nv = self.get_visible_length(nxt)
        if has_prev and has_next:
            row = prev + " " * (total - pv - nv) + nxt
        elif has_prev:
            row = prev
        elif has_next:
            row = " " * (total - nv) + nxt
        else:
            row = ""
        return self.center_text(row)

    def get_page_content(self):
        rows = self.pages_content.get(self.current_page, [])
        lines = ["\n"]
        for row in rows:
            lines.append(self.format_row(*row))
        lines.append("")
        lines.append(self.format_nav_row())
        return "\n".join(lines)

    def display(self):
        clear()
        self._print_banner()
        print()
        print(self.center_text(gradient_text(f"Logged in as: {self.username}")))
        print(self.get_page_content())
        print()
        page_ind = f"{gradient_text('[')} {self.current_page}/{self.total_pages} {gradient_text(']')}"
        print(self.center_text(page_ind))
        print()

    def get_choice(self):
        return input(
            f"      {gradient_text('[')} {Fore.WHITE}UtilityToolsV2{Style.RESET_ALL} {gradient_text(']')} {gradient_text('~>')} "
        ).strip()

    def show_credits(self):
        clear()
        self._print_banner()
        lines = [
            "website ~ https://www.utilitytoolsv2.store",
            "Owner & Dev ~ xritura01 ( not on discord )",
            "Thank you for using our script!",
            "Hope you have a nice day!"
        ]
        print("\n")
        for line in lines:
            print(gradient_text(line.center(self.size)))
        print("\n")
        input(gradient_text("      Press Enter to continue..."))

    def _get_ids(self, need_target=True):
        source = log.input("Source Guild ID")
        target = log.input("Target Guild ID") if need_target else None
        return source, target

    def _build(self, source, target=None):
        return UtilityClonerFunctions(self.token, source, target)

    def main_menu(self):
        while True:
            self.display()
            choice = self.get_choice()

            if choice == "<<" and self.current_page > 1:
                self.current_page -= 1
                continue
            if choice == ">>" and self.current_page < self.total_pages:
                self.current_page += 1
                continue

            try:
                if choice == "1":
                    s, t = self._get_ids()
                    self._build(s, t).clone_server_details()
                elif choice == "2":
                    s, t = self._get_ids()
                    self._build(s, t).clone_roles()
                elif choice == "3":
                    s, t = self._get_ids()
                    self._build(s, t).clone_emojis()
                elif choice == "4":
                    s, t = self._get_ids()
                    c = self._build(s, t)
                    for cat in [ch for ch in c.fetch_source_channels() if ch["type"] == 4]:
                        c.create_category_in_target(cat)
                elif choice == "5":
                    s, t = self._get_ids()
                    self._build(s, t).clone_channels()
                elif choice == "6":
                    source = log.input("Source Guild ID")
                    self._build(source, None).create_backup()
                elif choice == "7":
                    s, t = self._get_ids()
                    self._build(s, t).clone_nsfw_flags()
                elif choice == "8":
                    s, t = self._get_ids()
                    self._build(s, t).clone_stickers()
                elif choice == "9":
                    s, t = self._get_ids()
                    self._build(s, t).clone_webhooks()
                elif choice == "10":
                    self.show_credits()
                    continue
                elif choice == "*":
                    s, t = self._get_ids()
                    if not log.confirm("This will overwrite the target server. Continue?"):
                        continue
                    c = self._build(s, t)
                    c.clone_server_details()
                    c.clone_channels()
                    c.clone_roles()
                    c.clone_stickers()
                    c.clone_emojis()
                    c.clone_nsfw_flags()
                    c.clone_webhooks()
                    log.success("Full clone complete")
                elif choice == "$":
                    backups = [f for f in os.listdir("backups") if f.endswith(".json")]
                    if not backups:
                        log.error("No backups found")
                    else:
                        log.info("Available backups")
                        for i, b in enumerate(backups, 1):
                            print(f"      {gradient_text(str(i))}  {Fore.WHITE}{b}{Style.RESET_ALL}")
                        num = int(log.input("Select backup number")) - 1
                        if not (0 <= num < len(backups)):
                            log.error("Invalid selection")
                        else:
                            target = log.input("Target Guild ID")
                            if log.confirm("This will overwrite the target server. Continue?"):
                                self._build(None, target).restore_from_backup(backups[num])
                else:
                    log.error("Invalid option", detail=choice)
            except Exception as e:
                log.error("Unexpected error", detail=str(e))

            log.wait()


if __name__ == "__main__":
    UtilityClonerMenu()

