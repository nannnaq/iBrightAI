from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from patient.models import Patient


class HomeView(LoginRequiredMixin, TemplateView):
    login_url = "/accounts/login/"
    redirect_field_name = "redirect_to"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HomeView, self).dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 只显示当前用户创建的患者
        context['cases'] = Patient.objects.filter(created_by=self.request.user)
        return context
        

class ProfileView(TemplateView):
    # template_name = "home/profile.html"
    template_name = "registration/profile.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileView, self).dispatch(*args, **kwargs)
