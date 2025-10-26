import sys
import os
import time
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
from tkinter import ttk

# --- ustawienie wbudowanego ffmpeg ---
if getattr(sys, "frozen", False):
    ffmpeg_path = os.path.join(sys._MEIPASS, "ffmpeg.exe")
else:
    ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")

if not os.path.isfile(ffmpeg_path):
    raise FileNotFoundError(f"Nie znaleziono ffmpeg.exe pod ścieżką: {ffmpeg_path}")


class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MKV → MP4 Konwerter")
        self.root.geometry("520x340")
        self.root.resizable(False, False)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()

        # Wybór pliku MKV
        tk.Label(root, text="Wybierz plik MKV:").pack(pady=5)
        tk.Entry(root, textvariable=self.input_path, width=65).pack(pady=2)
        tk.Button(root, text="Przeglądaj", command=self.select_input).pack(pady=2)

        # Wybór miejsca zapisu MP4
        tk.Label(root, text="Zapisz jako MP4:").pack(pady=5)
        tk.Entry(root, textvariable=self.output_path, width=65).pack(pady=2)
        tk.Button(root, text="Wskaż miejsce zapisu", command=self.select_output).pack(pady=2)

        # Pasek postępu
        self.progress = ttk.Progressbar(root, orient="horizontal", length=450, mode="determinate")
        self.progress.pack(pady=10)

        # Procent i licznik czasu
        self.progress_label = tk.Label(root, text="0% | 00:00 / 00:00")
        self.progress_label.pack()

        # Start button
        self.start_button = tk.Button(
            root,
            text="Rozpocznij konwersję",
            command=self.start_conversion,
            font=("Arial", 14, "bold")
        )
        self.start_button.pack(pady=10)

    def select_input(self):
        path = filedialog.askopenfilename(filetypes=[("Pliki MKV", "*.mkv")])
        if path:
            self.input_path.set(path)

    def select_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("Pliki MP4", "*.mp4")])
        if path:
            self.output_path.set(path)

    def start_conversion(self):
        input_file = self.input_path.get()
        output_file = self.output_path.get()

        if not input_file or not output_file:
            messagebox.showwarning("Błąd", "Wybierz plik źródłowy i miejsce zapisu!")
            return
        if not os.path.isfile(input_file):
            messagebox.showerror("Błąd", f"Nie znaleziono pliku MKV:\n{input_file}")
            return

        self.start_button.config(state=tk.DISABLED)
        Thread(target=self.convert_ffmpeg, args=(input_file, output_file)).start()

    def convert_ffmpeg(self, input_file, output_file):
        try:
            # Przygotowanie pliku logu
            log_file = os.path.splitext(output_file)[0] + ".log"

            cmd = [
                ffmpeg_path,
                "-y",
                "-i", input_file,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-strict", "experimental",
                output_file
            ]

            with open(log_file, "w", encoding="utf-8") as log:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

                start_time = time.time()
                while True:
                    line = process.stdout.readline()
                    if line == "" and process.poll() is not None:
                        break

                    log.write(line)
                    log.flush()

                    # Szacowanie postępu na podstawie czasu
                    elapsed = time.time() - start_time
                    percent = min(elapsed / 10 * 100, 100)  # przybliżone
                    self.progress["value"] = percent
                    elapsed_min = int(elapsed // 60)
                    elapsed_sec = int(elapsed % 60)
                    self.progress_label.config(
                        text=f"{int(percent)}% | {elapsed_min:02d}:{elapsed_sec:02d} / ?"
                    )
                    self.root.update_idletasks()
                    time.sleep(0.05)

                process.wait()
                log.write(f"\nReturn code: {process.returncode}\n")
                log.flush()

            if process.returncode != 0:
                messagebox.showerror("Błąd", f"FFmpeg zakończył się błędem!\nZobacz log: {log_file}")
            elif not os.path.isfile(output_file):
                messagebox.showerror("Błąd", f"Nie udało się utworzyć pliku MP4.\nLog: {log_file}")
            else:
                self.progress["value"] = 100
                self.progress_label.config(text="100% | koniec")
                messagebox.showinfo("Sukces", f"Plik MP4 utworzony:\n{output_file}")

        except Exception as e:
            messagebox.showerror("Błąd", f"Coś poszło nie tak:\n{e}\nLog: {log_file}")
        finally:
            self.start_button.config(state=tk.NORMAL)
            self.progress["value"] = 0
            self.progress_label.config(text="0% | 00:00")


if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
