import re

urlSafe = re.compile('^[a-zA-Z0-9_-]*$')

normalizePattern = re.compile(r'[\W_]+')


def is_valid_tag(tag: str):
    m = urlSafe.fullmatch(tag)
    return m is not None


class TagBuilder:
    def __init__(self, base: str):
        self.tags = []
        self.base = base
        self.counter = 0

    def useGeneratedTag(self):
        tag = self.base + str(self.counter)
        self.counter += 1
        self.tags.append(tag)
        return tag

    def normalize(self, tag: str):
        if tag:
            normed = normalizePattern.sub('', tag)
            if normed in self.tags:
                return self.useGeneratedTag()
            self.tags.append(normed)
            return normed
        return self.useGeneratedTag()
