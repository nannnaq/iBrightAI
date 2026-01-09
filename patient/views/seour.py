import os

from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, ListView, TemplateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from patient.models import Patient, CornealTopography, ACCustomization, ReviewResult, BasicParams
from django.conf import settings
from patient.forms import (
    PatientForm,
    CornealTopographyForm,
    ACCustomizationForm,
    ReviewResultForm,
    BasicParamsForm,
    CornealTopographyFileForm,
)
from patient.views.other import ParamsModifyView

from services.seour import KBQ
from services.seour import SeourExtractor
from services.seour_4 import KBQ as KBQ_4

from services.zs_tear_film import TearFilmHeightCalculator, FluorescentStaining
from services.z_leimo import TEARFILMDATA

from services.z_qcode import txt_to_qrcode
from patient.views.constants import *
from patient.views.other import *
import numpy as np

class SeourBasicParasCreateView(CreateView):
    model = BasicParams
    form_class = BasicParamsForm
    # context_object_name = "basic_params"
    template_name = "seour/seour_index.html"
    success_url = "/patient/seour_patient/"

    def form_valid(self, form):
        # 调用父类的 form_valid 方法来保存表单数据并创建对象
        cleaned_data = form.cleaned_data
        patient_pk = cleaned_data.get('patient')
        eye_type = cleaned_data.get('eye')
        patient_pk = patient_pk.pk
        custom_type = "2"  # 定制方式Seour普通定制

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

            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request, data["data"])

        else:
            # 如果不存在，则创建新对象
            basic_params = form.save(custom_type=custom_type)
            # form.instance.patient = patient_pk  # 确保关联patient
            data = self.calculation_algorithm(patient_pk=patient_pk, eye_type=eye_type, basic_params_id=basic_params.id,
                                              custom_type=custom_type)

            messages.error(self.request, data["data"]) if data["state"] == 0 else messages.success(self.request,data["data"])


        # 重定向到patient的详情页面
        success_url = reverse('seour_patient_detail', kwargs={'pk': patient_pk})
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
        success_url = reverse('seour_patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)

    def calculation_algorithm(self, patient_pk, eye_type, basic_params_id, special_type=False, custom_type="2"):
        # 将保存的数据筛选出来，取出保存文件进行以下计算
        basic_params_data = BasicParams.objects.filter(id=basic_params_id, custom_type=custom_type).last()

        # 1. 获取总直径和光学区直径
        overall_diameter = float(basic_params_data.overall_diameter)
        optical_zone_diameter = float(basic_params_data.optical_zone_diameter)

        # 处理奇数问题：如果小数点后一位为奇数，减去0.1变成偶数
        def is_odd_decimal(value):
            """检查小数点后一位是否为奇数"""
            return int(round(value * 10)) % 2 == 1

        if is_odd_decimal(overall_diameter):
            overall_diameter = round(overall_diameter - 0.1, 1)
            print(f'[Seour普通定制] 总直径为奇数，调整为偶数: {overall_diameter}')

        if is_odd_decimal(optical_zone_diameter):
            optical_zone_diameter = round(optical_zone_diameter - 0.1, 1)
            print(f'[Seour普通定制] 光学区直径为奇数，调整为偶数: {optical_zone_diameter}')

        # 2. 使用调整后的值重新计算 AC 弧范围
        basic_params_data.ac_arc_start = optical_zone_diameter / 2 + 0.8
        basic_params_data.ac_arc_end = overall_diameter / 2 - 0.5

        # 3. 保存更新后的值到数据库
        basic_params_data.save(update_fields=['ac_arc_start', 'ac_arc_end'])

        data_file = basic_params_data.corneal_file
        # 保存文件
        if data_file:
            # 根据文件，计算角膜地形图
            from services import aop_mxf
            full_path = os.path.join(settings.MEDIA_ROOT, str(data_file))
            full_path = os.path.normpath(full_path)

            try:
                # 1. (新增) 创建一个持久化的 extractor 实例
                #    (SeourExtractor 在 __init__ 时就会自动解析高度和半径数据)
                seour_extractor = SeourExtractor(full_path)

                # 2. (修改) 使用实例获取 parse_data
                parse_data = seour_extractor.parse_eye_data()['KeratometricIndices3mm']

                # 3. (新增) 从实例中获取用于AI码的 50x50 高度数据矩阵
                #    (它在 services/seour.py 的 __init__ 中被加载到 self.height_data)
                raw_data_array = seour_extractor.height_data 

            except Exception as e:
                # (建议添加 traceback 以便调试)
                import traceback
                traceback.print_exc()
                return {"data": "角膜地形图数据非当前左/右眼文件，或文件已损坏", "state": 0, }

            flat_k = float(parse_data['FlatK'])
            plane_angle = int(parse_data['FlatAngle'])
            steep_k = float(parse_data['SteepK'])
            inclined_angle = int(parse_data['SteepAngle'])
            delta_k = abs(flat_k - steep_k)

            # 计算定制参数信息
            # print(f"平K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}",
            #       f"{[inclined_angle, inclined_angle + 180]}", )

            # 计算平K方向
            flat_k_com_result = KBQ([basic_params_data.ac_arc_start, basic_params_data.ac_arc_end],
                                    [plane_angle, plane_angle + 180],
                                    filter_data=full_path).main(k_type=0, special_type=special_type)

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
            steep_k_com_result = KBQ([round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end],
                                     [inclined_angle, inclined_angle + 180],
                                     filter_data=full_path).main(k_type=1,
                                                                 pin_q_values=flat_k_com_result['best_data']['Q'],
                                                                 pin_b_values=flat_k_com_result['best_data']["B"],
                                                                 special_type=special_type)

            # print(f"陡k:{steep_k_com_result}")
            steep_k_calculate = steep_k_com_result['best_data']['K']
            # 获取过压量，乘以-1再参与计算
            overpressure_val = float(basic_params_data.overpressure or 0) * -1
            base_arc_curvature_radius = 337.5 / (flat_k - float(basic_params_data.mirror_degree) - overpressure_val)
            tac_position = abs(steep_k_calculate - ac_arc_k1)
            # print(f"tac:{tac_position}")
            if np.isclose(tac_position, 0.25):
                # 如果TAC是0.25，将TAC设置为0.50,并且陡K=平K
                tac_position = 0.50
                steep_k_calculate = ac_arc_k1 # 确保陡K值也同步更新

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
                'al_type': 2,
                'degree_list': [inclined_angle, inclined_angle + 180],
                'file_path': full_path
            }

            # 计算平K泪膜图
            tear_film_ping_k = TearFilmHeightCalculator(optical_zone_diameter=optical_zone_diameter,ac_arc_k1=ac_arc_k1, **common_params).main_calculate()
            C1 = TEARFILMDATA(tear_film_ping_k['x'], tear_film_ping_k['y1'], tear_film_ping_k['y2'])
            tear_film_ping_k_data = C1.main()

            # 计算陡K泪膜图
            tear_film_steep_k = TearFilmHeightCalculator(optical_zone_diameter=optical_zone_diameter,ac_arc_k1=steep_k_calculate, **common_params).main_calculate()
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


