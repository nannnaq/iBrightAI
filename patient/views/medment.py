import os
import json

from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, ListView, TemplateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.conf import settings
from patient.models import Patient, CornealTopography, ACCustomization, ReviewResult, BasicParams
from patient.forms import (
    PatientForm,
    CornealTopographyForm,
    ACCustomizationForm,
    ReviewResultForm,
    BasicParamsForm,
    CornealTopographyFileForm,
)
from patient.views.other import *

from services.medment import KBQ
from services.medment_4 import KBQ as KBQ_4
from services.zs_tear_film import TearFilmHeightCalculator, FluorescentStaining
from services.z_leimo import TEARFILMDATA
from services.dixingtu_med_height import parse_topographic_map_data
from services.dixingt_med_qiexiang import parse_qiexiang_data
from services.dixingt_med_zhouxiang import parse_zhouxiang_data
from services.dixingt_med_leimozhiliang import parse_leiomozhilaing_data
from services.z_qcode import txt_to_qrcode

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from patient.models import Patient, BasicParams 
from django.forms.models import model_to_dict 

# --- 导入 AI 码 和 QR 码 需要的映射 ---
from patient.views.other import *

# ==========================================================
# =============   ↓↓↓ 新增的 API 视图函数 ↓↓↓   ==============
# ==========================================================

@csrf_exempt
def process_mxf_api_view(request):
    if request.method == 'POST':
        try:
            print("=== [1] 开始处理 POST 请求")
            form_data = request.POST.dict()
            patient_id = form_data.get('patient')
            eye = form_data.get('eye')
            uploaded_file = request.FILES.get('corneal_file')
            print(f"=== [2] patient_id={patient_id}, eye={eye}, has_file={uploaded_file is not None}")

            if not all([patient_id, eye, uploaded_file]):
                return JsonResponse({'success': False, 'error': '缺少 patient, eye 或 corneal_file 参数。'}, status=400)

            # --- 数据清洗逻辑 ---
            decimal_fields = ['mirror_degree', 'cylindrical_power', 'overpressure']
            float_fields = ['overall_diameter', 'optical_zone_diameter', 'ac_arc_width']
            for field in decimal_fields + float_fields:
                if form_data.get(field) == '' or form_data.get(field) is None:
                    # 将空值转换为 0，而不是 None
                    form_data[field] = 0
            print(f"=== [3] 数据清洗完成")

            # --- 移除查询键 ---
            form_data.pop('patient', None)
            form_data.pop('eye', None)
            form_data.pop('csrfmiddlewaretoken', None)
            print(f"=== [4] form_data: {form_data}")

            patient_instance = Patient.objects.get(pk=patient_id)
            print(f"=== [5] 获取患者成功: {patient_instance}")

            # 1. 保存前端传来的用户手动选择的参数
            # 使用 filter().last() 代替 update_or_create，因为可能存在多条历史记录
            basic_params = BasicParams.objects.filter(
                patient=patient_instance,
                eye=eye,
                custom_type='0'
            ).last()
            print(f"=== [6] 查询现有 BasicParams: {basic_params}")

            if basic_params:
                # 更新现有记录
                for key, value in form_data.items():
                    if hasattr(basic_params, key):
                        setattr(basic_params, key, value)
                basic_params.save()
                print(f"=== 更新现有 BasicParams: id={basic_params.id}")
            else:
                # 创建新记录 - 只保留 BasicParams 模型接受的字段
                valid_fields = {field.name for field in BasicParams._meta.get_fields() if hasattr(field, 'column')}
                filtered_form_data = {k: v for k, v in form_data.items() if k in valid_fields}
                print(f"=== 准备创建新 BasicParams, filtered_form_data: {filtered_form_data}")
                basic_params = BasicParams.objects.create(
                    patient=patient_instance,
                    eye=eye,
                    custom_type='0',
                    **filtered_form_data
                )
                print(f"=== 创建新 BasicParams 成功: id={basic_params.id}")

            print(f"=== 保存角膜文件: {uploaded_file.name}")
            basic_params.corneal_file.save(uploaded_file.name, uploaded_file, save=True)
            print(f"=== 角膜文件保存成功")

            # 2. 调用统一的、包含所有计算逻辑的 'calculation_algorithm'
            print(f"=== 开始调用 calculation_algorithm")
            view_instance = BasicParasCreateView()
            result = view_instance.calculation_algorithm(
                patient_pk=patient_id,
                eye_type=eye,
                basic_params_id=basic_params.id,
                custom_type='0'
            )

            if result.get('state') == 1:
                return JsonResponse({'success': True, 'message': result.get('data')})
            else:
                return JsonResponse({'success': False, 'error': result.get('data')}, status=400)

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"=== 错误详情 ===\n{error_trace}")
            print(f"=== form_data: {form_data}")
            return JsonResponse({'success': False, 'error': f'{str(e)}\n详情: {error_trace}'}, status=500)

    return JsonResponse({'success': False, 'error': '只接受 POST 请求。'}, status=405)
# ==========================================================
# =============   ↑↑↑ 新增的 API 视图函数 ↑↑↑   ==============
# ==========================================================

