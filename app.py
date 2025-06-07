import tkinter as tk
from transformers import pipeline
from mastodon import Mastodon, StreamListener
import re
import threading
import queue
import csv
from tkinter import simpledialog
import tkinter.ttk as ttk
from preprocess import preprocess_text
import nltk
import os

nltk.download('punkt')
nltk.download('stopwords')

ACCESS_TOKEN = "NEHiaVVyzlN6ETGR5habZCcjjq3ZB15n7KCMcU57_Go"
API_BASE_URL = "https://mastodon.social"

sentiment = pipeline("sentiment-analysis", model="best_model", tokenizer="best_model")

toot_queue = queue.Queue()

current_toot = None 
corrected_label = None
correction_target_selected = ""

class MyListener(StreamListener):
    def on_update(self, status):
        lang = status.get("language")
        if lang != "en":
            return

        html = status.get("content", "")
        original = re.sub('<[^<]+?>', '', html)
        preprocessed = preprocess_text(original)

        result_orig = sentiment(original)[0]
        result_clean = sentiment(preprocessed)[0]

        toot_queue.put({
            "original": original,
            "preprocessed": preprocessed,
            "orig_sentiment": result_orig["label"],
            "orig_score": round(result_orig["score"], 2),
            "prep_sentiment": result_clean["label"],
            "prep_score": round(result_clean["score"], 2),
        })
from tkinter.simpledialog import Dialog

class CorrectionDialog(Dialog):
    def body(self, master):
        self.corrected_label = None
        self.corrected_target = tk.StringVar(value="preprocessed")

        tk.Label(master, text="Apply correction to:").grid(row=1, column=0, columnspan=2, sticky="w")
        tk.Radiobutton(master, text="Preprocessed", variable=self.corrected_target, value="preprocessed").grid(row=2, column=0, sticky="w")
        tk.Radiobutton(master, text="Original", variable=self.corrected_target, value="original").grid(row=2, column=1, sticky="w")

        tk.Label(master, text="Select corrected sentiment:").grid(row=0, column=0, sticky="w")
        self.sentiment_var = tk.StringVar()
        self.sentiment_menu = ttk.Combobox(master, textvariable=self.sentiment_var, state="readonly")
        self.sentiment_menu['values'] = ("POSITIVE", "NEGATIVE", "NEUTRAL")
        self.sentiment_menu.grid(row=0, column=1)
        self.sentiment_menu.current(0)

    def apply(self):
        selected = self.sentiment_var.get()
        if selected in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
            self.corrected_label = selected

def start_stream():
    mastodon = Mastodon(access_token=ACCESS_TOKEN, api_base_url=API_BASE_URL)
    mastodon.stream_public(MyListener())

threading.Thread(target=start_stream, daemon=True).start()

root = tk.Tk()
root.title("Mastodon Sentiment Feed")
root.geometry("750x600")
root.configure(bg="#bb1b1b")

root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
root.update_idletasks()
root.minsize(400, 300)

frame = tk.Frame(root, bg="#ffffff", bd=2, relief="groove", padx=20, pady=20)
frame.grid(row=0, column=0, sticky="nsew")
frame.rowconfigure(1, weight=1)
frame.columnconfigure(0, weight=1)

heading = tk.Label(frame, text="Mastodon Sentiment Annotation Tool", font=("Helvetica", 20, "bold"), bg="#ffffff")
heading.grid(row=0, column=0, sticky="w", pady=(0, 10))

text_box = tk.Text(frame, wrap="word", font=("Helvetica", 12), bg="#ffffff", fg="#333333")
text_box.grid(row=1, column=0, sticky="nsew", pady=10)
text_box.configure(state="disabled") 

sentiment_label = tk.Label(
    frame, text="", font=("Helvetica", 14, "bold"),
    fg="blue", bg="#ffffff"
)
sentiment_label.grid(row=2, column=0, sticky="w", pady=(10, 10))

correction_target = tk.StringVar(value="preprocessed")
correction_target_selected = ""

def show_next():
    global current_toot, corrected_label
    corrected_label = None  

    if not toot_queue.empty():
        current_toot = toot_queue.get()

        text_box.configure(state="normal")
        text_box.delete("1.0", tk.END)

        text_box.tag_configure("header", font=("Helvetica", 14, "bold"))
        text_box.tag_configure("prediction", font=("Helvetica", 14), lmargin1=15, lmargin2=15)
        text_box.tag_configure("pos", foreground="#2e7d32")     
        text_box.tag_configure("neg", foreground="#c62828")     
        text_box.tag_configure("neu", foreground="#ef6c00")
        text_box.tag_configure("score_high", foreground="#2e7d32")  
        text_box.tag_configure("score_med", foreground="#ef6c00")   
        text_box.tag_configure("score_low", foreground="#c62828")  

        text_box.insert(tk.END, "Original:\n", "header")
        text_box.insert(tk.END, current_toot['original'] + "\n\n")

        text_box.insert(tk.END, "Prediction (Original): ", "header")
        text_box.insert(tk.END, f"{current_toot['orig_sentiment'].capitalize()} ", get_sentiment_tag(current_toot['orig_sentiment']))
        text_box.insert(tk.END, f"({current_toot['orig_score']*100:.2f}%)\n\n\n", get_score_tag(current_toot['orig_score']))

        text_box.insert(tk.END, "Preprocessed:\n", "header")
        text_box.insert(tk.END, current_toot['preprocessed'] + "\n\n")

        text_box.insert(tk.END, "Prediction (Preprocessed): ", "header")
        text_box.insert(tk.END, f"{current_toot['prep_sentiment'].capitalize()} ", get_sentiment_tag(current_toot['prep_sentiment']))
        text_box.insert(tk.END, f"({current_toot['prep_score']*100:.2f}%)\n\n\n", get_score_tag(current_toot['prep_score']))

        text_box.configure(state="disabled")
        sentiment_label.config(text="")
    else:
        current_toot = None
        text_box.configure(state="normal")
        text_box.delete("1.0", tk.END)
        text_box.insert(tk.END, "No new texts available.")
        text_box.configure(state="disabled")

