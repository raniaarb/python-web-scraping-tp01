

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

BASE_URL = "https://quotes.toscrape.com"

def fetch_page(url, session=None):
   
    s = session or requests
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; scraping-bot/1.0; +https://example.com/bot)"
    }
    resp = s.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    #  طباعة جزء من HTML للتأكيد
    print("\n HTML snippet from:", url)
    print(resp.text[:500])  # نعرض أول 500 حرف فقط لتجنّب الطول الكبير
    os.makedirs("html_pages", exist_ok=True)
    page_name = url.strip("/").replace("/", "_").replace(":", "")
    html_path = os.path.join("html_pages", f"{page_name}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(resp.text)

    return BeautifulSoup(resp.text, "html.parser")


def parse_quotes_from_soup(soup, page_number=None):
    """يستخرج الاقتباسات من الصفحة."""
    results = []
    quote_blocks = soup.select("div.quote")
    for qb in quote_blocks:
        text = qb.select_one("span.text").get_text(strip=True) if qb.select_one("span.text") else ""
        author = qb.select_one("small.author").get_text(strip=True) if qb.select_one("small.author") else ""
        tag_elements = qb.select("div.tags a.tag")
        tags = [t.get_text(strip=True) for t in tag_elements]
        results.append({
            "quote": text,
            "author": author,
            "tags": ";".join(tags),
            "page": page_number
        })
    return results


def scrape_all_quotes(base_url=BASE_URL, sleep_between=1.0):
    """يتنقّل عبر صفحات الموقع ويجمع جميع الاقتباسات."""
    session = requests.Session()
    page_url = base_url + "/"
    all_results = []
    page_number = 1

    while True:
        print(f"\n Fetching page {page_number}: {page_url}")
        soup = fetch_page(page_url, session=session)
        page_results = parse_quotes_from_soup(soup, page_number=page_number)
        if not page_results:
            print(" لا اقتباسات — انتهاء المحتوى.")
            break

        all_results.extend(page_results)

        next_link = soup.select_one("li.next > a")
        if next_link and next_link.get("href"):
            next_href = next_link["href"]
            page_url = base_url.rstrip("/") + next_href
            page_number += 1
            time.sleep(sleep_between)
        else:
            print(" انتهى المسح — لا صفحات إضافية.")
            break

    df = pd.DataFrame(all_results)
    return df


if __name__ == "__main__":
    df = scrape_all_quotes()
    print(f"\n Total quotes scraped: {len(df)}")
    out_csv = "quotes_toscrape_all_pages.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f" Saved to {out_csv}")

