from itertools import product

from implied_variables import tsgndpr, iktdp, lkgd
from utils import cardinality, single

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
            v_i_tdp.append(iktdp(t=t, d=d, p=p))
        for clause in cardinality(v_i_tdp, n):
            res.append(clause)
        return res

    @classmethod
    def teacher_is_not_allowed_to_have_more_than_one_idle_period_per_day(cls, t, d):
        res = []
        v_i_tdp = []
        for p in range(periods.start, periods.stop - 1):
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
            res.append([-lkgd(k=k, g=g, d=d)])
        return res

    @classmethod
    def forbidden_period_for_group(cls, g, d, p):
        return [[-tsgndpr(g=g, d=d, p=p)]]

    @classmethod
    def forbidden_day_for_group(cls, g, d):
        return [[-tsgndpr(g=g, d=d, p=p)] for p in periods]  # because ef students are always available lol

    @classmethod
    def groups_overlapping(cls, g_1, g_2, status='add'):
        return group_teacher_overlapping(g_1=g_1, g_2=g_2, status=status)


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


def group_teacher_overlapping(g_1=0, g_2=0, t_1=0, t_2=0, status='add'):
    cl = []
    for d, p in product(days, periods):
        x_t1g1dp = tsgndpr(t=t_1, g=g_1, d=d, p=p)
        x_t2g2dp = tsgndpr(t=t_2, g=g_2, d=d, p=p)
        cl.extend([[-x_t1g1dp, -x_t2g2dp], [-x_t2g2dp, -x_t1g1dp]])
    return cl


def checker(mus):
    from utils import Reader
    from ast import literal_eval
    clauses = Reader.clauses
    for clause in clauses.keys():
        flag = False
        print(clause)
        for i in literal_eval(clause):
            for j in i:
                if abs(j) in mus:
                    print(clause)
                    flag = True
                    break
            if flag:
                break
