import numpy as np
import sympy as sp
from loguru import logger
import uuid
import os
from collections import defaultdict

from django.conf import settings

from services.medment import KBQ as m_kbq
from services.medment_4 import KBQ as m_kbq_4
from services.seour import KBQ as s_kbq
from services.seour_4 import KBQ as s_kbq_4
from services.tomey import KBQ as t_kbq
from services.tomey_4 import KBQ as t_kbq_4

import matplotlib.pyplot as plt
from scipy.interpolate import interp2d
from scipy.ndimage import gaussian_filter
from matplotlib.colors import LinearSegmentedColormap, Normalize

from patient.models import *
from pathlib import Path

# 绝对路径
dirs = Path(settings.MEDIA_ROOT)



class TearFilmHeightCalculator:
    """
    计算角膜地形图中x坐标处的 tear film 高度。并生成泪膜图
    """

    def __init__(self,
                 lens_type,
                 optical_zone_diameter, #新增光学区直径范围选择
                 ace_position,
                 flat_k,
                 ac_arc_k1,
                 base_arc_curvature_radius,
                 side_arc_position,
                 ac_arc_start,
                 ac_arc_end,
                 reverse_arc_height,
                 overall_diameter,
                 al_type,
                 degree_list,
                 file_path=None,
                 rm_file=None,
                 ch_file=None,
                 ac_arc_k2=None,
                 ac_arc_k3=None,
                 ac_arc_k4=None,
                 ):

        """
        计算角膜地形图中x坐标处的 tear film 高度。计算镜片高度
        初始化计算器
            :param lens_type: 镜片类型，'s' 或 'A' 或 'PRO'
            :param ace_position: 计算的平K结果的Q值 ACe档位
            :param flat_k: 角膜地形图 “平K”
            :param ac_arc_k1: 定制参数信息 "AC弧K值"
            :param base_arc_curvature_radius: 基弧曲率半径(mm)
            :param side_arc_position: 边弧档位
            :param ac_arc_start: AC半径起始点
            :param ac_arc_end: AC半径结束点
            :param bc_arc_end: BC半径结束点
            :param overall_diameter: 总直径
            :param al_type: 算法类型
            :param degree_list: 角度范围
            :param file_path: 角膜文件地址
            :return: 一个字典，包含x坐标和对应的 tear film 高度
        """
        self.map_lens_type = {
            's': 0.23,
            'A': 0.23,
            'PRO': 0.23
        }

        self.len_type = lens_type
        self.optical_zone_diameter = optical_zone_diameter
        self.Q = self.map_lens_type[lens_type]
        self.B = reverse_arc_height - 5  # 反转弧矢高 - 5
        self.ace_position = ace_position
        self.flat_k = flat_k
        self.ac_arc_k1 = ac_arc_k1
        self.base_arc_curvature_radius = base_arc_curvature_radius
        self.side_arc_position = side_arc_position
        self.ac_arc_start = ac_arc_start
        self.ac_arc_end = ac_arc_end
        self.reverse_arc_height = reverse_arc_height
        self.overall_diameter = overall_diameter

        self.ac_arc_k2 = ac_arc_k2
        self.ac_arc_k3 = ac_arc_k3
        self.ac_arc_k4 = ac_arc_k4

        # 四个弧的区间
        self.bc_interval = [0, self.ac_arc_start - 0.8]
        self.rc_interval = [self.ac_arc_start - 0.8, self.ac_arc_start]
        self.ac_interval = [self.ac_arc_start, self.ac_arc_end]
        self.pc_interval = [self.ac_arc_end, round(self.overall_diameter / 2 + 0.1, 1)]

        # 算法类型
        self.al_type = int(al_type)
        # 角度范围
        self.degree_list = degree_list
        # 角膜文件地址
        self.file_path = file_path
        # 角膜文件地址 tomey
        self.rm_dat_path = rm_file
        self.ch_dat_path = ch_file

        # logger.info(f"bc_interval: {self.bc_interval}")
        # logger.info(f"rc_interval: {self.rc_interval}")
        # logger.info(f"ac_interval: {self.ac_interval}")
        # logger.info(f"pc_interval: {self.pc_interval}")

    # 以下为泪膜图生成用法
    def calculate_tear_film_height(self, ac_arc_k=None):
        # 参数设置
        rel_data = RelationshipTable.objects.filter(lens_type=self.len_type, belongs_level=1)
        closest_value = min(rel_data, key=lambda item: abs(
            float(item.base_arc_curvature_radius) - self.base_arc_curvature_radius))
        # logger.info(f"第一段最接近的值：{closest_value.base_arc_curvature_radius}")
        R_BC = float(closest_value.base_arc_curvature_radius)  # 为第一

        Q = float(closest_value.lens_type_number)
        B = self.B  # 反转弧矢高 - 5
        K_BC = self.flat_k  # 角膜地形图平K
        K_AC = self.ac_arc_k1 if ac_arc_k is None else ac_arc_k  # 计算的平K结果
        Q_AC = self.ace_position
        # R_BC = self.base_arc_curvature_radius  # 基弧曲率半径(mm)
        I_angle = self.side_arc_position  # 边弧档位
        ac_arc_start = self.ac_arc_start  # AC半径起始点
        ac_arc_end = self.ac_arc_end  # AC半径结束点
        bc_arc_end = self.ac_arc_start - 0.8  # BC半径结束点
        overall_diameter = self.overall_diameter / 2 + 0.01  # 镜片总的半径
        # --- ↓↓↓解决奇偶报错 核心修改在这里 ↓↓↓ ---
        # overall_diameter = self.pc_interval[1]  # 统一使用 pc_interval 的上限
        # --- ↑↑↑ 修改结束 ↑↑↑ ---

        c = 1 / R_BC
        R_AC = 337.5 / K_AC
        c_ac = 1 / R_AC

        # 镜片高度半径对应高度列表

        lens_height_list = list()

        # 生成横坐标数组
        x_values = np.round(np.arange(0, overall_diameter, 0.1), 1)
        # 解决奇数计算报错问题，将0.1改为0.05
        # x_values = np.arange(0, overall_diameter, 0.05)
        # x_values = np.round(np.arange(0, overall_diameter, 0.05), 1)
        y_values = np.zeros_like(x_values)

        # BC段计算
        for i, x in enumerate(x_values):
            if 0 <= x <= bc_arc_end:
                denominator = 1 + np.sqrt(1 - (1 + Q) * c ** 2 * x ** 2)
                y_values[i] = -1000 * c * x ** 2 / denominator + 5

                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)

        logger.info(f"y_values{y_values}")


        # BC段终点高度
        bc_end_idx = np.where(np.isclose(x_values, bc_arc_end))[0][0]
        Hbc_end = y_values[bc_end_idx]
        Hbc_end_mm = Hbc_end * 1e-3

        logger.info(f"Hbc_end_mm{Hbc_end_mm}")

        # AC段起点计算
        x_ac_start = ac_arc_start
        denominator_ac = 1 + np.sqrt(1 - (1 + Q_AC) * c_ac ** 2 * x_ac_start ** 2)
        Hac_start = -1000 * c_ac * x_ac_start ** 2 / denominator_ac - B
        Hac_start_mm = Hac_start * 1e-3

        # 圆弧段参数计算
        k = sp.symbols('k')
        eq = sp.Eq(bc_arc_end ** 2 + (Hbc_end_mm - k) ** 2, ac_arc_start ** 2 + (Hac_start_mm - k) ** 2)
        k_sol = float(sp.solve(eq, k)[0])  # 显式转换为Python float类型
        R_mm = np.sqrt(bc_arc_end ** 2 + (Hbc_end_mm - k_sol) ** 2)  # 现在所有参数都是原生float类型

        # 圆弧段计算
        for i, x in enumerate(x_values):
            if bc_arc_end < x < ac_arc_start:
                theta = np.arccos(x / R_mm)
                y_arc_mm = R_mm * np.sin(theta) + k_sol
                y_values[i] = y_arc_mm * 1e3

                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)

        # AC段计算
        for i, x in enumerate(x_values):
            if ac_arc_start <= x <= ac_arc_end:
                denominator = 1 + np.sqrt(1 - (1 + Q_AC) * c_ac ** 2 * x ** 2)
                y_values[i] = -1000 * c_ac * x ** 2 / denominator - B

                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)

        # 导数计算
        x_sym = sp.symbols('x_sym')
        H_ac = -1 * c_ac * x_sym ** 2 / (1 + sp.sqrt(1 - (1 + Q_AC) * c_ac ** 2 * x_sym ** 2)) - B / 1000
        dH_dx = sp.diff(H_ac, x_sym)
        AC_end_x = ac_arc_end
        AC_end_H = y_values[np.where(np.isclose(x_values, AC_end_x))[0][0]]
        AC_slope = float(dH_dx.subs(x_sym, AC_end_x))

        # PC直线参数计算
        theta_AC = np.degrees(np.arctan(AC_slope))
        theta_PC = theta_AC + I_angle/3
        PC_slope = np.tan(np.radians(theta_PC))

        # PC段计算
        for i, x in enumerate(x_values):
            if x > ac_arc_end:
                y_values[i] = AC_end_H + 1000 * PC_slope * (x - AC_end_x)

                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)

        # 输出最终结果
        # logger.info("计算完成，结果已存储在y_values数组中")
        # print("x_values shape:", x_values.shape)
        # print("y_values shape:", y_values)
        # print("y_values_list shape:", lens_height_list)

        return {
            "x_values": x_values,
            "y_values": y_values,
            "y_values_list": lens_height_list,
            "min_base_arc_curvature_radius": closest_value.base_arc_curvature_radius,
        }

    def calculate_tear_film_height_pro_A(self, ac_arc_k=None):
    
        bc = self.optical_zone_diameter   # 例如 4.7 ~ 7.0

        if 4.7 <= bc <= 5.3:
            lens_type_for_calc = "A+++"
        elif 5.4 <= bc <= 5.7:
            lens_type_for_calc = "A++"
        else:
            lens_type_for_calc = "PRO"

        Q_AC = self.ace_position
        K_AC = self.ac_arc_k1 if ac_arc_k is None else ac_arc_k  # 计算的平K结果 (软件上的AC弧K值）      计算的陡K结果=计算的平K结果(软件上的AC弧K值）+软件上环曲档位对应的环曲量
        B = self.B  # B+5=反转弧矢高

        rel_data = RelationshipTable.objects.filter(lens_type=lens_type_for_calc, belongs_level=1)
        closest_value = min(rel_data, key=lambda item: abs(
            float(item.base_arc_curvature_radius) - self.base_arc_curvature_radius))
        # logger.info(f"第一段最接近的值：{closest_value.base_arc_curvature_radius}")
        R_BC1 = float(
            closest_value.base_arc_curvature_radius)  # 为第一段基弧曲率半径，R_BC(计算)=337.5 / (K_BC - 4 - 0.75)  K_BC为角膜地形图平K；-4为球镜度 0.75为固定值,再到表中找到最接近R_BC(计算)的基弧曲率半径，则为R_BC1，选A、PRO系列才有两段，S系列只有一段，Q恒定为0.23

        rel_data = RelationshipTable.objects.filter(lens_type=lens_type_for_calc, belongs_level=2)
        closest_value_01 = min(rel_data, key=lambda item: abs(
            float(item.base_arc_curvature_radius) - self.base_arc_curvature_radius))
        # logger.info(f"第二段最接近的值：{closest_value_01.base_arc_curvature_radius}")
        R_BC2 = float(closest_value_01.base_arc_curvature_radius)  # 为第二段基弧曲率半径，根据R_BC(计算)找到再到表中找到最接近的基弧曲率半径，则为R_BC2

        c_1 = 1 / R_BC1
        c_2 = 1 / R_BC2
        Q_BC1 = float(closest_value.lens_type_number)  # BC段第一段0-2mm范围内的Q值，固定为0.23
        # logger.info(f"第一段Q值：{closest_value.lens_type_number}")
        Q_BC2 = float(closest_value_01.lens_type_number)  # 当选择A、PRO系列时，BC段第二段的Q值，根据R_BC(计算)到表中找到最接近的基弧曲率半径R_BC2所对应的Q值
        # logger.info(f"第二段Q值：{closest_value_01.lens_type_number}")
        I_angle = self.side_arc_position  # 边弧档位
        ac_arc_start = self.ac_arc_start  # AC半径起始点
        ac_arc_end = self.ac_arc_end  # AC半径结束点
        bc_arc_end = self.ac_arc_start - 0.8  # BC半径结束点
        # overall_diameter = self.overall_diameter / 2 + 0.01  # 镜片总的半径
        # --- ↓↓↓ 解决奇偶报错 核心修改在这里 ↓↓↓ ---
        overall_diameter = self.pc_interval[1]  # 统一使用 pc_interval 的上限
        # --- ↑↑↑ 修改结束 ↑↑↑ ---

        R_AC = 337.5 / K_AC
        c_ac = 1 / R_AC

        lens_height_list = list()
        # 生成横坐标数组
        x_values = np.round(np.arange(0, overall_diameter, 0.1), 1)  # 5.3是镜片总的半径
        # 解决奇数计算报错问题，将0.1改为0.05
        # x_values = np.arange(0, overall_diameter, 0.05)
        # x_values = np.round(np.arange(0, overall_diameter, 0.05), 1)  # 5.3是镜片总的半径
        y_values = np.zeros_like(x_values)

        # BC段计算
        for i, x in enumerate(x_values):
            if 0 <= x <= 2.0:  # 0-2.0是BC第一段的范围，
                denominator_1 = 1 + np.sqrt(1 - (1 + Q_BC1) * c_1 ** 2 * x ** 2)
                y_values[i] = -1000 * c_1 * x ** 2 / denominator_1 + 5
                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)
        for i, x in enumerate(x_values):
            if 2 < x <= bc_arc_end:  # 2.0-3.0是BC第二段段的范围，总的0-3.0为BC的范围，也就是光学区半径
                denominator_2 = 1 + np.sqrt(1 - (1 + Q_BC2) * c_2 ** 2 * x ** 2)
                y_values[i] = -1000 * c_2 * x ** 2 / denominator_2 + 5
                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)

        # BC段终点高度
        bc_end_idx = np.where(np.isclose(x_values, bc_arc_end))[0][0]
        Hbc_end = y_values[bc_end_idx]
        Hbc_end_mm = Hbc_end * 1e-3

        # AC段起点计算
        x_ac_start = ac_arc_start  # 3.8是指AC段的起点横坐标
        denominator_ac = 1 + np.sqrt(1 - (1 + Q_AC) * c_ac ** 2 * x_ac_start ** 2)
        Hac_start = -1000 * c_ac * x_ac_start ** 2 / denominator_ac - B  # B值
        Hac_start_mm = Hac_start * 1e-3

        # RC圆弧段参数计算
        k = sp.symbols('k')
        eq = sp.Eq(bc_arc_end ** 2 + (Hbc_end_mm - k) ** 2,
                   ac_arc_start ** 2 + (Hac_start_mm - k) ** 2)  # 3.0是指BC段的结束点横坐标，3.8是指AC段的起点横坐标
        k_sol = float(sp.solve(eq, k)[0])  # 显式转换为Python float类型
        R_mm = np.sqrt(bc_arc_end ** 2 + (Hbc_end_mm - k_sol) ** 2)  # 现在所有参数都是原生float类型；  R_mm为反转弧曲率半径

        # 圆弧段计算
        for i, x in enumerate(x_values):
            if bc_arc_end < x < ac_arc_start:  # 3.0-3.8是指RC段的范围，固定是0.8
                theta = np.arccos(x / R_mm)
                y_arc_mm = R_mm * np.sin(theta) + k_sol
                y_values[i] = y_arc_mm * 1e3
                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)

        # AC段计算
        for i, x in enumerate(x_values):
            if ac_arc_start <= x <= ac_arc_end:  # 3.8-4.8是指AC段的范围
                denominator = 1 + np.sqrt(1 - (1 + Q_AC) * c_ac ** 2 * x ** 2)
                y_values[i] = -1000 * c_ac * x ** 2 / denominator - B  # B值
                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)

        # 导数计算
        x_sym = sp.symbols('x_sym')
        H_ac = -1 * c_ac * x_sym ** 2 / (1 + sp.sqrt(1 - (1 + Q_AC) * c_ac ** 2 * x_sym ** 2)) - B / 1000  # B值
        dH_dx = sp.diff(H_ac, x_sym)
        AC_end_x = ac_arc_end  # 4.8是AC段结束点的横坐标
        AC_end_H = y_values[np.where(np.isclose(x_values, ac_arc_end))[0][0]]
        AC_slope = float(dH_dx.subs(x_sym, AC_end_x))

        # PC直线参数计算
        theta_AC = np.degrees(np.arctan(AC_slope))
        theta_PC = theta_AC + I_angle/3  # 8.8为边弧档位0对应的角度
        PC_slope = np.tan(np.radians(theta_PC))

        # PC段计算
        for i, x in enumerate(x_values):
            if x > ac_arc_end:  # PC段的范围固定是0.5 (半径)
                y_values[i] = AC_end_H + 1000 * PC_slope * (x - AC_end_x)

                lens_height_dict = dict()
                lens_height_dict["radius"] = float(x)
                lens_height_dict["height"] = y_values[i]
                lens_height_list.append(lens_height_dict)

        # 输出最终结果
        # logger.info("计算完成，结果已存储在y_values数组中")
        # logger.info("x_values shape:", x_values.shape)
        # logger.info("y_values shape:", y_values)
        # logger.info("y_values_list shape:", lens_height_list)

        return {
            "x_values": x_values,
            "y_values": y_values,
            "y_values_list": lens_height_list,
            "min_base_arc_curvature_radius": closest_value.base_arc_curvature_radius,
        }

    def wavelet_denoise(self, al_type, radius, degree_list, filter_data=None, rm_dat_path=None, ch_dat_path=None):
        """
        计算角膜高度
        :param al_type:算法类型
        CUSTOM_TYPE_CHOICES = [
            ("0", "Medment普通定制"),
            ("1", "Medment四轴定制"),
            ("2", "Seour普通定制"),
            ("3", "Seour四轴定制"),
            ("4", "tomey普通定制"),
            ("5", "tomey四轴定制"),
        ]
        """
        data_list = []
        # logger.info(f"al_type: {al_type}")
        # logger.info(f"al_type: {type(al_type)}")
        al_type = int(al_type)
        if al_type == 0:
            kbq_list = m_kbq(radius=radius, degree_list=degree_list, filter_data=filter_data)
        elif al_type == 1:
            kbq_list = m_kbq_4(radius=radius, degree_list=degree_list, filter_data=filter_data)
        elif al_type == 2:
            kbq_list = s_kbq(radius=radius, degree_list=degree_list, filter_data=filter_data)
        elif al_type == 3:
            kbq_list = s_kbq_4(radius=radius, degree_list=degree_list, filter_data=filter_data)
        elif al_type == 4:
            kbq_list = t_kbq(radius=radius, degree_list=degree_list, rm_dat_path=rm_dat_path, ch_dat_path=ch_dat_path)
        elif al_type == 5:
            kbq_list = t_kbq_4(radius=radius, degree_list=degree_list, rm_dat_path=rm_dat_path, ch_dat_path=ch_dat_path)

        radius_angle_data = kbq_list.radius_angle()

        return {
            "data_list": radius_angle_data,
            "degree_list": degree_list,
        }

    def replace_nan_values(self, y_values, ac_k=None):
        """ 处理AC段和PC段的NaN值
        Args:
            y_values: 原始数据数组(长度54)
            Q_AC: 软件上ACe档位对应的数值
            ac_arc_k1:   平k ac_arc_k1 陡k steep_k_calcul
            reverse_arc_height: 反转弧矢高
        """
        # 生成横坐标数组
        # print(f"原角膜高度参数：{y_values}")
        x_values = np.round(np.arange(self.bc_interval[0], self.pc_interval[1], 0.1), decimals=1)  # 5.3是总的镜片半径
        # 解决奇数计算报错问题，将0.1改为0.05
        # x_values = np.arange(self.bc_interval[0], self.pc_interval[1], 0.05) # 5.3是总的镜片半径
        # x_values = np.round(np.arange(self.bc_interval[0], self.pc_interval[1], 0.05), decimals=1)  # 5.3是总的镜片半径

        # AC PC范围
        ac_start, ac_end = self.ac_interval[0], self.ac_interval[1]  # AC段范围
        pc_start, pc_end = self.pc_interval[0], self.pc_interval[1]  # PC段范围
        B = self.B  # B值
        R_AC = 337.5 / (self.ac_arc_k1 if ac_k is None else ac_k)  # 平k ac_arc_k1，陡k steep_k_calcul
        c_ac = 1 / R_AC
        # 获取分段索引
        mask_AC = (x_values >= ac_start) & (x_values <= ac_end)
        indices_AC = np.where(mask_AC)[0]
        mask_PC = (x_values > pc_start) & (x_values <= pc_end)
        indices_AC_PC = np.where((x_values >= ac_start) & (x_values <= pc_end))[0]

        # ===== 计算AC段平均差值 =====
        ac_diffs = []
        for idx in indices_AC:
            if not np.isnan(y_values[idx]):
                x_val = x_values[idx]
                # 模型计算
                discriminant = 1 - (1 + self.ace_position) * (c_ac ** 2) * (x_val ** 2)
                denominator = 1 + np.sqrt(discriminant)
                height_y = (-1 * c_ac * x_val ** 2) / denominator - B / 1000
                ac_diffs.append(height_y - y_values[idx])

        avg_diff_AC = np.mean(ac_diffs)

        # ===== 替换AC-PC段NaN值 =====
        for idx in indices_AC_PC:
            if np.isnan(y_values[idx]):
                x_val = x_values[idx]
                # 模型计算
                discriminant = 1 - (1 + self.ace_position) * (c_ac ** 2) * (x_val ** 2)
                denominator = 1 + np.sqrt(discriminant)
                height_y = (-1 * c_ac * x_val ** 2) / denominator - B / 1000

                # 分段处理
                is_AC_segment = (ac_start <= x_val <= ac_end)
                is_PC_segment = (pc_start < x_val <= pc_end)

                if is_AC_segment:
                    y_values[idx] = height_y - avg_diff_AC  # AC段减差值
                elif is_PC_segment:
                    y_values[idx] = height_y - avg_diff_AC  # PC段减差值

        return y_values

    def main_calculate(self):
        cornea_height = self.wavelet_denoise(
            al_type=self.al_type,
            radius=[self.bc_interval[0], self.pc_interval[1] - 0.1],
            degree_list=self.degree_list,
            filter_data=self.file_path,
            rm_dat_path=self.rm_dat_path,
            ch_dat_path=self.ch_dat_path
        )
        data_list = cornea_height["data_list"]
        # logger.info(f"角膜高度:{data_list}")

        # 遍历cornea_height["data_list"]中的每个元素
        radius_list01 = list()
        radius_list02 = list()
        radius_list03 = list()
        radius_list04 = list()

        # 普通定制
        if len(data_list[0]) == 3:
            if self.len_type == "PRO" or self.len_type == "A":
                lens_height = self.calculate_tear_film_height_pro_A()
            else:

                lens_height = self.calculate_tear_film_height()

            # lens_height = self.calculate_tear_film_height()

            for item in data_list:
                cornea_height_item_0 = item.get("degree_list_k1") * (-1)
                cornea_height_item_1 = item.get("degree_list_k2") * (-1)
                radius_list01.append(cornea_height_item_0)
                radius_list02.append(cornea_height_item_1)

            # 补缺值
            radius_list01 = self.replace_nan_values(radius_list01)
            radius_list02 = self.replace_nan_values(radius_list02)
            # logger.info(f"radius_list01_nan:{radius_list01}")
            # logger.info(f"radius_list02_nan:{radius_list02}")
            # logger.info(f"radius_list01_nan:{type(radius_list01)}")
            # logger.info(f"radius_list02_nan:{type(radius_list02)}")

            radius_list01_1000 = [float(i) * 1000 for i in radius_list01]
            radius_list02_1000 = [float(i) * 1000 for i in radius_list02]

            # logger.info(f"len_height:{lens_height['y_values']}")
            # logger.info(f"radius_list01:{radius_list01_1000}")
            # logger.info(f"radius_list02:{radius_list02_1000}")

            radius_diff01 = lens_height['y_values'] - np.array(radius_list01_1000)
            radius_diff02 = lens_height['y_values'] - np.array(radius_list02_1000)
            # 如果是seour定制,将radius_diff01的前两个值替换成0
            if self.al_type == 2 or self.al_type == 3:
                radius_list01_1000[:2] = [0, 0]
                radius_list02_1000[:2] = [0, 0]

                radius_diff01[:2] = 0
                radius_diff02[:2] = 0
            elif self.al_type == 4 or self.al_type == 5:
                radius_list01_1000[:3] = [0, 0, 0]
                radius_list02_1000[:3] = [0, 0, 0]

                radius_diff01[:3] = 0
                radius_diff02[:3] = 0

            # logger.error(radius_list01)
            # logger.error(radius_list02)

            # logger.error(f"角度{self.degree_list[0]}差值：{radius_diff01}")
            # logger.error(f"角度{self.degree_list[1]}差值：{radius_diff02}")

            return {
                "x": lens_height['x_values'],
                "y1": radius_diff01.tolist(),
                "y2": radius_diff02.tolist(),
                "lens_height": lens_height['y_values'].tolist(),
                "radius_list01": radius_list01_1000,
                "radius_list02": radius_list02_1000,
                "min_base_arc_curvature_radius": lens_height["min_base_arc_curvature_radius"],
            }

        # 四轴定制
        elif len(data_list[0]) == 5:
            if self.len_type == "PRO" or self.len_type == "A":
                lens_height_01 = self.calculate_tear_film_height_pro_A(ac_arc_k=self.ac_arc_k1)
                lens_height_02 = self.calculate_tear_film_height_pro_A(ac_arc_k=self.ac_arc_k2)
                lens_height_03 = self.calculate_tear_film_height_pro_A(ac_arc_k=self.ac_arc_k3)
                lens_height_04 = self.calculate_tear_film_height_pro_A(ac_arc_k=self.ac_arc_k4)
            else:
                lens_height_01 = self.calculate_tear_film_height(ac_arc_k=self.ac_arc_k1)
                lens_height_02 = self.calculate_tear_film_height(ac_arc_k=self.ac_arc_k2)
                lens_height_03 = self.calculate_tear_film_height(ac_arc_k=self.ac_arc_k3)
                lens_height_04 = self.calculate_tear_film_height(ac_arc_k=self.ac_arc_k4)

            # lens_height = self.calculate_tear_film_height()
            for item in data_list:
                cornea_height_item_0 = item.get("degree_list_k1") * (-1)
                cornea_height_item_1 = item.get("degree_list_k2") * (-1)
                cornea_height_item_2 = item.get("degree_list_k3") * (-1)
                cornea_height_item_3 = item.get("degree_list_k4") * (-1)
                radius_list01.append(cornea_height_item_0)
                radius_list02.append(cornea_height_item_1)
                radius_list03.append(cornea_height_item_2)
                radius_list04.append(cornea_height_item_3)

            # logger.info(f"radius_list01:{radius_list01}")
            # logger.info(f"radius_list02:{radius_list02}")
            # logger.info(f"radius_list03:{radius_list03}")
            # logger.info(f"radius_list04:{radius_list04}")
            # 补缺值
            radius_list01 = self.replace_nan_values(radius_list01, ac_k=self.ac_arc_k1)
            radius_list02 = self.replace_nan_values(radius_list02, ac_k=self.ac_arc_k2)
            radius_list03 = self.replace_nan_values(radius_list03, ac_k=self.ac_arc_k3)
            radius_list04 = self.replace_nan_values(radius_list04, ac_k=self.ac_arc_k4)
            # logger.info(f"radius_list01_nan:{radius_list01}")
            # logger.info(f"radius_list02_nan:{radius_list02}")
            # logger.info(f"radius_list03_nan:{radius_list03}")
            # logger.info(f"radius_list04_nan:{radius_list04}")
            # logger.info(f"radius_list01_nan:{type(radius_list01)}")
            # logger.info(f"radius_list02_nan:{type(radius_list02)}")
            # logger.info(f"radius_list03_nan:{type(radius_list03)}")
            # logger.info(f"radius_list04_nan:{type(radius_list04)}")

            radius_list01_1000 = [float(i) * 1000 for i in radius_list01]
            radius_list02_1000 = [float(i) * 1000 for i in radius_list02]
            radius_list03_1000 = [float(i) * 1000 for i in radius_list03]
            radius_list04_1000 = [float(i) * 1000 for i in radius_list04]

            # logger.info(f"len_height:{lens_height['y_values']}")
            # logger.info(f"radius_list01:{radius_list01_1000}")
            # logger.info(f"radius_list02:{radius_list02_1000}")

            radius_diff01 = lens_height_01['y_values'] - np.array(radius_list01_1000)
            radius_diff02 = lens_height_02['y_values'] - np.array(radius_list02_1000)
            radius_diff03 = lens_height_03['y_values'] - np.array(radius_list03_1000)
            radius_diff04 = lens_height_04['y_values'] - np.array(radius_list04_1000)

            # 如果是seour定制,将radius_diff01的前两个值替换成0
            if self.al_type == 2 or self.al_type == 3:
                radius_list01_1000[:2] = [0, 0]
                radius_list02_1000[:2] = [0, 0]
                radius_list03_1000[:2] = [0, 0]
                radius_list04_1000[:2] = [0, 0]

                radius_diff01[:2] = 0
                radius_diff02[:2] = 0
                radius_diff03[:2] = 0
                radius_diff04[:2] = 0
            elif self.al_type == 4 or self.al_type ==5:
                radius_list01_1000[:3] = [0, 0, 0]
                radius_list02_1000[:3] = [0, 0, 0]
                radius_list03_1000[:3] = [0, 0, 0]
                radius_list04_1000[:3] = [0, 0, 0]

                radius_diff01[:3] = 0
                radius_diff02[:3] = 0
                radius_diff03[:3] = 0
                radius_diff04[:3] = 0

            # logger.error(radius_list01)
            # logger.error(radius_list02)

            # logger.error(f"角度{self.degree_list[0]}差值：{radius_diff01}")
            # logger.error(f"角度{self.degree_list[1]}差值：{radius_diff02}")

            return {
                "x": lens_height_01['x_values'],
                "y1": radius_diff01.tolist(),
                "y2": radius_diff02.tolist(),
                "y3": radius_diff03.tolist(),
                "y4": radius_diff04.tolist(),
                "lens_height_01": lens_height_01['y_values'].tolist(),
                "lens_height_02": lens_height_02['y_values'].tolist(),
                "lens_height_03": lens_height_03['y_values'].tolist(),
                "lens_height_04": lens_height_04['y_values'].tolist(),
                "radius_list01": radius_list01_1000,
                "radius_list02": radius_list02_1000,
                "radius_list03": radius_list03_1000,
                "radius_list04": radius_list04_1000,
                "min_base_arc_curvature_radius": lens_height_01["min_base_arc_curvature_radius"],
            }


