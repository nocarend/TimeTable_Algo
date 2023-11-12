import hashlib
from typing import List

import pysat.solvers
from pysat.formula import CNF

solver = pysat.solvers.Glucose3()

period_length = 2  # 2 hours
periods = 7  # number of lessons
duration = 1  #

groups = {1: "21215"}
teachers = {1: "volkov", 2: "pushkin"}
subjects = {
    1: "math_lec", 2: "math_prac", 3: "algebra_lec", 4: "algebra_prac",
    5: "algebra_lab"
}
counts = {1: 1, 2: 3, 3: 1, 4: 2, 5: 3}


def lessons_group(group):
    # group - [(lesson, teacher, ntimes in a week)]
    dict_groups = {
        1: [(1, 2, 1), (2, 1, 3), (3, 2, 1), (4, 2, 2), (5, 1, 3)]
    }
    return dict_groups[group]


def lessons_teacher(teacher: int):
    # teacher - subject - group - ntimes a week
    dict_teachers: dict = {
        2: {1: {1: 1}, 3: {1: 1}, 4: {1: 2}},
        1: {2: {1: 3}, 5: {1: 3}}
    }
    return dict_teachers[teacher]


"""
uncomplete calculations formula
жёстко влияет на производительность bound модуля
"""

mapa = {}


def tsgndp(t=0, s=0, g=0, n=0, d=0, p=0):
    # 100 teachers, 100 subjects, 100 groups, 60 times in a week,
    # 6 days in a week, 7 periods in a day
    h = int(
        hashlib.sha1(f"{t}_{s}_{g}_{n}_{d}_{p}".encode("utf-8")).hexdigest(),
        16) % 1000000
    """борьба с коллизиями и отображение хеша на переменную"""
    i = 0
    while h in mapa.keys() and mapa[h] != (t, s, g, n, d, p):
        h = int(hashlib.sha1(
            f"{t}_{s}_{g}_{n}_{d}_{p}_{i}".encode("utf-8")).hexdigest(),
                16) % 1000000
        i += 1
    return h


def tsgndp_calc(t, s, g, n, d, p):
    return tsgndp(t, s, g, n, d, p)


def tsgnd_calc(t, s, g, n, d):
    return tsgndp(t, s, g, n, d)


def tdp_calc(t, d, p):
    # return int(1e17) + tsgndp(t=t, d=d, p=p)
    return tsgndp(t, 0, 0, 0, d, p)


def gdp_calc(g, d, p):
    return tsgndp(0, 0, g, 0, d, p)


def gd_calc(g, d):
    return tsgndp(0, 0, g, 0, d, 0)


def td_calc(t, d):
    return tsgndp(t, 0, 0, 0, d, 0)


def tp_calc(t, p):
    return tsgndp(t, 0, 0, 0, 0, p)


def IKTDP(k, t, d=0, p=0):
    """A variable i^k_tdp is formed for each teacher t, day d, period p, and number k such
that 1 ≤ k ≤ duration(d)−2 and min(periods(d))+1 ≤ p ≤ max(periods(d))− k. It represents
 the fact that the teacher t has idle period of length k in the day d, starting with the period p"""
    h = int(
        hashlib.sha512(f"{k}_{t}_{d}_{p}".encode("utf-8")).hexdigest(),
        16) % 1000000
    """борьба с коллизиями и отображение хеша на переменную"""
    i = 0
    while h in mapa.keys() and mapa[h] != (k, t, d, p):
        h = int(
            hashlib.sha512(f"{k}_{t}_{d}_{p}_{i}".encode("utf-8")).hexdigest(),
            16) % 1000000
        i += 1
    return h


def ITDP(t, d, p):
    return IKTDP(0, t, d, p)


def IKTD(k, t, d):
    return IKTDP(k, t, d)


def IKT(k, t):
    """A variable itdp is formed for each teacher t, working day d and period
    p such that min(periods(d))+1 ≤ p ≤ max(periods(d))−1. It represents
    the fact that the teacher t has an idle period in the day d starting
    with the period p."""
    return IKTDP(k, t)


