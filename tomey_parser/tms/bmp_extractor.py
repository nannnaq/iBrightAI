from typing import Dict
from pathlib import Path
from tomey_parser.domain.models import DefBlock
from tomey_parser.utils.helper import ExtractHelper
from tomey_parser.tms.structure_extractor import StructureExtractor


class BmpExtractor:
    '''
    提取bmp图片
    '''
    def extractAndSave(self, sourceFile: Path, targetFilePath: str) -> None:
        '''
        提取bmp图片, 并保存到指定文件中
        :param sourceFile: 要提取的文件
        :param targetFilePath: 要写入的目标文件全路径
        '''
        extractor = StructureExtractor()

        # 提取数据块定义
        defBlockMap: Dict[str, DefBlock] = extractor.extract(sourceFile)
        print(f"提取BMP图片, 从文件: {sourceFile.absolute()}")
        # 得到图片的数据块
        defBlock: DefBlock = defBlockMap[StructureExtractor.BLOCK_VIDEO]

        # 提取图片
        self.doExtract(sourceFile, targetFilePath, defBlock)
    
    def doExtract(self, sourceFile: Path, targetFilePath: str, defBlock: DefBlock) -> Dict[str, float]:
        try:
            with open(sourceFile, 'rb') as raf, open(targetFilePath, 'wb') as fos:
                # 1. 移动到BMP数据起始偏移量
                position: int = defBlock.offset + 64
                raf.seek(position)

                # 2. 跳过前2字节魔数（"BM"），读取4字节文件大小（小端序）
                raf.read(2)
                file_size_bytes = raf.read(4)  # 读取bfSize字段（4字节）
                if len(file_size_bytes) != 4:
                    raise IOError("读取BMP文件头失败, 无法获取文件大小")
            
                bmp_total_size = ExtractHelper.bytesToIntLittleEndian(file_size_bytes)
                print(f"BMP文件总大小(字节): {bmp_total_size}")

                # 3. 回退到BMP起始位置（对应raf.seek(bmpOffset)）
                raf.seek(position)

                # 4. 读取完整的BMP数据
                bmp_data = raf.read(bmp_total_size)
                bytes_read = len(bmp_data)
                if bytes_read != bmp_total_size:
                    raise IOError(f"读取BMP数据不完整, 预期{bmp_total_size}字节，实际读取{bytes_read}字节")

                # 5. 写入提取的BMP文件
                fos.write(bmp_data)

                # 打印读取后偏移量
                print(f"读取后偏移量: {raf.tell()}")
                print(f"BMP图片提取成功, 保存路径：{targetFilePath}\n")

        except IOError as e:
            # 抛出IO异常
            raise IOError(f"提取BMP失败: {e}") from e
