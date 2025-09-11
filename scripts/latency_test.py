import os
import time
import json
import argparse
import requests


def run_test(api_base: str, company: str, question: str, timeout: int = 60):
    url = f"{api_base.rstrip('/')}/ask"
    payload = {"company": company, "question": question}
    headers = {"Content-Type": "application/json"}
    t0 = time.time()
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
        elapsed = time.time() - t0
        ok = resp.status_code == 200
        data = None
        try:
            data = resp.json()
        except Exception:
            pass
        return {
            "company": company,
            "status": resp.status_code,
            "ok": ok,
            "elapsed_sec": round(elapsed, 2),
            "error": (data or {}).get("detail") if not ok else None,
            "ticker": (data or {}).get("ticker") if ok else None,
        }
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - t0
        return {
            "company": company,
            "status": "exception",
            "ok": False,
            "elapsed_sec": round(elapsed, 2),
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=os.getenv("API_BASE", "http://127.0.0.1:8000"))
    parser.add_argument(
        "--companies",
        nargs="*",
        default=["Tesla", "Apple", "Google", "TCS", "Wipro"],
    )
    parser.add_argument(
        "--question",
        default="What is the near-term outlook and key risks?",
    )
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    print(f"API: {args.api}")
    print(f"Question: {args.question}")
    print("")

    results = []
    for company in args.companies:
        print(f"Testing: {company} ...", end=" ")
        res = run_test(args.api, company, args.question, args.timeout)
        results.append(res)
        status = "OK" if res["ok"] else "FAIL"
        print(f"{status} in {res['elapsed_sec']}s (status={res['status']})")

    print("\nSummary:")
    total = 0.0
    ok_count = 0
    for r in results:
        total += r["elapsed_sec"]
        if r["ok"]:
            ok_count += 1
        print(
            f"- {r['company']}: {r['elapsed_sec']}s, status={r['status']}, ok={r['ok']}, ticker={r.get('ticker')}, error={r.get('error')}"
        )
    avg = round(total / len(results), 2) if results else 0.0
    print(f"\nAvg latency: {avg}s over {len(results)} runs. Success: {ok_count}/{len(results)}.")


if __name__ == "__main__":
    main()


