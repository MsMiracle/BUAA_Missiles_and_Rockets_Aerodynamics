# 导弹与运载火箭气动计算大作业
## 题设
一个无限长的光滑直线导管，横截面积为1$m^2$，导管内有一个活塞，质量为1$kg$，左侧为真空，右侧充满空气。

初始时刻活塞和空气都静止。之后，活塞收到向右的推动力，产生加速度为：
$$a=\left\{\begin{aligned}
&3m/s^2& t\leq10s\\
&0& 10s<t\leq 30s\\
&1m/s^2& 30s<t\leq40s\\
&0& 40s<t\leq60s
\end{aligned}\right.$$

流场的温度恒定为20摄氏度，初始时刻空气的密度和压强都均匀，分别为1.205$kg/m^3$和1.0117$\times 10^5 Pa$，不考虑粘性，求活塞在60秒内的运动情况，以及流场在各个时刻的密度、速度和压强分布。

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
- 编译项目：
  ```bash
  cmake --build .
  ```
## 作者
*Mingze Qiu, School of Astronautics, BUAA*

*e-mail: qiumingze@buaa.edu.cn*

## 许可证
本项目采用 MIT License，欢迎自由使用和修改。