"""
PDF Editor - 功能完善的 PDF 编辑工具
功能包括：
1. 合并 PDF
2. 拆分 PDF
3. 提取指定页面
4. 添加水印
5. 加密/解密 PDF
6. 旋转页面
7. 删除页面
8. 提取文本
9. 添加密码
10. 压缩 PDF
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import os
import sys
import threading
from datetime import datetime

# PDF 处理库
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from PyPDF2.generic import NameObject, ArrayObject, NumberObject
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

# 尝试注册中文字体
try:
    pdfmetrics.registerFont(TTFont('WenQuanYi', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'))
    CHINESE_FONT = 'WenQuanYi'
except:
    CHINESE_FONT = 'Helvetica'


class PDFEditor:
    """PDF 编辑核心功能类"""
    
    @staticmethod
    def merge_pdfs(input_paths, output_path):
        """合并多个 PDF 文件"""
        merger = PdfMerger()
        for path in input_paths:
            merger.append(path)
        with open(output_path, 'wb') as f:
            merger.write(f)
        merger.close()
        return True, f"成功合并 {len(input_paths)} 个文件 → {output_path}"
    
    @staticmethod
    def split_pdf(input_path, output_dir, mode='all', page_ranges=None):
        """拆分 PDF
        mode: 'all' 每页一个文件, 'range' 按范围拆分
        """
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
                start = max(0, start - 1)  # 转为0索引
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
        """提取指定页面（1-based 页码列表）"""
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
        """删除指定页面"""
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
        """旋转页面 rotation: 90/180/270"""
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
        """添加文字水印"""
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # 创建水印 PDF
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(page_width, page_height))
            c.setFont(CHINESE_FONT, fontsize)
            c.setFillColorRGB(color[0]/255, color[1]/255, color[2]/255, alpha=opacity)
            
            # 对角线重复水印
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
        """加密 PDF"""
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
        """解密 PDF"""
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
        """提取 PDF 文本"""
        reader = PdfReader(input_path)
        text_parts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            text_parts.append(f"=== 第 {i+1} 页 ===\n{text}\n")
        
        full_text = "\n".join(text_parts)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            return True, f"文本已保存到 → {output_path}"
        return True, full_text
    
    @staticmethod
    def compress_pdf(input_path, output_path, quality=0.5):
        """压缩 PDF（通过压缩内容流和对象流）"""
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        # 压缩对象流（兼容不同版本 PyPDF2）
        try:
            writer.compress_content_streams()
        except AttributeError:
            # 新版本使用 remove_links / 压缩 writer 本身
            pass
        
        # 设置压缩
        try:
            writer._compress_streams = True
        except:
            pass
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # 二次压缩：重写时启用 zlib 压缩
        import zlib
        with open(output_path, 'rb') as f:
            data = f.read()
        
        original_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        
        if new_size >= original_size:
            # 如果没变小，尝试用 obj 压缩重写
            writer2 = PdfWriter()
            for page in reader.pages:
                writer2.add_page(page)
            # 强制压缩所有流对象
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
                        except:
                            pass
            with open(output_path, 'wb') as f:
                writer2.write(f)
            new_size = os.path.getsize(output_path)
        
        ratio = (1 - new_size / original_size) * 100 if original_size > 0 else 0
        return True, f"压缩完成: {original_size/1024:.1f}KB → {new_size/1024:.1f}KB (减少 {ratio:.1f}%)"


class PDFEditorGUI:
    """PDF 编辑器图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 编辑工具 v1.0")
        self.root.geometry("750x600")
        self.root.minsize(700, 550)
        
        # 设置图标（如果有的话）
        try:
            self.root.iconname("PDF Editor")
        except:
            pass
        
        self.current_file = None
        self.file_list = []  # 用于合并功能的多文件列表
        
        self._setup_ui()
    
    def _setup_ui(self):
        """构建界面"""
        # 顶部标题栏
        header = tk.Frame(self.root, bg='#1a73e8', height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="📄 PDF 编辑工具", font=('Arial', 16, 'bold'),
                 fg='white', bg='#1a73e8').pack(pady=10)
        
        # 主内容区 - 使用 Notebook（选项卡）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 样式
        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('Arial', 10))
        
        # 创建各个功能页
        self._create_merge_tab()
        self._create_split_tab()
        self._create_extract_tab()
        self._create_delete_tab()
        self._create_rotate_tab()
        self._create_watermark_tab()
        self._create_security_tab()
        self._create_text_tab()
        self._create_compress_tab()
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W, fg='#555')
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    # ============ 通用方法 ============
    
    def _select_file(self, entry_var, filetypes=None):
        """通用文件选择"""
        if filetypes is None:
            filetypes = [("PDF 文件", "*.pdf"), ("所有文件", "*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            entry_var.set(path)
            self.current_file = path
            self.status_var.set(f"已选择: {os.path.basename(path)}")
    
    def _select_output(self, entry_var, default_ext='.pdf'):
        """通用输出文件选择"""
        path = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=[("PDF 文件", "*.pdf")] if default_ext == '.pdf' else [("文本文件", "*.txt")]
        )
        if path:
            entry_var.set(path)
    
    def _select_output_dir(self, entry_var):
        """选择输出目录"""
        path = filedialog.askdirectory()
        if path:
            entry_var.set(path)
    
    def _run_task(self, func, *args, success_msg="操作完成"):
        """在线程中执行任务，避免界面卡死"""
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
                self.status_var.set(f"❌ 错误: {str(e)}")
                messagebox.showerror("错误", f"操作失败:\n{str(e)}")
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    # ============ 1. 合并 PDF ============
    
    def _create_merge_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📎 合并")
        
        tk.Label(tab, text="选择要合并的 PDF 文件（可多选）:", font=('Arial', 10)).pack(pady=10)
        
        # 文件列表显示
        list_frame = tk.Frame(tab)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        self.merge_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=10)
        self.merge_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.merge_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.merge_listbox.config(yscrollcommand=scrollbar.set)
        
        # 按钮行
        btn_frame = tk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Button(btn_frame, text="添加文件", command=self._merge_add_files).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="移除选中", command=self._merge_remove).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="上移", command=self._merge_move_up).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="下移", command=self._merge_move_down).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="清空", command=self._merge_clear).pack(side=tk.LEFT, padx=5)
        
        # 输出
        out_frame = tk.Frame(tab)
        out_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(out_frame, text="输出文件:").pack(side=tk.LEFT)
        self.merge_output = tk.StringVar()
        tk.Entry(out_frame, textvariable=self.merge_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(out_frame, text="浏览", command=lambda: self._select_output(self.merge_output)).pack(side=tk.LEFT)
        
        # 执行按钮
        tk.Button(tab, text="▶ 开始合并", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_merge).pack(pady=15)
    
    def _merge_add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF 文件", "*.pdf")])
        for p in paths:
            self.file_list.append(p)
            self.merge_listbox.insert(tk.END, os.path.basename(p))
    
    def _merge_remove(self):
        sel = self.merge_listbox.curselection()
        for i in reversed(sel):
            self.merge_listbox.delete(i)
            self.file_list.pop(i)
    
    def _merge_move_up(self):
        sel = self.merge_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        for i in sel:
            if i > 0:
                self.file_list[i-1], self.file_list[i] = self.file_list[i], self.file_list[i-1]
                self.merge_listbox.delete(i)
                self.merge_listbox.insert(i-1, os.path.basename(self.file_list[i-1]))
                self.merge_listbox.selection_set(i-1)
    
    def _merge_move_down(self):
        sel = self.merge_listbox.curselection()
        if not sel or sel[-1] == len(self.file_list) - 1:
            return
        for i in reversed(sel):
            if i < len(self.file_list) - 1:
                self.file_list[i+1], self.file_list[i] = self.file_list[i], self.file_list[i+1]
                self.merge_listbox.delete(i)
                self.merge_listbox.insert(i+1, os.path.basename(self.file_list[i+1]))
                self.merge_listbox.selection_set(i+1)
    
    def _merge_clear(self):
        self.file_list.clear()
        self.merge_listbox.delete(0, tk.END)
    
    def _do_merge(self):
        if len(self.file_list) < 2:
            messagebox.showwarning("提示", "请至少添加 2 个 PDF 文件")
            return
        if not self.merge_output.get():
            messagebox.showwarning("提示", "请选择输出文件位置")
            return
        self._run_task(PDFEditor.merge_pdfs, self.file_list.copy(), self.merge_output.get())
    
    # ============ 2. 拆分 PDF ============
    
    def _create_split_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="✂️ 拆分")
        
        # 输入文件
        f1 = tk.Frame(tab)
        f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.split_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.split_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.split_input)).pack(side=tk.LEFT)
        
        # 输出目录
        f2 = tk.Frame(tab)
        f2.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(f2, text="输出目录:").pack(side=tk.LEFT)
        self.split_output_dir = tk.StringVar()
        tk.Entry(f2, textvariable=self.split_output_dir, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output_dir(self.split_output_dir)).pack(side=tk.LEFT)
        
        # 拆分模式
        mode_frame = tk.LabelFrame(tab, text="拆分模式", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.split_mode = tk.StringVar(value="all")
        tk.Radiobutton(mode_frame, text="每页拆分为单独文件", variable=self.split_mode,
                       value="all").pack(anchor=tk.W)
        
        range_frame = tk.Frame(mode_frame)
        range_frame.pack(fill=tk.X, anchor=tk.W)
        tk.Radiobutton(range_frame, text="按页码范围拆分:", variable=self.split_mode,
                       value="range").pack(side=tk.LEFT)
        tk.Label(range_frame, text=" (如: 1-3,4-6,7-10)").pack(side=tk.LEFT)
        
        self.split_ranges = tk.StringVar()
        split_entry = tk.Entry(mode_frame, textvariable=self.split_ranges, width=50)
        split_entry.insert(0, "输入格式示例: 1-3,4-6")
        split_entry.config(fg="grey")

        def on_split_entry_click(event):
            if split_entry.get() == "输入格式示例: 1-3,4-6":
                split_entry.delete(0, tk.END)
                split_entry.config(fg="black")

        def on_split_entry_focusout(event):
            if split_entry.get() == "":
                split_entry.insert(0, "输入格式示例: 1-3,4-6")
                split_entry.config(fg="grey")

        split_entry.bind("<FocusIn>", on_split_entry_click)
        split_entry.bind("<FocusOut>", on_split_entry_focusout)
        split_entry.pack(pady=5)
        
        # 执行
        tk.Button(tab, text="▶ 开始拆分", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_split).pack(pady=15)
    
    def _do_split(self):
        if not self.split_input.get():
            messagebox.showwarning("提示", "请选择输入文件")
            return
        if not self.split_output_dir.get():
            messagebox.showwarning("提示", "请选择输出目录")
            return
        
        mode = self.split_mode.get()
        if mode == 'all':
            self._run_task(PDFEditor.split_pdf, self.split_input.get(),
                          self.split_output_dir.get(), 'all')
        else:
            ranges_str = self.split_ranges.get().strip()
            if not ranges_str:
                messagebox.showwarning("提示", "请输入页码范围")
                return
            try:
                ranges = []
                for part in ranges_str.split(','):
                    s, e = part.split('-')
                    ranges.append((int(s.strip()), int(e.strip())))
            except:
                messagebox.showerror("错误", "页码范围格式错误，请使用如 1-3,4-6 的格式")
                return
            self._run_task(PDFEditor.split_pdf, self.split_input.get(),
                          self.split_output_dir.get(), 'range', ranges)
    
    # ============ 3. 提取页面 ============
    
    def _create_extract_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📑 提取")
        
        f1 = tk.Frame(tab)
        f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.extract_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.extract_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.extract_input)).pack(side=tk.LEFT)
        
        tk.Label(tab, text="要提取的页码（用逗号分隔，如: 1,3,5）:", font=('Arial', 10)).pack(pady=10)
        self.extract_pages_var = tk.StringVar()
        tk.Entry(tab, textvariable=self.extract_pages_var, width=50, font=('Arial', 11)).pack(pady=5)
        
        f2 = tk.Frame(tab)
        f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.extract_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.extract_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.extract_output)).pack(side=tk.LEFT)
        
        tk.Button(tab, text="▶ 开始提取", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_extract).pack(pady=15)
    
    def _do_extract(self):
        if not self.extract_input.get():
            messagebox.showwarning("提示", "请选择输入文件")
            return
        if not self.extract_pages_var.get().strip():
            messagebox.showwarning("提示", "请输入要提取的页码")
            return
        try:
            pages = [int(x.strip()) for x in self.extract_pages_var.get().split(',')]
        except:
            messagebox.showerror("错误", "页码格式错误，请用逗号分隔数字")
            return
        if not self.extract_output.get():
            messagebox.showwarning("提示", "请选择输出文件")
            return
        self._run_task(PDFEditor.extract_pages, self.extract_input.get(),
                      self.extract_output.get(), pages)
    
    # ============ 4. 删除页面 ============
    
    def _create_delete_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🗑️ 删除")
        
        f1 = tk.Frame(tab)
        f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.delete_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.delete_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.delete_input)).pack(side=tk.LEFT)
        
        tk.Label(tab, text="要删除的页码（用逗号分隔，如: 2,4,6）:", font=('Arial', 10)).pack(pady=10)
        self.delete_pages_var = tk.StringVar()
        tk.Entry(tab, textvariable=self.delete_pages_var, width=50, font=('Arial', 11)).pack(pady=5)
        
        f2 = tk.Frame(tab)
        f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.delete_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.delete_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.delete_output)).pack(side=tk.LEFT)
        
        tk.Button(tab, text="▶ 开始删除", font=('Arial', 12, 'bold'),
                  bg='#e84040', fg='white', padx=30, pady=5,
                  command=self._do_delete).pack(pady=15)
    
    def _do_delete(self):
        if not self.delete_input.get():
            messagebox.showwarning("提示", "请选择输入文件")
            return
        if not self.delete_pages_var.get().strip():
            messagebox.showwarning("提示", "请输入要删除的页码")
            return
        try:
            pages = [int(x.strip()) for x in self.delete_pages_var.get().split(',')]
        except:
            messagebox.showerror("错误", "页码格式错误")
            return
        if not self.delete_output.get():
            messagebox.showwarning("提示", "请选择输出文件")
            return
        self._run_task(PDFEditor.delete_pages, self.delete_input.get(),
                      self.delete_output.get(), pages)
    
    # ============ 5. 旋转页面 ============
    
    def _create_rotate_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔄 旋转")
        
        f1 = tk.Frame(tab)
        f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.rotate_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.rotate_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.rotate_input)).pack(side=tk.LEFT)
        
        # 旋转角度
        angle_frame = tk.LabelFrame(tab, text="旋转角度", padx=10, pady=10)
        angle_frame.pack(fill=tk.X, padx=20, pady=10)
        self.rotate_angle = tk.StringVar(value="90")
        tk.Radiobutton(angle_frame, text="90°", variable=self.rotate_angle, value="90").pack(side=tk.LEFT, padx=20)
        tk.Radiobutton(angle_frame, text="180°", variable=self.rotate_angle, value="180").pack(side=tk.LEFT, padx=20)
        tk.Radiobutton(angle_frame, text="270°", variable=self.rotate_angle, value="270").pack(side=tk.LEFT, padx=20)
        
        # 旋转范围
        range_frame = tk.LabelFrame(tab, text="旋转范围", padx=10, pady=10)
        range_frame.pack(fill=tk.X, padx=20, pady=10)
        self.rotate_all = tk.BooleanVar(value=True)
        tk.Radiobutton(range_frame, text="所有页面", variable=self.rotate_all, value=True).pack(anchor=tk.W)
        tk.Radiobutton(range_frame, text="指定页面（逗号分隔，如: 1,3,5）:", variable=self.rotate_all, value=False).pack(anchor=tk.W)
        self.rotate_pages_var = tk.StringVar()
        tk.Entry(range_frame, textvariable=self.rotate_pages_var, width=40).pack(pady=5)
        
        f2 = tk.Frame(tab)
        f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.rotate_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.rotate_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.rotate_output)).pack(side=tk.LEFT)
        
        tk.Button(tab, text="▶ 开始旋转", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_rotate).pack(pady=15)
    
    def _do_rotate(self):
        if not self.rotate_input.get():
            messagebox.showwarning("提示", "请选择输入文件")
            return
        angle = int(self.rotate_angle.get())
        
        pages = None
        if not self.rotate_all.get():
            try:
                pages = [int(x.strip()) for x in self.rotate_pages_var.get().split(',')]
            except:
                messagebox.showerror("错误", "页码格式错误")
                return
        
        if not self.rotate_output.get():
            messagebox.showwarning("提示", "请选择输出文件")
            return
        
        self._run_task(PDFEditor.rotate_pages, self.rotate_input.get(),
                      self.rotate_output.get(), angle, pages)
    
    # ============ 6. 添加水印 ============
    
    def _create_watermark_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="💧 水印")
        
        f1 = tk.Frame(tab)
        f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.wm_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.wm_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.wm_input)).pack(side=tk.LEFT)
        
        # 水印文字
        tk.Label(tab, text="水印文字:", font=('Arial', 10)).pack(pady=(15,5))
        self.wm_text = tk.StringVar(value="CONFIDENTIAL")
        tk.Entry(tab, textvariable=self.wm_text, width=50, font=('Arial', 12)).pack(pady=5)
        
        # 参数设置
        param_frame = tk.Frame(tab)
        param_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(param_frame, text="字号:").grid(row=0, column=0, padx=5, sticky='w')
        self.wm_fontsize = tk.IntVar(value=50)
        tk.Spinbox(param_frame, from_=10, to=200, textvariable=self.wm_fontsize, width=8).grid(row=0, column=1, padx=5)
        
        tk.Label(param_frame, text="透明度(0-1):").grid(row=0, column=2, padx=15, sticky='w')
        self.wm_opacity = tk.DoubleVar(value=0.3)
        tk.Spinbox(param_frame, from_=0.1, to=1.0, increment=0.1, textvariable=self.wm_opacity, width=8).grid(row=0, column=3, padx=5)
        
        # 颜色选择
        tk.Label(param_frame, text="颜色:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.wm_color = tk.StringVar(value="gray")
        color_frame = tk.Frame(param_frame)
        color_frame.grid(row=1, column=1, columnspan=3, padx=5, sticky='w')
        for c in ['gray', 'red', 'blue', 'green', 'black']:
            tk.Radiobutton(color_frame, text=c, variable=self.wm_color, value=c).pack(side=tk.LEFT, padx=5)
        
        f2 = tk.Frame(tab)
        f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.wm_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.wm_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.wm_output)).pack(side=tk.LEFT)
        
        tk.Button(tab, text="▶ 添加水印", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_watermark).pack(pady=15)
    
    def _do_watermark(self):
        if not self.wm_input.get():
            messagebox.showwarning("提示", "请选择输入文件")
            return
        if not self.wm_text.get().strip():
            messagebox.showwarning("提示", "请输入水印文字")
            return
        
        color_map = {
            'gray': (128, 128, 128),
            'red': (255, 0, 0),
            'blue': (0, 0, 255),
            'green': (0, 128, 0),
            'black': (0, 0, 0)
        }
        color = color_map.get(self.wm_color.get(), (128, 128, 128))
        
        if not self.wm_output.get():
            messagebox.showwarning("提示", "请选择输出文件")
            return
        
        self._run_task(PDFEditor.add_watermark, self.wm_input.get(),
                      self.wm_output.get(), self.wm_text.get(),
                      self.wm_opacity.get(), self.wm_fontsize.get(), color)
    
    # ============ 7. 加密/解密 ============
    
    def _create_security_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔒 安全")
        
        # 加密区域
        enc_frame = tk.LabelFrame(tab, text="🔐 加密 PDF", padx=10, pady=10)
        enc_frame.pack(fill=tk.X, padx=20, pady=10)
        
        f1 = tk.Frame(enc_frame)
        f1.pack(fill=tk.X, pady=3)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.enc_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.enc_input, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.enc_input)).pack(side=tk.LEFT)
        
        f2 = tk.Frame(enc_frame)
        f2.pack(fill=tk.X, pady=3)
        tk.Label(f2, text="密码:").pack(side=tk.LEFT)
        self.enc_password = tk.StringVar()
        tk.Entry(f2, textvariable=self.enc_password, width=20, show='*').pack(side=tk.LEFT, padx=5)
        
        f3 = tk.Frame(enc_frame)
        f3.pack(fill=tk.X, pady=3)
        tk.Label(f3, text="输出文件:").pack(side=tk.LEFT)
        self.enc_output = tk.StringVar()
        tk.Entry(f3, textvariable=self.enc_output, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(f3, text="浏览", command=lambda: self._select_output(self.enc_output)).pack(side=tk.LEFT)
        
        tk.Button(enc_frame, text="▶ 加密", bg='#e8a01a', fg='white',
                  font=('Arial', 10, 'bold'), command=self._do_encrypt).pack(pady=5)
        
        # 解密区域
        dec_frame = tk.LabelFrame(tab, text="🔓 解密 PDF", padx=10, pady=10)
        dec_frame.pack(fill=tk.X, padx=20, pady=10)
        
        f4 = tk.Frame(dec_frame)
        f4.pack(fill=tk.X, pady=3)
        tk.Label(f4, text="输入文件:").pack(side=tk.LEFT)
        self.dec_input = tk.StringVar()
        tk.Entry(f4, textvariable=self.dec_input, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(f4, text="浏览", command=lambda: self._select_file(self.dec_input)).pack(side=tk.LEFT)
        
        f5 = tk.Frame(dec_frame)
        f5.pack(fill=tk.X, pady=3)
        tk.Label(f5, text="密码:").pack(side=tk.LEFT)
        self.dec_password = tk.StringVar()
        tk.Entry(f5, textvariable=self.dec_password, width=20, show='*').pack(side=tk.LEFT, padx=5)
        
        f6 = tk.Frame(dec_frame)
        f6.pack(fill=tk.X, pady=3)
        tk.Label(f6, text="输出文件:").pack(side=tk.LEFT)
        self.dec_output = tk.StringVar()
        tk.Entry(f6, textvariable=self.dec_output, width=35).pack(side=tk.LEFT, padx=5)
        tk.Button(f6, text="浏览", command=lambda: self._select_output(self.dec_output)).pack(side=tk.LEFT)
        
        tk.Button(dec_frame, text="▶ 解密", bg='#1a73e8', fg='white',
                  font=('Arial', 10, 'bold'), command=self._do_decrypt).pack(pady=5)
    
    def _do_encrypt(self):
        if not self.enc_input.get() or not self.enc_password.get():
            messagebox.showwarning("提示", "请选择文件并输入密码")
            return
        if not self.enc_output.get():
            messagebox.showwarning("提示", "请选择输出文件")
            return
        self._run_task(PDFEditor.encrypt_pdf, self.enc_input.get(),
                      self.enc_output.get(), self.enc_password.get())
    
    def _do_decrypt(self):
        if not self.dec_input.get() or not self.dec_password.get():
            messagebox.showwarning("提示", "请选择文件并输入密码")
            return
        if not self.dec_output.get():
            messagebox.showwarning("提示", "请选择输出文件")
            return
        self._run_task(PDFEditor.decrypt_pdf, self.dec_input.get(),
                      self.dec_output.get(), self.dec_password.get())
    
    # ============ 8. 提取文本 ============
    
    def _create_text_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📝 提取文本")
        
        f1 = tk.Frame(tab)
        f1.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.text_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.text_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.text_input)).pack(side=tk.LEFT)
        
        # 文本显示区域
        tk.Label(tab, text="提取的文本内容:", font=('Arial', 10)).pack(pady=(15,5))
        self.text_display = scrolledtext.ScrolledText(tab, height=12, wrap=tk.WORD, font=('Arial', 10))
        self.text_display.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # 按钮行
        btn_frame = tk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(btn_frame, text="▶ 提取文本", bg='#1a73e8', fg='white',
                  font=('Arial', 10, 'bold'), command=self._do_extract_text).pack(side=tk.LEFT, padx=5)
        
        self.text_output_path = tk.StringVar()
        tk.Label(btn_frame, text="保存为:").pack(side=tk.LEFT, padx=(20,5))
        tk.Entry(btn_frame, textvariable=self.text_output_path, width=25).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="浏览", command=lambda: self._select_output(self.text_output_path, '.txt')).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="保存", command=self._save_text).pack(side=tk.LEFT, padx=5)
    
    def _do_extract_text(self):
        if not self.text_input.get():
            messagebox.showwarning("提示", "请选择输入文件")
            return
        
        def worker():
            try:
                self.status_var.set("正在提取文本...")
                self.root.update()
                success, result = PDFEditor.extract_text(self.text_input.get())
                if success:
                    self.text_display.delete(1.0, tk.END)
                    self.text_display.insert(1.0, result)
                    self.status_var.set("✅ 文本提取完成")
                else:
                    self.status_var.set(f"❌ {result}")
                    messagebox.showerror("错误", result)
            except Exception as e:
                self.status_var.set(f"❌ 错误: {str(e)}")
                messagebox.showerror("错误", str(e))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _save_text(self):
        text = self.text_display.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "没有文本内容可保存")
            return
        if not self.text_output_path.get():
            messagebox.showwarning("提示", "请选择保存路径")
            return
        with open(self.text_output_path.get(), 'w', encoding='utf-8') as f:
            f.write(text)
        messagebox.showinfo("成功", f"文本已保存到 {self.text_output_path.get()}")
    
    # ============ 9. 压缩 PDF ============
    
    def _create_compress_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🗜️ 压缩")
        
        f1 = tk.Frame(tab)
        f1.pack(fill=tk.X, padx=20, pady=15)
        tk.Label(f1, text="输入文件:").pack(side=tk.LEFT)
        self.compress_input = tk.StringVar()
        tk.Entry(f1, textvariable=self.compress_input, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="浏览", command=lambda: self._select_file(self.compress_input)).pack(side=tk.LEFT)
        
        # 文件信息显示
        self.compress_info = tk.StringVar(value="等待选择文件...")
        tk.Label(tab, textvariable=self.compress_info, font=('Arial', 10), fg='#555').pack(pady=10)
        
        f2 = tk.Frame(tab)
        f2.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(f2, text="输出文件:").pack(side=tk.LEFT)
        self.compress_output = tk.StringVar()
        tk.Entry(f2, textvariable=self.compress_output, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="浏览", command=lambda: self._select_output(self.compress_output)).pack(side=tk.LEFT)
        
        tk.Button(tab, text="▶ 开始压缩", font=('Arial', 12, 'bold'),
                  bg='#1a73e8', fg='white', padx=30, pady=5,
                  command=self._do_compress).pack(pady=15)
        
        # 说明
        info = tk.Label(tab, text="💡 压缩通过优化 PDF 内部结构实现，可能减小文件体积",
                        font=('Arial', 9), fg='#888')
        info.pack(pady=20)
    
    def _do_compress(self):
        if not self.compress_input.get():
            messagebox.showwarning("提示", "请选择输入文件")
            return
        if not self.compress_output.get():
            messagebox.showwarning("提示", "请选择输出文件")
            return
        
        input_path = self.compress_input.get()
        size = os.path.getsize(input_path)
        self.compress_info.set(f"原始文件大小: {size/1024:.1f} KB")
        
        self._run_task(PDFEditor.compress_pdf, input_path, self.compress_output.get())


def main():
    """程序入口"""
    root = tk.Tk()
    
    # 居中窗口
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")
    
    app = PDFEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
