from itertools import product

from implied_variables import tsgndpr, iktdp, lkgd
from utils import *

period_length = 2
days = range(1, 7)
periods = range(1, 8)
lesson_duration = 1


class Teacher:
    @classmethod
    def number_of_teaching_days(cls, t, n):
        c = [tsgndpr(t=t, d=d) for d in days]
        cl = cardinality(c, n)
        # cl.extend(cardinality([-i for i in c], len(days) - n))
        return cl

    @classmethod
    def forbidden_period_for_teacher(cls, t, d, p):
        # return [[-tsgndpr(t=t, d=d, p=p)], [-tsgndpr(t=t, d=d)], [-tsgndpr(t=t, p=p)]]
        # TODO heuristic check, !
        if t in exact_teachers and (d, p) in exact_teachers[t]:
            return [[]]
        return [[-tsgndpr(t=t, d=d, p=p)]]

    @classmethod
    def forbidden_day_for_teacher(cls, t, d):
        return [[-tsgndpr(t=t, d=d)]]

    @classmethod
    def idle_of_length_k_is_not_allowed(cls, t, k):
        return [-iktdp(t=t, k=k)]

    @classmethod
    def teachers_overlapping(cls, t_1, t_2):
        return group_teacher_overlapping(t_1=t_1, t_2=t_2)

    @classmethod
    def teacher_is_allowed_to_have_at_most_n_idle_periods_per_week(cls, t, n):
        v_i_tdp = []
        res = []
        for d, p in product(days, periods):
            # if t in exact_teachers and (d, p) in exact_teachers[t]:
            #     continue
            v_i_tdp.append(iktdp(t=t, d=d, p=p))
        for clause in cardinality(v_i_tdp, n):
            res.append(clause)
        return res

    @classmethod
    def teacher_is_not_allowed_to_have_more_than_one_idle_period_per_day(cls, t, d):
        res = []
        v_i_tdp = []
        for p in range(periods.start, periods.stop - 1):
            # TODO heuristic check
            if t in exact_teachers and (d, p) in exact_teachers[t]:
                continue
            v_i_tdp.append(iktdp(t=t, d=d, p=p))
        for clause in single(v_i_tdp):
            res.append(clause)
        return res


class Group:

    @classmethod
    def group_work_day_minimum(cls, g, d, n):
        return [-tsgndpr(g=g, d=d), lkgd(k=n, g=g, d=d)]

    @classmethod
    def group_work_day_limited(cls, g, d, n):
        res = []
        for k in range(n + 1, periods.stop):
            # TODO heuristic check
            if g in exact_groups and (d, k) in exact_groups[k]:
                continue
            res.append([-lkgd(k=k, g=g, d=d)])
        return res

    @classmethod
    def forbidden_period_for_group(cls, g, d, p):
        if g in exact_groups and (d, p) in exact_groups[g]:
            return [[]]
        return [[-tsgndpr(g=g, d=d, p=p)]]

    @classmethod
    def forbidden_day_for_group(cls, g, d):
        res = []
        for p in periods:
            # TODO heuristic check
            if g in exact_groups and (d, p) in exact_groups[g]:
                continue
            res.append([-tsgndpr(g=g, d=d, p=p)])
        return res

    @classmethod
    def groups_overlapping(cls, g_1, g_2):
        return group_teacher_overlapping(g_1=g_1, g_2=g_2)


# def minimal_group_work_day(g, d, k):
#     """idle periods are included
#     k!=1"""
#     for p in range(periods.start, periods.stop - k + 1):
#         clauses.append(
#             [-tsgndpr(g=g, d=d, p=p), -tsgndpr(g=g, d=d, p=p + k - 1),
#              lkgd(k=k, g=g, d=d)])
#     """page 13 second cond how???"""

class Lesson:
    @classmethod
    def consecutive_days(cls, t, s, g, n):
        res = []
        for d in range(days.start, days.stop - 1):
            res.append(
                [-tsgndpr(t=t, s=s, g=g, n=n, d=d),
                 -tsgndpr(t=t, s=s, g=g, n=n + 1, d=d + 1)])
        return res

    s = set()

    @classmethod
    def exact_time_for_lesson(cls, t, s, g, d, p, r):
        # TODO can it be optimized?
        i = 1
        while (t, s, g, i) in cls.s:
            i += 1
        cls.s.add((t, s, g, i))
        # if t in exact_teachers and (d, p) in exact_teachers[t] or \
        #     g in exact_groups and (d, p) in exact_groups[g] or \
        #     r in exact_rooms
        res = [[tsgndpr(t=t, s=s, g=g, n=i, d=d, p=p, r=r)], [tsgndpr(t=t, s=s, g=g, d=d, p=p)]]
        # print(Reader.original_rooms)
        # for i_d, i_p, i_r in product(days, periods, Reader.original_rooms.values()):
        #     if i_d != d and i_p != p and i_r != r:
        #         res.append([-tsgndpr(t=t, s=s, g=g, n=i, d=i_d, p=i_p, r=i_r)])
        # print(len(res))
        # print(res)
        return res


def group_teacher_overlapping(g_1=0, g_2=0, t_1=0, t_2=0):
    cl = []
    for d, p in product(days, periods):
        if (t_1 in exact_teachers and (d, p) in exact_teachers[t_1] or
                g_1 in exact_groups and (d, p) in exact_groups[g_1] or
                t_2 in exact_teachers and (d, p) in exact_teachers[t_2] or
                g_2 in exact_groups and (d, p) in exact_groups[g_2]):
            continue
        x_t1g1dp = tsgndpr(t=t_1, g=g_1, d=d, p=p)
        x_t2g2dp = tsgndpr(t=t_2, g=g_2, d=d, p=p)
        cl.extend([[-x_t1g1dp, -x_t2g2dp], [-x_t2g2dp, -x_t1g1dp]])
    return cl


def checker(mus, assumptions):
    from utils import Reader
    clauses = Reader.clauses
    for clause in clauses:
        for i in clause:
            if abs(i) in mus:
                for j in clause:
                    if abs(j) in assumptions:
                        print(clause)
                        break
                break
