from dataclasses import dataclass


@dataclass
class DefBlock:
    ''' 数据块定义 '''
    code: int  # 数据代码
    flag: str  # 数据标识
    length: int  # 数据块长度-字节数
    offset: int  # 当前数据块偏移量
    offsetNext: int  # 下一个数据块偏移量
    offsetPrevious: int  # 前一个数据块偏移量
    remark: str

    def __init__(self, flag: str, offset: int, length: int, offsetNext: int,
                 offsetPrevious: int):
        self.flag = flag
        self.offset = offset
        self.length = length
        self.offsetNext = offsetNext
        self.offsetPrevious = offsetPrevious
        self.code = 0
        self.remark = ""

    @classmethod
    def newDefault(cls):
        return cls(None, -1, 0, -1, -1)

    @classmethod
    def newOf(cls, flag: str, offset: int, length: int):
        return cls(flag, offset, length, -1, -1)

    def __repr__(self) -> str:
        return f"标识:{self.flag}, 代码:{self.code}, 当前块偏移量:{self.offset}, 下一个数据块偏移量:{self.offsetNext}, 前一个数据块偏移量: {self.offsetPrevious}, 长度: {self.length}, 描述: {self.remark}"
