# patient/views/config.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class SettingsView(LoginRequiredMixin, TemplateView):
    """
    渲染通用的“配置设置”页面。
    这个视图只负责显示 HTML，所有复杂的文件操作
    都通过 pywebview API 交给 main.py 处理。
    """
    template_name = "config/settings_page.html" # 通用的模板名称

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "配置设置"
        return context