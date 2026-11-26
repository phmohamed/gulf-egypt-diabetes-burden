import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = pd.read_csv("data/who_ncd_gulf_egypt.csv")
d = d[d.indicator != "diabetes_death_rate"]  # only one year (2004) available, too old to compare
names = {"SAU": "Saudi Arabia", "EGY": "Egypt", "ARE": "UAE", "KWT": "Kuwait", "QAT": "Qatar",
         "BHR": "Bahrain", "OMN": "Oman", "USA": "USA", "GBR": "UK", "IND": "India"}
d["country"] = d.country.map(names)
d["sex"] = d.sex.map({"SEX_BTSX": "both", "SEX_MLE": "male", "SEX_FMLE": "female"})
focus = ["Saudi Arabia", "Egypt", "UAE", "Kuwait", "Qatar", "Bahrain", "Oman"]
d["age"] = d.age.fillna("none")
print(d.groupby("indicator").age.unique())
both = d[d.sex == "both"]
# diabetes prevalence exists for two age bands. Use 18+ for rankings, 30+ only where treatment coverage is applied (it is defined for 30+).
both = both[~((both.indicator == "diabetes_prevalence") & (both.age != "AGEGROUP_YEARS18-PLUS"))]
prev30 = d[(d.indicator == "diabetes_prevalence") & (d.sex == "both") & (d.age == "AGEGROUP_YEARS30-PLUS")].pivot(index="country", columns="year", values="value")

# 1. latest values per country
latest = (both.sort_values("year").groupby(["indicator", "country"]).tail(1)
          .pivot(index="country", columns="indicator", values="value").round(1))
latest.to_csv("data/latest_values.csv")
print(latest)

# 2. diabetes change 1990 -> 2022
dp = both[both.indicator == "diabetes_prevalence"].pivot(index="country", columns="year", values="value")
chg = pd.DataFrame({"1990": dp[1990], "2022": dp[2022]})
chg["change_points"] = chg["2022"] - chg["1990"]
chg["relative_change_pct"] = 100 * chg.change_points / chg["1990"]
chg = chg.round(1).sort_values("2022", ascending=False)
chg.to_csv("data/diabetes_change_1990_2022.csv")
print(chg)

# 3. treatment gap: prevalence x (1 - coverage), a rough "untreated share of adults" proxy
tc = both[both.indicator == "diabetes_treatment_coverage"].pivot(index="country", columns="year", values="value")[2022]
gap = pd.DataFrame({"prevalence_30plus_2022": prev30[2022], "treatment_coverage_2022": tc})
gap["untreated_adults_pct"] = (gap.prevalence_30plus_2022 * (1 - gap.treatment_coverage_2022 / 100)).round(1)
gap = gap.round(1).sort_values("untreated_adults_pct", ascending=False)
gap.to_csv("data/treatment_gap_2022.csv")
print(gap)

# 4. sex gap
sx = d[(d.indicator == "diabetes_prevalence") & (d.year == 2022) & (d.sex != "both") & (d.age == "AGEGROUP_YEARS18-PLUS")].pivot(index="country", columns="sex", values="value").round(1)
sx["female_minus_male"] = (sx.female - sx.male).round(1)
sx.to_csv("data/diabetes_by_sex_2022.csv")
print(sx)

# 5. obesity vs diabetes (latest year both exist)
ob = both[(both.indicator == "obesity_adults") & (both.year == 2022)].set_index("country").value
sc = pd.DataFrame({"obesity": ob, "diabetes": dp[2022]}).dropna()
print("corr obesity-diabetes (10 countries):", round(sc.corr().iloc[0, 1], 2))

# figures
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(8, 5))
for c in focus:
    s = both[(both.indicator == "diabetes_prevalence") & (both.country == c)].sort_values("year")
    ax.plot(s.year, s.value, label=c, lw=2.4 if c in ("Saudi Arabia", "Egypt") else 1.3)
ax.set_ylabel("Adults 18+ with diabetes, age-standardised (%)"); ax.set_title("Diabetes prevalence, 1990 to 2022 (WHO)")
ax.legend(frameon=False, ncol=2); fig.tight_layout(); fig.savefig("figures/diabetes_trend.png", dpi=150)

fig, ax = plt.subplots(figsize=(7, 4.5))
g = gap.sort_values("untreated_adults_pct")
ax.barh(g.index, g.untreated_adults_pct, color="#c0504d")
ax.set_xlabel("Adults 30+ with diabetes and no treatment (% of adults 30+, rough proxy)")
ax.set_title("Untreated diabetes, 2022"); fig.tight_layout(); fig.savefig("figures/untreated_diabetes.png", dpi=150)

fig, ax = plt.subplots(figsize=(6.5, 5))
ax.scatter(sc.obesity, sc.diabetes)
for c, r in sc.iterrows(): ax.annotate(c, (r.obesity, r.diabetes), fontsize=8, xytext=(4, 3), textcoords="offset points")
ax.set_xlabel("Adult obesity, 2022 (%)"); ax.set_ylabel("Diabetes prevalence, 2022 (%)")
ax.set_title("Obesity vs diabetes, 10 countries"); fig.tight_layout(); fig.savefig("figures/obesity_vs_diabetes.png", dpi=150)