def get_sentiment_tag(sentiment):
    sentiment = sentiment.strip().upper()
    if sentiment == "POSITIVE":
        return "pos"
    elif sentiment == "NEGATIVE":
        return "neg"
    elif sentiment == "NEUTRAL":
        return "neu"
    else:
        return ""

def get_score_tag(score):
    if score >= 0.7:
        return "score_high"
    elif score >= 0.5:
        return "score_med"
    else:
        return "score_low"

def correct_prediction():
    global corrected_label, correction_target_selected

    if current_toot:
        dialog = CorrectionDialog(root, title="Correct Prediction")

        if dialog.corrected_label:
            corrected_label = dialog.corrected_label
            correction_target_selected = dialog.corrected_target.get()
            sentiment_label.config(text=f"Corrected {correction_target_selected} to: {corrected_label}", fg="blue")

def save_prediction():
    if current_toot:
        file_exists = os.path.isfile("annotations.csv")

        final_label = corrected_label if corrected_label else current_toot["prep_sentiment"]
        corrected_on = correction_target_selected if corrected_label else ""

        with open("annotations.csv", mode="a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow([
                    "original_text", "preprocessed_text",
                    "orig_sentiment", "orig_score",
                    "prep_sentiment", "prep_score",
                    "corrected_label", "corrected_on"
                ])

            writer.writerow([
                current_toot["original"],
                current_toot["orig_sentiment"],
                current_toot["orig_score"],
                current_toot["preprocessed"],
                current_toot["prep_sentiment"],
                current_toot["prep_score"],
                corrected_label if corrected_label else "",
                corrected_on
            ])

        sentiment_label.config(text="Saved", fg="green")

style = ttk.Style()
style.theme_use("clam")
style.configure("Custom.TButton",
    font=("Helvetica", 12),
    padding=10,
    foreground="black",
    background="#FFCC00"
)

button_row = tk.Frame(frame, bg="#ffffff")
button_row.grid(row=3, column=0, pady=(10, 0), sticky="n")

next_button = ttk.Button(button_row, text="Next", command=show_next,style="Custom.TButton")
next_button.pack(side="left", padx=5)

correct_button = ttk.Button(button_row, text="Correct", command=correct_prediction, style="Custom.TButton")
correct_button.pack(side="left", padx=5)

correction_label = tk.Label(frame, text="Which prediction do you want to correct?", bg="#ffffff")
correction_label.grid(row=6, column=0, sticky="w", pady=(10, 0))

save_button = ttk.Button(button_row, text="Save", command=save_prediction, style="Custom.TButton")
save_button.pack(side="left", padx=5)

legend_frame = tk.Frame(frame, bg="#ffffff")
legend_frame.grid(row=2, column=0, sticky="w", pady=(5, 5))

sentiment_legend = tk.Frame(legend_frame, bg="#ffffff")
sentiment_legend.pack(anchor="w")

tk.Label(sentiment_legend, text="Positive", fg="#2e7d32", bg="#ffffff", font=("Helvetica", 10)).pack(side="left", padx=10)
tk.Label(sentiment_legend, text="Neutral", fg="#ef6c00", bg="#ffffff", font=("Helvetica", 10)).pack(side="left", padx=10)
tk.Label(sentiment_legend, text="Negative", fg="#c62828", bg="#ffffff", font=("Helvetica", 10)).pack(side="left", padx=10)

score_legend = tk.Frame(legend_frame, bg="#ffffff")
score_legend.pack(anchor="w", pady=(3, 0))

tk.Label(score_legend, text="High (≥ 70%)", fg="#2e7d32", bg="#ffffff", font=("Helvetica", 10)).pack(side="left", padx=10)
tk.Label(score_legend, text="Medium (50-70%)", fg="#ef6c00", bg="#ffffff", font=("Helvetica", 10)).pack(side="left", padx=10)
tk.Label(score_legend, text="Low (< 50%)", fg="#c62828", bg="#ffffff", font=("Helvetica", 10)).pack(side="left", padx=10)

root.mainloop()