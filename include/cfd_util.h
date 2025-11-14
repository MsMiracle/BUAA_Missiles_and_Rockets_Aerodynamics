/*
    include/cfd_util.h
    这里定义了解决一维流场问题时使用的一些工具函数
*/
#ifndef CFD_UTIL_H
#define CFD_UTIL_H

#include "constants.h"

extern f64 vel[NX];    // 速度数组
extern f64 pres[NX];   // 压力数组
extern f64 rho[NX];    // 密度数组

extern f64 fourierSeries[50][2];

f64     getPistonAcceleration(f64 time);

void    initFlowField();

f64 *   updateVelocity  (f64 time);
f64 *   updatePressure  (f64 time);
f64 *   updateRho       (f64 time);

f64     rborderRho      ();
f64     rborderVel      (f64 time);
#endif /* CFD_UTIL_H */