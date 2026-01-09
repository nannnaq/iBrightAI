import numpy as np
import pywt
from statsmodels.nonparametric.smoothers_lowess import lowess
import matplotlib.pyplot as plt

from loguru import logger


class TEARFILMDATA:
    def __init__(self, x, y1, y2):
        self.x = x
        self.y1 = y1
        self.y2 = y2

    # 小波降噪函数
    def sure_threshold(self, c, sigma=None):
        """计算基于SURE方法的阈值"""
        n = len(c)
        if sigma is None:
            sigma = np.median(np.abs(c)) / 0.6745  # 使用中值绝对偏差估计噪声
        c_sorted = np.sort(np.abs(c))
        cumsum = np.cumsum(c_sorted ** 2)
        risk = (n - 2 * np.arange(1, n + 1) + cumsum) / n
        idx = np.argmin(risk)
        return c_sorted[idx]

    def wavelet_denoise(self, data, wavelet='db6', level=5):
        """执行小波降噪"""
        coeffs = pywt.wavedec(data, wavelet, level=level)
        new_coeffs = [coeffs[0]]  # 保留近似系数

        for i in range(1, len(coeffs)):
            c = coeffs[i]
            t = self.sure_threshold(c)
            c_thresh = pywt.threshold(c, t, mode='soft')
            new_coeffs.append(c_thresh)

        denoised = pywt.waverec(new_coeffs, wavelet)

        # 确保长度一致
        if len(denoised) > len(data):
            denoised = denoised[:len(data)]
        elif len(denoised) < len(data):
            denoised = np.pad(denoised, (0, len(data) - len(denoised)), mode='edge')

        return denoised

    def main(self):
        # 执行小波降噪
        denoised_y1 = self.wavelet_denoise(self.y1, wavelet='db6', level=8)
        # 二次平滑处理（LOWESS）
        frac = 7 / len(self.y1)  # 窗口大小占总数据的比例
        smoothed_y1 = lowess(denoised_y1, self.x, frac=frac, it=0, return_sorted=False)

        denoised_y2 = self.wavelet_denoise(self.y2, wavelet='db6', level=8)
        frac = 7 / len(self.y2)  # 窗口大小占总数据的比例
        smoothed_y2 = lowess(denoised_y2, self.x, frac=frac, it=0, return_sorted=False)

        # 生成对称数据
        symmetric_x = np.concatenate([-self.x[::-1], self.x])  # 从负到正
        symmetric_y = np.concatenate([denoised_y2[::-1], smoothed_y1])  # 对应的y值

        # 绘制结果
        # plt.figure(figsize=(10, 6))
        # plt.plot(symmetric_x, symmetric_y, 'g-', linewidth=1.5, label='Smoothed')
        # plt.legend()
        # plt.xlabel('x')
        # plt.ylabel('y')
        # plt.title('Denoising and Smoothing Comparison (Symmetric)')
        # plt.grid(True)
        # plt.show()

        front_data = {
            "x": np.round(symmetric_x, 2).tolist(),
            "y": symmetric_y.tolist(),
        }
        # logger.info(f"front_data: {front_data}")
        return front_data


if __name__ == '__main__':
    # 定义数据
    x = np.arange(0, 10.61, 0.2)  # 生成54个点   镜片直径10.6
    y = [5.05734543, 5.00198291, 4.78605221, 4.86117648,
         5.09656303, 5.30236453, 5.52931891, 5.65154132,
         5.74958456, 5.90086921, 6.13291025, 6.51554213,
         6.67346635, 6.96838859, 7.31500072, 7.51622997,
         7.71501317, 8.12212659, 8.46314906, 8.62083564,
         8.97058745, 9.07716099, 9.40050072, 9.6507149,
         9.82533839, 10.11833474, 10.3744937, 10.46361851,
         10.81828332, 11.16437882, 11.38434369, 14.42756513,
         17.15348713, 19.81330039, 22.3382853, 24.23605759,
         26.38425317, 28.09589107, 29.52678526, 32.71388905,
         35.29482491, 37.50829314, 39.52077398, 41.0998696,
         42.31015804, 43.28060182, 44.43622057, -530.36640133,
         -656.18176323, -764.77288058, -875.13179385, -987.29430619,
         -1101.29820707, -1217.18341321]

    C = TEARFILMDATA(x, y)
    C.main()
