from collections import defaultdict
from typing import Any, Union

NestedDict = defaultdict[str, Union["NestedDict", Any]]
"""
ネストした辞書型
"""
