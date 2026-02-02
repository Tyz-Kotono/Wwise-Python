# naming.py
import re
from typing import List, Protocol


# -----------------------------
# Rule 接口（策略模式）
# -----------------------------
class NamingRule(Protocol):
    def apply(self, name: str) -> str:
        ...


# -----------------------------
# 具体规则实现
# -----------------------------
class RegexReplaceRule:
    def __init__(self, pattern: str, replacement: str):
        self.pattern = pattern
        self.replacement = replacement

    def apply(self, name: str) -> str:
        return re.sub(self.pattern, self.replacement, name)


class PrefixRule:
    def __init__(self, prefix: str, skip_if_exists: bool = True):
        self.prefix = prefix
        self.skip_if_exists = skip_if_exists

    def apply(self, name: str) -> str:
        if self.skip_if_exists and name.startswith(self.prefix):
            return name
        return f"{self.prefix}{name}"


class SuffixRule:
    def __init__(self, suffix: str, skip_if_exists: bool = True):
        self.suffix = suffix
        self.skip_if_exists = skip_if_exists

    def apply(self, name: str) -> str:
        if self.skip_if_exists and name.endswith(self.suffix):
            return name
        return f"{name}{self.suffix}"


class IndexRule:
    """
    自动编号：_01 / _02
    """
    def __init__(self, index: int, width: int = 2, prefix: str = "_"):
        self.index = index
        self.width = width
        self.prefix = prefix

    def apply(self, name: str) -> str:
        number = str(self.index).zfill(self.width)
        return f"{name}{self.prefix}{number}"


# -----------------------------
# 命名引擎
# -----------------------------
class NamingEngine:
    def __init__(self, rules: List[NamingRule]):
        self.rules = rules

    def rename(self, name: str) -> str:
        new_name = name
        for rule in self.rules:
            new_name = rule.apply(new_name)
        return new_name

    def rename_batch(self, names: List[str]) -> List[str]:
        return [self.rename(name) for name in names]
