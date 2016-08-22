# This is sample cython code. We may remove this in the future when we
# have real cython code, but for now use this sample to get the unit tests,
# build, etc. straightened out.

def fib2(int n):
    cdef int i
    cdef double a=0.0, b=1.0
    for i in range(n + 1):
        a,b=a+b,a
    return a
