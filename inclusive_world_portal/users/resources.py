"""Import/Export resources for user models."""
from import_export import resources, fields
from import_export.widgets import DateWidget
from .models import User


class UserResource(resources.ModelResource):
    """Resource class for importing/exporting Users."""
    
    date_joined = fields.Field(
        column_name='date_joined',
        attribute='date_joined',
        widget=DateWidget(format='%Y-%m-%d %H:%M:%S')
    )
    last_login = fields.Field(
        column_name='last_login',
        attribute='last_login',
        widget=DateWidget(format='%Y-%m-%d %H:%M:%S')
    )
    
    class Meta:
        model = User
        import_id_fields = ('username',)
        fields = (
            'id', 'username', 'email', 'name', 'role', 'status',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login'
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        # Exclude password field for security
        exclude = ('password',)
