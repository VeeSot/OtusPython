import inspect
from abc import ABC
from typing import List

from HW3.fields import Field, BaseField


class Validator1(ABC):
    def __init__(self):
        self.errors = []

    def get_errors(self):
        return self.errors

    def validate(self,obj:object):
        raise NotImplementedError('Please, to implement this method')

    @property
    def is_valid(self):
        return not self.errors


class Validator:
    def __init__(self, obj: dict, schema):
        self.obj = obj
        self.schema = schema
        self.errors = []
        self.filled_fields = []
        self.validate()

    def __validate(self, field, name, obj: dict):
        value = obj.get(name)
        constrains: List[Field] = filter(lambda v: isinstance(v, Field), field.__dict__.values())
        for constrain in constrains:
            if constrain.field_type == 'nullable':
                if not constrain.value:  # Can't be empty
                    if not value:
                        self.errors.append('Field {} should be filled'.format(name))
                else:
                    self.filled_fields.append(name)
            elif constrain.field_type == 'required':
                if constrain.value:
                    if not value:  # Missed in obj
                        self.errors.append('Field {} should be exists'.format(name))

    def get_errors(self):
        return self.errors

    def validate(self):
        members = inspect.getmembers(self.schema)
        checked_fields = {x[0]: x[1] for x in members if isinstance(x[1], BaseField)}
        for name, field in checked_fields.items():
            self.__validate(field, name, self.obj)

    @property
    def is_valid(self):
        return not self.errors


class FieldValidator(Validator1):
    nullable = 'nullable'
    required = 'required'

    def validate(self,field:Field):
        if field.field_type == FieldValidator.nullable:
            if not field.value:  # Can't be empty
                self.errors.append('Field {} should be filled'.format(name))

        elif constrain.field_type == 'required':
            if constrain.value:
                if not value:  # Missed in obj
                    self.errors.append('Field {} should be exists'.format(name))


class RequestValidator(Validator1):
    def validate(self):
        pass
