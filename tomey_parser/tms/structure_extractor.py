import os
from typing import Dict, List, IO, Optional
from pathlib import Path
import traceback
from tomey_parser.domain.models import DefBlock
from tomey_parser.utils.helper import ExtractHelper


class StructureExtractor:
    '''
    提取radius、height、stat等数据块头的数据
    '''
    BLOCK_HEAD = "HEAD"
    BLOCK_RADIUS = "RAD"
    BLOCK_HEIGHT = "HIT"
    BLOCK_STATS = "STA"
    BLOCK_VIDEO = "BMP"
    FLAG_UNKNOWN = "UNKNOWN"

    # 要提取的数据块标识及其特征，对应radius、height、stat、bmp的数据
    blcokSpecifics = {
        BLOCK_RADIUS: "Radi",
        BLOCK_HEIGHT: "Height",
        BLOCK_STATS: "Stat",
        BLOCK_VIDEO: "Video   "  # 注意：Video后面的空格不要去掉
    }

    # 文件头块定义
    header = DefBlock.newOf("HEAD", 0, 128)

    def extract(self, sourceFile: Path) -> Dict[str, DefBlock]:
        '''
        提取数据块定义
        :param: sourceFile: 被读取的原数据文件
        :return: 数据块，键=数据标识，值=数据块
        :rtype: Dict[str, DefBlock]
        '''
        blocks = self.doExtract(sourceFile)
        fileBlocks = {}
        for block in blocks:
            # 键=block.flag，值=block对象
            fileBlocks[block.flag] = block
        return fileBlocks

    def extractAndSave(self, sourceFiles: list[Path] = [], targetFilePath: str = "") -> None:
        '''
        批量提取数据块并保存到指定文件
        :param sourceFiles: 被读取的原数据文件
        :param targetFilePath: 要保存的文件
        :return: None
        '''
        fileBlocks = {}
        for file in sourceFiles:
            blocks = self.doExtract(file)
            fileBlocks[file] = blocks
        self.doSave(fileBlocks, targetFilePath)


    def doExtract(self, sourceFile: Path) -> List:
        '''
        执行提取数据块，并返回每个块的数据
        :param: sourceFile: 被读取的原数据文件
        :return: 块列表，List[DefBlock]
        '''
        print(f"获取数据块，从文件: {sourceFile.absolute()}")
        blocks = []
        # 跳过文件头
        offset = self.header.length if self.header else 0
        # 只读打开
        try:
            with open(sourceFile, 'rb') as raf:
                while len(blocks) != len(self.blcokSpecifics):
                    # 数据块头
                    blockHead = self.extractBlockHead(raf, offset)
                    # print(f"\t\tblockHead: {blockHead}")
                    # 判断数据标识
                    blockHead.flag = self.judgeFlag(blockHead, sourceFile)
                    if not blockHead.flag.casefold() == self.FLAG_UNKNOWN.casefold():
                        blocks.append(blockHead)
                        print(f"\t{blockHead}")
                    offset += blockHead.length
        except Exception as e:
            print(f"读文件数据块异常: {str(e)}")
            traceback.print_exc()
        return blocks

    def extractBlockHead(self, raf: IO[bytes], currentBlockOffset: int) -> DefBlock:
        '''
        提取数据块头
        :param: raf 文件流
        :param: currentBlockOffset 当前数据块偏移量
        :return: DefBlock，数据块
        '''
        # 关键步骤：定位到指定位置（数据起始位置偏移量）
        beginPosi = currentBlockOffset
        raf.seek(beginPosi)

        block = DefBlock.newDefault()
        # 代码 2字节
        block.code = self.read2(raf)
        # 下一个
        block.offsetNext = self.read4(raf)
        # 前一个
        block.offsetPrevious = self.read4(raf)
        # 当前
        block.offset = self.read4(raf)
        # 长度
        block.length = block.offsetNext - block.offset
        # 描述
        block.remark = self.readRemark(raf)
        return block

    def read2(self, raf: IO[bytes],) -> int:
        ''''
        读2个字节，并转成整型。
        raf 文件流
        '''
        # 取下一个数据块偏移量
        buffer = bytearray(2)
        bytesRead = raf.readinto(buffer)
        # 实际读取的字节数（可能小于预期，如文件末尾）
        if (bytesRead == 0):
            return -1
        # 小端序字节数组转int（2字节）
        return ExtractHelper.toSignedInt(buffer, "little")

    def read4(self, raf) -> int:
        """
        从二进制文件对象读取4字节，小端序转长整型
        :param raf: 二进制文件对象
        :return: 解析后的长整型，文件末尾返回 -1
        :raises IOError: 文件读取异常
        """
        # 1. 初始化4字节缓冲区（等效 Java byte[] buffer = new byte[4]）
        buffer = bytearray(4)

        # 2. 读取数据到缓冲区并获取实际读取字节数
        try:
            bytes_read = raf.readinto(buffer)
        except IOError as e:
            raise IOError(f"文件读取失败: {e}")

        # 3. 判断文件末尾（Java 返回 -1，Python readinto 返回 0）
        if bytes_read == 0:
            return -1

        # 4. 小端序4字节转长整型
        # 注意：若实际读取字节数<4，仅取有效部分并补0（保持4字节长度）
        if bytes_read < 4:
            buffer = buffer[:bytes_read] + b'\x00' * (4 - bytes_read)
        return ExtractHelper.bytesToIntLittleEndian(buffer)

    def readRemark(self, raf) -> str | None:
        """
        从二进制文件对象读取16字节并解码为UTF-8字符串
        :param raf: 二进制文件对象
        :return: 解码后的UTF-8字符串，文件末尾返回 None
        :raises IOError: 文件读取/指针操作异常
        """
        try:
            # 1. 移动文件指针：当前位置 + 1字节
            current_pos = raf.tell()  # 获取当前指针位置
            raf.seek(current_pos + 1)  # 指针偏移1字节

            # 2. 初始化16字节缓冲区
            buffer = bytearray(16)

            # 3. 读取数据到缓冲区并获取实际读取字节数
            bytes_read = raf.readinto(buffer)

            # 4. 判断文件末尾
            if bytes_read == 0:
                return None

            # 5. 截取实际读取的字节（避免缓冲区残留空字节）+ UTF-8解码
            # 仅处理实际读取的字节，剔除未读取的空字节，避免解码出多余的 \x00
            valid_bytes = buffer[:bytes_read]
            # 解码为UTF-8字符串，忽略无效字节（兼容文件末尾不完整的UTF-8编码）
            remark = valid_bytes.decode("UTF-8", errors="ignore")
            return remark
        except IOError as e:
            raise IOError(f"读取备注失败: {e}")

    def judgeFlag(self, defBlock: DefBlock, sourceFile: Path) -> str:
        '''
        判断当前数据块的标识, 用于区分radius、height、stat、vedio等数据块。
        图片块特征: 数据代码6; 是最后一个数据块，其下一个数据块偏移量和文件长度一样;
        radius、height、stat、vedio特征: 数据代码各不同; 备注也各自不同。
        这里按照备注区分;
        :param defBlock: 数据块
        :return: 数据标识
        '''
        if defBlock is None:
            return None
        remark = defBlock.remark
        if (remark is None):
            return None
        flag = None
        for key, value in self.blcokSpecifics.items():
            if (value in remark):
                flag = key
                break
        return self.FLAG_UNKNOWN if flag is None else flag

    def doSave(self, file_blocks: Optional[Dict[Path, List[DefBlock]]], targetFilePath: str) -> None:
        """
        将文件-块映射关系写入指定文件
        :param: file_blocks: 键为文件路径（os.PathLike，等效 Java File），值为 DefBlock 列表；None/空时直接返回
        :param: targetFilePath: 目标写入文件路径
        :return: None
        """
        # 1. 空值/空集合判断
        if file_blocks is None or not file_blocks:
            return

        # 2. 定义格式化模板
        file_pattern = "提取文件结构，从文件：%s"
        data_pattern = "    标识:%s, 代码: %d, 当前块偏移量: %d, 下一个数据块偏移量: %d, 前一个数据块偏移量: %d, 长度: %d"

        try:
            # 3. 打开文件并写入
            # encoding='utf-8' 显式指定编码，避免系统默认编码问题
            with open(targetFilePath, mode='w', encoding='utf-8', newline='') as writer:
                # 4. 遍历文件-块映射（等效 Java 遍历 Map.entrySet()）
                for file_path, blocks in file_blocks.items():
                    # 写入文件路径行（等效 entry.getKey().getAbsolutePath()）
                    abs_file_path = os.path.abspath(file_path)
                    writer.write(file_pattern % abs_file_path)
                    writer.write('\n')  # 等效 writer.newLine()

                    # 遍历每个 DefBlock 写入详情
                    for block in blocks:
                        # 格式化行内容（
                        text = data_pattern % (
                            block.flag,
                            block.code,
                            block.offset,
                            block.offsetNext,
                            block.offsetPrevious,
                            block.length
                        )
                        writer.write(text)
                        writer.write('\n')
                    # 文件块遍历完后换行（分隔不同文件）
                    writer.write('\n')
            print(f"写入文件成功：{targetFilePath}")
        except IOError as e:
            # 捕获 IO 异常
            print(f"写入文件时错误：{e}")
