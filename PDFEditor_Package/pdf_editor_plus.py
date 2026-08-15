"""
PDF Editor Pro - 功能完善的 PDF 编辑工具（增强版 v2.2）
=====================================================
在原版基础上新增「内容级编辑」能力：
  · 文字：修改内容、增删、改字号/字体/颜色/位置
  · 图片：替换、缩放、移动、删除
  · 表格：增删行列、修改单元格内容、调整列宽行高
  · 页面级：以上所有修改最终重新排版输出为新 PDF

v2.2 修复 - 文字输出黑方块问题：
  - 建立完整字体名映射表（覆盖所有已知变体名）
  - 解析时即清洗空字符 \\x00 和控制字符
  - 注册多个中文字体备选（WenQuanYi/NotoSansSC/MiSans/AliPuHui）
  - 生成时双重保障：映射 → 注册名 → 回退链
  - 字体可用性预检查，提前发现不可绘制文字
"""

# ── GUI 部分在 headless 环境下可选导入 ────────────────
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk, scrolledtext, colorchooser, simpledialog
    _HAS_TK = True
except ImportError:
    _HAS_TK = False
    class _Dummy:
        class StringVar:
            def __init__(self, *a, **kw): pass
            def get(self): return ''
            def set(self, v): pass
        class IntVar(StringVar): pass
        class DoubleVar(StringVar): pass
        class BooleanVar(StringVar): pass
        class Spinbox: pass
        class Listbox: pass
        class Frame: pass
        class Label: pass
        class Button: pass
        class Entry: pass
        class LabelFrame: pass
        class Scrollbar: pass
        class Radiobutton: pass
        class Tk: pass
        class Canvas: pass
        END = 0
        LEFT = RIGHT = TOP = BOTTOM = BOTH = NONE = ''
        X = Y = ''
        W = E = N = S = ''
        SUNKEN = 'sunken'
        VERTICAL = 'vertical'
        EXTENDED = 'extended'
        WORD = 'word'
        END = 'end'
    tk = _Dummy()
    filedialog = messagebox = ttk = scrolledtext = colorchooser = simpledialog = _Dummy()

import os
import sys
import threading
import copy
import io
import re
import traceback
from datetime import datetime
from collections import OrderedDict

# ── PDF 处理库 ──────────────────────────────────────────
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from PyPDF2.generic import NameObject, ArrayObject, NumberObject
import pdfplumber
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import Color, black, white, HexColor
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table as RLTable, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ══════════════════════════════════════════════════════════
# ★ 字体注册与映射（v2.2 核心修复）
# ══════════════════════════════════════════════════════════

# 存储所有已注册字体的 {短名: 文件路径}
_REGISTERED_FONTS = {}  # name -> path
_FONT_ALIASES = {}       # 变体名/别名 -> 已注册短名

def _register_font_safe(name, path):
    """安全注册字体，成功返回 True"""
    try:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
            _REGISTERED_FONTS[name] = path
            return True
    except Exception as e:
        print(f"  [字体] 注册 '{name}' 失败: {e}")
    return False