def LKGD(k, g, d):
    """Duration of a working day for student groups is encoded using variables l^k_gd which are formed for each group
    g, day d, and number k <= |periods(d)|. The variable l^k_gd represents the fact that teaching time for a group g
    spans for at least k periods (including idle periods) in a day d."""
    h = int(
        hashlib.md5(f"{k}_{g}_{d}".encode("utf-8")).hexdigest(),
        16) % 1000000
    """борьба с коллизиями и отображение хеша на переменную"""
    i = 0
    while h in mapa.keys() and mapa[h] != (k, g, d):
        h = int(
            hashlib.md5(f"{k}_{g}_{d}_{i}".encode("utf-8")).hexdigest(),
            16) % 1000000
        i += 1
    return h


def single(variables: List):
    l = []
    k = len(variables)
    for i in range(k):
        for j in range(i + 1, k):
            l.append([-variables[i], -variables[j]])
    return l


clauses = []
"""
пара не может идти > 1 периода

1. x_tsgndp ⇒ x_tsgnd - если в день d период p стоит пара, то точно в день d 
эта пара идёт

2. x_tsgnd ⇒ V_p t_tsgndp - если в день d стоит пара, то точно существует период p 
при котором это выполняется 

3. x_tsgndp ⇒ x_tdp - если учитель t даёт ведёт предмет s группе g n раз в 
неделю в день d парой p, то точно учитель t в день d парой p занят

4. x_tdp ⇒ V_tsgn x_tsgndp - если учитель t занят в день d парой p, то точно 
существуют предмет s и группа g, которые он ведёт в это время

5. x_tsgndp ⇒ x_gdp - если учитель ведёт предмет в данное время, то группа 
точно в это время там присутствует

6. x_gdp ⇒ V_tsgn x_tsgndp - если группа присутсвует в данное время, то точно в 
данное время ведётся каким-то учителем какой-то предмет 

7. x_tdp ⇒ x_td - если учитель ведёт пару в этот день, то он точно в этот день 
занят

8. x_td ⇒ V_p x_tdp - если учитель занят в этот день, то он точно ведёт хотя бы 
одну пару

9. x_tdp ⇒ x_tp - если учитель ведёт пару в данный период, то этот период у него точно занят

10. x_tp ⇒ V_d x_tdp - если у учителя данный период занят, то в один из дней этот период занят

11. i^k_tdp ⇔ (x_td(p−1) ∧ ^j¬x_td(p+j) ∧ x_td(p+k)) - учитель имеет период бездействия длины k в день d
 начиная с пары p. То есть пара p-1 есть и пара p+k есть, а между ними у него idle.

12. i^k_tdp ⇒ i^k_td - если учитель имеет idle время начиная с p пары, значит он точно имеет 
    в этот день idle время 

13. i^k_td ⇒ V_p i^k_tdp - если учитель имеет идле в этот день, значит точно существует пара,
    с которой этот период идёт

14. i^k_td ⇒ i^k_t - если учитель имеет идле период в данный день, то он когда-то имеет идле период

15. i^k_t ⇒ V_d i^k_td - если учитель имеет идле период, то в один из дней он точно есть.

16. i^k_tdp ⇒ i_tdp - если учитель имеет в это время идле период длиной k, 
    то он точно имеет идле период.

17. i_tdp ⇒ V_k i^k_tdp - если учитель имеет идле период в это время,
    то он имеет когда-то идле периож длиной k.
    
18. single({v1,_,vk}) = ^ (¬v_i V ¬v_j) | (1 <= i <= j <= k) - Только одна переменная из {} может быть истина.

todo 19. cardinality({v1, ..., v_k}) <= m - максимум m переменных могут быть истины.

todo 20. single({x_tsgnd | d in days}) и for each d in days single({x'_tsgndp | p in periods(d)})
 - каждый предмет шедулится ровно один раз в расписании ??? непон
 
21. single({x_tsgndp | tsgn in lessons(g)}) - каждая группа может находиться на одной паре одновременно

todo 22. x_tsg1ndp <=> x_tsgjndp, 1 < j <= k - каждый учитель может вести один предмет в одно премя.
 Однако несколько групп могут вестись одновременно. ??? надо ли

23. Forbidden and requested working hours. Forbidden hours and explicit
working hours for teachers are directly encoded by negation of variables xtdp,
xtd, and xtp. Forbidden hours for groups are encoded using the variables xgdp.
These constraints are represented by single literal clauses.

todo 24. Number of teaching days. The condition that a teacher t teaches for exactly
n days in a week is encoded by
cardinality(fxtd j d 2 daysg)  n ^ cardinality(f:xtd j d 2 daysg)  jdaysj􀀀n

not finished 25. x_gdp ^ xgd(p+k-1) ) => l^kgd for all p such that min(periods(d)) <= p <= max(periods(d)) - k + 1, 
and l^kgd => V min(periods(d)) <= p <= max(periods(d)) - k + 1 (x_gdp ^ x_gd(p+k-1))

26. The requirement that a work day duration for a group is limited to n periods,
is encoded by single literal constraints not l_kgd, for each k > n.

27. The requirement that a work day duration for a group is at least n periods is encoded by the constraint x_gd => l^n_gd.

Work day duration for teachers is encoded in a similar way.

todo 28. x_tsgnd => x'_tsgndp1 V ... V x'_tsgndp_n - The requirement that a lesson can begin only in period p1, p2, 
. . . , or pn 

todo 29. x'_tsgndp => (... last p .13

Idle periods constrains, p.13
"""

