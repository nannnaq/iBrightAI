import os
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, splev, splrep
import xml.etree.ElementTree as ET
from loguru import logger

from django.conf import settings
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eyehospital.settings")
django.setup()


BASE_DIR = settings.BASE_DIR

# logger.info(f'BASE_DIR: {BASE_DIR}/loguru.log')
logger.add(f'{BASE_DIR}/loguru.log', rotation="100 MB")


class TomeyExtractor:
    def __init__(self, rm_dat_path, ch_dat_path):
        # # 从Excel文件读取数据
        # self.RM_data = pd.read_excel(rm_excel_path).values
        # # print(self.RM_data)
        # self.CH_data = pd.read_excel(ch_excel_path).values

        # 从.dat中读取数据
        self.RM_data = self.parse_dat(rm_dat_path).values
        self.CH_data = self.parse_dat(ch_dat_path).values

        # 将无效的特殊值替换为NaN（参照 Medmont 的处理方式）
        # 注意：角膜高度数据可能包含负值和零值，这些是有效数据，不应替换
        # 只替换明显无效的极端值（如 -5e+20 或设备标记的无效值）
        INVALID_VALUE_THRESHOLD = -1e+10  # 小于此值认为是无效数据
        self.RM_data[self.RM_data < INVALID_VALUE_THRESHOLD] = np.nan
        self.CH_data[self.CH_data < INVALID_VALUE_THRESHOLD] = np.nan

        # 对于 Radius 数据，曲率半径应该是正数，0或负数是无效的
        self.RM_data[self.RM_data <= 0] = np.nan

        # 转置数据
        self.RM_data = self.RM_data.T
        self.CH_data = self.CH_data.T

        #--------------------9-8新加------------------
        # self.CH_data = np.hstack((self.CH_data, self.CH_data[:, [0]]))
        # self.RM_data = np.hstack((self.RM_data, self.RM_data[:, [0]]))

        # # 计算每列对应的角度和索引
        # # self.angle_step = 360 / self.CH_data.shape[1]  # 每列对应的角度步长
        # self.angle_step = 360 / (self.CH_data.shape[1] - 1)  # 每列对应的角度步长
        try:
            self.CH_data = np.hstack((self.CH_data, self.CH_data[:, [0]]))
            self.RM_data = np.hstack((self.RM_data, self.RM_data[:, [0]]))
            self.angle_step = 360 / (self.CH_data.shape[1] - 1)
        except ZeroDivisionError:
            print("警告：计算角度步长时发生除零错误...")
            self.angle_step = 0
        except Exception as e:
            print(f"错误：在数据后处理步骤中发生错误: {e}")
            self.angle_step = 0 # 确保即使出错也有默认值
        self.angle_columns = np.arange(0, self.CH_data.shape[1]) * self.angle_step  # 角度数组

    def parse_dat(self, file_path):
        """
        解析 .dat 文件，获取数据并返回 DataFrame。
        参数:
        - file_path: str，.dat 文件的路径
        返回:
        - df: pandas.DataFrame，包含解析后的数据
        """
        # 读取 .dat 文件
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 解析数据
        try:
            data = []
            for line in lines:
                # 移除首尾空白并用逗号分割
                cleaned_line = line.strip().replace(' ', '')  # 移除所有空格
                if not cleaned_line:  # 跳过空行
                    continue

                try:
                    # 分割字符串并转换为浮点数
                    row_data = [float(x) for x in cleaned_line.split(',')]
                    data.append(row_data)
                except ValueError as e:
                    logger.warning(f"无法解析行: {line.strip()}，错误: {e}")
                    continue

            # 创建 DataFrame（34列对应数据格式）
            df = pd.DataFrame(data)
        except Exception as e:
            logger.error(f"解析文件时发生错误: {e}")
            raise ValueError(f"文件格式错误")
        return df

    def get_height(self, R, theta):
        """
        根据给定的半径 R 和角度 theta 计算对应的高度值。

        参数:
        - R: float，输入的半径
        - theta: float，输入的角度（0-359）

        返回:
        - height: float，对应的高度值，如果角度或半径无效则返回NaN
        """
        # 检查角度范围
        if theta >= 360:
            theta = theta - 180
        if theta < 0 or theta >= 360:
            raise ValueError(f"请保证平角度/斜角度计算时增加180后依然在 0 到 359 的范围内")

        # 计算每列对应的角度
        # angle_step = 360 / self.CH_data.shape[1]
        # self.angle_step = 360 / (self.CH_data.shape[1] - 1)  # 每列对应的角度步长
        try:
            # 尝试计算角度步长。
            # 减1是正确的，因为N个数据点之间存在N-1个间隔。
            angle_step = 360 / (self.CH_data.shape[1] - 1)

        except ZeroDivisionError:
            # 特别捕获“除以零”的错误。
            # 这种情况最可能发生在 self.CH_data 数组恰好只有一列时，
            # 此时分母 (1 - 1) 会变成 0。
            print("警告：计算角度步长时发生除零错误。输入数据可能只有一列，无法计算步长。")
            angle_step = 0  # 设置一个安全的默认值，防止程序后续崩溃

        except Exception as e:
            # 这是一个“兜底”的保护，用于捕获所有其他意想不到的错误，
            # 例如 self.CH_data 对象不存在，或者不是一个有效的数组等。
            print(f"错误：在计算角度步长时失败。异常: {e}")
            angle_step = 0  # 同样设置一个安全的默认值

        angle_columns = np.arange(0, self.CH_data.shape[1]) * angle_step

        if theta < np.min(angle_columns) or theta > np.max(angle_columns):
            raise ValueError(f'角度 {theta}° 超出已有数据的角度范围')

        # 找到最接近theta的角度索引
        nearest_index = (np.abs(angle_columns - theta)).argmin()
        # 提取 RM_row 和 CH_row
        RM_row = self.RM_data[:, nearest_index]
        CH_row = self.CH_data[:, nearest_index]
        # 移除 NaN 值
        valid_idx = ~np.isnan(RM_row) & ~np.isnan(CH_row)
        RM_row = RM_row[valid_idx]
        CH_row = CH_row[valid_idx]

        height = np.nan
        # 如果最接近的角度不是精确匹配，则使用spline插值方法
        if angle_columns[nearest_index] != theta:
            # logger.debug('警告: 使用双线性插值方法来查找对应列')
            # 在角度方向上进行插值
            RM_interp_angle = np.zeros(self.RM_data.shape[0])
            CH_interp_angle = np.zeros(self.CH_data.shape[0])

            for i in range(self.RM_data.shape[0]):
                # 获取当前半径对应的 RM 和 CH 数据
                RM_temp = self.RM_data[i, :]
                CH_temp = self.CH_data[i, :]

                # 移除 NaN 值
                valid_idx = ~np.isnan(RM_temp) & ~np.isnan(CH_temp)
                RM_temp = RM_temp[valid_idx]
                CH_temp = CH_temp[valid_idx]
                angle_temp = angle_columns[valid_idx]

                # 插值
                if len(RM_temp) > 0 and len(CH_temp) > 0:
                    RM_interp_angle[i] = interp1d(angle_temp, RM_temp, kind='linear', bounds_error=False,
                                                  fill_value=np.nan)(theta)
                    CH_interp_angle[i] = interp1d(angle_temp, CH_temp, kind='linear', bounds_error=False,
                                                  fill_value=np.nan)(theta)
                else:
                    RM_interp_angle[i] = np.nan
                    CH_interp_angle[i] = np.nan

                # 移除插值结果中的 NaN 值
            valid_idx = ~np.isnan(RM_interp_angle) & ~np.isnan(CH_interp_angle)
            RM_interp_angle = RM_interp_angle[valid_idx]
            CH_interp_angle = CH_interp_angle[valid_idx]

            # 在半径方向上进行插值
            if len(RM_interp_angle) > 0 and len(CH_interp_angle) > 0:
                if R < np.min(RM_interp_angle) or R > np.max(RM_interp_angle):
                    # logger.info(f'{R:.1f}   | 超出范围')
                    pass
                else:
                    height = interp1d(RM_interp_angle, CH_interp_angle, kind='linear', bounds_error=False,
                                      fill_value=np.nan)(R)
                    # logger.info(f'{R:.1f}   | {height:.4f}')
            else:
                raise ValueError('所请求的角度没有有效数据')
        else:
            if len(RM_row) > 0 and len(CH_row) > 0:
                if R < np.min(RM_row) or R > np.max(RM_row):
                    # logger.info(f'{R:.1f}   | 超出范围')
                    pass
                else:
                    height = interp1d(RM_row, CH_row, kind='linear', bounds_error=False, fill_value=np.nan)(R)
                    # logger.info(f'{R:.1f}   | {height:.4f}')
            else:
                raise ValueError('所请求的角度没有有效数据')

        return abs(height)