class BasicParasCreateView(CreateView):
    model = BasicParams
    form_class = BasicParamsForm
    context_object_name = "basic_params"
    template_name = "memdent/medment_index.html"
    success_url = "/patient/patient/"

    def form_valid(self, form):
        # 调用父类的 form_valid 方法来保存表单数据并创建对象
        cleaned_data = form.cleaned_data
        patient_pk = cleaned_data.get('patient')
        eye_type = cleaned_data.get('eye')
        patient_pk = patient_pk.pk
        custom_type = "0"  # 定制方式普通定制

        # 检查是否已经存在关联的BasicParams对象
        basic_params_instance = BasicParams.objects.filter(patient=patient_pk, eye=eye_type, custom_type=custom_type).last()
        if basic_params_instance:
            # 如果存在，则更新该基本信息对象
            for field, value in cleaned_data.items():
                if hasattr(basic_params_instance, field):
                    setattr(basic_params_instance, field, value)
            basic_params_instance.save()
            # 查出关联对象(角膜地形图+定制参数信息),并更新
            data = self.calculation_algorithm(patient_pk=patient_pk, eye_type=eye_type, basic_params_id=basic_params_instance.id)
            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request,data["data"])

        else:
            # 如果不存在，则创建新对象
            basic_params = form.save(custom_type=custom_type)
            data = self.calculation_algorithm(patient_pk=patient_pk, eye_type=eye_type, basic_params_id=basic_params.id, custom_type=custom_type)
            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request,data["data"])

        # 重定向到patient的详情页面
        success_url = reverse('patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)

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

        # 重定向到patient的详情页面
        patient_pk = self.request.POST.get('patient')
        success_url = reverse('patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)

    def calculation_algorithm(self, patient_pk, eye_type, basic_params_id, special_type=False, custom_type="0"):
        # 将保存的数据筛选出来，取出保存文件进行以下计算
        basic_params_data = BasicParams.objects.filter(id=basic_params_id, custom_type=custom_type).last()


        # # 1. 获取基础参数对象
        basic_params_data = BasicParams.objects.get(id=basic_params_id)
        print(f'获取基础参数对象, basic_params_data: {basic_params_data}' )
        overall_diameter = float(basic_params_data.overall_diameter)
        optical_zone_diameter = float(basic_params_data.optical_zone_diameter)

        # 处理奇数问题：如果小数点后一位为奇数，减去0.1变成偶数
        def is_odd_decimal(value):
            """检查小数点后一位是否为奇数"""
            return int(round(value * 10)) % 2 == 1

        if is_odd_decimal(overall_diameter):
            overall_diameter = round(overall_diameter - 0.1, 1)
            print(f'总直径为奇数，调整为偶数: {overall_diameter}')

        if is_odd_decimal(optical_zone_diameter):
            optical_zone_diameter = round(optical_zone_diameter - 0.1, 1)
            print(f'光学区直径为奇数，调整为偶数: {optical_zone_diameter}')

        # 3. 执行和前端JS完全相同的计算逻辑
        basic_params_data.ac_arc_start = optical_zone_diameter/2 + 0.8
        basic_params_data.ac_arc_end = overall_diameter/2 - 0.5

        # 3. 将计算出的新值保存回数据库
        basic_params_data.save(update_fields=['ac_arc_start', 'ac_arc_end'])

        # (可选) 打印用于调试的参数
        params_dict = model_to_dict(basic_params_data, exclude=['corneal_file', 'corneal_file2'])
        print("\n" + "="*30)
        print(f"开始为 {eye_type} 眼计算，使用的参数如下:")
        print(json.dumps(params_dict, indent=4, ensure_ascii=False, default=str))
        print("="*30 + "\n")

        # 4. 准备文件路径并执行后续所有计算
        data_file = basic_params_data.corneal_file
        print(f'文件路径, data_file = basic_params_data.corneal_file: {data_file}' )
        if not data_file:
            return {"data": "未找到地形图文件，无法进行计算。", "state": 0}
        
        full_path = os.path.join(settings.MEDIA_ROOT, str(data_file))

    
        # data_file = basic_params_data.corneal_file
        # 保存文件
        if data_file:
            # 1. (新增) 先在这里计算并保存 AC 弧径宽
            #    因为后续的计算可能会用到这个值
            ac_arc_width_val = basic_params_data.ac_arc_end - basic_params_data.ac_arc_start
            basic_params_data.ac_arc_width = f"{ac_arc_width_val:.2f}"
            basic_params_data.save(update_fields=['ac_arc_width'])

            # 根据文件，计算角膜地形图
            from services import aop_mxf
            full_path = os.path.join(settings.MEDIA_ROOT, str(data_file))
            full_path = os.path.normpath(full_path)
            try:
                # 1. 创建解析器实例
                mxf_parser = aop_mxf.OperationMXF(full_path)
                
                # 2. 解析你需要的基础参数
                parse_data = mxf_parser.parse_parameters()
                
                # 3. (新增) 解析用于AI码的 50x50 原始数据矩阵
                raw_data_array = mxf_parser.parse_calculated_value() 

            except Exception as e:
                # 确保导入 traceback: import traceback
                # traceback.print_exc() # 打印详细错误，帮助调试
                return {"data": "角膜地形图数据非当前左/右眼文件，或文件已损坏", "state": 0, }

            flat_k = float(parse_data['FlatK'])
            plane_angle = float(parse_data['FlatAngle'])
            steep_k = float(parse_data['SteepK'])
            inclined_angle = float(parse_data['SteepAngle'])

            delta_k = abs(flat_k - steep_k)

            # 计算定制参数信息
            print(f"平K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}",
                  f"{[inclined_angle, inclined_angle + 180]}", )

            # 计算平K方向
            flat_k_com_result = KBQ([basic_params_data.ac_arc_start, basic_params_data.ac_arc_end],
                                    [plane_angle, plane_angle + 180],
                                    filter_data=full_path).main(k_type=0, special_type=special_type)
            if flat_k_com_result is None:
                return {"data": "角膜地形图数据不全，请更换角膜地形图文件", "state": 0, }

            print(f"平k:{flat_k_com_result}")
            ac_arc_k1 = flat_k_com_result['best_data']['K']
            ac_arc_k2 = flat_k_com_result['best_data']['K']
            ac_arc_k3 = flat_k_com_result['best_data']['K']
            ac_arc_k4 = flat_k_com_result['best_data']['K']
            reverse_arc_height = flat_k_com_result['best_data']["B"] + 5
            ace_position = flat_k_com_result['best_data']['Q']

            # 计算陡K方向
            print(f"陡K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}, "
                  f"{[inclined_angle, inclined_angle + 180]}, "
                  f"{flat_k_com_result['best_data']['Q']}",
                  f"{flat_k_com_result['best_data']['B']}")

            # 计算陡K，将平k计算的Q和B给定，只遍历k值，寻找最佳k值
            steep_k_com_result = KBQ([round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end],
                                     [inclined_angle, inclined_angle + 180],
                                     filter_data=full_path).main(k_type=1,
                                                                 pin_q_values=flat_k_com_result['best_data']['Q'],
                                                                 pin_b_values=flat_k_com_result['best_data']["B"],
                                                                 special_type=special_type)
            if steep_k_com_result is None:
                return {"data": "角膜地形图数据不全，请更换角膜地形图文件", "state": 0, }

            print(f"陡k:{steep_k_com_result}")
            steep_k_calculate = steep_k_com_result['best_data']['K']

            # =============   ↓↓↓ 现在计算基弧曲率半径 ↓↓↓   ==============
            
            # 1. 安全地获取球镜度和过矫压的值，并转换为浮点数
            mirror_degree_val = float(basic_params_data.mirror_degree or 0)
            overpressure_val = float(basic_params_data.overpressure or 0)
            print(f"--- 参与计算的球镜度: {mirror_degree_val}")
            print(f"--- 参与计算的过矫压: {overpressure_val}")
            # 2. 将过矫压取相反数，然后加到球镜度上
            effective_mirror_degree = mirror_degree_val - overpressure_val
            
            # 3. 使用新的“有效球镜度”来计算基弧曲率半径
            base_arc_curvature_radius = 337.5 / (flat_k + effective_mirror_degree - 0.75)

            # =============   ↑↑↑ 核心公式修改在这里 ↑↑↑   ==============

            tac_position = abs(steep_k_calculate - ac_arc_k1)
            if tac_position == 0.25:
                # 如果TAC是0.25，将TAC设置为0.50,并且陡K=平K
                tac_position = 0.50
                steep_k_calculate = ac_arc_k1

       


            print(f"tac:{tac_position}")
            # =============   ↓↓↓ 捕获完整结果 ↓↓↓   ==========

            
            # 原来的代码只获取了图片路径，现在我们获取包含路径和原始数据的整个字典
            img_tangential_curvature = parse_qiexiang_data(file_path=full_path).get("save_dir_path")
            raw_data_tangential = parse_qiexiang_data(file_path=full_path).get("raw_plotly_data") # 获取我们新增的原始数据
            
            img_axial_curvature = parse_zhouxiang_data(file_path=full_path).get("save_dir_path")
            raw_data_axial = parse_zhouxiang_data(file_path=full_path).get("raw_plotly_data")
            # ======================↑↑↑================================


            # 保存角膜地形图
            corneal_topography, created = CornealTopography.objects.update_or_create(
                patient=Patient.objects.get(id=patient_pk),
                BasicParams=basic_params_data,
                eye=eye_type,
                defaults={
                    'flat_k': flat_k,
                    'plane_angle': plane_angle,
                    'steep_k': steep_k,
                    'inclined_angle': inclined_angle,
                    'delta_k': delta_k,
                    'img_tangential_curvature': img_tangential_curvature,
                    'img_axial_curvature': img_axial_curvature,

                    # =============   ↓↓↓ 保存原始数据 ↓↓↓   ========
                    'raw_data_tangential': raw_data_tangential,
                    'raw_data_axial': raw_data_axial,
                    # =============   ↑↑↑ 保存原始数据 ↑↑↑   ========

                }
            )


            # 计算反转弧径宽和适配弧径宽
            reverse_arc_width_val = 0.8
            adaptable_arc_width_val = basic_params_data.ac_arc_end - basic_params_data.ac_arc_start

            create_result, created = ACCustomization.objects.update_or_create(
                patient=Patient.objects.get(id=patient_pk),
                eye=eye_type,
                BasicParams=basic_params_data,
                defaults={
                    'ac_arc_k1': ac_arc_k1,
                    'ac_arc_k2': ac_arc_k2,
                    'ac_arc_k3': ac_arc_k3,
                    'ac_arc_k4': ac_arc_k4,
                    'steep_k_calculate': steep_k_calculate,
                    'reverse_arc_height': reverse_arc_height,
                    'ace_position': ace_position,
                    'tac_position': tac_position,
                    'base_arc_curvature_radius': base_arc_curvature_radius,
                    # 'qrcode_medment_accustomization': qrcode_path,
                    # --- ↓↓↓ 新增这两行来保存计算结果 ↓↓↓ ---
                    'reverse_arc_width': f"{reverse_arc_width_val:.2f}",
                    'adaptable_arc_width': f"{adaptable_arc_width_val:.2f}",
                    # --- ↑↑↑ 新增结束 ↑↑↑ ---
                }
            )
            print("生成泪膜图数据")
            # 生成泪膜图数据
            common_params = {
                'lens_type': basic_params_data.lens_type,
                'ace_position': ace_position,
                'flat_k': flat_k,
                'base_arc_curvature_radius': base_arc_curvature_radius,
                'side_arc_position': create_result.side_arc_position,
                'ac_arc_start': basic_params_data.ac_arc_start,
                'ac_arc_end': basic_params_data.ac_arc_end,
                'reverse_arc_height': reverse_arc_height,
                'overall_diameter': basic_params_data.overall_diameter,
                'al_type': 0,
                'file_path': full_path
            }
            # print(f"common_params:{common_params}")
            print("计算平K泪膜图")
            # 计算平K泪膜图
            tear_film_ping_k = TearFilmHeightCalculator(optical_zone_diameter=optical_zone_diameter,ac_arc_k1=ac_arc_k1,
                                                        degree_list=[plane_angle, plane_angle + 180],
                                                        **common_params).main_calculate()
            C1 = TEARFILMDATA(tear_film_ping_k['x'], tear_film_ping_k['y1'], tear_film_ping_k['y2'])
            tear_film_ping_k_data = C1.main()
            print("计算陡K泪膜图")
            # 计算陡K泪膜图
            tear_film_steep_k = TearFilmHeightCalculator(optical_zone_diameter=optical_zone_diameter,ac_arc_k1=steep_k_calculate,
                                                         degree_list=[inclined_angle, inclined_angle + 180],
                                                         **common_params).main_calculate()
            C2 = TEARFILMDATA(tear_film_steep_k['x'], tear_film_steep_k['y1'], tear_film_steep_k['y2'])
            tear_film_steep_k_data = C2.main()

            # 保存泪膜图
            tear_film = {
                "tear_film_ping_k": tear_film_ping_k_data,
                "ping_k_lens_height": tear_film_ping_k['lens_height'],
                "ping_k_radius_list01": tear_film_ping_k['radius_list01'],
                "ping_k_radius_list02": tear_film_ping_k['radius_list02'],
                "tear_film_steep_k": tear_film_steep_k_data,
                "steep_k_lens_height": tear_film_steep_k['lens_height'],
                "steep_k_radius_list01": tear_film_steep_k['radius_list01'],
                "steep_k_radius_list02": tear_film_steep_k['radius_list02'],
                "bc": basic_params_data.ac_arc_start - 0.8,
                "rc": basic_params_data.ac_arc_start,
                "ac": basic_params_data.ac_arc_end,
                "pc": basic_params_data.overall_diameter/2,
            }
            # 拿到 "正确" 的基弧半径 (Value B)
            final_base_arc_radius = tear_film_ping_k["min_base_arc_curvature_radius"]
            create_result.base_arc_curvature_radius = final_base_arc_radius

            tac_label = str(create_result.tac_position)
            for option in tac_options:
                if option['value'] == float(create_result.tac_position): tac_label = option['label']; break
            ace_label = str(create_result.ace_position)
            for option in ace_position_options:
                if option['value'] == float(create_result.ace_position): ace_label = option['label']; break

            ai_code = generate_ai_code(basic_params_data, create_result, data_array=raw_data_array)

            qrcode_data = f"客户姓名：{basic_params_data.patient.name}\n" \
                          f"眼别：{basic_params_data.get_eye_display()}\n" \
                          f"基弧曲率半径：{round(float(final_base_arc_radius), 2)}\n" \
                          f"基弧直径：{basic_params_data.optical_zone_diameter}\n" \
                          f"反转弧直径：{basic_params_data.ac_arc_start * 2:.1f}\n" \
                          f"适配弧直径：{basic_params_data.ac_arc_end * 2}\n" \
                          f"总直径：{basic_params_data.overall_diameter}\n" \
                          f"颜色：{'蓝色' if eye_type == 'left' else '绿色'}\n" \
                          f"AI码：{ai_code}" # <-- AI码已添加

            qrcode_path = txt_to_qrcode(qrcode_data).get("save_dir_path", None)

            # 保存结果
            updated = ACCustomization.objects.filter(id=create_result.id).update(
                tear_film_data=tear_film,
                base_arc_curvature_radius=final_base_arc_radius,
                qrcode_medment_accustomization=qrcode_path,
                ai_code=ai_code
            )
            print("开始计算荧光染色图...")
            # 荧光染色图
            fluorescent_staining = FluorescentStaining(
                degree_list=[plane_angle, plane_angle + 180, inclined_angle, inclined_angle + 180],
                acc_id=create_result.id,
                overall_diameter=basic_params_data.overall_diameter,
                optical_zone_diameter=basic_params_data.optical_zone_diameter, )
            result = fluorescent_staining.fluorescent_staining(
                h1=tear_film_ping_k['y1'],
                h3=tear_film_ping_k['y2'],
                h2=tear_film_steep_k['y1'],
                h4=tear_film_steep_k['y2']
            )
            
            updated = result['updated']

            if updated:
                return {"data": "参数创建成功", "state": 1, }
            else:
                return {"data": "参数更新成功", "state": 1, }
        else:
            return {"data": "参数更新成功", "state": 1, }


class CustomizeView(DetailView):
    model = Patient
    template_name = "uppatient/../../templates/memdent/medment_index_4_customize.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.GET.get('pk', 1):
            response['pk'] = 1
            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 基本信息
        left_basic_params = BasicParams.objects.filter(patient=self.object, eye='left', custom_type='1').last()
        right_basic_params = BasicParams.objects.filter(patient=self.object, eye='right', custom_type='1').last()
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

        return context


class CustomizeViewCreate(CreateView):
    model = BasicParams
    form_class = BasicParamsForm
    template_name = "memdent/medment_index.html"
    success_url = "/patient/4_customize/"

    def form_valid(self, form):
        # 调用父类的 form_valid 方法来保存表单数据并创建对象
        cleaned_data = form.cleaned_data
        patient_pk = cleaned_data.get('patient')
        eye_type = cleaned_data.get('eye')
        patient_pk = patient_pk.pk
        custom_type = "1"  # 定制方式-4轴定制

        # 检查是否已经存在关联的BasicParams对象
        basic_params_instance = BasicParams.objects.filter(patient=patient_pk, eye=eye_type,
                                                           custom_type=custom_type).last()
        if basic_params_instance:
            # 如果存在，则更新该基本信息对象
            for field, value in cleaned_data.items():
                if hasattr(basic_params_instance, field):
                    setattr(basic_params_instance, field, value)
            basic_params_instance.save()

            # 查出关联对象(角膜地形图+定制参数信息),并更新
            data = self.calculation_algorithm(patient_pk=patient_pk, eye_type=eye_type,
                                              basic_params_id=basic_params_instance.id)

            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request,data["data"])

        else:
            # 如果不存在，则创建新对象
            # form.instance.patient = patient_pk  # 确保关联patient
            basic_params = form.save(custom_type=custom_type)
            data = self.calculation_algorithm(patient_pk=patient_pk, eye_type=eye_type, basic_params_id=basic_params.id,
                                              custom_type=custom_type)
            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request,data["data"])

        # 重定向到patient的详情页面
        success_url = reverse('4_customize', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)

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

    def calculation_algorithm(self, patient_pk, eye_type, basic_params_id, special_type=False, custom_type="1"):
        # 将保存的数据筛选出来，取出保存文件进行以下计算
        basic_params_data = BasicParams.objects.filter(id=basic_params_id, custom_type=custom_type).last()
        data_file = basic_params_data.corneal_file
        # 保存文件
        if data_file:
            # 1. (新增) 先在这里计算并保存 AC 弧径宽
            ac_arc_width_val = basic_params_data.ac_arc_end - basic_params_data.ac_arc_start
            basic_params_data.ac_arc_width = f"{ac_arc_width_val:.2f}"
            basic_params_data.save(update_fields=['ac_arc_width'])
            # 根据文件，计算角膜地形图
            from services import aop_mxf
            full_path = os.path.join(settings.MEDIA_ROOT, str(data_file))
            full_path = os.path.normpath(full_path)

            try:
                parse_data = aop_mxf.OperationMXF(full_path).parse_parameters()
            except Exception as e:
                return {"data": "角膜地形图数据非当前左/右眼文件，请更换角膜地形图文件", "state": 0, }

            flat_k = parse_data['FlatK']
            plane_angle = parse_data['FlatAngle']
            steep_k = parse_data['SteepK']
            inclined_angle = parse_data['SteepAngle']
            delta_k = abs(flat_k - steep_k)

            # 计算定制参数信息
            # print(f"平K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}",
            #       f"{[inclined_angle, inclined_angle + 180]}", )

            # 计算平K方向
            flat_k_com_result = KBQ_4([basic_params_data.ac_arc_start, basic_params_data.ac_arc_end],
                                      [plane_angle, plane_angle + 90, plane_angle + 180, plane_angle + 270],
                                      filter_data=full_path).main(k_type=0, special_type=special_type)
            if flat_k_com_result is None:
                return {"data": "角膜地形图数据不全，请更换角膜地形图文件", "state": 0, }
            # print(f"平k:{flat_k_com_result}")
            ac_arc_k1 = flat_k_com_result[0]['best_data']['K']
            ac_arc_k2 = flat_k_com_result[1]['best_data']['K']
            ac_arc_k3 = flat_k_com_result[2]['best_data']['K']
            ac_arc_k4 = flat_k_com_result[3]['best_data']['K']
            reverse_arc_height = flat_k_com_result[0]['best_data']["B"] + 5
            ace_position = flat_k_com_result[0]['best_data']['Q']

            # 计算陡K方向
            # print(f"陡K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}, "
            #       f"{[inclined_angle, inclined_angle + 180]}, "
            #       f"{flat_k_com_result[0]['best_data']['Q']}",
            #       f"{flat_k_com_result[0]['best_data']['B']}")

            # 计算陡K，将平k计算的Q和B给定，只遍历k值，寻找最佳k值
            steep_k_com_result = KBQ_4([round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end],
                                       [plane_angle, plane_angle + 90, plane_angle + 180, plane_angle + 270],
                                       filter_data=full_path).main(k_type=1,
                                                                   pin_q_values=flat_k_com_result[0]['best_data']['Q'],
                                                                   pin_b_values=flat_k_com_result[0]['best_data']["B"],
                                                                   special_type=special_type)
            if steep_k_com_result is None:
                return {"data": "角膜地形图数据不全，请更换角膜地形图文件", "state": 0, }

            # print(f"陡k:{steep_k_com_result}")
            steep_k_calculate = steep_k_com_result[0]['best_data']['K']
            base_arc_curvature_radius = 337.5 / (flat_k + float(basic_params_data.mirror_degree) - 0.75)
            tac_position = abs(steep_k_calculate - ac_arc_k1)
            # print(f"tac:{tac_position}")

            

            img_corneal_height = parse_topographic_map_data(file_path=full_path).get("save_dir_path")
            # ==========================================================
            # =============   ↓↓↓ 捕获完整结果 ↓↓↓   ==========
            # ==========================================================
            
            # 原来的代码只获取了图片路径，现在获取包含路径和原始数据的整个字典
            img_tangential_curvature = parse_qiexiang_data(file_path=full_path).get("save_dir_path")
            raw_data_tangential = parse_qiexiang_data(file_path=full_path).get("raw_plotly_data") 

            img_axial_curvature = parse_zhouxiang_data(file_path=full_path).get("save_dir_path")
            raw_data_axial = parse_zhouxiang_data(file_path=full_path).get("raw_plotly_data")
             # ======================↑↑↑================================
             # ======================↑↑↑================================
             # ======================↑↑↑================================
            img_tear_film_quality = parse_leiomozhilaing_data(file_path=full_path).get("save_dir_path")

            # 保存角膜地形图
            corneal_topography, created = CornealTopography.objects.update_or_create(
                patient=Patient.objects.get(id=patient_pk),
                BasicParams=basic_params_data,
                eye=eye_type,
                defaults={
                    'flat_k': flat_k,
                    'plane_angle': plane_angle,
                    'steep_k': steep_k,
                    'inclined_angle': inclined_angle,
                    'delta_k': delta_k,
                    'img_corneal_height': img_corneal_height,
                    'img_tangential_curvature': img_tangential_curvature,
                    'img_axial_curvature': img_axial_curvature,
                    'img_tear_film_quality': img_tear_film_quality,
                    # ==========================================================
                    # =============   ↓↓↓ 保存原始数据 ↓↓↓   ========
                    # ==========================================================
                    'raw_data_tangential': raw_data_tangential,
                    'raw_data_axial': raw_data_axial,
                    # ==========================================================
                    # =============   ↑↑↑ 保存原始数据 ↑↑↑   ========
                    # ==========================================================
                }
            )
            
            # 为 Tac 档位查找 label
            tac_label = str(tac_position) # 默认显示原始数值
            for option in tac_options:
                # 注意进行类型转换以确保正确比较
                if option['value'] == float(tac_position):
                    tac_label = option['label']
                    break

            # 为 ACe 档位查找 label
            ace_label = str(ace_position) # 默认显示原始数值
            for option in ace_position_options:
                if option['value'] == float(ace_position):
                    ace_label = option['label']
                    break

            # 生成二维码
            qrcode_data = f"患者ID：{patient_pk}\n角膜地形图ID：{corneal_topography.id}\n定制参数如下：\n" \
                          f"AC弧K值(D)：{ac_arc_k1}\n" \
                          f"基弧曲率半径(mm)：{base_arc_curvature_radius:.2f}\n" \
                          f"Tac档位：{tac_label}\n" \
                          f"ACe档位：{ace_label}\n" \
                        #   f"Tac档位：{tac_label}\n" \
                        #   f"ACe档位：{ace_label}\n" \
                        #   f"反转弧矢高：{reverse_arc_height}\n"

            qrcode_path = txt_to_qrcode(qrcode_data).get("save_dir_path", None)

            # 计算反转弧径宽和适配弧径宽
            reverse_arc_width_val = 0.8
            adaptable_arc_width_val = basic_params_data.ac_arc_end - basic_params_data.ac_arc_start

            create_result, created = ACCustomization.objects.update_or_create(
                patient=Patient.objects.get(id=patient_pk),
                eye=eye_type,
                BasicParams=basic_params_data,
                defaults={
                    'ac_arc_k1': ac_arc_k1,
                    'ac_arc_k2': ac_arc_k2,
                    'ac_arc_k3': ac_arc_k3,
                    'ac_arc_k4': ac_arc_k4,
                    'steep_k_calculate': steep_k_calculate,
                    'reverse_arc_height': reverse_arc_height,
                    'ace_position': ace_position,
                    'tac_position': tac_position,
                    'base_arc_curvature_radius': base_arc_curvature_radius,
                    'qrcode_medment_accustomization': qrcode_path,
                    'reverse_arc_width': f"{reverse_arc_width_val:.2f}",
                    'adaptable_arc_width': f"{adaptable_arc_width_val:.2f}",
                }
            )
            print("生成泪膜图数据参数准备完成，开始计算泪膜图数据...")
            # 生成泪膜图数据
            common_params = {
                'lens_type': basic_params_data.lens_type,
                'ace_position': ace_position,
                'flat_k': flat_k,
                'base_arc_curvature_radius': base_arc_curvature_radius,
                'side_arc_position': create_result.side_arc_position,
                'ac_arc_start': basic_params_data.ac_arc_start,
                'ac_arc_end': basic_params_data.ac_arc_end,
                'reverse_arc_height': reverse_arc_height,
                'overall_diameter': basic_params_data.overall_diameter,
                'al_type': 1,
                'file_path': full_path
            }
            # print(f"common_params:{common_params}")
            print("计算平K泪膜图数据开始...")
            # 计算平K泪膜图
            tear_film_ping_k = TearFilmHeightCalculator(ac_arc_k1=ac_arc_k1,
                                                        ac_arc_k2=ac_arc_k2,
                                                        ac_arc_k3=ac_arc_k3,
                                                        ac_arc_k4=ac_arc_k4,
                                                        degree_list=[plane_angle, plane_angle + 90, plane_angle + 180,
                                                                     plane_angle + 270],
                                                        **common_params).main_calculate()
            # 计算平K泪膜图
            C1 = TEARFILMDATA(tear_film_ping_k['x'], tear_film_ping_k['y1'], tear_film_ping_k['y3'])
            tear_film_ping_k_data_01 = C1.main()
            C2 = TEARFILMDATA(tear_film_ping_k['x'], tear_film_ping_k['y2'], tear_film_ping_k['y4'])
            tear_film_ping_k_data_02 = C2.main()

            # 保存泪膜图
            tear_film = {
                "tear_film_ping_k": tear_film_ping_k_data_01,
                "tear_film_steep_k": tear_film_ping_k_data_02,
                "ping_k_lens_height_01": tear_film_ping_k['lens_height_01'],
                "ping_k_lens_height_02": tear_film_ping_k['lens_height_02'],
                "ping_k_lens_height_03": tear_film_ping_k['lens_height_03'],
                "ping_k_lens_height_04": tear_film_ping_k['lens_height_04'],
                "ping_k_radius_list01": tear_film_ping_k['radius_list01'],
                "ping_k_radius_list02": tear_film_ping_k['radius_list02'],
                "ping_k_radius_list03": tear_film_ping_k['radius_list03'],
                "ping_k_radius_list04": tear_film_ping_k['radius_list04'],
                "bc": basic_params_data.ac_arc_start - 0.8,
                "rc": basic_params_data.ac_arc_start,
                "ac": basic_params_data.ac_arc_end,
                "pc": basic_params_data.overall_diameter / 2,
            }

            # 保存结果
            updated = ACCustomization.objects.filter(id=create_result.id).update(
                tear_film_data=tear_film,
                # base_arc_curvature_radius=tear_film_ping_k["min_base_arc_curvature_radius"],
            )

            if updated:
                return {"data": "参数创建成功", "state": 1, }
            else:
                return {"data": "参数更新成功", "state": 1, }
        else:
            return {"data": "参数更新成功", "state": 1, }


