import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tempfile
import os
import webbrowser

class RedditSentimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reddit Sentiment Analyzer")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabelFrame", background="#f0f0f0", font=('Helvetica', 10, 'bold'))
        self.style.configure("TLabel", background="#f0f0f0")
        self.style.configure("TButton", font=('Helvetica', 9))
        self.style.configure("Treeview", font=('Helvetica', 9), rowheight=25)
        self.style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        
        self.temp_files = []
        
        from parser import RedditParser
        self.parser = RedditParser()
        self.data = self.parser.get_analyzed_posts()
        
        self.current_images = []
        self.current_photo = None
        self.current_image_index = 0
        
        self.create_widgets()
    
    def create_widgets(self):
        if not self.data:
            tk.Label(self.root, text="Ошибка загрузки данных", fg="red", bg="#f0f0f0").pack()
            return
        
        
        stats_frame = ttk.LabelFrame(self.root, text="Общая статистика")
        stats_frame.pack(pady=10, padx=10, fill="x")
        
        stats = [
            ("Всего постов", self.data['posts_analyzed']),
            ("Позитивных", self.data['sentiment_distribution'].get('positive', 0)),
            ("Негативных", self.data['sentiment_distribution'].get('negative', 0)),
            ("Нейтральных", self.data['sentiment_distribution'].get('neutral', 0))
        ]
        
        for i, (label, value) in enumerate(stats):
            ttk.Label(stats_frame, text=f"{label}: {value}").grid(row=0, column=i, padx=10, pady=5)
        
    
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        
        self.create_sentiment_chart(top_frame)
        self.create_image_viewer(top_frame)        
        self.create_posts_table()
        self.create_details_section()
    
    def create_sentiment_chart(self, parent):
        chart_frame = ttk.LabelFrame(parent, text="Распределение тональности")
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=5)
        
        fig = Figure(figsize=(5, 3), dpi=100, facecolor="#f0f0f0")
        ax = fig.add_subplot(111)
        
        sentiments = self.data['sentiment_distribution']
        labels = list(sentiments.keys())
        sizes = list(sentiments.values())
        colors = ['#4CAF50', '#F44336', '#9E9E9E']  
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.axis('equal')
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
    
    def create_image_viewer(self, parent):
        self.image_frame = ttk.LabelFrame(parent, text="Изображение поста")
        self.image_frame.pack(side="right", fill="both", expand=True, pady=5)
        
        
        self.image_canvas = tk.Canvas(self.image_frame, bg="white", highlightthickness=0)
        self.image_scroll = ttk.Scrollbar(self.image_frame, orient="vertical", command=self.image_canvas.yview)
        self.image_canvas.configure(yscrollcommand=self.image_scroll.set)
        
        self.image_scroll.pack(side="right", fill="y")
        self.image_canvas.pack(side="left", fill="both", expand=True)
        
        
        self.image_container = ttk.Frame(self.image_canvas)
        self.image_canvas.create_window((0, 0), window=self.image_container, anchor="nw")
        
       
        self.image_label = ttk.Label(self.image_container)
        self.image_label.pack(fill="both", expand=True)
        
        
        nav_frame = ttk.Frame(self.image_frame)
        nav_frame.pack(fill="x", pady=(5, 0))
        
        self.prev_btn = ttk.Button(nav_frame, text="← Предыдущее", command=self.prev_image)
        self.prev_btn.pack(side="left", padx=5)
        
        self.next_btn = ttk.Button(nav_frame, text="Следующее →", command=self.next_image)
        self.next_btn.pack(side="right", padx=5)
        
        self.image_info = ttk.Label(nav_frame, text="0/0")
        self.image_info.pack()
        
        
        self.image_container.bind("<Configure>", lambda e: self.image_canvas.configure(
            scrollregion=self.image_canvas.bbox("all")))
    
    def create_posts_table(self):
        table_frame = ttk.LabelFrame(self.root, text="Посты Reddit")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
      
        self.tree = ttk.Treeview(table_frame, columns=('title', 'sentiment', 'images'), show='headings')
        self.tree.heading('title', text='Заголовок')
        self.tree.heading('sentiment', text='Тональность')
        self.tree.heading('images', text='Изображения')
        self.tree.column('title', width=400, anchor="w")
        self.tree.column('sentiment', width=100, anchor="center")
        self.tree.column('images', width=100, anchor="center")
        
        self.tree.tag_configure('positive', background='#E8F5E9')  
        self.tree.tag_configure('negative', background='#FFEBEE')  
        self.tree.tag_configure('neutral', background='#EEEEEE')   
        
        
        for post in self.data['detailed_results']:
            sentiment = post['analysis']['sentiment']
            self.tree.insert('', 'end', 
                           values=(post['title'], sentiment, len(post.get('images', []))),
                           tags=(sentiment,))
        
       
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        
        self.tree.bind('<<TreeviewSelect>>', self.on_post_select)
        self.tree.bind('<Double-1>', self.open_post_in_browser)
    
    def create_details_section(self):
        details_frame = ttk.LabelFrame(self.root, text="Детали поста")
        details_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.details_text = tk.Text(details_frame, height=8, wrap="word", font=('Helvetica', 9))
        self.details_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def on_post_select(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        
        item = self.tree.item(selected)
        title = item['values'][0]
        
        post = next((p for p in self.data['detailed_results'] if p['title'] == title), None)
        if not post:
            return
        
        
        self.details_text.config(state="normal")
        self.details_text.delete(1.0, tk.END)
        
        details = [
            f"Заголовок: {post['title']}\n",
            f"Автор: u/{post['author']}\n",
            f"Сабреддит: r/{post['subreddit']}\n",
            f"Рейтинг: {post['score']} | Комментарии: {post['num_comments']}\n",
            f"Дата: {post['created_utc']}\n",
            f"\nТональность: {post['analysis']['sentiment'].capitalize()}",
            f" (Полярность: {post['analysis']['polarity']:.2f}, ",
            f"Субъективность: {post['analysis']['subjectivity']:.2f})\n"
        ]
        
        self.details_text.insert(tk.END, ''.join(details))
        self.details_text.config(state="disabled")
        
        
        self.current_images = post.get('images', [])
        self.current_image_index = 0
        self.show_image()
    
    def show_image(self):
        if not self.current_images:
            self.image_label.config(image='', text='Нет изображений для отображения')
            self.image_info.config(text="0/0")
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            return
        
        
        img_url = self.current_images[self.current_image_index]
        img_data = self.download_image(img_url)
        
        if img_data:
            try:
                img = Image.open(BytesIO(img_data))
                
                
                canvas_width = self.image_canvas.winfo_width() - 20
                canvas_height = self.image_canvas.winfo_height() - 20
                
                img_ratio = img.width / img.height
                canvas_ratio = canvas_width / canvas_height
                
                if img_ratio > canvas_ratio:
                    new_width = canvas_width
                    new_height = int(canvas_width / img_ratio)
                else:
                    new_height = canvas_height
                    new_width = int(canvas_height * img_ratio)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.current_photo = ImageTk.PhotoImage(img)
                
                self.image_label.config(image=self.current_photo)
                self.image_info.config(text=f"{self.current_image_index + 1}/{len(self.current_images)}")
                
                self.prev_btn.config(state="normal" if self.current_image_index > 0 else "disabled")
                self.next_btn.config(state="normal" if self.current_image_index < len(self.current_images)-1 else "disabled")
                
            except Exception as e:
                self.image_label.config(image='', text=f"Ошибка загрузки изображения: {str(e)}")
        else:
            self.image_label.config(image='', text="Не удалось загрузить изображение")
    
    def download_image(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            return None
    
    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()
    
    def next_image(self):
        if self.current_image_index < len(self.current_images) - 1:
            self.current_image_index += 1
            self.show_image()
    
    def open_post_in_browser(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        
        item = self.tree.item(selected)
        title = item['values'][0]
        
        post = next((p for p in self.data['detailed_results'] if p['title'] == title), None)
        if post and 'permalink' in post:
            webbrowser.open(post['permalink'])
    
    def cleanup_temp_files(self):
        for path in self.temp_files:
            try:
                os.remove(path)
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = RedditSentimentApp(root)
    root.mainloop()
    app.cleanup_temp_files()
