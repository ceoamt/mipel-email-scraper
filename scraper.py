import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# ====== CONFIG ======
INPUT = "mipel129_espositori.csv"
OUTPUT = "mipel129_espositori_con_email.csv"

# pagine contatti da tentare
CONTACT_PATHS = ["", "contact", "contact-us", "contacts", "contatti", "contatto", "contattaci"]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)

def normalize_url(url):
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url

def extract_emails_from_url(url, timeout=15):
    emails = set()
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text
    except Exception:
        return set()

    soup = BeautifulSoup(html, "html.parser")

    # mailto
    for a in soup.select("a[href^=mailto]"):
        href = a.get("href", "")
        for e in EMAIL_RE.findall(href):
            emails.add(e)

    # testo
    text = soup.get_text(" ", strip=True)
    for e in EMAIL_RE.findall(text):
        emails.add(e)

    return emails

def find_email_for_site(site):
    site = normalize_url(site)
    if not site:
        return ""

    emails_seen = set()

    for path in CONTACT_PATHS:
        url = urljoin(site.rstrip("/") + "/", path)
        emails = extract_emails_from_url(url)
        if emails:
            emails_seen |= emails
            break

    # fallback generico, se proprio nulla
    if not emails_seen:
        domain = site.replace("http://", "").replace("https://", "").split("/")[0]
        if "." in domain:
            emails_seen.add("info@" + domain)

    return sorted(emails_seen)[0] if emails_seen else ""

def main():
    df = pd.read_csv(INPUT)
    if "email" not in df.columns:
        df["email"] = ""

    for idx, row in df.iterrows():
        if str(row.get("email", "")).strip():
            continue
        email = find_email_for_site(str(row.get("sito_web", "")))
        df.at[idx, "email"] = email
        print(idx + 1, "/", len(df), row.get("ragione_sociale"), "->", email)

    df.to_csv(OUTPUT, index=False)
    print("DONE:", OUTPUT)

if __name__ == "__main__":
    main()
