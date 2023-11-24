import hashlib
import json
from itertools import combinations
from typing import List
import pysat.solvers
from pysat.formula import CNF

from constraints import periods, days
from implied_variables import iktdp, tsgndpr, lkgd, map_tsgndpr
from utils import single, cardinality, read_input

solver = pysat.solvers.Glucose3()

groups, teachers, group_lessons, teacher_lessons, rooms, subjects, original_rooms = read_input("config_example1.json")
print("G", groups)
print("T", teachers)
print("Groups", group_lessons)
print("Teachers", teacher_lessons)
print("Rooms", rooms)
print("Subjects", subjects)
"""
uncomplete calculations formula
жёстко влияет на производительность bound модуля
"""

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

not finished 25. x_gdp ^ xgd(p+k-1) ) => l^kgd for all p such that min(periods(d)) <= p <= max(periods(d)) - k + 1, 
and l^kgd => V min(periods(d)) <= p <= max(periods(d)) - k + 1 (x_gdp ^ x_gd(p+k-1))

26. The requirement that a work day duration for a group is limited to n periods,
is encoded by single literal constraints not l_kgd, for each k > n.

27. The requirement that a work day duration for a group is at least n periods is encoded by the constraint x_gd => l^n_gd.

Work day duration for teachers is encoded in a similar way.

todo 28. x_tsgnd => x'_tsgndp1 V ... V x'_tsgndp_n - The requirement that a lesson can begin only in period p1, p2, 
. . . , or pn 

todo 29. x'_tsgndp => (... last p .13

30. x_tsgnd => not x_tsg(n+1)(d+1) for each day d except the last - если предметы не должны идти 2 дня подряд

31. x_tsgndpr => x_tsgndp 
         x_tdpr => x_tdp
         x_tsgndp => V_r x_tsgndpr
         x_tdp => V_r x_tdpr
         
32. single{x_tdpr | t in teachers} for each d, p, r. - всего один учитель может находиться в конкретном месте и 
времени.

todo 33. single{x_tdpr | r in rooms} for each d, p, r - всего одна комната может быть занята учителем в данное время. ??? странное условие, пока не делать.

