from PyQt5 import QtCore, QtGui, QtWidgets, Qt
import os
import hashlib
import requests
from threading import Thread
from functools import partial
from learning import get_hm_wk_info as hm_wk
import datetime


def usage():
    try:
        post_url = 'http://net.tsinghua.edu.cn/rad_user_info.php'
        resp = requests.post(url=post_url, timeout=0.5).text.split(',')[6]
        return resp
    except requests.exceptions.Timeout as e:
        return -1
    except requests.exceptions.ConnectionError as e:
        return -2


def check():
    post_url = 'http://net.tsinghua.edu.cn/do_login.php'
    data = {'action': 'check_online'}
    return requests.post(url=post_url, data=data).text


def logout():
    post_url = 'http://net.tsinghua.edu.cn/do_login.php'
    data = {'action': 'logout'}
    try:
        resp = requests.post(url=post_url, data=data, timeout=0.5).text
        print(resp)
        return resp
    except Exception as e:
        return {'text', 'error'}


def postRequest(post_url, data):
    r = requests.post(url=post_url, data=data)
    return r.content


def login(userid, userpass):
    post_url = 'http://net.tsinghua.edu.cn/do_login.php'

    data = {
        'action': 'login',
        'username': userid,
        'password': '{MD5_HEX}' + userpass,
        'ac_id': 1,
    }

    # t = Thread(postRequest, args=(post_url, data))
    # t.start()
    postRequest(post_url, data)
    return


