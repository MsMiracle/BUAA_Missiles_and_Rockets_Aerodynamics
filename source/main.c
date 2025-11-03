/*
    source/main.c
    流场仿真主程序
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

#include "cfd_util.h"
#include "cfd_differentials.h"
#include "constants.h"

#ifdef _OPENMP
#include <omp.h>
#endif

#ifdef _WIN32
#define CLEAR "cls"
#else
#define CLEAR "clear"
#endif

i32 main(i32 argc, char **argv){
#ifdef _OPENMP
    printf("[INFO] OpenMP is enabled, running with %d threads.\n", omp_get_max_threads());
#else
    printf("[INFO] OpenMP is not enabled, running in single-thread mode.\n");
#endif
    sleep(1);
    initFlowField();

    f64 t = 0.0;
    i32 step = 0;
    i32 maxSteps = (i32)(T_END / DT) + 1;
    f64 total_timer = 0.0;

    clock_t start_clock = clock();

    for (step = 0; step < maxSteps; step++){
        f64 *new_vel = updateVelocity(t);
        f64 *new_rho = updateRho(t);
        f64 *new_pres = updatePressure(t);
        
        memcpy(vel, new_vel, sizeof(f64) * NX);
        memcpy(rho, new_rho, sizeof(f64) * NX);
        memcpy(pres, new_pres, sizeof(f64) * NX);

        free(new_rho);
        free(new_pres);
        free(new_vel);

        if (step % PRINT_AFTER_STEPS == 0 || step == maxSteps - 1) {
            system(CLEAR);


            // ETA Calculation
            char eta_str[32] = "ETA: --:--:--";
            if (step > 10) { // Start calculating after a few steps for stability
                clock_t current_clock = clock();
                double elapsed_secs = (double)(current_clock - start_clock) / CLOCKS_PER_SEC;
                double steps_per_sec = (double)step / elapsed_secs;
                double remaining_secs = (double)(maxSteps - step) / steps_per_sec;

                int hours = (int)(remaining_secs / 3600);
                int minutes = (int)((remaining_secs - (hours * 3600)) / 60);
                int seconds = (int)remaining_secs % 60;
                sprintf(eta_str, "ETA: %02d:%02d:%02d", hours, minutes, seconds);
            }

            printf("t=%.8f step=%d/%d (%.2f%%) %s | rho[0]=%.8f vel[0]=%.8f pres[0]=%.8f\n",
                   t, step, maxSteps, (double)step / maxSteps * 100.0, eta_str,
                   rho[0], vel[0], pres[0]);
            fflush(stdout);
        }

        t += DT;
        if (t > total_timer){
            total_timer += TIMER;
            char filename[64];
            sprintf(filename, "build/snapshot_%.6e.csv", t);
            FILE *out = fopen(filename, "w");
            if (out == NULL){
                printf("[WARN] Cannot open %s for writing; continuing without CSV output.\n", filename);
            } else {
                fprintf(out, "time,idx,rho,vel,pres\n");
                for (i32 i = 0; i < NX; i += NX / 1000){
                    fprintf(out, "%.6f,%d,%.12e,%.12e,%.12e\n", t, i, rho[i], vel[i], pres[i]);
                }
            fclose(out);
            printf("[INFO] Saved snapshot at t=%.6f to %s\n", t, filename);
            }
        }
    }
    return 0;
}