# Linux/macOS 中文字体备选
for _name, _path in [
    ('WenQuanYi', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'),
    ('NotoSansSC', '/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf'),
    ('NotoSansSC', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),
    ('MiSans', '/usr/share/fonts/truetype/misans/MiSans-Regular.ttf'),
    ('AliPuHui', '/usr/share/fonts/truetype/alibaba-puhuiti/AlibabaPuHuiTi-2-55-Regular.ttf'),
    ('NotoSansLight', '/usr/share/fonts/truetype/noto/NotoSansSC-Light.ttf'),
]:
    _register_font_safe(_name, _path)

# Windows 自带中文字体（解决中文输出变黑方块的问题）
_WINDOWS_FONT_DIR = os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts')
for _name, _file in [
    ('MicrosoftYaHei', 'msyh.ttc'),
    ('SimSun', 'simsun.ttc'),
    ('SimHei', 'simhei.ttf'),
    ('DengXian', 'Deng.ttf'),
    ('KaiTi', 'simkai.ttf'),
    ('FangSong', 'simfang.ttf'),
    ('STSong', 'STSONG.TTF'),
    ('STKaiti', 'STKAITI.TTF'),
    ('STZhongsong', 'STZHONGS.TTF'),
]:
    _register_font_safe(_name, os.path.join(_WINDOWS_FONT_DIR, _file))

# 按优先级选择默认中文字体
CHINESE_FONT = 'Helvetica'
for _fn in [
    'MicrosoftYaHei', 'SimSun', 'SimHei', 'DengXian',
    'KaiTi', 'FangSong', 'STSong', 'STKaiti', 'STZhongsong',
    'WenQuanYi', 'NotoSansSC', 'MiSans', 'AliPuHui',
]:
    if _fn in _REGISTERED_FONTS:
        CHINESE_FONT = _fn
        break

print(f"[字体] 已注册: {list(_REGISTERED_FONTS.keys())}")
print(f"[字体] 默认中文字体: {CHINESE_FONT}")

# ── 字体名映射表（v2.2 核心） ────────────────────────
# pdfplumber 报告的字体名 → 我们注册的字体短名
# 覆盖：带前缀(AAAA+)、带后缀(-0/-Bold/-Italic)、不同大小写
_FONT_NAME_MAP = {
    # WenQuanYi 系列
    'WenQuanYiMicroHei-0':     'WenQuanYi',
    'WenQuanYiMicroHei':       'WenQuanYi',
    'WenQuanYi':               'WenQuanYi',
    'wqy-microhei':            'WenQuanYi',
    'AAAAAA+WenQuanYiMicroHei-0': 'WenQuanYi',
    'AAAAAA+WenQuanYi':        'WenQuanYi',
    # Noto Sans SC 系列
    'NotoSansSC-Regular':      'NotoSansSC',
    'NotoSansSC':              'NotoSansSC',
    'NotoSansCJKSC-Regular':   'NotoSansSC',
    'NotoSansCJK-Regular':     'NotoSansSC',
    'AAAAAA+NotoSansSC-Regular': 'NotoSansSC',
    'AAAAAA+NotoSansCJKSC-Regular': 'NotoSansSC',
    # MiSans
    'MiSans':                  'MiSans',
    'MiSans-Regular':          'MiSans',
    # Alibaba PuHuiTi
    'AlibabaPuHuiTi-2-55-Regular': 'AliPuHui',
    'AliPuHui':                'AliPuHui',
    # Windows 系统字体（微软雅黑/宋体/黑体/等线等）
    'MicrosoftYaHei':          'MicrosoftYaHei',
    'Microsoft Ya Hei':        'MicrosoftYaHei',
    'MicrosoftYaHei-Bold':     'MicrosoftYaHei',
    'Microsoft YaHei UI':      'MicrosoftYaHei',
    'MSYH':                    'MicrosoftYaHei',
    'YaHei':                   'MicrosoftYaHei',
    'SimSun':                  'SimSun',
    'NSimSun':                 'SimSun',
    'SimSun-ExtB':             'SimSun',
    '宋体':                     'SimSun',
    'SimHei':                  'SimHei',
    '黑体':                     'SimHei',
    'DengXian':                'DengXian',
    '等线':                     'DengXian',
    'KaiTi':                   'KaiTi',
    '楷体':                     'KaiTi',
    'FangSong':                'FangSong',
    '仿宋':                     'FangSong',
    'STSong':                  'STSong',
    '华文宋体':                 'STSong',
    'STKaiti':                 'STKaiti',
    '华文楷体':                 'STKaiti',
    'STZhongsong':             'STZhongsong',
    '华文中宋':                 'STZhongsong',
    # 通用英文字体映射
    'Helvetica':               'Helvetica',
    'Arial':                   'Helvetica',
    'Times-Roman':             'Times-Roman',
    'Times New Roman':         'Times-Roman',
    'Courier':                 'Courier',
    'Courier New':             'Courier',
}

def normalize_font_name(fontname):
    """
    ★ 将 pdfplumber/PDF 中的任意字体名归一化为已注册的字体名
    映射链：
      1. 直接查映射表
      2. 去掉 '+' 前缀（如 AAAA+Name → Name）
      3. 去掉 -Bold/-Italic/-0 等后缀
      4. 模糊匹配（忽略大小写、空格）
      5. 最终回退到 CHINESE_FONT
    """
    if not fontname or not isinstance(fontname, str):
        return CHINESE_FONT

    # 1. 直接匹配
    if fontname in _FONT_NAME_MAP:
        return _FONT_NAME_MAP[fontname]

    # 2. 去掉 '+' 前缀
    clean = fontname
    if '+' in clean:
        clean = clean.split('+')[-1]

    if clean in _FONT_NAME_MAP:
        return _FONT_NAME_MAP[clean]

    # 3. 去掉末尾的 -0, -Bold, -Italic 等
    import re as _re
    base = _re.sub(r'-(?:0|Bold|Italic|Regular|Medium|Light|Heavy|SemiBold|\d+)$', '', clean)
    if base in _FONT_NAME_MAP:
        return _FONT_NAME_MAP[base]

    # 4. 模糊匹配（忽略大小写）
    lower = clean.lower().replace(' ', '')
    for key, val in _FONT_NAME_MAP.items():
        if key.lower().replace(' ', '') == lower:
            return val
    # 部分匹配
    for key, val in _FONT_NAME_MAP.items():
        kl = key.lower().replace(' ', '')
        if kl in lower or lower in kl:
            # 避免太短的匹配
            if len(kl) >= 4:
                return val

    # 5. 最终回退
    return CHINESE_FONT


def is_font_available(fontname):
    """检查字体名是否已被 reportlab 注册"""
    try:
        pdfmetrics.getFont(fontname)
        return True
    except Exception:
        return False


def get_best_font_for_text(text, preferred=None):
    """
    根据文本内容选择最合适的已注册字体。
    - 如果文本包含中文 → 返回中文字体
    - 如果只有 ASCII → 可以用 Helvetica
    """
    if preferred and is_font_available(preferred):
        return preferred

    has_chinese = any(0x4E00 <= ord(c) <= 0x9FFF for c in (text or ''))
    if has_chinese:
        # 优先返回第一个可用的中文字体
        for fn in [
            CHINESE_FONT, 'MicrosoftYaHei', 'SimSun', 'SimHei', 'DengXian',
            'KaiTi', 'FangSong', 'STSong', 'STKaiti', 'STZhongsong',
            'WenQuanYi', 'NotoSansSC', 'MiSans', 'AliPuHui',
        ]:
            if is_font_available(fn):
                return fn
    return CHINESE_FONT


# ── PIL ────────────────────────────────────────────────
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ══════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════
def _safe_color(val, default=(0, 0, 0)):
    """安全地将各种颜色格式转为 (r,g,b) 0-255 元组"""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        v = int(val * 255) if val <= 1 else int(val)
        return (v, v, v)
    if isinstance(val, (list, tuple)):
        if len(val) == 1:
            v = int(val[0] * 255) if val[0] <= 1 else int(val[0])
            return (v, v, v)
        elif len(val) >= 3:
            r, g, b = val[0], val[1], val[2]
            if all(v <= 1 for v in (r, g, b)) and any(v > 0 for v in (r, g, b)):
                r, g, b = r * 255, g * 255, b * 255
            return (int(r), int(g), int(b))
    return default


def _rgb_to_reportlab(rgb_tuple):
    """(r,g,b) 0-255 → reportlab Color"""
    r, g, b = rgb_tuple
    return Color(r / 255.0, g / 255.0, b / 255.0)


def _parse_color(color_val):
    """接受 hex/tuple/Color，统一返回 reportlab Color"""
    if isinstance(color_val, Color):
        return color_val
    if isinstance(color_val, str) and color_val.startswith('#'):
        try:
            return HexColor(color_val)
        except Exception:
            return black
    if isinstance(color_val, (tuple, list)) and len(color_val) >= 3:
        return _rgb_to_reportlab(tuple(color_val[:3]))
    return black


def _clean_text(text):
    """
    ★ v2.2 清洗从 PDF 中提取的文字
    - 移除空字符 \\x00（下标字符解析失败的常见产物）
    - 移除其他控制字符（保留 \\n \\r \\t）
    - 统一替换全角空格
    """
    if not text:
        return ''
    # 移除空字符
    text = text.replace('\x00', '')
    # 移除其他控制字符（保留 \n \r \t）
    cleaned = []
    for ch in text:
        code = ord(ch)
        if code == 0x0000:
            continue
        elif code < 0x0020 and ch not in ('\n', '\r', '\t'):
            continue  # 跳过其他控制字符
        elif 0x200B <= code <= 0x200F:  # 零宽字符
            continue
        elif 0xFEFF == code:  # BOM
            continue
        else:
            cleaned.append(ch)
    return ''.join(cleaned)


def _validate_image_bytes(data):
    """验证图片字节数据是否有效，返回 (is_valid, format)"""
    if not data or len(data) < 8:
        return False, None
    if HAS_PIL:
        try:
            img = PILImage.open(io.BytesIO(data))
            img.verify()
            return True, img.format or 'UNKNOWN'
        except Exception:
            return False, None
    if data[:4] == b'\x89PNG':
        return True, 'PNG'
    if data[:2] == b'\xff\xd8':
        return True, 'JPEG'
    if data[:2] == b'BM':
        return True, 'BMP'
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return True, 'GIF'
    return False, None


def _extract_image_from_pdfplumber(img_info, page_width=None, page_height=None):
    """从 pdfplumber 的 image dict 中提取图片数据"""
    result = {'data': None, 'format': None, 'width': 0, 'height': 0, 'needs_png_conversion': False}

    raw = None
    stream_obj = None
    for key in ('stream', 'data', 'raw'):
        v = img_info.get(key)
        if v is not None:
            if hasattr(v, 'get_data') and not isinstance(v, (bytes, bytearray)):
                try:
                    raw = v.get_data()
                    stream_obj = v
                except Exception:
                    raw = None
            elif isinstance(v, (bytes, bytearray)):
                raw = bytes(v)
            if raw is not None:
                break

    if raw is None:
        try:
            obj = img_info.get('pdf_object')
            if obj is not None and hasattr(obj, 'get_data'):
                raw = obj.get_data()
                stream_obj = obj
        except Exception:
            pass

    if raw is None:
        return result

    if stream_obj is not None:
        try:
            sw = stream_obj.get('Width') or stream_obj.get('/Width')
            sh = stream_obj.get('Height') or stream_obj.get('/Height')
            if sw: result['width'] = int(sw)
            if sh: result['height'] = int(sh)
        except Exception:
            pass

    stream_filter = None
    if stream_obj is not None:
        try:
            stream_filter = stream_obj.get('/Filter')
        except Exception:
            pass

    is_valid, fmt = _validate_image_bytes(raw)

    if not is_valid and stream_filter is not None:
        filt_str = str(stream_filter)
        if 'JPX' in filt_str or 'JPEG2000' in filt_str:
            fmt = 'JPX'
        elif 'JBIG2' in filt_str:
            fmt = 'JBIG2'

    if is_valid:
        result['data'] = raw
        result['format'] = fmt or 'UNKNOWN'
        if HAS_PIL:
            try:
                im = PILImage.open(io.BytesIO(raw))
                result['width'], result['height'] = im.size
            except Exception:
                pass
        if not result['width']:
            result['width'] = int(img_info.get('width') or img_info.get('x1', 0) - img_info.get('x0', 0))
            result['height'] = int(img_info.get('height') or img_info.get('y1', 0) - img_info.get('y0', 0))
        return result

    # 原始像素数据 → 转 PNG
    w = 0; h = 0
    if stream_obj is not None:
        try: w = int(stream_obj.get('Width') or stream_obj.get('/Width') or 0)
        except: pass
        try: h = int(stream_obj.get('Height') or stream_obj.get('/Height') or 0)
        except: pass
    if not w: w = int(img_info.get('width') or 0)
    if not h: h = int(img_info.get('height') or 0)

    bpc = 8
    for k in ('BitsPerComponent', '/BitsPerComponent'):
        try:
            v = stream_obj.get(k) if stream_obj else None
            if v: bpc = int(v); break
        except: pass

    cs = img_info.get('colorspace') or img_info.get('ColorSpace') or ['/DeviceRGB']
    cs_str = str(cs)
    if 'CMYK' in cs_str: channels = 4
    elif 'Gray' in cs_str or 'DeviceG' in cs_str: channels = 1
    else: channels = 3

    expected = w * h * max(bpc // 8, 1) * channels
    if expected == 0:
        dw = int(img_info.get('width') or 0)
        dh = int(img_info.get('height') or 0)
        if dw and dh:
            expected = dw * dh * 3
            channels = 3
            w, h = dw, dh

    tolerance = max(channels, 16)
    if w > 0 and h > 0 and abs(len(raw) - expected) <= tolerance:
        if HAS_PIL:
            try:
                mode = {1: 'L', 3: 'RGB', 4: 'CMYK'}[channels]
                im = PILImage.frombytes(mode, (w, h), raw)
                if mode == 'CMYK':
                    im = im.convert('RGB')
                buf = io.BytesIO()
                im.save(buf, format='PNG')
                result['data'] = buf.getvalue()
                result['format'] = 'PNG'
                result['width'] = w
                result['height'] = h
                return result
            except Exception:
                pass
        result['data'] = raw
        result['format'] = 'RAW'
        result['width'] = w
        result['height'] = h
        return result

    return result
"""
PDF Editor Pro v2.2 - Part 2: 数据结构 + 解析器 + 生成器
"""

# ═══════════════════════════════════════════════════════════
# 数据结构：页面内容模型
# ═══════════════════════════════════════════════════════════
class TextBlock:
    """一段文字（v2.2 增强：字体自动归一化）"""
    def __init__(self, text='', x=0, y=0, fontsize=11, fontname=None,
                 color=black, bold=False, italic=False, alignment='left', width=None):
        self.text = _clean_text(text)
        self.x = x
        self.y = y
        self.fontsize = fontsize
        # ★ 字体名自动归一化
        self.fontname = normalize_font_name(fontname or CHINESE_FONT)
        self.color = color if isinstance(color, Color) else _parse_color(color)
        self.bold = bold
        self.italic = italic
        self.alignment = alignment
        self.width = width
        # 诊断信息
        self._original_fontname = fontname  # 保留原始名用于调试

    def to_paragraph(self):
        style_map = {'left': TA_LEFT, 'center': TA_CENTER, 'right': TA_RIGHT}
        # 确保字体可用
        fn = self.fontname if is_font_available(self.fontname) else CHINESE_FONT
        s = ParagraphStyle(
            'txt', fontName=fn, fontSize=self.fontsize,
            textColor=self.color, alignment=style_map.get(self.alignment, TA_LEFT),
            leading=self.fontsize * 1.3
        )
        safe = self.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return Paragraph(safe, s)


class ImageBlock:
    """一张图片"""
    def __init__(self, image_data=None, path=None, x=0, y=0, width=None, height=None):
        self.image_data = image_data
        self.path = path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._validated = False
        self._format = None

    def get_bytes(self):
        if self.image_data:
            return self.image_data
        if self.path and os.path.exists(self.path):
            try:
                with open(self.path, 'rb') as f:
                    self.image_data = f.read()
                return self.image_data
            except Exception:
                return None
        return None

    def is_valid(self):
        data = self.get_bytes()
        if not data:
            return False
        if getattr(self, '_format', None) in ('RAW', 'PNG', 'JPEG', 'BMP', 'GIF'):
            return True
        ok, fmt = _validate_image_bytes(data)
        self._validated = ok
        if fmt: self._format = fmt
        return ok

    def get_dimensions(self):
        data = self.get_bytes()
        if not data:
            return None, None
        if HAS_PIL:
            try:
                img = PILImage.open(io.BytesIO(data))
                return img.size
            except Exception:
                pass
        try:
            from reportlab.lib.utils import ImageReader
            ir = ImageReader(io.BytesIO(data))
            return ir.getSize()
        except Exception:
            return None, None


class TableBlock:
    """一个表格"""
    def __init__(self, x=0, y=0, col_widths=None, row_heights=None):
        self.x = x
        self.y = y
        self.headers = []
        self.rows = []
        self.col_widths = col_widths or []
        self.row_heights = row_heights or []
        self.fontsize = 10
        self.header_bg = HexColor('#4472C4')
        self.header_text_color = white
        self.grid_color = HexColor('#BFBFBF')
        self.cell_padding = 4

    def set_data(self, headers, rows):
        self.headers = list(headers)
        self.rows = [list(r) for r in rows]
        if not self.col_widths:
            self.col_widths = [80] * len(self.headers)

    def add_row(self, row=None):
        row = row or [''] * len(self.headers)
        self.rows.append(list(row))

    def insert_row(self, index, row=None):
        row = row or [''] * len(self.headers)
        self.rows.insert(index, list(row))

    def delete_row(self, index):
        if 0 <= index < len(self.rows):
            self.rows.pop(index)

    def add_column(self, header='', default='', index=None):
        if index is None:
            index = len(self.headers)
        self.headers.insert(index, header)
        for r in self.rows:
            r.insert(index, default)
        self.col_widths.insert(index, 80)

    def delete_column(self, index):
        if 0 <= index < len(self.headers):
            self.headers.pop(index)
            for r in self.rows:
                if index < len(r):
                    r.pop(index)
            if index < len(self.col_widths):
                self.col_widths.pop(index)

    def set_cell(self, row, col, value):
        if 0 <= row < len(self.rows) and 0 <= col < len(self.headers):
            self.rows[row][col] = str(value)

    def get_cell(self, row, col):
        if 0 <= row < len(self.rows) and 0 <= col < len(self.headers):
            return self.rows[row][col]
        return ''

    def to_reportlab_table(self):
        fn = CHINESE_FONT if is_font_available(CHINESE_FONT) else 'Helvetica'
        headers_styled = [
            Paragraph(str(h).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'),
                      ParagraphStyle('h', fontName=fn, fontSize=self.fontsize,
                                     textColor=self.header_text_color, alignment=TA_CENTER,
                                     leading=self.fontsize*1.2))
            for h in self.headers
        ]
        data = [headers_styled]
        for row in self.rows:
            r = [
                Paragraph(str(c).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'),
                          ParagraphStyle('c', fontName=fn, fontSize=self.fontsize-1,
                                         leading=(self.fontsize-1)*1.2))
                for c in row
            ]
            data.append(r)

        t = RLTable(data, colWidths=self.col_widths, repeatRows=1)
        cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), self.header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.header_text_color),
            ('GRID', (0, 0), (-1, -1), 0.5, self.grid_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), self.cell_padding),
            ('BOTTOTPADDING', (0, 0), (-1, -1), self.cell_padding),
            ('LEFTPADDING', (0, 0), (-1, -1), self.cell_padding),
            ('RIGTHPADDING', (0, 0), (-1, -1), self.cell_padding),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F2F2F2')]),
        ]
        t.setStyle(TableStyle(cmds))
        return t


class PageModel:
    """单页内容模型"""
    def __init__(self, width=A4[0], height=A4[1]):
        self.width = width
        self.height = height
        self.texts = []
        self.images = []
        self.tables = []
        self.background_color = None


