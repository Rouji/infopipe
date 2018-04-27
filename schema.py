class SchemaError(Exception):
    pass


class SchemaVal:
    def __init__(self, required: bool, vartype: type = None, default=None, comment: str = None):
        self.required = required
        self.vartype = vartype
        self.default = default
        self.comment = comment


class Schema:
    def __init__(self):
        self.vals = {}

    def add_vals(self, vals: dict):
        for name, val in vals.items():
            # check for values defined twice
            if name in self.vals.keys():
                raise SchemaError(f'schema value "{name}" cannot be defined twice')
            self.vals[name] = val

    def get(self, src, name):
        val = self.vals.get(name)
        if not val:
            raise SchemaError(f'schema value "{name}" unknown')

        spl = name.split('.')
        v = src
        try:
            for s in spl:
                v = v[s]
        except:
            if val.required:
                raise SchemaError(f'required schema value "{name}" not set')
            return self.vals[name].default
        if val.vartype is not None and type(v) != val.vartype:
            raise SchemaError(f'schema value "{name}" is of type "{type(v).__name__}", '
                              f'expected "{val.vartype.__name__}"')
        return v

    def validate(self, src):
        for name in self.vals.keys():
            self.get(src, name)
