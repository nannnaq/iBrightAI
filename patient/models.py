from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

EYE_CHOICES = [("left", "左眼"), ("right", "右眼")]


class Patient(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField(default=0)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=20, default="", blank=True, null=True)
    medical_record_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="病历号")
    create_date = models.DateTimeField(auto_now_add=True, null=True, blank=True, help_text="创建时间")

    # 关联创建者
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="创建者", related_name="patients")

    # 导出计数
    export_count = models.IntegerField(default=0, verbose_name="导出次数")

    # Medment 右眼复查信息
    medment_right_adaptation_status = models.CharField(max_length=100, default="", verbose_name="Medment右眼适配情况")
    medment_right_post_adjustment = models.CharField(max_length=100, default="", verbose_name="Medment右眼售后调整")
    medment_right_satisfaction = models.CharField(max_length=100, default="", verbose_name="Medment右眼满意度")
    medment_right_satisfaction_level = models.CharField(max_length=100, default="", verbose_name="Medment右眼满意度等级")

    # Medment 左眼复查信息
    medment_left_adaptation_status = models.CharField(max_length=100, default="", verbose_name="Medment左眼适配情况")
    medment_left_post_adjustment = models.CharField(max_length=100, default="", verbose_name="Medment左眼售后调整")
    medment_left_satisfaction = models.CharField(max_length=100, default="", verbose_name="Medment左眼满意度")
    medment_left_satisfaction_level = models.CharField(max_length=100, default="", verbose_name="Medment左眼满意度等级")

    # Seour 右眼复查信息
    seour_right_adaptation_status = models.CharField(max_length=100, default="", verbose_name="Seour右眼适配情况")
    seour_right_post_adjustment = models.CharField(max_length=100, default="", verbose_name="Seour右眼售后调整")
    seour_right_satisfaction = models.CharField(max_length=100, default="", verbose_name="Seour右眼满意度")
    seour_right_satisfaction_level = models.CharField(max_length=100, default="", verbose_name="Seour右眼满意度等级")

    # Seour 左眼复查信息
    seour_left_adaptation_status = models.CharField(max_length=100, default="", verbose_name="Seour左眼适配情况")
    seour_left_post_adjustment = models.CharField(max_length=100, default="", verbose_name="Seour左眼售后调整")
    seour_left_satisfaction = models.CharField(max_length=100, default="", verbose_name="Seour左眼满意度")
    seour_left_satisfaction_level = models.CharField(max_length=100, default="", verbose_name="Seour左眼满意度等级")

    # Tomey 右眼复查信息
    tomey_right_adaptation_status = models.CharField(max_length=100, default="", verbose_name="Tomey右眼适配情况")
    tomey_right_post_adjustment = models.CharField(max_length=100, default="", verbose_name="Tomey右眼售后调整")
    tomey_right_satisfaction = models.CharField(max_length=100, default="", verbose_name="Tomey右眼满意度")
    tomey_right_satisfaction_level = models.CharField(max_length=100, default="", verbose_name="Tomey右眼满意度等级")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '患者'
        verbose_name_plural = verbose_name