# ═══════════════════════════════════════════════════════════
# PDF 内容解析器（v2.2 增强：字体归一化 + 文字清洗）
# ═══════════════════════════════════════════════════════════
class PDFContentParser:
    """从 PDF 中提取文字/图片/表格到 PageModel"""

    @staticmethod
    def parse(pdf_path):
        """解析整个 PDF，返回 list[PageModel]"""
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                pm = PageModel(width=p.width, height=p.height)

                # ── 文字 ──
                try:
                    chars = p.chars or []
                    # 按字体分组，再合并为文字块
                    char_list = []
                    for ch in chars:
                        try:
                            raw_text = ch.get('text', '')
                            # ★ 清洗空字符
                            if '\x00' in raw_text:
                                raw_text = raw_text.replace('\x00', '')
                            if not raw_text or raw_text == '\x00':
                                continue

                            raw_color = ch.get('non_stroking_color', (0, 0, 0))
                            color_rgb = _safe_color(raw_color)
                            raw_font = ch.get('fontname', '') or CHINESE_FONT

                            char_list.append({
                                'text': raw_text,
                                'x0': ch.get('x0', 0),
                                'top': ch.get('top', 0),
                                'x1': ch.get('x1', 0),
                                'bottom': ch.get('bottom', 0),
                                'size': ch.get('size', 11) or 11,
                                'fontname': raw_font,
                                'color': _rgb_to_reportlab(color_rgb),
                            })
                        except Exception:
                            continue

                    # 合并为行
                    pm.texts = PDFContentParser._merge_chars_to_lines_v2(char_list, p.height)
                except Exception as e:
                    print(f"[WARN] 文字解析失败: {e}")

                # ── 图片 ──
                try:
                    imgs = p.images or []
                    for img_info in imgs:
                        try:
                            extracted = _extract_image_from_pdfplumber(img_info)
                            x0 = float(img_info.get('x0', 0) or 0)
                            top = float(img_info.get('top', 0) or 0)
                            x1 = float(img_info.get('x1', x0 + 1) or (x0 + 1))
                            bottom = float(img_info.get('bottom', top + 1) or (top + 1))

                            if extracted['data']:
                                ib = ImageBlock(
                                    image_data=extracted['data'],
                                    x=x0, y=p.height - top,
                                    width=extracted['width'] or max(x1 - x0, 1),
                                    height=extracted['height'] or max(bottom - top, 1)
                                )
                                ib._format = extracted['format']
                                ib._validated = True
                                pm.images.append(ib)
                            else:
                                ib = ImageBlock(
                                    x=x0, y=p.height - top,
                                    width=max(x1 - x0, 1), height=max(bottom - top, 1)
                                )
                                ib.image_data = None
                                ib._format = None
                                ib._validated = False
                                pm.images.append(ib)
                        except Exception as e:
                            print(f"[WARN] 跳过一张图片: {e}")
                            continue
                except Exception as e:
                    print(f"[WARN] 图片解析失败: {e}")

                # ── 表格 ──
                try:
                    tables = p.extract_tables() or []
                    table_props = []
                    try:
                        table_props = p.find_tables() or []
                    except Exception:
                        pass

                    for ti, tbl in enumerate(tables):
                        if not tbl:
                            continue
                        tb_obj = TableBlock(x=0, y=0)
                        if ti < len(table_props):
                            tp = table_props[ti]
                            try:
                                bbox = tp.bbox if hasattr(tp, 'bbox') else tp._bbox if hasattr(tp, '_bbox') else None
                                if bbox and len(bbox) >= 4:
                                    tb_obj.x = bbox[0]
                                    tb_obj.y = p.height - bbox[1]
                            except Exception:
                                pass

                        headers = tbl[0] if tbl else []
                        rows = tbl[1:] if len(tbl) > 1 else []
                        max_len = max((len(r) for r in rows), default=0)
                        max_len = max(max_len, len(headers))
                        headers = (headers + [''] * max_len)[:max_len]
                        rows = [(r + [''] * (max_len - len(r)))[:max_len] for r in rows]
                        # 清洗表格内容
                        headers = [_clean_text(h) for h in headers]
                        rows = [[_clean_text(c) for c in r] for r in rows]
                        tb_obj.set_data(headers, rows)

                        avail = (p.width - tb_obj.x * 2) or 400
                        if headers and not tb_obj.col_widths:
                            tb_obj.col_widths = [max(40, avail / len(headers))] * len(headers)
                        pm.tables.append(tb_obj)
                except Exception as e:
                    print(f"[WARN] 表格解析失败: {e}")

                pages.append(pm)
        return pages

    @staticmethod
    def _merge_chars_to_lines_v2(chars, page_height, tol=3.0):
        """
        ★ v2.2 增强版：按字体+字号+颜色+y坐标 分组后合并为行
        同一行的字符必须字体、字号、颜色一致（或更宽松：仅按y聚类）
        """
        if not chars:
            return []

        # 按 y 聚类
        y_groups = OrderedDict()
        for ch in chars:
            y_key = round((page_height - ch['top']) / tol) * tol
            y_groups.setdefault(y_key, []).append(ch)

        merged = []
        for y_key, group in y_groups.items():
            # 按 x 排序
            group.sort(key=lambda c: c['x0'])
            # 按字体+字号+颜色 进一步分组（处理同一行不同格式的情况）
            sub_groups = []
            current = []
            for ch in group:
                if not current:
                    current.append(ch)
                else:
                    prev = current[-1]
                    same_font = (ch['fontname'] == prev['fontname'])
                    same_size = abs(ch['size'] - prev['size']) < 0.5
                    same_color = (ch['color'] == prev['color'])
                    # 间距不超过 3 倍字号视为同一段
                    gap = ch['x0'] - prev['x1']
                    max_gap = prev['size'] * 3
                    if same_font and same_size and same_color and gap < max_gap:
                        current.append(ch)
                    else:
                        sub_groups.append(current)
                        current = [ch]
            if current:
                sub_groups.append(current)

            for sg in sub_groups:
                text = ''.join(c['text'] for c in sg)
                text = _clean_text(text)  # ★ 再次清洗
                if not text:
                    continue
                first = sg[0]
                merged.append(TextBlock(
                    text=text,
                    x=first['x0'],
                    y=y_key,
                    fontsize=first['size'],
                    fontname=normalize_font_name(first['fontname']),  # ★ 归一化
                    color=first['color'],
                ))

        return merged
"""
PDF Editor Pro v2.2 - Part 3: 生成器 + 编辑操作 + 原版 PDFEditor
"""

# ══════════════════════════════════════════════════════════
# PDF 重新生成器（v2.2 核心修复：字体保障）
# ══════════════════════════════════════════════════════════
class PDFRegenerator:
    """把 PageModel 列表重新绘制成 PDF"""

    @staticmethod
    def _ensure_font(fontname, text=''):
        """
        ★ v2.2 核心方法：确保字体可用
        映射链：原始名 → 归一化 → 按内容选字体 → 回退 CHINESE_FONT → 最终 Helvetica
        """
        # 1. 先归一化
        fn = normalize_font_name(fontname)

        # 2. 检查是否可用
        if is_font_available(fn):
            return fn

        # 3. 根据文本内容选择
        fn = get_best_font_for_text(text, preferred=fn)
        if is_font_available(fn):
            return fn

        # 4. 遍历所有已注册字体尝试
        for registered_name in _REGISTERED_FONTS:
            if is_font_available(registered_name):
                return registered_name

        # 5. 最终兜底
        return 'Helvetica'

    @staticmethod
    def generate(pages, output_path, page_size=A4):
        """直接画到 canvas（精确定位）"""
        c = rl_canvas.Canvas(output_path, pagesize=page_size)
        pw, ph = page_size

        for pi, pm in enumerate(pages):
            page_w = pm.width or pw
            page_h = pm.height or ph
            c.setPageSize((page_w, page_h))

            # 背景
            if pm.background_color:
                c.setFillColor(pm.background_color)
                c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
                c.setFillColor(black)

            # ── 文字 ──
            for tb in pm.texts:
                try:
                    text = _clean_text(tb.text)  # ★ 再次清洗
                    if not text:
                        continue

                    # ★ 字体三重保障
                    fontname = PDFRegenerator._ensure_font(tb.fontname, text)
                    c.setFont(fontname, tb.fontsize or 11)

                    # 颜色
                    try:
                        c.setFillColor(tb.color or black)
                    except Exception:
                        c.setFillColor(black)

                    # 绘制
                    x = tb.x or 0
                    y = tb.y or 0
                    c.drawString(x, y, text)
                except Exception as e:
                    print(f"[WARN] 文字绘制失败 p{pi}: {e}")

            # ── 图片 ──
            for ib in pm.images:
                PDFRegenerator._draw_image(c, ib, page_h, pi)

            # ── 表格 ──
            try:
                PDFRegenerator._draw_tables_on_canvas(c, pm)
            except Exception as e:
                print(f"[WARN] 表格绘制失败 p{pi}: {e}")

            c.showPage()
        c.save()

    @staticmethod
    def _draw_image(c, ib, page_h, page_idx):
        """安全绘制单张图片"""
        data = ib.get_bytes()
        if not data:
            PDFRegenerator._draw_image_placeholder(c, ib, page_h, "无图片数据")
            return

        try:
            from reportlab.lib.utils import ImageReader

            if HAS_PIL:
                try:
                    pil_img = PILImage.open(io.BytesIO(data))
                    pil_img.load()
                    if pil_img.mode not in ('RGB', 'L'):
                        pil_img = pil_img.convert('RGB')
                    png_buf = io.BytesIO()
                    pil_img.save(png_buf, format='PNG')
                    png_buf.seek(0)
                    ir = ImageReader(png_buf)
                    iw, ih = ir.getSize()
                except Exception:
                    w = int(ib.width or 0)
                    h = int(ib.height or 0)
                    if w > 0 and h > 0 and len(data) >= w * h * 3:
                        try:
                            pil_img = PILImage.frombytes('RGB', (w, h), data[:w*h*3])
                            png_buf = io.BytesIO()
                            pil_img.save(png_buf, format='PNG')
                            png_buf.seek(0)
                            ir = ImageReader(png_buf)
                            iw, ih = ir.getSize()
                        except Exception:
                            PDFRegenerator._draw_image_placeholder(c, ib, page_h, "无法解码")
                            return
                    else:
                        PDFRegenerator._draw_image_placeholder(c, ib, page_h, "数据无效")
                        return
            else:
                try:
                    ir = ImageReader(io.BytesIO(data))
                    iw, ih = ir.getSize()
                except Exception:
                    PDFRegenerator._draw_image_placeholder(c, ib, page_h, "无法解码(无PIL)")
                    return

            draw_w = ib.width or iw
            draw_h = ib.height or ih
            if ib.width and not ib.height:
                draw_h = ih * (draw_w / iw) if iw > 0 else draw_h
            elif ib.height and not ib.width:
                draw_w = iw * (draw_h / ih) if ih > 0 else draw_w
            elif not ib.width and not ib.height:
                draw_w, draw_h = iw, ih

            draw_y = (page_h - ib.y) - draw_h
            c.drawImage(ir, ib.x or 0, draw_y, width=draw_w, height=draw_h, preserveAspectRatio=True)
        except Exception as e:
            print(f"[WARN] 图片绘制失败 p{page_idx}: {e}")
            PDFRegenerator._draw_image_placeholder(c, ib, page_h, "绘制错误")

    @staticmethod
    def _draw_image_placeholder(c, ib, page_h, reason):
        try:
            w = ib.width or 50
            h = ib.height or 50
            x = ib.x or 0
            y = (page_h - ib.y) - h
            c.saveState()
            c.setStrokeColor(HexColor('#FF0000'))
            c.setLineWidth(1)
            c.setDash(3, 3)
            c.rect(x, y, w, h, fill=0, stroke=1)
            c.setDash()
            c.setFont('Helvetica', 8)
            c.setFillColor(HexColor('#FF0000'))
            c.drawString(x + 3, y + h/2, f"[图片占位: {reason}]")
            c.setFillColor(black)
            c.restoreState()
        except Exception:
            pass

    @staticmethod
    def _draw_tables_on_canvas(c, pm):
        """在 canvas 上直接绘制表格"""
        fn = CHINESE_FONT if is_font_available(CHINESE_FONT) else 'Helvetica'
        for tb in pm.tables:
            x0 = tb.x or 0
            y0 = pm.height - (tb.y or 0)
            row_h = 20
            cell_pad = 3

            c.setFillColor(tb.header_bg)
            total_w = sum(tb.col_widths) if tb.col_widths else 100
            c.rect(x0, y0 - row_h, total_w, row_h, fill=1, stroke=0)
            c.setFillColor(black)

            c.setFont(fn, tb.fontsize or 10)
            c.setFillColor(tb.header_text_color)
            cx = x0
            for i, h in enumerate(tb.headers):
                txt = str(h)[:20] if h else ''
                c.drawString(cx + cell_pad, y0 - row_h + cell_pad, txt)
                cx += tb.col_widths[i] if i < len(tb.col_widths) else 80
            c.setFillColor(black)

            cy = y0 - row_h
            alt = False
            for row in tb.rows:
                if alt:
                    c.setFillColor(HexColor('#F2F2F2'))
                    c.rect(x0, cy - row_h, total_w, row_h, fill=1, stroke=0)
                    c.setFillColor(black)
                alt = not alt
                cx = x0
                c.setFont(fn, max(7, (tb.fontsize or 10) - 1))
                for i, cell in enumerate(row):
                    txt = str(cell)[:30] if cell else ''
                    c.drawString(cx + cell_pad, cy - row_h + cell_pad, txt)
                    cx += tb.col_widths[i] if i < len(tb.col_widths) else 80
                c.setStrokeColor(tb.grid_color)
                c.setLineWidth(0.5)
                c.line(x0, cy, x0 + total_w, cy)
                cy -= row_h

            c.setStrokeColor(tb.grid_color)
            c.rect(x0, cy, total_w, y0 - cy)
            cx = x0
            for w in (tb.col_widths or [])[:-1]:
                cx += w
                c.line(cx, y0, cx, cy)