class SeourPatientBasicInfor(DetailView):
    model = Patient
    template_name = "seour/seour_index.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.GET.get('pk', 1):
            response['pk'] = 1
            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 基本信息
        left_basic_params = BasicParams.objects.filter(patient=self.object, eye='left', custom_type='2').last()
        right_basic_params = BasicParams.objects.filter(patient=self.object, eye='right', custom_type='2').last()
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


class SeourCustomizeView(DetailView):
    model = Patient
    template_name = "seour/seour_index_4_customize.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.GET.get('pk', 1):
            response['pk'] = 1
            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 基本信息
        left_basic_params = BasicParams.objects.filter(patient=self.object, eye='left', custom_type='3').last()
        right_basic_params = BasicParams.objects.filter(patient=self.object, eye='right', custom_type='3').last()
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


class SeourCustomizeViewCreate(CreateView):
    # Seour四轴定制
    model = BasicParams
    form_class = BasicParamsForm
    template_name = "seour/seour_index_4_customize.html"
    success_url = "/patient/seour_4_customize/"

    def form_valid(self, form):
        # 调用父类的 form_valid 方法来保存表单数据并创建对象
        cleaned_data = form.cleaned_data
        patient_pk = cleaned_data.get('patient')
        eye_type = cleaned_data.get('eye')
        patient_pk = patient_pk.pk
        custom_type = "3"  # 定制方式-seour-4轴定制

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
        success_url = reverse('seour_4_customize', kwargs={'pk': patient_pk})
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
        success_url = reverse('seour_4_customize', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)

    def calculation_algorithm(self, patient_pk, eye_type, basic_params_id, special_type=False, custom_type="3"):
        # 将保存的数据筛选出来，取出保存文件进行以下计算
        basic_params_data = BasicParams.objects.filter(id=basic_params_id, custom_type=custom_type).last()
        data_file = basic_params_data.corneal_file
        # 保存文件
        if data_file:
            full_path = os.path.join(settings.MEDIA_ROOT, str(data_file))
            full_path = os.path.normpath(full_path)

            try:
                parse_data = SeourExtractor(full_path).parse_eye_data()['KeratometricIndices3mm']
            except:
                return {"data": "角膜地形图数据非当前左/右眼文件，请更换角膜地形图文件", "state": 0, }

            flat_k = float(parse_data['FlatK'])
            plane_angle = int(parse_data['FlatAngle'])
            steep_k = float(parse_data['SteepK'])
            inclined_angle = int(parse_data['SteepAngle'])
            delta_k = abs(flat_k - steep_k)

            # # 计算定制参数信息
            # print(f"平K方向参数：{[round(basic_params_data.ac_arc_start, 2), basic_params_data.ac_arc_end]}",
            #       f"{[inclined_angle, inclined_angle + 180]}", )

            # 计算平K方向
            try:
                flat_k_com_result = KBQ_4([basic_params_data.ac_arc_start, basic_params_data.ac_arc_end],
                                          [plane_angle, plane_angle + 90, plane_angle + 180, plane_angle + 270],
                                          filter_data=full_path).main(k_type=0, special_type=special_type)
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
                                           filter_data=full_path).main(k_type=1,
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
                'al_type': basic_params_data.custom_type,
                'file_path': full_path
            }
            # print(f"common_params:{common_params}")

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
                base_arc_curvature_radius=tear_film_ping_k["min_base_arc_curvature_radius"],
            )

            # # 荧光染色图
            # fluorescent_staining = FluorescentStaining(
            #     degree_list=[plane_angle, plane_angle + 180, inclined_angle, inclined_angle + 180],
            #     acc_id=create_result.id,
            #     overall_diameter=basic_params_data.overall_diameter,
            #     optical_zone_diameter=basic_params_data.optical_zone_diameter, )
            # result = fluorescent_staining.fluorescent_staining(
            #     h1=tear_film_ping_k['y1'],
            #     h3=tear_film_ping_k['y2'],
            #     h2=tear_film_ping_k['y3'],
            #     h4=tear_film_ping_k['y4']
            # )
            # updated = result["updated"]

            if updated:
                return {"data": "参数创建成功", "state": 1, }
            else:
                return {"data": "参数更新成功", "state": 1, }
        else:
            return {"data": "参数更新成功", "state": 1, }


