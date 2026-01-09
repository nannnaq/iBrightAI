import xml.etree.ElementTree as Et

import numpy as np
import pandas as pd
import math


class OperationMXF:
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.tree = Et.parse(xml_file)
        self.root = self.tree.getroot()

    def parse_parameters(self):
        """解析FlatK, FlatAngle, SteepK, SteepAngle和cornealHeight下的所有字段"""
        params = {}

        # 解析FlatK, FlatAngle, SteepK, SteepAngle
        k_values = self.root.find(".//KeratometricIndices7mm")
        if k_values is not None:
            params['FlatK'] = k_values.find("FlatK").text if k_values.find("FlatK") is not None else None
            params['FlatAngle'] = k_values.find("FlatAngle").text if k_values.find("FlatAngle") is not None else None
            params['SteepK'] = k_values.find("SteepK").text if k_values.find("SteepK") is not None else None
            params['SteepAngle'] = k_values.find("SteepAngle").text if k_values.find("SteepAngle") is not None else None
        else:
            params['FlatK'] = float(self.root.find(".//FlatK").text) if self.root.find(".//FlatK") is not None else None
            params['FlatAngle'] = math.degrees(float(self.root.find(".//FlatAngle").text)) if self.root.find(
                ".//FlatAngle") is not None else None
            params['SteepK'] = float(self.root.find(".//SteepK").text) if self.root.find(
                ".//SteepK") is not None else None
            params['SteepAngle'] = math.degrees(float(self.root.find(".//SteepAngle").text)) if self.root.find(
                ".//SteepAngle") is not None else None

        # 解析cornealHeight下的所有字段
        corneal_height = self.root.find(".//CornealHeight")
        if corneal_height is not None:
            params['cornealHeight'] = {
                child.tag: child.text for child in corneal_height
            }
        return params

    def parse_calculated_value(self, key_data=None):
        """
        解析cornealHeight下的所有字段
        返回: numpy.ndarray
        """
        data = self.parse_parameters() if key_data is None else key_data
        data1 = data['cornealHeight']['Data'].replace(" ", ",").split("\n\t\t\t\t\t")
        blank_list = []
        for item in data1:
            _list = []
            data_list = item.split(',')
            for a in data_list:
                _list.append(a)
            blank_list.append(_list)
        result = pd.DataFrame(blank_list)
        result = result.apply(pd.to_numeric, errors='coerce')

        result = result.iloc[1:]  # 去除第一行
        result = result.iloc[:-1]  # 去除最后一行
        result = result.iloc[:, :-1]  # 去除最后一列
        # result.to_excel("aaa.xlsx", index=False)
        result = result.to_numpy()
        return result

    def parse_topographic_map_data(self):
        """解析MXF文件，地形图数据"""
        params = {}
        corneal_height = self.root.find(".//CornealHeight")
        if corneal_height is not None:
            params['cornealHeight'] = {
                child.tag: child.text for child in corneal_height
            }
        return params

    def parse_tangential_curvature_map_data(self):
        """解析MXF文件，切向曲率图"""
        params = {}
        corneal_height = self.root.find(".//TangentialCurvature")
        if corneal_height is not None:
            params['cornealHeight'] = {
                child.tag: child.text for child in corneal_height
            }
        return params

    def parse_transverse_curvature_diagram_data(self):
        """轴向曲率图"""
        params = {}
        corneal_height = self.root.find(".//AxialCurvature")
        if corneal_height is not None:
            params['cornealHeight'] = {
                child.tag: child.text for child in corneal_height
            }
        return params

    def parse_tear_film_quality_map_data(self):
        """泪膜质量图"""
        params = {}
        corneal_height = self.root.find(".//TearFilmQualityData")
        if corneal_height is not None:
            params['cornealHeight'] = {
                child.tag: child.text for child in corneal_height
            }
        return params


if __name__ == '__main__':
    print(OperationMXF(
        "/Users/makelin/Documents/ParttimeProject/Glasses_hospital/hospital-server/data/medment/MedmontStudio.mxf").parse_tear_film_quality_map_data())
    # print(OperationMXF("../media/uploads/MedmontStudio.mxf").parse_calculated_value())
