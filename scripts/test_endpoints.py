import os
import time
import json
import argparse
import requests


def ping(api):
    t0 = time.time()
    r = requests.get(f"{api}/", timeout=10)
    return r.status_code, round(time.time() - t0, 2), r.json()


def quote(api, ticker):
    t0 = time.time()
    r = requests.get(f"{api}/data/quote/{ticker}", timeout=10)
    data = None
    try:
        data = r.json()
    except Exception:
        pass
    return r.status_code, round(time.time() - t0, 2), data


def history(api, ticker, days=30):
    t0 = time.time()
    r = requests.get(f"{api}/data/history/{ticker}", params={"days": days}, timeout=10)
    data = None
    try:
        data = r.json()
    except Exception:
        pass
    return r.status_code, round(time.time() - t0, 2), data


def ask(api, company, question, timeout=60):
    t0 = time.time()
    r = requests.post(
        f"{api}/ask",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"company": company, "question": question}),
        timeout=timeout,
    )
    data = None
    try:
        data = r.json()
    except Exception:
        pass
    return r.status_code, round(time.time() - t0, 2), data


def vector_search(api, query, k=3):
    t0 = time.time()
    r = requests.post(
        f"{api}/search/vector",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"query": query, "k": k}),
        timeout=15,
    )
    data = None
    try:
        data = r.json()
    except Exception:
        pass
    return r.status_code, round(time.time() - t0, 2), data


def recent_history(api, limit=5):
    t0 = time.time()
    r = requests.get(f"{api}/history", params={"limit": limit}, timeout=10)
    data = None
    try:
        data = r.json()
    except Exception:
        pass
    return r.status_code, round(time.time() - t0, 2), data


def report(api, company, question, timeout=120):
    t0 = time.time()
    r = requests.post(
        f"{api}/reports/stock",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"company": company, "question": question}),
        timeout=timeout,
    )
    return r.status_code, round(time.time() - t0, 2), r.headers.get("content-type")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=os.getenv("API_BASE", "http://127.0.0.1:8000"))
    parser.add_argument("--ticker", default="TSLA")
    parser.add_argument("--company", default="Tesla")
    parser.add_argument("--question", default="Provide a concise current outlook and key risks.")
    parser.add_argument("--ask_timeout", type=int, default=60)
    args = parser.parse_args()

    api = args.api.rstrip("/")
    print(f"Testing API base: {api}\n")

    sc, t, data = ping(api)
    print(f"GET /  -> {sc} in {t}s | {data}")

    sc, t, data = quote(api, args.ticker)
    print(f"GET /data/quote/{args.ticker} -> {sc} in {t}s | ok={not data or not data.get('quote', {}).get('error')} ")

    sc, t, data = history(api, args.ticker)
    n = len((data or {}).get("history", [])) if isinstance(data, dict) else 0
    print(f"GET /data/history/{args.ticker} -> {sc} in {t}s | points={n}")

    sc, t, data = vector_search(api, f"{args.company} outlook", k=2)
    c = len((data or {}).get("results", [])) if isinstance(data, dict) else 0
    print(f"POST /search/vector -> {sc} in {t}s | results={c}")

    sc, t, data = ask(api, args.company, args.question, timeout=args.ask_timeout)
    ok = sc == 200
    print(f"POST /ask -> {sc} in {t}s | ok={ok} | ticker={(data or {}).get('ticker')} | err={(data or {}).get('detail')}")

    sc, t, data = recent_history(api, limit=5)
    num = len((data or {}).get("queries", [])) if isinstance(data, dict) else 0
    print(f"GET /history -> {sc} in {t}s | rows={num}")

    # Report endpoint is heavier; optional quick check for status only
    # sc, t, ctype = report(api, args.company, args.question, timeout=90)
    # print(f"POST /reports/stock -> {sc} in {t}s | content-type={ctype}")


if __name__ == "__main__":
    main()