class BasicParams(models.Model):
    LENS_TYPE_CHOICES = [
        ("s", "s"),
        ("PRO", "PRO"),
        ("A", "A"),
    ]
    CUSTOM_TYPE_CHOICES = [
        ("0", "Medment普通定制"),
        ("1", "Medment四轴定制"),
        ("2", "Seour普通定制"),
        ("3", "Seour四轴定制"),
        ("4", "tomey普通定制"),
        ("5", "tomey四轴定制"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="患者", help_text="患者")
    custom_type = models.CharField(max_length=5, default="0", choices=CUSTOM_TYPE_CHOICES, help_text="定制类型",
                                   verbose_name="定制类型", )
    eye = models.CharField(choices=EYE_CHOICES, max_length=5, help_text="眼", verbose_name="眼")
    lens_type = models.CharField(max_length=5, choices=LENS_TYPE_CHOICES, default='s', help_text="镜片类型",
                                 verbose_name="镜片类型")
    ring_cus = models.CharField(max_length=50, blank=True, null=True)  # 允许为空
    ac_cus = models.CharField(max_length=50, blank=True, null=True)
    overall_diameter = models.FloatField(max_length=10, default=0, help_text="总直径",
                                         verbose_name="总直径")
    optical_zone_diameter = models.FloatField(max_length=10, default=0, help_text="光学区直径",
                                              verbose_name="光学区直径")
    ac_arc_start = models.FloatField(max_length=10, null=True, blank=True, help_text="AC弧范围起始值",
                                     verbose_name="AC弧范围起始值")
    ac_arc_end = models.FloatField(max_length=10, null=True, blank=True, help_text="AC弧范围结束值",
                                   verbose_name="AC弧范围结束值")
    ac_arc_width = models.FloatField(max_length=10, default=0, help_text="AC弧径宽,AC弧范围结束值-起始值/2",
                                     verbose_name="AC弧径宽")
    mirror_degree = models.DecimalField(max_digits=8, decimal_places=4, default=0, help_text="球镜度",
                                        verbose_name="球镜度")
    cylindrical_power = models.DecimalField(max_digits=8, decimal_places=4, default=0, help_text="柱镜度",
                                            verbose_name="柱镜度", null=True, blank=True)
    overpressure = models.DecimalField(max_digits=8, decimal_places=4, default=0, help_text="过压量",
                                       verbose_name="过压量", null=True, blank=True)
    glass_color = models.CharField(max_length=5, default='', help_text="镜片颜色", verbose_name="镜片颜色")
    center_height = models.CharField(max_length=5, default='', help_text="中心厚度", verbose_name="中心厚度")
    corneal_file = models.FileField(upload_to='uploads/corneal_1', null=True, blank=True, help_text="角膜地形图文件1",
                                    verbose_name="角膜地形图文件1")
    corneal_file2 = models.FileField(upload_to='uploads/corneal_2', null=True, blank=True, help_text="角膜地形图文件2",
                                     verbose_name="角膜地形图文件2")
    create_date = models.DateTimeField(auto_now_add=True, null=True, blank=True, help_text="创建时间",
                                       verbose_name="创建时间")
    update_date = models.DateTimeField(auto_now=True, null=True, blank=True, help_text="更新时间",
                                       verbose_name="更新时间")

    # 复查相关字段（数据库中存在但之前未定义）
    adaptation_status = models.CharField(max_length=100, default="", verbose_name="适配情况")
    post_adjustment = models.CharField(max_length=100, default="", verbose_name="售后调整")
    review_date = models.DateField(null=True, blank=True, verbose_name="复查日期")
    satisfaction_level = models.CharField(max_length=100, default="", verbose_name="满意度等级")

    def __str__(self):
        return f'{self.patient.name}-{self.eye} basic'

    class Meta:
        verbose_name = '基本参数'
        verbose_name_plural = verbose_name
        # ==========================================================
        # =============   ↓↓↓ 新增：添加复合索引 ↓↓↓   ================
        # ==========================================================
        indexes = [
            models.Index(fields=['patient', 'eye', 'custom_type']),
        ]
        # ==========================================================
        # =============   ↑↑↑ 新增：添加复合索引 ↑↑↑   ================
        # ==========================================================

class CornealTopography(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="患者", help_text="患者")
    BasicParams = models.ForeignKey(BasicParams, on_delete=models.CASCADE, null=True, blank=True,
                                    verbose_name="基本参数", help_text="基本参数")
    eye = models.CharField(choices=EYE_CHOICES, max_length=5, verbose_name="眼", help_text="眼")
    flat_k = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="平k", verbose_name="平k")
    steep_k = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="陡k", verbose_name="陡k")
    plane_e = models.CharField(max_length=10, default='', help_text="平面e", verbose_name="平面e")
    plane_angle = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="平角度",
                                      verbose_name="平角度")
    inclined_surface_e = models.CharField(max_length=10, default='', help_text="斜面e", verbose_name="斜面e")
    inclined_angle = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="斜角度",
                                         verbose_name="斜角度")
    delta_k = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="delta K",
                                  verbose_name="delta K")
    img_corneal_height = models.ImageField(upload_to='uploads/CornealHeight', null=True, blank=True,
                                           help_text="高度图", verbose_name="高度图")
    img_tangential_curvature = models.ImageField(upload_to='uploads/TangentialCurvature', null=True, blank=True,
                                                 help_text="切向曲率图",
                                                 verbose_name="切向曲率图")
    
    # ==========================================================
    # =============   ↓↓↓ 新增的字段 ↓↓↓   =====================
    # ==========================================================
    raw_data_tangential = models.JSONField(null=True, blank=True, verbose_name="切向曲率图原始数据")
    raw_data_axial = models.JSONField(null=True, blank=True, verbose_name="轴向曲率图原始数据")
    # ==========================================================
    # =============   ↑↑↑ 新增的字段 ↑↑↑   =====================
    # ==========================================================

    img_axial_curvature = models.ImageField(upload_to='uploads/AxialCurvature', null=True, blank=True,
                                            help_text="轴向曲率图",
                                            verbose_name="轴向曲率图")
    img_tear_film_quality = models.ImageField(upload_to='uploads/TearFilmQualityData', null=True, blank=True,
                                              help_text="泪膜质量图",
                                              verbose_name="泪膜质量图")
    create_date = models.DateTimeField(auto_now_add=True, null=True, blank=True, help_text="创建时间",
                                       verbose_name="创建时间")
    update_date = models.DateTimeField(auto_now=True, null=True, blank=True, help_text="更新时间",
                                       verbose_name="更新时间")

    def __str__(self):
        return f'{self.patient.name}-{self.eye} topography'

    class Meta:
        verbose_name = '角膜地形图'
        verbose_name_plural = verbose_name
        # ==========================================================
        # =============   ↓↓↓ 新增：为外键和筛选字段添加索引 ↓↓↓  ======
        # ==========================================================
        indexes = [
            models.Index(fields=['patient', 'eye', 'BasicParams']),
        ]
        # ==========================================================
        # =============   ↑↑↑ 新增：为外键和筛选字段添加索引 ↑↑↑  ======
        # ==========================================================