class SeourCornealTopographyUpdateView(UpdateView):
    model = CornealTopography
    form_class = CornealTopographyForm

    def form_valid(self, form):
        patient = self.object.patient
        basic_data = self.object.BasicParams
        patient_pk = patient.id

        # 保存表单数据
        form.save()
        # 重定向到patient的详情页面
        messages.success(self.request, "角膜地形图更新成功")
        if basic_data.custom_type == '2':
            success_url = reverse('seour_patient', kwargs={'pk': patient_pk})
        elif basic_data.custom_type == '3':
            success_url = reverse('seour_4_customize', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)



class SeourSpecialProgressBarView(View):
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
        success_url = reverse('seour_patient_detail', kwargs={'pk': patient_pk})
        success_url += f"?success=done&eyes_type={eyes_type}"
        return HttpResponseRedirect(success_url)


class SeourUpdateParameter(View):
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
        success_url = reverse('seour_patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)


class SeourReviewResultUpdateView(View):
    """
    Seour 普通定制复查结果更新视图
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
            patient.seour_right_adaptation_status = adaptation_status
            patient.seour_right_post_adjustment = post_adjustment
            patient.seour_right_satisfaction = satisfaction
            patient.seour_right_satisfaction_level = satisfaction_level
        elif eye_type == 'left':
            patient.seour_left_adaptation_status = adaptation_status
            patient.seour_left_post_adjustment = post_adjustment
            patient.seour_left_satisfaction = satisfaction
            patient.seour_left_satisfaction_level = satisfaction_level

        patient.save()
        messages.success(request, f"{'右眼' if eye_type == 'right' else '左眼'}复查结果保存成功")

        success_url = reverse('seour_patient_detail', kwargs={'pk': patient_pk})
        return HttpResponseRedirect(success_url)
