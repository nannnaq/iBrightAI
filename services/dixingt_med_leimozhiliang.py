import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from scipy.interpolate import griddata
from services.aop_mxf import OperationMXF
from django.conf import settings
import uuid
import os
from patient.models import CornealTopography
from pathlib import Path

# 绝对路径
dirs = Path(settings.MEDIA_ROOT)


def parse_leiomozhilaing_data(file_path):
    """泪膜质量图"""
    xmf = OperationMXF(file_path)
    top_data = xmf.parse_tangential_curvature_map_data()
    data = xmf.parse_calculated_value(key_data=top_data)
    Z = data.astype(float)

    # 转换无效值为NaN
    Z[Z == -1] = np.nan

    # 2. 创建原始坐标网格
    x_range_orig = np.linspace(-6, 6, 50)
    y_range_orig = np.linspace(-6, 6, 50)
    X_orig, Y_orig = np.meshgrid(x_range_orig, y_range_orig)

    # 3. 创建高分辨率网格用于插值
    interp_factor = 10  # 插值因子，增加分辨率
    x_range_highres = np.linspace(-6, 6, 50 * interp_factor)
    y_range_highres = np.linspace(-6, 6, 50 * interp_factor)
    X_highres, Y_highres = np.meshgrid(x_range_highres, y_range_highres)

    # 4. 执行二维插值
    valid_indices = np.where(~np.isnan(Z))
    valid_points = np.column_stack((X_orig[valid_indices], Y_orig[valid_indices]))
    valid_values = Z[valid_indices]

    Z_highres = griddata(valid_points, valid_values,
                        (X_highres, Y_highres), method='cubic', fill_value=np.nan)



    # 6. 创建16级严格分界色阶（标准明亮版本）
    # 颜色映射顺序从陡峭(红色)到平坦(蓝色)
    rgb_values = [
        [0, 0, 100],           # -3000~-3200μm (最平坦，深蓝色)
        [0, 0, 127],           # -2800~-3000μm (深蓝色)
        [0, 0, 209],           # -2600~-2800μm (中蓝色)
        [0, 45, 255],          # -2400~-2600μm (亮蓝色)
        [0, 119, 255],         # -2200~-2400μm (青蓝色)
        [0, 198, 255],         # -2000~-2200μm (浅青)
        [0, 255, 216],         # -1800~-2000μm (青绿色)
        [0, 255, 112],         # -1600~-1800μm (草绿色)
        [0, 255, 0],           # -1400~-1600μm (绿色)
        [112, 255, 0],         # -1200~-1400μm (黄绿色)
        [216, 255, 0],         # -1000~-1200μm (黄色)
        [255, 206, 0],         # -800~-1000μm (橙黄色)
        [255, 142, 0],         # -600~-800μm (橙色)
        [255, 79, 0],          # -400~-600μm (橙红色)
        [255, 15, 0],          # -200~-400μm (红橙色)
        [191, 0, 0]            # 0~-200μm (最陡峭，深红色)
    ]
    rgb_values = rgb_values[::1]
    # 将RGB值归一化到0-1范围
    normalized_colors = [[r/255, g/255, b/255] for r, g, b in rgb_values]
    n_levels = len(normalized_colors)  # 颜色级别数

    # 7. 创建色阶边界
    min_val = -0.035
    max_val = 1.035
    step = 0.07
    bounds = np.arange(min_val, max_val + step, step)  # 17个边界点

    # 8. 设置NaN值颜色为灰色
    custom_cmap = ListedColormap(normalized_colors, N=n_levels)
    custom_cmap.set_bad(color=[100/255, 100/255, 100/255])  # RGB(100,100,100)

    # 9. 创建热力图
    plt.figure(figsize=(10, 10), dpi=100)
    norm = BoundaryNorm(bounds, ncolors=n_levels)

    # 创建图像显示
    im = plt.imshow(Z_highres,
                   cmap=custom_cmap,
                   norm=norm,  # 应用离散归一化
                   origin='lower',
                   extent=[-6, 6, -6, 6],
                   aspect='equal')

    # 10. 添加半透明黑色覆盖层降低亮度
    # 创建一个覆盖整个图像区域的黑色半透明层
    dark_layer = np.zeros((Z_highres.shape[0], Z_highres.shape[1], 4))  # 4通道：RGBA
    dark_layer[:, :, 3] = 0.2  # 设置透明度为0.2（即20%的黑色）

    # 显示这个半透明层
    plt.imshow(dark_layer,
               extent=[-6, 6, -6, 6],
               origin='lower',
               aspect='equal')

    # 11. 添加颜色条
    cbar = plt.colorbar(im, fraction=0.046, pad=0.04)
    cbar.set_label('Elevation (μm)', fontsize=14)

    # 12. 设置颜色条刻度和标签
    # 计算每个色块中心位置
    tick_positions = (bounds[:-1] + bounds[1:]) / 2  # 16个中心位置

    # 创建刻度标签 (0, -200, -400, ..., -3000)
    tick_labels = [f"{val:.2f}" for val in np.linspace(min_val+step/2 , max_val-step/2 , n_levels)]

    # 创建刻度位置与标签的映射关系
    # 由于颜色条顶部对应0(红色)，底部对应-3200(蓝色)
    # 我们需要确保0标签在红色色块中心位置（最顶部）
    tick_positions_sorted = np.sort(tick_positions)  # 从小到大排序：-3100到-100
    #tick_positions_sorted = np.flip(tick_positions_sorted)  # 从大到小排序：-100到-3100

    # 应用刻度设置
    cbar.set_ticks(tick_positions_sorted)
    cbar.set_ticklabels(tick_labels)
    cbar.ax.tick_params(labelsize=10)  # 减小字体防止重叠

    # 13. 添加网格（使用浅灰色）
    plt.grid(True, color='#999999', linestyle='--', alpha=0.3)

    # 14. 设置背景为深灰色
    plt.gca().set_facecolor('#222222')  # 深灰色背景

    uuid_id = uuid.uuid4()

    # 确保目录存在并保存图片
    fa_image_dir = dirs / "dxt_image_tear_film_quality"
    if not os.path.exists(fa_image_dir):
        os.makedirs(fa_image_dir)

    save_dir = dirs / "dxt_image_tear_film_quality" / f"{uuid_id}.png"
    save_dir_path = os.path.join("dxt_image_tear_film_quality", f"{uuid_id}.png")
    plt.savefig(save_dir)
    plt.close()

    # 16. 显示结果
    # plt.tight_layout()
    # plt.show()

    return {"save_dir_path": save_dir_path}


if __name__ == '__main__':
    file_path = r'/Users/makelin/Documents/ParttimeProject/Glasses_hospital/hospital-server/data/medment/MedmontStudio.mxf'
    parse_leiomozhilaing_data(file_path)