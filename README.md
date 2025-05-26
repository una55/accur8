

# 🚩 accur8 - Final Version 

A modular, multithreaded brute force tool for penetration testers and red teamers.  
Supports custom headers, proxies, Tor, rate limit bypass, password mutation, CSRF tokens, and detailed reporting.

---

## ✨ Features

- ⚡ Multi-threaded: Fast, concurrent login attempts.
- 🎭 Custom Headers & Proxies: Bypass WAFs, test behind corporate proxies.
- 🕵️‍♂️ Tor Support: Route traffic through Tor for anonymity.
- 🚦 Rate Limit Bypass: Randomized IP headers to bypass basic rate limiting.
- 🛡️ Automatic CSRF Handling: Fetches CSRF tokens if required.
- 🔀 Password Mutation: Common mutations to increase success rates.
- 📊 Progress Bar & Logging: Real-time progress with colored output.
- 📑 HTML/JSON/CSV/Text Reports : Save results in multiple formats.
- 🤖 CAPTCHA/2FA Detection: Stops if advanced defenses are detected.

---

## 🛠️ Requirements

- 🐍 `Python 3.7+`
- 📦 Install dependencies:
  ```bash
  pip install requests pysocks stem tqdm colorama jinja2 beautifulsoup4
  ```

---
## ⚙️ Installation 
  ```
  git clone https://github.com/una55/accur8.git && cd accur8 && pip install -r requirements.txt && python accur8.py -h
  ```
---

## 🚀 Usage

```bash
python accur8.py -u <url> -U <username|userfile.txt> -P <passlist.txt> [options]
```

### 🔗 Required Arguments

- `-u`, `--url`  
  🌐 URL of the login form (e.g., `https://target.com/login`)
- `-U`, `--username`  
  👤 Username or file with usernames (one per line)
- `-P`, `--passlist`  
  🔑 Password list file (one password per line)

### ⚙️ Optional Arguments

| Option                | Description                                                           |
|-----------------------|-----------------------------------------------------------------------|
| `--csrf`              | 🔒 Enable CSRF token fetching                                         |
| `--proxy`             | 🌍 Proxy URL (e.g., `http://127.0.0.1:8080`)                          |
| `--threads`           | 🧵 Number of threads (default: 10)                                    |
| `--fail-flag`         | 🚫 String in response indicating login failure (default: `Invalid`)   |
| `--method`            | 📬 HTTP method to use (`POST` or `GET`, default: `POST`)              |
| `--headers`           | 📦 Custom headers as JSON string                                      |
| `--tor`               | 🕸️ Route requests through Tor (requires Tor running locally)          |
| `--rate-bypass`       | 🎲 Randomize IP headers to bypass rate limiting                       |
| `--mutate`            | 🔄 Enable password mutations                                          |
| `--output-format`     | 📝 Output format: `text`, `json`, `csv` (default: `text`)             |
| `--output-file`       | 💾 Output file for results (default: `results.out`)                   |

---

## 🧑‍💻 Examples

### Basic Usage

```bash
python brute_forcer.py -u https://example.com/login -U admin -P passwords.txt
```

### Brute Force with User List and Proxy

```bash
python brute_forcer.py -u https://example.com/login -U users.txt -P passwords.txt --proxy http://127.0.0.1:8080
```

### Use Tor, Rate Bypass, and Save as CSV

```bash
python brute_forcer.py -u https://example.com/login -U admin -P passwords.txt --tor --rate-bypass --output-format csv
```

### With Custom Headers and CSRF

```bash
python brute_forcer.py -u https://example.com/login -U admin -P passwords.txt --headers '{"Referer": "https://example.com/login"}' --csrf
```

---

## 📂 Output

- 📈 Progress Bar: Shows real-time progress.
- 🗝️ found.txt: Stores valid credentials found.
- 📄 results.out: Log of attempts and successes (format depends on `--output-format`).
- 🖼️ brute_report.html: Colorful HTML report for easy review.

---

## ⚠️ Notes

- Legal Notice:  
  🚨 Use this tool only on systems you own or have explicit permission to test. Unauthorized use is illegal.
- Tor:  
  🕸️ To use Tor, ensure the Tor service is running (`sudo service tor start` or `tor` on command line).
- CSRF:  
  🔒 Enable `--csrf` if the login form uses a CSRF token named `csrf_token`.
- CAPTCHA/2FA:  
  🤖 If detected, the tool will stop automatically.

---

## 🆘 Troubleshooting

- Module Not Found:  
  🧩 Install missing modules with `pip install <module>`.
- Tor Not Working:  
  🕳️ Check Tor is running and listening on port 9050 (SOCKS5) and 9051 (control port).
- Custom Login Fields:  
  🛠️ The tool auto-detects common field names. For unusual forms, you may need to adapt the code.
- Linux Users [Debian's Specifically] need to activate a virtual python environment before using the tool.
- ```
  python3 venv venv1 && source venv1/bin/activate
  ```
---

## 📜 License

For educational and authorized penetration testing use only.  
No warranty. Use at your own risk.

---

**Happy hacking!** 🤘  
If you find this useful, consider contributing or reporting issues!

---

