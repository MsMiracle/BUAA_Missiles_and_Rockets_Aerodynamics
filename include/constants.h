/*
    include/constants.h
    这里列举出了一些在使用有限差分法求解一维 NS 方程时用到的常数，以及一些题设条件
*/

#ifndef __CONSTANTS_H
#define __CONSTANTS_H

#define i32 int
#define u32 unsigned int
#define i64 long long
#define u64 unsigned long long
#define f32 float
#define f64 double

#define PI 3.14159265358979323846       // 圆周率
#define R 8.31                          // 气体常数 (J/(mol·K))

#define MU_STAR 0.029                   // 气体的平均分子量 (kg/mol)
#define P_INIT 101325.0                 // 初始压力 (Pa)
#define T_INIT 293.15                   // 初始温度 (K)
#define RHO_INIT (P_INIT * MU_STAR / (R * T_INIT)) // 初始密度 (kg/m^3)
#define K (R * T_INIT) / MU_STAR

#define NX 1000                         // X 方向的仿真点数（细网格）
#define DX 5e-3                         // X 方向的空间步长 (m)

#define DT 1e-5                         // 时间步长 (s)
#define HALF_DT2 (DT * DT) / 2          // 二阶时间项系数
#define T_END 60.0                      // 结束时间 (s)

#define TIMER 1e-1                      // 保存时间间隔 (s)
#define PRINT_AFTER_STEPS 1000           // 每隔多少步更新一次终端输出

#endif /* __CONSTANTS_H */