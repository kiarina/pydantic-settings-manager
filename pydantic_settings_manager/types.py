from collections import defaultdict
from typing import Any, DefaultDict, Union

NestedDict = DefaultDict[str, Union["NestedDict", Any]]
"""
ネストした辞書型
"""
