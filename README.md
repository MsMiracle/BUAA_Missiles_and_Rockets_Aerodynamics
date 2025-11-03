# 导弹与运载火箭气动计算大作业
## 题设
一个无限长的光滑直线导管，横截面积为 $1\,m^2$，导管内有一个活塞，质量为 $1\,kg$，左侧为真空，右侧充满空气。

初始时刻活塞和空气都静止。之后，活塞收到向右的推动力，产生加速度为：
$$a=\left\{\begin{aligned}
&3m/s^2& t\leq10s\\
&0& 10s<t\leq 30s\\
&1m/s^2& 30s<t\leq40s\\
&0& 40s<t\leq60s
\end{aligned}\right.$$

流场的温度恒定为20摄氏度，初始时刻空气的密度和压强都均匀，分别为 $1.205\,kg/m^3$ 和 $1.0117 \times 10^5 Pa$，不考虑粘性，求活塞在60秒内的运动情况，以及流场在各个时刻的密度、速度和压强分布。

## 迭代方法
使用二阶展开的差分方程对离散后的流场进行迭代计算，具体差分方程如下：
$$\left\{
  \begin{aligned}
    \rho^\prime \approx \rho+\frac{\partial\rho}{\partial t}\Delta t + \frac{\partial^2\rho}{\partial t^2}\frac{\Delta t^2}{2}\\
    \,\\
    v^\prime \approx v+\frac{\partial v}{\partial t}\Delta t + \frac{\partial^2 v}{\partial t^2}\frac{\Delta t^2}{2}
  \end{aligned}
  \right.$$
其中，
$$\left\{\begin{aligned}
\frac{\partial^2\rho}{\partial t^2} = &-\frac{\partial \rho}{\partial x}\left(-v\frac{\partial v}{\partial x}-\frac{K\partial\rho}{\rho\partial x}-a\right)\\
&-v\left(-\frac{\partial v}{\partial x}-v\frac{\partial^2\rho}{\partial x^2}-\frac{\partial \rho}{\partial x}\frac{\partial v}{\partial x}-\rho\frac{\partial ^2v}{\partial x^2}\right)\\
&-\frac{\partial v}{\partial x}\left(-v\frac{\partial\rho}{\partial x}-\rho\frac{\partial v}{\partial x}\right)\\
&-\rho\left(-\frac{\partial v}{\partial x}\frac{\partial v}{\partial x}-v\frac{\partial^2v}{\partial x^2}+\frac{K}{\rho^2}\frac{\partial\rho}{\partial x}\frac{\partial \rho}{\partial x} - \frac{K}{\rho}\frac{\partial^2\rho}{\partial x^2}\right)\\
\frac{\partial^2v}{\partial t^2}= &-\frac{\partial v}{\partial x}\left(-v\frac{\partial v}{\partial x}-\frac{K}{\rho}\frac{\partial\rho}{\partial x}-a\right)\\
&-v\left(-\frac{\partial v}{\partial x}\frac{\partial v}{\partial x}-v\frac{\partial ^2v}{\partial x^2}+\frac{K}{\rho^2}\frac{\partial\rho}{\partial x}\frac{\partial\rho}{\partial x}-\frac{K}{\rho}\frac{\partial^2\rho}{\partial x^2}\right)\\
&+\frac{K}{\rho^2}\frac{\partial\rho}{\partial x}\left(-v\frac{\partial \rho}{\partial x}-\rho\frac{\partial v}{\partial x}\right)\\
&-\frac{K}{\rho}\left(-\frac{\partial v}{\partial x}\frac{\partial \rho}{\partial x}-v\frac{\partial^2\rho}{\partial x^2}-\frac{\partial\rho}{\partial x}\frac{\partial v}{\partial x}-\rho\frac{\partial^2v}{\partial x^2}\right)\\
K = &\frac{RT}{\mu^\ast}
\end{aligned}\right.$$

## 边界条件处理
**左边界**（活塞位置）：
  - 速度：$v=0$
  - 密度：通过连续性方程推导
$$\rho^\prime=\rho-\rho\mathrm{d}t\times\left.\frac{\partial v}{\partial x}\right|_{x=0}$$
  - 压强：通过状态方程计算
$$P=\frac{R}{\mu^\ast}\rho^\prime T$$

**右边界**（导管末端）：一阶向右差分。

## 仿真参数设置
您可以在 `include/constants.h` 文件中设置仿真的相关参数，为了保证收敛，可以参考下文的步长选择部分。

本项目中采用的默认参数如下：
```c
DX = 1e-3        // 空间步长，单位：米
DT = 2e-6        // 时间步长，单位：秒
```

## 数据可视化方法
- 推荐指令：
```bash
python vispy/visualizations.py --field pres --play-all --interval 0.2 --no-lock-scale
```
该指令将播放所有快照文件，显示压强分布，刷新间隔为 0.2 秒，且不锁定色标范围。

## 步长选择（DX 与 DT）
为了保证显式推进的数值稳定性与准确性，请参考以下约束：

- 超曲线型 CFL 条件（核心约束）

  系统可视作以特征速度 $a=|v|+c$ 传播的双曲方程，其中声速 $c=\sqrt{K}$，$K=\tfrac{RT}{\mu^\ast}$。

  建议时间步长满足
  $$
  \Delta t \;\le\; \text{CFL}\; \frac{\Delta x}{\max_x\big(|v(x)|+c\big)}\,.
  $$
  本程序使用二阶时间展开（与 Lax–Wendroff 相近），稳健起见取 $\text{CFL}\in[0.2,0.8]$，推荐缺省 $\text{CFL}\approx0.5$。

- 声速与常量的关系

  $$c = \sqrt{K} = \sqrt{\tfrac{RT}{\mu^\ast}}$$
  以默认参数 $R=8.31\,\mathrm{J/(mol\cdot K)}$、$T=293.15\,\mathrm{K}$、$\mu^\ast=0.029\,\mathrm{kg/mol}$，有
  $$K\approx8.40\times10^4\;\Rightarrow\;c\approx2.9\times10^2\,\mathrm{m/s}.$$

- 网格与边界的最小规模要求

  边界二阶单边差分（使用到最远第 3 个点）要求 $\text{NX}\ge4$，且 $\Delta x>0$。当 $\Delta x$ 取值更小（更细网格）时，为满足上式 CFL 约束需要相应减小 $\Delta t$。

- 实用选型建议（示例）

  若 $\Delta x=10^{-5}\,\mathrm{m}$，且早期 $|v|\approx0$，取 $\text{CFL}=0.5$，则
  $$
  \Delta t \lesssim 0.5\,\frac{10^{-5}}{\,290\,} \;\approx\;1.7\times10^{-8}\,\mathrm{s},
  $$
  因此可以设置 `DT = 1e-8`。随着流速增大，应进一步减小 `DT` 或增大 `DX` 以保持 $$\frac{(|v|+c)\,\Delta t}{\Delta x}\le \text{CFL}$$。

提示：若出现数值发散（例如 NaN），通常是 CFL 超限或边界附近梯度过大所致。优先减小 `DT`，必要时放宽输出频率以减少 I/O 干扰。

## 编译方法
本项目使用CMake进行编译。为了计算效率，我们引入了 OpenMP 进行多线程加速。在编译之前请确保您的系统已经安装了 CMake 和支持 OpenMP 的编译器（如 GCC 或 Clang）。
- 安装 OpenMP（如果尚未安装）：
  - 对于 Ubuntu/Debian 系统，可以使用以下命令安装：
    ```bash
    sudo apt-get install libomp-dev
    ```
  - 对于 macOS 系统，可以通过 Homebrew 安装：
    ```bash
    brew install libomp
    ```
  - 对于 Windows 系统，由于编译器自带 OpenMP 支持，通常不需要额外安装。
- 创建构建目录并进入该目录：
  ```bash
  mkdir build
  cd build
  ```
- 运行 CMake 配置项目：
  ```bash
  cmake ..
  // 如果不需要多线程，运行以下即可
  cmake .. -DOPENMP=OFF
  ```
- 编译运行项目：
  ```bash
  cmake --build .
  ./sim
  ```
## 作者

*Author:* Mingze Qiu, School of Astronautics, Beihang University.  
*Email:* <qiumingze@buaa.edu.cn>
## 许可证
本项目采用 MIT License，欢迎自由使用和修改。