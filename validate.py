"""Validate cold_chain.ttl and run every query in queries.rq.

Usage:  python validate.py            (prints a report, writes results.txt)
        python validate.py --csv out  (also writes one CSV per query result)

Steps
  1. Parse the Turtle file (syntax check) and count triples.
  2. Vocabulary check: every predicate and class used in the data is declared.
  3. Domain/range check: every subject/object already has the declared
     domain/range type (via rdf:type + rdfs:subClassOf), so the RDFS
     domain/range rules add no surprising new types.
  4. Compute the RDFS closure (owlrl) and run all queries on the explicit
     graph and on the inferred graph.
  5. Compare each query's row count with the expected count below; any
     mismatch makes the script exit with code 1.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import owlrl
from rdflib import Graph, RDF, RDFS, OWL, URIRef

HERE = Path(__file__).parent
TTL = HERE / "cold_chain.ttl"
RQ = HERE / "queries.rq"
VOCAB = "http://example.org/coldchain/vocab#"
BUILTIN = (str(RDF), str(RDFS), str(OWL))

# Expected row counts (see the "Expected:" comment above each query).
# Q7 runs twice: without and with RDFS inference.
EXPECTED_ROWS = {"Q1": 1, "Q2": 2, "Q3": 2, "Q4": 1, "Q5": 2, "Q6": 2, "Q7": 0, "Q7+inference": 14, "Q8": 0, "Q9": 1}

out_lines = []


def say(line=""):
    print(line)
    out_lines.append(line)


def short(term, g):
    try:
        return g.namespace_manager.normalizeUri(term) if isinstance(term, URIRef) else str(term)
    except Exception:
        return str(term)


def load_queries():
    text = RQ.read_text()
    prefix_block = "\n".join(l for l in text.splitlines() if l.startswith("PREFIX"))
    parts = re.split(r"^#### ", text, flags=re.M)[1:]
    queries = []
    for part in parts:
        title = part.splitlines()[0].strip()
        body = "\n".join(l for l in part.splitlines()[1:] if not l.lstrip().startswith("#"))
        queries.append((title, prefix_block + "\n" + body))
    return queries


def run(g, q):
    res = g.query(q)
    return [tuple(short(v, g) if v is not None else "" for v in row) for row in res], [str(v) for v in res.vars]


def print_table(rows, cols, key, mismatches):
    say("    " + " | ".join(cols))
    for r in rows:
        say("    " + " | ".join(r))
    expected = EXPECTED_ROWS.get(key)
    ok = expected is None or expected == len(rows)
    say(f"    ({len(rows)} rows; expected {expected}: {'OK' if ok else 'MISMATCH'})")
    if not ok:
        mismatches.append(key)


def subclass_closure(g):
    sup = {}
    for c, d in g.subject_objects(RDFS.subClassOf):
        sup.setdefault(c, set()).add(d)
    def ups(c, seen=None):
        seen = seen or {c}
        for d in sup.get(c, ()):
            if d not in seen:
                seen.add(d)
                ups(d, seen)
        return seen
    return ups


def write_csv(directory, key, rows, cols):
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / f"{key.replace('+', '_')}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", type=Path, metavar="DIR", help="write each query result to DIR/<query>.csv")
    args = ap.parse_args(argv)

    g = Graph()
    g.parse(TTL, format="turtle")
    say(f"[1] Syntax OK - {TTL.name} parsed, {len(g)} explicit triples")

    # [2] vocabulary check
    declared_props = set(g.subjects(RDF.type, RDF.Property))
    declared_classes = set(g.subjects(RDF.type, RDFS.Class))
    undeclared = set()
    for p in set(g.predicates()):
        if str(p).startswith(VOCAB) and p not in declared_props:
            undeclared.add(p)
    for c in set(g.objects(None, RDF.type)):
        if str(c).startswith(VOCAB) and c not in declared_classes:
            undeclared.add(c)
    say(f"[2] Vocabulary: {len(declared_classes)} classes, {len(declared_props)} properties; "
        f"undeclared terms used: {len(undeclared)}")
    for t in undeclared:
        say(f"    UNDECLARED {short(t, g)}")

    # [3] domain/range check
    ups = subclass_closure(g)
    types = {}
    for s, c in g.subject_objects(RDF.type):
        types.setdefault(s, set()).update(ups(c))
    problems = []
    for p in declared_props:
        dom = g.value(p, RDFS.domain)
        rng = g.value(p, RDFS.range)
        for s, o in g.subject_objects(p):
            if dom is not None and dom not in types.get(s, ()):
                problems.append(f"{short(s, g)} used as subject of {short(p, g)} but is not a {short(dom, g)}")
            if rng is not None and not str(rng).startswith("http://www.w3.org/2001/XMLSchema#") \
                    and rng not in types.get(o, ()):
                problems.append(f"{short(o, g)} used as object of {short(p, g)} but is not a {short(rng, g)}")
    say(f"[3] Domain/range check: {len(problems)} violations")
    for pr in problems:
        say("    " + pr)

    # [4] inference + queries
    gi = Graph()
    for t in g:
        gi.add(t)
    for pfx, ns in g.namespaces():
        gi.bind(pfx, ns, override=True)
    owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(gi)
    say(f"[4] RDFS closure (owlrl): {len(gi)} triples ({len(gi) - len(g)} inferred, "
        f"incl. RDFS axiomatic triples)")

    mismatches = []
    for title, q in load_queries():
        key = title.split()[0]
        say()
        say(f"=== {title}")
        rows, cols = run(g, q)
        if key == "Q7":
            say("  without inference:")
            print_table(rows, cols, key, mismatches)
            if args.csv:
                write_csv(args.csv, key, rows, cols)
            rows, cols = run(gi, q)
            say("  with RDFS inference:")
            key = "Q7+inference"
        print_table(rows, cols, key, mismatches)
        if args.csv:
            write_csv(args.csv, key, rows, cols)

    say()
    say(f"[5] Expected row counts: {len(EXPECTED_ROWS) - len(mismatches)}/{len(EXPECTED_ROWS)} match"
        + (f" - MISMATCH in {', '.join(mismatches)}" if mismatches else ""))

    (HERE / "results.txt").write_text("\n".join(out_lines) + "\n")
    print("\nWrote results.txt")
    return 1 if (undeclared or problems or mismatches) else 0


if __name__ == "__main__":
    sys.exit(main())