class ACCustomization(models.Model):
    side_arc_position_CHOICE = [(16.8, "+2"), (12.8, "+1"), (8.8, "0"), (4.8, "-1")]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="患者", help_text="患者")
    BasicParams = models.ForeignKey(BasicParams, on_delete=models.CASCADE, null=True, blank=True,
                                    verbose_name="基本参数", help_text="基本参数")
    eye = models.CharField(choices=EYE_CHOICES, max_length=5, verbose_name="眼", help_text="眼")
    ac_arc_k1 = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="AC弧K1",
                                    verbose_name="AC弧K1")
    ac_arc_k2 = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="AC弧K2",
                                    verbose_name="AC弧K2", null=True, blank=True)
    ac_arc_k3 = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="AC弧K3",
                                    verbose_name="AC弧K3", null=True, blank=True)
    ac_arc_k4 = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="AC弧K4",
                                    verbose_name="AC弧K4", null=True, blank=True)
    steep_k_calculate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="陡K计算结果",
                                            verbose_name="陡K计算结果", null=True, blank=True)
    axis = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="轴位", verbose_name="轴位",
                               null=True, blank=True)
    reverse_arc_height = models.CharField(max_length=5, default="", help_text="反转弧矢高", verbose_name="反转弧矢高")
    reverse_arc_width = models.CharField(max_length=5, default="", help_text="反转弧径宽", verbose_name="反转弧径宽")
    base_arc_diameter = models.CharField(max_length=5, default="", help_text="基弧直径", verbose_name="基弧直径")
    side_arc_position = models.FloatField(choices=side_arc_position_CHOICE, max_length=5, default=8.8,
                                          help_text="边弧档位", verbose_name="边弧档位")
    base_arc_curvature_radius = models.DecimalField(max_digits=12, decimal_places=6, default=0,
                                                    help_text="基弧曲率半径",
                                                    verbose_name="基弧曲率半径")
    reverse_arc_curvature_radius = models.CharField(max_length=5, default="", help_text="反转弧曲率半径",
                                                    verbose_name="反转弧曲率半径")
    adaptation_arc_curvature_radius = models.CharField(max_length=5, default="", help_text="适配弧径宽",
                                                       verbose_name="适配弧径宽")
    adaptable_arc_width = models.CharField(max_length=5, default="", help_text="配适弧径度", verbose_name="配适弧径度")
    ace_position = models.DecimalField(max_digits=5, decimal_places=2, help_text="ACe档位", verbose_name="ACe档位")
    tac_position = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Tac档位",
                                       verbose_name="Tac档位", null=True, blank=True)
    tear_film_data = models.JSONField(default=dict, help_text="泪膜图数据", verbose_name="泪膜图数据")
    ai_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="AI码")
    fluorescent_staining_image = models.ImageField(upload_to='fa_image', null=True,
                                                   blank=True, help_text="荧光染色图", verbose_name="荧光染色图")
    qrcode_medment_accustomization = models.ImageField(upload_to='qrcode_medment_accustomization', null=True,
                                                       blank=True, help_text="二维码", verbose_name="二维码")
    create_date = models.DateTimeField(auto_now_add=True, null=True, blank=True, help_text="创建时间",
                                       verbose_name="创建时间")
    update_date = models.DateTimeField(auto_now=True, null=True, blank=True, help_text="更新时间",
                                       verbose_name="更新时间")

    def __str__(self):
        return f'{self.patient.name}-{self.eye} ac'

    class Meta:
        verbose_name = '定制信息'
        verbose_name_plural = verbose_name


class ReviewResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="患者", help_text="患者")
    BasicParams = models.ForeignKey(BasicParams, on_delete=models.CASCADE, null=True, blank=True,
                                    verbose_name="基本参数",
                                    help_text="基本参数")
    eye = models.CharField(choices=EYE_CHOICES, max_length=5, verbose_name="眼", help_text="眼")
    adaptation_status = models.CharField(max_length=100, default="", help_text="适配情况", verbose_name="适配情况")
    post_adjustment = models.CharField(max_length=100, default="", help_text="售后调整", verbose_name="售后调整")
    satisfaction_level = models.CharField(max_length=100, default="", help_text="售后原因", verbose_name="售后原因")
    review_date = models.DateField(auto_now_add=True, help_text="满意度", verbose_name="满意度调查日期")
    create_date = models.DateField(auto_now_add=True, null=True, blank=True, help_text="创建时间",
                                   verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, help_text="更新时间", verbose_name="更新时间")

    def __str__(self):
        return f'{self.patient.name}-{self.eye} review result'

    class Meta:
        verbose_name = '复查结果'
        verbose_name_plural = verbose_name


class CornealTopographyFile(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '角膜地形图文件'
        verbose_name_plural = verbose_name


class RelationshipTable(models.Model):
    base_arc_curvature_radius = models.DecimalField(max_digits=12, decimal_places=6, default=0,
                                                    help_text="基弧曲率半径",
                                                    verbose_name="基弧曲率半径")
    lens_type_number = models.CharField(max_length=5, default="", help_text="映射镜片类型对应的数值",
                                        verbose_name="映射镜片类型对应的数值")
    belongs_level = models.SmallIntegerField(default=0, help_text="所属档位", verbose_name="所属档位")
    lens_type = models.CharField(max_length=255, help_text="镜片类型", verbose_name="镜片类型")

    class Meta:
        verbose_name = 'A.PRO系列曲率半径映射表'
        verbose_name_plural = verbose_name
