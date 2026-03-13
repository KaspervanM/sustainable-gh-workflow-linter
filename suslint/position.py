from ruamel.yaml.comments import CommentedMap
from typing import Tuple


def pos(mapping: CommentedMap, key: str) -> Tuple[int, int]:
    """Return 1-based line/column of a mapping key.
    
    ruamel.yaml returns 0-based lines and columns, but most editors use 1-based.
    This function returns the position of the key in a mapping.
    """
    line, col = mapping.lc.key(key)
    return line + 1, col + 1