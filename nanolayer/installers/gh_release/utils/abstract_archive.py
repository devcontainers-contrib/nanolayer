from abc import ABC, abstractmethod
from typing import List


class AbstractExtendedArchive(ABC):
    @abstractmethod
    def get_member_permissions(self, member_name: str) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_names_by_prefix(self, prefix: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_names_by_suffix(self, suffix: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def names_by_filename(self, filename: str) -> List[str]:
        raise NotImplementedError()

    @abstractmethod
    def get_file_members(self) -> List[str]:
        raise NotImplementedError()
