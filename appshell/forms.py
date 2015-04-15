from flask.ext.wtf import Form

class OrderedForm(Form):
    def __iter__(self):
        fields = list(super(OrderedForm, self).__iter__())
        field_order = getattr(self, 'field_order', None)
        if field_order:
            temp_fields = []
            for name in field_order:
                if name == '*':
                    temp_fields.extend([f for f in fields if f.name not in field_order])
                else:
                    temp_fields.append([f for f in fields if f.name == name][0])
            fields =temp_fields
        return iter(fields)
        
    field_order = ['*','ok']
