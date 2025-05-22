import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from parser import RedditParser
import tempfile
import os


class RedditSentimentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reddit Sentiment Analyzer")
        self.temp_files = []
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

        stats_frame = ttk.LabelFrame(self.root, text="Общая статистика")
        stats_frame.pack(pady=10, padx=10, fill="x")

        total_posts = self.data['posts_analyzed']
        sentiment_counts = self.data['sentiment_distribution']

        ttk.Label(stats_frame, text=f"Всего постов: {total_posts}").grid(row=0, column=0, padx=5)
        ttk.Label(stats_frame, text=f"Позитивных: {sentiment_counts.get('positive', 0)}").grid(row=0, column=1, padx=5)
        ttk.Label(stats_frame, text=f"Негативных: {sentiment_counts.get('negative', 0)}").grid(row=0, column=2, padx=5)
        ttk.Label(stats_frame, text=f"Нейтральных: {sentiment_counts.get('neutral', 0)}").grid(row=0, column=3, padx=5)

        self.combined_frame = ttk.Frame(self.root)
        self.combined_frame.pack(padx=10, pady=10, fill="x")

        self.create_sentiment_chart(self.combined_frame)
        self.create_image_viewer(self.combined_frame)

        self.create_posts_table()
        self.create_details_section()

    def create_sentiment_chart(self, parent):
        chart_frame = ttk.LabelFrame(parent, text="Распределение тональности")
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0,10))

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

    def create_image_viewer(self, parent):
        self.image_frame = ttk.LabelFrame(parent, text="Изображения поста")
        self.image_frame.pack(side="right", fill="both", expand=True)

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
            self.tree.insert('', 'end', values=(post['title'], sentiment, image_count), tags=(sentiment,))

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

    def on_frame_configure(self, event):
        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))

    def on_post_select(self, event):
        selected = self.tree.focus()
        if not selected:
            return

        values = self.tree.item(selected, 'values')
        title = values[0]

        post = next((p for p in self.data['detailed_results'] if p['title'] == title), None)
        if not post:
            return

        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"Заголовок: {post['title']}\n")
        self.details_text.insert(tk.END, f"Автор: {post['author']}\n")
        self.details_text.insert(tk.END, f"Ссылка: {post['url']}\n")
        self.details_text.insert(tk.END, f"Оценка: {post['score']}\n")
        self.details_text.insert(tk.END, f"Комментариев: {post['num_comments']}\n")
        self.details_text.insert(tk.END, f"Дата: {post['created_utc']}\n")
        self.details_text.insert(tk.END, f"Тональность: {post['analysis']['sentiment']}\n")

        self.current_images = post.get('images', [])
        self.current_image_index = 0
        self.show_image()

    def show_image(self):
        self.image_label.config(image='', text='')

        if not self.current_images:
            self.image_label.config(text='Нет изображений для отображения.')
            self.image_index_label.config(text="0/0")
            return

        image_url = self.current_images[self.current_image_index]
        local_path = self.download_temp_image(image_url)

        if local_path:
            try:
                image = Image.open(local_path).convert("RGB")
                image.thumbnail((700, 500))
                self.current_photo = ImageTk.PhotoImage(image)
                self.image_label.config(image=self.current_photo)
                self.image_index_label.config(text=f"{self.current_image_index + 1}/{len(self.current_images)}")
            except Exception as e:
                self.image_label.config(text=f"Ошибка открытия: {e}")
        else:
            self.image_label.config(text="Ошибка загрузки изображения.")

    def next_image(self):
        if self.current_image_index < len(self.current_images) - 1:
            self.current_image_index += 1
            self.show_image()

    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()

    def download_temp_image(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_file.write(response.content)
                temp_file.close()
                self.temp_files.append(temp_file.name)
                return temp_file.name
            else:
                print(f"[ERROR] Не удалось загрузить изображение: {response.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки: {e}")
            return None

    def cleanup_temp_files(self):
        for path in getattr(self, 'temp_files', []):
            try:
                os.remove(path)
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = RedditSentimentApp(root)
    root.mainloop()
    app.cleanup_temp_files()
