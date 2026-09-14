import json, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "*/*"}

def probe(name, url):
    print("=" * 70)
    print(name)
    print(url)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
        print("상태: OK", r.status, "/ 길이", len(body))
        print("--- 앞부분 400자 ---")
        print(body[:400])
    except Exception as e:
        print("실패:", type(e).__name__, e)
    print()

probe("A. stooq VIX",      "https://stooq.com/q/d/l/?s=%5Evix&i=d")
probe("B. stooq NDX",      "https://stooq.com/q/d/l/?s=%5Endq&i=d")
probe("C. stooq QQQ(ETF)", "https://stooq.com/q/d/l/?s=qqq.us&i=d")
probe("D. naver VIX",      "https://api.stock.naver.com/index/.VIX/price?pageSize=10&page=1")
probe("E. naver NDX",      "https://api.stock.naver.com/index/.NDX/price?pageSize=10&page=1")
probe("F. naver 통합검색",  "https://m.stock.naver.com/front-api/marketIndex/productDetail?category=worldIndex&reutersCode=.VIX")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump({"probe": "진단 실행 중"}, f, ensure_ascii=False)