Correctness conditions:
    34. v_d x_tsgnd - Each lesson has to be scheduled. DONE
    20. single({x_tsgnd | d in days}) 
        for each d in days single({x'_tsgndp | p in periods(d)}) 
        - Each lesson is scheduled exactly once in the timetable. DONE
    21. single({x_tsgndp | tsgn in lessons(g)}) for each g, d, p - Each group can attend only one lesson at a time. DONE
    22. x_tsg1ndp <=> x_tsgjndp, 1 < j <= k - Every teacher can teach only one lesson at a time. Still, in some cases it
        is required that several groups (e.g., g1; : : : ; gk) are joined into a cluster of
        groups and that they attend the lesson tsn together, in the same period of
        time. DONE ?

Comfort Requirements:
    23. Forbidden and requested working hours. Forbidden hours and explicit
    working hours for teachers are directly encoded by negation of variables xtdp,
    xtd, and xtp. Forbidden hours for groups are encoded using the variables xgdp.
    These constraints are represented by single literal clauses. DONE ?
    34. Groups and teachers overlapping. The condition that two groups g1
    and g2 are not allowed to attend lessons in the same time. DONE ? (проверить на большом датасете)
    35. Number of teaching days. The condition that a teacher t teaches for exactly
    n days in a week. DONE
    # 36. Work day duration
    37. Idle periods. DONE ?
        
Idle periods constrains, p.13"""

"""begin 37"""


def idle_of_length_k_is_not_allowed(t, k):
    clauses.append([-iktdp(t=t, k=k)])


def teacher_is_not_allowed_to_have_more_than_one_idle_period_per_day(t, d):
    v_i_tdp = []
    for p in range(periods.start, periods.stop - 1):
        v_i_tdp.append(iktdp(t=t, d=d, p=p))
    ss = single(v_i_tdp)
    for clause in ss:
        clauses.append(clause)


def teacher_is_allowed_to_have_at_most_n_idle_periods_per_week(t, n):
    v_i_tdp = []
    for d in days:
        for p in periods:
            v_i_tdp.append(iktdp(t=t, d=d, p=p))
    card = cardinality(v_i_tdp, n)
    for clause in card:
        clauses.append(clause)


"""end 37"""

"""begin 34"""

"""end 34"""
# exit()
"""begin 33"""
for d in days:
    for p in periods:
        for t in teachers.values():
            v_r_x_tdpr = []
            for r_t in rooms.values():
                for r in r_t:
                    v_r_x_tdpr.append(tsgndpr(t=t, d=d, p=p, r=r))
            ss = single(v_r_x_tdpr)
            clauses.extend(ss)
"""end 33"""
"""begin 32"""
for d in days:
    for p in periods:
        for r_t in rooms.values():
            for r in r_t:
                v_t_x_tdpr = []
                for t in teachers.values():
                    v_t_x_tdpr.append(tsgndpr(t=t, d=d, p=p, r=r))
                ss = single(v_t_x_tdpr)
                clauses.extend(ss)

"""end 32"""

"""begin 30"""


def consecutive_days(t, s, g, n):
    """"n - ый раз проводится в неделе (как я понял)"""
    for d in range(days.start, days.stop - 1):
        clauses.append(
            [-tsgndpr(t=t, s=s, g=g, n=n, d=d), -tsgndpr(t=t, s=s, g=g, n=n + 1, d=d + 1)])


"""end 30"""

"""begin 27"""


def group_work_day_minimum(g, d, n):
    clauses.append([-tsgndpr(g=g, d=d), lkgd(k=n, g=g, d=d)])


"""end 27"""

"""begin 26"""


def group_work_day_limited(g, d, n):
    for k in range(n + 1, periods.stop):
        clauses.append([-lkgd(k=k, g=g, d=d)])


"""end 26"""

"""begin 23"""

"""end 23"""

"""begin 25"""


def minimal_group_work_day(g, d, k):
    """idle periods are included
    k!=1"""
    for p in range(periods.start, periods.stop - k + 1):
        clauses.append(
            [-tsgndpr(g=g, d=d, p=p), -tsgndpr(g=g, d=d, p=p + k - 1),
             lkgd(k=k, g=g, d=d)])
    """page 13 second cond how???"""


"""end 25"""
"""!!!!"""
for t, subjs in teacher_lessons.items():
    for sub_type, sub_arr in subjs.items():
        for sgn in sub_arr:
            s = sgn[0]
            for g in sgn[1]:
                for n in range(1, sgn[2] + 1):
                    v_d_x_tsgnd = []
                    for d in days:
                        v_d_x_tsgnd.append(tsgndpr(t=t, s=s, g=g, n=n, d=d))
                        v_p_x_tsgndp = []
                        for p in periods:
                            x_tsgndp = tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p)
                            x_tdp = tsgndpr(t=t, d=d, p=p)
                            x_td = tsgndpr(t=t, d=d)
                            v_p_x_tsgndp.append(x_tsgndp)
                            """begin 1"""
                            clauses.append(
                                [-x_tsgndp, tsgndpr(t=t, s=s, g=g, n=n, d=d)])
                            """end 1"""
                            """begin 3"""
                            clauses.append([-x_tsgndp, x_tdp])
                            """end 3"""
                            """begin 31 pt1"""
                            v_r_x_tsgndpr = []
                            for k_r, r_t in rooms.items():
                                for r in r_t:
                                    x_tsgndpr = tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p, r=r)
                                    if sub_type == k_r:
                                        v_r_x_tsgndpr.append(x_tsgndpr)
                                    clauses.append([-x_tsgndpr, x_tsgndp])
                            clauses.append([-x_tsgndp, *v_r_x_tsgndpr])
                            """end 31 pt1"""
                        """begin 2"""
                        clauses.append([-tsgndpr(t=t, s=s, g=g, n=n, d=d),
                                        *v_p_x_tsgndp])
                        """end 2"""
                        """begin 20 pt1"""
                        ss = single(v_p_x_tsgndp)
                        for clause in ss:
                            clauses.append(clause)
                        """end 20 pt1"""
                    """begin 34"""
                    clauses.append(v_d_x_tsgnd)
                    """end 34"""
                    ss = single(v_d_x_tsgnd)
                    """begin 20 pt2"""
                    for clause in ss:
                        clauses.append(clause)
                    """end 20 pt2"""

