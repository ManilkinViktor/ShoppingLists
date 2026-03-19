import enum


class FieldConstraints(enum.IntEnum):
    BASE_LEN = 256
    DESCRIPTION_LEN = 1024
    QUANTITY_BORDER = 10 ** 18
    MIN_PASSWORD = 5
