import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "*/*"}

def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def fetch_fng():
    urls = ["https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            "https://api.allorigins.win/raw?url=https%3A%2F%2Fproduction.dataviz.cnn.io%2Findex%2Ffearandgreed%2Fgraphdata"]
    err = None
    for u in urls:
        try:
            f = get_json(u)["fear_and_greed"]
            return {"score": round(float(f["score"]), 1), "rating": f["rating"],
                    "week": round(float(f["previous_1_week"]), 1),
                    "month": round(float(f["previous_1_month"]), 1)}
        except Exception as e:
            err = e
    raise err

def fetch_closes(symbol):
    closes = []
    for page in range(1, 31):
        url = f"https://api.stock.naver.com/index/{symbol}/price?pageSize=10&page={page}"
        rows = get_json(url)
        if not rows:
            break
        for r in rows:
            v = r.get("closePrice")
            if v:
                try:
                    closes.append(float(str(v).replace(",", "")))
                except ValueError:
                    pass
        time.sleep(0.5)
    if len(closes) < 210:
        raise ValueError(f"데이터 부족 ({len(closes)}일)")
    closes.reverse()
    return closes

def main():
    errors = []

    try:
        fng = fetch_fng()
    except Exception as e:
        fng = None
        errors.append(f"공포탐욕지수 수집 실패: {e}")

    try:
        vix = round(fetch_closes(".VIX")[-1], 2)
    except Exception as e:
        vix = None
        errors.append(f"VIX 수집 실패: {e}")

    try:
        c = fetch_closes(".NDX")
        last = c[-1]
        w = c[-200:]
        ma200 = sum(w) / len(w)
        high = max(c)
        ndx = {"last": round(last, 2), "ma200": round(ma200, 2),
               "high52w": round(high, 2),
               "drawdown": round((last / high - 1) * 100, 2),
               "maGap": round((last / ma200 - 1) * 100, 2),
               "days": len(c)}
    except Exception as e:
        ndx = None
        errors.append(f"나스닥100 수집 실패: {e}")

    now = datetime.now(KST)
    out = {"updatedAt": now.isoformat(timespec="seconds"),
           "updatedLabel": now.strftime("%Y년 %m월 %d일 %H:%M") + " (한국시각)",
           "fng": fng, "vix": vix, "ndx": ndx, "errors": errors}

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))

main()
