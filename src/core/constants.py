import enum

class FieldConstraints(enum.IntEnum):
    base_len = 256
    description_len = 1024
    quantity_border = 10 ** 18
    min_password = 5
