## About

Pal Engine 逆向工程。本地化，脚本解析与编辑/重建工具

引擎特征：

​	目录中有：`dll/Pal.dll`

部分使用此引擎的会社与别称：

Softpal, Amuse-Craft ,CRYSTALiA, Hearts,Us:track, piriri!,Unison Shift...

### 工具使用方法

0. 本项目Python版本：3.10.9，其他版本不清楚能否运行

1. Pac解包：

   ```
   usage: pac_unpack.py [-h] -pac PAC [-p] [-ua] [-un [UN ...]]
   
   options:
     -h, --help    show this help message and exit
     -pac PAC      Pac archive file
     -p            Print file list
     -ua           Unpack all files
     -un [UN ...]  Files to be unpacked
   ```

   example：

   ```
   python pac_unpack.py -pac data.pac -un SCRIPT.SRC
   ```

2. Pal文件解密：

   ```
   usage: pal_file_decrypt.py [-h] [-f F]
   
   options:
     -h, --help  show this help message and exit
     -f F        File to be decrypted
   ```

3. 导出JSON与重打包：

   放置解密后的SCRIPT.SRC与TEXT.DAT在程序data目录下，执行对应命令。

```
usage: pal_script_tool.py [-h] [-d] [-b]

options:
  -h, --help  show this help message and exit
  -d          Export data/SCRIPT.SRC, data/TEXT.DAT to json
  -b          Rebuild Script and Text by json
```

2. 内容编辑：

   以下为解析后的脚本样本，Translate字段中填入新的文本即可，其他字段请勿修改。

```json
{
    "Text": {
        "Original": "「やーっと起きた」",
        "Translate": "「やーっと起きた」",
        "TextOffset": 7638
    },
    "Name": {
        "Original": "少女",
        "Translate": "少女",
        "TextOffset": 7661
    },
    "ScriptOffset": 444044
}
```

### 当前支持解析的字节码

1. Text Show：Hi 00 02 Lo 00 02, 00 0F, 00 10, 00 11, 00 12, 00 13, 00 14 
2. Select: Hi 00 06 Lo 00 02

### 其他

1. 仅支持原始文本编码为sjis的游戏，目标编码为GBK，需要修改字体编码与编码范围校验。

2. 一般情况，重建的脚本与文本可直接放到游戏data文件夹下，直接启动游戏即可（免封包免加密）

3. 支持编辑的内容：对话文本，对话角色名，选项文本

4. 在引擎最大演出文本长度128字节内，可以写任意长度文本

5. 暂未解析的脚本所引用的文本将仅转换编码并保持原地不动，避免了因脚本解析不全而导致游戏读取到错误文本

6. 引擎版本可能有差异，本项目不一定适用于所有版本。

7. 图片，字体，窗口文本，字体编码，编码范围检验修改可以自行学习，未来可能会补充文章。

8. 分析文章待更新。

**注**：本项目仅供程序学习与研究，不包含移除游戏DRM的功能，不提供任何游戏样本，使用造成的任何版权/法律问题与本项目作者无关。

**Note**: This project is for program learning and research only, it does not contain the function of removing game DRM, it does not provide any game samples, and any copyright/legal issues caused by its use have nothing to do with the author of this project.
