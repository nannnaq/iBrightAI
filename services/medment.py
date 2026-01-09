# import os
import json

import numpy as np
import pandas as pd
# ⬇️⬇️ 步骤 1: 导入新的、更快的插值器 ⬇️⬇️
from scipy.interpolate import griddata, LinearNDInterpolator
from django.conf import settings
from loguru import logger

from services.aop_mxf import OperationMXF
import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eyehospital.settings")
django.setup()

BASE_DIR = settings.BASE_DIR


# logger.info(f'BASE_DIR: {BASE_DIR}/loguru.log')
# logger.add(f'{BASE_DIR}/loguru.log', rotation="100 MB")


class MedmentExtractor:
    """给定角度及弦长，计算"""

    def __init__(self, excel_file=None, xml_file=None):
        file_path = excel_file
        # 从Excel文件中读取数据并检查维度

        self.Z = pd.read_excel(file_path, header=None, skiprows=1, nrows=50).values if excel_file else OperationMXF(
            xml_file).parse_calculated_value()

        if self.Z.shape != (50, 50):
            raise ValueError("读取的矩阵不是50x50的，请检查输入文件。")

        # 替换异常值为 NaN
        self.Z[self.Z == -5e+20] = np.nan

        # 定义X和Y坐标范围
        self.x_range = np.linspace(-6, 6, 50)
        self.y_range = np.linspace(-6, 6, 50)
        self.X, self.Y = np.meshgrid(self.x_range, self.y_range)

        # ⬇️⬇️ 步骤 2: 在 __init__ 中只创建一次插值器 ⬇️⬇️
        # 提取所有有效的 (x, y, z) 点
        valid_indices = np.where(~np.isnan(self.Z))
        valid_X = self.X[valid_indices].ravel()
        valid_Y = self.Y[valid_indices].ravel()
        valid_Z = self.Z[valid_indices].ravel()
        
        # 创建插值器对象
        # 注意：如果点太少，LinearNDInterpolator 可能会失败
        if len(valid_X) > 3:
             # 使用 'list(zip(valid_X, valid_Y))' 来构建点对
            self.interpolator = LinearNDInterpolator(list(zip(valid_X, valid_Y)), valid_Z, fill_value=np.nan)
        else:
            # 作为备用方案
            self.interpolator = None
            logger.warning("MedmentExtractor 中有效数据点不足，无法创建插值器。")
        # ⬆️⬆️ 优化结束 ⬆️⬆️


    def get_z_value(self, angle, chord_length):
        """
        根据角度和弦长计算对应的Z值。
        参数:
        - angle: float，输入角度（度）
        - chord_length: float，输入弦长
        返回:
        - Z_value: float，对应的Z值
        """

        # 将角度转换为弧度
        theta = np.deg2rad(angle)

        # 计算弦的中点坐标
        x = (chord_length / 2) * np.cos(theta)
        y = (chord_length / 2) * np.sin(theta)

        # 限制坐标范围在 -6 到 6 之间
        x = np.clip(x, -6, 6)
        y = np.clip(y, -6, 6)

        # ⬇️⬇️ 步骤 3: 使用创建好的插值器进行快速计算 ⬇️⬇️
        if self.interpolator:
            z_value = self.interpolator((x, y))
            
            # 如果插值结果是 nan (例如点在凸包之外)，则尝试使用 'nearest' 填充
            if np.isnan(z_value):
                 z_value = griddata((self.X.ravel(), self.Y.ravel()), self.Z.ravel(), (x, y), method='nearest')
        else:
            # 备用方案：回退到旧的、逐个计算的 griddata (线性)
            z_value = griddata((self.X.ravel(), self.Y.ravel()), self.Z.ravel(), (x, y), method='linear')

        # ⬆️⬆️ 优化结束 ⬆️⬆️

        # 返回平K高度值
        # logger.info(f"{angle}高度值：{z_value}")
        return abs(z_value)

    def fill_missing_value(self, x, y):
        """
        [此函数在新的插值器下不再需要，但保留以防万一]
        """
        fill_range = 1  # 允许填充的周围范围（单位距离）

        # 找到最接近的索引
        x_idx = (np.abs(self.x_range - x)).argmin()
        y_idx = (np.abs(self.y_range - y)).argmin()

        # 确定填充范围
        x_min_idx = max(0, x_idx - fill_range)
        x_max_idx = min(len(self.x_range) - 1, x_idx + fill_range)
        y_min_idx = max(0, y_idx - fill_range)
        y_max_idx = min(len(self.y_range) - 1, y_idx + fill_range)

        # 提取填充区域并填充 NaN 值
        Z_fill_region = self.Z[y_min_idx:y_max_idx + 1, x_min_idx:x_max_idx + 1]
        Z_filled = pd.DataFrame(Z_fill_region).interpolate(
            method='linear', axis=0, limit_direction='both'
        ).interpolate(
            method='linear', axis=1, limit_direction='both'
        ).values

        # 将填充结果放回 Z 矩阵
        self.Z[y_min_idx:y_max_idx + 1, x_min_idx:x_max_idx + 1] = Z_filled

        # 再次尝试插值
        z_value = griddata(
            (self.X.ravel(), self.Y.ravel()),
            self.Z.ravel(),
            (x, y),
            method='linear'
        )

        return abs(z_value)


