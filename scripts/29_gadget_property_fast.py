"""B 性质快速版: B=BBL-0, ∀端口对, ∀|S|<=2: B-S 无端口间哈密顿路.
编码: 边变量, 度约束 (a,b 度1, 其余度2), 惰性子回路消除."""
import sys
from itertools import combinations

import networkx as nx
from pysat.solvers import Cadical195

sys.stdout.reconfigure(line_buffering=True)

BBL = [[1,2,3],[0,33,37],[0,32,36],[0,34,35],[8,14,18],[9,15,19],[9,10,17],[8,11,16],
       [4,7,13],[5,6,12],[6,12,21],[7,13,20],[9,10,24],[8,11,25],[4,16,30],[5,17,31],
       [7,14,23],[6,15,22],[4,25,29],[5,24,28],[11,23,27],[10,22,26],[17,21,35],
       [16,20,34],[12,19,33],[13,18,32],[21,27,37],[20,26,36],[19,31,33],[18,30,32],
       [14,29,34],[15,28,35],[2,25,29],[1,24,28],[3,23,30],[3,22,31],[2,27,37],[1,26,36]]


def ham_path(G, a, b):
    if a not in G or b not in G or not nx.is_connected(G): return False
    edges = sorted(tuple(sorted(e)) for e in G.edges())
    eidx = {e: i + 1 for i, e in enumerate(edges)}
    cnf = []
    for v in G.nodes():
        inc = [eidx[tuple(sorted((v, w)))] for w in G.neighbors(v)]
        need = 1 if v in (a, b) else 2
        if len(inc) < need: return False
        # 度 = need: 至少 need (组合下界), 至多 need (组合上界)
        for comb in combinations(inc, len(inc) - need + 1):
            cnf.append(list(comb))                       # >= need
        for comb in combinations(inc, need + 1):
            cnf.append([-x for x in comb])               # <= need
    with Cadical195(bootstrap_with=cnf) as s:
        while s.solve():
            model = set(s.get_model())
            chosen = [e for e, i in eidx.items() if i in model]
            H = nx.Graph(chosen)
            comps = list(nx.connected_components(H))
            path_comp = next(c for c in comps if a in c)
            if b in path_comp and len(comps) == 1:
                return True
            # 消除不含 a 的每个圈分量
            blocked = False
            for c in comps:
                if a in c and b in c: continue
                ces = [eidx[e] for e in chosen if e[0] in c and e[1] in c]
                if ces:
                    s.add_clause([-x for x in ces]); blocked = True
            if not blocked:
                s.add_clause([-eidx[e] for e in chosen])
    return False


Gb = nx.Graph()
for u, nbrs in enumerate(BBL):
    for v in nbrs: Gb.add_edge(u, v)
B = Gb.copy(); B.remove_node(0)

viol = tested = 0
samples = []
for a, b in combinations((1, 2, 3), 2):
    cands = [v for v in B.nodes() if v not in (a, b)]
    Ss = [()] + [(x,) for x in cands] + list(combinations(cands, 2))
    for S in Ss:
        tested += 1
        H = B.copy(); H.remove_nodes_from(S)
        if ham_path(H, a, b):
            viol += 1
            if len(samples) < 8: samples.append((a, b, S))
print(f"B性质(快): 测试 {tested}, 违例 {viol}")
for s in samples: print("  违例:", s)
