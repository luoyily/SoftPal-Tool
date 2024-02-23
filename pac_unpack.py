import struct
from pathlib import Path
import argparse

class PacFile:
    def __init__(self, bytes_data):
        self.bytes_data = bytearray(bytes_data)
        self.file_name_bytes = self.bytes_data[:32]
        self.file_name = str(self.file_name_bytes[:self.file_name_bytes.find(b'\x00')],encoding='ascii')
        self.size = struct.unpack('I', self.bytes_data[32:36])[0]
        self.offset = struct.unpack('I', self.bytes_data[36:40])[0]


class PacArchive:
    def __init__(self, pac_path: str):
        self.pac_path = Path(pac_path)
        self.out_path = Path(self.pac_path.stem)
        self.file_list:list[PacFile] = []
        self.file_name_id_map = {}
        self.hfile = open(pac_path, 'rb')
        self.hfile.seek(2088)
        self.file_list_start = 2052
        # i.e. the offset of the first file
        self.file_list_end = struct.unpack('I', self.hfile.read(4))[0]
        index = 0
        for i in range(self.file_list_start,self.file_list_end,40):
            self.hfile.seek(i)
            file_info_bytes = self.hfile.read(40)
            item = PacFile(file_info_bytes)
            self.file_list.append(item)
            self.file_name_id_map[item.file_name] = index
            index += 1
    
    def print_file_list(self):
        for k,v in self.file_name_id_map.items():
            print(f'{v} {k}')

    def export_file(self,index:int):
        self.out_path.mkdir(exist_ok=True)
        file = self.file_list[index]
        self.hfile.seek(file.offset)
        data = self.hfile.read(file.size)
        f_out = open(self.out_path/file.file_name,'wb')
        f_out.write(data)
        f_out.close()

    def export_all_file(self):
        for i in range(len(self.file_list())):
            self.export_file(i)

    def export_file_by_names(self,names: list):
        for name in names:
            index = self.file_name_id_map[name]
            self.export_file(index)

# python run
# pac = PacArchive('data.pac')
# pac.print_file_list()
# pac.export_file_by_names(['SCRIPT.SRC','TEXT.DAT'])
# pac.hfile.close()

# cli
parser = argparse.ArgumentParser()
parser.add_argument('-pac', help='Pac archive file',required=True)
parser.add_argument('-p',action='store_true', help='Print file list')
parser.add_argument('-ua',action='store_true', help='Unpack all files')
parser.add_argument('-un', nargs='*', help='Files to be unpacked')

args = parser.parse_args()

pac = PacArchive(args.pac)

if args.p:
    pac.print_file_list()
if args.ua:
    pac.export_all_file()
elif args.un:
    pac.export_file_by_names(args.un)