"""Import/Export resources for portal models."""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget
from .models import Program, Enrollment
from inclusive_world_portal.users.models import User


class ProgramResource(resources.ModelResource):
    """Resource class for importing/exporting Programs."""
    
    start_date = fields.Field(
        column_name='start_date',
        attribute='start_date',
        widget=DateWidget(format='%Y-%m-%d')
    )
    end_date = fields.Field(
        column_name='end_date',
        attribute='end_date',
        widget=DateWidget(format='%Y-%m-%d')
    )
    
    class Meta:
        model = Program
        import_id_fields = ('program_id',)
        fields = (
            'program_id', 'name', 'description', 'fee', 'capacity',
            'archived', 'start_date', 'end_date', 'enrollment_status',
            'enrolled'
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True


class EnrollmentResource(resources.ModelResource):
    """Resource class for importing/exporting Enrollments (user-program relations)."""
    
    user = fields.Field(
        column_name='user_username',
        attribute='user',
        widget=ForeignKeyWidget(User, field='username')
    )
    program = fields.Field(
        column_name='program_name',
        attribute='program',
        widget=ForeignKeyWidget(Program, field='name')
    )
    assigned_by = fields.Field(
        column_name='assigned_by_username',
        attribute='assigned_by',
        widget=ForeignKeyWidget(User, field='username')
    )
    
    class Meta:
        model = Enrollment
        import_id_fields = ('enrollment_id',)
        fields = (
            'enrollment_id', 'user', 'program', 'status', 
            'preference_order', 'enrolled_at', 'assigned_by',
            'assignment_notes', 'assigned_at'
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