# class ParamsDetailView(DetailView):
#     model = Patient
#     template_name = "patient/4_customize_detail.html"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         eye = self.request.GET.get('eye')
#         basic_params = BasicParams.objects.get(patient=self.object, eye=eye)
#         corneal_topography = CornealTopography.objects.get(patient=self.object, eye=eye)
#         ac_customization = ACCustomization.objects.get(patient=self.object, eye=eye)
#         context['basic_params'] = basic_params
#         context['corneal_topography'] = corneal_topography
#         context['ac_customization'] = ac_customization
#         return context


class CustomizedUpdateView(UpdateView):
    model = ACCustomization
    form_class = ACCustomizationForm
    template_name = "memdent/medment_index.html"
    success_url = "/patient/4_customize/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 基本信息
        left_basic_params = BasicParams.objects.filter(patient=self.object, eye='left', custom_type='1').last()
        right_basic_params = BasicParams.objects.filter(patient=self.object, eye='right', custom_type='1').last()
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

        return context

    def form_valid(self, form):
        cus_pk = self.kwargs.get('pk')
        patient_pk = self.object.patient.pk
        form.save()
        success_url = reverse('4_customize', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)


class CornealTopographyUpdateView(UpdateView):
    model = CornealTopography
    form_class = CornealTopographyForm

    def form_valid(self, form):
        patient = self.object.patient
        patient_pk = patient.id
        basic_data = self.object.BasicParams
        print(f"basic_data.custom_type:{basic_data.custom_type}")

        # 保存表单数据
        form.save()
        # 重定向到patient的详情页面
        messages.success(self.request, "角膜地形图更新成功")
        if basic_data.custom_type == '0':
            success_url = reverse('patient_detail', kwargs={'pk': patient_pk})
        elif basic_data.custom_type == '1':
            success_url = reverse('4_customize', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)


