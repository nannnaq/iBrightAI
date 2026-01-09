from typing import Dict
from pathlib import Path
import traceback
from tomey_parser.domain.models import DefBlock
from tomey_parser.utils.helper import ExtractHelper
from tomey_parser.tms.structure_extractor import StructureExtractor


class StatExtractor:
    '''
    提取stat的指标数据
    '''
    # stats数据块头长度
    LENGTH_BLOCK_HEAD = 64
    # 指标值字节数
    LENGTH_VALUE = 4
    #
    dataOffsetIndex: Dict[str, int]= {
        "SimK1/ks": 0,
        "SimK2/kf": 4,
        "MinK": 8,
        "Cyl": 12,

        "SimK1/ks Ang": 16,
        "SimK2/kf Ang": 20,
        "MinK Ang.": 24,
        "SRI": 32,
        "SAI": 36
    }

    # ↓↓↓↓ 新增方法 ↓↓↓↓
    def extract_data(self, sourceFile: Path) -> Dict[str, float]:
        """
        仅提取 Stat 数据并返回字典
        """
        extractor = StructureExtractor()
        defBlockMap: Dict[str, DefBlock] = extractor.extract(sourceFile)
        
        if StructureExtractor.BLOCK_STATS not in defBlockMap:
            print(f"警告: 文件 {sourceFile} 中未找到 STATS 数据块")
            return {}

        return self.doExtractValue(sourceFile, defBlockMap[StructureExtractor.BLOCK_STATS])

    def extractAndSave(self, sourceFiles: list[Path], targetFilePath: str) -> None:
        '''
        提取stat指标数据, 并保存到指定文件
        
        :param sourceFiles: 要提取的文件列表
        :param targetFilePath: 要写入的目标文件全路径
        '''
        extractor = StructureExtractor()
        fileValues: Dict[Path, Dict[str, float]] = {}
        # 变量要提取的源文件
        for file in sourceFiles:
            # 提取数据块定义
            defBlockMap: Dict[str, DefBlock] = extractor.extract(file)
            print(f"提取Stats数据，从文件：{file.absolute()}")

            # 取stats块的偏移量及其指标
            values = self.doExtractValue(file, defBlockMap[StructureExtractor.BLOCK_STATS])
            fileValues[file] = values
        # 写入提取结果
        self.doSave(fileValues, StructureExtractor.BLOCK_STATS, targetFilePath)

    def doExtractValue(self, sourceFile: Path, defBlock: DefBlock) -> Dict[str, float]:
        ''''
        提取指定标识的指标值
        :param sourceFile: 要提取的文件
        :param defBlock: 数据块
        :return: Dict类型，每个指标的数值
        '''
        print(f"  数据块结构：{defBlock}")
        ret = {}
        # 只读打开，避免并发
        try:
            with open(sourceFile, 'rb') as raf:
                for key, value in self.dataOffsetIndex.items():
                    # 定位到指定位置： 数据块头起始位置 + 数据块头长度 + 相对于数据块数据起始位置的偏移量
                    dataBeginPosi = defBlock.offset + self.LENGTH_BLOCK_HEAD + value
                    raf.seek(dataBeginPosi)
                    # 读取指定长度的字节
                    buffer = bytearray(self.LENGTH_VALUE)
                    bytesRead = raf.readinto(buffer)
                    # 实际读取的字节数（可能小于预期，如文件末尾）
                    if (bytesRead == 0):
                        return None

                    # 处理读取到的二进制数据
                    # 注意：有符号小端
                    value: float = ExtractHelper.bytesToFloatLittleEndian(buffer)
                    ret[key] = value

                    # 打印结果，方便调试
                    print(f"  从位置 {dataBeginPosi} 读取了 {self.LENGTH_VALUE} 字节： {ExtractHelper.bytesToHex(buffer)}, {key}\t --> {value}")
        except Exception as e:
            print(f"读Stat数据异常: {str(e)}")
            traceback.print_exc()
        return ret

    def doSave(self, fileValues: Dict[Path, Dict[str, float]], blockFlag: str, targetFilePath: str) -> None:
        """
        批量保存文件指标数据到指定路径
        :param fileValues: 嵌套字典，键=Path对象，值=指标字典（键=指标名，值=浮点值）
        :param blockFlag: 块标识
        :param targetFilePath: 目标文件路径
        :return: None
        """
        # 校验空值（对应Java fileValues == null || fileValues.isEmpty()）
        if not fileValues:  # Python中空字典/None都会判定为False
            return

        # 定义格式化模板
        file_pattern = "[%s] 提取 %s 数据，从文件：%s"
        data_pattern = "    指标:%s, 值: %f"

        # 写入文件（Python with语句自动关闭文件）
        try:
            # 以UTF-8编码写入
            with open(targetFilePath, 'w', encoding='utf-8') as f:
                # 遍历外层字典
                for file_path, indicators in fileValues.items():
                    # 写入文件级标题（对应writer.write + String.format）
                    file_line = file_pattern % (ExtractHelper.formatNow(), blockFlag, file_path.absolute())
                    f.write(file_line + '\n')  # writer.newLine() 对应\n

                    # 遍历内层指标字典
                    for indicator_name, indicator_value in indicators.items():
                        data_line = data_pattern % (indicator_name, indicator_value)
                        f.write(data_line + '\n')

                    # 文件间空行分隔（对应writer.newLine()）
                    f.write('\n')
            print(f"写入文件成功：{targetFilePath}")

        # 捕获IO异常（对应Java IOException）
        except IOError as e:
            print(f"写入文件时错误：{e}")
