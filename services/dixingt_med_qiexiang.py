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
def  parse_qiexiang_data(file_path):
    """切向曲率图"""
    xmf = OperationMXF(file_path)
    top_data = xmf.parse_tangential_curvature_map_data()
    data = xmf.parse_calculated_value(key_data=top_data)
    Z = data.astype(float)

    # 转换无效值为NaN
    Z[Z == 0] = np.nan

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

    Z_highres = np.flipud(Z_highres)

    # # ==========================================================
    # # =============   ↓↓↓ 新增逻辑：准备ECharts数据 ↓↓↓   ===========
    # # ==========================================================
    # echarts_data = []
    # # 遍历高分辨率网格的每一个点
    # for i, y in enumerate(y_range_highres):
    #     for j, x in enumerate(x_range_highres):
    #         value = Z_highres[i, j]
    #         # 只有当值不是NaN时才添加到结果中
    #         if not np.isnan(value):
    #             # ECharts热力图需要 [x, y, value] 格式
    #             echarts_data.append([round(float(x), 4), round(float(y), 4), round(float(value), 4)])
    # # ==========================================================
    # # =============   ↑↑↑ 新增逻辑：准备ECharts数据 ↑↑↑   ===========
    # # ==========================================================



    # 计算色阶范围
    min_val = np.nanmin(Z)  # 原始数据最小值
    max_val_original = np.nanmax(Z)  # 原始数据最大值
    max_val = max_val_original  # 新最大值 = 原始最大值的80%

    # 动态计算步长（保证16级分界）
    n_levels = 16  # 16级色阶
    step = (max_val - min_val) / n_levels  # 步长 = 总范围 / 色阶数

    # 创建色阶边界（17个边界点，对应16个区间）
    bounds = np.arange(min_val, max_val, step)

    # 创建颜色映射（保持原16级色阶定义）
    rgb_values = [
                     [0, 0, 100], [0, 0, 127], [0, 0, 209], [0, 45, 255],
                     [0, 119, 255], [0, 198, 255], [0, 255, 216], [0, 255, 112],
                     [0, 255, 0], [112, 255, 0], [216, 255, 0], [255, 206, 0],
                     [255, 142, 0], [255, 79, 0], [255, 15, 0], [191, 0, 0]
                 ][::-1]  # 反转顺序：红（陡峭）→蓝（平坦）
    normalized_colors = [[r / 255, g / 255, b / 255] for r, g, b in rgb_values]
    custom_cmap = ListedColormap(normalized_colors, N=n_levels)
    custom_cmap.set_bad(color=[0.4, 0.4, 0.4])  # NaN值显示为灰色

    # 绘制热力图（其余设置不变）
    plt.figure(figsize=(10, 10), dpi=100)
    norm = BoundaryNorm(bounds, ncolors=n_levels)
    im = plt.imshow(Z_highres, cmap=custom_cmap, norm=norm, extent=[-6, 6, -6, 6], aspect='equal')

    # 设置颜色条刻度标签（居中显示区间值）
    tick_positions = (bounds[:-1] + bounds[1:]) / 2  # 16个色块中心位置
    tick_labels = [f"{val:.2f}" for val in tick_positions]  # 标签为实际中心值
    cbar = plt.colorbar(im, fraction=0.046, pad=0.04)
    cbar.set_ticks(tick_positions)
    cbar.set_ticklabels(tick_labels)
    cbar.set_label('Elevation (μm)', fontsize=14)

    # 13. 添加网格（使用浅灰色）
    plt.grid(True, color='#999999', linestyle='--', alpha=0.3)

    # 14. 设置背景为深灰色
    plt.gca().set_facecolor('#222222')  # 深灰色背景

    uuid_id = uuid.uuid4()

    # 确保目录存在并保存图片
    fa_image_dir = dirs / "dxt_image_tangential_curvature"
    if not os.path.exists(fa_image_dir):
        os.makedirs(fa_image_dir)

    save_dir = dirs / "dxt_image_tangential_curvature" / f"{uuid_id}.png"
    save_dir_path = os.path.join("dxt_image_tangential_curvature", f"{uuid_id}.png")
    plt.savefig(save_dir)
    plt.close()
    # === 新增：返回给前端的 JSON 数据 ===
    raw_plotly_data = {
        "x": x_range_highres.tolist(),
        "y": y_range_highres.tolist(),
        "z": [[None if np.isnan(v) else v for v in row] for row in Z_highres]  # NaN替换为None，前端JS能识别
    }
    # 16. 显示结果
    # plt.tight_layout()
    # plt.show()

    # return {"save_dir_path": save_dir_path}

        # ==========================================================
    # =============   ↓↓↓ 修改返回值 ↓↓↓   =====================
    # ==========================================================
    return {"save_dir_path": save_dir_path, "raw_plotly_data": raw_plotly_data}
    # ==========================================================
    # =============   ↑↑↑ 修改返回值 ↑↑↑   =====================
    # ==========================================================


if __name__ == '__main__':
    file_path = r'/Users/makelin/Documents/ParttimeProject/Glasses_hospital/hospital-server/data/medment/MedmontStudio.mxf'
    parse_qiexiang_data(file_path)