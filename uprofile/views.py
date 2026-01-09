from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView


class ProfileView(DetailView):
    # template_name = "home/profile.html"
    template_name = "registration/profile.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileView, self).dispatch(*args, **kwargs)

    def get_object(self):
        return self.request.user.profile
