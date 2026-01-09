from abc import abstractmethod
import traceback
from pathlib import Path
from typing import List, Dict
from tomey_parser.domain.models import DefBlock
from tomey_parser.utils.helper import ExtractHelper
from tomey_parser.tms.structure_extractor import StructureExtractor


class ExtractorSupport:
    # ↓↓↓↓ 新增方法 ↓↓↓↓
    def extract_to_csv_string(self, sourceFile: Path) -> str:
        """
        提取数据并返回 CSV 格式的字符串 (不保存文件)
        """
        ret: List[List[str]] = self.doExtract(sourceFile)
        if not ret:
            return ""
            
        csv_lines = []
        row_size = self.getRowSize() # 256
        column_size = len(ret)       # 34
        
        # 转置矩阵：按行拼接
        for row_index in range(row_size):
            row_values = []
            for col_index in range(column_size):
                col_list = ret[col_index]
                value = col_list[row_index]
                row_values.append(value)
            csv_lines.append(",".join(row_values))
            
        return "\n".join(csv_lines)

    def extractAndSave(self, sourceFile: Path, targetFilePath: str) -> None:
        '''
        提取数据并保存到指定文件
        :param sourceFile: 被读取的原数据文件
        :param targetFilePath: 要保存的文件
        :return: None
        '''
        ret: List[List[str]] = self.doExtract(sourceFile)
        self.saveFile(targetFilePath, ret)

    def doExtract(self, sourceFile: Path) -> List[List[str]]:
        '''
        提取数据
        :param sourceFile: 被读取的原数据文件
        :return: 提取的数据
        :rtype: List[List[str]]
        '''
        datas = self.getRowSize()
        ret: List[List[str]] = []

        values: List[str] = None

        try:
            # 提取数据块定义
            extractor = StructureExtractor()
            defBlockMap: Dict[str, DefBlock] = extractor.extract(sourceFile)
            print(f"提取 {self.tag()} 数据，从文件：{sourceFile.absolute()}")
            # 得到数据块
            defBlock: DefBlock = defBlockMap[self.tag()]
            # 读取的起始位置
            position: int = defBlock.offset + 64

            # 只读模式打开文件
            with open(sourceFile, 'rb') as raf:
                # 关键步骤：定位到指定位置（数据起始位置偏移量）
                raf.seek(position)
                for c in range(self.getColumSize()):
                    values: List[str] = []
                    for j in range(datas):
                        # 读取指定长度的字节
                        buffer = raf.read(self.getDataLength())
                        bytes_read = len(buffer)

                        # 读取到文件末尾（实际字节数不足）
                        if bytes_read < self.getDataLength():
                            return None

                        # 打印调试信息
                        # print(f"列 {c}-{j} 从位置 {position} 读取了 {bytes_read} 字节：", end='')
                        position += self.getDataLength()

                        # 解析小端有符号整数（核心逻辑）
                        value = ExtractHelper.toSignedInt(buffer, 'little')
                        # 格式化数值
                        v = ExtractHelper.formatNumber(value, self.scale())

                        # 打印十六进制和解析结果
                        hex_str = ' '.join([f"{b:02X}" for b in buffer[:2]])
                        # print(f" {hex_str} --> {value} 格式化-> {v}")

                        values.append(v)
                    ret.append(values)
        except Exception as e:
            print(f"读文件数据块异常: {str(e)}")
            traceback.print_exc()
            return None
        return ret

    def saveFile(self, targetFilePath: str, ret: List[List[str]]) -> None:
        '''
        保存解析数据到文件(将二维列表写入文件)
        :param targetFilePath: 保存的文件名
        :param ret: 二维列表[列[行]]，格式为 [[列0行0, 列0行1...], [列1行0, 列1行1...]]
        '''
        column_size = len(ret)
        row_size = self.getRowSize()

        # 使用with上下文管理器自动关闭文件
        try:
            with open(targetFilePath, 'w', encoding='utf-8', newline='\r\n') as f:
                # 遍历每一行
                for row_index in range(row_size):
                    # 遍历每一列
                    for col_index in range(column_size):
                        # 按列取数据 → 列列表的第row_index个元素
                        col_list = ret[col_index]
                        value = col_list[row_index]
                        # 写入当前值
                        f.write(value)
                        # 最后一列：换行；否则：写逗号分隔符
                        if col_index == self.getColumSize() - 1:
                            f.write('\n')
                        else:
                            f.write(',')
            print(f"写入文件成功：{targetFilePath}\n")
        except IOError as e:
            # 捕获IO异常（对应Java的IOException）
            print(f"写入文件时错误：{e}\n")

    @abstractmethod
    def scale(self) -> int:
        """ 数据处理的精度 """
        pass

    @abstractmethod
    def tag(self) -> str:
        """ 数据标识 """
        pass

    def getColumSize(self) -> int:
        """ 获取列数 """
        return 34

    def getRowSize(self) -> int:
        ''' 获取行数 '''
        return 256

    def getDataLength(self) -> int:
        """获取每个数据的字节长度"""
        return 2
