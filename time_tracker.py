#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматизация и учёта рабочего времени - СОВРЕМЕННЫЙ HUD ДИЗАЙН
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name='time_tracker.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.insert_test_data()
    
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT,
                department TEXT,
                phone TEXT,
                email TEXT,
                hire_date TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                clock_in TEXT NOT NULL,
                clock_out TEXT,
                hours REAL DEFAULT 0,
                date TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    def insert_test_data(self):
        self.cursor.execute("SELECT COUNT(*) FROM employees")
        if self.cursor.fetchone()[0] == 0:
            test_employees = [
                ("Иванов Иван Петрович", "Разработчик", "IT", "+7 (999) 123-45-67", "ivanov@mail.ru", "2023-01-15"),
                ("Петрова Анна Сергеевна", "Менеджер", "Управление", "+7 (999) 234-56-78", "petrova@mail.ru", "2023-02-20"),
                ("Сидоров Алексей Владимирович", "Тестировщик", "QA", "+7 (999) 345-67-89", "sidorov@mail.ru", "2023-03-10"),
                ("Козлова Елена Дмитриевна", "Дизайнер", "Дизайн", "+7 (999) 456-78-90", "kozlova@mail.ru", "2023-04-05"),
            ]
            for emp in test_employees:
                self.cursor.execute(
                    "INSERT INTO employees (name, position, department, phone, email, hire_date) VALUES (?, ?, ?, ?, ?, ?)",
                    emp
                )
            self.conn.commit()
    
    def get_employees(self):
        self.cursor.execute("SELECT id, name, position, department FROM employees ORDER BY name")
        return self.cursor.fetchall()
    
    def get_employee_by_id(self, emp_id):
        self.cursor.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
        return self.cursor.fetchone()
    
    def add_employee(self, name, position, department, phone, email, hire_date):
        try:
            self.cursor.execute(
                "INSERT INTO employees (name, position, department, phone, email, hire_date) VALUES (?, ?, ?, ?, ?, ?)",
                (name, position, department, phone, email, hire_date)
            )
            self.conn.commit()
            return True
        except:
            return False
    
    def update_employee(self, emp_id, name, position, department, phone, email, hire_date):
        try:
            self.cursor.execute(
                "UPDATE employees SET name=?, position=?, department=?, phone=?, email=?, hire_date=? WHERE id=?",
                (name, position, department, phone, email, hire_date, emp_id)
            )
            self.conn.commit()
            return True
        except:
            return False
    
    def delete_employee(self, emp_id):
        try:
            self.cursor.execute("DELETE FROM time_records WHERE employee_id=?", (emp_id,))
            self.cursor.execute("DELETE FROM employees WHERE id=?", (emp_id,))
            self.conn.commit()
            return True
        except:
            return False
    
    def is_working_now(self, employee_id):
        today = datetime.now().date().isoformat()
        self.cursor.execute(
            "SELECT id FROM time_records WHERE employee_id=? AND date=? AND clock_out IS NULL",
            (employee_id, today)
        )
        return self.cursor.fetchone() is not None
    
    def clock_in(self, employee_id):
        now = datetime.now()
        now_str = now.isoformat()
        date_str = now.date().isoformat()
        
        if self.is_working_now(employee_id):
            return False, "Сотрудник уже на работе!"
        
        self.cursor.execute(
            "INSERT INTO time_records (employee_id, clock_in, date) VALUES (?, ?, ?)",
            (employee_id, now_str, date_str)
        )
        self.conn.commit()
        return True, f"✓ Приход отмечен в {now.strftime('%H:%M:%S')}"
    
    def clock_out(self, employee_id):
        now = datetime.now()
        now_str = now.isoformat()
        date_str = now.date().isoformat()
        
        self.cursor.execute(
            "SELECT id, clock_in FROM time_records WHERE employee_id=? AND date=? AND clock_out IS NULL",
            (employee_id, date_str)
        )
        record = self.cursor.fetchone()
        
        if not record:
            return False, "Нет отметки о приходе!"
        
        record_id, clock_in_str = record
        clock_in_time = datetime.fromisoformat(clock_in_str)
        hours = (now - clock_in_time).total_seconds() / 3600
        
        self.cursor.execute(
            "UPDATE time_records SET clock_out=?, hours=? WHERE id=?",
            (now_str, round(hours, 2), record_id)
        )
        self.conn.commit()
        return True, f"✓ Уход отмечен. Отработано: {round(hours, 2)} ч."
    
    def get_today_records(self):
        today = datetime.now().date().isoformat()
        self.cursor.execute('''
            SELECT e.name, e.position, 
                   substr(t.clock_in, 11, 5) as clock_in_time,
                   CASE WHEN t.clock_out IS NOT NULL THEN substr(t.clock_out, 11, 5) ELSE '--:--' END,
                   CASE WHEN t.hours > 0 THEN t.hours ELSE 0 END
            FROM time_records t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.date = ?
            ORDER BY t.clock_in DESC
        ''', (today,))
        return self.cursor.fetchall()
    
    def get_today_working(self):
        today = datetime.now().date().isoformat()
        self.cursor.execute('''
            SELECT e.name, e.position, substr(t.clock_in, 11, 5)
            FROM time_records t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.date=? AND t.clock_out IS NULL
        ''', (today,))
        return self.cursor.fetchall()
    
    def get_history(self, start_date, end_date):
        self.cursor.execute('''
            SELECT e.name, e.position, t.date,
                   substr(t.clock_in, 11, 5),
                   substr(t.clock_out, 11, 5),
                   t.hours
            FROM time_records t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.date BETWEEN ? AND ? AND t.clock_out IS NOT NULL
            ORDER BY t.date DESC
        ''', (start_date, end_date))
        return self.cursor.fetchall()
    
    def get_statistics(self, period='month'):
        today = datetime.now().date()
        today_str = today.isoformat()
        
        if period == 'week':
            start_date = today - timedelta(days=7)
            period_name = "за неделю"
        else:
            start_date = today - timedelta(days=30)
            period_name = "за месяц"
        
        start_date_str = start_date.isoformat()
        
        self.cursor.execute('''
            SELECT e.name, e.position,
                   ROUND(SUM(t.hours), 1) as total_hours,
                   COUNT(t.id) as days_worked,
                   ROUND(AVG(t.hours), 1) as avg_hours
            FROM time_records t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.date BETWEEN ? AND ? AND t.clock_out IS NOT NULL
            GROUP BY e.id
            ORDER BY total_hours DESC
        ''', (start_date_str, today_str))
        
        return self.cursor.fetchall(), start_date, today, period_name
    
    def close(self):
        self.conn.close()


