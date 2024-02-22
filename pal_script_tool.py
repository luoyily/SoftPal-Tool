import struct
import json
import argparse

class PalScriptBase:
    def __init__(self, bytecodes: bytes):
        self.bytecodes = bytearray(bytecodes)

    def __str__(self) -> str:
        bytes_to_str = self.bytecodes
        if len(self.bytecodes) > 36:
            bytes_to_str = self.bytecodes[:36]
        return ' '.join(['%02X' % x for x in bytes_to_str])

    def dword2int(self, dword):
        return struct.unpack('I', dword)[0]

    def int2dword(self, i):
        return struct.pack('I', i)

    def modify_bytes(self, offset, bytecodes):
        self.bytecodes[offset:offset+len(bytecodes)] = bytecodes

    def compile_script(self):
        return self.bytecodes


class PalScriptTextShow(PalScriptBase):
    def __init__(self, bytecodes, offset):
        # 32 bytes
        super().__init__(bytecodes)

        self.text = self.bytecodes[4:8]
        self.name = self.bytecodes[12:16]
        self.text_offset = self.dword2int(self.text)
        self.name_offset = self.dword2int(self.name)
        self.offset = offset
        self.has_name = bool(self.name != b'\xFF\xFF\xFF\x0F')

    def modify_text(self, text_offset: int):
        self.text = self.int2dword(text_offset)

    def modify_name(self, name_offset: int):
        self.name = self.int2dword(name_offset)

    def apply_change(self):
        self.bytecodes[4:8] = self.text
        self.bytecodes[12:16] = self.name


class PalScriptSelect(PalScriptBase):
    def __init__(self, bytecodes: bytes, offset):
        # 16 bytes
        # 1F 00 01 00 83 99 00 00 17 00 01 00 02 00 06 00
        super().__init__(bytecodes)
        self.text = self.bytecodes[4:8]
        self.text_offset = self.dword2int(self.text)
        self.offset = offset
        self.has_name = False

    def modify_text(self, text_offset: int):
        self.text = self.int2dword(text_offset)

    def apply_change(self):
        self.bytecodes[4:8] = self.text


class PalText:
    def __init__(self, bytes_data, offset=0):
        self.bytes_data = bytearray(bytes_data)
        self.index = self.bytes_data[:4]
        self.text = self.bytes_data[4:]
        self.text_str = str(self.text, encoding='sjis')
        self.offset = offset
        self.new_offset = 0
        self.is_modified = False
        self.has_parsed_script_ref = False

    def __str__(self) -> str:
        index_str = ' '.join(['%02X' % x for x in self.index])
        return f'{index_str} {self.text_str}'

    def replace_unsupported_text_in_draw(self):
        replace_list = [b'\xA1\xA1']
        new_bytes_data = bytearray()
        i = 0
        for i in range(0, len(self.bytes_data), 2):
            byte_t = self.bytes_data[i:i+2]
            if byte_t not in replace_list:
                new_bytes_data += byte_t
        self.bytes_data = new_bytes_data

    def convert_encoding(self, target_encoding='gbk'):
        if not self.is_modified:
            gbk_bytes = self.text_str.encode(
                target_encoding, errors='replace').replace(b'?', b'??')
            self.text = gbk_bytes

    def modify_text(self, new_text: str, encoding='gbk'):
        self.text = new_text.encode(
            encoding, errors='replace').replace(b'?', b'??')
        self.is_modified = True

    def apply_change(self):
        self.bytes_data = self.index+self.text

    def compile_text(self):
        self.replace_unsupported_text_in_draw()
        return self.bytes_data+b'\x00'