"""begin 27"""


def group_work_day_minimum(g, d, n):
    clauses.append([-gd_calc(g, d), LKGD(n, g, d)])


"""end 27"""

"""begin 26"""


def group_work_day_limited(g, d, n):
    for k in range(n + 1, 8):
        clauses.append([-LKGD(k, g, d)])


"""end 26"""

"""begin 23"""


def forbidden_hour_for_teacher(t, d, p):
    clauses.append([-tdp_calc(t, d, p)])
    clauses.append([-td_calc(t, d)])
    clauses.append(([-tp_calc(t, p)]))


def forbidden_hour_for_group(g, d, p):
    clauses.append([-gdp_calc(g, d, p)])


"""end 23"""

"""begin 25"""


def minimal_group_work_day(g, d, k):
    """idle periods are included
    k!=1"""
    for p in range(1, 8 - k + 1):
        clauses.append([-gdp_calc(g, d, p), -gdp_calc(g, d, p + k - 1), LKGD(k, g, d)])
    """page 13 second cond how???"""


"""end 25"""

for t in teachers.keys():
    tsgn = lessons_teacher(t)
    for s in tsgn.keys():
        for g in tsgn[s].keys():
            for n in range(1, tsgn[s][g] + 1):
                for d in range(1, 7):
                    v_p_x_tsgndp = []
                    for p in range(1, 8):
                        x_tsgndp = tsgndp_calc(t, s, g, n, d, p)
                        x_tdp = tdp_calc(t, d, p)
                        x_td = td_calc(t, d)
                        v_p_x_tsgndp.append(x_tsgndp)
                        """begin 1"""
                        clauses.append(
                            [-x_tsgndp, tsgnd_calc(t, s, g, n, d)])
                        """end 1"""
                        """begin 3"""
                        clauses.append([-x_tsgndp, x_tdp])
                        """end 3"""
                    """begin 2"""
                    clauses.append([-tsgnd_calc(t, s, g, n, d),
                                    *v_p_x_tsgndp])
                    """end 2"""

for t in teachers.keys():
    tsgn = lessons_teacher(t)
    for d in range(1, 7):
        for p in range(1, 8):
            v_tsgn_x_tsgndp = []
            for s in tsgn.keys():
                for g in tsgn[s].keys():
                    for n in range(1, tsgn[s][g] + 1):
                        v_tsgn_x_tsgndp.append(tsgndp_calc(t, s, g, n, d, p))
            """begin 4"""
            clauses.append([-tdp_calc(t, d, p), *v_tsgn_x_tsgndp])
            """end 4"""

