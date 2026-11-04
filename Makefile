# Common tasks. Run `make` (or `make all`) for every check that CI runs.
PY ?= python3

.PHONY: all validate shacl exports test figure csv

all: validate shacl exports test

validate:  ## vocabulary, domain/range, queries and row counts; rewrites results.txt
	$(PY) validate.py

shacl:  ## SHACL shapes; prints excursion warnings
	$(PY) shacl_check.py

exports:  ## check N-Triples / JSON-LD / RDF/XML still match the Turtle
	$(PY) export_formats.py --check

test:
	$(PY) -m pytest -q tests

figure:  ## regenerate figures/s101_subgraph.png and .svg
	$(PY) draw_graph.py

csv:  ## query results as CSV files in out/
	$(PY) validate.py --csv out
