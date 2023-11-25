# TimeTable_Algo

Best (not finished yet) solution using SAT solver

## Supported constrains

### Forbidden and requested working hours.

### Groups and teachers overlapping.

The condition that two groups ``g1`` and ``g2`` (or teachers ``t1`` and ``t2``) are not allowed to attend lessons in the
same time.

### Number of teaching days.

The condition that a teacher ``t`` teaches for exactly ``n`` days in a week.

### Idle periods.

1. The requirement that idle periods of length ``k`` are not allowed for the teacher ``t``.
2. The requirement that a teacher t is not allowed to have more than one idle
period per day.
3. The requirement that a teacher t is allowed to have at most n idle periods per
week.