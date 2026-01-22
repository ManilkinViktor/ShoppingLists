from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):

    cnt_repr_attrs = 1
    repr_attrs = tuple()

    def __repr__(self):
        attrs = []
        for idx, attr in enumerate(self.__table__.columns.keys()):
            if idx < self.cnt_repr_attrs or attr in self.repr_attrs:
                attrs.append(attr)

        return f'<{self.__class__.__name__}({', '.join(f'{attr}={getattr(self, attr)}' for attr in attrs)})>'

