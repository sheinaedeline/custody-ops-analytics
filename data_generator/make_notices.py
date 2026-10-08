"""
Project 7, Stage E: create 10 fictional capital-call and distribution notices as PDFs,
in three different layouts, plus the answer key you will check AI extraction against.

    pip install reportlab pandas
    python data_generator/make_notices.py
"""

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parents[1] / "project7" / "notices"
OUT.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()
INVESTOR = "Example Super (fictional)"

notices = [
    # id, type, fund, currency, commitment, pct_called or None, amount, notice_date, due_date, layout
    ("N01", "Capital call", "Fictional Infrastructure Trust 01", "AUD", 20_000_000, 0.05, None, "2026-07-01", "2026-07-15", "letter"),
    ("N02", "Distribution", "Fictional Property Trust 03", "AUD", None, None, 412_750.00, "2026-07-02", "2026-07-10", "table"),
    ("N03", "Capital call", "Fictional Private Equity Trust 02", "USD", 15_000_000, 0.08, None, "2026-07-03", "2026-07-17", "breakdown"),
    ("N04", "Capital call", "Fictional Infrastructure Trust 04", "AUD", None, None, 1_250_000.00, "2026-07-06", "2026-07-20", "table"),
    ("N05", "Distribution", "Fictional Private Equity Trust 05", "USD", None, None, 87_300.50, "2026-07-07", "2026-07-14", "letter"),
    ("N06", "Capital call", "Fictional Property Trust 06", "AUD", 10_000_000, 0.10, None, "2026-07-08", "2026-07-22", "breakdown"),
    ("N07", "Distribution", "Fictional Infrastructure Trust 07", "AUD", None, None, 659_120.00, "2026-07-09", "2026-07-16", "table"),
    ("N08", "Capital call", "Fictional Private Equity Trust 08", "AUD", 25_000_000, 0.04, None, "2026-07-10", "2026-07-24", "letter"),
    ("N09", "Distribution", "Fictional Property Trust 09", "AUD", None, None, 230_000.00, "2026-07-13", "2026-07-20", "breakdown"),
    ("N10", "Capital call", "Fictional Infrastructure Trust 10", "USD", 12_000_000, 0.065, None, "2026-07-14", "2026-07-28", "table"),
]


def long_date(iso):
    return pd.Timestamp(iso).strftime("%-d %B %Y")


def slash_date(iso):
    return pd.Timestamp(iso).strftime("%d/%m/%Y")


key_rows = []
for nid, ntype, fund, ccy, commit, pct, amount, ndate, ddate, layout in notices:
    if amount is None:
        amount = round(commit * pct, 2)
    ref = f"{fund.split()[1][:3].upper()}-{nid}-2026"
    key_rows.append({"notice_id": nid, "file_name": f"{nid}_{ntype.replace(' ', '_').lower()}.pdf",
                     "notice_type": ntype, "fund_name": fund, "investor": INVESTOR, "currency": ccy,
                     "amount": amount, "notice_date": ndate, "due_date": ddate, "reference": ref})
    story = []
    doc = SimpleDocTemplate(str(OUT / key_rows[-1]["file_name"]), pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm)
    story.append(Paragraph(f"<b>{fund}</b>", styles["Title"]))
    story.append(Paragraph("FICTIONAL DOCUMENT FOR A TRAINING PORTFOLIO - NOT A REAL NOTICE", styles["Italic"]))
    story.append(Spacer(1, 8 * mm))

    if layout == "letter":
        verb = "contribute" if ntype == "Capital call" else "receive"
        story += [
            Paragraph(long_date(ndate), styles["Normal"]), Spacer(1, 4 * mm),
            Paragraph(f"To: {INVESTOR}", styles["Normal"]), Spacer(1, 4 * mm),
            Paragraph(f"<b>{ntype} notice</b> (our reference {ref})", styles["Heading3"]),
            Paragraph(
                f"Dear Investor, we write to advise that you are required to {verb} "
                f"<b>{ccy} {amount:,.2f}</b> in respect of your interest in the Fund. "
                + (f"This represents {pct:.1%} of your total commitment of {ccy} {commit:,.0f}. " if pct else "")
                + f"Payment {'is due' if ntype == 'Capital call' else 'will be made'} on or before "
                  f"{long_date(ddate)}.", styles["Normal"]),
            Spacer(1, 6 * mm),
            Paragraph("Yours sincerely,<br/>Fund Administration Team (fictional)", styles["Normal"]),
        ]
    elif layout == "table":
        rows = [["Notice type", ntype.upper()], ["Investor", INVESTOR], ["Notice date", slash_date(ndate)],
                ["Value date", slash_date(ddate)], ["Currency", ccy], ["Net amount", f"{amount:,.2f}"],
                ["Reference", ref]]
        t = Table(rows, colWidths=[50 * mm, 100 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                               ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                               ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold")]))
        story.append(t)
    else:  # breakdown: amount must be worked out or read from the bottom line
        story += [Paragraph(f"{ntype} - Investor statement", styles["Heading3"]),
                  Paragraph(f"Investor: {INVESTOR} &nbsp;&nbsp; Issued: {long_date(ndate)} &nbsp;&nbsp; Ref: {ref}",
                            styles["Normal"]), Spacer(1, 4 * mm)]
        if ntype == "Capital call":
            rows = [["Item", f"Amount ({ccy})"], ["Total commitment", f"{commit:,.0f}"],
                    ["Percentage called this notice", f"{pct:.1%}"],
                    ["Gross amount called", f"{amount + 2500:,.2f}"],
                    ["Less: equalisation credit", "(2,500.00)"],
                    ["Amount payable", f"{amount:,.2f}"]]
        else:
            rows = [["Item", f"Amount ({ccy})"], ["Income distribution", f"{amount * 0.7:,.2f}"],
                    ["Capital distribution", f"{amount * 0.3:,.2f}"], ["Total distribution", f"{amount:,.2f}"]]
        t = Table(rows, colWidths=[90 * mm, 60 * mm])
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
                               ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.black),
                               ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                               ("ALIGN", (1, 0), (1, -1), "RIGHT")]))
        story += [t, Spacer(1, 4 * mm),
                  Paragraph(f"Settlement date: {long_date(ddate)}", styles["Normal"])]
    doc.build(story)

pd.DataFrame(key_rows).to_csv(OUT.parent / "p7_notice_answer_key.csv", index=False)
print(f"Wrote {len(key_rows)} notices to {OUT}")
