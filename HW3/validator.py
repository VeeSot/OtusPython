from abc import ABC

from HW3.requests import BasicRequest


class Validator(ABC):
    def __init__(self):
        self.errors = []

    def get_errors(self):
        return self.errors

    def validate(self):
        raise NotImplementedError('Please, to implement this method')

    @property
    def is_valid(self):
        return not self.errors


# class Validator:
#     def __init__(self, obj: dict, schema):
#         self.obj = obj
#         self.schema = schema
#         self.errors = []
#         self.filled_fields = []
#         self.validate()
#
#     def __validate(self, field, name, obj: dict):
#         value = obj.get(name)
#         constrains: List[Field] = filter(lambda v: isinstance(v, Field), field.__dict__.values())
#         for constrain in constrains:
#             if constrain.field_type == 'nullable':
#                 if not constrain.value:  # Can't be empty
#                     if not value:
#                         self.errors.append('Field {} should be filled'.format(name))
#                 else:
#                     self.filled_fields.append(name)
#             elif constrain.field_type == 'required':
#                 if constrain.value:
#                     if not value:  # Missed in obj
#                         self.errors.append('Field {} should be exists'.format(name))
#
#     def get_errors(self):
#         return self.errors
#
#     def validate(self):
#         members = inspect.getmembers(self.schema)
#         checked_fields = {x[0]: x[1] for x in members if isinstance(x[1], BaseField)}
#         for name, field in checked_fields.items():
#             self.__validate(field, name, self.obj)
#
#     @property
#     def is_valid(self):
#         return not self.errors


class FieldValidator(Validator):
    def __init__(self, field, name, value):
        self.name = name
        self.field = field
        self.value = value
        super().__init__()

    def validate(self):
        can_be_nullable = is_required = False
        nullable_field = getattr(self.field, 'nullable', None)
        required_field = getattr(self.field, 'required', None)

        if nullable_field:
            can_be_nullable = nullable_field.value
        if required_field:
            is_required = required_field.value

        if not can_be_nullable:
            if not self.field.value:  # Can't be empty
                self.errors.append('Field {} should be filled'.format(self.name))

        if is_required and self.value is None:
            self.errors.append('Field {} should be exists'.format(self.name))


class RequestValidator(Validator):
    def __init__(self, obj: dict, schema: BasicRequest):
        super().__init__()
        self.obj = obj
        self.schema = schema

    def validate(self):
        schema_fields = [field for field in dir(self.schema) if not field.startswith('_')]
        for schema_field in schema_fields:
            value = getattr(self.obj, schema_field, None)
            field = getattr(self.schema, schema_field)
            field_validator = FieldValidator(field, schema_field, value)
            field_validator.validate()
            if not field_validator.is_valid:
                self.errors = field_validator.errors[0]
                break
