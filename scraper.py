import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time

INPUT = "mipel129_espositori.csv"
OUTPUT = "mipel129_espositori_con_email.csv"

CONTACT_PATHS = ["", "contact", "contact-us", "contacts", "contatti", "contatto"]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MipelScraper/1.0)"
}

def normalize_url(url):
    if not url or pd.isna(url):
        return ""
    url = str(url).strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url

def extract_emails(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print("Status:", url, r.status_code)
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select("a[href^=mailto]"):
            mail = a.get("href", "")
            emails.update(EMAIL_RE.findall(mail))

        text = soup.get_text(" ", strip=True)
        emails.update(EMAIL_RE.findall(text))

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
    print("Rows found:", len(df))

    if "email" not in df.columns:
        df["email"] = ""

    for i, row in df.iterrows():
        current_email = str(row.get("email", "")).strip()

        if current_email and current_email.lower() != "nan":
            continue

        print(f"{i+1}/{len(df)} -> {row.get('ragione_sociale')}")
        email = find_email(row.get("sito_web"))
        df.at[i, "email"] = email

    df.to_csv(OUTPUT, index=False)
    print("Done.")
