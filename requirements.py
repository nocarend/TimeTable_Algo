from itertools import product

from constraints import days, periods
from implied_variables import tsgndpr, iktdp
from utils import single


class Correctness:
    def __init__(self, teachers, original_rooms, rooms, teacher_lessons):
        self.teachers = teachers
        self.original_rooms = original_rooms
        self.teacher_lessons = teacher_lessons
        self.rooms = rooms

    def _room_weak(self):
        def _room_teacher(arg_1, arg_2, _type=False):
            res = []
            for d, p, a_1 in product(days, periods, arg_1.values()):
                v_x_tdpr = []
                for a_2 in arg_2.values():
                    v_x_tdpr.append(tsgndpr(t=a_1 if not _type else a_2, d=d, p=p, r=a_2 if not _type else a_1))
                res.extend(single(v_x_tdpr))
            return res

        """32,33"""
        return _room_teacher(self.teachers, self.original_rooms) + _room_teacher(self.original_rooms, self.teachers,
                                                                                 True)

    def _room_strong(self):
        res = []
        for (t, subjs), d, p, (k_r, r_t) in product(self.teacher_lessons.items(), days, periods,
                                                    self.rooms.items()):
            if k_r != 'lec':  # сильно замедляет, but...
                ss = []
                for r, (sub_type, sub_arr) in product(r_t, subjs.items()):
                    if sub_type != k_r:
                        continue  # hz
                    for sgn in sub_arr:
                        for n, g in product(range(1, sgn[2] + 1), sgn[1]):
                            ss.append(tsgndpr(t=t, s=sgn[0], g=g, n=n, d=d, p=p, r=r))
                res.extend(single(ss))
                continue
            for r in r_t:
                x_tdpr = tsgndpr(t=t, d=d, p=p, r=r)
                for sub_type, sub_arr in subjs.items():
                    for sgn in sub_arr:
                        for n, g in product(range(1, sgn[2] + 1), sgn[1]):
                            res.append([-tsgndpr(t=t, s=sgn[0], g=g, n=n, d=d, p=p, r=r), x_tdpr])
        return res

    def room_all(self):
        return self._room_strong() + self._room_weak()


