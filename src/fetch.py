"""Download WHO Global Health Observatory indicators for Gulf countries, Egypt and a few comparators."""
import requests, pandas as pd

BASE = "https://ghoapi.azureedge.net/api/"
INDICATORS = {
    "NCD_DIABETES_PREVALENCE_AGESTD": "diabetes_prevalence",
    "NCD_DIABETES_TREATMENT_AGESTD": "diabetes_treatment_coverage",
    "NCD_BMI_30A": "obesity_adults",
    "BP_04": "raised_bp",
    "SA_0000001440": "diabetes_death_rate",
}
COUNTRIES = ["SAU", "EGY", "ARE", "KWT", "QAT", "BHR", "OMN", "USA", "GBR", "IND"]

frames = []
for code, name in INDICATORS.items():
    flt = "SpatialDim in (" + ",".join(f"'{c}'" for c in COUNTRIES) + ")"
    r = requests.get(BASE + code, params={"$filter": flt}, timeout=60)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["value"])
    if df.empty:
        print("no rows for", code); continue
    df = df[["SpatialDim", "TimeDim", "Dim1", "Dim2", "NumericValue", "Low", "High"]]
    df.columns = ["country", "year", "sex", "age", "value", "low", "high"]
    df["indicator"] = name
    frames.append(df)
    print(name, len(df))
pd.concat(frames, ignore_index=True).to_csv("data/who_ncd_gulf_egypt.csv", index=False)