class KBQ:
    """计算平K、Q、B"""

    def __init__(self, radius: list = None, degree_list: list = None, filter_data=None):
        self.filter_data = filter_data
        self.radius = radius  # degree_list作为一个2个数据的列表,切记暂为半径
        self.degree_list = degree_list  # degree_list作为一个2个数据的列表

        # 将x_value 写成范围，即半径范围
        self.radius_list = np.arange(self.radius[0], self.radius[1] + 0.1, 0.1).tolist()
        #解决奇数计算报错问题，将0.1改为0.05
        # self.radius_list = np.arange(self.radius[0], self.radius[1] + 0.1, 0.05).tolist()
        self.rounded_radius_list = [round(num, 1) for num in self.radius_list]
        
        # ⬇️⬇️ 步骤 4: 这是我上次的修复，确保它被应用 ⬇️⬇️
        # 在循环外只创建一次 Extractor 实例
        self.extractor = MedmentExtractor(xml_file=self.filter_data)
        # ⬆️⬆️ 优化 ⬆️⬆️

    def radius_angle(self):
        """
        通过半径和平k方向高度、陡K方向高度,生成一个大list
        :param self:
        :return:
        """

        data_list = []
        for item in self.rounded_radius_list:
            data_dict = {'radius': float(item),
                         # ⬇️⬇️ 步骤 5: 使用 self.extractor ⬇️⬇️
                         'degree_list_k1': self.extractor.get_z_value(
                             self.degree_list[0],
                             float(item) * 2),
                         # ⬇️⬇️ 步骤 5: 使用 self.extractor ⬇️⬇️
                         'degree_list_k2': self.extractor.get_z_value(
                             self.degree_list[1],
                             float(item) * 2)}
            data_list.append(data_dict)

        # logger.info(data_list)
        return data_list

    @staticmethod
    def formula_numpy(_k, _x, _q, _b):
        """
        根据给定的参数计算相应的公式结果。

        参数:
        _k: 公式中的参数k
        _x: 可以是单个数值或者numpy数组，代表公式中的变量x
        _q: 公式中的参数q
        _b: 公式中的参数b

        返回:
        根据公式计算得到的结果，和输入的_x形状一致（如果_x是数组）或者是单个数值（如果_x是单个数值）
        """
        _c = _k / 337.5  # 直接一步计算出_c，避免中间变量_r的使用以及多余的除法运算
        numerator = _c * _x ** 2
        denominator = 1 + np.sqrt(1 - (1 + _q) * _c ** 2 * _x ** 2)
        return numerator / denominator + _b / 1000

    def difference_square_deviation(self, radius, degree_01, degree_02, k_type=None, pin_q_values=None,
                                    pin_b_values=None):
        """
        根据三个值，算出一个方差list; 计算陡K，将平k计算的Q和B给定，只遍历k值，寻找最佳k值
        :param radius:
        :param degree_01:
        :param degree_02:
        :param k_type: 0,平k；1,陡k
        :param pin_q_values: 平k 最佳q值
        :param pin_b_values: 陡k 最佳b值
        :return:
        """
        # 计算平均数
        average_k = np.mean([degree_01, degree_02])
        # B_values = list(np.arange(-50, 55, 5)) if k_type == 0 else pin_b_values
        B_values = [0]
        K_values = list(np.arange(35, 50.25, 0.25))
        Q_values = [0, -0.25, -0.5, -0.75, -1] if k_type == 0 else pin_q_values

        # 建立三维坐标
        B, K, Q = np.meshgrid(B_values, K_values, Q_values, indexing='ij')
        # 将三维坐标合成一个二维数组
        combined_array = np.column_stack((B.ravel(), K.ravel(), Q.ravel()))
        # 镜片高度数据, 并计算平方差
        results = self.formula_numpy(combined_array[:, 1], radius, combined_array[:, 2], combined_array[:, 0])
        # np.set_printoptions(threshold=np.inf)
        # aaa = np.array(results)
        # logger.info(f"高度数据：{aaa}")
        # print(f"average_k:{average_k}")
        squared_diff = (results - average_k) ** 2

        data = {
            "radius": radius,
            "qbk": combined_array,
            "mean_of_diff": np.mean(results - average_k),
            "squared_diff": squared_diff,
            "qbk_len": len(combined_array),
            "squared_diff_len": len(squared_diff),
            "type": k_type
        }

        return data

    def difference_square_deviation_special(self, radius, degree_01, degree_02, k_type=None, pin_q_values=None,
                                            pin_b_values=None):
        """
        根据三个值，算出一个方差list; 计算陡K，将平k计算的Q和B给定，只遍历k值，寻找最佳k值
        :param radius:
        :param degree_01:
        :param degree_02:
        :param k_type: 0,平k；1,陡k
        :param pin_q_values: 平k 最佳q值
        :param pin_b_values: 陡k 最佳b值
        :return:
        """
        # 计算平均数
        average_k = np.mean([degree_01, degree_02])
        B_values = list(np.arange(-50, 55, 5))
        K_values = list(np.arange(35, 50.25, 0.25))
        Q_values = [-0.25]

        # 建立三维坐标
        B, K, Q = np.meshgrid(B_values, K_values, Q_values, indexing='ij')
        # 将三维坐标合成一个二维数组
        combined_array = np.column_stack((B.ravel(), K.ravel(), Q.ravel()))
        # 镜片高度数据, 并计算平方差
        results = self.formula_numpy(combined_array[:, 1], radius, combined_array[:, 2], combined_array[:, 0])
        # np.set_printoptions(threshold=np.inf)
        # aaa = np.array(results)
        # logger.info(f"高度数据：{aaa}")
        squared_diff = (results - average_k) ** 2

        return {
            "radius": radius,
            "qbk": combined_array,
            "squared_diff": squared_diff,
            "qbk_len": len(combined_array),
            "squared_diff_len": len(squared_diff),
            "type": k_type
        }

    def main(self, k_type=None, pin_q_values=None, pin_b_values=None, special_type=False):
        """
        计算平K、Q、B"
        :param k_type: 0,平k；1,陡k
        :param pin_q_values: 平k 最佳q值
        :param pin_b_values: 陡k 最佳b值
        :return: 最佳数据，K,Q,B
        """
        finally_array = []
        count: int = 0
        for item in self.radius_angle():
            # 如果特殊情况下，走special方法
            if special_type:
                data = self.difference_square_deviation_special(item['radius'],
                                                                item['degree_list_k1'],
                                                                item['degree_list_k2'], k_type) \
                    if k_type == 0 else self.difference_square_deviation(item['radius'],
                                                                         item['degree_list_k1'],
                                                                         item['degree_list_k2'],
                                                                         k_type,
                                                                         pin_q_values,
                                                                         pin_b_values)
            else:
                data = self.difference_square_deviation(item['radius'],
                                                        item['degree_list_k1'],
                                                        item['degree_list_k2'], k_type) \
                    if k_type == 0 else self.difference_square_deviation(item['radius'],
                                                                         item['degree_list_k1'],
                                                                         item['degree_list_k2'],
                                                                         k_type,
                                                                         pin_q_values,
                                                                         pin_b_values)
            count = data['qbk_len']
            finally_array.append(data)

        p_diff_list = []
        for i in range(count):
            diff_list = []
            for item1 in finally_array:
                diff_list.append({"diff": item1['squared_diff'][i], "qbk": item1['qbk'][i], "radius": item1['radius']})
            diff_list = [item for item in diff_list if not np.isnan(item['diff'])]
            if len(diff_list) != 0:
                mean_variance = sum(item3['diff'] for item3 in diff_list) / len(diff_list)
                p_diff_list.append({"qbk": diff_list[0]['qbk'], "mean": mean_variance})
            else:
                pass

        try:
            means = np.array([item4["mean"] for item4 in p_diff_list])
            min_index = np.argmin(means)
            min_value = means[min_index]
        except Exception as e:
            return None

        # logger.success(f"最小值的位置是: {min_index}")
        # logger.success(f"最小值的值是: {min_value}")
        # logger.success(f"最小值的组合是: {p_diff_list[min_index]}")
        # logger.success(f"最佳K值：{p_diff_list[min_index]['qbk'][1]}")

        """
        最小方差的位置：{min_position}
        最小方差的值：{min_number}
        平方差最小的组合：{result[min_position]}
        最佳数据：combined_array[min_position]
                 平K:combined_array[min_position][1]
                 Q:combined_array[min_position][2]
                 B:combined_array[min_position][0]
        """

        best_data = {
            "minimum_variance": min_value,
            "best_data": {
                "K": p_diff_list[min_index]['qbk'][1],
                "Q": p_diff_list[min_index]['qbk'][2],
                "B": p_diff_list[min_index]['qbk'][0]
                # "B": 0
            }
        }

        return best_data


if __name__ == '__main__':
    # 使用示例
    # 1. 实例化 MedmentExtractor，并提供XML和Excel文件路径
    # print(BASE_DIR / "data" / "medment" / "test.xlsx")
    # extractor = MedmentExtractor(BASE_DIR / "data" / "medment" / "test.xlsx")
    #
    # # 3. 计算给定角度和弦长的Z值
    # _angle = 66 # 输入角度（度）
    # _chord_length = 8.2  # 输入弦长
    # Z_value = extractor.get_z_value(_angle, _chord_length)
    # print(f"角度{_angle}弦长{_chord_length}对应的Z值:", Z_value)
    #
    filter_data1 = BASE_DIR / "data" / "medment" / "test.xlsx"
    filter_data2 = BASE_DIR / "data" / "medment" / "MedmontStudio.mxf"
    result = KBQ([0, 5.3], [156, 336], filter_data=filter_data2).main(k_type=0)
    print(result)
    print(result['best_data']['K'])
    print(MedmentExtractor(excel_file=filter_data1).get_z_value(336, 3.3))