for t, subjs in teacher_lessons.items():
    for d in days:
        for p in periods:
            for k_r, r_t in rooms.items():
                for r in r_t:
                    x_tdpr = tsgndpr(t=t, d=d, p=p, r=r)
                    v = []
                    for sub_type, sub_arr in subjs.items():
                        for sgn in sub_arr:
                            s = sgn[0]
                            for g in sgn[1]:
                                for n in range(1, sgn[2] + 1):
                                    x_tsgndpr = tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p, r=r)
                                    v.append(x_tsgndpr)
                                    clauses.append([-x_tsgndpr, x_tdpr])
                    clauses.append([-x_tdpr, *v])

for t, subjs in teacher_lessons.items():
    for sub_arr in subjs.values():
        for sgn in sub_arr:
            s = sgn[0]
            if len(sgn[1]) > 1:
                g_1 = sgn[1][0]
                single_x_tsgndp = []
                for g_j in sgn[1]:
                    for n in range(1, sgn[2] + 1):
                        for d in days:
                            for p in periods:
                                x_tsgndp = tsgndpr(t=t, s=s, g=g_1, n=n, d=d, p=p)
                                if g_1 == g_j:
                                    single_x_tsgndp.append(x_tsgndp)
                                    continue
                                x_tsgjndp = tsgndpr(t=t, s=s, g=g_j, n=n, d=d, p=p)
                                clauses.extend([[-x_tsgndp, x_tsgjndp], [x_tsgndp, -x_tsgjndp]])
                ss = single(single_x_tsgndp)
                for clause in ss:
                    clauses.append(clause)

"""!!!!"""
for t, subjs in teacher_lessons.items():
    for d in days:
        for p in periods:
            v_tsgn_x_tsgndp = []
            for sub_arr in subjs.values():
                for sgn in sub_arr:
                    s = sgn[0]
                    for g in sgn[1]:
                        for n in range(1, sgn[2] + 1):
                            v_tsgn_x_tsgndp.append(tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p))
            """begin 4"""
            clauses.append([-tsgndpr(t=t, d=d, p=p), *v_tsgn_x_tsgndp])
            """end 4"""

"""!!!"""
for g, subjs in group_lessons.items():
    for d in days:
        for p in periods:
            x_gpd = tsgndpr(g=g, d=d, p=p)
            v_tsgn_x_tsgndp = []
            for stn in subjs:
                s = stn[0]
                t = stn[1]
                for n in range(1, stn[2] + 1):
                    v_tsgn_x_tsgndp.append(tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p))
                    """begin 5"""
                    clauses.append([-tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p), x_gpd])
                    """end 5"""
            """begin 6"""
            clauses.append([-x_gpd, *v_tsgn_x_tsgndp])
            """end 6"""

for t in teachers.values():
    for d in days:
        v_p_x_tdp = []
        x_td = tsgndpr(t=t, d=d)
        for p in periods:
            x_tdp = tsgndpr(t=t, d=d, p=p)
            """begin 7"""
            clauses.append([-x_tdp, x_td])
            """end 7"""
            v_p_x_tdp.append(x_tdp)
            v_r_tdpr = []
            """begin 31 pt2"""
            for r_t in rooms.values():
                for r in r_t:
                    x_tdpr = tsgndpr(t=t, d=d, p=p, r=r)
                    v_r_tdpr.append(x_tdpr)
                    clauses.append([-x_tdpr, x_tdp])
            clauses.append([-x_tdp, *v_r_tdpr])
            """end 31 pt2"""
        """begin 8"""
        clauses.append([-x_td, *v_p_x_tdp])
        """end 8"""