class ErrorView(TemplateView):
    template_name = 'upexceptionpage/error.html'


class SpecialProgressBarView(View):
    def post(self, request, *args, **kwargs):
        # 处理 POST 请求
        type_cc = request.POST.get('type_cc', 0)
        patient_pk = request.POST.get('patient_pk', 0)

        ac_cus = request.POST.get('ac_cus', 0)
        ace_position = request.POST.get('ace_position', 0)

        ring_cus = request.POST.get('ring_cus', 0)
        tac_position = request.POST.get('tac_position', 0)

        # 如果value是说明要进行处理ace_position
        if type_cc == 'right_ace_position_modify':
            basic_param_id = request.POST.get('right_basic_params_id', 0)
            ac_custom_id = request.POST.get('right_ac_custom_id', 0)

            basic_filter = BasicParams.objects.filter(id=basic_param_id)
            acc_filter = ACCustomization.objects.filter(id=ac_custom_id)

            basic_filter.update(ac_cus=ac_cus)
            acc_filter.update(ace_position=ace_position)
            eyes_type = basic_filter.first().eye

        elif type_cc == 'right_tac_position_modify':

            basic_param_id = request.POST.get('right_basic_params_id', 0)
            ac_custom_id = request.POST.get('right_ac_custom_id', 0)
            acc_filter = ACCustomization.objects.filter(id=ac_custom_id)
            k1 = float(acc_filter.first().ac_arc_k1) + float(tac_position)
            basic_filter = BasicParams.objects.filter(id=basic_param_id)

            basic_filter.update(ring_cus=ring_cus)
            acc_filter.update(tac_position=tac_position, steep_k_calculate=k1)
            eyes_type = basic_filter.first().eye

        elif type_cc == 'left_ace_position_modify':

            basic_param_id = request.POST.get('left_basic_params_id', 0)
            ac_custom_id = request.POST.get('left_ac_custom_id', 0)

            basic_filter = BasicParams.objects.filter(id=basic_param_id)
            acc_filter = ACCustomization.objects.filter(id=ac_custom_id)

            basic_filter.update(ac_cus=ac_cus)
            acc_filter.update(ace_position=ace_position)
            eyes_type = basic_filter.first().eye

        elif type_cc == 'left_tac_position_modify':

            basic_param_id = request.POST.get('left_basic_params_id', 0)
            ac_custom_id = request.POST.get('left_ac_custom_id', 0)
            acc_filter = ACCustomization.objects.filter(id=ac_custom_id)
            k1 = float(acc_filter.first().ac_arc_k1) + float(tac_position)
            basic_filter = BasicParams.objects.filter(id=basic_param_id)

            basic_filter.update(ring_cus=ring_cus)
            acc_filter.update(tac_position=tac_position, steep_k_calculate=k1)
            eyes_type = basic_filter.first().eye

        messages.success(request, "更新成功")
        # 返回 JSON 响应
        success_url = reverse('patient_detail', kwargs={'pk': patient_pk})
        success_url += f"?success=done&eyes_type={eyes_type}"
        return HttpResponseRedirect(success_url)


