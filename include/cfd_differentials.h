/*
    include/differentials.h
    提供了计算物理量的微分的工具函数
*/
#ifndef __CFD_DIFFERENTIALS_H
#define __CFD_DIFFERENTIALS_H


#include "constants.h"
f64     prho_pt     (i32 idx);
f64     pprho_ppt   (i32 idx, f64 time);

f64     pvx_pt      (i32 idx, f64 time);
f64     ppvx_ppt    (i32 idx, f64 time);

f64     prho_px     (i32 idx);
f64     pprho_ppx   (i32 idx);

f64     pvx_px      (i32 idx);
f64     ppvx_ppx    (i32 idx);

#endif /*__CFD_DIFFERENTIALS_H*/