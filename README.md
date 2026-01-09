# hospital-server

@author: 16
@date: 2023/12/1
@description: 眼镜医院管理系统后端

## 项目开发和测试所使用的操作系统
```angular2html
window10 或 macos 13以上
```
## python版本
```angular2html
3.10.16
```
## 安装方式
```
pip install -r requirements.txt
```
## 运行方式
#### 联网运行,服务器运行
1. 通过mysql先创建数据库-创建eyehospital数据库
2. 修改django settings.py文件
```
Database 服务器运行
https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "eyehospital",
        "USER": "root",
        "PASSWORD": "123456",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}
```
3. 修改文件配置路径
```
服务器运行，媒体文件配置
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```
4. 数据库迁移
```
python manage.py makemigrations
python manage.py migrate
python manage.py init
python manage.py createsuperuser
设置管理员账号：admin
设置管理员密码：123456
```
5. 运行项目
```
python manage.py runserver 0.0.0.0:8000
```
6. 打开浏览器,输入http://127.0.0.1:8000/accounts/login/ 
```
根据自己设置的账号密码登录
账号：admin
密码：123456
```

#### 本地运行
1. 数据库配置
```
# 本地运行,数据库配置修改为使用
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'db.sqlite3')),
    }
}
```
2. 媒体配置
```
# 本地运行，媒体文件配置
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))
MEDIA_URL = '/media/'
```
3. 配置本地账号密码,通过main.py
```
# 检查并创建超级用户（仅DEBUG模式）
if settings.DEBUG:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        logging.info("创建超级用户admin...")
        User.objects.create_superuser('admin', '', '123456') // 将这里改掉
        logging.info("超级用户创建完成 - 用户名:admin 密码:123456")  // 将这里改掉
```
4. 打包方式(必须win10以上打包)
```
pyinstaller pack.spec
```
5. dist文件中启动exe文件
```
双击GlassesHospital.exe文件启动
```
