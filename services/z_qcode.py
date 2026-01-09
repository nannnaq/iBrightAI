import qrcode
import matplotlib.pyplot as plt
from django.conf import settings
import uuid
import os
from pathlib import Path

dirs = Path(settings.MEDIA_ROOT)


# 生成二维码并保存
def txt_to_qrcode(input_data, output_image="qrcode.png"):
    # 读取文本内容
    text_content = input_data

    # 创建二维码对象
    qr = qrcode.QRCode(
        version=1,  # 控制尺寸（1-40）
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # 容错率
        box_size=10,  # 每个格子的像素大小
        border=4,  # 二维码边距
    )

    # 添加文本数据
    qr.add_data(text_content)
    qr.make(fit=True)

    # 生成二维码图像
    img = qr.make_image(fill_color="black", back_color="white")

    # 保存图像
    uuid_id = uuid.uuid4()

    # 确保目录存在并保存图片
    fa_image_dir = dirs / "qrcode_medment_accustomization"
    if not os.path.exists(fa_image_dir):
        os.makedirs(fa_image_dir)

    save_dir = dirs / "qrcode_medment_accustomization" / f"{uuid_id}.png"
    save_dir_path = os.path.join("qrcode_medment_accustomization", f"{uuid_id}.png")
    img.save(save_dir)
    print(f"二维码已保存至: {save_dir_path}")

    # 16. 显示结果
    # plt.tight_layout()
    # plt.show()

    return {"save_dir_path": save_dir_path}


# 使用示例
if __name__ == "__main__":
    input_txt = "input.txt"  # 替换为你的txt文件路径
    output_png = "text_qrcode.png"  # 输出图片名

    txt_to_qrcode(input_txt, output_png)