# ══════════════════════════════════════════════════════════
# 高级编辑操作
# ══════════════════════════════════════════════════════════
class PDFEditorAdvanced:
    """对 PageModel 列表执行高级编辑"""

    # ── 文字 ──────────────────────────────────────────
    @staticmethod
    def edit_text(pages, page_idx, text_idx, new_text=None, **kwargs):
        tb = pages[page_idx].texts[text_idx]
        if new_text is not None:
            tb.text = _clean_text(new_text)  # ★ 清洗
        for k in ('fontsize', 'bold', 'italic', 'alignment', 'x', 'y', 'width'):
            if k in kwargs:
                setattr(tb, k, kwargs[k])
        if 'fontname' in kwargs:
            # ★ 归一化字体名
            tb.fontname = normalize_font_name(kwargs['fontname'])
        if 'color' in kwargs:
            tb.color = _parse_color(kwargs['color'])

    @staticmethod
    def add_text(pages, page_idx, text, x=50, y=50, fontsize=12, color=black, fontname=None, **kw):
        tb = TextBlock(
            text=_clean_text(text),  # ★ 清洗
            x=x, y=y, fontsize=fontsize,
            color=color,
            fontname=normalize_font_name(fontname or CHINESE_FONT)  # ★ 归一化
        )
        pages[page_idx].texts.append(tb)

    @staticmethod
    def delete_text(pages, page_idx, text_idx):
        pages[page_idx].texts.pop(text_idx)

    @staticmethod
    def find_text(pages, keyword, case_sensitive=False):
        results = []
        for pi, pm in enumerate(pages):
            for ti, tb in enumerate(pm.texts):
                hay = tb.text if case_sensitive else tb.text.lower()
                needle = keyword if case_sensitive else keyword.lower()
                if needle in hay:
                    results.append((pi, ti, tb.text))
        return results

    @staticmethod
    def replace_all_text(pages, old, new, case_sensitive=False):
        count = 0
        new_clean = _clean_text(new)
        for pi, pm in enumerate(pages):
            for tb in pm.texts:
                hay = tb.text if case_sensitive else tb.text.lower()
                needle = old if case_sensitive else old.lower()
                if needle in hay:
                    if case_sensitive:
                        tb.text = tb.text.replace(old, new_clean)
                    else:
                        tb.text = re.sub(re.escape(old), new_clean, tb.text, flags=re.IGNORECASE)
                    count += 1
        return count

    # ── 图片 ──────────────────────────────────────────
    @staticmethod
    def add_image(pages, page_idx, img_path, x=50, y=50, width=None, height=None):
        ib = ImageBlock(path=img_path, x=x, y=y, width=width, height=height)
        data = ib.get_bytes()
        if data and _validate_image_bytes(data)[0]:
            ib.image_data = data
        pages[page_idx].images.append(ib)
        return len(pages[page_idx].images) - 1

    @staticmethod
    def delete_image(pages, page_idx, img_idx):
        pages[page_idx].images.pop(img_idx)

    @staticmethod
    def edit_image(pages, page_idx, img_idx, new_path=None, width=None, height=None, x=None, y=None):
        ib = pages[page_idx].images[img_idx]
        if new_path:
            ib.path = new_path
            ib.image_data = None
            data = ib.get_bytes()
            if data:
                ib.image_data = data
        if width is not None: ib.width = width
        if height is not None: ib.height = height
        if x is not None: ib.x = x
        if y is not None: ib.y = y

    @staticmethod
    def scale_image(pages, page_idx, img_idx, scale=1.0):
        ib = pages[page_idx].images[img_idx]
        if ib.width: ib.width = ib.width * scale
        if ib.height: ib.height = ib.height * scale

    @staticmethod
    def get_image_info(pages, page_idx, img_idx):
        ib = pages[page_idx].images[img_idx]
        data = ib.get_bytes()
        fmt = getattr(ib, '_format', None)
        if not fmt and data:
            ok, fmt = _validate_image_bytes(data)
            if not ok: fmt = 'RAW'
        info = {
            'x': ib.x, 'y': ib.y,
            'width': ib.width, 'height': ib.height,
            'has_data': data is not None,
            'is_valid': (data is not None),
            'format': fmt,
        }
        orig_w, orig_h = ib.get_dimensions()
        info['original_width'] = orig_w
        info['original_height'] = orig_h
        return info

    # ── 表格 ──────────────────────────────────────────
    @staticmethod
    def add_table(pages, page_idx, headers, rows, x=50, y=50, col_widths=None):
        tb = TableBlock(x=x, y=y)
        tb.set_data(headers, rows)
        if col_widths:
            tb.col_widths = list(col_widths)
        pages[page_idx].tables.append(tb)
        return len(pages[page_idx].tables) - 1

    @staticmethod
    def delete_table(pages, page_idx, table_idx):
        pages[page_idx].tables.pop(table_idx)

    @staticmethod
    def edit_table_cell(pages, page_idx, table_idx, row, col, value):
        pages[page_idx].tables[table_idx].set_cell(row, col, _clean_text(str(value)))

    @staticmethod
    def add_table_row(pages, page_idx, table_idx, row_data=None, position=None):
        tb = pages[page_idx].tables[table_idx]
        if position is None:
            tb.add_row(row_data)
        else:
            tb.insert_row(position, row_data)

    @staticmethod
    def delete_table_row(pages, page_idx, table_idx, row_idx):
        pages[page_idx].tables[table_idx].delete_row(row_idx)

    @staticmethod
    def add_table_column(pages, page_idx, table_idx, header='', default='', position=None):
        pages[page_idx].tables[table_idx].add_column(header, default, position)

    @staticmethod
    def delete_table_column(pages, page_idx, table_idx, col_idx):
        pages[page_idx].tables[table_idx].delete_column(col_idx)

    @staticmethod
    def set_table_col_widths(pages, page_idx, table_idx, widths):
        pages[page_idx].tables[table_idx].col_widths = list(widths)


# ══════════════════════════════════════════════════════════
# 原版 PDFEditor（保留所有功能）
# ══════════════════════════════════════════════════════════
class PDFEditor:
    """PDF 编辑核心功能类"""

    @staticmethod
    def merge_pdfs(input_paths, output_path):
        merger = PdfMerger()
        for path in input_paths:
            merger.append(path)
        with open(output_path, 'wb') as f:
            merger.write(f)
        merger.close()
        return True, f"成功合并 {len(input_paths)} 个文件 → {output_path}"

    @staticmethod
    def split_pdf(input_path, output_dir, mode='all', page_ranges=None):
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        results = []
        if mode == 'all':
            for i in range(total_pages):
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                out_path = os.path.join(output_dir, f"page_{i+1}.pdf")
                with open(out_path, 'wb') as f:
                    writer.write(f)
                results.append(out_path)
            return True, f"成功拆分 {total_pages} 页到 {output_dir}"
        elif mode == 'range' and page_ranges:
            for idx, (start, end) in enumerate(page_ranges):
                start = max(0, start - 1)
                end = min(total_pages, end)
                writer = PdfWriter()
                for i in range(start, end):
                    writer.add_page(reader.pages[i])
                out_path = os.path.join(output_dir, f"pages_{start+1}-{end}.pdf")
                with open(out_path, 'wb') as f:
                    writer.write(f)
                results.append(out_path)
            return True, f"成功按范围拆分 → {len(results)} 个文件"

    @staticmethod
    def extract_pages(input_path, output_path, pages):
        reader = PdfReader(input_path)
        total = len(reader.pages)
        writer = PdfWriter()
        for p in pages:
            if 1 <= p <= total:
                writer.add_page(reader.pages[p - 1])
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True, f"成功提取 {len(pages)} 页 → {output_path}"

    @staticmethod
    def delete_pages(input_path, output_path, pages_to_delete):
        reader = PdfReader(input_path)
        total = len(reader.pages)
        writer = PdfWriter()
        for i in range(total):
            if (i + 1) not in pages_to_delete:
                writer.add_page(reader.pages[i])
        with open(output_path, 'wb') as f:
            writer.write(f)
        remaining = total - len(pages_to_delete)
        return True, f"已删除 {len(pages_to_delete)} 页，剩余 {remaining} 页 → {output_path}"

    @staticmethod
    def rotate_pages(input_path, output_path, rotation, pages=None):
        reader = PdfReader(input_path)
        writer = PdfWriter()
        total = len(reader.pages)
        for i in range(total):
            page = reader.pages[i]
            if pages is None or (i + 1) in pages:
                page.rotate(rotation)
            writer.add_page(page)
        with open(output_path, 'wb') as f:
            writer.write(f)
        target = f"第 {pages} 页" if pages else "所有页面"
        return True, f"已旋转 {target} {rotation}° → {output_path}"

    @staticmethod
    def add_watermark(input_path, output_path, text, opacity=0.3, fontsize=50, color=(128,128,128)):
        reader = PdfReader(input_path)
        writer = PdfWriter()
        fn = CHINESE_FONT if is_font_available(CHINESE_FONT) else 'Helvetica'
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            packet = io.BytesIO()
            c = rl_canvas.Canvas(packet, pagesize=(page_width, page_height))
            c.setFont(fn, fontsize)
            c.setFillColorRGB(color[0]/255, color[1]/255, color[2]/255, alpha=opacity)
            c.saveState()
            c.translate(page_width/2, page_height/2)
            c.rotate(45)
            for x in range(-int(page_width), int(page_width), fontsize * 3):
                c.drawString(x, 0, text)
                c.drawString(x, fontsize * 2, text)
            c.restoreState()
            c.save()
            packet.seek(0)
            watermark_reader = PdfReader(packet)
            watermark_page = watermark_reader.pages[0]
            page.merge_page(watermark_page)
            writer.add_page(page)
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True, f"已添加水印「{text}」→ {output_path}"

    @staticmethod
    def encrypt_pdf(input_path, output_path, password, owner_password=None):
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        if owner_password is None:
            owner_password = password
        writer.encrypt(user_password=password, owner_password=owner_password)
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True, f"已加密 PDF → {output_path}"

    @staticmethod
    def decrypt_pdf(input_path, output_path, password):
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            result = reader.decrypt(password)
            if not result:
                return False, "密码错误，无法解密"
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True, f"已解密 PDF → {output_path}"

    @staticmethod
    def extract_text(input_path, output_path=None):
        reader = PdfReader(input_path)
        text_parts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ''
            text_parts.append(f"=== 第 {i+1} 页 ===\n{text}\n")
        full_text = "\n".join(text_parts)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            return True, f"文本已保存到 → {output_path}"
        return True, full_text

    @staticmethod
    def compress_pdf(input_path, output_path, quality=0.5):
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        try:
            writer.compress_content_streams()
        except AttributeError:
            pass
        try:
            writer._compress_streams = True
        except Exception:
            pass
        with open(output_path, 'wb') as f:
            writer.write(f)
        import zlib
        original_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        if new_size >= original_size:
            writer2 = PdfWriter()
            for page in reader.pages:
                writer2.add_page(page)
            for page in writer2.pages:
                if '/Contents' in page:
                    contents = page['/Contents']
                    if hasattr(contents, 'get_object'):
                        try:
                            obj = contents.get_object()
                            if hasattr(obj, 'get_data'):
                                raw = obj.get_data()
                                compressed = zlib.compress(raw, 9)
                                obj._data = compressed
                                obj['/Filter'] = NameObject('/FlateDecode')
                        except Exception:
                            pass
            with open(output_path, 'wb') as f:
                writer2.write(f)
            new_size = os.path.getsize(output_path)
        ratio = (1 - new_size / original_size) * 100 if original_size > 0 else 0
        return True, f"压缩完成: {original_size/1024:.1f}KB → {new_size/1024:.1f}KB (减少 {ratio:.1f}%)"
