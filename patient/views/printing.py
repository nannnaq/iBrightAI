from django.views.generic import ListView, View
from django.contrib import messages
from django.shortcuts import redirect, render
from patient.models import Patient
from django.shortcuts import render
from patient.models import Patient, BasicParams, CornealTopography, ACCustomization

from collections import defaultdict # <-- 确保导入

# ---------------------------------------------------
# 视图 1: 显示带复选框的患者列表
# ---------------------------------------------------
class PrintPatientListView(ListView):
    model = Patient
    template_name = 'printing/print_patient_list.html'
    context_object_name = 'cases' # 模板中将使用 'cases' 变量
    paginate_by = 20

    def get_queryset(self):
        # 只显示当前用户创建的患者
        return Patient.objects.filter(created_by=self.request.user).order_by('-create_date')

    def get_context_data(self, **kwargs):
        # 1. 调用父类方法，获取基础上下文 (包括 'page_obj' 和 'cases')
        context = super().get_context_data(**kwargs)
        
        # 2. 从 'page_obj' 中获取当前页的患者列表
        page_patients = context['page_obj'] 
        patient_ids = [p.id for p in page_patients]
        
        # 3. 一次性查询出这些患者所有相关的 'custom_type'
        all_params = BasicParams.objects.filter(
            patient_id__in=patient_ids
        ).values_list('patient_id', 'custom_type').distinct()
        
        # 4. 将查询结果存入一个字典，方便查找
        #    格式: { 36: ['0', '2'], 37: ['4'] }
        patient_map = defaultdict(list)
        for pid, ctype in all_params:
            patient_map[pid].append(ctype)

        # 5. (核心逻辑) 遍历当前页的患者，为每个人计算正确的 'print_ctype'
        enhanced_patient_list = []
        for patient in page_patients:
            custom_types = patient_map.get(patient.id, [])
            
            print_ctype = None
            if '0' in custom_types:      # 规则 1: Medmont 普通 (ctype=0) 
                print_ctype = '0'
            elif '2' in custom_types:    # 规则 2: Seour 普通 (ctype=2)
                print_ctype = '2'
            elif '4' in custom_types:    # 规则 3: Tomey 普通 (ctype=4)
                print_ctype = '4'
            elif '1' in custom_types:    # 规则 4: Medmont 四轴 (ctype=1)
                print_ctype = '1'
            elif '3' in custom_types:    # 规则 5: Seour 四轴 (ctype=3)
                print_ctype = '3'
            elif '5' in custom_types:    # 规则 6: Tomey 四轴 (ctype=5)
                print_ctype = '5'
            elif custom_types:           # 备用：如果存在任何未知类型
                print_ctype = custom_types[0]
                
            enhanced_patient_list.append({
                'patient': patient,          # 模板中通过 item.patient.name 访问
                'print_ctype': print_ctype   # 模板中通过 item.print_ctype 访问 (可能是 '0', '2', '4' 或 None)
            })
        
        # 6. 用我们处理过的新列表，覆盖掉 Django 默认的 'cases' 列表
        context['cases'] = enhanced_patient_list
        context['page_title'] = '选择要打印的患者'
        return context

# ---------------------------------------------------
# 视图 2: 处理来自打印列表页面的 POST 请求
# ---------------------------------------------------
class GeneratePrintReportView(View):
    
    def post(self, request, *args, **kwargs):
        # 1. 获取所有勾选的患者 ID
        patient_ids = request.POST.getlist('patient_ids')
        
        if not patient_ids:
            messages.error(request, "您没有选择任何患者。")
            return redirect('print_page') # 重定向回选择页面
        
        # 2. (未来在这里处理打印逻辑)
        #    现在，我们只重定向回列表页面，并显示一条消息
        
        messages.success(request, f"您选择了 {len(patient_ids)} 个患者。打印逻辑尚未实现。")
        
        # 简单地重定向回选择页面
        return redirect('print_page')
        
        # (未来的逻辑可能是: 
        #  context = {'selected_patients': Patient.objects.filter(id__in=patient_ids)}
        #  return render(request, 'patient/print_preview.html', context))

# ---------------------------------------------------
# 视图 3: 打印详情页 (已添加调试信息)
# ---------------------------------------------------
class PrintDetailView(View):
    template_name = 'printing/print_detail.html'

    def get(self, request, *args, **kwargs):
        patient_pk = self.kwargs.get('pk')
        # 'ctype' 将是 '0' (Medmont), '2' (Seour), '4' (Tomey)
        custom_type = request.GET.get('ctype')
        
        try:
            patient = Patient.objects.get(pk=patient_pk)
            
            # --- 1. 获取右眼数据 ---
            right_basic = BasicParams.objects.filter(patient=patient, custom_type=custom_type, eye='right').last()
            right_topo = None
            right_custom = None
            if right_basic:
                right_topo = CornealTopography.objects.filter(BasicParams=right_basic).last()
                right_custom = ACCustomization.objects.filter(BasicParams=right_basic).last()

            # --- 2. 获取左眼数据 ---
            left_basic = BasicParams.objects.filter(patient=patient, custom_type=custom_type, eye='left').last()
            left_topo = None
            left_custom = None
            if left_basic:
                left_topo = CornealTopography.objects.filter(BasicParams=left_basic).last()
                left_custom = ACCustomization.objects.filter(BasicParams=left_basic).last()

            # --- ↓↓↓ 3.获取并转换设备名称 ↓↓↓ ---
            device_name = "未知设备"
            if custom_type == '0':
                device_name = 'Medmont'
            elif custom_type == '2':
                device_name = 'Suoer'
            elif custom_type == '4':
                device_name = 'Tomey'
            elif custom_type == '1':
                device_name = 'Medmont' 
            elif custom_type == '3':
                device_name = 'Suoer'   
            elif custom_type == '5':
                device_name = 'Tomey'   
            else:
                # 备用方案，如果 ctype 不在预期内
                if right_basic: device_name = right_basic.get_custom_type_display().split('-')[0]
                elif left_basic: device_name = left_basic.get_custom_type_display().split('-')[0]
            # --- ↑↑↑ 修改结束 ↑↑↑ ---

            # --- 4. 传递所有数据到模板 ---
            context = {
                'patient': patient,
                'right_basic': right_basic,
                'right_topo': right_topo,
                'right_custom': right_custom,
                'left_basic': left_basic,
                'left_topo': left_topo,
                'left_custom': left_custom,
                'page_title': f"{patient.name} - {device_name} 打印预览",
                'device_name': device_name,
            }
            return render(request, self.template_name, context)

        except Patient.DoesNotExist:
            messages.error(request, "未找到指定的患者。")
            return redirect('print_page')