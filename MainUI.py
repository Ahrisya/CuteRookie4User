import sys
from MCTS import MCTS, load_models
import copy
import numpy as np
from Dialogs import *

class AIPlayer(QThread):
	_signal = pyqtSignal(str)
	def __init__(self, dim):
		super(AIPlayer, self).__init__()
		rewardnet, predictnet = load_models('./model')
		self.mcts = MCTS(dim, rewardnet, predictnet, 1, 10)

	def setParam(self, thres, c1, c2, time_limit, ban):
		self.mcts.set_params(c1, c2, thres)
		self.time_limit = time_limit
		self.ban = ban

	def setPicks(self, ai_picks, user_picks):
		self.ai_picks = ai_picks
		self.user_picks = user_picks

	def run(self):
		self.mcts.reset()
		acts, probs = self.mcts.search([self.ai_picks, self.user_picks], self.time_limit, self.ban)
		next_pick = idx2name[acts[np.argmax(probs)]]
		self._signal.emit(next_pick)

	def predict(self, ai_picks, user_picks):
		return self.mcts.predict_win_rate([user_picks, ai_picks])


class MainUI(QMainWindow):
	def __init__(self):
		super(MainUI, self).__init__()
		self.loadingWindow = LoadingWindow()
		self.loadingWindow.show()
		self.loadingWindow.downloader._signal.connect(self.startMainUI)
		self.loadingWindow.getResources()

	def startMainUI(self, value):
		if value > 0:
			return
		self.loadingWindow.close()
		self.loadUserInfo()
		self.initUI()
		self.initDialog()
		self.rightWidget.setEnabled(False)
		self.timer = QTimer()
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self.refreshTimer)
		self.count = 10
		self.round = 0
		self.T1 = []
		self.T2 = []
		self.can_select = False
		self.AI = AIPlayer(len(name2idx))
		self.AI._signal.connect(self.getAIPick)

	def loadUserInfo(self):
		with open('config.json', 'r') as f:
			self.user_config = json.load(f)
		f.close()

		
	def initUI(self):
		# main widget
		self.mainWidget = QWidget()
		self.mainLayout = QHBoxLayout()
		self.mainWidget.setLayout(self.mainLayout)

		# left widget
		self.leftWidget = QWidget()
		self.leftLayout = QVBoxLayout()
		self.leftWidget.setLayout(self.leftLayout)
		self.leftWidget.setObjectName('left_widget')

		self.settingWidget = QWidget()
		self.settingLayout = QGridLayout()
		self.settingWidget.setLayout(self.settingLayout)
		self.settingWidget.setObjectName('setting_widget')

		self.paraLabel = QLabel('AI参数')
		self.paraLabel.setObjectName('left_label')
		self.paraLabel.setFixedHeight(50)
		self.paraLabel.setAlignment(Qt.AlignCenter)

		self.c1Text = QLineEdit(str(self.user_config['params']['c1']))
		self.c1Text.setFixedHeight(30)
		self.c2Text = QLineEdit(str(self.user_config['params']['c2']))
		self.c2Text.setFixedHeight(30)
		self.timeText = QLineEdit(str(self.user_config['params']['time_limit']))
		self.timeText.setFixedHeight(30)
		self.thresText = QLineEdit(str(self.user_config['params']['thres']))
		self.thresText.setFixedHeight(30)

		self.teamLabel = QLabel('阵容设置')
		self.teamLabel.setObjectName('left_label')
		self.teamLabel.setFixedHeight(50)
		self.teamLabel.setAlignment(Qt.AlignCenter)

		self.banBtn = QPushButton('Ban')
		self.banBtn.setFixedSize(QSize(100, 30))
		self.banBtn.clicked.connect(self.showBanDialog)
		if self.user_config['params']['use_ban']:
			self.banBtn.setText('Ban(已启用)')
		else:
			self.banBtn.setText('Ban(未启用)')

		self.otherLabel = QLabel('其他')
		self.otherLabel.setObjectName('left_label')
		self.otherLabel.setFixedHeight(50)
		self.otherLabel.setAlignment(Qt.AlignCenter)

		self.saveBtn = QPushButton('保存设置')
		self.saveBtn.setFixedSize(QSize(100, 30))
		self.saveBtn.clicked.connect(self.saveConfig)

		self.resetBtn = QPushButton('恢复默认')
		self.resetBtn.setFixedSize(QSize(100, 30))
		self.resetBtn.clicked.connect(self.resetConfig)

		self.moreBtn = QPushButton('更多')
		self.moreBtn.setFixedSize(QSize(100, 30))
		self.moreBtn.clicked.connect(self.showmoreDialog)

		self.cheatCBox = QCheckBox('作弊模式')
		self.cheatCBox.setFixedSize(QSize(100, 30))
		self.cheatCBox.setChecked(self.user_config['params']['cheat'])

		self.settingLayout.addWidget(self.paraLabel, 0, 0, 1, 2, Qt.AlignCenter)
		self.settingLayout.addWidget(QLabel('C1'), 1, 0, Qt.AlignCenter)
		self.settingLayout.addWidget(self.c1Text, 1, 1, Qt.AlignCenter)
		self.settingLayout.addWidget(QLabel('C2'), 2, 0, Qt.AlignCenter)
		self.settingLayout.addWidget(self.c2Text, 2, 1, Qt.AlignCenter)
		self.settingLayout.addWidget(QLabel('阈值'), 3, 0, Qt.AlignCenter)
		self.settingLayout.addWidget(self.thresText, 3, 1, Qt.AlignCenter)
		self.settingLayout.addWidget(QLabel('计算时间(s)'), 4, 0, Qt.AlignCenter)
		self.settingLayout.addWidget(self.timeText, 4, 1, Qt.AlignCenter)
		self.settingLayout.addWidget(self.teamLabel, 5, 0, 1, 2, Qt.AlignCenter)
		self.settingLayout.addWidget(self.banBtn, 6, 0, 1, 2, Qt.AlignCenter)
		self.settingLayout.addWidget(self.otherLabel, 7, 0, 1, 2, Qt.AlignCenter)
		self.settingLayout.addWidget(self.saveBtn, 8, 0, 1, 2, Qt.AlignCenter)
		self.settingLayout.addWidget(self.resetBtn, 9, 0, 1, 2, Qt.AlignCenter)
		self.settingLayout.addWidget(self.moreBtn, 10, 0, 1, 2, Qt.AlignCenter)
		self.settingLayout.addWidget(self.cheatCBox, 11, 0, 1, 2, Qt.AlignCenter)

		self.settingLayout.setHorizontalSpacing(10)

		self.settingWidget.setStyleSheet(
			'''
			QWidget#setting_widget {background:#3A3A3A; border-radius:5px; border:1px solid white}
			QLabel {color:white; font-family: "Microsoft YaHei UI"; font-size:16px}
			QLabel#left_label {border:none; border-bottom:1px solid white; font-size:24px; font-weight:normal; min-width:100px}
			QPushButton {border:none; font-family:"Microsoft YaHei UI"; font-size:16px; color:white}
			QPushButton:hover {border:1px solid #F3F3F5; border-radius:10px; background:LightGray; color:black}
			QLineEdit {border-radius:2px; font-size:16px}
			QCheckBox {border:none; font-family:"Microsoft YaHei UI"; font-size:16px; color:white}
			'''
			)

		self.startBtn = QPushButton('开始')
		self.startBtn.setObjectName('start_btn')
		self.startBtn.setFixedSize(QSize(150, 60))
		self.startBtn.clicked.connect(self.startGame)

		self.leftLayout.addWidget(self.settingWidget)
		self.leftLayout.addWidget(self.startBtn)
		self.leftWidget.setStyleSheet(
			'''
			QPushButton#start_btn {border:1px solid gray; border-radius:10px; font-family:"Microsoft YaHei UI"; font-size:24px; color:black; background:LightGray}
			QPushButton#start_btn:hover {border:1px solid white; background:LightGreen; font-size:28px; color:black}
			'''
			)

		# right widget
		self.rightWidget = QWidget()
		self.rightLayout = QGridLayout()
		self.rightWidget.setLayout(self.rightLayout)

		self.topsettingWidget = QWidget()
		self.topsettingLayout = QHBoxLayout()
		self.topsettingWidget.setLayout(self.topsettingLayout)
		self.topsettingWidget.setObjectName('topsetting_widget')

		self.toprightWidget = QWidget()
		self.toprightLayout = QHBoxLayout()
		self.toprightWidget.setLayout(self.toprightLayout)
		self.toprightWidget.setObjectName('topright_widget')

		self.selectedT1 = []
		self.selectedT2 = []
		for i in range(5):
			self.selectedT1.append(QLabel(''))
			self.selectedT2.append(QLabel(''))
		for i in range(5):
			self.selectedT1[i].setFixedSize(QSize(50, 50))
			self.topsettingLayout.addWidget(self.selectedT1[i], Qt.AlignCenter)

		self.vsLabel = QLabel('VS')
		self.vsLabel.setFixedSize(QSize(50, 50))
		self.vsLabel.setStyleSheet('font-size:16px; font-weight:bold; border:none')
		self.vsLabel.setAlignment(Qt.AlignCenter)

		for i in range(5):
			self.selectedT2[i].setFixedSize(QSize(50, 50))
			self.toprightLayout.addWidget(self.selectedT2[i], Qt.AlignCenter)

		self.rightLayout.addWidget(self.topsettingWidget, 0, 0, Qt.AlignCenter)
		self.rightLayout.addWidget(self.vsLabel, 0, 1, Qt.AlignCenter)
		self.rightLayout.addWidget(self.toprightWidget, 0, 2, Qt.AlignCenter)

		self.statusT1 = QLabel('')
		self.statusT1.setFixedSize(QSize(300, 50))
		self.statusT1.setAlignment(Qt.AlignCenter)
		self.statusT1.setStyleSheet('font-family:"Microsoft YaHei UI"; font-size:24px; color:red;')
		self.statusT2 = QLabel('')
		self.statusT2.setFixedSize(QSize(300, 50))
		self.statusT2.setAlignment(Qt.AlignCenter)
		self.statusT2.setStyleSheet('font-family:"Microsoft YaHei UI"; font-size:24px; color:red;')

		self.paintingT1 = QLabel('')
		self.paintingT1.setFixedSize(QSize(300, 300))
		self.paintingT1.setAlignment(Qt.AlignCenter)
		self.paintingT1.setStyleSheet('font-family:"Microsoft YaHei UI"; font-size:60px; color:red;')
		self.paintingT2 = QLabel('')
		self.paintingT2.setFixedSize(QSize(300, 300))
		self.paintingT2.setAlignment(Qt.AlignCenter)
		self.paintingT2.setStyleSheet('font-family:"Microsoft YaHei UI"; font-size:60px; color:red;')


		self.timerLabel = QLabel('10')
		self.timerLabel.setFixedSize(QSize(50, 50))
		self.timerLabel.setStyleSheet('font-size:24px; font-weight:bold; color:red')
		self.timerLabel.setAlignment(Qt.AlignCenter)

		self.rightLayout.addWidget(self.statusT1, 1, 0, Qt.AlignCenter)
		self.rightLayout.addWidget(self.timerLabel, 1, 1, Qt.AlignCenter)
		self.rightLayout.addWidget(self.statusT2, 1, 2, Qt.AlignCenter)
		self.rightLayout.addWidget(self.paintingT1, 2, 0, Qt.AlignCenter)
		self.rightLayout.addWidget(self.paintingT2, 2, 2, Qt.AlignCenter)
		# pool
		self.bottomWidget = QWidget()
		self.bottomLayout = QHBoxLayout()
		self.bottomWidget.setLayout(self.bottomLayout)

		self.initPool()
		if self.user_config['params']['use_ban']:
			self.ban = self.user_config['params']['ban']
			self.refreshPool(self.ban)
		else:
			self.ban = []

		self.bottomLayout.addWidget(self.poolTab)
		self.okBtn = QPushButton('确定')
		self.okBtn.setFixedSize(QSize(80, 80))
		self.okBtn.setObjectName('ok')
		self.okBtn.clicked.connect(self.confirmShishen)
		self.bottomLayout.addWidget(self.okBtn)
		self.rightLayout.addWidget(self.bottomWidget, 3, 0, 1, 3, Qt.AlignCenter)
		
		self.rightWidget.setObjectName('right_widget')
		self.rightWidget.setStyleSheet(
			'''
			QWidget {background:transparent; border-radius:5px; border:1px solid gray}
			QWidget#right_widget {background:DarkGray; border-radius:5px; border:1px solid gray}
			QWidget#topsetting_widget {background:DarkBlue; border-radius:5px; border:2px solid gray}
			QWidget#topright_widget {background:DarkRed; border-radius:5px; border:2px solid gray}
			QPushButton#ok {border:2px solid gray; border-radius:40px; font-family:"Microsoft YaHei UI"; font-size:24px; background:LightGray}
			QPushButton#ok:hover {border:2px solid white; border-radius:40px; font-family:"Microsoft YaHei UI"; font-size:28px; background:LightGreen}
			'''
			)

		self.setWindowOpacity(0.95)
		self.mainLayout.addWidget(self.leftWidget)
		self.mainLayout.addWidget(self.rightWidget)
		self.setCentralWidget(self.mainWidget)

		self.resize(900, 600)
		screen = QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width() - size.width())/2, (screen.height() - size.height())/2)

		self.setWindowTitle('萌新-CuteRookie v' + self.user_config['version'])
		self.show()

	def initDialog(self):
		self.banDialog = BanDialog(self.user_config['params']['ban'], self.user_config['params']['use_ban'])
		self.moreDialog = MoreDialog(self.user_config['version'], self.user_config['last_update'])
		self.endDialog = EndGameDialog()

	def initPool(self):
		self.pool = {}
		name2rarity = {shishen[key]['name']: shishen[key]['rarity'] for key in shishen}
		name2key = {shishen[key]['name']: int(key) for key in shishen}
		for name in name2idx:
			self.pool[name] = [name2key[name], name2rarity[name], QPushButton(QIcon('assets/icon/{}.png'.format(name)), '')]
			self.pool[name][2].setIconSize(QSize(64, 64))
			self.pool[name][2].setFixedSize(QSize(68, 68))
			self.pool[name][2].setObjectName(name)
			# signal
			self.pool[name][2].clicked.connect(self.setSelected)
		self.pool = sorted(self.pool.items(), key=lambda x: (x[1][1], x[1][0]), reverse=True)
		

		self.poolTab = QTabWidget()
		# 0:SP, 1:SSR, 2:SR, 3:R, 4:N
		self.tab = [QWidget() for i in range(5)] 
		self.tabLayout = [QHBoxLayout() for i in range(5)]
		for i in range(5):
			self.tabLayout[i].setSpacing(10)
			self.tab[i].setLayout(self.tabLayout[i])

		for i in range(len(self.pool)):
			self.tabLayout[6 - self.pool[i][1][1]].addWidget(self.pool[i][1][2], Qt.AlignLeft)

		self.scroll = [QScrollArea() for i in range(5)]
		for i in range(5):
			self.scroll[i].setWidget(self.tab[i])
			self.poolTab.addTab(self.scroll[i], self.num2rarity(6 - i))
		self.poolTab.setFixedSize(QSize(600, 135))
		self.poolTab.setStyleSheet(
			'''
				QWidget {background:transparent}
				QScrollArea {background:#4B4B4B}
				QScrollBar:horizontal {border:none; background: #f5f5f7}
				QScrollBar::handle:horizontal {border:none; border-radius:10px; background: Gainsboro}
				QScrollBar::right-arrow:horizontal, QScrollBar::left-arrow:horizontal {border:none; background:none; color:none}
				QPushButton {border:2px solid #E1E1E1; border-radius:5px}
				QPushButton:hover {background: #F3F3F5; border-style:outset}
			''')

	def refreshPool(self, ban):
		for i in range(len(self.pool)):
			if self.pool[i][1][2].objectName() in ban:
				self.pool[i][1][2].setHidden(True)
			else:
				self.pool[i][1][2].setHidden(False)

	def num2rarity(self, n):
		if n == 2:
			return 'N'
		elif n == 3:
			return 'R'
		elif n == 4:
			return 'SR'
		elif n == 5:
			return 'SSR'
		elif n == 6:
			return 'SP'
		else:
			return 'All'

	def saveConfig(self):
		self.user_config['params']['c1'] = float(self.c1Text.text())
		self.user_config['params']['c2'] = float(self.c2Text.text())
		self.user_config['params']['time_limit'] = float(self.timeText.text())
		self.user_config['params']['thres'] = float(self.thresText.text())
		self.user_config['params']['use_ban'] = self.banDialog.enabled()
		self.user_config['params']['ban'] = self.ban
		self.user_config['params']['cheat'] = self.cheatCBox.isChecked()
		config_file = open('config.json', 'w')
		config_file.write(json.dumps(self.user_config))
		config_file.close()
		QMessageBox.information(self,"提示","用户参数与设置已保存！",QMessageBox.Yes,QMessageBox.Yes)

	def resetConfig(self):
		self.c1Text.setText(str(self.user_config['params']['default_c1']))
		self.c2Text.setText(str(self.user_config['params']['default_c2']))
		self.timeText.setText(str(self.user_config['params']['default_time_limit']))
		self.thresText.setText(str(self.user_config['params']['default_thres']))
		self.cheatCBox.setChecked(False)
		self.banDialog.reset()
		self.ban = []
		self.refreshPool([])
		self.banBtn.setText('Ban(未启用)')
		QMessageBox.information(self,"提示","参数与设置已重置！",QMessageBox.Yes,QMessageBox.Yes)

	def setSelected(self):
		if self.can_select:
			sending_button = self.sender()
			name = sending_button.objectName()
			self.selected = name
			self.paintingT1.setPixmap(QPixmap('assets/painting/{}.png'.format(name)))
			self.paintingT1.setScaledContents(True)

	def reset(self):
		self.count = 10
		self.round = 0
		self.T1 = []
		self.T2 = []
		self.can_select = True
		self.ok1 = False
		for i in range(5):
			self.selectedT1[i].setPixmap(QPixmap(''))
			self.selectedT2[i].setPixmap(QPixmap(''))
		for i in range(len(self.pool)):
			if self.pool[i][0] not in self.ban:
				self.selected = self.pool[i][0]
				break
		self.paintingT1.setPixmap(QPixmap('assets/painting/{}.png'.format(self.selected)))
		self.paintingT1.setScaledContents(True)
		self.paintingT2.setText('?')
		self.statusT1.setText('选择中')
		self.statusT2.setText('选择中')


	def startGame(self):
		self.reset()
		self.is_running = True
		self.leftWidget.setEnabled(False)
		self.rightWidget.setEnabled(True)
		c1 = float(self.c1Text.text())
		c2 = float(self.c2Text.text())
		thres = float(self.thresText.text())
		time_limit = float(self.timeText.text())
		self.AI.setParam(thres, c1, c2, time_limit, [name2idx[name] for name in self.ban])
		self.timer.start()
		if self.cheatCBox.isChecked():
			self.timerLabel.setText('...')
		self.runAI()

	def runAI(self):
		self.statusT2.setText('选择中')
		self.paintingT2.setText('?')
		self.AI.setPicks([name2idx[name] for name in self.T2], [name2idx[name] for name in self.T1])
		self.AI.start()

	def getAIPick(self, ai_pick):
		self.selected_ai = ai_pick
		self.statusT2.setText('已选定')
		if self.cheatCBox.isChecked():
			self.paintingT2.setPixmap(QPixmap('assets/painting/{}.png'.format(self.selected_ai)))
			self.paintingT2.setScaledContents(True)

	def refreshTimer(self):
		if self.count > 0:
			if self.statusT1.text() == '已选定' and self.statusT2.text() == '已选定':
				self.count = 0
			else:
				if not self.cheatCBox.isChecked():
					self.count -= 1
					self.timerLabel.setText(str(self.count))
		elif self.count > -3:
			self.count -= 1
			self.can_select = False
			self.timerLabel.setText(str(3 + self.count))
			self.statusT1.setText('已选定')
			self.selectedT1[4 - self.round].setPixmap(QPixmap('assets/icon/{}.png'.format(self.selected)))
			self.selectedT1[4 - self.round].setScaledContents(True)
			self.paintingT2.setPixmap(QPixmap('assets/painting/{}.png'.format(self.selected_ai)))
			self.paintingT2.setScaledContents(True)
			self.selectedT2[self.round].setPixmap(QPixmap('assets/icon/{}.png'.format(self.selected_ai)))
			self.selectedT2[self.round].setScaledContents(True)
		else:
			self.can_select = True
			self.count = 10
			self.T1.append(self.selected)
			self.T2.append(self.selected_ai)
			self.round += 1
			if self.round == 5:
				self.endGame()
			else:
				if self.cheatCBox.isChecked():
					self.timerLabel.setText('...')
				self.statusT1.setText('选择中')
				self.statusT2.setText('选择中')
				self.paintingT2.setText('?')
				self.runAI()

	def confirmShishen(self):
		if self.is_running:
			self.can_select = False
			self.statusT1.setText('已选定')
		

	def endGame(self):
		self.is_running = False
		self.leftWidget.setEnabled(True)
		self.rightWidget.setEnabled(False)
		self.timer.stop()
		wr = self.AI.predict([name2idx[name] for name in self.T2], [name2idx[name] for name in self.T1])
		self.endDialog.setInfo(self.T1, self.T2, wr)
		self.endDialog.show()

	def showBanDialog(self):
		if self.banDialog.exec():
			if self.banDialog.enabled():
				self.ban = self.banDialog.getChecked()
				self.banBtn.setText('Ban(已启用)')
				self.refreshPool(self.ban)
			else:
				self.ban = []
				self.banBtn.setText('Ban(未启用)')
				self.refreshPool(self.ban)

	def showmoreDialog(self):
		self.moreDialog.show()

