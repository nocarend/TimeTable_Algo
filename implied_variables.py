import hashlib
from typing import List

map_tsgndpr = {}
map_iktdp = {}
map_lkgd = {}

MOD = 10000000


def tsgndpr(t=0, s=0, g=0, n=0, d=0, p=0, r=0):
    # 100 teachers, 100 subjects, 100 groups, 60 times in a week,
    # 6 days in a week, 7 periods in a day, rooms
    h = int(
        hashlib.shake_256(f"{t}_{s}_{g}_{n}_{d}_{p}_{r}".encode("utf-8")).hexdigest(20),
        16) % MOD + 1
    """борьба с коллизиями и отображение хеша на переменную"""
    i = 0
    while h in map_tsgndpr and map_tsgndpr[h] != (t, s, g, n, d, p, r):
        h = int(hashlib.sha1(
            f"{t}_{s}_{g}_{n}_{d}_{p}_{r}_{i}".encode("utf-8")).hexdigest(),
                16) % MOD + 1
        i += 1
    map_tsgndpr[h] = (t, s, g, n, d, p, r)
    return h


def iktdp(k=0, t=0, d=0, p=0):
    """A variable i^k_tdp is formed for each teacher t, day d, period p, and number k such
that 1 ≤ k ≤ duration(d)−2 and min(periods(d))+1 ≤ p ≤ max(periods(d))− k. It represents
 the fact that the teacher t has idle period of length k in the day d, starting with the period p"""
    h = int(
        hashlib.sha512(f"{k}_{t}_{d}_{p}".encode("utf-8")).hexdigest(),
        16) % MOD + 1
    """борьба с коллизиями и отображение хеша на переменную"""
    i = 0
    while h in map_iktdp and map_iktdp[h] != (k, t, d, p):
        h = int(
            hashlib.sha512(f"{k}_{t}_{d}_{p}_{i}".encode("utf-8")).hexdigest(),
            16) % MOD + 1
        i += 1
    map_iktdp[h] = (k, t, d, p)
    return h


def lkgd(k=0, g=0, d=0):
    """Duration of a working day for student groups is encoded using variables l^k_gd which are formed for each group
    g, day d, and number k <= |periods(d)|. The variable l^k_gd represents the fact that teaching time for a group g
    spans for at least k periods (including idle periods) in a day d."""
    h = int(
        hashlib.md5(f"{k}_{g}_{d}".encode("utf-8")).hexdigest(),
        16) % MOD + 1
    """борьба с коллизиями и отображение хеша на переменную"""
    i = 0
    while h in map_lkgd and map_lkgd[h] != (k, g, d):
        h = int(
            hashlib.md5(f"{k}_{g}_{d}_{i}".encode("utf-8")).hexdigest(),
            16) % MOD + 1
        i += 1
    map_lkgd[h] = (k, g, d)
    return h


def assumption_hash(l: List):
    return hash(tuple(map(lambda x: hash(tuple(x)), l)))
