from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import json
import urllib.request
import requests
import os
import socket

with open('model/name2idx.json', 'r', encoding='utf8') as f:
	name2idx = json.load(f)
f.close()

idx2name = {name2idx[name]:name for name in name2idx}

with open('model/shishen.json', 'r', encoding='utf8') as f:
	shishen = json.load(f)
f.close()

with open('config.json', 'r') as f:
	user_config = json.load(f)
f.close()

class Downloader(QThread):
	_signal = pyqtSignal(int)
	def __init__(self):
		super(Downloader, self).__init__()

	def setUrls(self, urls):
		self.urls = urls

	def run(self):
		n = 0
		for item in self.urls:
			urllib.request.urlretrieve(item[1], item[0])
			n += 1
			self._signal.emit(n)
		self._signal.emit(-1)


class LoadingWindow(QDialog):
	def __init__(self):
		super(LoadingWindow, self).__init__()
		self.ready = False
		self.initUI()
		self.isNetOK = self.checkNetOK()
		self.downloader = Downloader()
		self.downloader._signal.connect(self.updateBar)


	def initUI(self):
		self.mainLayout = QVBoxLayout()
		self.statusLabel = QLabel('检查资源……')
		self.progressBar = QProgressBar()

		self.mainLayout.addWidget(self.statusLabel)
		self.mainLayout.addWidget(self.progressBar)

		self.setLayout(self.mainLayout)
		self.setFixedSize(300, 100)
		self.setStyleSheet(
			'''
			QLabel {font-family: "Microsoft YaHei UI"; font-size:16px}
			QPushButton {font-family: "Microsoft YaHei UI"; font-size:16px}
			''')
		self.setWindowTitle('启动中')

	def checkNetOK(self):
		testserver = ('www.baidu.com', 443)
		s = socket.socket()
		s.settimeout(3)
		try:
			status = s.connect_ex(testserver)
			if status == 0:
				s.close()
				return True
			else:
				return False
		except Exception as e:
			return False

	def getUpdates(self):
		response = requests.get("https://yysrank.ahrisy.com/download/h5model/config.json")
		new_config = json.loads(response.text)
		global user_config
		if user_config['version'] < new_config['version']:
			messageBox = QMessageBox(QMessageBox.Information,"提示","程序已更新，请前往 https://yysrank.ahrisy.com/ai 下载最新版\n更新内容：" + new_config['feature'])
			Qyes = messageBox.addButton(self.tr("退出"), QMessageBox.YesRole)
			Qno = messageBox.addButton(self.tr("忽略此次更新"), QMessageBox.NoRole)
			messageBox.exec_()
			if messageBox.clickedButton() == Qyes:
				app = QApplication.instance()
				app.quit()

		if user_config['last_update'] < new_config['last_update']:
			self.statusLabel.setText('检查到模型更新，下载中……')
			url = "https://yysrank.ahrisy.com/download/h5model/"
			urllib.request.urlretrieve(url + "rewardnet_best.h5", './model/rewardnet_best.h5')
			urllib.request.urlretrieve(url + "predictnet_best.h5", './model/predictnet_best.h5')
			urllib.request.urlretrieve(url + "name2idx.json", './model/name2idx.json')
			urllib.request.urlretrieve(url + "shishen.json", './model/shishen.json')
			config_file = open('config.json', 'w')
			user_config['last_update'] = new_config['last_update']
			config_file.write(json.dumps(user_config))
			config_file.close()
			self.statusLabel.setText('模型下载完成，重新加载中……')
			with open('model/name2idx.json', 'r', encoding='utf8') as f:
				name2idx = json.load(f)
			f.close()

			idx2name = {name2idx[name]:name for name in name2idx}

			with open('model/shishen.json', 'r', encoding='utf8') as f:
				shishen = json.load(f)
			f.close()

			with open('config.json', 'r') as f:
				user_config = json.load(f)
			f.close()



	def getResources(self):
		if not os.path.exists('assets'):
			os.makedirs('assets/painting')
			os.makedirs('assets/icon')
		names = [name for name in name2idx]
		paintings = []
		for root, dirs, files in os.walk('./assets/painting'):
			for f in files:
				if os.path.splitext(f)[1] == '.png':
					paintings.append(os.path.splitext(f)[0])

		icons = []
		for root, dirs, files in os.walk('./assets/icon'):
			for f in files:
				if os.path.splitext(f)[1] == '.png':
					icons.append(os.path.splitext(f)[0])

		new_paintings = list(set(names) - set(paintings))
		new_icons = list(set(names) - set(paintings))

		painting_url = {shishen[key]['name']:shishen[key]['painting'] for key in shishen}
		icon_url = {shishen[key]['name']:shishen[key]['icon_transparent'] for key in shishen}
		to_be_downloaded = []
		for name in new_paintings:
			to_be_downloaded.append(['./assets/painting/' + name + '.png', painting_url[name]])
		for name in new_icons:
			to_be_downloaded.append(['./assets/icon/' + name + '.png', icon_url[name]])

		self.statusLabel.setText('下载式神图标与立绘……')
		self.progressBar.setMaximum(len(to_be_downloaded))
		self.progressBar.setValue(0)
		self.downloader.setUrls(to_be_downloaded)
		self.downloader.start()

	def updateBar(self, value):
		if value > 0:
			self.progressBar.setValue(value)





