from abc import ABC, abstractmethod
from .type import Type

class BaseTypeExtractor(ABC):
    def __init__(self, db_extractor, fca_helper, config):
        self.fca_helper = fca_helper
        self.config = config
        self.db_extractor = db_extractor

    @abstractmethod
    def extract_types(self):
        pass

    def _determine_hierarchy(self, types):
        # Implement logic to determine subtype/supertype relationships
        pass
