import re
import json
import pandas as pd

class Parse:

    def __init__(self,filename=r'H:\Mammoth_Files\Rule_Engine\Latest\userDefined_ruleEngineParameters_56G.json.txt',attrib_def = r'H:\Mammoth_Files\Automation\Python\attributes_gtm.json'):
        self.filename=filename
        self.attrib_def = attrib_def
        self.ports = {}
        self.DRP = {}

    def parse_attributes(self):
        with open(self.filename) as fp:
            for line in fp:
                self.content =line.strip('\n')
                self.port_attribute = self.content.split('.')
                self.value = re.findall("(?<=32'h)(.*)", self.port_attribute[1])
                self.name = re.findall("(.*)(?= = 32'h)", self.port_attribute[1])
                if self.port_attribute[0]=='port':
                    self.ports.update({self.name[0]:hex(int(self.value[0],16))})
                else:
                    self.DRP.update({self.name[0]: hex(int(self.value[0], 16))})
        return self.ports, self.DRP

    def parse_attributes_with_address(self):
        with open(self.filename) as fp:
            for line in fp:
                self.content =line.strip('\n')
                self.port_attribute = self.content.split('.')
                self.value = re.findall("(?<=32'h)(.*)", self.port_attribute[1])
                self.name = re.findall("(.*)(?= = 32'h)", self.port_attribute[1])
                if self.port_attribute[0]=='port':
                    self.ports.update({self.name[0]:hex(int(self.value[0],16))})
                else:
                    self.DRP.update({self.name[0]: hex(int(self.value[0], 16))})

        with open(self.attrib_def) as self.json_data:
            self.d = json.load(self.json_data)
            self.json_data.close()
            self.d = pd.DataFrame(self.d)
            self.dT = self.d.T
            self.duals = self.dT[self.dT.dstSubBlock == 'dual']
            self.ch = self.dT[self.dT.dstSubBlock == 'CH']
            self.Reg_name = []
            self.Address = []
            

        for self.index, self.row in self.ch.iterrows():
            if self.row['dstSubBlock'] == 'CH':
                for ch in ['0','1']:
                    self.Reg_name.append('CH' + ch + '_' + str(self.index))   #'CH' + str(ch) + '_' + str(self.index)
                    if ch == '0':
                        self.Address.append(((hex((int(str(self.row['Offset']), 16) + 0x000))).strip('0x')).zfill(4))
                    elif ch == '1':
                        self.Address.append(((hex((int(str(self.row['Offset']), 16) + 0x200))).strip('0x')).zfill(4))
        for index, row in self.duals.iterrows():
            if row['dstSubBlock'] == 'dual':
                self.Reg_name.append(str(index))
                self.Address.append(((hex((int(str(row['Offset']), 16) + 0x000))).strip('0x')).zfill(4))

        self.keyd = []
        self.valued = []

        for key, value in self.DRP.iteritems():
            self.keyd.append(key)
            self.valued.append(value)

        self.DRPpd = pd.DataFrame(index=self.keyd, columns=['Value'], data=self.valued)
        self.Offsetpd = pd.DataFrame(index=self.Reg_name, columns=['Address'], data=self.Address)
        self.Output = pd.merge(self.DRPpd, self.Offsetpd, left_index=True, right_index=True)
        return self.Output.sort_index(),self.ports
