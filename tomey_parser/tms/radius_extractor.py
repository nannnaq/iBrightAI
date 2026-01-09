from tomey_parser.tms.extractor_support import ExtractorSupport
from tomey_parser.tms.structure_extractor import StructureExtractor


class RadiusExtractor(ExtractorSupport):
    '''
    导出radius数据
    '''

    def scale(self) -> int:
        return 1000

    def tag(self) -> str:
        return StructureExtractor.BLOCK_RADIUS