class KBQ:
    """计算平K、Q、B"""

    def __init__(self, radius: list = None, degree_list: list = None, rm_dat_path=None, ch_dat_path=None):
        self.rm_dat_path = rm_dat_path
        self.ch_dat_path = ch_dat_path

        self.radius = radius  # degree_list作为一个2个数据的列表,切记暂为半径
        self.degree_list = degree_list  # degree_list作为一个2个数据的列表

        # 将x_value 写成范围，即半径范围
        self.radius_list = np.arange(self.radius[0], self.radius[1] + 0.1, 0.1).tolist()
        self.rounded_radius_list = [round(num, 1) for num in self.radius_list]

    def radius_angle(self):
        """
        通过半径和平k方向高度、陡K方向高度,生成一个大list
        :param self:
        :return:
        """

        data_list = []
        for item in self.rounded_radius_list:
            data_dict = {'radius': float(item),
                         'degree_list_k1': TomeyExtractor(rm_dat_path=self.rm_dat_path, ch_dat_path=self.ch_dat_path).get_height(
                             theta=self.degree_list[0],
                             R=float(item)),
                         'degree_list_k2': TomeyExtractor(rm_dat_path=self.rm_dat_path, ch_dat_path=self.ch_dat_path).get_height(
                             theta=self.degree_list[1],
                             R=float(item))}
            data_list.append(data_dict)

        logger.info(data_list)
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
        squared_diff = (results - average_k) ** 2

        return {
            "radius": radius,
            "qbk": combined_array,
            "squared_diff": squared_diff,
            "qbk_len": len(combined_array),
            "squared_diff_len": len(squared_diff),
            "type": k_type
        }

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
        # B_values = list(np.arange(-50, 55, 5))
        B_values = [0]
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
    # 1. 实例化 TomeyExtractor，并提供 RM 和 CH 的 dat 文件路径
    rm_path = BASE_DIR / "data" / "Tomey" / "RAD_1_3301.dat"
    ch_path = BASE_DIR / "data" / "Tomey" / "HIT_1_3301.dat"
    extractor = TomeyExtractor(rm_path, ch_path)

    # # 2. 根据半径和角度计算高度
    # _R = 3.0  # 输入半径
    # _theta = 200  # 输入角度
    # height_data = extractor.get_height(_R, _theta)
    # logger.info(f"半径{_R},角度{_theta},对应的高度为:{height_data}")

    # 3. 计算K、Q、B
    result = KBQ([0, 6], [156, 336], rm_dat_path=rm_path, ch_dat_path=ch_path).main(k_type=0)
    logger.info(result)
    logger.info(f"最优K值:{result['best_data']['K']}")
