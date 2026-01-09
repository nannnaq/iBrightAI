from django.urls import path
from patient.views.patients import (
    PatientBasicInfor,
    PatientUpdateView,
    CaseCreateView,
    CaseListView,
    CaseDeleteView
)
from patient.views.medment import (
    CustomizeView,
    CornealTopographyUpdateView,
    # ParamsDetailView,
    CustomizedUpdateView,
    BasicParasCreateView,
    SpecialProgressBarView,
    UpdateParameter,
    ErrorView,
    CustomizeViewCreate,
    MedmentReviewResultUpdateView,
)

from patient.views.other import (
    ReviewResultUpdateView,
    ExportCustomizedView,
    ImportCustomizedView,
    ExportReviewedView,
    ImportReviewedView,
    ParamsModifyView,
    GenerateExportDataView,
    UpdateExportCountView,

)

from patient.views.seour import (
    SeourBasicParasCreateView,
    SeourSpecialProgressBarView,
    SeourUpdateParameter,
    SeourPatientBasicInfor,
    SeourCustomizeView,
    SeourCustomizeViewCreate,
    SeourCornealTopographyUpdateView,
    SeourReviewResultUpdateView,
)

from patient.views.tomey import (
    TomeyBasicParasCreateView,
    TomeySpecialProgressBarView,
    TomeyPatientBasicInfor,
    TomeyCustomizeView,
    TomeyCustomizeViewCreate,
    TomeyUpdateParameter,
)

from patient.views import medment # <-- 确保导入了 medment
from patient.views import printing
from patient.views.printing import PrintPatientListView, GeneratePrintReportView
from patient.views.printing import PrintPatientListView, GeneratePrintReportView, PrintDetailView

from patient.views import config
from patient.views.tomey import ProcessTomeyDataView

urlpatterns = [
    # ==========================================================
    # =============   ↓↓↓ 新增的 API 路径 ↓↓↓   ==================
    # ==========================================================
    # 自动读取.mxf文件的API
    path('api/process-mxf/', medment.process_mxf_api_view, name='process_mxf_api'),
    # 导出患者数据的API
    path('api/generate-export-data/', GenerateExportDataView.as_view(), name='generate_export_data'),
    # 更新导出次数的API
    path('api/update-export-count/', UpdateExportCountView.as_view(), name='update_export_count'),
    # ==========================================================
    # =============   ↑↑↑ 新增的 API 路径 ↑↑↑   ==================
    # ==========================================================
    # path("patient/", PatientCreateView.as_view(), name="patient"),
    # 病人增删改查
    path('patient/<int:pk>/', PatientBasicInfor.as_view(), name='patient_detail'),
    path("patient_history/", CaseListView.as_view(), name="patient_list"),
    path("patient_update/<int:pk>", PatientUpdateView.as_view(), name="patient_update"),
    path("create_case/", CaseCreateView.as_view(), name="create_case"),
    path("patient/delete/<int:pk>/", CaseDeleteView.as_view(), name="patient_delete"),

    # medment定制方法-普通定制
    path("create_basic/", BasicParasCreateView.as_view(), name="basic_infor"),
    # medment定制方法-普通定制-特殊处理AC\环曲定制特殊处理
    path("special_progress", SpecialProgressBarView.as_view(), name="special_progress_bar"),
    path("update_params/", UpdateParameter.as_view(), name="update_params"),
    # medment定制方法-普通定制-复查结果更新
    path("medment_review_update/", MedmentReviewResultUpdateView.as_view(), name="medment_review_update"),
    # medment定制方法-四轴定制
    path("4_customize/<int:pk>/", CustomizeView.as_view(), name="4_customize"),
    path("create_4_customize/", CustomizeViewCreate.as_view(), name="create_4_customize"),
    # memdent通用-修改角膜地形图
    path("updatecorneal/<int:pk>/", CornealTopographyUpdateView.as_view(), name="updatecorneal"),


    # seour定制方法-普通定制
    path("seour_create_basic/", SeourBasicParasCreateView.as_view(), name="seour_basic_infor"),
    path("seour_patient/<int:pk>/", SeourPatientBasicInfor.as_view(), name='seour_patient_detail'),
    # seour定制方法-普通定制-特殊处理AC\环曲定制特殊处理
    path("seour_special_progress", SeourSpecialProgressBarView.as_view(), name="seour_special_progress_bar"),
    path("seour_update_params/", SeourUpdateParameter.as_view(), name="seour_update_params"),
    # seour定制方法-普通定制-复查结果更新
    path("seour_review_update/", SeourReviewResultUpdateView.as_view(), name="seour_review_update"),
    # seour定制方法-四轴定制
    path("seour_create_4_customize/", SeourCustomizeViewCreate.as_view(), name="seour_create_4_customize"),
    path("seour_4_customize/<int:pk>/", SeourCustomizeView.as_view(), name="seour_4_customize"),
    # seour通用-修改角膜地形图
    path("seour_updatecorneal/<int:pk>/", SeourCornealTopographyUpdateView.as_view(), name="seour_updatecorneal"),


    # tomey定制方法-普通定制
    path("tomey_create_basic/", TomeyBasicParasCreateView.as_view(), name="tomey_basic_infor"),
    path("tomey_patient/<int:pk>/", TomeyPatientBasicInfor.as_view(), name='tomey_patient_detail'),
    # tomey定制方法-普通定制-特殊处理AC\环曲定制特殊处理
    path("tomey_special_progress", TomeySpecialProgressBarView.as_view(), name="tomey_special_progress_bar"),
    path("tomey_update_params/", TomeyUpdateParameter.as_view(), name="tomey_update_params"),
    # tomey定制方法-四轴定制
    path("tomey_create_4_customize/", TomeyCustomizeViewCreate.as_view(), name="tomey_create_4_customize"),
    path("tomey_4_customize/<int:pk>/", TomeyCustomizeView.as_view(), name="tomey_4_customize"),


    # 错误页面
    path('error/', ErrorView.as_view(), name='error_page'),
    # path("4_customize_params_detail/<int:pk>/", ParamsDetailView.as_view(), name="4_customize_params_detail"),
    path("4_customized_update/<int:pk>/", CustomizedUpdateView.as_view(), name="4_customized_update"),
    # path("acc_customize/<int:patient_id>/", ACCustomizationUpdateView.as_view(), name="customize_detail_modify",),
    # path(
    #     "ac_customization/",
    #     ACCustomizationCreateView.as_view(),
    #     name="ac_customization",
    # ),

    # 复查、导入、导出都暂无
    path(
        "review_result/<int:pk>/",
        ReviewResultUpdateView.as_view(),
        name="review_result",
    ),
    path("export_customized/", ExportCustomizedView.as_view(), name="export_customized"),
    path("import_customized/", ImportCustomizedView.as_view(), name="import_customized"),
    path("export_reviewed/", ExportReviewedView.as_view(), name="export_reviewed"),
    path("import_reviewed/", ImportReviewedView.as_view(), name="import_reviewed"),
    path("params_modify/<int:pk>/", ParamsModifyView.as_view(), name="params_modify"),
    # 打印
    path("print/", PrintPatientListView.as_view(), name="print_page"),
    path("print/generate/", GeneratePrintReportView.as_view(), name="generate_print_report"),
    path("print_detail/<int:pk>/", PrintDetailView.as_view(), name="print_detail_page"),
    path("settings/", config.SettingsView.as_view(), name="settings_page"),
    path('api/process-tomey-data/', ProcessTomeyDataView.as_view(), name='process_tomey_data'),
]