class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(QtWidgets.QMainWindow, self).__init__()
        self.setWindowFlags(Qt.Qt.WindowMinimizeButtonHint)
        self.setTray()

        self.mode = 0
        self.school = 0
        self.wifiList = []
        self.triggerList = []

    def get_hmwk(self, userid, userpass):
        previous = self.stateText.text()
        self.changeStateText('正在获取网络学堂信息')
        hm = []
        try:
            hm = hm_wk(userid, userpass)
        except Exception as e:
            self.changeStateText('密码错误')
            return

        f = open('learn.txt', 'wb')
        for h in hm:
            line = h[0] + '\r\n'
            for i in range(1, len(h)):
                line += '\t'
                line += h[i][0] + ' 截止日期：' + h[i][1]
                line += '\r\n'
            line += '\r\n'
            f.write(line.encode())
        f.close()
        os.system('learn.txt')
        self.changeStateText(previous)
        #self.changeStateText(previous)
        #page = QtWidgets.QDialog()
        #page.resize(1920, 1080)
        #page.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        #page.setFixedSize(page.width() + 100, page.height())
        #grim = QtWidgets.QGridLayout(page)
        #row = 0
        #for course in hm:
        #    label_ = QtWidgets.QLabel()
        #    label_.setText(course[0])
        #    grim.addWidget(label_, row, 0)
        #    row += 1
        #    for i in range(1, len(course)):
        #        label = QtWidgets.QLabel()
        #        label.setText(str(course[i][0] + ' 截止日期: ' + course[i][1]))
        #        grim.addWidget(label, row, 1)
        #        row += 1
        #page.setFixedSize(page.width() + 100, page.height())
        #page.exec()
        pass

    def check_learning(self):
        # 检查网络学堂作业
        userid = ''
        if os.path.exists('account'):
            f = open('account', 'rb')
            account = f.read().decode().split('\n')
            f.close()
            if len(account) >= 2:
                userid = account[0]

        userpass = QtWidgets.QInputDialog(self).getText(
            self, '登录', '密码', QtWidgets.QLineEdit.Password)

        if not userpass[1]:
            return
        t = Thread(target=self.get_hmwk, args=(userid, userpass))
        t.start()
        pass

    def quitexec(self):
        confirm = QtWidgets.QMessageBox.question(self.centralwidget, "问题",
                                                 "确定断开网络连接?")
        if confirm == QtWidgets.QMessageBox.Yes:
            t = Thread(target=self.quitAccount)
            t.start()
            # self.quitAccount()
            QtCore.QCoreApplication.instance().quit()

    def closeEvent(self, event):
        confirm = QtWidgets.QMessageBox.question(self.centralwidget, "警告",
                                                 "确定断开网络连接?")
        if confirm == QtWidgets.QMessageBox.Yes:
            self.changeStateText("正在退出...")
            self.quitexec()
            event.accept()
        else:
            event.ignore()

    def quitAccount(self):
        if 'successful' in logout():
            self.changeStateText("已退出登录")
        else:
            self.changeStateText("不在清华网内")

    def checkWeb(self):
        while True:
            try:
                import time
                time.sleep(1)
                resp = requests.get("http://www.baidu.com", timeout=0.5)

                break
            except requests.exceptions.Timeout as e:
                self.changeStateText("网络连接不通")
                return False
                break
            except Exception as e:
                continue

        return True

    def freshWifi(self):
        self.wifiList.clear()
        self.listWidget.clear()
        if not os.path.exists('preference.ini'):
            f = open('preference.ini', 'wb')
            f.close()

        f = open('preference.ini', 'rb')
        content = f.read().decode().split('\n')
        # print(content)
        self.listWidget.doubleClicked.connect(self.connectWifi)

        networkList = os.popen('netsh wlan show networks')
        lines = []
        try:
            lines = networkList.readlines()
        except Exception as e:
            lines = []
        networkList.close()
        networks = []
        for line in lines:
            if 'SSID' in line:
                networks.append(line.split(': ')[1][:-1])
            else:
                continue

        self.connectMenu.clear()
        self.triggerList.clear()
        i = 0
        for net in content:
            if net[1:] in networks:
                self.listWidget.addItem(net)
                self.wifiList.append(net)
                self.triggerList.append(QtWidgets.QAction(self.connectMenu))
                self.triggerList[i].setObjectName("act" + net[1:])
                self.triggerList[i].setText(net)
                self.triggerList[i].triggered.connect(
                    partial(self.connectWifiByName, net))
                self.connectMenu.addAction(self.triggerList[i])
                i += 1

        actFresh = QtWidgets.QAction(self.connectMenu)
        actFresh.triggered.connect(self.freshWifi)
        actFresh.setText("刷新")
        self.connectMenu.addAction(actFresh)

    def upload(self, userid, passwd):
        while True:
            try:
                isonline = (check() == 'online')
                if isonline:
                    self.changeStateText('当前登陆用户:\n' + str(userid) +
                                         "\n已使用%.2fGB" % (int(usage()) / 1e9))
                    self.tray.setToolTip("%s已登陆" % (userid))
                    self.school = 1
                    return
                else:
                    res = login(userid, passwd).decode('utf-8')
                    if 'err' not in res:
                        self.changeStateText('当前登陆用户:\n' + str(
                            userid) + "\n已使用%.2fGB" % (int(usage()) / 1e9))
                        self.tray.setToolTip("%s已登陆" % (userid))
                        self.school = 1
                    else:
                        self.changeStateText('登陆失败,检查用户名和密码!')
                        os.remove('account')
                        return
                break
            except Exception as e:
                continue

    def connectWifi(self, wifi):
        name = wifi.data()
        t = Thread(target=self.connectWifiName, args=(name, ))
        t.start()
        self.changeStateText("正在连接")
        # self.connectWifiName(name)

    def connectWifiByName(self, name):
        # name = act.text()
        t = Thread(target=self.connectWifiName, args=(name, ))
        t.start()
        self.changeStateText(name + "正在连接")
        self.tray.setToolTip(name + "正在连接")
        # self.connectWifiName(name)

    def connectWifiName(self, wifi):
        userid = ''
        passwd = ''

        name = wifi
        if (name[0] == '?'):
            if os.path.exists('account'):
                f = open('account', 'rb')
                account = f.read().decode().split('\n')
                f.close()
                if len(account) >= 2:
                    userid = account[0]
                    passwd = account[1]
                    response = os.popen('netsh wlan connect ' +
                                        name[1:]).readlines()
                    self.changeStateText(name[1:] + '\n' + response[0] +
                                         '检测到清华网,正在登陆')

                    # t1 = Thread(target=self.upload, args=(userid, passwd))
                    # t1.start()
                    self.upload(userid, passwd)

                else:
                    dialog = QtWidgets.QMessageBox.warning(
                        self, "警告", "没有登录账户信息", QtWidgets.QMessageBox.Yes)
                    dialog.exec()

            else:
                f = open('account', 'wb')
                f.close()
                dialog = QtWidgets.QMessageBox.warning(
                    self, "警告", "没有登录账户信息", QtWidgets.QMessageBox.Yes)
                dialog.exec()

        elif name[0] == '!':
            response = os.popen('netsh wlan connect ' + name[1:]).readlines()
            self.changeStateText(response[0] + '%s\n网络已连接' % (name[1:]))
            self.tray.setToolTip("%s已连接" % (name[1:]))
            # t2 = Thread(target=self.checkWeb)
            # t2.start()
            self.checkWeb()

    def changeStateText(self, state):
        self.stateText.setText(state)

    def loadLinkList(self, linkList):
        pass

    def searchTHU(self):
        use = usage()
        if use == -1:
            self.changeStateText("不在清华网内")
        elif use == -2:
            self.changeStateText("网络未连接")
        else:
            text = self.stateText.text()
            a = text.split('\n')
            a[-1] = str("已使用%.2fGB" % (int(use) / 1e9))
            self.changeStateText('\n'.join(a))
        pass

    def saveAccount(self, username, userpass, dialog):
        userkey = hashlib.md5(userpass.encode()).hexdigest()
        f = open('account', 'wb')
        f.write((username + '\n' + userkey).encode())
        f.close()
        dialog.close()

    def savePreference(self, THU, NoTHU, dialog):
        if not os.path.exists('preference.ini'):
            f = open('preference.ini', 'wb')
            f.close()

        f = open('preference.ini', 'wb')
        for row in NoTHU.split('\n'):
            f.write(('!' + row + '\n').encode())
        for row in THU.split('\n'):
            f.write(('?' + row + '\n').encode())
        f.close()
        dialog.close()

    def setMode(self, mode):
        self.mode = mode

    def saveSetting(self, dialog):
        f = open('setting.ini', 'wb')
        content = f.write(self.mode.encode())
        f.close()
        dialog.close()

    def setting(self):
        if not os.path.exists('setting.ini'):
            f = open('setting.ini', 'wb')
            f.close()

        f = open('setting.ini', 'rb')
        content = f.read().decode()

        dialog = QtWidgets.QDialog()
        dialog.resize(300, 200)
        dialog.setWindowTitle("联网优先级")
        dialog.setWindowFlags(Qt.Qt.WindowCloseButtonHint)

        p = dialog.palette()
        p.setColor(dialog.backgroundRole(), QtGui.QColor(255, 255, 255))
        dialog.setPalette(p)

        group = QtWidgets.QGroupBox()

        check1 = QtWidgets.QRadioButton(group)
        check2 = QtWidgets.QRadioButton(group)
        submit = QtWidgets.QPushButton()
        layout = QtWidgets.QGridLayout(dialog)

        check1.setText("自动连接")
        check2.setText("点选网络")
        submit.setText("确认")
        check1.toggled.connect(lambda: self.setMode('0'))
        check2.toggled.connect(lambda: self.setMode('1'))
        submit.clicked.connect(lambda: self.saveSetting(dialog))

        if content == "0":
            check1.toggle()
        elif content == "1":
            check2.toggle()

        layout.addWidget(check1, 0, 0)
        layout.addWidget(check2, 0, 1)
        layout.addWidget(submit, 1, 0, 1, 2)
        layout.setSpacing(0)

        dialog.exec()
        f.close()

    def preference(self):
        if not os.path.exists('preference.ini'):
            f = open('preference.ini', 'wb')
            f.close()

        f = open('preference.ini', 'rb')
        content = f.read().decode().split('\n')
        f.close()

        dialog = QtWidgets.QDialog()
        dialog.resize(300, 200)
        dialog.setWindowTitle("联网优先级")
        dialog.setWindowFlags(Qt.Qt.WindowCloseButtonHint)

        p = dialog.palette()
        p.setColor(dialog.backgroundRole(), QtGui.QColor(255, 255, 255))
        dialog.setPalette(p)

        layout = QtWidgets.QVBoxLayout(dialog)

        label1 = QtWidgets.QLabel()
        label1.setText("清华网")
        label2 = QtWidgets.QLabel()
        label2.setText("非清华网")

        NoTHU = QtWidgets.QTextEdit()
        THU = QtWidgets.QTextEdit()
        NoTHU.setStyleSheet("border:0;")
        THU.setStyleSheet("border:0;")

        submit = QtWidgets.QPushButton()
        submit.setText("确认修改")
        submit.clicked.connect(
            lambda: self.savePreference(THU.toPlainText(), NoTHU.toPlainText(), dialog)
        )

        for network in content:
            if len(network) >= 2:
                if network[0] == '?':
                    THU.append(network[1:])
                elif network[0] == '!':
                    NoTHU.append(network[1:])

        layout.addWidget(label2)
        layout.addWidget(NoTHU)
        layout.addWidget(label1)
        layout.addWidget(THU)
        layout.addWidget(submit)

        dialog.exec()

    def account(self):
        if not os.path.exists('account'):
            f = open('account', 'wb')
            f.close()

        f = open('account', 'rb')
        history_name = ''
        content = f.read().decode().split('\n')
        f.close()
        if len(content) >= 2:
            history_name = content[0]

        dialog = QtWidgets.QDialog()
        dialog.resize(300, 200)
        dialog.setWindowTitle("账户信息")
        dialog.setWindowFlags(Qt.Qt.WindowCloseButtonHint)

        p = dialog.palette()
        p.setColor(dialog.backgroundRole(), QtGui.QColor(255, 255, 255))
        dialog.setPalette(p)

        layout = QtWidgets.QGridLayout(dialog)

        username = QtWidgets.QLineEdit()
        password = QtWidgets.QLineEdit()
        submit = QtWidgets.QPushButton()
        username.setStyleSheet("border:0;")
        password.setStyleSheet("border:0;")

        username.setPlaceholderText("用户名")
        password.setPlaceholderText("密码")

        if history_name != '':
            username.setText(history_name)

        submit.setText("确认")
        password.setEchoMode(2)

        layout.addWidget(username, 0, 0)
        layout.addWidget(password, 1, 0)
        layout.addWidget(submit, 2, 0)

        submit.clicked.connect(
            lambda: self.saveAccount(username.text(), password.text(), dialog))

        dialog.exec()

    def act(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show()

    def setTray(self):
        self.tray = QtWidgets.QSystemTrayIcon()  # 创建系统托盘对象
        self.icon = QtGui.QIcon('myTunet.png')  # 创建图标
        self.tray.setIcon(self.icon)  # 设置系统托盘图标
        self.tray.activated.connect(self.act)  # 设置托盘点击事件处理函数
        self.tray_menu = QtWidgets.QMenu(
            QtWidgets.QApplication.desktop())  # 创建菜单
        self.RestoreAction = QtWidgets.QAction(
            '还原 ', self, triggered=self.show)  # 添加一级菜单动作选项(还原主窗口)
        self.QuitAccountAction = QtWidgets.QAction(
            '登出 ', self, triggered=self.quitAccount)  # 添加一级菜单动作选项(退出登录)
        self.QuitAction = QtWidgets.QAction(
            '退出程序 ', self, triggered=self.quitexec)  # 添加一级菜单动作选项(退出程序)
        self.FreshAction = QtWidgets.QAction(
            '刷新 ', self, triggered=self.freshWifi)  # 添加一级菜单动作选项(退出程序)
        # self.connectMenu = QtWidgets.QMenu(self.tray_menu)
        # self.connectMenu.setTitle("连接")
        # self.connectMenu.triggered.connect(self.freshWifi)
        # self.tray_menu.addMenu(self.connectMenu)
        # self.connectMenu.triggered.connect(self.freshWifi)
        self.connectMenu = self.tray_menu.addMenu('可用连接')
        self.connectMenu.triggered.connect(self.freshWifi)

        self.connectMenu.addAction(self.FreshAction)
        self.tray_menu.addAction(self.RestoreAction)  # 为菜单添加动作
        self.tray_menu.addAction(self.QuitAccountAction)
        self.tray_menu.addAction(self.QuitAction)
        self.tray.setContextMenu(self.tray_menu)  # 设置系统托盘菜单
        self.tray.show()

    def setupUi(self):
        # 创建文件夹
        file_dir = os.environ['LOCALAPPDATA']
        if not os.path.exists(file_dir + r'\\myTunet'):
            os.mkdir(file_dir + r'\\myTunet')

        # 切换工作路径
        os.chdir(os.path.join(file_dir, 'myTunet'))

        # 初始化窗口
        self.setWindowIcon(QtGui.QIcon("myTunet.ico"))
        MainWindow = self
        MainWindow.setObjectName("MainWindow")
        MainWindow.setMinimumSize(QtCore.QSize(464, 255))
        MainWindow.setMaximumSize(QtCore.QSize(464, 255))
        MainWindow.resize(464, 255)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.backImg = QtWidgets.QLabel(self.centralwidget)
        self.backImg.setGeometry(QtCore.QRect(0, 0, 461, 221))
        self.backImg.setText("")
        self.backImg.setObjectName("backImg")
        self.backImg.setPixmap(QtGui.QPixmap("myTunet.png"))
        self.backImg.setScaledContents(True)
        self.stateText = QtWidgets.QLabel(self.centralwidget)
        self.stateText.setGeometry(QtCore.QRect(30, 70, 221, 61))
        self.stateText.setObjectName("stateText")
        self.stateText.setStyleSheet("background:rgba(255,255,255,0.2)")
        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(270, 0, 191, 231))
        self.listWidget.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setStyleSheet("background:rgba(255,255,255,0.3);")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 464, 17))
        self.menubar.setObjectName("menubar")
        self.func = QtWidgets.QMenu(self.menubar)
        self.func.setObjectName("func")
        self.checklearn = QtWidgets.QAction(MainWindow)
        self.checklearn.setObjectName('checklearn')
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu2 = QtWidgets.QAction(MainWindow)
        self.menu2.setObjectName("menu2")
        self.help = QtWidgets.QAction(MainWindow)
        self.help.setObjectName("help")
        self.search = QtWidgets.QAction(MainWindow)
        self.search.setObjectName("search")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionAccount = QtWidgets.QAction(MainWindow)
        self.actionAccount.setObjectName("actionAccount")
        self.actionAccount.triggered.connect(self.account)
        self.checklearn.triggered.connect(self.check_learning)
        self.actionPreference = QtWidgets.QAction(MainWindow)
        self.actionPreference.setObjectName("actionPreference")
        self.actionPreference.triggered.connect(self.preference)
        self.actionSetting = QtWidgets.QAction(MainWindow)
        self.actionSetting.setObjectName("actionSetting")
        self.actionSetting.triggered.connect(self.setting)
        self.actionQuitAccount = QtWidgets.QAction(MainWindow)
        self.actionQuitAccount.setObjectName("actionQuitAccount")
        self.actionQuitAccount.triggered.connect(self.quitAccount)
        self.actionExec = QtWidgets.QAction(MainWindow)
        self.actionExec.setObjectName("actionExec")
        self.actionExec.triggered.connect(self.quitexec)
        self.menu.addAction(self.actionAccount)
        self.menu.addAction(self.actionPreference)
        self.menu.addAction(self.actionSetting)
        self.menu.addSeparator()
        self.menu.addAction(self.actionQuitAccount)
        self.menu.addAction(self.actionExec)
        self.func.addAction(self.checklearn)
        self.menu2.triggered.connect(self.freshWifi)
        self.help.triggered.connect(self.helpInfo)
        self.search.triggered.connect(self.searchTHU)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.func.menuAction())
        self.menubar.addAction(self.menu2)
        self.menubar.addAction(self.search)
        self.menubar.addAction(self.help)
        self.help.setShortcut('F1')
        self.search.setShortcut('F5')

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.tray.setToolTip("正在连接")

        if not os.path.exists('account'):
            f = open('account', 'wb')
            f.close()

        f = open('account', 'rb')
        history_name = ''
        content = f.read().decode().split('\n')
        if len(content) >= 2:
            history_name = content[0]
            self.stateText.setText("用户名: %s <br/>未登录" % (history_name))
        else:
            self.stateText.setText("请设置用户名和密码")

        self.freshWifi()

        if not os.path.exists('setting.ini'):
            f = open('setting.ini', 'wb')
            f.close()

        f = open('setting.ini', 'rb')
        content = f.read().decode()
        f.close()
        if content == '0':
            for index in self.wifiList:
                t = Thread(target=self.connectWifiName, args=(index, ))
                t.start()
                break
                # self.connectWifiName(index)
                # if self.checkWeb():
                #    break
                # else:
                #    continue
            pass
        elif content == '1':
            pass

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "myTunet清华网助手"))
        self.stateText.setText(_translate("MainWindow", "stateText"))
        self.menu.setTitle(_translate("MainWindow", "配置"))
        self.func.setTitle("工具")
        self.checklearn.setText("检查网络学堂")
        self.menu2.setText("刷新WiFi")
        self.search.setText("流量查询")
        self.help.setText("帮助(F1)")
        self.actionAccount.setText(_translate("MainWindow", "账户"))
        self.actionPreference.setText(_translate("MainWindow", "联网优先级"))
        self.actionSetting.setText(_translate("MainWindow", "启动设置"))
        self.actionQuitAccount.setText(_translate("MainWindow", "退出登录"))
        self.actionExec.setText(_translate("MainWindow", "退出程序"))

    def helpInfo(self):
        w = QtWidgets.QDialog()
        label = QtWidgets.QLabel(w)
        label.setText(
            "在设置中:\n\t账户信息中登入清华账号\n  联网优先级中根据是否需要\n  认证填写网络名" +
            "\n\t联网设置里,自动连接意味着\n  程序在打开时会按照优先级设置自\n  动连接认证,点选意味着每次打开不\n  会自动连接"
        )
        w.resize(300, 200)
        w.setWindowTitle("帮助信息")
        w.setWindowFlags(Qt.Qt.WindowCloseButtonHint)
        w.exec()

    def changeEvent(self, event):
        if event.type(
        ) == QtCore.QEvent.WindowStateChange and self.isMinimized():
            event.ignore()
            self.hide()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    mainwindow = Ui_MainWindow()
    mainwindow.setupUi()
    mainwindow.show()

    sys.exit(app.exec_())
    pass