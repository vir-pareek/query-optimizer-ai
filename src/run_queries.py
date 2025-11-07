import sqlite3, time, csv, os, re

DB_PATH = os.path.join("data","synth.db")
PAIRS_PATH = os.path.join("data","query_pairs.txt")
TIMINGS_CSV = os.path.join("data","timings.csv")

def explain_plan(cur, sql):
    # Use EXPLAIN QUERY PLAN to get high-level steps
    cur.execute("EXPLAIN QUERY PLAN " + sql)
    rows = cur.fetchall()
    # Concatenate plan text
    return " | ".join([r[3] for r in rows if len(r) >= 4])

def time_query(cur, sql, warmups=1, runs=3):
    # Warmup (JIT/cache effects)
    for _ in range(warmups):
        list(cur.execute(sql))
    # Time a few runs, take median
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        list(cur.execute(sql))
        dt = (time.perf_counter() - t0) * 1000.0  # ms
        times.append(dt)
    times.sort()
    return times[len(times)//2]

def read_pairs(path):
    with open(path, "r") as f:
        content = f.read()
    chunks = content.split("###PAIR###")
    pairs = []
    for ch in chunks:
        if "--A--" in ch and "--B--" in ch:
            a = ch.split("--A--")[1].split("--B--")[0].strip()
            b = ch.split("--B--")[1].split("--TAG--")[0].strip()
            tag = ch.split("--TAG--")[1].strip()
            pairs.append((a,b,tag))
    return pairs

def main():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    pairs = read_pairs(PAIRS_PATH)
    with open(TIMINGS_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pair_id","variant","tag","sql","plan","latency_ms"])
        for i,(a,b,tag) in enumerate(pairs):
            for variant, sql in [("A",a), ("B",b)]:
                plan = explain_plan(cur, sql)
                latency = time_query(cur, sql)
                w.writerow([i, variant, tag, " ".join(sql.split()), plan, round(latency,3)])
    conn.close()
    print("Wrote timing results to", TIMINGS_CSV)

if __name__ == "__main__":
    main()