class BanDialog(QDialog):
	def __init__(self, ban, use_ban):
		super(BanDialog, self).__init__()
		self.initUI(ban, use_ban)

	def initUI(self, ban, use_ban):
		self.mainLayout = QGridLayout()

		self.groupLayout = QGridLayout()
		self.groupWidget = QWidget()
		self.groupWidget.setLayout(self.groupLayout)
		self.shishenBtn = {}
		name2rarity = {shishen[key]['name']: shishen[key]['rarity'] for key in shishen}
		name2key = {shishen[key]['name']: int(key) for key in shishen}
		for name in name2idx:
			self.shishenBtn[name] = [name2key[name], name2rarity[name], QPushButton(QIcon('assets/icon/{}.png'.format(name)), '')]
			self.shishenBtn[name][2].setIconSize(QSize(50, 50))
			self.shishenBtn[name][2].setFixedSize(QSize(60, 60))
			self.shishenBtn[name][2].setObjectName(name)
			self.shishenBtn[name][2].setCheckable(True)
			if name in ban:
				self.shishenBtn[name][2].setChecked(True)

		self.shishenBtn = sorted(self.shishenBtn.items(), key=lambda x: (x[1][1], x[1][0]), reverse=True)

		n = 0
		j = 0
		while True:
			for i in range(10):
				self.groupLayout.addWidget(self.shishenBtn[n][1][2], j, i, Qt.AlignCenter)
				n += 1
				if n >= len(self.shishenBtn):
					break
			j += 1
			if n >= len(self.shishenBtn):
				break

		self.enableCheckBox = QCheckBox('启用Ban位')
		self.enableCheckBox.setChecked(use_ban)
		self.okBtn = QPushButton('确定')
		self.okBtn.setObjectName('OK')
		self.okBtn.setFixedSize(QSize(80, 40))
		self.okBtn.clicked.connect(self.accept)

		self.groupWidget.setObjectName('shishen_group')
		self.mainLayout.addWidget(self.groupWidget, 0, 0, 1, 2, Qt.AlignCenter)
		self.mainLayout.addWidget(self.enableCheckBox, 1, 0, Qt.AlignCenter)
		self.mainLayout.addWidget(self.okBtn, 1, 1, Qt.AlignCenter)

		self.setLayout(self.mainLayout)
		self.setWindowTitle('设置Ban位')
		self.setStyleSheet(
			'''
			QWidget#shishen_group {border:2px solid gray; border-radius:10px; background:LightGray}
			QCheckBox {font-family: "Microsoft YaHei UI"; font-size:18px}
			QPushButton {border:1px solid gray; border-radius:10px}
			QPushButton:checked {border:5px solid red; border-radius:10px}
			QPushButton#OK {border:1px solid gray; font-family:"Microsoft YaHei UI"; font-size:18px; background:LightGray}
			QPushButton#OK:hover {border:1px solid #F3F3F5; border-radius:10px; font-size:20px; background:LightGreen}
			''')

	def enabled(self):
		return self.enableCheckBox.isChecked()

	def getChecked(self):
		name = []
		for item in self.shishenBtn:
			if item[1][2].isChecked():
				name.append(item[0])
		return name

	def reset(self):
		self.enableCheckBox.setChecked(False)
		for i in range(len(self.shishenBtn)):
			self.shishenBtn[i][1][2].setChecked(False)


