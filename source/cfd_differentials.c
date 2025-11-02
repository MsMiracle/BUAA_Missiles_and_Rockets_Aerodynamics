/*
    include/cfd_differentials
    提供了差分方法计算偏微分的函数
*/
#include "cfd_util.h"
#include "cfd_differentials.h"
#include "constants.h"
#include <math.h>

f64 prho_px(i32 idx){
    if (idx == 0){
        /* 左边界：一阶前向差分 */
        return (rho[1] - rho[0]) / DX;
    } else if (idx == NX - 1){
        /* 右边界：一阶后向差分 */
        return (rho[NX - 1] - rho[NX - 2]) / DX;
    } else {
        /* 内部：二阶中心差分 */
        return (rho[idx + 1] - rho[idx - 1]) / (2 * DX);
    }
}

f64 pvx_px(i32 idx){
    if (idx == 0){
        /* 左边界：一阶前向差分 */
        return (vel[1] - vel[0]) / DX;
    } else if (idx == NX - 1){
        /* 右边界：一阶后向差分 */
        return (vel[NX - 1] - vel[NX - 2]) / DX;
    } else {
        /* 内部：二阶中心差分 */
        return (vel[idx + 1] - vel[idx - 1]) / (2 * DX);
    }
}

f64 prho_pt(i32 idx){
    return (
        -vel[idx] * prho_px(idx) - rho[idx] * pvx_px(idx)
    );
}

f64 pprho_ppx(i32 idx){
    if (idx == 0){
        /* 左边界：二阶单边差分 (forward) */
        return (2*rho[0] - 5*rho[1] + 4*rho[2] - rho[3]) / (DX * DX);
    } else if (idx == NX - 1){
        /* 右边界：二阶单边差分 (backward) */
        return (2*rho[NX-1] - 5*rho[NX-2] + 4*rho[NX-3] - rho[NX-4]) / (DX * DX);
    } else {
        /* 内部：二阶中心差分 */
        return (rho[idx + 1] - 2 * rho[idx] + rho[idx - 1]) / (DX * DX);
    }
}

f64 ppvx_ppx(i32 idx){
    if (idx == 0){
        /* 左边界：二阶单边差分 (forward) */
        return (2*vel[0] - 5*vel[1] + 4*vel[2] - vel[3]) / (DX * DX);
    } else if (idx == NX - 1){
        /* 右边界：二阶单边差分 (backward) */
        return (2*vel[NX-1] - 5*vel[NX-2] + 4*vel[NX-3] - vel[NX-4]) / (DX * DX);
    } else {
        /* 内部：二阶中心差分 */
        return (vel[idx + 1] - 2 * vel[idx] + vel[idx - 1]) / (DX * DX);
    }
}

f64 ppvx_ppt(i32 idx, f64 time){
    return (
        -(-vel[idx] * pvx_px(idx) - K / rho[idx] * prho_px(idx) - getPistonAcceleration(time)) * pvx_px(idx)
        -vel[idx] * (-pow(pvx_px(idx), 2) - vel[idx] * ppvx_ppx(idx) + K * pow(prho_px(idx) / rho[idx], 2) - K / rho[idx] * pprho_ppx(idx))
        + K / pow(rho[idx], 2) * (-vel[idx] * prho_px(idx) - rho[idx] * pvx_px(idx)) * prho_px(idx)
        - K / rho[idx] * (-pvx_px(idx) * prho_px(idx) - vel[idx] * pprho_ppx(idx) - prho_px(idx) * pvx_px(idx) - rho[idx] * ppvx_ppx(idx))
    );
}

f64 pprho_ppt(i32 idx, f64 time){
    f64 _pvx_px = pvx_px(idx);
    f64 _prho_px = prho_px(idx);
    f64 _getPistonAcc = getPistonAcceleration(time);
    f64 _vel = vel[idx];
    f64 _rho = rho[idx];
    f64 _pprho_ppx = pprho_ppx(idx);
    f64 _ppvx_ppx = ppvx_ppx(idx);
    
    f64 _term1 = -(-vel[idx] * pvx_px(idx) - K / rho[idx] * prho_px(idx) - getPistonAcceleration(time)) * prho_px(idx);
    f64 _term2 = -vel[idx] * (-pvx_px(idx) * prho_px(idx) - vel[idx] * pprho_ppx(idx) - prho_px(idx) * pvx_px(idx) - rho[idx] * ppvx_ppx(idx));
    f64 _term3 = -(-vel[idx] * prho_px(idx) - rho[idx] * pvx_px(idx)) * pvx_px(idx);
    f64 _term4 = -rho[idx] * (-pow(pvx_px(idx), 2) - vel[idx] * ppvx_ppx(idx) + K * pow(prho_px(idx) / rho[idx], 2) - K / rho[idx] * pprho_ppx(idx));
    return (
        _term1
        + _term2
        + _term3
        + _term4
    );
}

f64 pvx_pt(i32 idx, f64 time){
    return -vel[idx] * pvx_px(idx) - K / rho[idx] * prho_px(idx) - getPistonAcceleration(time);
}