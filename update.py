import json
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*"}

def get_json(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_fng():
    d = get_json("https://production.dataviz.cnn.io/index/fearandgreed/graphdata")
    f = d["fear_and_greed"]
    return {"score": round(float(f["score"]), 1), "rating": f["rating"],
            "week": round(float(f["previous_1_week"]), 1),
            "month": round(float(f["previous_1_month"]), 1)}

def fetch_closes(symbol, rng):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={rng}&interval=1d"
    d = get_json(url)["chart"]["result"][0]
    return [c for c in d["indicators"]["quote"][0]["close"] if c is not None]

def main():
    errors = []
    try:
        fng = fetch_fng()
    except Exception as e:
        fng = None; errors.append(f"공포탐욕지수 수집 실패: {e}")
    try:
        vix = round(fetch_closes("%5EVIX", "1mo")[-1], 2)
    except Exception as e:
        vix = None; errors.append(f"VIX 수집 실패: {e}")
    try:
        c = fetch_closes("%5ENDX", "2y")
        last = c[-1]; w = c[-200:]
        ma200 = sum(w)/len(w); high = max(c[-252:])
        ndx = {"last": round(last,2), "ma200": round(ma200,2), "high52w": round(high,2),
               "drawdown": round((last/high-1)*100,2), "maGap": round((last/ma200-1)*100,2)}
    except Exception as e:
        ndx = None; errors.append(f"나스닥100 수집 실패: {e}")

    now = datetime.now(KST)
    out = {"updatedAt": now.isoformat(timespec="seconds"),
           "updatedLabel": now.strftime("%Y년 %m월 %d일 %H:%M") + " (한국시각)",
           "fng": fng, "vix": vix, "ndx": ndx, "errors": errors}
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))

main()