class MoreDialog(QDialog):
	def __init__(self, version, last_update_time):
		super(MoreDialog, self).__init__()
		self.last_update_time = last_update_time
		self.version = version
		self.initUI()

	def initUI(self):
		self.mainLayout = QGridLayout()
		self.mainLayout.addWidget(QLabel('作者'), 0, 0, Qt.AlignCenter)
		self.mainLayout.addWidget(QLabel('Ahrisy'), 0, 1, Qt.AlignCenter)
		self.mainLayout.addWidget(QLabel('QQ交流群'), 1, 0, Qt.AlignCenter)
		self.mainLayout.addWidget(QLabel('850716880'), 1, 1, Qt.AlignCenter)
		self.mainLayout.addWidget(QLabel('B站'), 2, 0, Qt.AlignCenter)
		biliLabel = QLabel('<a href=https://space.bilibili.com/4847326>https://space.bilibili.com/4847326</a>')
		biliLabel.setOpenExternalLinks(True)
		self.mainLayout.addWidget(biliLabel, 2, 1, Qt.AlignCenter)

		self.mainLayout.addWidget(QLabel('项目主页'), 3, 0, Qt.AlignCenter)
		linkLabel = QLabel('<a href=https://yysrank.ahrisy.com/ai>https://yysrank.ahrisy.com/ai</a>')
		linkLabel.setOpenExternalLinks(True)
		self.mainLayout.addWidget(linkLabel, 3, 1, Qt.AlignCenter)

		self.mainLayout.addWidget(QLabel('GitHub'), 4, 0, Qt.AlignCenter)
		gitLabel = QLabel('<a href=https://github.com/Ahrisya/CuteRookie4User>https://github.com/Ahrisya/CuteRookie4User</a>')
		gitLabel.setOpenExternalLinks(True)
		self.mainLayout.addWidget(gitLabel, 4, 1, Qt.AlignCenter)

		self.mainLayout.addWidget(QLabel('当前版本'), 5, 0, Qt.AlignCenter)
		self.mainLayout.addWidget(QLabel(self.version), 5, 1, Qt.AlignCenter)

		self.mainLayout.addWidget(QLabel('模型每周一下午更新，当前模型更新时间：' + self.last_update_time), 6, 0, 1, 2, Qt.AlignCenter)

		self.mainLayout.setSpacing(10)

		self.setLayout(self.mainLayout)
		self.setStyleSheet(
			'''
			QLabel {font-family: "Microsoft YaHei UI"; font-size:16px}
			QPushButton {font-family: "Microsoft YaHei UI"; font-size:16px}
			''')
		self.setWindowTitle('More……')

class EndGameDialog(QDialog):
	def __init__(self):
		super(EndGameDialog, self).__init__()
		self.initUI()

	def initUI(self):
		self.T1Widget = QWidget()
		self.T1Layout = QHBoxLayout()
		self.T1Widget.setLayout(self.T1Layout)

		self.T2Widget = QWidget()
		self.T2Layout = QHBoxLayout()
		self.T2Widget.setLayout(self.T2Layout)

		self.T1 = []
		self.T2 = []
		for i in range(5):
			self.T1.append(QLabel(''))
			self.T2.append(QLabel(''))
		for i in range(5):
			self.T1Layout.addWidget(self.T1[i])
			self.T2Layout.addWidget(self.T2[i])

		self.wr = QLabel('')
		self.winRateWidget = QWidget()
		self.winRateLayout = QHBoxLayout()
		self.winRateWidget.setLayout(self.winRateLayout)
		self.winRateLayout.addWidget(QLabel('蓝色方预测胜率为'))
		self.winRateLayout.addWidget(self.wr)

		self.mainLayout = QVBoxLayout()
		self.mainLayout.addWidget(self.T1Widget, Qt.AlignCenter)
		vsLabel = QLabel('VS')
		vsLabel.setAlignment(Qt.AlignCenter)
		self.mainLayout.addWidget(vsLabel, Qt.AlignCenter)
		self.mainLayout.addWidget(self.T2Widget, Qt.AlignCenter)
		self.mainLayout.addWidget(self.winRateWidget, Qt.AlignCenter)

		self.T1Widget.setStyleSheet('background:DarkBlue; border-radius:5px; border:2px solid gray')
		self.T2Widget.setStyleSheet('background:DarkRed; border-radius:5px; border:2px solid gray')
		self.setLayout(self.mainLayout)
		self.setStyleSheet(
			'''
			QLabel {font-family: "Microsoft YaHei UI"; font-size:24px}
			''')
		self.setWindowTitle('AI预测结果')

	def setInfo(self, T1, T2, wr):
		for i in range(5):
			self.T1[i].setPixmap(QPixmap('assets/icon/{}.png'.format(T1[i])))
			self.T2[i].setPixmap(QPixmap('assets/icon/{}.png'.format(T2[i])))
		self.wr.setText('%.2f%%' % (100*wr))
		