class ModernButton(tk.Canvas):
    """Современная кнопка с эффектами"""
    def __init__(self, parent, text, command, color="#3498db", hover_color="#5dade2", **kwargs):
        self.command = command
        self.color = color
        self.hover_color = hover_color
        self.default_bg = parent.cget("bg")
        
        super().__init__(parent, height=40, highlightthickness=0, **kwargs)
        self.create_rounded_rect(0, 0, 150, 40, 10, fill=color, outline="", tags="rect")
        self.create_text(75, 20, text=text, fill="white", font=("Segoe UI", 10, "bold"), tags="text")
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = []
        for x, y in [(x1+radius, y1), (x2-radius, y1), (x2, y1), (x2, y1+radius),
                     (x2, y2-radius), (x2, y2), (x2-radius, y2), (x1+radius, y2),
                     (x1, y2), (x1, y2-radius), (x1, y1+radius), (x1, y1)]:
            points.extend([x, y])
        return self.create_polygon(points, **kwargs, smooth=True)
    
    def on_enter(self, e):
        self.delete("rect")
        self.create_rounded_rect(0, 0, 150, 40, 10, fill=self.hover_color, outline="", tags="rect")
        self.tag_lower("rect", "text")
    
    def on_leave(self, e):
        self.delete("rect")
        self.create_rounded_rect(0, 0, 150, 40, 10, fill=self.color, outline="", tags="rect")
        self.tag_lower("rect", "text")
    
    def on_click(self, e):
        if self.command:
            self.command()


class TimeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TimeTracker Pro - Учёт рабочего времени")
        self.root.geometry("1300x800")
        self.root.configure(bg='#0f0f1a')
        
        # Настройка стилей
        self.setup_styles()
        
        self.db = Database()
        self.current_employee = None
        
        self.create_widgets()
        self.update_clock()
        self.refresh_all()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Стиль для вкладок
        style.configure("TNotebook", background='#0f0f1a', borderwidth=0)
        style.configure("TNotebook.Tab", background='#1a1a2e', foreground='#a0a0b0',
                       padding=[20, 10], font=('Segoe UI', 10, 'bold'))
        style.map("TNotebook.Tab", background=[('selected', '#16213e'), ('active', '#1e2a4a')],
                 foreground=[('selected', '#00d2ff'), ('active', '#00d2ff')])
        
        # Стиль для фреймов
        style.configure("Card.TFrame", background='#1a1a2e', relief='flat', borderwidth=0)
        style.configure("Title.TLabel", background='#1a1a2e', foreground='#00d2ff', 
                       font=('Segoe UI', 12, 'bold'))
    
    def create_widgets(self):
        # Верхняя панель HUD
        self.create_hud_panel()
        
        # Вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Создание вкладок
        self.today_tab = tk.Frame(self.notebook, bg='#0f0f1a')
        self.history_tab = tk.Frame(self.notebook, bg='#0f0f1a')
        self.employees_tab = tk.Frame(self.notebook, bg='#0f0f1a')
        self.stats_tab = tk.Frame(self.notebook, bg='#0f0f1a')
        
        self.notebook.add(self.today_tab, text="  📅 ТЕКУЩИЙ ДЕНЬ  ")
        self.notebook.add(self.history_tab, text="  📊 ИСТОРИЯ  ")
        self.notebook.add(self.employees_tab, text="  👥 СОТРУДНИКИ  ")
        self.notebook.add(self.stats_tab, text="  📈 СТАТИСТИКА  ")
        
        # Заполнение вкладок
        self.create_today_tab()
        self.create_history_tab()
        self.create_employees_tab()
        self.create_stats_tab()
    
    def create_hud_panel(self):
        """Создание современной HUD панели"""
        hud_frame = tk.Frame(self.root, bg='#1a1a2e', height=120)
        hud_frame.pack(fill=tk.X, padx=0, pady=0)
        hud_frame.pack_propagate(False)
        
        # Градиентная полоса сверху
        gradient_bar = tk.Frame(hud_frame, bg='#00d2ff', height=3)
        gradient_bar.pack(fill=tk.X)
        
        # Основной контент
        content = tk.Frame(hud_frame, bg='#1a1a2e')
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)
        
        # Левая секция - Логотип и время
        left_section = tk.Frame(content, bg='#1a1a2e')
        left_section.pack(side=tk.LEFT, fill=tk.Y)
        
        logo_label = tk.Label(left_section, text="⚡ TIMETRACKER PRO", 
                             font=('Segoe UI', 16, 'bold'), bg='#1a1a2e', fg='#00d2ff')
        logo_label.pack(anchor='w')
        
        self.clock_label = tk.Label(left_section, font=('Segoe UI', 11), 
                                   bg='#1a1a2e', fg='#a0a0b0')
        self.clock_label.pack(anchor='w', pady=(5, 0))
        
        # Центральная секция - Информация о сотруднике
        center_section = tk.Frame(content, bg='#1a1a2e')
        center_section.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=30)
        
        # Карточка сотрудника
        employee_card = tk.Frame(center_section, bg='#16213e', relief=tk.RAISED, bd=0)
        employee_card.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем рамку
        tk.Frame(employee_card, bg='#00d2ff', height=2).pack(fill=tk.X)
        
        emp_content = tk.Frame(employee_card, bg='#16213e')
        emp_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        self.emp_name_label = tk.Label(emp_content, text="НЕ ВЫБРАН", 
                                      font=('Segoe UI', 13, 'bold'), bg='#16213e', fg='#ffffff')
        self.emp_name_label.pack(anchor='w')
        
        self.emp_status_label = tk.Label(emp_content, text="", 
                                        font=('Segoe UI', 10), bg='#16213e')
        self.emp_status_label.pack(anchor='w', pady=(5, 0))
        
        # Правая секция - Кнопки
        right_section = tk.Frame(content, bg='#1a1a2e')
        right_section.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кастомные кнопки
        self.create_modern_button(right_section, "👤 ВЫБРАТЬ", self.select_employee, '#3498db', '#5dade2')
        self.create_modern_button(right_section, "✅ ПРИШЁЛ", self.clock_in, '#27ae60', '#2ecc71', state='disabled')
        self.create_modern_button(right_section, "❌ УШЁЛ", self.clock_out, '#e74c3c', '#ec7063', state='disabled')
    
    def create_modern_button(self, parent, text, command, color, hover_color, state='normal'):
        """Создание современной кнопки"""
        btn_frame = tk.Frame(parent, bg='#1a1a2e')
        btn_frame.pack(side=tk.LEFT, padx=5)
        
        btn = tk.Button(btn_frame, text=text, command=command,
                       bg=color, fg='white', font=('Segoe UI', 10, 'bold'),
                       padx=25, pady=8, bd=0, cursor='hand2',
                       activebackground=hover_color, activeforeground='white')
        
        if state == 'disabled':
            btn.config(state='disabled', bg='#555555')
        
        btn.pack()
        
        # Сохраняем ссылку для обновления состояния
        if "ПРИШЁЛ" in text:
            self.clock_in_btn = btn
        elif "УШЁЛ" in text:
            self.clock_out_btn = btn
        
        return btn
    
    def create_today_tab(self):
        # Статистическая карточка
        stats_card = tk.Frame(self.today_tab, bg='#1a1a2e')
        stats_card.pack(fill=tk.X, padx=20, pady=15)
        
        # Карточка "Сейчас на работе"
        working_card = tk.Frame(stats_card, bg='#1a1a2e', relief=tk.RAISED, bd=0)
        working_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Frame(working_card, bg='#2ecc71', height=2).pack(fill=tk.X)
        
        working_title = tk.Label(working_card, text="🟢 СЕЙЧАС НА РАБОТЕ", 
                                font=('Segoe UI', 11, 'bold'), bg='#1a1a2e', fg='#2ecc71')
        working_title.pack(pady=(15, 10), padx=15, anchor='w')
        
        self.working_listbox = tk.Listbox(working_card, font=('Segoe UI', 10), 
                                         bg='#16213e', fg='#e0e0e0', 
                                         selectbackground='#00d2ff', height=5,
                                         bd=0, highlightthickness=0)
        self.working_listbox.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Карточка "Сегодняшние записи"
        records_card = tk.Frame(self.today_tab, bg='#1a1a2e', relief=tk.RAISED, bd=0)
        records_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        tk.Frame(records_card, bg='#3498db', height=2).pack(fill=tk.X)
        
        records_title = tk.Label(records_card, text="📝 СЕГОДНЯШНИЕ ЗАПИСИ", 
                                font=('Segoe UI', 11, 'bold'), bg='#1a1a2e', fg='#3498db')
        records_title.pack(pady=(15, 10), padx=15, anchor='w')
        
        # Текстовое поле с прокруткой
        text_frame = tk.Frame(records_card, bg='#1a1a2e')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.today_text = tk.Text(text_frame, font=('Segoe UI', 10), 
                                  bg='#16213e', fg='#e0e0e0',
                                  bd=0, highlightthickness=0, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, command=self.today_text.yview)
        self.today_text.configure(yscrollcommand=scrollbar.set)
        
        self.today_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_history_tab(self):
        # Панель фильтров
        filter_card = tk.Frame(self.history_tab, bg='#1a1a2e', relief=tk.RAISED, bd=0)
        filter_card.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Frame(filter_card, bg='#9b59b6', height=2).pack(fill=tk.X)
        
        filter_content = tk.Frame(filter_card, bg='#1a1a2e')
        filter_content.pack(pady=20, padx=20)
        
        tk.Label(filter_content, text="С даты:", bg='#1a1a2e', fg='#a0a0b0', 
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        self.start_date = tk.Entry(filter_content, width=12, font=('Segoe UI', 10),
                                  bg='#16213e', fg='#e0e0e0', bd=0, insertbackground='white')
        self.start_date.pack(side=tk.LEFT, padx=5)
        self.start_date.insert(0, (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        
        tk.Label(filter_content, text="По дату:", bg='#1a1a2e', fg='#a0a0b0',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        self.end_date = tk.Entry(filter_content, width=12, font=('Segoe UI', 10),
                                bg='#16213e', fg='#e0e0e0', bd=0, insertbackground='white')
        self.end_date.pack(side=tk.LEFT, padx=5)
        self.end_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        show_btn = tk.Button(filter_content, text="ПОКАЗАТЬ", command=self.show_history,
                            bg='#9b59b6', fg='white', font=('Segoe UI', 10, 'bold'),
                            padx=20, pady=5, bd=0, cursor='hand2',
                            activebackground='#af7ac5')
        show_btn.pack(side=tk.LEFT, padx=20)
        
        # Текстовое поле для истории
        history_card = tk.Frame(self.history_tab, bg='#1a1a2e', relief=tk.RAISED, bd=0)
        history_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.history_text = tk.Text(history_card, font=('Segoe UI', 10), wrap=tk.WORD,
                                   bg='#16213e', fg='#e0e0e0', bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(history_card, command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 15), pady=15)
    
    def create_employees_tab(self):
        # Кнопки управления
        btn_card = tk.Frame(self.employees_tab, bg='#1a1a2e', relief=tk.RAISED, bd=0)
        btn_card.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Frame(btn_card, bg='#e67e22', height=2).pack(fill=tk.X)
        
        btn_container = tk.Frame(btn_card, bg='#1a1a2e')
        btn_container.pack(pady=15, padx=15)
        
        buttons = [
            ("➕ ДОБАВИТЬ", self.add_employee, '#27ae60'),
            ("✏️ РЕДАКТИРОВАТЬ", self.edit_employee, '#3498db'),
            ("🗑️ УДАЛИТЬ", self.delete_employee, '#e74c3c'),
            ("🔄 ОБНОВИТЬ", self.load_employees_list, '#95a5a6')
        ]
        
        for text, cmd, color in buttons:
            btn = tk.Button(btn_container, text=text, command=cmd,
                           bg=color, fg='white', font=('Segoe UI', 10, 'bold'),
                           padx=20, pady=8, bd=0, cursor='hand2')
            btn.pack(side=tk.LEFT, padx=5)
        
        # Список сотрудников
        list_card = tk.Frame(self.employees_tab, bg='#1a1a2e', relief=tk.RAISED, bd=0)
        list_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        tk.Frame(list_card, bg='#00d2ff', height=2).pack(fill=tk.X)
        
        list_container = tk.Frame(list_card, bg='#1a1a2e')
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(list_container, text="СПИСОК СОТРУДНИКОВ", font=('Segoe UI', 11, 'bold'),
                bg='#1a1a2e', fg='#00d2ff').pack(anchor='w', pady=(0, 10))
        
        self.employees_listbox = tk.Listbox(list_container, font=('Segoe UI', 10),
                                           bg='#16213e', fg='#e0e0e0',
                                           selectbackground='#00d2ff', height=10,
                                           bd=0, highlightthickness=0)
        self.employees_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Информация о сотруднике
        info_card = tk.Frame(list_container, bg='#16213e', relief=tk.RAISED, bd=0)
        info_card.pack(fill=tk.X, pady=(10, 0))
        
        self.employee_info_text = tk.Text(info_card, font=('Segoe UI', 10), height=6,
                                         bg='#16213e', fg='#a0a0b0', bd=0, 
                                         highlightthickness=0, state='disabled')
        self.employee_info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.employees_listbox.bind('<<ListboxSelect>>', self.on_employee_select)
    
    def create_stats_tab(self):
        # Кнопки статистики
        btn_card = tk.Frame(self.stats_tab, bg='#1a1a2e', relief=tk.RAISED, bd=0)
        btn_card.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Frame(btn_card, bg='#2ecc71', height=2).pack(fill=tk.X)
        
        btn_container = tk.Frame(btn_card, bg='#1a1a2e')
        btn_container.pack(pady=15, padx=15)
        
        week_btn = tk.Button(btn_container, text="НЕДЕЛЯ", command=lambda: self.show_stats('week'),
                            bg='#3498db', fg='white', font=('Segoe UI', 10, 'bold'),
                            padx=25, pady=8, bd=0, cursor='hand2')
        week_btn.pack(side=tk.LEFT, padx=5)
        
        month_btn = tk.Button(btn_container, text="МЕСЯЦ", command=lambda: self.show_stats('month'),
                             bg='#3498db', fg='white', font=('Segoe UI', 10, 'bold'),
                             padx=25, pady=8, bd=0, cursor='hand2')
        month_btn.pack(side=tk.LEFT, padx=5)
        
        # Текстовое поле для статистики
        stats_card = tk.Frame(self.stats_tab, bg='#1a1a2e', relief=tk.RAISED, bd=0)
        stats_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.stats_text = tk.Text(stats_card, wrap=tk.WORD, font=('Consolas', 10),
                                 bg='#16213e', fg='#00ff9d', bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(stats_card, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 15), pady=15)
    
    def update_clock(self):
        current_time = datetime.now().strftime('%H:%M:%S')
        current_date = datetime.now().strftime('%d.%m.%Y')
        self.clock_label.config(text=f"{current_date}  •  {current_time}")
        self.root.after(1000, self.update_clock)
    
    def select_employee(self):
        employees = self.db.get_employees()
        if not employees:
            messagebox.showwarning("Внимание", "Нет сотрудников!")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Выбор сотрудника")
        win.geometry("500x450")
        win.configure(bg='#0f0f1a')
        
        tk.Label(win, text="ВЫБЕРИТЕ СОТРУДНИКА", font=('Segoe UI', 14, 'bold'),
                bg='#0f0f1a', fg='#00d2ff').pack(pady=20)
        
        listbox = tk.Listbox(win, font=('Segoe UI', 11), bg='#16213e', fg='#e0e0e0',
                            selectbackground='#00d2ff', bd=0, highlightthickness=0)
        listbox.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        for emp in employees:
            listbox.insert(tk.END, f"{emp[1]}  |  {emp[2]}  |  {emp[3]}")
        
        def confirm():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                self.current_employee = employees[idx]
                self.emp_name_label.config(text=self.current_employee[1].upper())
                
                is_working = self.db.is_working_now(self.current_employee[0])
                
                if is_working:
                    self.clock_in_btn.config(state='disabled', bg='#555555')
                    self.clock_out_btn.config(state='normal', bg='#e74c3c')
                    self.emp_status_label.config(text="🔴 В РАБОТЕ", fg='#e74c3c')
                else:
                    self.clock_in_btn.config(state='normal', bg='#27ae60')
                    self.clock_out_btn.config(state='disabled', bg='#555555')
                    self.emp_status_label.config(text="⚪ НЕ В РАБОТЕ", fg='#95a5a6')
                
                win.destroy()
                messagebox.showinfo("Успех", f"Выбран: {self.current_employee[1]}")
            else:
                messagebox.showwarning("Внимание", "Выберите сотрудника!")
        
        tk.Button(win, text="ВЫБРАТЬ", command=confirm,
                 bg='#27ae60', fg='white', font=('Segoe UI', 11, 'bold'),
                 padx=40, pady=10, bd=0, cursor='hand2').pack(pady=20)
    
    def clock_in(self):
        if not self.current_employee:
            messagebox.showwarning("Внимание", "Сначала выберите сотрудника!")
            return
        
        success, message = self.db.clock_in(self.current_employee[0])
        
        if success:
            messagebox.showinfo("Успех", message)
            self.clock_in_btn.config(state='disabled', bg='#555555')
            self.clock_out_btn.config(state='normal', bg='#e74c3c')
            self.emp_status_label.config(text="🔴 В РАБОТЕ", fg='#e74c3c')
            self.refresh_all()
        else:
            messagebox.showwarning("Внимание", message)
    
    def clock_out(self):
        if not self.current_employee:
            messagebox.showwarning("Внимание", "Сначала выберите сотрудника!")
            return
        
        success, message = self.db.clock_out(self.current_employee[0])
        
        if success:
            messagebox.showinfo("Успех", message)
            self.clock_in_btn.config(state='normal', bg='#27ae60')
            self.clock_out_btn.config(state='disabled', bg='#555555')
            self.emp_status_label.config(text="⚪ НЕ В РАБОТЕ", fg='#95a5a6')
            self.refresh_all()
        else:
            messagebox.showwarning("Внимание", message)
    
    def show_history(self):
        start = self.start_date.get()
        end = self.end_date.get()
        
        try:
            datetime.strptime(start, '%Y-%m-%d')
            datetime.strptime(end, '%Y-%m-%d')
        except:
            messagebox.showerror("Ошибка", "Неверный формат даты!")
            return
        
        self.history_text.delete(1.0, tk.END)
        records = self.db.get_history(start, end)
        
        if not records:
            self.history_text.insert(tk.END, "📭 Нет записей за выбранный период")
            return
        
        for rec in records:
            line = f"👤 {rec[0]:<25} | 💼 {rec[1]:<15} | 📅 {rec[2]} | ⏰ {rec[3]}-{rec[4]} | ⌛ {rec[5]} ч.\n"
            self.history_text.insert(tk.END, line)
            self.history_text.insert(tk.END, "─" * 95 + "\n")
    
    def add_employee(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление сотрудника")
        dialog.geometry("500x600")
        dialog.configure(bg='#0f0f1a')
        
        tk.Label(dialog, text="НОВЫЙ СОТРУДНИК", font=('Segoe UI', 14, 'bold'),
                bg='#0f0f1a', fg='#00d2ff').pack(pady=20)
        
        labels = ["ФИО:", "Должность:", "Отдел:", "Телефон:", "Email:", "Дата найма:"]
        entries = {}
        
        for label in labels:
            frame = tk.Frame(dialog, bg='#0f0f1a')
            frame.pack(pady=10, padx=30, fill=tk.X)
            
            tk.Label(frame, text=label, width=15, anchor='w', bg='#0f0f1a',
                    fg='#a0a0b0', font=('Segoe UI', 10)).pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=('Segoe UI', 10), bg='#16213e', fg='#e0e0e0',
                           bd=0, insertbackground='white')
            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            entries[label] = entry
        
        entries["Дата найма:"].insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        def save():
            values = [entries[label].get().strip() for label in labels]
            if not values[0]:
                messagebox.showwarning("Внимание", "Введите ФИО")
                return
            
            if self.db.add_employee(values[0], values[1], values[2], values[3], values[4], values[5]):
                messagebox.showinfo("Успех", "Сотрудник добавлен")
                dialog.destroy()
                self.load_employees_list()
                self.refresh_all()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить")
        
        tk.Button(dialog, text="СОХРАНИТЬ", command=save,
                 bg='#27ae60', fg='white', font=('Segoe UI', 11, 'bold'),
                 padx=40, pady=10, bd=0, cursor='hand2').pack(pady=30)
    
    def edit_employee(self):
        selection = self.employees_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return
        
        selected_text = self.employees_listbox.get(selection[0])
        emp_id = int(selected_text.split('|')[0].strip())
        emp_info = self.db.get_employee_by_id(emp_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование сотрудника")
        dialog.geometry("500x600")
        dialog.configure(bg='#0f0f1a')
        
        tk.Label(dialog, text="РЕДАКТИРОВАНИЕ", font=('Segoe UI', 14, 'bold'),
                bg='#0f0f1a', fg='#00d2ff').pack(pady=20)
        
        labels = ["ФИО:", "Должность:", "Отдел:", "Телефон:", "Email:", "Дата найма:"]
        entries = {}
        
        for label in labels:
            frame = tk.Frame(dialog, bg='#0f0f1a')
            frame.pack(pady=10, padx=30, fill=tk.X)
            
            tk.Label(frame, text=label, width=15, anchor='w', bg='#0f0f1a',
                    fg='#a0a0b0', font=('Segoe UI', 10)).pack(side=tk.LEFT)
            entry = tk.Entry(frame, font=('Segoe UI', 10), bg='#16213e', fg='#e0e0e0',
                           bd=0, insertbackground='white')
            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            entries[label] = entry
        
        entries["ФИО:"].insert(0, emp_info[1])
        entries["Должность:"].insert(0, emp_info[2] if emp_info[2] else '')
        entries["Отдел:"].insert(0, emp_info[3] if emp_info[3] else '')
        entries["Телефон:"].insert(0, emp_info[4] if emp_info[4] else '')
        entries["Email:"].insert(0, emp_info[5] if emp_info[5] else '')
        entries["Дата найма:"].insert(0, emp_info[6] if emp_info[6] else '')
        
        def save():
            values = [entries[label].get().strip() for label in labels]
            if not values[0]:
                messagebox.showwarning("Внимание", "Введите ФИО")
                return
            
            if self.db.update_employee(emp_id, values[0], values[1], values[2], values[3], values[4], values[5]):
                messagebox.showinfo("Успех", "Данные обновлены")
                dialog.destroy()
                self.load_employees_list()
                self.refresh_all()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить")
        
        tk.Button(dialog, text="СОХРАНИТЬ", command=save,
                 bg='#27ae60', fg='white', font=('Segoe UI', 11, 'bold'),
                 padx=40, pady=10, bd=0, cursor='hand2').pack(pady=30)
    
    def delete_employee(self):
        selection = self.employees_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return
        
        selected_text = self.employees_listbox.get(selection[0])
        emp_id = int(selected_text.split('|')[0].strip())
        emp_name = selected_text.split('|')[1].strip()
        
        if messagebox.askyesno("Подтверждение", f"Удалить {emp_name}?"):
            if self.db.delete_employee(emp_id):
                messagebox.showinfo("Успех", "Сотрудник удалён")
                self.load_employees_list()
                
                if self.current_employee and self.current_employee[0] == emp_id:
                    self.current_employee = None
                    self.emp_name_label.config(text="НЕ ВЫБРАН")
                    self.emp_status_label.config(text="")
                    self.clock_in_btn.config(state='disabled', bg='#555555')
                    self.clock_out_btn.config(state='disabled', bg='#555555')
                
                self.refresh_all()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить")
    
    def on_employee_select(self, event):
        selection = self.employees_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.employees_listbox.get(selection[0])
        emp_id = int(selected_text.split('|')[0].strip())
        emp_info = self.db.get_employee_by_id(emp_id)
        
        if emp_info:
            self.employee_info_text.config(state='normal')
            self.employee_info_text.delete(1.0, tk.END)
            
            info = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 ФИО:        {emp_info[1]}
💼 Должность:  {emp_info[2] if emp_info[2] else 'Не указана'}
🏢 Отдел:      {emp_info[3] if emp_info[3] else 'Не указан'}
📞 Телефон:    {emp_info[4] if emp_info[4] else 'Не указан'}
✉️ Email:      {emp_info[5] if emp_info[5] else 'Не указан'}
📅 Дата найма: {emp_info[6] if emp_info[6] else 'Не указана'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """
            self.employee_info_text.insert(tk.END, info)
            self.employee_info_text.config(state='disabled')
    
    def show_stats(self, period):
        self.stats_text.delete(1.0, tk.END)
        stats, start_date, end_date, period_name = self.db.get_statistics(period)
        
        self.stats_text.insert(tk.END, "╔" + "═" * 78 + "╗\n")
        self.stats_text.insert(tk.END, f"║{' СТАТИСТИКА РАБОЧЕГО ВРЕМЕНИ ' + period_name.upper():^78}║\n")
        self.stats_text.insert(tk.END, f"║{' Период: ' + str(start_date) + ' — ' + str(end_date):^78}║\n")
        self.stats_text.insert(tk.END, "╠" + "═" * 78 + "╣\n")
        
        if not stats:
            self.stats_text.insert(tk.END, "║{' Нет данных за указанный период':^78}║\n")
        else:
            self.stats_text.insert(tk.END, f"║ {'ФИО':<30} {'Должность':<20} {'Часов':<10} {'Дней':<8} {'Среднее':<8} ║\n")
            self.stats_text.insert(tk.END, "╠" + "═" * 78 + "╣\n")
            
            for stat in stats:
                name, position, hours, days, avg = stat
                line = f"║ {name:<30} {position:<20} {hours:<10} {days:<8} {avg:<8} ║\n"
                self.stats_text.insert(tk.END, line)
            
            if stats:
                total_hours = sum(s[2] for s in stats)
                self.stats_text.insert(tk.END, "╠" + "═" * 78 + "╣\n")
                self.stats_text.insert(tk.END, f"║{' ИТОГО: ' + str(total_hours) + ' часов':^78}║\n")
        
        self.stats_text.insert(tk.END, "╚" + "═" * 78 + "╝\n")
    
    def load_employees_list(self):
        self.employees_listbox.delete(0, tk.END)
        employees = self.db.get_employees()
        for emp in employees:
            self.employees_listbox.insert(tk.END, f"{emp[0]} | {emp[1]} | {emp[2]} | {emp[3]}")
    
    def refresh_all(self):
        # Обновляем сотрудников на работе
        self.working_listbox.delete(0, tk.END)
        working = self.db.get_today_working()
        if working:
            for emp in working:
                self.working_listbox.insert(tk.END, f"🟢 {emp[0]} — {emp[1]}  |  с {emp[2]}")
        else:
            self.working_listbox.insert(tk.END, "   Нет сотрудников на работе")
        
        # Обновляем сегодняшние записи
        self.today_text.delete(1.0, tk.END)
        records = self.db.get_today_records()
        if not records:
            self.today_text.insert(tk.END, "📭 Нет записей за сегодня\n")
        else:
            for rec in records:
                line = f"👤 {rec[0]:<25} | 💼 {rec[1]:<15} | ⏰ {rec[2]} — {rec[3]} | ⌛ {rec[4]} ч.\n"
                self.today_text.insert(tk.END, line)
                self.today_text.insert(tk.END, "─" * 70 + "\n")
        
        # Обновляем историю
        self.show_history()
        
        # Обновляем статистику
        self.show_stats('week')
    
    def on_closing(self):
        if messagebox.askokcancel("Выход", "Закрыть программу?"):
            self.db.close()
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.mainloop()
