import pandas as pd, numpy as np, os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, f1_score

DATA_INDIV = os.path.join("data","features_individual.csv")
DATA_PAIRS = os.path.join("data","features_pairs.csv")
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def top_features(model, feature_names, k=12):
    imp = model.feature_importances_
    idx = np.argsort(imp)[::-1][:k]
    return list(zip(np.array(feature_names)[idx], imp[idx]))

def train_regression():
    df = pd.read_csv(DATA_INDIV)
    y = np.log1p(df["latency_ms"])
    X = df.drop(columns=["latency_ms","pair_id","variant","tag"])
    X = X.fillna(0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    rf = RandomForestRegressor(n_estimators=300, random_state=42)
    rf.fit(X_train, y_train)
    preds = rf.predict(X_test)
    mae = mean_absolute_error(np.expm1(y_test), np.expm1(preds))
    r2 = r2_score(y_test, preds)
    print(f"[REG] MAE(ms)={mae:.3f}, R2={r2:.3f}")
    print("[REG] Top features:", top_features(rf, X.columns))
    return rf, X.columns

def train_pairwise():
    df = pd.read_csv(DATA_PAIRS)
    y = df["label_A_is_faster"]
    X = df.drop(columns=["pair_id","label_A_is_faster"])
    X = X.fillna(0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    clf = RandomForestClassifier(n_estimators=400, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds)
    print(f"[CLS] ACC={acc:.3f}, F1={f1:.3f}")
    print("[CLS] Top features:", top_features(clf, X.columns))
    return clf, X.columns

if __name__ == "__main__":
    reg_model, reg_cols = train_regression()
    cls_model, cls_cols = train_pairwise()

    # Persist models
    import joblib
    joblib.dump((reg_model, list(reg_cols)), "models/regressor.joblib")
    joblib.dump((cls_model, list(cls_cols)), "models/pairwise_clf.joblib")
    print("Saved models in models/")