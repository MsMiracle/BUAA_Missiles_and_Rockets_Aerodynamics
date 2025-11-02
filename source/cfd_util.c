#include "cfd_util.h"
#include "cfd_differentials.h"
#include "constants.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* 全局数组定义（在头文件中用 extern 声明） */
f64 vel[NX];
f64 pres[NX];
f64 rho[NX];

f64 getPistonAcceleration(f64 time){
    if (time < 10){
        return 3.0;
    }
    else if (time < 30){
        return 0.0;
    }
    else if (time < 40){
        return 1.0;
    }
    else {
        return 0.0;
    }
}

void initFlowField(){
    for (int i = 0; i < NX; i ++){
        vel     [i] = 0;
        pres    [i] = P_INIT;
        rho     [i] = RHO_INIT;
    }
    printf("[INFO] FlowField Initialized.\n");
}

f64 rborderRho(){
    int i = NX - 1;
    return (-rho[i] * (vel[i] - vel[i - 1]) / DX - vel[i] * (rho[i] - rho[i - 1]) / DX) * DT + rho[i];
}

f64 rborderVel(f64 time){
    int i = NX - 1;
    f64 fx = -rho[i] * getPistonAcceleration(time);
    return (
        ((fx - ((pres[i] - pres[i - 1]) / DX)) / rho[i]
        - vel[i] * (vel[i] - vel[i - 1]) / DX) * DT + vel[i]
    );
}
f64 * updateRho(f64 time){
    f64 *new_rho = (f64 *)malloc(sizeof(f64) * NX);
    if (!new_rho){
        printf("[ERROR] Memory allocation failed during rho update at %.8f sec", time);
        exit(-1);
    }
    for (int i = 1; i < NX - 1; i ++){
        f64 _prho_pt = prho_pt(i);
        f64 _pprho_ppt = pprho_ppt(i, time);
        new_rho[i] = rho[i] + DT * _prho_pt + HALF_DT2 * _pprho_ppt;
    }
    new_rho[NX - 1] = rborderRho();
    /* 左边界：用连续性方程更新，避免与内部离散不一致 */
    new_rho[0] = rho[0] - rho[0] * DT * ( (vel[1] - vel[0]) / DX );
    return new_rho;
}

f64 * updateVelocity(f64 time){
    f64 *new_vel = (f64 *)malloc(sizeof(f64) * NX);
    if (!new_vel){
        printf("[ERROR] Memory allocation failed during vel update at %.8f sec", time);
        exit(-1);
    }
    for (int i = 1; i < NX - 1; i ++){
        new_vel[i] = vel[i] + DT * pvx_pt(i, time) + HALF_DT2 * ppvx_ppt(i, time);
    }
    new_vel[NX - 1] = rborderVel(time);
    new_vel[0] = 0.0;
    return new_vel;
}

f64 * updatePressure(f64 time){
    f64 *new_pres = (f64 *)malloc(sizeof(f64) * NX);
    if (!new_pres){
        printf("[ERROR] Memory allocation failed during pres update at %.8f sec", time);
        exit(-1);
    }
    for (int i = 0; i < NX; i ++){
        new_pres[i] = R / MU_STAR * rho[i] * T_INIT;
    }
    return new_pres;
}