class FluorescentStaining:
    def __init__(self, degree_list, acc_id, overall_diameter, optical_zone_diameter):
        self.overall_diameter = overall_diameter  # 镜片总的半径
        self.optical_zone_diameter = optical_zone_diameter  # 光学区直径
        self.degree_list = sorted(degree_list)
        self.acc_id = acc_id

    # 以下为荧光染色图用法
    def fluorescent_staining(self, h1, h2, h3, h4):
        # logger.info(f"h1:{h1}")
        # logger.info(f"h2:{h2}")
        # logger.info(f"h3:{h3}")
        # logger.info(f"h4:{h4}")

        # 原始数据部分保持不变
        H1 = np.array(h1)
        H2 = np.array(h2)
        H3 = np.array(h3)
        H4 = np.array(h4)  # 差值H1对应120° H2对应210° H3对应300° H4对应30°
        # 定义原始角度和半径
        angles = np.arange(0, 360, 1)
        num_points = len(H1)
        r = np.linspace(0, self.overall_diameter / 2, num_points)  # 5.3是镜片总的的半径

        # 计算原始厚度矩阵
        tear_film_thickness = np.zeros((num_points, len(angles)))  # 下列四个角度对应的就是平K和陡K四个角度
        # logger.info(f"四个角度：{self.degree_list}")
        for j in range(num_points):
            for i, alpha in enumerate(angles):
                if self.degree_list[0] <= alpha < self.degree_list[1]:
                    tear_film_thickness[j, i] = 0.5 * (H4[j] - H1[j]) * np.cos(
                        np.radians((alpha - self.degree_list[0]) * 2)) + 0.5 * (
                                                        H4[j] + H1[j])

                elif self.degree_list[1] <= alpha < self.degree_list[2]:
                    tear_film_thickness[j, i] = 0.5 * (H1[j] - H2[j]) * np.cos(
                        np.radians((alpha - self.degree_list[1]) * 2)) + 0.5 * (
                                                        H1[j] + H2[j])
                elif self.degree_list[2] <= alpha < self.degree_list[3]:
                    tear_film_thickness[j, i] = 0.5 * (H2[j] - H3[j]) * np.cos(
                        np.radians((alpha - self.degree_list[2]) * 2)) + 0.5 * (
                                                        H2[j] + H3[j])
                elif alpha >= self.degree_list[3] or alpha < self.degree_list[0]:
                    adjusted_alpha = alpha - 360 if alpha >= self.degree_list[3] else alpha
                    tear_film_thickness[j, i] = 0.5 * (H3[j] - H4[j]) * np.cos(
                        np.radians((adjusted_alpha + (360 - self.degree_list[3])) * 2)) + 0.5 * (H3[j] + H4[j])

        # 新增插值参数定义
        r_interp = np.linspace(0, self.overall_diameter / 2, 500)  # 半径插值点，5.3是镜片总的的半径
        angles_interp = np.linspace(0, 360, 720)  # 角度插值点（关键修复）

        # 执行插值
        interp_func = interp2d(angles, r, tear_film_thickness, kind='cubic')
        tear_film_thickness_interp = interp_func(angles_interp, r_interp)
        # 添加高斯模糊
        sigma = 15 # 控制模糊强度
        #在角度方向扩展数据以处理周期性边界
        extended_data = np.hstack([tear_film_thickness_interp, tear_film_thickness_interp, tear_film_thickness_interp])
        #对扩展数据进行模糊
        extended_blurred = gaussian_filter(extended_data, sigma=sigma)
        # 取中间部分作为最终结果
        tear_film_thickness_interp = extended_blurred[:, 720:1440]

        # 转换为笛卡尔坐标系（此处已正确定义angles_interp）
        Theta_interp, R_interp = np.meshgrid(
            np.radians(angles_interp),
            r_interp
        )
        X_cart = R_interp * np.cos(Theta_interp)
        Y_cart = R_interp * np.sin(Theta_interp)

        # 定义颜色方案
        # start_color_inner = np.array([13, 13, 13]) / 255  # 暗黑色
        # end_color_inner = np.array([0.4, 1, 0.28])  # 亮绿色

        # 定义颜色方案 修改为单一颜色映射
        start_color = np.array([0.08, 0.21, 0.03]) # 暗黑色
        end_color = np.array([0.4, 1, 0.28])  # 亮绿色

        # 创建绿色渐变映射
        # green_colormap = np.column_stack([
        #     np.linspace(0.08, 0.4, 256),
        #     np.linspace(0.21, 1, 256),
        #     np.linspace(0.03, 0.28, 256)
        # ])

        #创建单一颜色映射
        single_colormap = LinearSegmentedColormap.from_list('single_cmap', [start_color, end_color])

        # 创建区域掩码  3.0是基弧半径，也就是基弧半径内是一种颜色映射、基弧半径外是另外一种颜色映射
        # mask_inner = R_interp <= self.optical_zone_diameter / 2  # 3.0是光学区半径
        # mask_outer = R_interp > self.optical_zone_diameter / 2  # 3.0是光学区半径

        #计算新的显示范围以增强对比度
        data_min = np.min(tear_film_thickness_interp)
        data_max = np.max(tear_film_thickness_interp)
        data_range = data_max - data_min
        
        #压缩显示范围以增强对比度（只显示中间80%的数据范围）
        display_min = data_min + 0. * data_range
        display_max = data_max - 0.* data_range

        # 创建归一化对象
        # norm_inner = Normalize(vmin=20, vmax=70)
        # norm_outer = Normalize(vmin=1, vmax=70)

        # 创建归一化对象（压缩范围）
        normsingle = Normalize(vmin=display_min, vmax=display_max)

        # 创建自定义颜色映射
        # cmap_inner = LinearSegmentedColormap.from_list('inner_cmap', [start_color_inner, end_color_inner])
        # cmap_outer = LinearSegmentedColormap.from_list('outer_cmap',
        #                                                [(0.08, 0.21, 0.03), (0.4, 1, 0.28)], N=256)

        # 应用掩码和颜色映射
        # inner_data = np.where(mask_inner, tear_film_thickness_interp, np.nan)
        # outer_data = np.where(mask_outer, tear_film_thickness_interp, np.nan)

        # 绘制图形
        fig, ax = plt.subplots(figsize=(7, 7))

        # # 先绘制外围区域
        # img_outer = ax.pcolormesh(X_cart, Y_cart, outer_data,
        #                           cmap=cmap_outer,
        #                           norm=norm_outer,
        #                           shading='auto')

        # # 再绘制内部区域
        # img_inner = ax.pcolormesh(X_cart, Y_cart, inner_data,
        #                           cmap=cmap_inner,
        #                           norm=norm_inner,
        #                           shading='auto')

        # 使用单一颜色映射绘制整个图像
        img_single = ax.pcolormesh(X_cart, Y_cart, tear_film_thickness_interp,
                                  cmap=single_colormap,
                                  norm=normsingle,
                                  shading='auto')

        # 设置图形属性
        ax.set_xlim(-6, 6)
        ax.set_ylim(-6, 6)
        ax.set_title('Customized Fluorescent Staining Pattern')
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_aspect('equal')

        # 添加颜色条（可选）
        # plt.colorbar(img_inner, label='Inner Thickness (20-70 μm)')
        # plt.colorbar(img_outer, label='Outer Thickness (10-70 μm)')
        uuid_id = uuid.uuid4()

        # 确保目录存在
        fa_image_dir = dirs / "fa_image"
        if not os.path.exists(fa_image_dir):
            os.makedirs(fa_image_dir)

        save_dir = dirs / "fa_image" / f"{uuid_id}.png"
        save_dir_path = os.path.join("fa_image", f"{uuid_id}.png")
        update = ACCustomization.objects.filter(id=self.acc_id).update(
            fluorescent_staining_image=str(save_dir_path)
        )

        plt.savefig(save_dir)
        plt.close()
        # plt.show()

        return {
            "x": list(X_cart),
            "y": list(Y_cart),
            "updated": update,
        }


