import os

from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, ListView, TemplateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from patient.models import Patient, CornealTopography, ACCustomization, ReviewResult, BasicParams
from patient.forms import (
    PatientForm,
    CornealTopographyForm,
    ACCustomizationForm,
    ReviewResultForm,
    BasicParamsForm,
    CornealTopographyFileForm,
)

from patient.views.other import ParamsModifyView

from services.tomey import KBQ
from services.tomey import TomeyExtractor
from services.tomey_4 import KBQ as KBQ_4
from services.zs_tear_film import TearFilmHeightCalculator, FluorescentStaining
from services.z_leimo import TEARFILMDATA

from services.z_qcode import txt_to_qrcode
from patient.views.constants import *

from patient.views.other import *

from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from patient.models import Patient, BasicParams, CornealTopography
from patient.views.other import ParamsModifyView # 引入二次计算逻辑

from services.dixingtu_med_height import parse_topographic_map_data
from services.dixingt_med_qiexiang import parse_qiexiang_data
from services.dixingt_med_zhouxiang import parse_zhouxiang_data
from services.dixingt_med_leimozhiliang import parse_leiomozhilaing_data
# tms文件解析视图
@method_decorator(csrf_exempt, name='dispatch')
class ProcessTomeyDataView(View):
    def post(self, request):
        try:
            # ==========================================
            # 1. 接收基础数据 & 文件
            # ==========================================
            patient_id = request.POST.get('patient_id')
            eye = request.POST.get('eye', 'right')
            
            # 辅助函数：安全获取浮点数
            def get_float(k, d=0):
                try: 
                    val = request.POST.get(k)
                    return float(val) if val else d
                except: return d

            # 辅助函数：安全获取 Decimal/String (优先取传入值，否则为0)
            def get_decimal(k):
                val = request.POST.get(k)
                if val is None or val == '':
                    return 0
                return val

            # 地形图参数
            flat_k = get_float('flat_k')
            steep_k = get_float('steep_k')
            plane_angle = get_float('plane_angle')
            inclined_angle = get_float('inclined_angle')
            delta_k = get_float('delta_k')
            
            # 用户表单参数
            overall_diameter = get_float('overall_diameter', 10.6)
            optical_zone_diameter = get_float('optical_zone_diameter', 6.0)
            
            # 获取球镜、柱镜、过压量 (从前端回传的值)
            mirror_degree = get_decimal('mirror_degree')
            cylindrical_power = get_decimal('cylindrical_power')
            overpressure = get_decimal('overpressure')

            # 文件
            radius_file = request.FILES.get('radius_file')
            height_file = request.FILES.get('height_file')
            
            if not radius_file or not height_file:
                return JsonResponse({'success': False, 'error': '缺少半径或高度数据文件'})

            # ==========================================
            # 2. 创建或更新 BasicParams (关键修改)
            # ==========================================
            patient = get_object_or_404(Patient, pk=patient_id) if patient_id else None
            
            # 计算 AC弧径宽
            ac_arc_width_val = get_float('ac_arc_width', 0)
            ac_arc_start = optical_zone_diameter / 2 + 0.8
            ac_arc_end = overall_diameter / 2 - 0.5

            if ac_arc_width_val == 0:
                ac_arc_width_val = ac_arc_end - ac_arc_start


            basic_param, created = BasicParams.objects.update_or_create(
                patient=patient,
                eye=eye,
                custom_type='4', # 4 = Tomey普通定制
                defaults={
                    'lens_type': 'PRO',
                    'overall_diameter': overall_diameter,
                    'optical_zone_diameter': optical_zone_diameter,
                    'ac_arc_width': ac_arc_width_val,
                    'ac_arc_start': ac_arc_start,
                    'ac_arc_end': ac_arc_end,
                    'mirror_degree': mirror_degree,         # 更新为用户填写的球镜度
                    'cylindrical_power': cylindrical_power, # 更新为用户填写的柱镜度
                    'overpressure': overpressure,           # 更新为用户填写的过压量
                    'corneal_file': radius_file,  
                    'corneal_file2': height_file, 
                }
            )

            # 获取文件绝对路径 (用于KBQ计算)
            rm_file_path = basic_param.corneal_file.path
            ch_file_path = basic_param.corneal_file2.path

            # ==========================================
            # 3. 创建或更新 CornealTopography
            # ==========================================
            # 同样使用 update_or_create
            CornealTopography.objects.update_or_create(
                patient=patient,
                BasicParams=basic_param,
                eye=eye,
                defaults={
                    'flat_k': flat_k,
                    'steep_k': steep_k,
                    'plane_angle': plane_angle,
                    'inclined_angle': inclined_angle,
                    'delta_k': delta_k,
                }
            )

            # ==========================================
            # 4. 智能设计计算 (KBQ算法)
            # ==========================================
            
            # 4.1 平K方向
            try:
                flat_k_result = KBQ(
                    [basic_param.ac_arc_start, basic_param.ac_arc_end],
                    [plane_angle, plane_angle + 180],
                    rm_dat_path=rm_file_path, 
                    ch_dat_path=ch_file_path
                ).main(k_type=0, special_type=False)
            except Exception as e:
                # 捕获算法内部错误，防止崩溃，使用默认值兜底
                print(f"KBQ算法(平K)计算错误: {str(e)}")
                flat_k_result = None

            if flat_k_result and flat_k_result.get('best_data'):
                best_data_flat = flat_k_result['best_data']
                ac_arc_k1 = best_data_flat['K']
                ac_arc_k2 = ac_arc_k1
                ac_arc_k3 = ac_arc_k1
                ac_arc_k4 = ac_arc_k1
                reverse_arc_height = best_data_flat["B"] + 5
                ace_position = best_data_flat['Q']
            else:
                # 如果计算失败，给一个合理的默认值，避免报错
                ac_arc_k1 = flat_k - 1.0
                ac_arc_k2 = ac_arc_k3 = ac_arc_k4 = ac_arc_k1
                reverse_arc_height = -0.05
                ace_position = 0

            # 4.2 陡K方向
            steep_k_calculate = steep_k - 1.0 # 默认值
            try:
                steep_k_result = KBQ(
                    [round(basic_param.ac_arc_start, 2), basic_param.ac_arc_end],
                    [inclined_angle, inclined_angle + 180],
                    rm_dat_path=rm_file_path, 
                    ch_dat_path=ch_file_path
                ).main(k_type=1, pin_q_values=ace_position, pin_b_values=reverse_arc_height-5, special_type=False) # 注意还原B值

                if steep_k_result and steep_k_result.get('best_data'):
                    steep_k_calculate = steep_k_result['best_data']['K']
            except Exception as e:
                print(f"KBQ算法(陡K)计算错误: {str(e)}")

            # 4.3 计算基弧
            try:
                mirror_val = float(mirror_degree or 0)
                overpressure_val = float(overpressure or 0)
                effective_mirror = mirror_val - overpressure_val
                # 避免分母为0
                denominator = flat_k + effective_mirror - 0.75
                if denominator == 0: denominator = 0.001
                base_arc_curvature_radius = 337.5 / denominator
            except Exception:
                base_arc_curvature_radius = 0

            tac_position = abs(steep_k_calculate - ac_arc_k1)
            if tac_position == 0.25:
                tac_position = 0.50
                steep_k_calculate = ac_arc_k1

            # ==========================================
            # 5. 创建或更新定制记录 (ACCustomization)
            # ==========================================
            reverse_arc_width_val = "0.80"
            adaptable_arc_width_val = f"{basic_param.ac_arc_end - basic_param.ac_arc_start:.2f}"

            # 使用 update_or_create 替代 create
            ac_customization, created = ACCustomization.objects.update_or_create(
                patient=patient,
                BasicParams=basic_param,
                eye=eye,
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
                    'side_arc_position': 8.8,
                    'reverse_arc_width': reverse_arc_width_val,
                    'adaptable_arc_width': adaptable_arc_width_val,
                }
            )

            # ==========================================
            # 6. 生成核心图表 (泪膜、荧光、二维码)
            # ==========================================
            
            common_params = {
                'lens_type': basic_param.lens_type,
                'ace_position': float(ace_position),
                'flat_k': float(flat_k),
                'base_arc_curvature_radius': float(base_arc_curvature_radius),
                'side_arc_position': float(ac_customization.side_arc_position),
                'ac_arc_start': float(basic_param.ac_arc_start),
                'ac_arc_end': float(basic_param.ac_arc_end),
                'reverse_arc_height': float(reverse_arc_height),
                'overall_diameter': float(basic_param.overall_diameter),
                'al_type': 4,
                'rm_file': rm_file_path,
                'ch_file': ch_file_path,
            }

            try:
                # 6.1 泪膜图计算
                tear_ping = TearFilmHeightCalculator(
                    optical_zone_diameter=float(optical_zone_diameter),
                    ac_arc_k1=float(ac_arc_k1),
                    degree_list=[float(plane_angle), float(plane_angle + 180)],
                    **common_params
                ).main_calculate()
                C1 = TEARFILMDATA(tear_ping['x'], tear_ping['y1'], tear_ping['y2'])
                
                tear_steep = TearFilmHeightCalculator(
                    optical_zone_diameter=float(optical_zone_diameter),
                    ac_arc_k1=float(steep_k_calculate),
                    degree_list=[float(inclined_angle), float(inclined_angle + 180)],
                    **common_params
                ).main_calculate()
                C2 = TEARFILMDATA(tear_steep['x'], tear_steep['y1'], tear_steep['y2'])

                tear_film_data = {
                    "tear_film_ping_k": C1.main(),
                    "tear_film_steep_k": C2.main(),
                    "ping_k_lens_height": tear_ping['lens_height'],
                    "ping_k_radius_list01": tear_ping['radius_list01'],
                    "ping_k_radius_list02": tear_ping['radius_list02'],
                    "steep_k_lens_height": tear_steep['lens_height'],
                    "steep_k_radius_list01": tear_steep['radius_list01'],
                    "steep_k_radius_list02": tear_steep['radius_list02'],
                    "bc": basic_param.ac_arc_start - 0.8,
                    "rc": basic_param.ac_arc_start,
                    "ac": basic_param.ac_arc_end,
                    "pc": basic_param.overall_diameter / 2,
                }

                # 6.2 更新基弧 (使用 TearFilm 修正后的值)
                final_base_arc_radius = tear_ping["min_base_arc_curvature_radius"]
                ac_customization.base_arc_curvature_radius = final_base_arc_radius
            
            except Exception as e:
                print(f"泪膜图计算错误: {e}")
                # 出错时保持默认值，不中断流程
                tear_film_data = {}
                final_base_arc_radius = base_arc_curvature_radius

            # 6.3 生成 AI 码
            try:
                ai_code = generate_ai_code(basic_param, ac_customization)
            except: ai_code = ""

            # 6.4 生成二维码
            try:
                # 获取文字 Label
                tac_label = str(tac_position)
                for option in tac_options:
                    if option['value'] == float(tac_position): tac_label = option['label']; break
                ace_label = str(ace_position)
                for option in ace_position_options:
                    if option['value'] == float(ace_position): ace_label = option['label']; break

                qrcode_text = (
                    f"客户姓名：{patient.name}\n"
                    f"眼别：{basic_param.get_eye_display()}\n"
                    f"基弧曲率半径：{round(float(final_base_arc_radius), 2)}\n"
                    f"基弧直径：{basic_param.optical_zone_diameter}\n"
                    f"反转弧直径：{basic_param.ac_arc_start * 2:.1f}\n"
                    f"适配弧直径：{basic_param.ac_arc_end * 2}\n"
                    f"总直径：{basic_param.overall_diameter}\n"
                    f"颜色：{'蓝色' if eye == 'left' else '绿色'}\n"
                    f"AI码：{ai_code}"
                )
                qrcode_res = txt_to_qrcode(qrcode_text)
                qrcode_path = qrcode_res.get("save_dir_path")
            except: qrcode_path = None

            # 6.5 保存最终结果 (更新字段)
            ac_customization.tear_film_data = tear_film_data
            ac_customization.ai_code = ai_code
            ac_customization.qrcode_medment_accustomization = qrcode_path
            ac_customization.save()

            # 6.6 生成荧光染色图
            print("开始生成荧光染色图...")
            try:
                fluorescent_staining = FluorescentStaining(
                    degree_list=[float(plane_angle), float(plane_angle + 180), float(inclined_angle), float(inclined_angle + 180)],
                    acc_id=ac_customization.id,
                    overall_diameter=float(basic_param.overall_diameter),
                    optical_zone_diameter=float(basic_param.optical_zone_diameter)
                )
                fluorescent_staining.fluorescent_staining(
                    h1=tear_ping['y1'] if 'tear_ping' in locals() else [],
                    h3=tear_ping['y2'] if 'tear_ping' in locals() else [],
                    h2=tear_steep['y1'] if 'tear_steep' in locals() else [],
                    h4=tear_steep['y2'] if 'tear_steep' in locals() else []
                )
            except Exception as e:
                print(f"荧光图生成错误: {e}")

            return JsonResponse({
                'success': True, 
                'message': 'Tomey 智能定制成功',
                'basic_param_id': basic_param.id,
                'ac_customization_id': ac_customization.id
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class TomeyBasicParasCreateView(CreateView):
    model = BasicParams
    form_class = BasicParamsForm
    # context_object_name = "basic_params"
    template_name = "tomey/tomey_index.html"
    success_url = "/patient/tomey_patient/"

    def form_valid(self, form):
        # 调用父类的 form_valid 方法来保存表单数据并创建对象
        cleaned_data = form.cleaned_data
        patient_pk = cleaned_data.get('patient')
        eye_type = cleaned_data.get('eye')
        patient_pk = patient_pk.pk
        custom_type = "4"  # 定制方式tomey普通定制

        # 检查是否已经存在关联的BasicParams对象
        basic_params_instance = BasicParams.objects.filter(patient=patient_pk, eye=eye_type,custom_type=custom_type).last()
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
            basic_params = form.save(custom_type=custom_type)
            # form.instance.patient = patient_pk  # 确保关联patient
            data = self.calculation_algorithm(patient_pk=patient_pk, eye_type=eye_type, basic_params_id=basic_params.id,
                                              custom_type=custom_type)

            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request,data["data"])

        # 重定向到patient的详情页面
        success_url = reverse('tomey_patient_detail', kwargs={'pk': patient_pk})
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
        success_url = reverse('tomey_patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)

    def calculation_algorithm(self, patient_pk, eye_type, basic_params_id, special_type=False, custom_type="4"):
        # 将保存的数据筛选出来，取出保存文件进行以下计算
        try:
            flat_k = float(self.request.POST.get('flat_k'))
            plane_angle = float(self.request.POST.get('plane_angle'))
            steep_k = float(self.request.POST.get('steep_k'))
            inclined_angle = float(self.request.POST.get('inclined_angle'))
            delta_k = abs(steep_k - flat_k)
        except Exception as e:
            return {"data": f"请完整填写角膜数据", "state": 0, }

        # print(flat_k, plane_angle, steep_k, inclined_angle, delta_k)
        basic_params_data = BasicParams.objects.filter(id=basic_params_id, custom_type=custom_type).last()
        rm_file = basic_params_data.corneal_file
        ch_file = basic_params_data.corneal_file2
        # 保存文件
        if rm_file and ch_file:
            # 根据文件，计算角膜地形图

            rm_file = os.path.join(settings.MEDIA_ROOT, str(rm_file))
            rm_file = os.path.normpath(rm_file)

            ch_file = os.path.join(settings.MEDIA_ROOT, str(ch_file))
            ch_file = os.path.normpath(ch_file)

            try:
                parse_data = TomeyExtractor(rm_dat_path=rm_file, ch_dat_path=ch_file)
            except:
                return {"data": "角膜地形图数据非当前左/右眼文件，请更换角膜地形图文件", "state": 0, }

            flat_k = flat_k
            plane_angle = plane_angle
            steep_k = steep_k
            inclined_angle = inclined_angle
            delta_k = delta_k

            # 计算定制参数信息
            # print(f"平K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}",
            #       f"{[inclined_angle, inclined_angle + 180]}", )

            # 计算平K方向
            try:
                flat_k_com_result = KBQ([basic_params_data.ac_arc_start, basic_params_data.ac_arc_end],
                                        [plane_angle, plane_angle + 180],
                                        rm_dat_path=rm_file, ch_dat_path=ch_file).main(k_type=0, special_type=special_type)
            except Exception as e:
                return {"data": f"{e}", "state": 0, }

            # print(f"平k:{flat_k_com_result}")
            ac_arc_k1 = flat_k_com_result['best_data']['K']
            ac_arc_k2 = flat_k_com_result['best_data']['K']
            ac_arc_k3 = flat_k_com_result['best_data']['K']
            ac_arc_k4 = flat_k_com_result['best_data']['K']
            reverse_arc_height = flat_k_com_result['best_data']["B"] + 5
            ace_position = flat_k_com_result['best_data']['Q']

            # 计算陡K方向
            # print(f"陡K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}, "
            #       f"{[inclined_angle, inclined_angle + 180]}, "
            #       f"{flat_k_com_result['best_data']['Q']}",
            #       f"{flat_k_com_result['best_data']['B']}")

            # 计算陡K，将平k计算的Q和B给定，只遍历k值，寻找最佳k值
            try:
                steep_k_com_result = KBQ([round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end],
                                         [inclined_angle, inclined_angle + 180],
                                         rm_dat_path=rm_file, ch_dat_path=ch_file).main(k_type=1,
                                                                     pin_q_values=flat_k_com_result['best_data']['Q'],
                                                                     pin_b_values=flat_k_com_result['best_data']["B"],
                                                                     special_type=special_type)
            except Exception as e:
                return {"data": f"{e}", "state": 0, }

            # print(f"陡k:{steep_k_com_result}")
            steep_k_calculate = steep_k_com_result['best_data']['K']
            base_arc_curvature_radius = 337.5 / (flat_k + float(basic_params_data.mirror_degree) - 0.75)
            tac_position = abs(steep_k_calculate - ac_arc_k1)
            # print(f"tac:{tac_position}")

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
                    'delta_k': delta_k
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
                    # --- ↓↓↓ 3. 保存二维码路径 ↓↓↓ ---
                    # 'qrcode_medment_accustomization': qrcode_path,
                    # --- ↑↑↑ 保存结束 ↑↑↑ ---
                    # --- ↓↓↓ 新增这两行来保存计算结果 ↓↓↓ ---
                    'reverse_arc_width': f"{reverse_arc_width_val:.2f}",
                    'adaptable_arc_width': f"{adaptable_arc_width_val:.2f}",
                    # --- ↑↑↑ 新增结束 ↑↑↑ ---
                }
            )

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
                'al_type': 4,
                'degree_list': [inclined_angle, inclined_angle + 180],
                'rm_file': rm_file,
                "ch_file": ch_file,
            }

            # 计算平K泪膜图
            tear_film_ping_k = TearFilmHeightCalculator(ac_arc_k1=ac_arc_k1, **common_params).main_calculate()
            C1 = TEARFILMDATA(tear_film_ping_k['x'], tear_film_ping_k['y1'], tear_film_ping_k['y2'])
            tear_film_ping_k_data = C1.main()

            # 计算陡K泪膜图
            tear_film_steep_k = TearFilmHeightCalculator(ac_arc_k1=steep_k_calculate, **common_params).main_calculate()
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
                "pc": basic_params_data.overall_diameter / 2,
            }

            # print(tear_film)
            # 拿到 "正确" 的基弧半径 (Value B)
            final_base_arc_radius = tear_film_ping_k["min_base_arc_curvature_radius"]
            create_result.base_arc_curvature_radius = final_base_arc_radius
            tac_label = str(create_result.tac_position)
            for option in tac_options:
                if option['value'] == float(create_result.tac_position): tac_label = option['label']; break
            ace_label = str(create_result.ace_position)
            for option in ace_position_options:
                if option['value'] == float(create_result.ace_position): ace_label = option['label']; break

            ai_code = generate_ai_code(basic_params_data, create_result) # <-- create_result 此时在内存中含有 Value B

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


