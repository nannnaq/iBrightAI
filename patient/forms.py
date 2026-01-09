import re
from django import forms
from .models import Patient, CornealTopography, ACCustomization, ReviewResult, BasicParams, CornealTopographyFile
from decimal import Decimal


class BootStrapModelForm(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', "placeholder": '请输入%s' % field.label})


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "name",
            "birth_date",
            "gender",
            "phone",
            "age",
            "medical_record_number"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', "placeholder": '请输入%s' % field.label})
            self.fields['phone'].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # 仅当 phone 字段有值 (不为空) 时，才进行正则表达式校验
        if phone and not re.match(r'^1[3-9]\d{9}$', phone):
            raise forms.ValidationError("请输入有效的手机号码")
        
        # 无论 phone 是否为空，都要返回它的值
        return phone


class BasicParamsForm(forms.ModelForm):
    class Meta:
        model = BasicParams
        fields = ["patient", "eye", "lens_type", "ring_cus", "ac_cus", "overall_diameter", "optical_zone_diameter",
                  "ac_arc_width", "mirror_degree", "cylindrical_power", "overpressure", "corneal_file", "corneal_file2",
                  "ac_arc_start", "ac_arc_end"]

    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data)
        ac_arc_start_result = float(cleaned_data.get('optical_zone_diameter')) + 1.6
        ac_arc_end_result = float(cleaned_data.get('overall_diameter')) - 0.5 * 2
        cleaned_data['ac_arc_start'] = round(ac_arc_start_result / 2, 2)
        cleaned_data['ac_arc_end'] = ac_arc_end_result / 2
        return cleaned_data

    def save(self, commit=True, custom_type=None):
        instance = super().save(commit=False)
        # 设置额外的值
        if custom_type:
            instance.custom_type = custom_type

        # 如果 commit=True，则保存到数据库
        if commit:
            instance.save()
        return instance

    def clean_corneal_file(self):
        corneal_file = self.cleaned_data.get('corneal_file')
        if corneal_file:
            return corneal_file
        else:
            raise forms.ValidationError("请上传文件")



class CornealTopographyForm(forms.ModelForm):
    class Meta:
        model = CornealTopography
        fields = ["plane_e", "inclined_surface_e"]


class ACCustomizationForm(forms.ModelForm):
    class Meta:
        model = ACCustomization
        fields = []


class ReviewResultForm(forms.ModelForm):
    class Meta:
        model = ReviewResult
        fields = ["eye", "adaptation_status", "post_adjustment", "satisfaction_level"]


class CornealTopographyFileForm(forms.ModelForm):
    class Meta:
        model = CornealTopographyFile
        fields = ["patient", "file"]


class ParamsModifyForm(BootStrapModelForm, forms.ModelForm):
    class Meta:
        model = ACCustomization
        fields = ["id", "ac_arc_k1", "ac_arc_k2", "ac_arc_k3", "ac_arc_k4", "base_arc_curvature_radius", "tac_position",
                  "steep_k_calculate", "axis", "ace_position", "reverse_arc_height", "side_arc_position", ]

    def clean_steep_k_calculate(self):
        steep_k_calculate = self.cleaned_data['steep_k_calculate']
        tac_position = self.cleaned_data['tac_position']
        if tac_position or tac_position == 0:
            print(f"tac_position:{tac_position}")
            ac_arc_k1 = self.cleaned_data['ac_arc_k1']
            steep_k_calculate = float(ac_arc_k1) + float(tac_position)
            return steep_k_calculate
        else:
            return steep_k_calculate

