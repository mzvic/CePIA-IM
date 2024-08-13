import sys
from PyQt6 import QtWidgets, uic, QtCore
import pyvisa
import os
import pyqtgraph as pg
from time import sleep
import pyvisa


# Open RM
rm = pyvisa.ResourceManager()

#call device connected
#print("Connected VISA resources: ")
rm.list_resources()



'''
Probar con {read_async()} para realizar mediciones continuas, este comando viene incluido en PyVISA.

time = np.array([])
temp = np.array([])

    def callback(datos)

        global time, temp

        time = np.append(time, time.size)
        temp = np.append(temp, datos)

        p.plot(time, temp, clear=True)

    def read_async(self, device, command, delay=1, callback=True)
        device.read_async(command, callback, delay=1)

    self.write_command(rig_dmm, '*RST')
    self.write_command(rig_dmm, 'CONF:TEMP')
    self.write_command(rig_dmm, 'TRIG:COUN 1')

self.read_async(rig_dmm, 'MEAS?')

'''

script_directory = os.path.dirname(os.path.abspath(__file__))
ui_folder = r"\HMI_RRL_3.ui"
ui_dir = script_directory + ui_folder

'''

device_curve_folder = r"\device_curves_data"
curve_1_file = 'lakeshore_m336.txt'
curve_2_file = 'rig_sp.txt'
curve_1 = script_directory+device_curve_folder+'\\'+curve_1_file
curve_2 = script_directory+device_curve_folder+'\\'+curve_2_file
data_A = np.genfromtxt(curve_1, delimiter=',')
data_B = np.genfromtxt(curve_2, delimiter=',')
coef_A = np.polyfit(data_A[:, 0], data_A[:, 1], 2)
coef_B = np.polyfit(data_B[:, 0], data_B[:, 1], 2)
poly_A = np.poly1d(coef_A)
poly_B = np.poly1d(coef_B)

'''

class QueryThread(QtCore.QThread):
    response_received = QtCore.pyqtSignal(str)  # Señal para emitir la respuesta

    def __init__(self, device, command, interval=500, parent=None):
        super().__init__(parent)
        self.device = device
        self.command = command
        self.interval = interval  # Intervalo de tiempo entre comandos
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
    
                self.Q = self.device.query(self.command)
                self.W = self.device.write(self.command)
                caracter = '?'
                if self.command.find(caracter):
                    self.response = self.Q
                elif self.command == 0:
                    pass
                else:
                    self.response = self.W
                
                self.response_received.emit(self.response)

            except Exception as e:
                print(f"Error querying device: {e}")
            self.msleep(self.interval)



    def stop(self):
        self.running = False
        self.wait()



class Interfaz(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Interfaz,self).__init__(parent)
        self.ui=uic.loadUi(ui_dir, self)
        self.dmm_device = None
        self.query_thread = None

        # Set Window Title
        self.setWindowTitle("TEMPERATURE CONTROL - LAKESHORE MODEL 336")

        # Connection with GUI (.ui)
        self.ui.c_sp.clicked.connect(self.sp_connection)
        self.ui.c_dmm.clicked.connect(self.dmm_connection)
        self.ui.c_ls.clicked.connect(self.ls_connection)
        
        self.ui.volt_set.clicked.connect(self.voltage_set)


        #Valves definition
        self.V = 0

        
        #Se crea gráfica
        self.layout1=self.ui.verticalLayout_3
        self.PlotWidget1=pg.PlotWidget(name="Plot1", title=u'Temperature vs Time')
        
        self.PlotWidget1.setLabel('bottom', 'Time', 'min')
        self.PlotWidget1.setLabel('left', 'Temperature', '°C')
        self.PlotWidget1.setYRange(0,50)

        self.layout1.addWidget(self.PlotWidget1)

        # Auxiliar fuctions
    def query_command(self, device, command):
            query = device.query(command)
            print(query)

    def write_command(self, device, command):
          device.write(command)


    # Device Comunication
    def dmm_connection(self):
        if self.ui.c_dmm.isChecked():
            try:
                self.rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
                self.write_command(self.rig_dmm, "*RST") # Reset the instrument
                sleep(2)
                self.write_command(self.rig_dmm, ":FUNC:CURR:DC") # Set current DC function
                self.write_command(self.rig_dmm, ":CURR:DC:RANG 1A") #Set 1A range
                sleep(2)
                self.write_command(self.rig_dmm, ":MEAS AUTO") # Set automatic measurameter
                sleep(2)

                command = ":MEASure:CURRent:DC?"  
                self.query_thread = QueryThread(self.rig_dmm, command, interval=500)
                self.query_thread.response_received.connect(self.response)
                self.query_thread.start()

            except Exception as err:
                print(f'error {err}')


            print("Digital MultiMeter Connected!")

        else:
            if self.query_thread:
                self.query_thread.stop()
            if self.rig_dmm:
                self.dmm_device.close()
            print("Digital MultiMeter Disconnected!")
    
    def response(self, response):
        print(round(float(response), 2))
        print(f"IDN: {response}")
        print(type(response))
        self.ui.curr_m.setText(str(self.response))

    def sp_connection(self):
        if self.ui.c_sp.isChecked():

            #rig_sp  = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C170700397::INSTR')
            print("Supply Power Connected!")
        else:

            #rig_sp.close()
            print("Supply Power Disconnected!")

    def ls_connection(self):
        if self.ui.c_ls.isChecked():

            #ls = rm.open_resource("COM5", baud_rate=57600, parity=constants.Parity.odd, data_bits=7)
            #self.write_command(ls, "*RST") # Reset the instrument
            #time.sleep(1)
            #self.write_command(ls, ":INP:CHAN 3") # Set current DC function
            #self.write_command(ls, ":INP:RANG 1") #Set 1A range
            #self.write_command(ls, ":UNIT:TEMP CEL") #Set 1A range
            #self.write_command(ls, ":TEMP:SCAL 0.01") #Set 1A range
            #time.sleep(1)
        
            #while True:
                #meas_ls = self.query_command(ls, ":MEAS:TEMP?")
                #self.ui.temp_m.setText(meas_ls)
                #time.sleep(0.5)

            print("LakeShore Model 336 Connected!")
        else:

            #ls.close()
            print("LakeShore Model 336 Disconnected!")


        # Principal fuctions
    def voltage_set(self):
        
        self.V = round(float(self.ui.volt_c.text()), 2)
        #self.write_command(rig_sp, "*RST")
        #time.sleep(1)
        #self.write_command(rig_sp, ":INST CH1")
        #self.write_command(rig_sp, ":VOLT:PROT 15")
        #self.write_command(rig_sp, f':VOLT {V}')
        #self.write_command(rig_sp, ":OUTP CH1 ON")
        #time.sleep(1)

        if self.V == 0:
            pass

        elif self.V > 15:
            sleep(0.5)
            self.ui.volt_c.setText("EXCEEDS MAX. VOLTAGE")

        elif self.V < 0:
            self.ui.volt_c.setText("NEGATIVE VOLT. ERROR")

        else:
            while self.V <= 15:
                #meas_sp = self.query_command(rig_sp, ":MEAS:VOLT:DC? CH1")
                #self.ui.volt_m.setText(str(meas_sp))
                sleep(1)
                sleep(1)




if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    window = Interfaz()
    window.show()
    sys.exit(app.exec())