class Mixed:
    def __init__(self, teachers, teacher_lessons, group_lessons, original_rooms, rooms):
        self.teachers = teachers
        self.original_rooms = original_rooms
        self.group_lessons = group_lessons
        self.rooms = rooms
        self.teacher_lessons = teacher_lessons

    def mixed_all(self):
        return (self._mixed_first() + self._mixed_second() + self._mixed_third() + self._mixed_fourth()
                + self._mixed_fifth() + self._mixed_sixth() + self._mixed_seventh() + self._mixed_eighth()
                + self._mixed_ninth())

    def _mixed_first(self):
        res = []
        for t, subjs in self.teacher_lessons.items():
            for sub_type, sub_arr in subjs.items():
                for sgn in sub_arr:
                    s = sgn[0]
                    for g, n in product(sgn[1], range(1, sgn[2] + 1)):
                        v_d_x_tsgnd = []
                        for d in days:
                            x_tsgnd = tsgndpr(t=t, s=s, g=g, n=n, d=d)
                            v_d_x_tsgnd.append(x_tsgnd)
                            v_p_x_tsgndp = []
                            for p in periods:
                                x_tsgndp = tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p)
                                x_tdp = tsgndpr(t=t, d=d, p=p)
                                v_p_x_tsgndp.append(x_tsgndp)
                                """begin 31 pt1"""
                                v_r_x_tsgndpr = []
                                for k_r, r_t in self.rooms.items():
                                    for r in r_t:
                                        x_tsgndpr = tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p, r=r)
                                        if sub_type == k_r:
                                            v_r_x_tsgndpr.append(x_tsgndpr)
                                        res.append([-x_tsgndpr, x_tsgndp])
                                res.extend([[-x_tsgndp, x_tsgnd], [-x_tsgndp, *v_r_x_tsgndpr], [-x_tsgndp, x_tdp]])
                                """end 31 pt1"""
                            """begin 20 pt1"""
                            res.extend(single(v_p_x_tsgndp) + [[-x_tsgnd, *v_p_x_tsgndp]])
                            """end 20 pt1"""
                        """begin 34"""
                        """end 34"""
                        """begin 20 pt2"""
                        res.extend(single(v_d_x_tsgnd) + [v_d_x_tsgnd])
                        """end 20 pt2"""
        return res

    def _mixed_second(self):
        res = []
        for t, subjs in self.teacher_lessons.items():
            for sub_type, sub_arr in subjs.items():
                if sub_type != 'lec':
                    continue
                for sgn in sub_arr:
                    s = sgn[0]
                    if len(sgn[1]) < 1:
                        continue
                    g_1 = sgn[1][0]
                    for n in range(1, sgn[2] + 1):
                        single_x_tsgndp = []
                        for g_j, d, p in product(sgn[1], days, periods):
                            x_tsgndp = tsgndpr(t=t, s=s, g=g_1, n=n, d=d, p=p)
                            if g_1 == g_j:
                                single_x_tsgndp.append(x_tsgndp)
                                continue
                            x_tsgjndp = tsgndpr(t=t, s=s, g=g_j, n=n, d=d, p=p)
                            res.extend([[-x_tsgndp, x_tsgjndp], [x_tsgndp, -x_tsgjndp]])
                        res.extend(single(single_x_tsgndp))
        return res

    def _mixed_third(self):
        res = []
        for (t, subjs), d, p in product(self.teacher_lessons.items(), days, periods):
            v_tsgn_x_tsgndp = []
            for sub_arr in subjs.values():
                for sgn in sub_arr:
                    s = sgn[0]
                    for g, n in product(sgn[1], range(1, sgn[2] + 1)):
                        v_tsgn_x_tsgndp.append(tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p))
            """begin 4"""
            res.append([-tsgndpr(t=t, d=d, p=p), *v_tsgn_x_tsgndp])
            """end 4"""
        return res

    def _mixed_fourth(self):
        res = []
        for (g, subjs), d, p in product(self.group_lessons.items(), days, periods):
            x_gpd = tsgndpr(g=g, d=d, p=p)
            v_tsgn_x_tsgndp = []
            for stn in subjs:
                s = stn[0]
                t = stn[1]
                for n in range(1, stn[2] + 1):
                    x_tsgndp = tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p)
                    v_tsgn_x_tsgndp.append(x_tsgndp)
                    """begin 5"""
                    res.append([-x_tsgndp, x_gpd])
                    """end 5"""
            """begin 6"""
            res.append([-x_gpd, *v_tsgn_x_tsgndp])
            """end 6"""
        return res

    def _mixed_fifth(self):
        res = []
        for t, d in product(self.teachers.values(), days):
            v_p_x_tdp = []
            x_td = tsgndpr(t=t, d=d)
            for p in periods:
                x_tdp = tsgndpr(t=t, d=d, p=p)
                v_p_x_tdp.append(x_tdp)
                v_r_tdpr = []
                """begin 31 pt2"""
                for r in self.original_rooms.values():
                    x_tdpr = tsgndpr(t=t, d=d, p=p, r=r)
                    v_r_tdpr.append(x_tdpr)
                    res.append([-x_tdpr, x_tdp])
                res.extend([[-x_tdp, x_td], [-x_tdp, *v_r_tdpr]])
                """end 31 pt2"""
            """begin 8"""
            res.append([-x_td, *v_p_x_tdp])
            """end 8"""
        return res

    def _mixed_sixth(self):
        res = []
        for t, p in product(self.teachers.values(), periods):
            v_d_x_tdp = []
            x_tp = tsgndpr(t=t, p=p)
            for d in days:
                x_tdp = tsgndpr(t=t, d=d, p=p)
                v_d_x_tdp.append(x_tdp)
                """begin 9"""
                res.append([-x_tdp, x_tp])
                """end 9"""
            """begin 10"""
            res.append([-x_tp, *v_d_x_tdp])
            """end 10"""
        return res

    def _mixed_seventh(self):
        res = []
        for k, t in product(range(periods.start, periods.stop - 2), self.teachers.values()):
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
                    for j in range(k):
                        x_tdp_j = tsgndpr(t=t, d=d, p=p + j)
                        res.append([-i_k_tdp, -x_tdp_j])
                        v_j_x_tdp_j.append(x_tdp_j)
                    """end 11"""
                    """begin 12"""
                    res.extend(
                        [[-i_k_tdp, i_k_td], [-x_tdp_1, *v_j_x_tdp_j, -x_tdp_k, -i_k_tdp], [-i_k_tdp, x_tdp_k],
                         [-i_k_tdp, x_tdp_1]])
                    """end 12"""
                    v_p_i_k_tdp.append(i_k_tdp)
                """begin 13"""
                """end 13"""
                """begin 14"""
                res.extend([[-i_k_td, i_k_t], [-i_k_td, *v_p_i_k_tdp]])
                """end 14"""
            """begin 15"""
            res.append([-i_k_t, *v_d_i_k_td])
            """end 15"""
        return res

    def _mixed_eighth(self):
        res = []
        for t, d, p in product(self.teachers.values(), days, range(periods.start + 1, periods.stop - 1)):
            i_tdp = iktdp(t=t, d=d, p=p)
            v_k_i_k_tdp = []
            for k in range(periods.start, periods.stop - p):
                i_k_tdp = iktdp(k=k, t=t, d=d, p=p)
                v_k_i_k_tdp.append(i_k_tdp)
                """begin 16"""
                res.append([-i_k_tdp, i_tdp])
                """end 16"""
            """begin 17"""
            res.append([-i_tdp, *v_k_i_k_tdp])
            """end 17"""
        return res

    def _mixed_ninth(self):
        res = []
        for (g, subjs), d, p in product(self.group_lessons.items(), days, periods):
            v_tsgn_x_tsgndp = []
            for stn in subjs:
                s = stn[0]
                t = stn[1]
                for n in range(1, stn[2] + 1):
                    v_tsgn_x_tsgndp.append(tsgndpr(t=t, s=s, g=g, n=n, d=d, p=p))
            res.extend(single(v_tsgn_x_tsgndp))
        return res
