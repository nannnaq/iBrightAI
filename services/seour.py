import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from django.conf import settings
from loguru import logger
from scipy.interpolate import interp1d


import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eyehospital.settings")
django.setup()


BASE_DIR = settings.BASE_DIR


class SeourExtractor:
    def __init__(self, xml_file):
        # 解析XML文件
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()

        # radius_excel_path = BASE_DIR / 'data' / 'seour' / 'seour-radius.xlsx'
        # height_excel_path = BASE_DIR / 'data' / 'seour' / 'seour-height.xlsx'
        #
        # # 从Excel文件中读取 RadiusMillimeter 和 CornealHeight 数据
        # self.radius_data = pd.read_excel(radius_excel_path, header=None).values
        # self.height_data = pd.read_excel(height_excel_path, header=None).values

        # 从XML文件中读取 RadiusMillimeter 和 CornealHeight 数据
        self.radius_data = self.parser_xml_radiusMillimeter().values
        self.height_data = self.parser_xml_cornealHeight().values

    def parse_eye_data(self):
        """根据 EyeType 解析 KeratometricIndices3mm 内容（Radius和Height使用Excel数据）"""
        eye_data = {}
        for eye in self.root.findall(".//SW6000PatientTest"):
            eye_type = eye.find("EyeType").text if eye.find("EyeType") is not None else "Unknown"
            eye_data = {
                "KeratometricIndices3mm": self.parse_keratometric_indices_7mm(eye),
                # "RadiusMillimeter": self.radius_data,
                # "CornealHeight": self.height_data
            }
        return eye_data

    def parser_xml_cornealHeight(self):
        """根据xml内容提取cornealHeight"""
        corneal_height = self.root.find(".//CornealHeight")
        if corneal_height is not None:
            CornealHeight = {child.tag: child.text for child in corneal_height}
            lines = CornealHeight['Data'].replace(" ", ",").split("\n")
            df = pd.DataFrame([list(map(float, line.split(','))) for line in lines])
            return df
        return None

    def parser_xml_radiusMillimeter(self):
        """根据xml内容提取cornealHeight"""
        radius_data = self.root.find(".//RadiusMillimeter")
        if radius_data is not None:
            RadiusMillimeter = {child.tag: child.text for child in radius_data}
            lines = RadiusMillimeter['Data'].replace(" ", ",").split("\n")
            df = pd.DataFrame([list(map(float, line.split(','))) for line in lines])
            return df
        return None

    def parse_keratometric_indices_7mm(self, eye):
        """解析指定眼睛类型下的 KeratometricIndices3mm 标签内容"""
        keratometric_indices = eye.find("Data/KeratometricIndices3mm")
        if keratometric_indices is not None:
            return {
                "FlatK": keratometric_indices.find("FlatK").text if keratometric_indices.find(
                    "FlatK") is not None else None,
                "FlatAngle": keratometric_indices.find("FlatAngle").text if keratometric_indices.find(
                    "FlatAngle") is not None else None,
                "SteepK": keratometric_indices.find("SteepK").text if keratometric_indices.find(
                    "SteepK") is not None else None,
                "SteepAngle": keratometric_indices.find("SteepAngle").text if keratometric_indices.find(
                    "SteepAngle") is not None else None
            }
        return {"error": "KeratometricIndices3mm 标签未找到"}

    def find_closest_height(self, R, theta):
        """
        查找给定半径和角度下的最接近的高度值。

        参数:
        - R: float, 输入的半径
        - theta: int, 输入的角度 (0-359)

        返回:
        - height: float, 对应高度值
        """
        # 定义缺失值
        MissBH = -1.000000e+02
        MissCH = 0.000000e+00

        # 将缺失值替换为 NaN
        height_data = np.where(self.height_data == MissBH, np.nan, self.height_data)
        radius_data = np.where(self.radius_data == MissCH, np.nan, self.radius_data)

        # 检查角度范围
        if theta < 0 or theta >= 360:
            raise ValueError("角度 theta 必须在 0 到 359 的范围内")

        # 获取对应的行数据
        theta = int(theta)
        RM_row = radius_data[theta, :]
        CH_row = height_data[theta, :]

        # 移除 NaN 值
        valid_idx = ~np.isnan(RM_row) & ~np.isinf(RM_row) & ~np.isnan(CH_row) & ~np.isinf(CH_row)
        RM_row_valid = RM_row[valid_idx]
        CH_row_valid = CH_row[valid_idx]

        # 检查是否有有效数据
        if RM_row_valid.size == 0 or CH_row_valid.size == 0:
            raise ValueError("没有可用于查找的有效数据")

        interp_func = interp1d(RM_row_valid, CH_row_valid, kind='linear', bounds_error=False, fill_value=np.nan)
        # 计算插值高度
        height = interp_func(R)

        # 计算插值高度
        # 检查是否找到有效数据
        # if np.isnan(height):
        #     raise ValueError("没有找到大于输入半径且最接近的有效数据")

        return abs(height)


class KBQ:
    """计算平K、Q、B"""

    def __init__(self, radius: list = None, degree_list: list = None, filter_data=None):
        self.filter_data = filter_data
        self.radius = radius  # degree_list作为一个2个数据的列表,切记暂为半径
        self.degree_list = degree_list  # degree_list作为一个2个数据的列表

        # 将x_value 写成范围，即半径范围
        self.radius_list = np.arange(self.radius[0], self.radius[1] + 0.1, 0.1).tolist()
        self.rounded_radius_list = [round(num, 3) for num in self.radius_list]

        # ⬇️⬇️⬇️ 新增：在这里只创建一次 Extractor ⬇️⬇️⬇️
        self.extractor = SeourExtractor(xml_file=self.filter_data)

    def radius_angle(self):
        """
        通过半径和平k方向高度、陡K方向高度,生成一个大list
        :param self:
        :return:
        """

        data_list = []
        for item in self.rounded_radius_list:
            data_dict = {'radius': float(item),
                         # ⬇️⬇️⬇️ 修改：使用 self.extractor ⬇️⬇️⬇️
                         'degree_list_k1': self.extractor.find_closest_height(
                             theta=self.degree_list[0],
                             R=float(item)),
                         # ⬇️⬇️⬇️ 修改：使用 self.extractor ⬇️⬇️⬇️
                         'degree_list_k2': self.extractor.find_closest_height(
                             theta=self.degree_list[1],
                             R=float(item))}
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
    # 1. 实例化SeourExtractor，并提供XML和Excel文件路径
    path = BASE_DIR / "data" / "seour" / "01-01-OD-13-54-57.xml"
    extractor = SeourExtractor(path)

    # 2. 解析眼睛数据
    eye_data = extractor.parse_eye_data()
    print(eye_data)


    # parse_height_data = extractor.parser_xml_cornealHeight()
    # print(parse_height_data)
    # print(type(parse_height_data))
    #
    # parse_radius_data = extractor.parser_xml_radiusMillimeter()
    # print(parse_radius_data.values)
    # print(type(parse_radius_data.values))
    # print(extractor.parser_xml_radiusMillimeter())

    # 3. 示例查找最近高度
    # R = 1.0  # 输入的半径
    # theta = 4  # 输入的角度
    # height_result = extractor.find_closest_height(R, theta)
    # print("对应的高度为:", height_result)

    # 4. 计算最佳的KQB
    # filter_data1 = BASE_DIR / "data" / "medment" / "test.xlsx"
    # filter_data2 = BASE_DIR / "data" / "medment" / "MedmontStudio.mxf"
    result = KBQ([3.3, 4.6], [19, 199], filter_data=path).main(k_type=0)
    print(result)
    print(result['best_data']['K'])