class PalTextPack:
    def __init__(self, bytes_data):
        self.bytes_data = bytes_data
        self.text_obj: list[PalText] = []
        self.modified_text_obj: list[PalText] = []
        self.offset_id_map = {}
        i = 0
        offset = 16
        while offset < len(self.bytes_data):
            text_end = self.bytes_data.find(b'\x00', offset+4)
            item = PalText(self.bytes_data[offset:text_end], offset)
            self.text_obj.append(item)
            self.offset_id_map[offset] = i
            i += 1
            offset = text_end + 1

    def convert_all_encoding(self, target_encoding='gbk'):
        for i in range(len(self.text_obj)):
            text = self.text_obj[i]
            text.convert_encoding(target_encoding)
            text.apply_change()
            self.text_obj[i] = text

    def find_text_by_offset(self, offset: int, return_id=False):
        index = self.offset_id_map[offset]
        text = self.text_obj[index]
        if return_id:
            return (index, text)
        return text

    def modify_text_by_offset(self, offset: int, new_text: str):
        text_index = self.offset_id_map[offset]
        text_obj_t = self.text_obj[text_index]
        text_obj_t.modify_text(new_text)
        text_obj_t.apply_change()
        # self.text_obj[text_index] = text_obj_t
        self.modified_text_obj.append(text_obj_t)

    def rebuild(self, convert_encoding='gbk', save_path='TEXT_Rebuild.DAT'):
        self.convert_all_encoding(convert_encoding)
        # no encrypt head
        new_bytes_data = b'\x00'+self.bytes_data[1:16]
        new_offset = self.text_obj[0].offset
        for i in range(len(self.text_obj)):
            text = self.text_obj[i]

            text_bytes = text.compile_text()
            new_bytes_data += text_bytes
            text.new_offset = new_offset
            self.text_obj[i] = text
            new_offset += len(text_bytes)

        # append write
        for text in self.modified_text_obj:
            text_bytes = text.compile_text()
            new_bytes_data += text_bytes
            # Find the original text and change its new offset.
            old_text_index, old_text = self.find_text_by_offset(
                text.offset, return_id=True)
            old_text.new_offset = new_offset
            self.text_obj[old_text_index] = old_text
            new_offset += len(text_bytes)

        f_out = open(save_path, 'wb')
        f_out.write(new_bytes_data)
        f_out.close()
        return self.text_obj


