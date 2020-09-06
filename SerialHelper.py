# coding=utf-8
import sys
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from SerialHelper_gui import Ui_Form
import pyqtgraph as pg
import array


class Pyqt5_Serial(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(Pyqt5_Serial, self).__init__()
        self.setupUi(self)
        self.open = False
        self.setWindowTitle("串口助手")
        self.ser = serial.Serial()
        # self.port_check()
        # plot_data
        self.data = []
        self.x = []
        self.tempx = []
        self.count = 0
        # 接收数据和发送数据数目置零
        self.data_num_received = 0
        self.lineEdit.setText(str(self.data_num_received))
        self.data_num_sended = 0
        self.lineEdit_2.setText(str(self.data_num_sended))
        self.idx = 0
        self.historyLength = 200
        # initialize functions
        self.init()
        # 设置绘图窗口
        self.p1, self.curve = self.set_graph_ui()

    def init(self):
        # 串口检测按钮
        if not self.open:
            self.timer2 = QTimer()
            self.timer2.timeout.connect(self.port_check)
            self.timer2.start(50)
        self.s1__box_1.clicked.connect(self.port_check)

        # 串口信息显示
        self.s1__box_2.currentTextChanged.connect(self.port_imf)

        # 打开串口按钮
        self.open_button.clicked.connect(self.port_open)

        # 关闭串口按钮
        self.close_button.clicked.connect(self.port_close)

        # 发送数据按钮
        self.s3__send_button.clicked.connect(self.data_send)

        # 定时发送数据
        self.timer_send = QTimer()
        self.timer_send.timeout.connect(self.data_send)
        self.timer_send_cb.stateChanged.connect(self.data_send_timer)

        # 定时器接收数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.data_receive)

        # 清除发送窗口
        self.s3__clear_button.clicked.connect(self.send_data_clear)

        # 清除接收窗口
        self.s2__clear_button.clicked.connect(self.receive_data_clear)
        # 调用绘图
        self.timer1 = pg.QtCore.QTimer()
        self.timer1.timeout.connect(self.plot_data)  # 定时调用plotData函数
        self.timer1.start(10)  # 多少ms调用一次

    # 串口检测
    def port_check(self):
        # 检测所有存在的串口，将信息存储在字典中
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.s1__box_2.clear()
        for port in port_list:
            self.Com_Dict["%s" % port[0]] = "%s" % port[1]
            self.s1__box_2.addItem(port[0])
        if len(self.Com_Dict) == 0:
            pass

    # 串口信息
    def port_imf(self):
        # 显示选定的串口的详细信息
        imf_s = self.s1__box_2.currentText()
        if imf_s != "":
            pass

    # 打开串口
    def port_open(self):
        self.ser.port = self.s1__box_2.currentText()
        self.ser.baudrate = int(self.s1__box_3.currentText())
        self.ser.bytesize = int(self.s1__box_4.currentText())
        self.ser.stopbits = int(self.s1__box_6.currentText())
        self.ser.parity = self.s1__box_5.currentText()

        try:
            self.ser.open()
            self.isportopen = True
        except:
            QMessageBox.critical(self, "Port Error", "此串口不能被打开！")
            return None

        # 打开串口接收定时器，周期为2ms
        self.timer.start(2)

        if self.ser.isOpen():
            self.open_button.setEnabled(False)
            self.close_button.setEnabled(True)
            self.formGroupBox1.setTitle("串口状态（已开启）")

    # 关闭串口
    def port_close(self):
        self.timer.stop()
        self.timer_send.stop()
        try:
            self.ser.close()
        except:
            pass
        self.open_button.setEnabled(True)
        self.close_button.setEnabled(False)
        self.lineEdit_3.setEnabled(True)
        # 接收数据和发送数据数目置零
        self.data_num_received = 0
        self.lineEdit.setText(str(self.data_num_received))
        self.data_num_sended = 0
        self.lineEdit_2.setText(str(self.data_num_sended))
        self.formGroupBox1.setTitle("串口状态（已关闭）")

    # 发送数据
    def data_send(self):
        if self.ser.isOpen():
            input_s = self.s3__send_text.toPlainText()
            if input_s != "":
                # 非空字符串
                if self.hex_send.isChecked():
                    # hex发送
                    input_s = input_s.strip()
                    send_list = []
                    while input_s != '':
                        try:
                            num = int(input_s[0:2], 16)
                        except ValueError:
                            QMessageBox.critical(
                                self, 'wrong data', '请输入十六进制数据，以空格分开!')
                            return None
                        input_s = input_s[2:].strip()
                        send_list.append(num)
                    input_s = bytes(send_list)
                else:
                    # ascii发送
                    input_s = (input_s + '\r\n').encode('utf-8')

                num = self.ser.write(input_s)
                self.data_num_sended += num
                self.lineEdit_2.setText(str(self.data_num_sended))
        else:
            pass

    # 接收数据
    def data_receive(self):
        try:
            num = self.ser.inWaiting()
        except:
            self.port_close()
            return None
        if num > 0:
            data = self.ser.read(num)
            try:
                self.dat = float(self.ser.readline())
            except ValueError:
                pass
            num = len(data)
            # hex显示
            if self.hex_receive.checkState():
                out_s = ''
                for i in range(0, len(data)):
                    out_s = out_s + '{:02X}'.format(data[i]) + ' '
                self.s2__receive_text.insertPlainText(out_s)
            else:
                # 串口接收到的字符串为b'123',要转化成unicode字符串才能输出到窗口中去
                self.s2__receive_text.insertPlainText(
                    data.decode('iso-8859-1'))

            # 统计接收字符的数量
            self.data_num_received += num
            self.lineEdit.setText(str(self.data_num_received))

            # 获取到text光标
            textCursor = self.s2__receive_text.textCursor()
            # 滚动到底部
            textCursor.movePosition(textCursor.End)
            # 设置光标到text中去
            self.s2__receive_text.setTextCursor(textCursor)

        else:
            pass

    # 定时发送数据
    def data_send_timer(self):
        if self.timer_send_cb.isChecked():
            self.timer_send.start(int(self.lineEdit_3.text()))
            self.lineEdit_3.setEnabled(False)
        else:
            self.timer_send.stop()
            self.lineEdit_3.setEnabled(True)

    def set_graph_ui(self):

        pg.setConfigOptions(antialias=True)  # pg全局变量设置函数，antialias=True开启曲线抗锯齿

        pg.setConfigOption('background', 'w')  # 背景设置为白色
        pg.setConfigOption('foreground', 'k')

        win = pg.GraphicsLayoutWidget()  # 创建pg layout，可实现数据界面布局自动管理

        # pg绘图窗口可以作为一个widget添加到GUI中的graph_layout，当然也可以添加到Qt其他所有的容器中
        self.PyqtgraphWorkspace.addWidget(win)

        p1 = win.addPlot()  # 添加第一个绘图窗口
        p1.setLabel('left', text='voltage', color='#000000')  # y轴设置函数
        # p1.showGrid(x=True, y=True)  # 栅格设置函数
        p1.setLogMode(x=False, y=False)  # False代表线性坐标轴，True代表对数坐标轴
        p1.setLabel('bottom', text='time', color='#000000', units='s')  # x轴设置函数
        p1.showGrid(x=True, y=True)  # 把X和Y的表格打开
        p1.setRange(xRange=[0, self.historyLength])
        # p1.setRange(xRange=[0, 100], yRange=[-1.2, 1.2], padding=0)
        # p1.setLabel(axis='left', text='y / V')  # 靠左
        # p1.setLabel(axis='bottom', text='x / point')
        # p1.setTitle('printing')  # 表格的名字
        self.curve = p1.plot(x=self.x, y=self.data, pen='r', name='values')
        return p1, self.curve

    def plot_data(self):
        # 内部作用域想改变外部域变量
        try:
            if self.count < self.historyLength:
                self.data.append(self.dat)
                self.tempx.append(self.historyLength - self.count)
                self.x = self.tempx[::-1]
                self.count += 1
            else:
                self.data[:-1] = self.data[1:]
                self.data[self.count - 1] = self.dat
        except AttributeError or TypeError:
            pass
        self.curve.setData(x=self.x, y=self.data)

    # 清除显示

    def send_data_clear(self):
        self.s3__send_text.setText("")

    def receive_data_clear(self):
        self.s2__receive_text.setText("")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myshow = Pyqt5_Serial()
    myshow.show()
    sys.exit(app.exec_())
