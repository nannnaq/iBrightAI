from tomey_parser.tms.extractor_support import ExtractorSupport
from tomey_parser.tms.structure_extractor import StructureExtractor


class HeightExtractor(ExtractorSupport):
    '''
    导出height数据
    '''

    def scale(self) -> int:
        return 10000

    def tag(self) -> str:
        return StructureExtractor.BLOCK_HEIGHT
