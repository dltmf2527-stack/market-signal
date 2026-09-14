import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
      "Accept": "*/*",
      "Accept-Language": "en-US,en;q=0.9"}

def get_text(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def get_json(url, timeout=30):
    return json.loads(get_text(url, timeout))

# ── 공포탐욕지수 ──
def fetch_fng():
    urls = [
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        "https://api.allorigins.win/raw?url=https%3A%2F%2Fproduction.dataviz.cnn.io%2Findex%2Ffearandgreed%2Fgraphdata",
    ]
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

# ── 시세: Stooq(CSV) 우선, 실패 시 야후 ──
def from_stooq(sym):
    txt = get_text(f"https://stooq.com/q/d/l/?s={sym}&i=d")
    rows = [r for r in txt.strip().split("\n")[1:] if r]
    out = []
    for r in rows:
        p = r.split(",")
        if len(p) >= 5:
            try:
                out.append(float(p[4]))
            except ValueError:
                pass
    if len(out) < 250:
        raise ValueError(f"stooq 데이터 부족 ({len(out)})")
    return out

def from_yahoo(sym):
    for h in ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]:
        try:
            d = get_json(f"https://{h}/v8/finance/chart/{sym}?range=3y&interval=1d")
            c = d["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            return [x for x in c if x is not None]
        except Exception:
            time.sleep(2)
    raise ValueError("yahoo 실패")

def fetch_closes(stooq_sym, yahoo_sym):
    err = None
    for fn, arg in [(from_stooq, stooq_sym), (from_yahoo, yahoo_sym)]:
        try:
            return fn(arg)
        except Exception as e:
            err = e
            time.sleep(2)
    raise err

def main():
    errors = []

    try:
        fng = fetch_fng()
    except Exception as e:
        fng = None
        errors.append(f"공포탐욕지수 수집 실패: {e}")

    try:
        vix = round(fetch_closes("^vix", "%5EVIX")[-1], 2)
    except Exception as e:
        vix = None
        errors.append(f"VIX 수집 실패: {e}")

    try:
        c = fetch_closes("^ndq", "%5ENDX")
        last = c[-1]
        w = c[-200:]
        ma200 = sum(w) / len(w)
        high = max(c[-252:])
        ndx = {"last": round(last, 2), "ma200": round(ma200, 2),
               "high52w": round(high, 2),
               "drawdown": round((last / high - 1) * 100, 2),
               "maGap": round((last / ma200 - 1) * 100, 2)}
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
