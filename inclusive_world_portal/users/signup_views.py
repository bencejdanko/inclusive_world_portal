from django.views.generic import TemplateView
from django.shortcuts import redirect


class RoleSelectionView(TemplateView):
    """
    View for selecting member or volunteer role before signup.
    """
    template_name = 'account/role_selection.html'
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already authenticated, redirect to dashboard
        if request.user.is_authenticated:
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
