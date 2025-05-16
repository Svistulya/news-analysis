import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from parser import RedditParser

class RedditSentimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reddit Sentiment Analyzer")
        self.root.geometry("1200x900")
        
        
        self.parser = RedditParser()
        self.data = self.parser.get_analyzed_posts()
        
        self.current_images = []
        self.current_photo = None
        self.current_image_index = 0
        
        self.create_widgets()
    
    def create_widgets(self):
        if not self.data:
            tk.Label(self.root, text="Ошибка загрузки данных", fg="red").pack()
            return
        
        # Верхняя панель с общей статистикой
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
        self.create_image_viewer()
        
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
        
        self.tree = ttk.Treeview(table_frame, columns=('title', 'sentiment', 'images'), show='headings')
        self.tree.heading('title', text='Заголовок')
        self.tree.heading('sentiment', text='Тональность')
        self.tree.heading('images', text='Изображения')
        self.tree.column('title', width=400)
        self.tree.column('sentiment', width=100)
        self.tree.column('images', width=100)
        
        for post in self.data['detailed_results']:
            sentiment = post['analysis']['sentiment']
            image_count = len(post.get('images', []))
            self.tree.insert('', 'end', values=(post['title'], sentiment, image_count), 
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
    
    def create_image_viewer(self):
        self.image_frame = ttk.LabelFrame(self.root, text="Изображения поста")
        self.image_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        
        self.image_canvas = tk.Canvas(self.image_frame, bg='white')
        self.scroll_y = ttk.Scrollbar(self.image_frame, orient="vertical", command=self.image_canvas.yview)
        self.image_canvas.configure(yscrollcommand=self.scroll_y.set)
        
        self.scroll_y.pack(side="right", fill="y")
        self.image_canvas.pack(side="left", fill="both", expand=True)
        
        
        self.image_container = ttk.Frame(self.image_canvas)
        self.image_canvas.create_window((0, 0), window=self.image_container, anchor="nw")
        
        
        self.image_label = ttk.Label(self.image_container)
        self.image_label.pack()
        
        
        self.image_nav_frame = ttk.Frame(self.image_frame)
        self.image_nav_frame.pack(fill="x")
        
        self.prev_button = ttk.Button(self.image_nav_frame, text="← Предыдущее", command=self.prev_image)
        self.prev_button.pack(side="left", padx=5)
        
        self.next_button = ttk.Button(self.image_nav_frame, text="Следующее →", command=self.next_image)
        self.next_button.pack(side="right", padx=5)
        
        self.image_index_label = ttk.Label(self.image_nav_frame, text="0/0")
        self.image_index_label.pack()
        
        
        self.image_container.bind("<Configure>", self.on_frame_configure)
    
    def on_frame_configure(self, event):
        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
    
    def load_image_from_url(self, url):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            
            
            max_width = self.image_canvas.winfo_width() - 50
            max_height = 600
            
            width, height = img.size
            ratio = min(max_width/width, max_height/height)
            new_size = (int(width*ratio), int(height*ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Не удалось загрузить изображение {e}")
            return None
    
    def display_image(self, image_url):
        self.current_photo = self.load_image_from_url(image_url)
        if self.current_photo:
            self.image_label.config(image=self.current_photo)
        else:
            self.image_label.config(text="Не удалось загрузить изображение")
    
    def display_images(self, image_urls):
        self.current_images = image_urls
        self.current_image_index = 0
        if self.current_images:
            self.display_image(self.current_images[0])
            self.update_navigation_controls()
        else:
            self.image_label.config(text="Нет изображений для отображения")
            self.update_navigation_controls()
    
    def update_navigation_controls(self):
        if self.current_images:
            self.image_index_label.config(text=f"{self.current_image_index+1}/{len(self.current_images)}")
            self.prev_button.config(state="normal" if self.current_image_index > 0 else "disabled")
            self.next_button.config(state="normal" if self.current_image_index < len(self.current_images)-1 else "disabled")
        else:
            self.image_index_label.config(text="0/0")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
    
    def next_image(self):
        if self.current_images and self.current_image_index < len(self.current_images)-1:
            self.current_image_index += 1
            self.display_image(self.current_images[self.current_image_index])
            self.update_navigation_controls()
    
    def prev_image(self):
        if self.current_images and self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_image(self.current_images[self.current_image_index])
            self.update_navigation_controls()
    
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
        self.display_images(post.get('images', []))
    
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