for t in teachers.values():
    for p in periods:
        v_d_x_tdp = []
        x_tp = tsgndpr(t=t, p=p)
        for d in days:
            x_tdp = tsgndpr(t=t, d=d, p=p)
            v_d_x_tdp.append(x_tdp)
            """begin 9"""
            clauses.append([-x_tdp, x_tp])
            """end 9"""
        """begin 10"""
        clauses.append([-x_tp, *v_d_x_tdp])
        """end 10"""

for k in range(periods.start, periods.stop - 2):
    for t in teachers.values():
        i_k_t = iktdp(k=k, t=t)
        v_d_i_k_td = []
        for d in days:
            i_k_td = iktdp(k=k, t=t, d=d)
            v_d_i_k_td.append(i_k_td)
            v_p_i_k_tdp = []
            for p in range(periods.start + 1, periods.stop - k):
                i_k_tdp = iktdp(k=k, t=t, d=d, p=p)
                x_tdp_1 = tsgndpr(t=t, d=d, p=p - 1)
                x_tdp_k = tsgndpr(t=t, d=d, p=p + k)
                v_j_x_tdp_j = []
                """begin 11"""
                clauses.append([-i_k_tdp, x_tdp_1])
                for j in range(k):
                    x_tdp_j = tsgndpr(t=t, d=d, p=p + j)
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

for t in teachers.values():
    for d in days:
        for p in range(periods.start + 1, periods.stop - 1):
            i_tdp = iktdp(t=t, d=d, p=p)
            v_k_i_k_tdp = []
            for k in range(periods.start, periods.stop - p):
                i_k_tdp = iktdp(k=k, t=t, d=d, p=p)
                v_k_i_k_tdp.append(i_k_tdp)
                """begin 16"""
                clauses.append([-i_k_tdp, i_tdp])
                """end 16"""
            """begin 17"""
            clauses.append([-i_tdp, *v_k_i_k_tdp])
            """end 17"""

for g, subjs in group_lessons.items():
    for d in days:
        for p in periods:
            v_tsgn_x_tsgndp = []
            for stn in subjs:
                s = stn[0]
                t = stn[1]
                for n in range(1, stn[2] + 1):
                    v_tsgn_x_tsgndp.append(tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p))
            ss = single(v_tsgn_x_tsgndp)
            for clause in ss:
                clauses.append(clause)

cnf = CNF()
# print(clauses)
cnf.from_clauses(clauses)
print(len(clauses))
solver.append_formula(cnf)
print(solver.solve())
model = solver.get_model()
# print(map_tsgndpr)
# print(model)
# print(clauses)
res = []
for i in model:
    if i > 0 and i in map_tsgndpr:
        var = map_tsgndpr[i]
        if (((t := var[0]) in teachers.values()) and ((l := var[1]) in (les := subjects).values()) and (
                (gr := var[2]) in (grps := groups).values())
                # and ((times := var[3]) <= group_lessons[gr])
                and var[-3] != 0 and var[
                    -2] != 0 and var[-1] != 0):
            # print(var, t, les, grps)
            r = []
            for tt in teachers:
                if teachers[tt] == t:
                    r.append(tt)
                    break
            for ll in subjects:
                if subjects[ll] == l:
                    r.append(ll)
                    break
            for grgr in groups:
                if groups[grgr] == gr:
                    r.append(grgr)
                    break
            r.extend([var[-3], var[-2]])
            for rr in original_rooms:
                if original_rooms[rr] == var[-1]:
                    r.append(rr)
                    break
            res.append(r)
res.sort()
for i in res:
    print(*i)
# 24565

# print(solver.get_core())
