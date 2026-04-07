"""
V4.1 – Aggressive Substring Mapping Engine — Verification Script
Tests _resolve_project() and _build_match_tables() by instantiating
a lightweight subclass that bypasses DB/Excel I/O.
"""
import sys, os, types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pathlib import Path
from reconciler import LennarQBReconciler

# ── Subclass that skips __init__ filesystem operations ────────────────────────
class TestReconciler(LennarQBReconciler):
    def __init__(self):
        # Skip parent __init__; inject dictionaries directly
        self.mapping_dict = {
            'WILTON MANORS':     'ALTESSA TH',
            'ABESS SOUTH 100':   'HERON POINTE 100S',
            'HERON POINTE 100S': 'HERON POINTE 100S',
            'ALTESSA TH':        'ALTESSA TH',
        }
        self.foreman_dict = {
            'ALTESSA TH':        'John Smith',
            'HERON POINTE 100S': 'Jane Doe',
        }
        self._build_match_tables()   # Uses the real method

rec = TestReconciler()

# ── Test cases ────────────────────────────────────────────────────────────────
PASS = "✅ PASS"
FAIL = "❌ FAIL"

tests = [
    ("Exact key match",                        "WILTON MANORS",                       "ALTESSA TH"),
    ("Key is substring – QB composite name",   "WILTON MANORS (ALTESSA TH)",          "ALTESSA TH"),
    ("Value is substring – Lennar padded",     "ALTESSA TH - PHASE A",                "ALTESSA TH"),
    ("Abess exact key",                        "ABESS SOUTH 100",                     "HERON POINTE 100S"),
    ("Key substring in longer QB name",        "ABESS SOUTH 100 (HERON POINTE 100S)", "HERON POINTE 100S"),
    ("Hard-coded alias: Vivant 2510460",       "VIVANT AT MIRAMAR 2510460",           "VIVANT 2510460"),
    ("Hard-coded alias: Vivant 2510660",       "VIVANT C 2510660 SOMETHING",          "VIVANT - 2510660"),
    ("Hard-coded alias: Redland",              "REDLAND RIDGE HOMES",                 "REDLAND RIDGE REDWOOD / REDLAND RIDGE SF"),
    ("Hard-coded alias: Dorta",                "DORTA DEVELOPMENT",                   "SP RESIDENTIAL VILLAS"),
    ("No-match passthrough",                   "COMPLETELY UNKNOWN PROJECT",           "COMPLETELY UNKNOWN PROJECT"),
]

print("\n" + "="*68)
print("  V4.1 Aggressive Mapping Engine — Unit Tests")
print("="*68)
all_passed = True
for desc, inp, expected in tests:
    result = rec._resolve_project(inp)
    ok     = result == expected
    if not ok:
        all_passed = False
    icon = PASS if ok else FAIL
    print(f"{icon}  {desc}")
    if not ok:
        print(f"       input:    {inp!r}")
        print(f"       expected: {expected!r}")
        print(f"       got:      {result!r}")

# ── Balance simulation: WILTON MANORS ↔ ALTESSA TH = $0.00 diff ──────────────
print("\n" + "-"*68)
print("  Balance simulation: WILTON MANORS QB ↔ ALTESSA TH Lennar → $0.00")
print("-"*68)

QBAmount     = 5_000.00
LennarAmount = 5_000.00

qb_proj     = rec._resolve_project("WILTON MANORS (ALTESSA TH)")
lennar_proj = rec._resolve_project("ALTESSA TH")

print(f"  QB resolved:     {qb_proj!r}  (${QBAmount:,.2f})")
print(f"  Lennar resolved: {lennar_proj!r}  (${LennarAmount:,.2f})")

if qb_proj == lennar_proj:
    diff   = round(LennarAmount - QBAmount, 2)
    icon   = PASS if diff == 0.00 else FAIL
    print(f"  Both map to same entity → Diff = ${diff:,.2f}  {icon}")
    if diff != 0.00:
        all_passed = False
else:
    print(f"  {FAIL} Projects do NOT match — would appear as separate rows in audit!")
    all_passed = False

# ── Foreman lookup verification ───────────────────────────────────────────────
print("\n" + "-"*68)
print("  Foreman lookup: ABESS SOUTH 100 → HERON POINTE 100S → Jane Doe")
print("-"*68)

proj    = rec._resolve_project("ABESS SOUTH 100 (HERON POINTE 100S)")
foreman = rec.foreman_dict.get(proj, "Pending Assignment")
ok = foreman == "Jane Doe"
if not ok:
    all_passed = False
icon = PASS if ok else FAIL
print(f"  Resolved project: {proj!r}")
print(f"  Foreman:          {foreman!r}  {icon}")

print("\n" + "="*68)
print(f"  FINAL: {'ALL TESTS PASSED ✅' if all_passed else 'SOME TESTS FAILED ❌'}")
print("="*68 + "\n")
sys.exit(0 if all_passed else 1)
