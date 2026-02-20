import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time
import os

INPUT = "mipel129_espositori.csv"
OUTPUT = "mipel129_espositori_con_email.csv"

CONTACT_PATHS = [
    "",
    "contact",
    "contact-us",
    "contacts",
    "contatti",
    "contatto",
    "about",
    "about-us",
]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

def normalize_url(url):
    if not url or pd.isna(url):
        return ""
    url = str(url).strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def decode_cloudflare_email(encoded):
    try:
        r = int(encoded[:2], 16)
        email = ''.join(
            chr(int(encoded[i:i+2], 16) ^ r)
            for i in range(2, len(encoded), 2)
        )
        return email
    except:
        return None

def extract_emails_from_html(html):
    emails = set()

    # Email standard
    emails.update(EMAIL_RE.findall(html))

    # Email offuscate tipo info [at] dominio.com
    obfuscated = re.findall(r"([A-Za-z0-9._%+-]+)\s?\[at\]\s?([A-Za-z0-9.-]+\.[A-Za-z]{2,})", html, re.I)
    for user, domain in obfuscated:
        emails.add(f"{user}@{domain}")

    return emails

def extract_emails(url):
    emails = set()

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print("Status:", url, r.status_code)

        soup = BeautifulSoup(r.text, "html.parser")

        # Cloudflare email decode
        for tag in soup.find_all("a", {"data-cfemail": True}):
            encoded = tag["data-cfemail"]
            decoded = decode_cloudflare_email(encoded)
            if decoded:
                emails.add(decoded)

        html = r.text
        emails.update(extract_emails_from_html(html))

    except Exception as e:
        print("Error:", url, e)

    return emails

def find_email(site):
    site = normalize_url(site)
    if not site:
        return ""

    for path in CONTACT_PATHS:
        url = urljoin(site.rstrip("/") + "/", path)
        emails = extract_emails(url)

        if emails:
            return sorted(emails)[0]

        time.sleep(1)

    return ""

def main():
    df = pd.read_csv(INPUT)

    if "email" not in df.columns:
        df["email"] = ""

    print("Rows found:", len(df))

    for i, row in df.iterrows():
        current_email = str(row.get("email", "")).strip()

        if current_email and current_email.lower() != "nan":
            continue

        print(f"{i+1}/{len(df)} -> {row.get('ragione_sociale')}")

        email = find_email(row.get("sito_web"))
        df.at[i, "email"] = email

    df.to_csv(OUTPUT, index=False)
    print("Files in directory:", os.listdir())
    print("Done.")

if __name__ == "__main__":
    main()
