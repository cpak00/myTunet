# myTunet
清华网助手，官方的速度慢并且容易崩，我这姑且算是做了些改进吧！
# 说明
使用python3，用python2运行应该会出错（大概吧）
使用pyQt做的界面，另外还用到了一些官方库，如果想以python方式运行的话需要安装pyQy5
```
pip install PyQt5
```
另外本项目也可以使用pyInstaller打包，本人之后还使用winRAR做成了自解压文件，可以自动在桌面创建快捷方式，应该还是比较方便的。
打包后的程序是不需要python3环境就可以运行的，会以.exe形式发布
```
pip install pyInstaller
pyInstaller -D -w tunet.py -i tunet.ico
```
# 关于安全性
本程序会把用户名和账户密码（md5加密后的）以明文存储在用户appData目录下，之后的版本应该会改进加密方式，不过好像也无所谓。
