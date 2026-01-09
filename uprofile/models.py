from django.db import models
from django.contrib.auth.models import User


# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="用户", help_text="用户")
    fullname = models.CharField(max_length=120, help_text="姓名", verbose_name="姓名")
    position = models.CharField(max_length=120, verbose_name="职位", help_text="职位")
    department = models.CharField(max_length=120, verbose_name="部门", help_text="部门")
    mobile = models.CharField(max_length=20, blank=True, verbose_name="手机", help_text="手机")
    # avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    bio = models.TextField()

    def __str__(self):
        return self.fullname

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
