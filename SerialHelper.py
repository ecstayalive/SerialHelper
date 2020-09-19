'''
@author Bruce Hou
@date 2019/01/15
@update 2020/09/06
@detail
'''
import sys
import gc
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from SerialHelper_gui import Ui_Form
import pyqtgraph as pg


class Pyqt5_Serial(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(Pyqt5_Serial, self).__init__()
        self.setupUi(self)
        self.open = False
        self.setWindowTitle("SerialHelper")
        self.ser = serial.Serial()

        self.flag = 2
        self.data = []
        self.x = []
        self.tempx = []
        self.count = 0

        self.tssend = False
        # Set the number of received data and sent data to zero
        self.data_num_received = 0
        self.lineEdit.setText(str(self.data_num_received))
        self.data_num_sended = 0
        self.lineEdit_2.setText(str(self.data_num_sended))
        self.idx = 0
        self.historyLength = 200
        # initialize functions
        self.init()
        # Set up the drawing window
        self.p1, self.curve = self.set_graph_ui()

    def init(self):
        # Serial port detection button
        if not self.open:
            self.timer2 = QTimer()
            self.timer2.timeout.connect(self.port_check)
            self.timer2.start(50)
        self.s1__box_1.clicked.connect(self.port_check)

        # Serial information display
        self.s1__box_2.currentTextChanged.connect(self.port_imf)

        # Open the serial port button
        self.open_button.clicked.connect(self.port_open)

        # Close the serial port button
        self.close_button.clicked.connect(self.port_close)

        # Send data button
        self.s3__send_button.clicked.connect(self.data_send)

        # Send data regularly
        self.timer_send = QTimer()
        self.timer_send.timeout.connect(self.data_send)
        self.timer_send_cb.stateChanged.connect(self.data_send_timer)

        # Timer receive data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.data_receive)

        # Clear send window
        self.s3__clear_button.clicked.connect(self.send_data_clear)

        # Clear the receive window
        self.s2__clear_button.clicked.connect(self.receive_data_clear)

        # Call drawing
        self.timer1 = pg.QtCore.QTimer()
        self.timer1.timeout.connect(self.plot_data)  # Call the plotData function regularly
        self.timer1.start(10)  # How many ms to call once

    ''' Serial port processing function '''

    # Serial port detection
    def port_check(self):
        # Detect all existing serial ports and store the information in the dictionary
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.s1__box_2.clear()
        for port in port_list:
            self.Com_Dict["%s" % port[0]] = "%s" % port[1]
            self.s1__box_2.addItem(port[0])
        if len(self.Com_Dict) == 0:
            pass

    # Serial port information
    def port_imf(self):
        # Display detailed information of the selected serial port

        imf_s = self.s1__box_2.currentText()
        if imf_s != "":
            pass

    # Open the serial port
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
            QMessageBox.critical(self, "Port Error", "This serial port cannot be opened!")
            return None

        # Open the serial port receiving timer, the period is 2ms
        self.timer.start(2)

        if self.ser.isOpen():
            self.open_button.setEnabled(False)
            self.close_button.setEnabled(True)
            self.formGroupBox1.setTitle("Serial port status (opened)")

            self.flag = 1

    # Close the serial port
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
        # Set the number of received data and sent data to zero
        self.data_num_received = 0
        self.lineEdit.setText(str(self.data_num_received))
        self.data_num_sended = 0
        self.lineEdit_2.setText(str(self.data_num_sended))
        self.formGroupBox1.setTitle("Serial port status (closed)")
        # delete the variable
        del self.dat
        gc.collect()
        if self.flag == 1:
            self.flag = 0

    ''' Send function '''

    # Send data
    def data_send(self):
        if self.ser.isOpen():
            input_s = self.s3__send_text.toPlainText()
            if input_s != "":
                # Non-empty string
                if self.hex_send.isChecked():
                    # send data with hex format
                    input_s = input_s.strip()
                    send_list = []
                    while input_s != '':
                        try:
                            num = int(input_s[0:2], 16)
                        except ValueError:
                            QMessageBox.critical(
                                self, 'wrong data', 'Please enter the hexadecimal data, separated by spaces!')
                            return None
                        input_s = input_s[2:].strip()
                        send_list.append(num)
                    input_s = bytes(send_list)
                else:
                    # send data with ascii format
                    input_s = (input_s + '\r\n').encode('utf-8')

                num = self.ser.write(input_s)
                self.data_num_sended += num
                self.lineEdit_2.setText(str(self.data_num_sended))
                if not self.tssend:
                    self.s3__send_text.clear()
        else:
            pass

    # Send data regularly
    def data_send_timer(self):
        if self.timer_send_cb.isChecked():
            self.tssend = True
            self.timer_send.start(int(self.lineEdit_3.text()))
            self.lineEdit_3.setEnabled(False)
        else:
            self.tssend = False
            self.timer_send.stop()
            self.lineEdit_3.setEnabled(True)

    # Clear display
    def send_data_clear(self):
        self.s3__send_text.setText("")

    ''' Receiving data function '''

    # Receiving data
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
            # show datas with hex format
            if self.hex_receive.checkState():
                out_s = ''
                for i in range(0, len(data)):
                    out_s = out_s + '{:02X}'.format(data[i]) + ' '
                self.s2__receive_text.insertPlainText(out_s)
            else:
                # The string received by the serial port is b'123'
                # which must be converted into a unicode string to be output to the window
                self.s2__receive_text.insertPlainText(
                    data.decode('iso-8859-1'))

            # Count the number of characters received
            self.data_num_received += num
            self.lineEdit.setText(str(self.data_num_received))

            # Get the text cursor
            textCursor = self.s2__receive_text.textCursor()
            # Scroll to the bottom
            textCursor.movePosition(textCursor.End)
            # Set the cursor to text
            self.s2__receive_text.setTextCursor(textCursor)

        else:
            pass

    # Clear display
    def receive_data_clear(self):
        self.s2__receive_text.setText("")

    ''' Figure layout settings and drawing functions '''

    def set_graph_ui(self):

        # pg global variable setting function
        # antialias=True turns on curve anti-aliasing
        pg.setConfigOptions(antialias=True)

        pg.setConfigOption('background', 'w')  # Set the background to white
        pg.setConfigOption('foreground', 'k')

        # Create pg layout to realize automatic management of data interface layout
        win = pg.GraphicsLayoutWidget()

        # The pg drawing window can be added to the graph_layout in the GUI as a widget
        # and of course it can also be added to all other containers in Qt
        self.PyqtgraphWorkspace.addWidget(win)

        p1 = win.addPlot()  # Add the first drawing window

        # Set legend
        p1.addLegend()
        p1.setLabel('left', text='voltage', color='#000000')  # y-axis setting function
        # p1.showGrid(x=True, y=True)  # Raster setting function
        p1.setLogMode(x=False, y=False)  # False represents the linear axis, and True represents the logarithmic axis
        p1.setLabel('bottom', text='time', color='#000000', units='s')  # X axis setting function
        p1.showGrid(x=True, y=True)  # Open the table of X and Y
        p1.setRange(xRange=[0, self.historyLength])
        # p1.setRange(xRange=[0, 100], yRange=[-1.2, 1.2], padding=0)
        # p1.setLabel(axis='left', text='y / V')  # Keep left
        # p1.setLabel(axis='bottom', text='x / point')
        # p1.setTitle('printing')  # The name of the table
        # self.curve = p1.plot(x=self.x, y=self.data, pen='r', name='values', symbolBrush=(255,0,0))
        self.curve = p1.plot(x=self.x, y=self.data, pen='r', name='values')
        return p1, self.curve

    def plot_data(self):
        # The inner scope wants to change the outer scope variable
        try:
            if self.count <= self.historyLength:
                self.data.append(self.dat)
                self.count += 1
                self.tempx.append(self.historyLength - self.count)
                self.x = self.tempx[::-1]
                # print(len(self.x), len(self.data))
            else:
                self.data[:-1] = self.data[1:]
                self.data[self.count - 1] = self.dat
                # print(len(self.x), len(self.data))
        except AttributeError or TypeError:
            pass
        finally:
            self.curve.setData(x=self.x, y=self.data)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myshow = Pyqt5_Serial()
    myshow.show()
    sys.exit(app.exec_())
