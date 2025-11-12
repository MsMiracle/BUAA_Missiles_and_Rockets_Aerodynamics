#include "cfd_util.h"
#include "cfd_differentials.h"
#include "constants.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#ifdef _OPENMP
#include <omp.h>
#endif

/* 全局数组定义（在头文件中用 extern 声明） */
f64 vel[NX];
f64 pres[NX];
f64 rho[NX];
/* Fourier series coefficients for piston acceleration: rows are (a_n, b_n) */
f64 fourierSeries[50][2] = {
    {0.5513288954, 0.3183098862},
    {0.5513288954, 0.9549296586},
    {-0.0000000000, 0.4244131816},
    {-0.2756644477, 0.4774648293},
    {-0.1102657791, 0.0636619772},
    {-0.0000000000, 0.0000000000},
    {0.0787612708, 0.0454728409},
    {0.1378322239, 0.2387324146},
    {-0.0000000000, 0.1414710605},
    {-0.1102657791, 0.1909859317},
    {-0.0501208087, 0.0289372624},
    {-0.0000000000, 0.0000000000},
    {0.0424099150, 0.0244853759},
    {0.0787612708, 0.1364185227},
    {-0.0000000000, 0.0848826363},
    {-0.0689161119, 0.1193662073},
    {-0.0324311115, 0.0187241110},
    {-0.0000000000, 0.0000000000},
    {0.0290173103, 0.0167531519},
    {0.0551328895, 0.0954929659},
    {0.0000000000, 0.0606304545},
    {-0.0501208087, 0.0868117871},
    {-0.0239708215, 0.0138395603},
    {-0.0000000000, 0.0000000000},
    {0.0220531558, 0.0127323954},
    {0.0424099150, 0.0734561276},
    {-0.0000000000, 0.0471570202},
    {-0.0393806354, 0.0682092613},
    {-0.0190113412, 0.0109762030},
    {-0.0000000000, 0.0000000000},
    {0.0177848031, 0.0102680608},
    {0.0344580560, 0.0596831037},
    {-0.0000000000, 0.0385830165},
    {-0.0324311115, 0.0561723329},
    {-0.0157522542, 0.0090945682},
    {-0.0000000000, 0.0000000000},
    {0.0149007810, 0.0086029699},
    {0.0290173103, 0.0502594557},
    {-0.0000000000, 0.0326471678},
    {-0.0275664448, 0.0477464829},
    {-0.0134470462, 0.0077636558},
    {-0.0000000000, 0.0000000000},
    {0.0128216022, 0.0074025555},
    {0.0250604043, 0.0434058936},
    {-0.0000000000, 0.0282942121},
    {-0.0239708215, 0.0415186808},
    {-0.0117304020, 0.0067725508},
    {-0.0000000000, 0.0000000000},
    {0.0112516101, 0.0064961201},
    {0.0220531558, 0.0381971863},
};
/* DC term a0/2 for the piecewise acceleration (period T=60s):
   integral over a(t) is 3*10 + 0*20 + 1*10 + 0*20 = 40
   a0 = (2/T)*Integral = (2/60)*40 = 4/3, hence a0/2 = 2/3
*/
static const f64 PISTON_FOURIER_A0_HALF = 2.0/3.0;  /* ~0.6666666667 */
static const f64 PISTON_PERIOD = 60.0;

f64 getPistonAcceleration(f64 time)
{
    /* Reduce time to [0, T) for periodic extension */
    f64 t = fmod(time, PISTON_PERIOD);
    if (t < 0) t += PISTON_PERIOD;

    f64 acc = PISTON_FOURIER_A0_HALF;
    /* Sum over provided harmonics */
    for (int k = 0; k < 50; ++k)
    {
        int n = k + 1; /* harmonic index */
        f64 an = fourierSeries[k][0];
        f64 bn = fourierSeries[k][1];
        f64 w = 2.0 * PI * n / PISTON_PERIOD;
        acc += an * cos(w * t) + bn * sin(w * t);
    }
    return acc;
}

void initFlowField()
{
    for (int i = 0; i < NX; i++)
    {
        vel[i] = 0;
        pres[i] = P_INIT;
        rho[i] = RHO_INIT;
    }
    printf("[INFO] FlowField Initialized.\n");
}

f64 rborderRho()
{
    int i = NX - 1;
    return (-rho[i] * (vel[i] - vel[i - 1]) / DX - vel[i] * (rho[i] - rho[i - 1]) / DX) * DT + rho[i];
}

f64 rborderVel(f64 time)
{
    int i = NX - 1;
    f64 fx = -rho[i] * getPistonAcceleration(time);
    return (
        ((fx - ((pres[i] - pres[i - 1]) / DX)) / rho[i] - vel[i] * (vel[i] - vel[i - 1]) / DX) * DT + vel[i]);
}
f64 *updateRho(f64 time)
{
    f64 *new_rho = (f64 *)malloc(sizeof(f64) * NX);
    if (!new_rho)
    {
        printf("[ERROR] Memory allocation failed during rho update at %.8f sec", time);
        exit(-1);
    }
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int i = 1; i < NX - 1; i++)
    {
        f64 _prho_pt = prho_pt(i);
        f64 _pprho_ppt = pprho_ppt(i, time);
        new_rho[i] = rho[i] + DT * _prho_pt + HALF_DT2 * _pprho_ppt;
    }
    new_rho[NX - 1] = rborderRho();
    /* 左边界：用连续性方程更新，避免与内部离散不一致 */
    new_rho[0] = rho[0] - rho[0] * DT * ((vel[1] - vel[0]) / DX);
    return new_rho;
}

f64 *updateVelocity(f64 time)
{
    f64 *new_vel = (f64 *)malloc(sizeof(f64) * NX);
    if (!new_vel)
    {
        printf("[ERROR] Memory allocation failed during vel update at %.8f sec", time);
        exit(-1);
    }
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int i = 1; i < NX - 1; i++)
    {
        new_vel[i] = vel[i] + DT * pvx_pt(i, time) + HALF_DT2 * ppvx_ppt(i, time);
    }
    new_vel[NX - 1] = rborderVel(time);
    new_vel[0] = 0.0;
    return new_vel;
}

f64 *updatePressure(f64 time)
{
    f64 *new_pres = (f64 *)malloc(sizeof(f64) * NX);
    if (!new_pres)
    {
        printf("[ERROR] Memory allocation failed during pres update at %.8f sec", time);
        exit(-1);
    }
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int i = 0; i < NX; i++)
    {
        new_pres[i] = R / MU_STAR * rho[i] * T_INIT;
    }
    return new_pres;
}