for g in groups.keys():
    tsgn = lessons_group(g)
    for d in range(1, 7):
        for p in range(1, 8):
            x_gpd = gdp_calc(g, d, p)
            v_tsgn_x_tsgndp = []
            for stn in tsgn:
                s = stn[0]
                t = stn[1]
                for n in range(1, stn[2] + 1):
                    v_tsgn_x_tsgndp.append(tsgndp_calc(t, s, g, n, d, p))
                    """begin 5"""
                    clauses.append([-tsgndp_calc(t, s, g, n, d, p), x_gpd])
                    """end 5"""
            """begin 21"""
            s = single(v_tsgn_x_tsgndp)
            for clause in s:
                clauses.append(clause)
            """end 21"""
            """begin 6"""
            clauses.append([-x_gpd, *v_tsgn_x_tsgndp])
            """end 6"""

for t in teachers:
    for d in range(1, 7):
        v_p_x_tdp = []
        x_td = td_calc(t, d)
        for p in range(1, 8):
            x_tdp = tdp_calc(t, d, p)
            """begin 7"""
            clauses.append([-x_tdp, x_td])
            """end 7"""
            v_p_x_tdp.append(x_tdp)
        """begin 8"""
        clauses.append([-x_td, *v_p_x_tdp])
        """end 8"""

for t in teachers:
    for p in range(1, 8):
        v_d_x_tdp = []
        x_tp = tp_calc(t, p)
        for d in range(1, 7):
            x_tdp = tdp_calc(t, d, p)
            v_d_x_tdp.append(x_tdp)
            """begin 9"""
            clauses.append([-x_tdp, x_tp])
            """end 9"""
        """begin 10"""
        clauses.append([-x_tp, *v_d_x_tdp])
        """end 10"""

for k in range(1, 6):
    for t in teachers:
        i_k_t = IKT(k, t)
        v_d_i_k_td = []
        for d in range(1, 7):
            i_k_td = IKTD(k, t, d)
            v_d_i_k_td.append(i_k_td)
            v_p_i_k_tdp = []
            for p in range(2, 8 - k):
                i_k_tdp = IKTDP(k, t, d, p)
                x_tdp_1 = tdp_calc(t, d, p - 1)
                x_tdp_k = tdp_calc(t, d, p + k)
                v_j_x_tdp_j = []
                """begin 11"""
                clauses.append([-i_k_tdp, x_tdp_1])
                for j in range(k):
                    x_tdp_j = tdp_calc(t, d, p + j)
                    clauses.append([-i_k_tdp, -x_tdp_j])
                    v_j_x_tdp_j.append(x_tdp_j)
                clauses.append([-i_k_tdp, x_tdp_k])
                clauses.append([-x_tdp_1, *v_j_x_tdp_j, -x_tdp_k, -i_k_tdp])
                """end 11"""
                """begin 12"""
                clauses.append([-i_k_tdp, i_k_td])
                """end 12"""
                v_p_i_k_tdp.append(i_k_tdp)
            """begin 13"""
            clauses.append([-i_k_td, *v_p_i_k_tdp])
            """end 13"""
            """begin 14"""
            clauses.append([-i_k_td, i_k_t])
            """end 14"""
        """begin 15"""
        clauses.append([-i_k_t, *v_d_i_k_td])
        """end 15"""

for t in teachers:
    for d in range(1, 7):
        for p in range(2, 7):
            i_tdp = ITDP(t, d, p)
            v_k_i_k_tdp = []
            for k in range(1, 8 - p):
                i_k_tdp = IKTDP(k, t, d, p)
                v_k_i_k_tdp.append(i_k_tdp)  # багуля
                """begin 16"""
                clauses.append([-i_k_tdp, i_tdp])
                """end 16"""
            """begin 17"""
            clauses.append([-i_tdp, *v_k_i_k_tdp])
            """end 17"""

cnf = CNF()
print(clauses)
cnf.from_clauses(clauses)
print(len(clauses))
solver.append_formula(cnf)
print(solver.solve())
# print(solver.get_model())
