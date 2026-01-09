import struct
import time
from datetime import datetime


class ExtractHelper:
    '''
    数值、日期时间的格式转换辅助类
    '''

    @staticmethod
    def formatNow() -> str:
        """
        格式化当前系统时间为 "yyyy-MM-dd HH:mm:ss" 字符串
        :return: 格式化后的时间字符串
        """
        # 获取当前本地时间 → 对应Java的new Date()
        now = datetime.now()
        # 按指定格式格式化
        # %Y=4位年, %m=2位月, %d=2位日, %H=24小时制时, %M=分, %S=秒
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_time

    @staticmethod
    def nanoTime() -> int:
        return time.time_ns()

    @staticmethod
    def bytesToIntLittleEndian(bytes_data: bytes | bytearray) -> int:
        """
        小端序4字节数组转无符号64位长整型
        :param bytes_data: 4字节数组
        :return: 无符号长整型（Python int 天然支持大整数，等效 Java long）
        :raises ValueError: 字节数组长度非4时抛出
        """
        if len(bytes_data) != 4:
            raise ValueError("必须传入4字节数组")
        # <I：小端序（<）+ 无符号32位整数（I），Python自动转为int（等效Java long）
        return struct.unpack('<I', bytes_data)[0]
    
    @staticmethod
    def toSignedInt(bytes_data: bytes | bytearray, byte_order: str) -> int:
        """
        2字节转有符号整数（考虑字节序） 范围：-32768 ~ 32767（16位有符号整数范围）
        :param bytes_data: 输入的字节数组（bytes/bytearray），必须长度为2
        :param byte_order: 字节序，可选 'big'（大端）/'little'（小端），对应 Java ByteOrder
        :return: 有符号32位整数（等效 Java short 自动提升为 int）
        :raises ValueError: 字节数组长度不是2时抛出
        """
        # 1. 校验字节数组长度（等效 Java if (bytes.length != 2) 抛异常）
        if len(bytes_data) != 2:
            raise ValueError("必须传入2字节数组")

        # 2. 处理字节序，解析为有符号16位整数（等效 ByteBuffer.getShort()）
        # struct 格式说明：
        # > = 大端（BigEndian），< = 小端（LittleEndian），h = 有符号16位短整型（short）
        fmt = '>h' if byte_order == 'big' else '<h'
        # 解析字节为short（16位），Python会自动转为int（32位），等效Java的自动类型提升
        signed_short = struct.unpack(fmt, bytes_data)[0]
        return signed_short

    @staticmethod
    def bytesToHex(bytes_data: bytes) -> str:
        """
        将4字节的字节数组转换为小写十六进制字符串（对齐Java的bytesToHex逻辑）
        :param bytes_data: 待转换的字节数组（bytes类型）
        :return: 小写十六进制字符串（8位，如 b'\x12\x34\x56\x78' → "12345678"）
        :raises ValueError: 若字节数组长度不是4
        """
        # 校验字节数组长度（对应Java的IllegalArgumentException）
        if len(bytes_data) != 4:
            raise ValueError("字节数组必须是4个字节")

        # 遍历字节，转换为两位小写十六进制（对齐String.format("%02x", b)）
        hex_str = ''.join(f"{byte:02x}" for byte in bytes_data)
        return hex_str

    @staticmethod
    def bytesToFloatLittleEndian(bytes_data: bytes) -> float:
        """
        将4字节的字节数组按小端序（Little Endian）转换为float类型（32位单精度浮点）
        :param bytes_data: 待转换的字节数组（bytes类型）
        :return: 32位单精度浮点数
        :raises ValueError: 若字节数组长度不是4
        """
        # 校验字节数组长度（对应Java的IllegalArgumentException）
        if len(bytes_data) != 4:
            raise ValueError("字节数组必须是4个字节")

        # 按小端序解析4字节为32位单精度浮点数（对应Java ByteBuffer.getFloat()）
        # struct.unpack 返回元组，[0] 取第一个元素（唯一值）
        # '<f' 含义：< = 小端序，f = 32位单精度浮点数（对应Java float）
        float_value = struct.unpack('<f', bytes_data)[0]
        return float_value

    def formatNumber(number: int, scale: float) -> str:
        """
        按精度转小数，保留4位小数（不足补零），总长度9位
        :param number: 输入的整数
        :param scale: 精度（除数，对应Java的float类型）
        :return: 格式化后的字符串（总长度9位，含小数点/符号）
        """
        # 核心逻辑：整数 / 精度值 = 小数
        value = number / scale
        # 格式化规则：%9.4f
        # 9 = 总长度（含符号、小数点、数字），4 = 小数位（不足补零，超过则四舍五入）
        return f"{value:9.4f}"
