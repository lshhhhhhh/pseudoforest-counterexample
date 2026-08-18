# A planar triangulation with no partition into two induced pseudoforests

**Answer to Problem 1 of L. Ploscaru (20th Emléktábla Workshop, 2026, p. 17): NO.**

There is a planar triangulation **T\*** on **58 vertices** whose vertex set cannot be
partitioned into two sets each inducing a pseudoforest (= every component has at
most one cycle); equivalently, T\* admits no orientation with
min(d⁺(v), d⁻(v)) ≤ 1 at every vertex.

The construction substitutes three copies of (BBL − v) — the 38-vertex
Barnette–Bosák–Lederberg graph minus a vertex — into K₄, and takes the planar
dual of the resulting 112-vertex cubic graph. The human-readable proof uses an
Euler-characteristic "region rank" identity for the curve system that any
candidate partition induces in the dual, plus a pigeonhole argument; the only
external ingredient is the non-Hamiltonicity of the BBL graph. By exhaustive
SAT verification every planar triangulation on n ≤ 17 vertices IS partitionable,
so a minimum counterexample has between 18 and 58 vertices.

**Paper:** [`paper/main.pdf`](paper/main.pdf) (LaTeX source included).

## Verify it yourself (no trust required)

```
pip install networkx python-sat
python verify_counterexample.py
```

Expected output ends with `ALL CHECKS PASSED - T* is a counterexample.`
The verifier performs five checks from the archived adjacency lists alone:
structure of both graphs, T\* = dual(G\*), non-Hamiltonicity of the base graph,
a positive control (with a direct degree check of a returned orientation), and
the final infeasibility (SAT, CaDiCaL). Theorem B (all n <= 17 feasible) has a
separate audit package under `verification/` (model-verifying sweep script,
per-order logs, environment hashes). The claim was
additionally confirmed by three independently written encodings under multiple
solvers, positive/mechanism controls (0, 1, 2 BBL fragments → feasible; 3 → not),
and an adversarial review pass.

The triangulation itself, as a graph6 string (58 vertices):

```
y|XMGMm?k@?A@P?t__p_??AEOGX??p@OSCs_O??EC??_??BO??CO_??_O??GC??u?_??C???GO???B?????SA???j????Oo????G???A_@???B@B???C?B???AA`G???Aq__??A??????G??K??????SC?????CA?????@?_?A??AoC??????_??@???A???????A???????W_O?????DW??????AE??????B?????????CG???O??GGW??????O?W??????GSD???????Uc?
```

## Contents

| Path | What it is |
|---|---|
| `paper/` | The paper (PDF + LaTeX source + figures) |
| `verify_counterexample.py` | Self-contained verifier (start here) |
| `data/counterexample_58.json` | Adjacency lists + graph6 for T\* (58) and G\* (112) |
| `scripts/` | Research-archive scripts: construction, independent encodings, mechanism controls, lemma checks (paths are machine-specific; kept for transparency) |

## Attribution & AI disclosure

Author: Shaoheng Lai (laishaoheng1996@gmail.com). This work was carried out in
close collaboration with an AI assistant (Anthropic Claude: Fable 5 / Opus 5),
which proposed and executed the experimental programme, the construction, and
proof drafts under the author's direction; an independent adversarial AI review
pass re-derived the proofs and re-implemented all machine checks. All claims are mechanically checkable via the included scripts (standard
libraries and SAT solvers are still trusted). The AI system is not an
author.

## License

Code and data: MIT. Paper text (`paper/`): CC BY 4.0.

*Posted 2026-08-18 to establish priority; comments and endorsement inquiries welcome.*