if __name__ == '__main__':
    # 泪膜图
    calculator = TearFilmHeightCalculator(lens_type="s",
                                          ace_position=-0.25,
                                          flat_k=41.01,
                                          ac_arc_k1=45.25,  # 平k ac_arc_k1，陡k steep_k_calculate
                                          base_arc_curvature_radius=7.39,
                                          side_arc_position=8.8,
                                          ac_arc_start=3.8,
                                          ac_arc_end=4.8,
                                          reverse_arc_height=40.0,
                                          overall_diameter=10.6,
                                          al_type=0,
                                          degree_list=[40, 220],
                                          # al_type=1,
                                          # degree_list=[30, 120, 210, 300],
                                          file_path="../data/medment/1920-04-13-右.mxf"
                                          )
    ca_h1_h3 = calculator.main_calculate()
    # calculator = TearFilmHeightCalculator(lens_type="s",
    #                                       ace_position=-0.25,
    #                                       flat_k=41.01,
    #                                       # ac_arc_k1=39.25,  # 平k ac_arc_k1，陡k steep_k_calculate
    #                                       ac_arc_k1=41.50,  # 平k ac_arc_k1，陡k steep_k_calculate
    #                                       base_arc_curvature_radius=8.18,
    #                                       side_arc_position=8.8,
    #                                       ac_arc_start=3.8,
    #                                       ac_arc_end=4.8,
    #                                       reverse_arc_height=50.0,
    #                                       overall_diameter=10.6,
    #                                       al_type=0,
    #                                       degree_list=[40, 220],
    #                                       # al_type=1,
    #                                       # degree_list=[30, 120, 210, 300],
    #                                       file_path="../data/medment/1920-04-13-右.mxf"
    #                                       )
    # ca_h2_h4 = calculator.main_calculate()
    print(ca_h1_h3)

    # 荧光染色图
    # fluorescent_staining = FluorescentStaining(degree=30, acc_id=15)
    # fluorescent_staining.fluorescent_staining(
    #     h1=ca_h1_h3['y1'],
    #     h3=ca_h1_h3['y2'],
    #     h2=ca_h2_h4['y1'],
    #     h4=ca_h2_h4['y2']
    # )
