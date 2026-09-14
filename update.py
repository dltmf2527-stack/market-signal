import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "*/*",
      "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
      "Referer": "https://m.stock.naver.com/"}

def get_text(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def get_json(url, timeout=30):
    return json.loads(get_text(url, timeout))

# ── 공포탐욕지수 (CNN) ──
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

# ── 시세: 네이버 금융 ──
def from_naver(code):
    # 네이버는 한 번에 최대 약 1년치씩 주므로 3페이지를 이어붙임
    closes = []
    for page in range(3):
        url = (f"https://api.stock.naver.com/chart/foreign/index/{code}"
               f"?periodType=dayCandle&page={page+1}")
        d = get_json(url)
        rows = d if isinstance(d, list) else d.get("priceInfos", d.get("result", []))
        for r in rows:
            v = r.get("closePrice") or r.get("cv") or r.get("close")
            if v is None:
                continue
            try:
                closes.append(float(str(v).replace(",", "")))
            except ValueError:
                pass
        time.sleep(1)
    if len(closes) < 250:
        raise ValueError(f"네이버 데이터 부족 ({len(closes)})")
    closes.reverse()  # 과거 → 최신 순으로 정렬
    return closes

def from_stooq(sym):
    txt = get_text(f"https://stooq.com/q/d/l/?s={sym}&i=d")
    out = []
    for r in txt.strip().split("\n")[1:]:
        p = r.split(",")
        if len(p) >= 5:
            try:
                out.append(float(p[4]))
            except ValueError:
                pass
    if len(out) < 250:
        raise ValueError(f"stooq 데이터 부족 ({len(out)})")
    return out

def fetch_closes(naver_code, stooq_sym):
    errs = []
    for fn, arg in [(from_naver, naver_code), (from_stooq, stooq_sym)]:
        try:
            return fn(arg)
        except Exception as e:
            errs.append(f"{fn.__name__}: {e}")
            time.sleep(2)
    raise ValueError(" / ".join(errs))

def main():
    errors = []

    try:
        fng = fetch_fng()
    except Exception as e:
        fng = None
        errors.append(f"공포탐욕지수 수집 실패: {e}")

    try:
        vix = round(fetch_closes("VIX", "^vix")[-1], 2)
    except Exception as e:
        vix = None
        errors.append(f"VIX 수집 실패: {e}")

    try:
        c = fetch_closes("NAS@NDX", "^ndq")
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
