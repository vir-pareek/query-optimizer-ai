import joblib, os, re, sys, pandas as pd
from extract_features import count_kw, plan_feats
import sqlite3

DB_PATH = os.path.join("data","synth.db")
REG_PATH = "models/regressor.joblib"
CLS_PATH = "models/pairwise_clf.joblib"

def explain(db, sql):
    cur = db.cursor()
    cur.execute("EXPLAIN QUERY PLAN " + sql)
    rows = cur.fetchall()
    return " | ".join([r[3] for r in rows if len(r) >= 4])

def predict_pair(a_sql, b_sql):
    reg, reg_cols = joblib.load(REG_PATH)
    clf, cls_cols = joblib.load(CLS_PATH)

    with sqlite3.connect(DB_PATH) as db:
        a_plan = explain(db, a_sql)
        b_plan = explain(db, b_sql)

    # Regression for each
    def fe(sql, plan):
        f = count_kw(sql); f.update(plan_feats(plan))
        return f
    fa, fb = fe(a_sql, a_plan), fe(b_sql, b_plan)
    dfa = pd.DataFrame([fa]).reindex(columns=reg_cols, fill_value=0)
    dfb = pd.DataFrame([fb]).reindex(columns=reg_cols, fill_value=0)

    a_latency = float((reg.predict(dfa))[0])
    b_latency = float((reg.predict(dfb))[0])

    # Pairwise classification
    diff = {f"diff_{k}": fa.get(k,0)-fb.get(k,0) for k in fa}
    diff["diff_uses_index"] = (1 if "using index" in a_plan.lower() else 0) - \
                              (1 if "using index" in b_plan.lower() else 0)
    dfpair = pd.DataFrame([diff]).reindex(columns=cls_cols, fill_value=0)
    winner = clf.predict(dfpair)[0]

    print("=== Query A ===")
    print(a_sql.strip())
    print("Plan:", a_plan)
    print("Predicted log-latency:", round(a_latency,3))
    print("\n=== Query B ===")
    print(b_sql.strip())
    print("Plan:", b_plan)
    print("Predicted log-latency:", round(b_latency,3))
    print("\n=== Verdict ===")
    print("A is faster" if winner==1 else "B is faster")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python src/predict_cli.py 'SQL_A' 'SQL_B'")
        sys.exit(1)
    a_sql = sys.argv[1]
    b_sql = sys.argv[2]
    predict_pair(a_sql, b_sql)