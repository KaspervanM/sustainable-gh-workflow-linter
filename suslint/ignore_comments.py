from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.tokens import CommentToken
from typing import Iterable, Any
import re

IGNORE_COMMENT_REGEX = r"^\s*#\s*suslint\s+ignore\s*:"

def get_line_ignore_comments(d: CommentedMap, comments: dict[int, str] = {}) -> dict[int, str]:
    if hasattr(d, 'ca'):
        parent_comments = d.ca.comment
        combined_comments = []
        if isinstance(parent_comments, list):
            combined_comments = parent_comments
        for item in getattr(d.ca, "items", {}).values():
            combined_comments.extend(item)

        flattened_combined_comments = []
        for elem in combined_comments:
            if isinstance(elem, CommentToken):
                flattened_combined_comments.append(elem)
            elif isinstance(elem, list):
                for e in elem:
                    flattened_combined_comments.append(e)

        for commentToken in flattened_combined_comments:
            if isinstance(commentToken, CommentToken):
                comment = commentToken.value
                if comment:
                    if re.search(IGNORE_COMMENT_REGEX, comment):
                        line = commentToken.start_mark.line + 1
                        comments[line] = comment

        if isinstance(d, dict):
            for k in d:
                get_line_ignore_comments(d[k], comments=comments)
        elif isinstance(d, list):
            for idx, k in enumerate(d):
                get_line_ignore_comments(k, comments=comments)
    return comments


def get_line_ignores(d: CommentedMap) -> dict[int, list[str]]:
    line_ignore_comments = get_line_ignore_comments(d)

    line_ignores = {}
    for line, ignore_comment in line_ignore_comments.items():
        rule_list_string = ignore_comment.split(':')[1]
        rule_list = list(map(str.strip, rule_list_string.split(',')))
        line_ignores[line] = rule_list

    return line_ignores
