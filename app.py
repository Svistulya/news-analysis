import json
import tkinter as tk
from tkinter import ttk
from textblob import TextBlob
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RedditSentimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reddit Sentiment Analyzer")
        self.root.geometry("900x700")
        
        
        self.data = self.load_data()
        
       
        self.create_widgets()
        
    def load_data(self):
        try:
            with open('reddit_sentiment_analysis.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def create_widgets(self):
        if not self.data:
            tk.Label(self.root, text="Ошибка загрузки данных", fg="red").pack()
            return
        
        
        stats_frame = ttk.LabelFrame(self.root, text="Общая статистика")
        stats_frame.pack(pady=10, padx=10, fill="x")
        
        total_posts = self.data['posts_analyzed']
        sentiment_counts = self.data['sentiment_distribution']
        
        ttk.Label(stats_frame, text=f"Всего постов: {total_posts}").grid(row=0, column=0, padx=5)
        ttk.Label(stats_frame, text=f"Позитивных: {sentiment_counts.get('positive', 0)}").grid(row=0, column=1, padx=5)
        ttk.Label(stats_frame, text=f"Негативных: {sentiment_counts.get('negative', 0)}").grid(row=0, column=2, padx=5)
        ttk.Label(stats_frame, text=f"Нейтральных: {sentiment_counts.get('neutral', 0)}").grid(row=0, column=3, padx=5)
        
        
        self.create_sentiment_chart()
        
        
        self.create_posts_table()
        
        
        self.create_details_section()
    
    def create_sentiment_chart(self):
        chart_frame = ttk.LabelFrame(self.root, text="Распределение тональности")
        chart_frame.pack(pady=10, padx=10, fill="x")
        
        fig = Figure(figsize=(6, 3), dpi=100)
        ax = fig.add_subplot(111)
        
        sentiments = self.data['sentiment_distribution']
        labels = sentiments.keys()
        sizes = sentiments.values()
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_posts_table(self):
        table_frame = ttk.LabelFrame(self.root, text="Заголовки постов")
        table_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        
        self.tree = ttk.Treeview(table_frame, columns=('title', 'sentiment'), show='headings')
        self.tree.heading('title', text='Заголовок')
        self.tree.heading('sentiment', text='Тональность')
        self.tree.column('title', width=600)
        self.tree.column('sentiment', width=100)
        
        
        for post in self.data['detailed_results']:
            sentiment = post['analysis']['sentiment']
            self.tree.insert('', 'end', values=(post['title'], sentiment), 
                            tags=(sentiment,))
        
        
        self.tree.tag_configure('positive', background='#d4edda')
        self.tree.tag_configure('negative', background='#f8d7da')
        self.tree.tag_configure('neutral', background='#e2e3e5')
        
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        
        
        self.tree.bind('<<TreeviewSelect>>', self.on_post_select)
    
    def create_details_section(self):
        details_frame = ttk.LabelFrame(self.root, text="Детали анализа")
        details_frame.pack(pady=10, padx=10, fill="x")
        
        self.details_text = tk.Text(details_frame, height=8, wrap="word")
        self.details_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        
        self.selected_post_chart = None
        self.chart_canvas = None
    
    def on_post_select(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
            
        item_data = self.tree.item(selected_item)
        title = item_data['values'][0]
        
        
        post = next((p for p in self.data['detailed_results'] if p['title'] == title), None)
        if not post:
            return
            
       
        analysis = post['analysis']
        details = (
            f"Заголовок: {title}\n\n"
            f"Тональность: {analysis['sentiment']}\n"
            f"Полярность: {analysis['polarity']:.2f} (от -1 до 1)\n"
            f"Субъективность: {analysis['subjectivity']:.2f} (от 0 до 1)\n\n"
            f"Интерпретация:\n"
            f"- Полярность ближе к 1: позитивный тон\n"
            f"- Полярность ближе к -1: негативный тон\n"
            f"- Субъективность выше 0.5: мнение/оценка\n"
            f"- Субъективность ниже 0.5: факты/информация"
        )
        
        self.details_text.config(state="normal")
        self.details_text.delete(1.0, "end")
        self.details_text.insert("end", details)
        self.details_text.config(state="disabled")
        
        self.update_post_chart(analysis)
    
    def update_post_chart(self, analysis):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            
        chart_frame = ttk.LabelFrame(self.root, text="Анализ выбранного поста")
        chart_frame.pack(pady=10, padx=10, fill="x")
        
        fig = Figure(figsize=(6, 2), dpi=100)
        ax = fig.add_subplot(111)
        
       
        labels = ['Полярность', 'Субъективность']
        values = [analysis['polarity'], analysis['subjectivity']]
        colors = ['#007bff', '#28a745']
        
        bars = ax.bar(labels, values, color=colors)
        
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom')
        
        ax.set_ylim(-1, 1)
        ax.axhline(0, color='black', linewidth=0.8)
        
        self.chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = RedditSentimentApp(root)
    root.mainloop()