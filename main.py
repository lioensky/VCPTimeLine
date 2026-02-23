import tkinter as tk
from tkinter import ttk, messagebox
import threading
import asyncio
import datetime
import traceback

import config
import parser
import summarizer
import timeline

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("时间线生成器 (Timeline Generator)")
        self.geometry("600x450")
        
        # UI Elements
        self.create_widgets()
        
    def create_widgets(self):
        # Frame
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Character Name
        ttk.Label(frame, text="角色名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.char_var = tk.StringVar(value="小克")
        self.char_entry = ttk.Entry(frame, textvariable=self.char_var, width=30)
        self.char_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Start YM
        ttk.Label(frame, text="起始年月 (YYYY-MM):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_var = tk.StringVar(value="2024-01")
        self.start_entry = ttk.Entry(frame, textvariable=self.start_var, width=30)
        self.start_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # End YM
        current_ym = datetime.datetime.now().strftime("%Y-%m")
        ttk.Label(frame, text="结束年月 (YYYY-MM):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.end_var = tk.StringVar(value=current_ym)
        self.end_entry = ttk.Entry(frame, textvariable=self.end_var, width=30)
        self.end_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Start Button
        self.start_btn = ttk.Button(frame, text="开始生成 (Start)", command=self.on_start)
        self.start_btn.grid(row=3, column=0, columnspan=2, pady=15)
        
        # Log Box
        self.log_text = tk.Text(frame, height=15, width=70, state=tk.DISABLED)
        self.log_text.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, command=self.log_text.yview)
        scrollbar.grid(row=4, column=2, sticky=(tk.N, tk.S))
        self.log_text['yscrollcommand'] = scrollbar.set
        
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(4, weight=1)

    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_idletasks()

    def generate_months(self, start_ym, end_ym):
        # Generate list of YYYY-MM strings
        start_y, start_m = map(int, start_ym.split("-"))
        end_y, end_m = map(int, end_ym.split("-"))
        
        months = []
        y, m = start_y, start_m
        while y < end_y or (y == end_y and m <= end_m):
            months.append(f"{y:04d}-{m:02d}")
            m += 1
            if m > 12:
                m = 1
                y += 1
        return months

    def on_start(self):
        char_name = self.char_var.get().strip()
        start_ym = self.start_var.get().strip()
        end_ym = self.end_var.get().strip()
        
        if not char_name or not start_ym or not end_ym:
            messagebox.showerror("错误", "请填写完整所有字段！")
            return
            
        try:
            datetime.datetime.strptime(start_ym, "%Y-%m")
            datetime.datetime.strptime(end_ym, "%Y-%m")
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确，应为 YYYY-MM")
            return
            
        if start_ym > end_ym:
            messagebox.showerror("错误", "起始年月不能大于结束年月！")
            return
            
        # Validate config
        is_valid, msg = config.validate_config()
        if not is_valid:
            messagebox.showerror("配置错误 (Config Error)", f"环境变量配置检查失败：\n{msg}")
            return
            
        self.start_btn.config(state=tk.DISABLED)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Start background thread
        threading.Thread(target=self.run_process, args=(char_name, start_ym, end_ym), daemon=True).start()
        
    def run_process(self, char_name, start_ym, end_ym):
        try:
            self.log(f"开始任务: 角色={char_name}, 范围={start_ym} 到 {end_ym}")
            
            # 1. 检查已有的总结
            self.log("检查已有时间线文件...")
            existing = timeline.get_summarized_months(char_name, start_ym, end_ym)
            if existing:
                self.log(f"发现已有的月份: {', '.join(sorted(existing))}")
                
            # 2. 读取记忆库
            self.log("正在扫描记忆库，请稍候...")
            memories_by_month = parser.discover_memories(char_name, start_ym, end_ym)
            self.log(f"扫描完成，找到了跨越 {len(memories_by_month)} 个月的碎片。")
            
            # 3. 按月处理
            month_list = self.generate_months(start_ym, end_ym)
            
            # Setup an event loop for this thread to run async logic
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for ym in month_list:
                if ym in existing:
                    self.log(f"[{ym}] 跳过，已存在总结。")
                    continue
                    
                month_memories = memories_by_month.get(ym, [])
                if not month_memories:
                    self.log(f"[{ym}] 跳过，该月无任何记忆。")
                    continue
                    
                self.log(f"[{ym}] 开始总结，共 {len(month_memories)} 条记忆碎片...")
                
                # Callback to update log from async function
                def update_cb(msg):
                    # use after to update GUI from thread safely
                    self.after(0, self.log, f"      -> {msg}")
                
                try:
                    summary = loop.run_until_complete(
                        summarizer.process_month(month_memories, char_name, update_status_cb=update_cb)
                    )
                    
                    timeline.save_month_summary(char_name, ym, summary)
                    self.log(f"[{ym}] 汇总完成，并保存到文件。")
                    
                except Exception as e:
                    self.log(f"[{ym}] 处理时发生错误: {str(e)}")
                    print(traceback.format_exc())
            
            loop.close()
            self.log("\n====== 全部处理完成！======")
            
        except Exception as e:
            self.log(f"\n执行过程中发生异常: {e}")
            print(traceback.format_exc())
            
        finally:
            self.after(0, lambda: self.start_btn.config(state=tk.NORMAL))


if __name__ == "__main__":
    app = Application()
    app.mainloop()