class UpdateParameter(View):

    def post(self, request, *args, **kwargs):
        ac_custom_id_left = request.POST.get('left_ac_custom_id', 0)
        ac_custom_id_right = request.POST.get('right_ac_custom_id', 0)
        patient_pk = request.POST.get('patient_pk', 0)
        update_func = request.POST.get("update_func")

        if update_func == "0":
            if ac_custom_id_left:
                ParamsModifyView.secondary_caluculation(ac_custom_id_left)
            if ac_custom_id_right:
                ParamsModifyView.secondary_caluculation(ac_custom_id_right)
        elif update_func == "1":
            if ac_custom_id_left:
                acc_left = ACCustomization.objects.filter(id=ac_custom_id_left).first()
                if acc_left and acc_left.BasicParams:  # 添加空值检查
                    BasicParams.objects.filter(id=acc_left.BasicParams.id).delete()
            if ac_custom_id_right:
                acc_right = ACCustomization.objects.filter(id=ac_custom_id_right).first()
                if acc_right and acc_right.BasicParams:  # 添加空值检查
                    BasicParams.objects.filter(id=acc_right.BasicParams.id).delete()

        messages.success(request, "更新成功")
        success_url = reverse('patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)


class MedmentReviewResultUpdateView(View):
    """
    Medment 普通定制复查结果更新视图
    处理右眼和左眼的复查结果保存
    """
    def post(self, request, *args, **kwargs):
        patient_pk = request.POST.get('patient_pk')
        eye_type = request.POST.get('eye_type')  # 'right' 或 'left'

        if not patient_pk:
            messages.error(request, "缺少患者ID")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        try:
            patient = Patient.objects.get(pk=patient_pk)
        except Patient.DoesNotExist:
            messages.error(request, "患者不存在")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        # 获取表单数据
        adaptation_status = request.POST.get('adaptation_status', '')
        post_adjustment = request.POST.get('post_adjustment', '')
        satisfaction = request.POST.get('satisfaction', '')
        satisfaction_level = request.POST.get('satisfaction_level', '')

        # 根据眼别更新对应字段
        if eye_type == 'right':
            patient.medment_right_adaptation_status = adaptation_status
            patient.medment_right_post_adjustment = post_adjustment
            patient.medment_right_satisfaction = satisfaction
            patient.medment_right_satisfaction_level = satisfaction_level
        elif eye_type == 'left':
            patient.medment_left_adaptation_status = adaptation_status
            patient.medment_left_post_adjustment = post_adjustment
            patient.medment_left_satisfaction = satisfaction
            patient.medment_left_satisfaction_level = satisfaction_level

        patient.save()
        messages.success(request, f"{'右眼' if eye_type == 'right' else '左眼'}复查结果保存成功")

        success_url = reverse('patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)

