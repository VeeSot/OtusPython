class Field:
    def __init__(self, field, value):
        self.field_type = field
        self.value = value


class BaseField(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            field = Field(k, v)
            setattr(self, k, field)
        self.value = None

    def __get__(self, obj, objtype):
        if obj:
            return self.value
        else:
            # Return constrains for fields
            return self

    def __set__(self, obj, value):
        self.value = value


class CharField(BaseField):
    pass


class ArgumentsField(BaseField):
    pass


class EmailField(CharField):
    pass


class PhoneField(BaseField):
    pass


class DateField(BaseField):
    pass


class BirthDayField(BaseField):
    pass


class GenderField(BaseField):
    pass


class ClientIDsField(BaseField):
    pass