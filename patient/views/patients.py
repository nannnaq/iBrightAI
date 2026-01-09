from django.views.generic import CreateView, UpdateView, DetailView, ListView, TemplateView, View, DeleteView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin

import json # <-- 1. 确保在文件顶部导入 json 库

from patient.models import Patient, CornealTopography, ACCustomization, ReviewResult, BasicParams
from patient.forms import PatientForm

from datetime import datetime, timedelta


class CaseListView(LoginRequiredMixin, ListView):
    model = Patient
    # template_name = "patient/patient11_list.html"
    template_name = "uppatient/patient_list.html"  # 模板名称
    context_object_name = "cases"  # 模板中使用的变量名称
    paginate_by = 10  # 分页，每页显示10条数据
    ordering = "-create_date"
    
    # LoginRequiredMixin 的配置：未登录时跳转的地址，默认是 settings.LOGIN_URL
    # login_url = '/login/'  # 如果你的登录也 URL 不是默认的，可以在这里指定

    def get_queryset(self):
        # 因为有了 LoginRequiredMixin，执行到这里时 self.request.user 一定是登录用户
        # 不会再报 AnonymousUser 的错
        queryset = super().get_queryset().filter(created_by=self.request.user)

        name = self.request.GET.get("name")
        gender = self.request.GET.get("gender")
        age = self.request.GET.get("age")
        # create_date = self.request.GET.get("create_date")
        create_date_str = self.request.GET.get("create_date") # 解决时区问题，重命名变量以示区分
        medical_record_number = self.request.GET.get("medical_record_number")
        if name:
            queryset = queryset.filter(name__icontains=name)
        if gender:
            queryset = queryset.filter(gender=gender)
        if age:
            queryset = queryset.filter(age=age)
        # if create_date:
        #     queryset = queryset.filter(create_date__date=create_date)
        if create_date_str:
            try:
                # 1. 将前端传来的日期字符串转换为 date 对象
                start_date = datetime.strptime(create_date_str, "%Y-%m-%d").date()
                # 2. 计算第二天的日期
                end_date = start_date + timedelta(days=1)
                # 3. 使用 __gte (大于等于) 和 __lt (小于) 进行范围查询
                queryset = queryset.filter(create_date__gte=start_date, create_date__lt=end_date)
            except ValueError:
                # 如果日期格式不正确，则忽略此筛选条件
                pass
        if medical_record_number:
            queryset = queryset.filter(medical_record_number__icontains=medical_record_number)

        return queryset

class CaseCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = "memdent/medment_index.html"
    success_url = "/patient/patient_history/"

    def form_valid(self, form):
        # 设置创建者为当前登录用户
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = Patient.objects.last()
        return context

    def form_invalid(self, form):
        # 收集所有字段错误信息
        error_messages = []
        for field, errors in form.errors.items():
            # 获取字段的标签名，如果没有标签则使用字段名
            field_label = form.fields[field].label or field
            for error in errors:
                error_messages.append(f"{field_label}: {error}")

        # 将所有错误信息合并显示
        messages.error(self.request, '创建失败,请检查以下错误, ' + f"{error_messages[0]}")
        return super().form_invalid(form)


class CaseDeleteView(DeleteView):
    model = Patient
    success_url = "/patient/patient_history/"

    def form_valid(self, form):
        messages.success(self.request, '删除成功。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '删除失败，请检查表单数据。')
        return super().form_invalid(form)


class PatientBasicInfor(DetailView):
    model = Patient
    template_name = "memdent/medment_index.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.GET.get('pk', 1):
            response['pk'] = 1
            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 基本信息
        left_basic_params = BasicParams.objects.filter(patient=self.object, eye='left', custom_type='0').last()
        right_basic_params = BasicParams.objects.filter(patient=self.object, eye='right', custom_type='0').last()
        context['left_basic_params'] = left_basic_params
        context['right_basic_params'] = right_basic_params
        # 角膜地形图
        context['left_corneal_topography'] = CornealTopography.objects.filter(patient=self.object, eye='left',
                                                                              BasicParams=left_basic_params).last()
        context['right_corneal_topography'] = CornealTopography.objects.filter(patient=self.object, eye='right',
                                                                               BasicParams=right_basic_params).last()

        # 定制参数信息
        context['left_ac_customization'] = ACCustomization.objects.filter(patient=self.object, eye='left',
                                                                          BasicParams=left_basic_params).last()
        context['right_ac_customization'] = ACCustomization.objects.filter(patient=self.object, eye='right',
                                                                           BasicParams=right_basic_params).last()
        # 复查结果
        context['left_review_result'] = ReviewResult.objects.filter(patient=self.object, eye='left',
                                                                    BasicParams=left_basic_params).last()
        context['right_review_result'] = ReviewResult.objects.filter(patient=self.object, eye='right',
                                                                     BasicParams=right_basic_params).last()
        
        # ====================================================================
        # =============   ↓↓↓ 已修正的逻辑：传递地形图原始数据 ↓↓↓   ===========
        # ====================================================================
        
        # 1. 先从刚刚填充的 context 字典中获取 topography 对象
        right_topo_obj = context.get('right_corneal_topography')
        left_topo_obj = context.get('left_corneal_topography')
        
        # 2. 使用这个新的局部变量进行判断和数据转换
        # 处理右眼地形图原始数据
        # 切向图数据 (Tangential)
        if right_topo_obj and right_topo_obj.raw_data_tangential:
            context['right_topo_data_plotly_json'] = right_topo_obj.raw_data_tangential
        else:
            context['right_topo_data_plotly_json'] = 'null'

        # 轴向图数据 (Axial)
        if right_topo_obj and right_topo_obj.raw_data_axial:
            context['right_topo_data_axial_json'] = json.dumps(right_topo_obj.raw_data_axial)
        else:
            context['right_topo_data_axial_json'] = 'null'

        # 处理左眼地形图原始数据
        # 切向图数据 (Tangential)
        if left_topo_obj and left_topo_obj.raw_data_tangential:
            context['left_topo_data_json'] = left_topo_obj.raw_data_tangential
        else:
            context['left_topo_data_json'] = 'null'

        # 轴向图数据 (Axial)
        if left_topo_obj and left_topo_obj.raw_data_axial:
            context['left_topo_data_axial_json'] = json.dumps(left_topo_obj.raw_data_axial)
        else:
            context['left_topo_data_axial_json'] = 'null'

        # ====================================================================
        # =============   ↑↑↑ 已修正的逻辑：传递地形图原始数据 ↑↑↑   ===========
        # ====================================================================
        # print(context)
        return context


class PatientListHome(ListView):
    model = Patient
    paginate_by = 10  # 分页，每页显示10条数据
    ordering = "id"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PatientUpdateView(UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "memdent/medment_index.html"
    success_url = "/patient/patient_history/"

    def form_valid(self, form):
        # 调用父类的 form_valid 方法来保存表单数据并创建对象
        super().form_valid(form)
        return super().form_valid(form)
