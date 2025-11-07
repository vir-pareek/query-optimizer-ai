import re, os, pandas as pd

TIMINGS_CSV = os.path.join("data","timings.csv")
FEATURES_CSV = os.path.join("data","features.csv")

KW = [
    " join ", " exists ", " in ", " group by ", " order by ",
    " limit ", " where ", " select ", " count(", " sum(", " avg(",
    " min(", " max(", " distinct ", " subquery "
]

def count_kw(sql):
    s = " " + sql.lower() + " "
    feats = {}
    for k in KW:
        feats[f"kw_{k.strip()}"] = s.count(k)
    # crude subquery heuristic: '(' SELECT ... ')'
    feats["num_parens"] = s.count("(")
    feats["num_equals"] = s.count("=")
    feats["num_and"] = s.count(" and ")
    feats["num_or"] = s.count(" or ")
    feats["len_chars"] = len(s)
    return feats

def plan_feats(plan):
    p = " " + plan.lower() + " "
    return {
        "plan_uses_index": int("using index" in p),
        "plan_temp_btree": int("use temp btree" in p or "temp" in p),
        "plan_scan": p.count("scan"),
        "plan_search": p.count("search"),
    }

def main():
    df = pd.read_csv(TIMINGS_CSV)
    # pivot into pairwise comparison label: faster=A/B
    # Also keep regression target (latency)
    rows = []
    for pair_id, g in df.groupby("pair_id"):
        g = g.sort_values("variant")
        a = g[g["variant"]=="A"].iloc[0]
        b = g[g["variant"]=="B"].iloc[0]
        # Classification label: which is faster (A=1 if faster else 0)
        faster_a = int(a["latency_ms"] < b["latency_ms"])
        # Build feature rows for A and B individually (for regression)
        for row in [a,b]:
            feats = count_kw(row["sql"])
            feats.update(plan_feats(row["plan"]))
            feats.update({
                "pair_id": row["pair_id"],
                "variant": row["variant"],
                "tag": row["tag"],
                "latency_ms": row["latency_ms"],
            })
            rows.append(feats)
        # Also a pairwise record
    pair_records = []
    for pair_id, g in df.groupby("pair_id"):
        g = g.set_index("variant")
        a_sql = g.loc["A","sql"]; b_sql = g.loc["B","sql"]
        a_plan = g.loc["A","plan"]; b_plan = g.loc["B","plan"]
        a_lat = g.loc["A","latency_ms"]; b_lat = g.loc["B","latency_ms"]
        y = int(a_lat < b_lat)
        fa = count_kw(a_sql); fb = count_kw(b_sql)
        pa = plan_feats(a_plan); pb = plan_feats(b_plan)
        # Difference features (A - B)
        diff = {f"diff_{k}": fa.get(k,0)-fb.get(k,0) for k in fa}
        diff.update({f"diff_{k}": pa.get(k,0)-pb.get(k,0) for k in pa})
        diff.update({"pair_id": pair_id, "label_A_is_faster": y})
        pair_records.append(diff)

    df_individual = pd.DataFrame(rows)
    df_pairs = pd.DataFrame(pair_records)

    # Save
    df_individual.to_csv(FEATURES_CSV.replace("features","features_individual"), index=False)
    df_pairs.to_csv(FEATURES_CSV.replace("features","features_pairs"), index=False)
    print("Saved features to data/features_individual.csv and data/features_pairs.csv")

if __name__ == "__main__":
    main()