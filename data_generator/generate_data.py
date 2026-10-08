"""
Generate the fictional custody dataset used by every project in the portfolio.

All names, codes and numbers are made up. Run from the repo root:

    python data_generator/generate_data.py

Outputs go to ./data (Projects 1-6) and ./project7 (Project 7).
A list of every data-quality problem injected on purpose is written to
data/_injected_issues.csv so you can check your queries and workflows catch them.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
AS_OF = pd.Timestamp("2026-06-30")
START = pd.Timestamp("2026-01-05")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
P7 = ROOT / "project7"
DATA.mkdir(exist_ok=True)
P7.mkdir(exist_ok=True)

rng = np.random.default_rng(SEED)
issues = []  # (issue_type, table, key, note)


def log(issue_type, table, key, note=""):
    issues.append({"issue_type": issue_type, "table": table, "key": key, "note": note})


def isin_check_digit(base11: str) -> str:
    """ISIN check digit (Luhn on the letters-to-numbers expansion)."""
    digits = "".join(str(int(c, 36)) for c in base11)
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - total % 10) % 10)


def make_isin(country: str) -> str:
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    body = "".join(rng.choice(list(chars), 9))
    base = country + body
    return base + isin_check_digit(base)


bdays = pd.bdate_range(START, AS_OF)  # business days (ignores public holidays)

# ---------------------------------------------------------------- reference data
phonetic = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India",
            "Juliett", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo",
            "Sierra", "Tango"]
client_types = ["Super fund"] * 10 + ["Asset manager"] * 7 + ["Insurer"] * 3
clients = pd.DataFrame({
    "client_id": [f"C{i:03d}" for i in range(1, 21)],
    "client_name": [f"Fund {p} (fictional)" for p in phonetic],
    "client_type": client_types,
})

accounts = []
n = 1
for cid in clients.client_id:
    for k in range(2):
        accounts.append({"account_id": f"A{n:04d}", "client_id": cid,
                         "account_name": f"{cid} {'Main' if k == 0 else 'Growth'} Portfolio",
                         "base_currency": "AUD"})
        n += 1
accounts = pd.DataFrame(accounts)

letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
tickers = set()
while len(tickers) < 200:
    tickers.add("".join(rng.choice(letters, 3)))
tickers = sorted(tickers)

sec_rows = []
for i, t in enumerate(tickers, start=1):
    r = rng.random()
    asset_class = "Equity" if r < 0.70 else ("Bond" if r < 0.90 else "ETF")
    r2 = rng.random()
    if r2 < 0.80:
        ccy, market, country = "AUD", "ASX", "AU"
    elif r2 < 0.95:
        ccy, market, country = "USD", "NYSE", "US"
    else:
        ccy, market, country = "EUR", "XETRA", "DE"
    sec_rows.append({
        "security_id": f"S{i:04d}", "isin": make_isin(country), "ticker": t,
        "security_name": f"Fictional {'Bond' if asset_class == 'Bond' else 'Company'} {i:03d} "
                         f"{'Notes' if asset_class == 'Bond' else 'Ltd'}",
        "asset_class": asset_class, "currency": ccy, "market": market,
    })
securities = pd.DataFrame(sec_rows)
# DQ: missing ISINs
for idx in rng.choice(securities.index, 4, replace=False):
    log("missing_isin", "securities", securities.at[idx, "security_id"])
    securities.at[idx, "isin"] = None

counterparties = pd.DataFrame({
    "counterparty_id": [f"CP{i:02d}" for i in range(1, 13)],
    "counterparty_name": [f"Broker {c} (fictional)" for c in "ABCDEFGHIJKL"],
})
# Two brokers fail far more often: this is the "story" in the data
fail_rate = {cp: 0.02 for cp in counterparties.counterparty_id}
fail_rate.update({"CP03": 0.09, "CP08": 0.07, "CP05": 0.035})

# ---------------------------------------------------------------- prices
price_rows = []
start_price = {}
for s in securities.itertuples():
    p0 = rng.uniform(95, 105) if s.asset_class == "Bond" else rng.uniform(2, 120)
    vol = 0.002 if s.asset_class == "Bond" else 0.018
    path = p0 * np.exp(np.cumsum(rng.normal(0, vol, len(bdays))))
    start_price[s.security_id] = p0
    for d, p in zip(bdays, path):
        price_rows.append((s.security_id, d.date(), round(float(p), 4)))
prices = pd.DataFrame(price_rows, columns=["security_id", "price_date", "close_price"])
price_lookup = prices.set_index(["security_id", "price_date"]).close_price

# ---------------------------------------------------------------- trades
N = 10_000
sec_pick = rng.choice(securities.security_id, N)
sec_info = securities.set_index("security_id")
trade_dates = rng.choice(bdays, N)
rows = []
for i in range(N):
    sid = sec_pick[i]
    td = pd.Timestamp(trade_dates[i])
    lag = 1 if sec_info.at[sid, "market"] == "NYSE" else 2
    sd = td + pd.offsets.BDay(lag)
    px = price_lookup[(sid, td.date())] * rng.uniform(0.995, 1.005)
    qty = int(rng.choice([100, 250, 500, 1000, 2000, 5000, 10000]) * rng.integers(1, 6))
    rows.append({
        "trade_id": f"T{i + 1:06d}",
        "account_id": rng.choice(accounts.account_id),
        "security_id": sid,
        "counterparty_id": rng.choice(counterparties.counterparty_id),
        "trade_date": td.date(),
        "settle_date": sd.date(),
        "side": rng.choice(["BUY", "SELL"]),
        "quantity": qty,
        "price": round(float(px), 4),
        "currency": sec_info.at[sid, "currency"],
    })
trades = pd.DataFrame(rows)
trades["trade_value"] = (trades.quantity * trades.price).round(2)

# ---------------------------------------------------------------- settlements
reasons = ["Insufficient securities", "Insufficient cash", "SSI mismatch",
           "Late instruction", "Counterparty fail"]
st_rows = []
for t in trades.itertuples():
    sd = pd.Timestamp(t.settle_date)
    if sd > AS_OF:
        st_rows.append((t.trade_id, t.settle_date, None, "PENDING", None, None))
        continue
    if rng.random() < fail_rate[t.counterparty_id]:
        reason = rng.choice(reasons, p=[0.35, 0.2, 0.2, 0.15, 0.1])
        late = int(rng.integers(1, 8))
        actual = sd + pd.offsets.BDay(late)
        if actual > AS_OF:
            st_rows.append((t.trade_id, t.settle_date, None, "FAILED", reason, None))
        else:
            st_rows.append((t.trade_id, t.settle_date, actual.date(), "SETTLED", reason, late))
    else:
        st_rows.append((t.trade_id, t.settle_date, t.settle_date, "SETTLED", None, 0))
settlements = pd.DataFrame(st_rows, columns=["trade_id", "expected_settle_date", "actual_settle_date",
                                             "status", "fail_reason", "days_late"])
settlements["days_late"] = settlements["days_late"].astype("Int64")

# DQ problems in trades (after settlements so every trade has one settlement row)
idx = rng.choice(trades.index, 15, replace=False)
dups = trades.loc[idx].copy()
for k in dups.trade_id:
    log("duplicate_trade_id", "trades", k)
trades = pd.concat([trades, dups], ignore_index=True)

for i in rng.choice(trades.index[:N], 8, replace=False):
    trades.at[i, "settle_date"] = (pd.Timestamp(trades.at[i, "trade_date"]) - pd.offsets.BDay(1)).date()
    log("settle_before_trade", "trades", trades.at[i, "trade_id"])
for i in rng.choice(trades.index[:N], 10, replace=False):
    trades.at[i, "quantity"] = -abs(trades.at[i, "quantity"])
    trades.at[i, "trade_value"] = round(trades.at[i, "quantity"] * trades.at[i, "price"], 2)
    log("non_positive_quantity", "trades", trades.at[i, "trade_id"])
for i in rng.choice(trades.index[:N], 6, replace=False):
    trades.at[i, "currency"] = "GBP"
    log("currency_mismatch", "trades", trades.at[i, "trade_id"], "security currency differs")
for i in rng.choice(trades.index[:N], 5, replace=False):
    trades.at[i, "security_id"] = f"S9{rng.integers(100, 999)}"
    log("orphan_security_id", "trades", trades.at[i, "trade_id"], trades.at[i, "security_id"])

# ---------------------------------------------------------------- positions (as at AS_OF)
last_px = prices[prices.price_date == AS_OF.date()].set_index("security_id").close_price
pos_rows = []
for a in accounts.account_id:
    held = rng.choice(securities.security_id, int(rng.integers(15, 31)), replace=False)
    for sid in held:
        qty = int(rng.integers(1, 200)) * 500
        pos_rows.append({"position_date": AS_OF.date(), "account_id": a, "security_id": sid,
                         "isin": sec_info.at[sid, "isin"], "quantity": qty,
                         "market_value": round(qty * float(last_px[sid]), 2),
                         "currency": sec_info.at[sid, "currency"]})
custodian_positions = pd.DataFrame(pos_rows)

client_positions = custodian_positions[["position_date", "account_id", "security_id", "quantity"]].copy()
n_pos = len(client_positions)
qty_break = rng.choice(client_positions.index, int(n_pos * 0.03), replace=False)
for i in qty_break:
    delta = int(rng.choice([-1, 1]) * rng.integers(1, 20) * 100)
    client_positions.at[i, "quantity"] += delta
    log("recon_quantity_break", "client_positions",
        f"{client_positions.at[i, 'account_id']}|{client_positions.at[i, 'security_id']}", f"delta {delta}")
remaining = client_positions.index.difference(qty_break)
missing = rng.choice(remaining, int(n_pos * 0.01), replace=False)
for i in missing:
    log("recon_missing_at_client", "client_positions",
        f"{client_positions.at[i, 'account_id']}|{client_positions.at[i, 'security_id']}")
client_positions = client_positions.drop(index=missing)
extra = []
for _ in range(int(n_pos * 0.01)):
    a = rng.choice(accounts.account_id)
    held = set(custodian_positions.loc[custodian_positions.account_id == a, "security_id"])
    sid = rng.choice([s for s in securities.security_id if s not in held])
    extra.append({"position_date": AS_OF.date(), "account_id": a, "security_id": sid,
                  "quantity": int(rng.integers(1, 50)) * 500})
    log("recon_missing_at_custodian", "client_positions", f"{a}|{sid}")
client_positions = pd.concat([client_positions, pd.DataFrame(extra)], ignore_index=True)

# ---------------------------------------------------------------- write Projects 1-6 files
clients.to_csv(DATA / "clients.csv", index=False)
accounts.to_csv(DATA / "accounts.csv", index=False)
securities.to_csv(DATA / "securities.csv", index=False)
counterparties.to_csv(DATA / "counterparties.csv", index=False)
prices.to_csv(DATA / "prices.csv", index=False)
trades.to_csv(DATA / "trades.csv", index=False)
settlements.to_csv(DATA / "settlements.csv", index=False)
custodian_positions.to_csv(DATA / "custodian_positions.csv", index=False)
client_positions.to_csv(DATA / "client_positions.csv", index=False)

# Project 3 inputs: the fund manager's file looks different on purpose
fm = client_positions.merge(securities[["security_id", "ticker", "security_name"]], on="security_id", how="left")
fm_out = pd.DataFrame({
    "Portfolio Code": fm.account_id,
    "Ticker": fm.ticker,
    "Security Description": fm.security_name.str.upper(),
    "Holding Date": pd.to_datetime(fm.position_date).dt.strftime("%d/%m/%Y"),
    "Units": fm.quantity.map(lambda q: f"{q:,}"),
})
fm_out.to_excel(DATA / "fund_manager_positions.xlsx", index=False, sheet_name="Holdings")
tmap = securities[["ticker", "isin"]].dropna()
unmapped = rng.choice(tmap.index, 2, replace=False)
for i in unmapped:
    log("ticker_not_in_map", "ticker_isin_map", tmap.at[i, "ticker"])
tmap.drop(index=unmapped).to_csv(DATA / "ticker_isin_map.csv", index=False)

# ================================================================= Project 7
p7_as_of = AS_OF
managers = ["Manager A - Australian Equities", "Manager B - Global Equities",
            "Manager C - Fixed Income", "Manager D - Unlisted Assets"]
listed = securities.dropna(subset=["isin"]).copy()
aus_eq = listed[(listed.asset_class == "Equity") & (listed.market == "ASX")].sample(45, random_state=1)
glb_eq = listed[(listed.asset_class == "Equity") & (listed.market != "ASX")].sample(20, random_state=2)
bonds = listed[listed.asset_class == "Bond"].sample(25, random_state=3)

unlisted_types = ["Unlisted property", "Infrastructure", "Private equity"]
unlisted = pd.DataFrame({
    "outgoing_code": [f"UL-{i:03d}" for i in range(1, 16)],
    "incoming_code": [f"PRV{i:04d}" for i in range(1, 16)],
    "security_name": [f"Fictional {['Property', 'Infrastructure', 'Private Equity'][i % 3]} Trust {i:02d}" for i in range(1, 16)],
    "asset_class": [unlisted_types[i % 3] for i in range(1, 16)],
})

hold = []
for df, mgr in [(aus_eq, managers[0]), (glb_eq, managers[1]), (bonds, managers[2])]:
    for s in df.itertuples():
        qty = int(rng.integers(5, 400)) * 1000 if s.asset_class != "Bond" else int(rng.integers(10, 200)) * 100000
        px = float(last_px[s.security_id]) if s.asset_class != "Bond" else float(last_px[s.security_id]) / 100
        mv = round(qty * px, 2)
        accrued = round(mv * rng.uniform(0.002, 0.012), 2) if s.asset_class == "Bond" else 0.0
        hold.append({"portfolio": mgr, "id_type": "ISIN", "security_id": s.isin, "security_name": s.security_name,
                     "asset_class": "Fixed income" if s.asset_class == "Bond" else
                     ("Australian equities" if s.market == "ASX" else "Global equities"),
                     "quantity": qty, "market_value_aud": mv, "accrued_income_aud": accrued})
for u in unlisted.itertuples():
    mv = round(float(rng.uniform(5, 25)) * 1e6, 2)
    hold.append({"portfolio": managers[3], "id_type": "INTERNAL", "security_id": u.outgoing_code,
                 "security_name": u.security_name, "asset_class": u.asset_class,
                 "quantity": 1, "market_value_aud": mv, "accrued_income_aud": 0.0})
outgoing = pd.DataFrame(hold)
outgoing.insert(0, "as_at_date", p7_as_of.date())

# Incoming custodian: different column names and codes, plus transition breaks
inc = outgoing.copy()
inc["security_id"] = inc.apply(
    lambda r: unlisted.set_index("outgoing_code").at[r.security_id, "incoming_code"]
    if r.id_type == "INTERNAL" else r.security_id, axis=1)
listed_idx = inc.index[inc.id_type == "ISIN"]
miss = rng.choice(listed_idx, 3, replace=False)
for i in miss:
    log("p7_missing_at_incoming", "p7_incoming_custodian_holdings", inc.at[i, "security_id"])
qty_idx = rng.choice(listed_idx.difference(miss), 5, replace=False)
for i in qty_idx:
    factor = rng.choice([0.9, 0.95, 1.05, 1.1])
    old = inc.at[i, "quantity"]
    inc.at[i, "quantity"] = int(round(old * factor))
    inc.at[i, "market_value_aud"] = round(inc.at[i, "market_value_aud"] * inc.at[i, "quantity"] / old, 2)
    log("p7_quantity_break", "p7_incoming_custodian_holdings", inc.at[i, "security_id"], f"x{factor}")
bond_idx = inc.index[(inc.asset_class == "Fixed income")].difference(miss)
acc_idx = rng.choice(bond_idx, 6, replace=False)
for i in acc_idx:
    inc.at[i, "accrued_income_aud"] = 0.0
    log("p7_missing_accrued_income", "p7_incoming_custodian_holdings", inc.at[i, "security_id"])
inc = inc.drop(index=miss)
incoming = pd.DataFrame({
    "valuation_date": pd.to_datetime(inc.as_at_date).dt.strftime("%Y%m%d"),
    "account_code": inc.portfolio.str.split(" - ").str[0].str.replace("Manager ", "EXS-MGR-"),
    "sec_id": inc.security_id, "sec_id_type": inc.id_type.replace({"INTERNAL": "PRIVATE"}),
    "description": inc.security_name, "units": inc.quantity,
    "mv_aud": inc.market_value_aud, "accrued_aud": inc.accrued_income_aud,
})
outgoing.to_csv(P7 / "p7_outgoing_custodian_holdings.csv", index=False)
incoming.to_csv(P7 / "p7_incoming_custodian_holdings.csv", index=False)

# Incoming custodian's security master (4 unlisted assets have no mapping to the old code)
sm_listed = pd.concat([aus_eq, glb_eq, bonds])
sm = pd.DataFrame({
    "sec_id": sm_listed["isin"], "sec_id_type": "ISIN", "outgoing_code": None,
    "description": sm_listed.security_name,
    "asset_class": np.where(sm_listed.asset_class == "Bond", "Fixed income",
                            np.where(sm_listed.market == "ASX", "Australian equities", "Global equities")),
    "sector": rng.choice(["Financials", "Materials", "Energy", "Health care", "Industrials",
                          "Technology", "Utilities", "Government"], len(sm_listed)),
})
um = unlisted.copy()
no_map = rng.choice(um.index, 4, replace=False)
for i in no_map:
    log("p7_unmapped_security_id", "p7_security_master", um.at[i, "outgoing_code"])
um.loc[no_map, "outgoing_code"] = None
sm = pd.concat([sm, pd.DataFrame({
    "sec_id": um.incoming_code, "sec_id_type": "PRIVATE", "outgoing_code": um.outgoing_code,
    "description": um.security_name, "asset_class": um.asset_class, "sector": "Unlisted",
})], ignore_index=True)
sm.to_csv(P7 / "p7_security_master.csv", index=False)

# Prices for listed holdings, last ~3 months, with anomalies and stale prices
p7_days = pd.bdate_range("2026-04-01", p7_as_of)
p7_px = prices[(prices.security_id.isin(sm_listed.security_id)) &
               (pd.to_datetime(prices.price_date) >= p7_days[0])].copy()
p7_px = p7_px.merge(securities[["security_id", "isin"]], on="security_id")[["isin", "price_date", "close_price"]]
p7_px = p7_px.sort_values(["isin", "price_date"]).reset_index(drop=True)
spike_isins = rng.choice(aus_eq["isin"], 5, replace=False)
for isin in spike_isins:
    rows_i = p7_px.index[p7_px["isin"] == isin]
    j = rng.choice(rows_i[10:-5])
    p7_px.at[j, "close_price"] = round(p7_px.at[j, "close_price"] * rng.choice([1.35, 0.68]), 4)
    log("p7_price_anomaly", "p7_prices", isin, str(p7_px.at[j, "price_date"]))
stale_isins = rng.choice(list(set(sm_listed["isin"]) - set(spike_isins)), 4, replace=False)
for isin in stale_isins:
    rows_i = p7_px.index[p7_px["isin"] == isin]
    last8 = rows_i[-8:]
    p7_px.loc[last8, "close_price"] = p7_px.at[last8[0], "close_price"]
    log("p7_stale_price", "p7_prices", isin, "unchanged for last 8 business days")
p7_px.to_csv(P7 / "p7_prices.csv", index=False)

# Daily NAV per investment option, with two jumps
nav_rows = []
for opt, base, vol in [("Conservative", 1.85, 0.0015), ("Balanced", 2.40, 0.004), ("Growth", 2.95, 0.006)]:
    path = base * np.exp(np.cumsum(rng.normal(0.0002, vol, len(p7_days))))
    for d, v in zip(p7_days, path):
        nav_rows.append({"nav_date": d.date(), "investment_option": opt, "unit_price": round(float(v), 5)})
nav = pd.DataFrame(nav_rows)
for opt in ["Balanced", "Growth"]:
    j = rng.choice(nav.index[(nav.investment_option == opt)][20:-5])
    nav.at[j, "unit_price"] = round(nav.at[j, "unit_price"] * 1.06, 5)
    log("p7_nav_jump", "p7_nav", opt, str(nav.at[j, "nav_date"]))
nav.to_csv(P7 / "p7_nav.csv", index=False)

# Quarterly unlisted valuations: 3 stale, 1 missing entirely
val_rows = []
stale_un = rng.choice(unlisted.index, 4, replace=False)
missing_un, stale_three = stale_un[0], stale_un[1:]
for u in unlisted.itertuples():
    if u.Index == missing_un:
        continue
    dates = ["2025-09-30", "2025-12-31"] if u.Index in stale_three else ["2025-09-30", "2025-12-31", "2026-03-31"]
    v = float(rng.uniform(5, 25)) * 1e6
    for d in dates:
        v *= rng.uniform(0.97, 1.05)
        val_rows.append({"sec_id": u.incoming_code, "valuation_date": d, "valuation_aud": round(v, 2),
                         "valuer": rng.choice(["Independent valuer X (fictional)", "Manager valuation"])})
for i in stale_three:
    log("p7_stale_unlisted_valuation", "p7_unlisted_valuations", unlisted.at[i, "incoming_code"], "latest 2025-12-31")
log("p7_missing_unlisted_valuation", "p7_unlisted_valuations", unlisted.at[missing_un, "incoming_code"])
pd.DataFrame(val_rows).to_csv(P7 / "p7_unlisted_valuations.csv", index=False)

# Carbon data for listed equities, deliberately incomplete (coverage below 90% of equity value)
eq = pd.concat([aus_eq, glb_eq])
carbon = pd.DataFrame({"isin": eq["isin"],
                       "scope1_2_tco2e": rng.lognormal(10, 1.2, len(eq)).round(0),
                       "revenue_aud_m": rng.lognormal(6, 1.0, len(eq)).round(1),
                       "data_year": 2025})
eq_mv = outgoing[outgoing.asset_class.isin(["Australian equities", "Global equities"])] \
    .set_index("security_id").market_value_aud
order = eq_mv.sort_values(ascending=False).index
drop_isins, covered = [], eq_mv.sum()
for isin in order[2:]:  # drop a few large holdings until coverage is ~85%
    if covered / eq_mv.sum() <= 0.86:
        break
    drop_isins.append(isin)
    covered -= eq_mv[isin]
for isin in drop_isins:
    log("p7_missing_carbon_data", "p7_carbon", isin)
carbon[~carbon["isin"].isin(drop_isins)].to_csv(P7 / "p7_carbon.csv", index=False)

pd.DataFrame(issues).to_csv(DATA / "_injected_issues.csv", index=False)

print("Rows written:")
for name, df in [("trades", trades), ("settlements", settlements), ("prices", prices),
                 ("custodian_positions", custodian_positions), ("client_positions", client_positions),
                 ("p7 outgoing", outgoing), ("p7 incoming", incoming)]:
    print(f"  {name:22s}{len(df):>8,}")
print(f"  injected issues       {len(issues):>8,}")
