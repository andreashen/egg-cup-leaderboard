"""球队名称标准化映射工具"""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TeamMapper:
    """将各类名称/别名映射到统一标准球队名"""

    def __init__(self, aliases_csv: Path) -> None:
        # alias (lower) -> standard_name
        self._map: dict[str, str] = {}
        self._load(aliases_csv)

    def _load(self, path: Path) -> None:
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith("#") or row[0].strip() == "standard_name":
                    continue
                standard = row[0].strip()
                # First column is standard_name; remaining are aliases
                self._map[standard.lower()] = standard
                for alias in row[1:]:
                    alias = alias.strip()
                    if alias:
                        key = alias.lower()
                        if key in self._map and self._map[key] != standard:
                            logger.warning(
                                "别名冲突: '%s' 同时映射到 '%s' 和 '%s'，将使用后者",
                                alias,
                                self._map[key],
                                standard,
                            )
                        self._map[key] = standard

    def resolve(self, name: str) -> str | None:
        """将输入名称转换为标准球队名，失败返回 None"""
        return self._map.get(name.strip().lower())

    def resolve_or_raise(self, name: str) -> str:
        result = self.resolve(name)
        if result is None:
            raise ValueError(f"未能识别的球队名称: '{name}'")
        return result

    def validate_all(self, names: list[str]) -> list[str]:
        """批量校验并返回标准名，若有无法映射的名称则抛出异常"""
        errors = []
        results = []
        for name in names:
            std = self.resolve(name)
            if std is None:
                errors.append(name)
            else:
                results.append(std)
        if errors:
            raise ValueError(f"以下球队名称无法识别: {errors}")
        return results