class PalScriptDisassembler:
    def __init__(self, script_path, text_path):
        f_script = open(script_path, 'rb')
        self.script = f_script.read()
        f_script.close()
        f_text = open(text_path, 'rb')
        self.text = f_text.read()
        f_text.close()
        self.text_pack = PalTextPack(self.text)
        self.parsed_script_pack: list[PalScriptTextShow] = []
        self.base_script = PalScriptBase(self.script)
        self.script_pack_offset_id_map = {}
        content = self.script
        n_scripts = 0

        for i in range(0, len(content)-4, 4):
            dword = content[i:i+4]
            if dword == b'\x17\x00\x01\x00':
                after_hi = content[i+6:i+8]
                after_lo = content[i+4:i+6]
                #  02 0f 10 11 12 13 14
                dialog_text_type = [b'\x02\x00', b'\x0f\x00', b'\x10\x00',
                                    b'\x11\x00', b'\x12\x00', b'\x13\x00', b'\x14\x00']
                if after_hi == b'\x02\x00' and after_lo in dialog_text_type:
                    item = PalScriptTextShow(content[i-24:i+8], offset=i-24)
                    self.parsed_script_pack.append(item)
                    self.script_pack_offset_id_map[i-24] = n_scripts
                    n_scripts += 1
                elif after_hi == b'\x06\x00' and after_lo == b'\x02\x00':
                    item = PalScriptSelect(content[i-8:i+8], offset=i-8)
                    self.parsed_script_pack.append(item)
                    self.script_pack_offset_id_map[i-8] = n_scripts
                    n_scripts += 1

    def find_script_obj_by_offset(self, offset: int):
        script_index = self.script_pack_offset_id_map[offset]
        return self.parsed_script_pack[script_index]

    def export_json(self, path='script_export.json'):
        script_json = []
        for script in self.parsed_script_pack:
            text_offset = script.text_offset
            text_obj = self.text_pack.find_text_by_offset(text_offset)
            text_str = text_obj.text_str
            item = {
                "Text": {
                    "Original": text_str,
                    "Translate": text_str,
                    "TextOffset": text_offset
                },
                "Name": None,
                "ScriptOffset": script.offset
            }
            if script.has_name:
                name_offset = script.name_offset
                text_obj = self.text_pack.find_text_by_offset(name_offset)
                name_str = text_obj.text_str
                name_dict = {
                    "Original": name_str,
                    "Translate": name_str,
                    "TextOffset": name_offset
                }
                item["Name"] = name_dict
            script_json.append(item)
        export_f = open(path, 'w', encoding='utf-8')
        json.dump(script_json, export_f, ensure_ascii=False,indent=4)
        export_f.close()

    def add_text_is_ref_info(self):
        script_ref_offset = []
        for s in self.parsed_script_pack:
            if s.has_name:
                script_ref_offset.append(s.name_offset)
            script_ref_offset.append(s.text_offset)
        for i in range(len(self.text_pack.text_obj)):
            text = self.text_pack.text_obj[i]
            if text.offset in script_ref_offset:
                text.has_parsed_script_ref = True
            self.text_pack.text_obj[i] = text

    def rebuild_script_text_by_json(self, json_path: str, new_script_path='SCRIPT.SRC', new_text_path='TEXT.DAT'):
        f_json = open(json_path, 'r', encoding='utf-8')
        script = json.load(f_json)
        f_json.close()

        for i in script:
            text = i["Text"]["Translate"]
            text_offset = i["Text"]["TextOffset"]
            script_offset = i["ScriptOffset"]
            if i["Name"]:
                name = i["Name"]["Translate"]
                name_offset = i["Name"]["TextOffset"]
                self.text_pack.modify_text_by_offset(name_offset, name)

            self.text_pack.modify_text_by_offset(text_offset, text)
        # self.add_text_is_ref_info()
        self.text_pack.rebuild(save_path=new_text_path)

        for i in script:
            text = i["Text"]["Translate"]
            text_offset = i["Text"]["TextOffset"]
            script_offset = i["ScriptOffset"]

            script_obj = self.find_script_obj_by_offset(script_offset)
            new_text_obj = self.text_pack.find_text_by_offset(text_offset)
            new_text_offset = new_text_obj.new_offset
            script_obj.modify_text(new_text_offset)

            if i["Name"]:
                name = i["Name"]["Translate"]
                name_offset = i["Name"]["TextOffset"]
                new_text_obj = self.text_pack.find_text_by_offset(name_offset)
                new_text_offset = new_text_obj.new_offset
                script_obj.modify_name(new_text_offset)
            script_obj.apply_change()
            script_bytecodes = script_obj.compile_script()
            self.base_script.modify_bytes(script_offset, script_bytecodes)
        f_script = open(new_script_path, 'wb')
        f_script.write(self.base_script.bytecodes)
        f_script.close()

    def script_text_num_check(self):
        script_num = len(self.parsed_script_pack)
        script_ref_text_num = 0
        script_ref_offset = []
        text_offsets = []
        first_dialog_text_offset = self.parsed_script_pack[0].text_offset
        first_dialog_text_index = self.text_pack.offset_id_map[first_dialog_text_offset]
        for s in self.parsed_script_pack:
            if s.has_name:
                script_ref_text_num += 2
                script_ref_offset.append(s.name_offset)
            else:
                script_ref_text_num += 1
            script_ref_offset.append(s.text_offset)
        for i in self.text_pack.text_obj:
            if i.offset not in script_ref_offset and i.offset > first_dialog_text_offset:
                text_offsets.append(i.offset)
        text_num_total = len(self.text_pack.text_obj)

        show_text_num = text_num_total-first_dialog_text_index
        print('Offset of text not referenced in parsed scripts:')
        print(text_offsets)
        print(f'Parsed Script Num:{script_num}\nTotal Text Num:{text_num_total}')
        print(f'Show Text Num:{show_text_num}\nScript Ref Text Num:{script_ref_text_num}')


ds = PalScriptDisassembler('data/SCRIPT.SRC', 'data/TEXT.DAT')

# Export json
# ds.export_json('script_export.json')
# Rebuild
# ds.rebuild_script_text_by_json('script_export.json')
# ds.script_text_num_check()

# Don't like command line running? Just comment out the code below
parser = argparse.ArgumentParser()
parser.add_argument('-d', action='store_true', help='Export data/SCRIPT.SRC, data/TEXT.DAT to json')
parser.add_argument('-b', action='store_true', help='Rebuild Script and Text by json')

args = parser.parse_args()

if args.d:
    ds.export_json('script_export.json')
elif args.b:
    ds.rebuild_script_text_by_json('script_export.json')
    ds.script_text_num_check()