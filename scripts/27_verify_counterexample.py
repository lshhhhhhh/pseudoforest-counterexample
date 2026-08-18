"""反例验证链 A/B/D:
A. 阳性对照: 同一 solve() 代码跑已知可行的三角剖分 (正二十面体) => 应 SAT
D. BBL 非哈密顿性: SAT 搜 Ham 圈 => 应 UNSAT
B. 部件性质: B=BBL-0, ∀端口对 {a,b}⊂{1,2,3}, ∀S⊆V(B)∖{a,b}, |S|<=2:
   B-S 中 a,b 间无哈密顿路 (覆盖 B-S 全部顶点)? 全部成立 => 鸽笼手证覆盖宽松版
"""
import sys
from itertools import combinations

import networkx as nx
from pysat.solvers import Cadical195
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

BBL = [[1,2,3],[0,33,37],[0,32,36],[0,34,35],[8,14,18],[9,15,19],[9,10,17],[8,11,16],
       [4,7,13],[5,6,12],[6,12,21],[7,13,20],[9,10,24],[8,11,25],[4,16,30],[5,17,31],
       [7,14,23],[6,15,22],[4,25,29],[5,24,28],[11,23,27],[10,22,26],[17,21,35],
       [16,20,34],[12,19,33],[13,18,32],[21,27,37],[20,26,36],[19,31,33],[18,30,32],
       [14,29,34],[15,28,35],[2,25,29],[1,24,28],[3,23,30],[3,22,31],[2,27,37],[1,26,36]]

# ---------- A. 阳性对照 ----------
def solve_pf(T, tri_faces=None, strict=False):
    adjT = {v: sorted(T.neighbors(v)) for v in T.nodes()}
    edges = sorted(tuple(sorted(e)) for e in T.edges())
    eidx = {e: i for i, e in enumerate(edges)}
    mE = len(edges)
    cnf = []
    for v in T.nodes():
        outl, inl = [], []
        for w in adjT[v]:
            e = (min(v, w), max(v, w)); x = eidx[e] + 1
            if v == e[0]: outl.append(x); inl.append(-x)
            else: outl.append(-x); inl.append(x)
        mv = mE + v + 1
        for a, b in combinations(outl, 2): cnf.append([-mv, -a, -b])
        for a, b in combinations(inl, 2): cnf.append([mv, -a, -b])
    if strict and tri_faces:
        for (a, b, c) in tri_faces:
            cnf.append([-(mE+a+1), -(mE+b+1), -(mE+c+1)])
            cnf.append([mE+a+1, mE+b+1, mE+c+1])
    with Cadical195(bootstrap_with=cnf) as s:
        return s.solve()

ico = nx.icosahedral_graph()
print(f"A. 正二十面体 (n=12 三角剖分): 宽松={'SAT' if solve_pf(ico) else 'UNSAT?!'}")
# 再拿一个大的: T3 gadget 族? 用随机可行三角剖分 -- 取 plantri n=12 第一个
import subprocess
pr = subprocess.run([r"E:\math\vendor\plantri55\plantri.exe", "-a", "12"],
                    capture_output=True, text=True)
line = pr.stdout.strip().splitlines()[0]
head, _, rest = line.partition(" ")
rot = [[ord(c)-ord("a") for c in p] for p in rest.split(",")]
Tt = nx.Graph((u, v) for u, nb in enumerate(rot) for v in nb)
print(f"A2. plantri n=12 #1: 宽松={'SAT' if solve_pf(Tt) else 'UNSAT?!'}")

# ---------- D. BBL 非哈密顿 ----------
def ham_cycle_exists(G):
    """SAT: 2-因子 + 连通性靠惰性加割 (小图直接位置编码更稳: 用邻接矩阵DP太大,
    用 SAT 顺序编码: x[v][i] = v 在位置 i)."""
    nodes = sorted(G.nodes()); n = len(nodes)
    idx = {v: i for i, v in enumerate(nodes)}
    pool = IDPool()
    def X(v, i): return pool.id((v, i))
    cnf = []
    for v in nodes:
        cnf.append([X(v, i) for i in range(n)])
        for i, j in combinations(range(n), 2):
            cnf.append([-X(v, i), -X(v, j)])
    for i in range(n):
        cnf.append([X(v, i) for v in nodes])
        for u, v in combinations(nodes, 2):
            cnf.append([-X(u, i), -X(v, i)])
    cnf.append([X(nodes[0], 0)])
    adj = {v: set(G.neighbors(v)) for v in nodes}
    for i in range(n):
        for u in nodes:
            for v in nodes:
                if u != v and v not in adj[u]:
                    cnf.append([-X(u, i), -X(v, (i+1) % n)])
    with Cadical195(bootstrap_with=cnf) as s:
        return s.solve()

Gb = nx.Graph()
for u, nbrs in enumerate(BBL):
    for v in nbrs: Gb.add_edge(u, v)
print(f"D. BBL 有 Ham 圈: {ham_cycle_exists(Gb)}  (应 False)")

# ---------- B. 部件性质 ----------
def ham_path_exists(G, a, b):
    """G 中 a->b 哈密顿路 (覆盖全部顶点)."""
    nodes = sorted(G.nodes()); n = len(nodes)
    if a not in G or b not in G: return False
    if not nx.is_connected(G): return False
    pool = IDPool()
    def X(v, i): return pool.id((v, i))
    cnf = []
    for v in nodes:
        cnf.append([X(v, i) for i in range(n)])
        for i, j in combinations(range(n), 2):
            cnf.append([-X(v, i), -X(v, j)])
    for i in range(n):
        cnf.append([X(v, i) for v in nodes])
        for u, v in combinations(nodes, 2):
            cnf.append([-X(u, i), -X(v, i)])
    cnf.append([X(a, 0)]); cnf.append([X(b, n-1)])
    adj = {v: set(G.neighbors(v)) for v in nodes}
    for i in range(n - 1):
        for u in nodes:
            for v in nodes:
                if u != v and v not in adj[u]:
                    cnf.append([-X(u, i), -X(v, i+1)])
    with Cadical195(bootstrap_with=cnf) as s:
        return s.solve()

B = Gb.copy(); B.remove_node(0)
ports = [1, 2, 3]
viol = 0; tested = 0
Vb = [v for v in B.nodes()]
for a, b in combinations(ports, 2):
    # S 不含 a,b (端口须在路两端; 若端口被删则该穿越对不存在, 自动满足)
    cands = [v for v in Vb if v not in (a, b)]
    Ss = [()] + [(x,) for x in cands] + list(combinations(cands, 2))
    for S in Ss:
        tested += 1
        H = B.copy(); H.remove_nodes_from(S)
        if ham_path_exists(H, a, b):
            viol += 1
            if viol <= 5: print(f"  B违例: 端口({a},{b}) S={S} 存在Ham路!")
print(f"B. 部件性质: 测试 {tested} 组, 违例 {viol} (0 => 鸽笼手证直接覆盖宽松版)")