class TomeySpecialProgressBarView(View):
    def post(self, request, *args, **kwargs):
        # 处理 POST 请求
        # print(request.POST)
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
        success_url = reverse('tomey_patient_detail', kwargs={'pk': patient_pk})
        success_url += f"?success=done&eyes_type={eyes_type}"
        return HttpResponseRedirect(success_url)


class TomeyPatientBasicInfor(DetailView):
    model = Patient
    template_name = "tomey/tomey_index.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.GET.get('pk', 1):
            response['pk'] = 1
            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 基本信息
        left_basic_params = BasicParams.objects.filter(patient=self.object, eye='left', custom_type='4').last()
        right_basic_params = BasicParams.objects.filter(patient=self.object, eye='right', custom_type='4').last()
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


class TomeyCustomizeView(DetailView):
    model = Patient
    template_name = "tomey/tomey_index_4_customize.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.GET.get('pk', 1):
            response['pk'] = 1
            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 基本信息
        left_basic_params = BasicParams.objects.filter(patient=self.object, eye='left', custom_type='5').last()
        right_basic_params = BasicParams.objects.filter(patient=self.object, eye='right', custom_type='5').last()
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


class TomeyCustomizeViewCreate(CreateView):
    # Tomey四轴定制
    model = BasicParams
    form_class = BasicParamsForm
    template_name = "tomey/tomey_index_4_customize.html"
    success_url = "/patient/tomey_4_customize/"

    def form_valid(self, form):
        # 调用父类的 form_valid 方法来保存表单数据并创建对象
        try:
            cleaned_data = form.cleaned_data
            patient_pk = cleaned_data.get('patient')
            eye_type = cleaned_data.get('eye')
            patient_pk = patient_pk.pk
            custom_type = "5"  # 定制方式-Tomey-4轴定制
        except Exception as e:
            return {"data": f"请完整填写角膜数据", "state": 0, }

        # 检查是否已经存在关联的BasicParams对象
        basic_params_instance = BasicParams.objects.filter(patient=patient_pk, eye=eye_type,custom_type=custom_type).last()
        if basic_params_instance:
            # 如果存在，则更新该基本信息对象
            for field, value in cleaned_data.items():
                if hasattr(basic_params_instance, field):
                    setattr(basic_params_instance, field, value)
            basic_params_instance.save()
            # 查出关联对象(角膜地形图+定制参数信息),并更新
            data = self.calculation_algorithm(patient_pk=patient_pk, eye_type=eye_type, basic_params_id=basic_params_instance.id)
            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request, data["data"])

        else:
            # 如果不存在，则创建新对象
            # form.instance.patient = patient_pk  # 确保关联patient
            basic_params = form.save(custom_type=custom_type)
            data = self.calculation_algorithm(patient_pk=patient_pk, eye_type=eye_type, basic_params_id=basic_params.id, custom_type=custom_type)
            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request,data["data"])

        # 重定向到patient的详情页面
        success_url = reverse('tomey_4_customize', kwargs={'pk': patient_pk})
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
        success_url = reverse('tomey_4_customize', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)

    def calculation_algorithm(self, patient_pk, eye_type, basic_params_id, special_type=False, custom_type="5"):
        # 将保存的数据筛选出来，取出保存文件进行以下计算
        flat_k = float(self.request.POST.get('flat_k'))
        plane_angle = float(self.request.POST.get('plane_angle'))
        steep_k = float(self.request.POST.get('steep_k'))
        inclined_angle = float(self.request.POST.get('inclined_angle'))
        delta_k = abs(steep_k - flat_k)

        basic_params_data = BasicParams.objects.filter(id=basic_params_id, custom_type=custom_type).last()
        rm_file = basic_params_data.corneal_file
        ch_file = basic_params_data.corneal_file2
        # 保存文件
        if rm_file and ch_file:
            # 根据文件，计算角膜地形图

            rm_file = os.path.join(settings.MEDIA_ROOT, str(rm_file))
            rm_file = os.path.normpath(rm_file)

            ch_file = os.path.join(settings.MEDIA_ROOT, str(ch_file))
            ch_file = os.path.normpath(ch_file)

            try:
                parse_data = TomeyExtractor(rm_dat_path=rm_file, ch_dat_path=ch_file)
            except:
                return {"data": "角膜地形图数据非当前左/右眼文件，请更换角膜地形图文件", "state": 0, }

            flat_k = flat_k
            plane_angle = plane_angle
            steep_k = steep_k
            inclined_angle = inclined_angle
            delta_k = delta_k

            # 计算定制参数信息
            # print(f"平K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}",
            #       f"{[inclined_angle, inclined_angle + 180]}", )

            # 计算平K方向
            try:
                flat_k_com_result = KBQ_4([basic_params_data.ac_arc_start, basic_params_data.ac_arc_end],
                                          [plane_angle, plane_angle + 90, plane_angle + 180, plane_angle + 270],
                                          rm_dat_path=rm_file, ch_dat_path=ch_file).main(k_type=0, special_type=special_type)
            except ValueError as e:
                return {"data": f"{e}", "state": 0, }

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
            try:
                steep_k_com_result = KBQ_4([round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end],
                                           [plane_angle, plane_angle + 90, plane_angle + 180, plane_angle + 270],
                                           rm_dat_path=rm_file, ch_dat_path=ch_file).main(k_type=1,
                                                                       pin_q_values=flat_k_com_result[0]['best_data']['Q'],
                                                                       pin_b_values=flat_k_com_result[0]['best_data']["B"],
                                                                       special_type=special_type)
            except ValueError as e:
                return {"data": f"{e}", "state": 0, }

            # print(f"陡k:{steep_k_com_result}")
            steep_k_calculate = steep_k_com_result[0]['best_data']['K']
            base_arc_curvature_radius = 337.5 / (flat_k + float(basic_params_data.mirror_degree) - 0.75)
            tac_position = abs(steep_k_calculate - ac_arc_k1)
            # print(f"tac:{tac_position}")

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
                    'delta_k': delta_k
                }
            )

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
                    'base_arc_curvature_radius': base_arc_curvature_radius
                }
            )

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
                'al_type': 5,
                'degree_list': [plane_angle, plane_angle + 90, plane_angle + 180, plane_angle + 270],
                'rm_file': rm_file,
                "ch_file": ch_file,
            }
            # print(f"common_params:{common_params}")

            # 计算平K泪膜图
            tear_film_ping_k = TearFilmHeightCalculator(ac_arc_k1=ac_arc_k1,
                                                        ac_arc_k2=ac_arc_k2,
                                                        ac_arc_k3=ac_arc_k3,
                                                        ac_arc_k4=ac_arc_k4,
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
                base_arc_curvature_radius=tear_film_ping_k["min_base_arc_curvature_radius"],
            )

            if updated:
                return {"data": "参数创建成功", "state": 1, }
            else:
                return {"data": "参数更新成功", "state": 1, }
        else:
            return {"data": "参数更新成功", "state": 1, }


class TomeyUpdateParameter(View):
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
        success_url = reverse('tomey_patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)