"""
PDF Editor Pro v2.2 - Part 4: GUI 界面
"""

class PDFEditorGUI:
    """PDF 编辑器图形界面（增强版 v2.2 - 字体修复）"""

    def __init__(self, root):
        if not _HAS_TK:
            raise RuntimeError("tkinter 不可用，无法启动 GUI")
        self.root = root
        self.root.title("PDF 编辑工具 Pro v2.2 (字体修复版)")
        self.root.geometry("900x720")
        self.root.minsize(850, 650)

        self.current_file = None
        self.file_list = []
        self._page_models = None
        self._current_page_idx = 0

        # 字体诊断信息
        self._font_info = f"可用字体: {list(_REGISTERED_FONTS.keys())}"

        self._setup_ui()

    # ─────────────────────────────────────────────────────
    def _setup_ui(self):
        header = tk.Frame(self.root, bg='#1a73e8', height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="📄 PDF 编辑工具 Pro v2.2", font=('Arial', 16, 'bold'),
                 fg='white', bg='#1a73e8').pack(pady=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('Arial', 10))

        # 原版选项卡
        self._create_merge_tab()
        self._create_split_tab()
        self._create_extract_tab()
        self._create_delete_tab()
        self._create_rotate_tab()
        self._create_watermark_tab()
        self._create_security_tab()
        self._create_text_tab()
        self._create_compress_tab()

        # 新增：内容编辑选项卡
        self._create_content_editor_tab()

        self.status_var = tk.StringVar(value=f"就绪 | {self._font_info}")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W, fg='#555')
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # ═════════════════════════════════════════════════
    # 通用辅助
    # ═════════════════════════════════════════════════
    def _select_file(self, entry_var, filetypes=None):
        if filetypes is None:
            filetypes = [("PDF 文件", "*.pdf"), ("所有文件", "*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            entry_var.set(path)
            self.current_file = path
            self.status_var.set(f"已选择: {os.path.basename(path)}")

    def _select_output(self, entry_var, default_ext='.pdf'):
        path = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=[("PDF 文件", "*.pdf")] if default_ext == '.pdf' else [("文本文件", "*.txt")]
        )
        if path:
            entry_var.set(path)

    def _select_output_dir(self, entry_var):
        path = filedialog.askdirectory()
        if path:
            entry_var.set(path)

    def _run_task(self, func, *args, success_msg="操作完成"):
        def worker():
            try:
                self.status_var.set("处理中...")
                self.root.update()
                result = func(*args)
                if isinstance(result, tuple):
                    success, msg = result
                else:
                    success, msg = True, str(result)
                if success:
                    self.status_var.set(f"✅ {msg}")
                    messagebox.showinfo("成功", msg)
                else:
                    self.status_var.set(f"❌ {msg}")
                    messagebox.showerror("错误", msg)
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                self.status_var.set(f"❌ 错误: {err_msg}")
                messagebox.showerror("错误", f"操作失败:\n{err_msg}\n\n详细:\n{traceback.format_exc()[:500]}")
        threading.Thread(target=worker, daemon=True).start()

    # ═════════════════════════════════════════════════
    # 1. 合并
    # ═════════════════════════════════════════════════
    def _create_merge_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📎 合并")
        tk.Label(tab, text="选择要合并的 PDF 文件（可多选）:", font=('Arial', 10)).pack(pady=10)
        list_frame = tk.Frame(tab); list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        self.merge_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=10)
        self.merge_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.merge_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.merge_listbox.config(yscrollcommand=sb.set)
        btn = tk.Frame(tab); btn.pack(fill=tk.X, padx=20, pady=5)
        tk.Button(btn, text="添加文件", command=self._merge_add_files).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="移除选中", command=self._merge_remove).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="上移", command=self._merge_move_up).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="下移", command=self._merge_move_down).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="清空", command=self._merge_clear).pack(side=tk.LEFT, padx=5)
        out = tk.Frame(tab); out.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(out, text="输出文件:").pack(side=tk.LEFT)
        self.merge_output = tk.StringVar()
        tk.Entry(out, textvariable=self.merge_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(out, text="浏览", command=lambda: self._select_output(self.merge_output)).pack(side=tk.LEFT)
        tk.Button(tab, text="▶ 开始合并", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_merge).pack(pady=15)

    def _merge_add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF 文件", "*.pdf")])
        for p in paths:
            self.file_list.append(p)
            self.merge_listbox.insert(tk.END, os.path.basename(p))

    def _merge_remove(self):
        for i in reversed(self.merge_listbox.curselection()):
            self.merge_listbox.delete(i); self.file_list.pop(i)

    def _merge_move_up(self):
        sel = self.merge_listbox.curselection()
        if not sel or sel[0] == 0: return
        for i in sel:
            if i > 0:
                self.file_list[i-1], self.file_list[i] = self.file_list[i], self.file_list[i-1]
                self.merge_listbox.delete(i)
                self.merge_listbox.insert(i-1, os.path.basename(self.file_list[i-1]))
                self.merge_listbox.selection_set(i-1)

    def _merge_move_down(self):
        sel = self.merge_listbox.curselection()
        if not sel or sel[-1] == len(self.file_list)-1: return
        for i in reversed(sel):
            if i < len(self.file_list)-1:
                self.file_list[i+1], self.file_list[i] = self.file_list[i], self.file_list[i+1]
                self.merge_listbox.delete(i)
                self.merge_listbox.insert(i+1, os.path.basename(self.file_list[i+1]))
                self.merge_listbox.selection_set(i+1)

    def _merge_clear(self):
        self.file_list.clear(); self.merge_listbox.delete(0, tk.END)

    def _do_merge(self):
        if len(self.file_list) < 2:
            messagebox.showwarning("提示", "请至少添加 2 个 PDF 文件"); return
        if not self.merge_output.get():
            messagebox.showwarning("提示", "请选择输出文件位置"); return
        self._run_task(PDFEditor.merge_pdfs, self.file_list.copy(), self.merge_output.get())

    # ═════════════════════════════════════════════════
    # 2. 拆分
    # ═════════════════════════════════════════════════
    def _create_split_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="✂️ 拆分")
        f1 = tk.Frame(tab); f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.split_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.split_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.split_input)).pack(side=tk.LEFT)
        f2 = tk.Frame(tab); f2.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(f2, text="输出目录:").pack(side=tk.LEFT)
        self.split_output_dir = tk.StringVar()
        tk.Entry(f2, textvariable=self.split_output_dir, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output_dir(self.split_output_dir)).pack(side=tk.LEFT)
        mf = tk.LabelFrame(tab, text="拆分模式", padx=10, pady=10); mf.pack(fill=tk.X, padx=20, pady=10)
        self.split_mode = tk.StringVar(value="all")
        tk.Radiobutton(mf, text="每页拆分为单独文件", variable=self.split_mode, value="all").pack(anchor=tk.W)
        rf = tk.Frame(mf); rf.pack(fill=tk.X, anchor=tk.W)
        tk.Radiobutton(rf, text="按页码范围拆分:", variable=self.split_mode, value="range").pack(side=tk.LEFT)
        tk.Label(rf, text=" (如: 1-3,4-6)").pack(side=tk.LEFT)
        self.split_ranges = tk.StringVar()
        tk.Entry(mf, textvariable=self.split_ranges, width=50).pack(pady=5)
        tk.Button(tab, text="▶ 开始拆分", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_split).pack(pady=15)

    def _do_split(self):
        if not self.split_input.get(): messagebox.showwarning("提示","请选择输入文件"); return
        if not self.split_output_dir.get(): messagebox.showwarning("提示","请选择输出目录"); return
        mode = self.split_mode.get()
        if mode == 'all':
            self._run_task(PDFEditor.split_pdf, self.split_input.get(), self.split_output_dir.get(), 'all')
        else:
            try:
                ranges = [tuple(int(x) for x in p.split('-')) for p in self.split_ranges.get().split(',')]
            except Exception:
                messagebox.showerror("错误","页码范围格式错误"); return
            self._run_task(PDFEditor.split_pdf, self.split_input.get(), self.split_output_dir.get(), 'range', ranges)

    # ═════════════════════════════════════════════════
    # 3-9. 原版功能选项卡（保留，略去详细注释）
    # ═════════════════════════════════════════════════
    def _create_extract_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="📑 提取")
        f1 = tk.Frame(tab); f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.extract_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.extract_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.extract_input)).pack(side=tk.LEFT)
        tk.Label(tab, text="要提取的页码（用逗号分隔）:", font=('Arial', 10)).pack(pady=10)
        self.extract_pages_var = tk.StringVar()
        tk.Entry(tab, textvariable=self.extract_pages_var, width=50, font=('Arial', 11)).pack(pady=5)
        f2 = tk.Frame(tab); f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.extract_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.extract_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.extract_output)).pack(side=tk.LEFT)
        tk.Button(tab, text="▶ 开始提取", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_extract).pack(pady=15)

    def _do_extract(self):
        try: pages = [int(x) for x in self.extract_pages_var.get().split(',')]
        except Exception: messagebox.showerror("错误","页码格式错误"); return
        self._run_task(PDFEditor.extract_pages, self.extract_input.get(), self.extract_output.get(), pages)

    def _create_delete_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="🗑️ 删页")
        f1 = tk.Frame(tab); f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.delete_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.delete_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.delete_input)).pack(side=tk.LEFT)
        tk.Label(tab, text="要删除的页码（用逗号分隔）:", font=('Arial', 10)).pack(pady=10)
        self.delete_pages_var = tk.StringVar()
        tk.Entry(tab, textvariable=self.delete_pages_var, width=50, font=('Arial', 11)).pack(pady=5)
        f2 = tk.Frame(tab); f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.delete_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.delete_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.delete_output)).pack(side=tk.LEFT)
        tk.Button(tab, text="▶ 开始删除", font=('Arial', 12, 'bold'),
                  bg='#e84040', fg='white', padx=30, pady=5,
                  command=self._do_delete).pack(pady=15)

    def _do_delete(self):
        try: pages = [int(x) for x in self.delete_pages_var.get().split(',')]
        except Exception: messagebox.showerror("错误","页码格式错误"); return
        self._run_task(PDFEditor.delete_pages, self.delete_input.get(), self.delete_output.get(), pages)

    def _create_rotate_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="🔄 旋转")
        f1 = tk.Frame(tab); f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.rotate_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.rotate_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.rotate_input)).pack(side=tk.LEFT)
        af = tk.LabelFrame(tab, text="旋转角度", padx=10, pady=10); af.pack(fill=tk.X, padx=20, pady=10)
        self.rotate_angle = tk.StringVar(value="90")
        for v, t in [("90","90°"),("180","180°"),("270","270°")]:
            tk.Radiobutton(af, text=t, variable=self.rotate_angle, value=v).pack(side=tk.LEFT, padx=20)
        rf = tk.LabelFrame(tab, text="旋转范围", padx=10, pady=10); rf.pack(fill=tk.X, padx=20, pady=10)
        self.rotate_all = tk.BooleanVar(value=True)
        tk.Radiobutton(rf, text="所有页面", variable=self.rotate_all, value=True).pack(anchor=tk.W)
        tk.Radiobutton(rf, text="指定页面（逗号分隔）:", variable=self.rotate_all, value=False).pack(anchor=tk.W)
        self.rotate_pages_var = tk.StringVar()
        tk.Entry(rf, textvariable=self.rotate_pages_var, width=40).pack(pady=5)
        f2 = tk.Frame(tab); f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.rotate_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.rotate_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.rotate_output)).pack(side=tk.LEFT)
        tk.Button(tab, text="▶ 开始旋转", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_rotate).pack(pady=15)

    def _do_rotate(self):
        angle = int(self.rotate_angle.get())
        pages = None
        if not self.rotate_all.get():
            try: pages = [int(x) for x in self.rotate_pages_var.get().split(',')]
            except Exception: messagebox.showerror("错误","页码格式错误"); return
        self._run_task(PDFEditor.rotate_pages, self.rotate_input.get(), self.rotate_output.get(), angle, pages)

    def _create_watermark_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="💧 水印")
        f1 = tk.Frame(tab); f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.wm_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.wm_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.wm_input)).pack(side=tk.LEFT)
        tk.Label(tab, text="水印文字:", font=('Arial', 10)).pack(pady=(15,5))
        self.wm_text = tk.StringVar(value="CONFIDENTIAL")
        tk.Entry(tab, textvariable=self.wm_text, width=50, font=('Arial', 12)).pack(pady=5)
        pf = tk.Frame(tab); pf.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(pf, text="字号:").grid(row=0, column=0, padx=5, sticky='w')
        self.wm_fontsize = tk.IntVar(value=50)
        tk.Spinbox(pf, from_=10, to=200, textvariable=self.wm_fontsize, width=8).grid(row=0, column=1, padx=5)
        tk.Label(pf, text="透明度:").grid(row=0, column=2, padx=15, sticky='w')
        self.wm_opacity = tk.DoubleVar(value=0.3)
        tk.Spinbox(pf, from_=0.1, to=1.0, increment=0.1, textvariable=self.wm_opacity, width=8).grid(row=0, column=3, padx=5)
        f2 = tk.Frame(tab); f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.wm_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.wm_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.wm_output)).pack(side=tk.LEFT)
        tk.Button(tab, text="▶ 添加水印", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_watermark).pack(pady=15)

    def _do_watermark(self):
        color_map = {'gray':(128,128,128),'red':(255,0,0),'blue':(0,0,255),'green':(0,128,0),'black':(0,0,0)}
        color = color_map.get(getattr(self, 'wm_color', None) and self.wm_color.get() or 'gray', (128,128,128))
        self._run_task(PDFEditor.add_watermark, self.wm_input.get(), self.wm_output.get(),
                       self.wm_text.get(), self.wm_opacity.get(), self.wm_fontsize.get(), color)

    def _create_security_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="🔒 安全")
        ef = tk.LabelFrame(tab, text="🔐 加密", padx=10, pady=10); ef.pack(fill=tk.X, padx=20, pady=10)
        f1 = tk.Frame(ef); f1.pack(fill=tk.X, pady=3)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.enc_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.enc_input, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.enc_input)).pack(side=tk.LEFT)
        f2 = tk.Frame(ef); f2.pack(fill=tk.X, pady=3)
        tk.Label(f2, text="密码:").pack(side=tk.LEFT)
        self.enc_password = tk.StringVar()
        tk.Entry(f2, textvariable=self.enc_password, width=20, show='*').pack(side=tk.LEFT, padx=5)
        f3 = tk.Frame(ef); f3.pack(fill=tk.X, pady=3)
        tk.Label(f3, text="输出文件:").pack(side=tk.LEFT)
        self.enc_output = tk.StringVar()
        tk.Entry(f3, textvariable=self.enc_output, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(f3, text="浏览", command=lambda: self._select_output(self.enc_output)).pack(side=tk.LEFT)
        tk.Button(ef, text="▶ 加密", bg='#e8a01a', fg='white', font=('Arial', 10, 'bold'), command=self._do_encrypt).pack(pady=5)

        df = tk.LabelFrame(tab, text="🔓 解密", padx=10, pady=10); df.pack(fill=tk.X, padx=20, pady=10)
        f4 = tk.Frame(df); f4.pack(fill=tk.X, pady=3)
        tk.Label(f4, text="输入文件:").pack(side=tk.LEFT)
        self.dec_input = tk.StringVar()
        tk.Entry(f4, textvariable=self.dec_input, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(f4, text="浏览", command=lambda: self._select_file(self.dec_input)).pack(side=tk.LEFT)
        f5 = tk.Frame(df); f5.pack(fill=tk.X, pady=3)
        tk.Label(f5, text="密码:").pack(side=tk.LEFT)
        self.dec_password = tk.StringVar()
        tk.Entry(f5, textvariable=self.dec_password, width=20, show='*').pack(side=tk.LEFT, padx=5)
        f6 = tk.Frame(df); f6.pack(fill=tk.X, pady=3)
        tk.Label(f6, text="输出文件:").pack(side=tk.LEFT)
        self.dec_output = tk.StringVar()
        tk.Entry(f6, textvariable=self.dec_output, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(f6, text="浏览", command=lambda: self._select_output(self.dec_output)).pack(side=tk.LEFT)
        tk.Button(df, text="▶ 解密", bg='#1a73e8', fg='white', font=('Arial', 10, 'bold'), command=self._do_decrypt).pack(pady=5)

    def _do_encrypt(self):
        self._run_task(PDFEditor.encrypt_pdf, self.enc_input.get(), self.enc_output.get(), self.enc_password.get())

    def _do_decrypt(self):
        self._run_task(PDFEditor.decrypt_pdf, self.dec_input.get(), self.dec_output.get(), self.dec_password.get())

    def _create_text_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="📝 文本")
        f1 = tk.Frame(tab); f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.text_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.text_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.text_input)).pack(side=tk.LEFT)
        tk.Label(tab, text="提取的文本内容:", font=('Arial', 10)).pack(pady=(15,5))
        self.text_display = scrolledtext.ScrolledText(tab, height=12, wrap=tk.WORD, font=('Arial', 10))
        self.text_display.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        bf = tk.Frame(tab); bf.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(bf, text="▶ 提取文本", bg='#1a73e8', fg='white', font=('Arial', 10, 'bold'), command=self._do_extract_text).pack(side=tk.LEFT, padx=5)
        self.text_output_path = tk.StringVar()
        tk.Label(bf, text="保存为:").pack(side=tk.LEFT, padx=(20,5))
        tk.Entry(bf, textvariable=self.text_output_path, width=25).pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="浏览", command=lambda: self._select_output(self.text_output_path, '.txt')).pack(side=tk.LEFT)
        tk.Button(bf, text="保存", command=self._save_text).pack(side=tk.LEFT, padx=5)

    def _do_extract_text(self):
        def worker():
            try:
                self.status_var.set("正在提取文本..."); self.root.update()
                ok, result = PDFEditor.extract_text(self.text_input.get())
                self.text_display.delete(1.0, tk.END)
                self.text_display.insert(1.0, result if ok else "")
                self.status_var.set("✅ 文本提取完成" if ok else f"❌ {result}")
            except Exception as e:
                messagebox.showerror("错误", str(e))
        threading.Thread(target=worker, daemon=True).start()

    def _save_text(self):
        text = self.text_display.get(1.0, tk.END).strip()
        if not text: messagebox.showwarning("提示","没有文本内容"); return
        if not self.text_output_path.get(): messagebox.showwarning("提示","请选择保存路径"); return
        with open(self.text_output_path.get(),'w',encoding='utf-8') as f: f.write(text)
        messagebox.showinfo("成功","文本已保存")

    def _create_compress_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="🗜️ 压缩")
        f1 = tk.Frame(tab); f1.pack(fill=tk.X, padx=20, pady=15)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.compress_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.compress_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.compress_input)).pack(side=tk.LEFT)
        self.compress_info = tk.StringVar(value="等待选择文件...")
        tk.Label(tab, textvariable=self.compress_info, font=('Arial', 10), fg='#555').pack(pady=10)
        f2 = tk.Frame(tab); f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.compress_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.compress_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.compress_output)).pack(side=tk.LEFT)
        tk.Button(tab, text="▶ 开始压缩", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_compress).pack(pady=15)
        tk.Label(tab, text="💡 压缩通过优化 PDF 内部结构实现", font=('Arial', 9), fg='#888').pack(pady=20)

    def _do_compress(self):
        if not self.compress_input.get(): messagebox.showwarning("提示","请选择输入文件"); return
        if not self.compress_output.get(): messagebox.showwarning("提示","请选择输出文件"); return
        size = os.path.getsize(self.compress_input.get())
        self.compress_info.set(f"原始文件大小: {size/1024:.1f} KB")
        self._run_task(PDFEditor.compress_pdf, self.compress_input.get(), self.compress_output.get())

    # ═════════════════════════════════════════════════
    # ★ 10. 内容编辑（v2.2 字体修复版）
    # ═════════════════════════════════════════════════
    def _create_content_editor_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="✏️ 内容编辑")

        # ── 字体状态提示 ──
        font_status = tk.Label(tab, text=self._font_info, font=('Arial', 8), fg='#1a73e8')
        font_status.pack(anchor='w', padx=10, pady=2)

        # ── 加载区 ──
        load_f = tk.Frame(tab); load_f.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(load_f, text="PDF 文件:").pack(side=tk.LEFT)
        self.ce_input = tk.StringVar()
        tk.Entry(load_f, textvariable=self.ce_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(load_f, text="浏览", command=lambda: self._select_file(self.ce_input)).pack(side=tk.LEFT, padx=3)
        tk.Button(load_f, text="🔍 解析PDF", bg='#1a73e8', fg='white', font=('Arial',10,'bold'),
                  command=self._ce_load).pack(side=tk.LEFT, padx=10)

        # ── 页面选择 ──
        page_f = tk.Frame(tab); page_f.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(page_f, text="页面:").pack(side=tk.LEFT)
        self.ce_page_sel = tk.Spinbox(page_f, from_=1, to=1, width=6, command=self._ce_refresh_view)
        self.ce_page_sel.pack(side=tk.LEFT, padx=5)
        tk.Label(page_f, text="(解析后可选)").pack(side=tk.LEFT, padx=5)

        # ── 主编辑区 ──
        self.ce_note = ttk.Notebook(tab)
        self.ce_note.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._ce_build_text_tab()
        self._ce_build_image_tab()
        self._ce_build_table_tab()
        self._ce_build_find_tab()

        # ── 输出区 ──
        out_f = tk.Frame(tab); out_f.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(out_f, text="输出文件:").pack(side=tk.LEFT)
        self.ce_output = tk.StringVar()
        tk.Entry(out_f, textvariable=self.ce_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(out_f, text="浏览", command=lambda: self._select_output(self.ce_output)).pack(side=tk.LEFT, padx=3)
        tk.Button(out_f, text="💾 生成PDF", bg='#28a745', fg='white', font=('Arial',12,'bold'),
                  padx=20, command=self._ce_generate).pack(side=tk.LEFT, padx=15)

    # ── 文字编辑子页（v2.2 字体修复）──────────────
    def _ce_build_text_tab(self):
        t = ttk.Frame(self.ce_note)
        self.ce_note.add(t, text="📝 文字")

        list_f = tk.Frame(t); list_f.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ce_text_list = tk.Listbox(list_f, height=10)
        self.ce_text_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(list_f, orient=tk.VERTICAL, command=self.ce_text_list.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.ce_text_list.config(yscrollcommand=sb.set)
        self.ce_text_list.bind('<<ListboxSelect>>', self._ce_text_select)

        f = tk.LabelFrame(t, text="编辑选中文字", padx=8, pady=8)
        f.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(f, text="内容:").grid(row=0, column=0, sticky='w')
        self.ce_text_content = tk.StringVar()
        tk.Entry(f, textvariable=self.ce_text_content, width=50).grid(row=0, column=1, padx=5, pady=2)

        tk.Label(f, text="字号:").grid(row=1, column=0, sticky='w')
        self.ce_text_size = tk.IntVar(value=11)
        tk.Spinbox(f, from_=6, to=72, textvariable=self.ce_text_size, width=8).grid(row=1, column=1, sticky='w', padx=5)

        # ★ v2.2: 字体下拉选择（只列出已注册可用的字体）
        tk.Label(f, text="字体:").grid(row=1, column=2, padx=10)
        font_choices = list(_REGISTERED_FONTS.keys()) + (['Helvetica'] if 'Helvetica' not in _REGISTERED_FONTS else [])
        self.ce_text_font = tk.StringVar(value=CHINESE_FONT)
        tk.OptionMenu(f, self.ce_text_font, *font_choices).grid(row=1, column=3, padx=5)

        tk.Label(f, text="颜色(hex):").grid(row=2, column=0, sticky='w')
        self.ce_text_color = tk.StringVar(value="#000000")
        tk.Entry(f, textvariable=self.ce_text_color, width=12).grid(row=2, column=1, sticky='w', padx=5)

        tk.Label(f, text="X:").grid(row=3, column=0, sticky='w')
        self.ce_text_x = tk.IntVar(value=0)
        tk.Entry(f, textvariable=self.ce_text_x, width=8).grid(row=3, column=1, sticky='w', padx=5)
        tk.Label(f, text="Y:").grid(row=3, column=2, padx=10)
        self.ce_text_y = tk.IntVar(value=0)
        tk.Entry(f, textvariable=self.ce_text_y, width=8).grid(row=3, column=3, padx=5)

        btn_f = tk.Frame(f); btn_f.grid(row=4, column=0, columnspan=4, pady=5)
        tk.Button(btn_f, text="✅ 应用修改", command=self._ce_text_apply).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="➕ 新增文字", command=self._ce_text_add).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="❌ 删除选中", command=self._ce_text_delete).pack(side=tk.LEFT, padx=5)

        rep_f = tk.LabelFrame(t, text="批量替换", padx=8, pady=5)
        rep_f.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(rep_f, text="查找:").pack(side=tk.LEFT)
        self.ce_rep_old = tk.StringVar()
        tk.Entry(rep_f, textvariable=self.ce_rep_old, width=15).pack(side=tk.LEFT, padx=3)
        tk.Label(rep_f, text="替换为:").pack(side=tk.LEFT, padx=5)
        self.ce_rep_new = tk.StringVar()
        tk.Entry(rep_f, textvariable=self.ce_rep_new, width=15).pack(side=tk.LEFT, padx=3)
        tk.Button(rep_f, text="🔄 全部替换", command=self._ce_text_replace_all).pack(side=tk.LEFT, padx=10)

    # ── 图片编辑子页 ──────────────────────────────────
    def _ce_build_image_tab(self):
        t = ttk.Frame(self.ce_note)
        self.ce_note.add(t, text="🖼️ 图片")

        self.ce_img_status = tk.StringVar(value="(选择图片后查看状态)")
        tk.Label(t, textvariable=self.ce_img_status, font=('Arial', 9), fg='#666').pack(anchor='w', padx=10, pady=3)

        list_f = tk.Frame(t); list_f.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ce_img_list = tk.Listbox(list_f, height=8)
        self.ce_img_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(list_f, orient=tk.VERTICAL, command=self.ce_img_list.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.ce_img_list.config(yscrollcommand=sb.set)
        self.ce_img_list.bind('<<ListboxSelect>>', self._ce_img_select)

        f = tk.LabelFrame(t, text="编辑选中图片", padx=8, pady=8)
        f.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(f, text="缩放比例:").grid(row=0, column=0, sticky='w')
        self.ce_img_scale = tk.DoubleVar(value=1.0)
        tk.Spinbox(f, from_=0.1, to=5.0, increment=0.1, textvariable=self.ce_img_scale, width=8).grid(row=0, column=1, padx=5)

        tk.Label(f, text="宽度(pt):").grid(row=0, column=2, padx=10)
        self.ce_img_w = tk.IntVar(value=0)
        tk.Entry(f, textvariable=self.ce_img_w, width=8).grid(row=0, column=3, padx=5)
        tk.Label(f, text="高度(pt):").grid(row=1, column=2, padx=10)
        self.ce_img_h = tk.IntVar(value=0)
        tk.Entry(f, textvariable=self.ce_img_h, width=8).grid(row=1, column=3, padx=5)

        tk.Label(f, text="X:").grid(row=1, column=0, sticky='w')
        self.ce_img_x = tk.IntVar(value=0)
        tk.Entry(f, textvariable=self.ce_img_x, width=8).grid(row=1, column=1, padx=5)
        tk.Label(f, text="Y:").grid(row=2, column=0, sticky='w')
        self.ce_img_y = tk.IntVar(value=0)
        tk.Entry(f, textvariable=self.ce_img_y, width=8).grid(row=2, column=1, padx=5)

        btn_f = tk.Frame(f); btn_f.grid(row=3, column=0, columnspan=4, pady=5)
        tk.Button(btn_f, text="✅ 应用修改", command=self._ce_img_apply).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="➕ 添加图片", command=self._ce_img_add).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="❌ 删除选中", command=self._ce_img_delete).pack(side=tk.LEFT, padx=5)
        tk.Label(btn_f, text="(新图片将插入到当前页)").pack(side=tk.LEFT, padx=10)

    # ── 表格编辑子页 ──────────────────────────────────
    def _ce_build_table_tab(self):
        t = ttk.Frame(self.ce_note)
        self.ce_note.add(t, text="📊 表格")

        sel_f = tk.Frame(t); sel_f.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(sel_f, text="选择表格:").pack(side=tk.LEFT)
        self.ce_tbl_sel = tk.Spinbox(sel_f, from_=0, to=0, width=5, command=self._ce_tbl_select)
        self.ce_tbl_sel.pack(side=tk.LEFT, padx=5)

        prev_f = tk.LabelFrame(t, text="表格内容（编辑后点应用）", padx=5, pady=5)
        prev_f.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.ce_tbl_text = scrolledtext.ScrolledText(prev_f, height=10, font=('Courier', 10))
        self.ce_tbl_text.pack(fill=tk.BOTH, expand=True)
        self.ce_tbl_text.insert(1.0, "加载表格后，此处显示 CSV 格式内容\n第一行=表头，后续行=数据\n修改后点击「应用表格修改」")

        cw_f = tk.Frame(t); cw_f.pack(fill=tk.X, padx=5, pady=3)
        tk.Label(cw_f, text="列宽(逗号分隔,pt):").pack(side=tk.LEFT)
        self.ce_tbl_cw = tk.StringVar()
        tk.Entry(cw_f, textvariable=self.ce_tbl_cw, width=40).pack(side=tk.LEFT, padx=5)

        btn_f = tk.Frame(t); btn_f.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(btn_f, text="✅ 应用表格修改", bg='#1a73e8', fg='white',
                  command=self._ce_tbl_apply).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="➕ 添加一行", command=self._ce_tbl_add_row).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="➕ 添加一列", command=self._ce_tbl_add_col).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="❌ 删除最后一行", command=self._ce_tbl_del_row).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="❌ 删除最后一列", command=self._ce_tbl_del_col).pack(side=tk.LEFT, padx=5)

    # ── 查找子页 ──────────────────────────────────────
    def _ce_build_find_tab(self):
        t = ttk.Frame(self.ce_note)
        self.ce_note.add(t, text="🔎 查找")

        f = tk.Frame(t); f.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(f, text="查找文字:").pack(side=tk.LEFT)
        self.ce_find_kw = tk.StringVar()
        tk.Entry(f, textvariable=self.ce_find_kw, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="🔍 查找全部", command=self._ce_find).pack(side=tk.LEFT, padx=10)

        self.ce_find_result = scrolledtext.ScrolledText(t, height=10, font=('Courier', 10))
        self.ce_find_result.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # ──────────────────────────────────────────────────────
    # 内容编辑：事件处理（v2.2 字体修复）
    # ──────────────────────────────────────────────────────
    def _ce_load(self):
        path = self.ce_input.get()
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示","请选择有效的 PDF 文件"); return
        def worker():
            try:
                self.status_var.set("正在解析 PDF（文字/图片/表格）...")
                self.root.update()
                self._page_models = PDFContentParser.parse(path)
                self._current_page_idx = 0
                self.ce_page_sel.config(from_=1, to=max(1, len(self._page_models)))
                self.ce_page_sel.delete(0, tk.END)
                self.ce_page_sel.insert(0, "1")

                total_texts = sum(len(pm.texts) for pm in self._page_models)
                total_imgs = sum(len(pm.images) for pm in self._page_models)
                total_tbls = sum(len(pm.tables) for pm in self._page_models)

                # ★ 字体诊断信息
                font_used = set()
                for pm in self._page_models:
                    for tb in pm.texts:
                        font_used.add(tb.fontname)

                self.status_var.set(
                    f"✅ 解析完成：{len(self._page_models)}页 | 文字{total_texts} | 图片{total_imgs} | 表格{total_tbls} | 字体: {font_used}"
                )
                self._ce_refresh_view()
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                self.status_var.set(f"❌ 解析失败: {err_msg}")
                messagebox.showerror("错误", f"解析失败:\n{err_msg}\n\n{traceback.format_exc()[:500]}")
        threading.Thread(target=worker, daemon=True).start()

    def _ce_refresh_view(self):
        if not self._page_models: return
        try:
            idx = int(self.ce_page_sel.get()) - 1
        except Exception:
            idx = 0
        self._current_page_idx = max(0, min(idx, len(self._page_models)-1))
        pm = self._page_models[self._current_page_idx]

        # 文字
        self.ce_text_list.delete(0, tk.END)
        for i, tb in enumerate(pm.texts):
            preview = (tb.text or '')[:40].replace('\n','')
            # ★ 显示字体名（已归一化）+ 可用性标记
            font_ok = "✓" if is_font_available(tb.fontname) else "⚠"
            self.ce_text_list.insert(tk.END, f"[{i}] {font_ok} {preview} (font={tb.fontname}, size={tb.fontsize})")

        # 图片
        self.ce_img_list.delete(0, tk.END)
        for i, ib in enumerate(pm.images):
            info = PDFEditorAdvanced.get_image_info(self._page_models, self._current_page_idx, i)
            status = "✓" if info['is_valid'] else "⚠"
            fmt = info['format'] or 'unknown'
            self.ce_img_list.insert(tk.END, f"[{i}] {status} {fmt} {info['width']:.0f}x{info['height']:.0f} @({info['x']:.0f},{info['y']:.0f})")

        # 表格
        if pm.tables:
            self.ce_tbl_sel.config(from_=1, to=len(pm.tables))
            self.ce_tbl_sel.delete(0, tk.END)
            self.ce_tbl_sel.insert(0, "1")
            self._ce_tbl_select()
        else:
            self.ce_tbl_text.delete(1.0, tk.END)
            self.ce_tbl_text.insert(1.0, "(当前页无表格)")

    # ── 文字事件（v2.2 修复）──────────────────────
    def _ce_text_select(self, event=None):
        sel = self.ce_text_list.curselection()
        if not sel or not self._page_models: return
        idx = sel[0]
        pm = self._page_models[self._current_page_idx]
        if 0 <= idx < len(pm.texts):
            tb = pm.texts[idx]
            self.ce_text_content.set(tb.text or '')
            self.ce_text_size.set(int(tb.fontsize or 11))
            # ★ 字体名必须是已注册的
            fn = tb.fontname if is_font_available(tb.fontname) else CHINESE_FONT
            self.ce_text_font.set(fn)
            try:
                self.ce_text_color.set(tb.color.hexval() if hasattr(tb.color,'hexval') else "#000000")
            except Exception:
                self.ce_text_color.set("#000000")
            self.ce_text_x.set(int(tb.x or 0))
            self.ce_text_y.set(int(tb.y or 0))

    def _ce_text_apply(self):
        sel = self.ce_text_list.curselection()
        if not sel or not self._page_models: return
        idx = sel[0]
        pm = self._page_models[self._current_page_idx]
        if idx >= len(pm.texts): return
        tb = pm.texts[idx]

        # ★ 清洗文字 + 归一化字体
        tb.text = _clean_text(self.ce_text_content.get())
        tb.fontsize = self.ce_text_size.get()
        tb.fontname = normalize_font_name(self.ce_text_font.get())  # ★ 关键修复
        try: tb.color = HexColor(self.ce_text_color.get())
        except Exception: pass
        tb.x = self.ce_text_x.get()
        tb.y = self.ce_text_y.get()

        # 验证字体可用
        if not is_font_available(tb.fontname):
            tb.fontname = CHINESE_FONT
            self.status_var.set(f"⚠ 字体 '{self.ce_text_font.get()}' 不可用，已回退到 {CHINESE_FONT}")
        else:
            self.status_var.set(f"✅ 已修改文字 #{idx} (font={tb.fontname})")

        self._ce_refresh_view()

    def _ce_text_add(self):
        if not self._page_models: return
        pm = self._page_models[self._current_page_idx]
        fontname = normalize_font_name(self.ce_text_font.get())
        PDFEditorAdvanced.add_text(pm, 0, "新文字", x=50, y=50, fontsize=12, fontname=fontname)
        self._ce_refresh_view()

    def _ce_text_delete(self):
        sel = self.ce_text_list.curselection()
        if not sel or not self._page_models: return
        PDFEditorAdvanced.delete_text(self._page_models, self._current_page_idx, sel[0])
        self._ce_refresh_view()

    def _ce_text_replace_all(self):
        if not self._page_models: return
        old = self.ce_rep_old.get()
        new = self.ce_rep_new.get()
        if not old: return
        n = PDFEditorAdvanced.replace_all_text(self._page_models, old, new)
        self._ce_refresh_view()
        messagebox.showinfo("完成", f"共替换 {n} 处")

    # ── 图片 ──────────────────────────────────────────
    def _ce_img_select(self, event=None):
        sel = self.ce_img_list.curselection()
        if not sel or not self._page_models: return
        idx = sel[0]
        info = PDFEditorAdvanced.get_image_info(self._page_models, self._current_page_idx, idx)
        ib = self._page_models[self._current_page_idx].images[idx]
        self.ce_img_w.set(int(ib.width or 0))
        self.ce_img_h.set(int(ib.height or 0))
        self.ce_img_x.set(int(ib.x or 0))
        self.ce_img_y.set(int(ib.y or 0))
        self.ce_img_scale.set(1.0)
        if info['is_valid']:
            self.ce_img_status.set(f"✓ 有效图片 | 格式: {info['format']} | 原始: {info['original_width']}x{info['original_height']}")
        elif info['has_data']:
            self.ce_img_status.set(f"⚠ 图片数据存在但可能损坏 | 建议用「添加图片」替换")
        else:
            self.ce_img_status.set(f"⚠ 无法提取图片数据 | 请使用「添加图片」插入新图片")

    def _ce_img_apply(self):
        sel = self.ce_img_list.curselection()
        if not sel or not self._page_models: return
        idx = sel[0]
        pm = self._page_models[self._current_page_idx]
        if idx >= len(pm.images): return
        ib = pm.images[idx]
        scale = self.ce_img_scale.get()
        if scale and scale != 1.0:
            PDFEditorAdvanced.scale_image(self._page_models, self._current_page_idx, idx, scale)
        else:
            PDFEditorAdvanced.edit_image(
                self._page_models, self._current_page_idx, idx,
                width=self.ce_img_w.get() if self.ce_img_w.get() > 0 else None,
                height=self.ce_img_h.get() if self.ce_img_h.get() > 0 else None,
                x=self.ce_img_x.get(), y=self.ce_img_y.get()
            )
        self._ce_refresh_view()
        self.status_var.set(f"✅ 已修改图片 #{idx}")

    def _ce_img_add(self):
        if not self._page_models:
            messagebox.showwarning("提示", "请先解析 PDF"); return
        path = filedialog.askopenfilename(filetypes=[("图片","*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.tif")])
        if not path: return
        if HAS_PIL:
            try:
                img = PILImage.open(path); img.verify()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图片:\n{e}"); return
        new_idx = PDFEditorAdvanced.add_image(
            self._page_models, self._current_page_idx, path, x=50, y=50, width=200, height=150
        )
        self._ce_refresh_view()
        self.status_var.set(f"✅ 已添加图片 #{new_idx}")

    def _ce_img_delete(self):
        sel = self.ce_img_list.curselection()
        if not sel or not self._page_models: return
        PDFEditorAdvanced.delete_image(self._page_models, self._current_page_idx, sel[0])
        self._ce_refresh_view()

    # ── 表格 ──────────────────────────────────────────
    def _ce_tbl_select(self, event=None):
        if not self._page_models: return
        try: t_idx = int(self.ce_tbl_sel.get()) - 1
        except: t_idx = 0
        pm = self._page_models[self._current_page_idx]
        if 0 <= t_idx < len(pm.tables):
            tb = pm.tables[t_idx]
            lines = [','.join(str(h) for h in tb.headers)]
            for row in tb.rows:
                lines.append(','.join(str(c) for c in row))
            self.ce_tbl_text.delete(1.0, tk.END)
            self.ce_tbl_text.insert(1.0, '\n'.join(lines))
            self.ce_tbl_cw.set(','.join(str(int(w)) for w in tb.col_widths))

    def _ce_tbl_apply(self):
        if not self._page_models: return
        try: t_idx = int(self.ce_tbl_sel.get()) - 1
        except: t_idx = 0
        pm = self._page_models[self._current_page_idx]
        if not (0 <= t_idx < len(pm.tables)): return
        tb = pm.tables[t_idx]
        text = self.ce_tbl_text.get(1.0, tk.END).strip()
        lines = [l for l in text.split('\n') if l.strip()]
        if not lines: return
        headers = [c.strip() for c in lines[0].split(',')]
        rows = [[c.strip() for c in l.split(',')] for l in lines[1:]]
        max_cols = max(len(headers), max((len(r) for r in rows), default=0))
        headers += [f'col{len(headers)+i+1}' for i in range(max_cols - len(headers))]
        rows = [r + ['' for _ in range(max_cols - len(r))] for r in rows]
        # ★ 清洗表格内容
        headers = [_clean_text(h) for h in headers]
        rows = [[_clean_text(c) for c in r] for r in rows]
        tb.set_data(headers, rows)
        cw_str = self.ce_tbl_cw.get().strip()
        if cw_str:
            try:
                widths = [float(x) for x in cw_str.split(',')]
                if len(widths) == len(headers): tb.col_widths = widths
                elif len(widths) > len(headers): tb.col_widths = widths[:len(headers)]
                else: tb.col_widths = widths + [80]*(len(headers)-len(widths))
            except Exception: pass
        self._ce_refresh_view()
        self.status_var.set(f"✅ 表格已更新")

    def _ce_tbl_add_row(self):
        if not self._page_models: return
        try: t_idx = int(self.ce_tbl_sel.get())-1
        except: t_idx = 0
        pm = self._page_models[self._current_page_idx]
        if t_idx < len(pm.tables):
            pm.tables[t_idx].add_row(['']*len(pm.tables[t_idx].headers))
            self._ce_tbl_select()

    def _ce_tbl_add_col(self):
        if not self._page_models: return
        try: t_idx = int(self.ce_tbl_sel.get())-1
        except: t_idx = 0
        pm = self._page_models[self._current_page_idx]
        if t_idx < len(pm.tables):
            pm.tables[t_idx].add_column('新列','')
            self._ce_tbl_select()

    def _ce_tbl_del_row(self):
        if not self._page_models: return
        try: t_idx = int(self.ce_tbl_sel.get())-1
        except: t_idx = 0
        pm = self._page_models[self._current_page_idx]
        if t_idx < len(pm.tables) and pm.tables[t_idx].rows:
            pm.tables[t_idx].delete_row(len(pm.tables[t_idx].rows)-1)
            self._ce_tbl_select()

    def _ce_tbl_del_col(self):
        if not self._page_models: return
        try: t_idx = int(self.ce_tbl_sel.get())-1
        except: t_idx = 0
        pm = self._page_models[self._current_page_idx]
        if t_idx < len(pm.tables) and len(pm.tables[t_idx].headers) > 1:
            pm.tables[t_idx].delete_column(len(pm.tables[t_idx].headers)-1)
            self._ce_tbl_select()

    # ── 查找 ──────────────────────────────────────────
    def _ce_find(self):
        if not self._page_models: return
        kw = self.ce_find_kw.get()
        if not kw: return
        results = PDFEditorAdvanced.find_text(self._page_models, kw)
        self.ce_find_result.delete(1.0, tk.END)
        if not results:
            self.ce_find_result.insert(1.0, f"未找到「{kw}」")
            return
        lines = [f"找到 {len(results)} 处：「{kw}」\n{'='*40}"]
        for pi, ti, text in results:
            lines.append(f"  第{pi+1}页 [# {ti}] {text[:60]}")
        self.ce_find_result.insert(1.0, '\n'.join(lines))

    # ── 生成输出（v2.2 字体保障）──────────────────
    def _ce_generate(self):
        if not self._page_models:
            messagebox.showwarning("提示","请先解析 PDF"); return
        out = self.ce_output.get()
        if not out:
            messagebox.showwarning("提示","请选择输出文件"); return

        # ★ 生成前最终字体检查
        font_report = {}
        for pi, pm in enumerate(self._page_models):
            for tb in pm.texts:
                fn = tb.fontname
                if fn not in font_report:
                    font_report[fn] = {'count': 0, 'available': is_font_available(fn)}
                font_report[fn]['count'] += 1

        # 自动修复不可用的字体
        fixed_count = 0
        for pi, pm in enumerate(self._page_models):
            for tb in pm.texts:
                if not is_font_available(tb.fontname):
                    tb.fontname = CHINESE_FONT
                    fixed_count += 1

        if fixed_count > 0:
            self.status_var.set(f"⚠ 自动修复 {fixed_count} 处字体回退到 {CHINESE_FONT}")

        def worker():
            try:
                self.status_var.set("正在重新生成 PDF...")
                self.root.update()
                PDFRegenerator.generate(self._page_models, out)
                sz = os.path.getsize(out)
                self.status_var.set(f"✅ 已生成: {out} ({sz/1024:.1f}KB)")
                messagebox.showinfo("成功",
                    f"PDF 已生成：\n{out}\n大小: {sz/1024:.1f}KB\n\n字体使用:\n" +
                    '\n'.join(f"  {fn}: {info['count']}处 ({'✓' if info['available'] else '已回退'})"
                              for fn, info in font_report.items()))
            except Exception as e:
                err_msg = f"{type(e).__name__}: {e}"
                self.status_var.set(f"❌ 生成失败: {err_msg}")
                messagebox.showerror("错误", f"生成失败:\n{err_msg}\n\n{traceback.format_exc()[:500]}")
        threading.Thread(target=worker, daemon=True).start()


# ═══════════════════════════════════════════════════════════
# 程序入口
# ═══════════════════════════════════════════════════════════
def main():
    if not _HAS_TK:
        print("错误: 当前环境没有 tkinter，无法启动 GUI。")
        print("核心模块（PDFContentParser / PDFRegenerator / PDFEditorAdvanced）仍可正常导入使用。")
        sys.exit(1)
    root = tk.Tk()
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    x = (root.winfo_screenwidth()//2) - (w//2)
    y = (root.winfo_screenheight()//2) - (h//2)
    root.geometry(f"+{x}+{y}")
    app = PDFEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
