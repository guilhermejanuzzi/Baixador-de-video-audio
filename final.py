#py -m PyInstaller --onefile --noconsole final.py
import customtkinter as ctk
import yt_dlp
import threading
import datetime
from tkinter import filedialog
import os
import re
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def caminho_ffmpeg():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "ffmpeg.exe")

CAMINHO_FFMPEG = caminho_ffmpeg()

def tem_ffmpeg():
    return os.path.exists(CAMINHO_FFMPEG)



def limpar_ansi(texto):
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

def progresso(d, log):
    if d['status'] == 'downloading':
        percent = limpar_ansi(d.get('_percent_str', '0%'))
        speed = limpar_ansi(d.get('_speed_str', 'N/A'))
        eta = limpar_ansi(d.get('_eta_str', 'N/A'))
        log(f"⬇️ {percent} | {speed} | ETA: {eta}")
    elif d['status'] == 'finished':
        log("✨ Finalizando...")

def baixar_arquivo(url, caminho, log, formato="video"):
    if not tem_ffmpeg():
        log(f"❌ ffmpeg NÃO encontrado em: {CAMINHO_FFMPEG}")
        return False

    if formato == "video":
        opcoes = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": caminho,
            "merge_output_format": "mp4",
            "ffmpeg_location": CAMINHO_FFMPEG,
            "noplaylist": True,
            "progress_hooks": [lambda d: progresso(d, log)]
        }

        log("🎬 Baixando na melhor qualidade possível...")

        try:
            with yt_dlp.YoutubeDL(opcoes) as ydl:
                info = ydl.extract_info(url, download=False)

                formatos = [f for f in info.get('formats', []) if f.get('height')]
                if formatos:
                    melhor = max(formatos, key=lambda x: x.get('height', 0))
                    log(f"📺 Melhor: {melhor.get('height')}p | {melhor.get('vcodec')}")

                ydl.download([url])
                log("✅ Concluído!")
                return True

        except Exception as e:
            log(f"❌ Erro: {str(e)}")
            return False

    else:
        opcoes = {
            "format": "bestaudio/best",
            "outtmpl": caminho,
            "ffmpeg_location": CAMINHO_FFMPEG,
            "progress_hooks": [lambda d: progresso(d, log)]
        }

        try:
            with yt_dlp.YoutubeDL(opcoes) as ydl:
                ydl.download([url])
            log("🎵 Áudio concluído!")
            return True
        except Exception as e:
            log(f"❌ Erro áudio: {str(e)}")
            return False

def salvar_historico(url, tipo="video"):
    data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("historico_downloads.txt", "a", encoding="utf-8") as f:
        f.write(f"{data} | {tipo.upper()} | MELHOR QUALIDADE | {url}\n")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x650")

        status = "ffmpeg OK" if tem_ffmpeg() else "ffmpeg NÃO encontrado"
        self.title(f"Baixador - {status}")

        self.log_box = ctk.CTkTextbox(self, height=180)
        self.log_box.pack(fill="x", padx=10, pady=(10,5))

        container = ctk.CTkFrame(self)
        container.pack(expand=True, fill="both", padx=10, pady=5)

        self.frame_video = ctk.CTkFrame(container)
        self.frame_video.pack(side="left", expand=True, fill="both", padx=(0,10))

        self.frame_audio = ctk.CTkFrame(container)
        self.frame_audio.pack(side="right", expand=True, fill="both", padx=(10,0))

        self.criar_secao(self.frame_video, "VÍDEO", "video")
        self.criar_secao(self.frame_audio, "ÁUDIO", "audio")

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="Limpar", command=self.limpar_log).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Histórico", command=self.ver_historico).pack(side="right", padx=5)

    def log(self, texto):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {texto}\n")
        self.log_box.see("end")

    def limpar_log(self):
        self.log_box.delete("1.0", "end")
        self.log("Pronto!")

    def criar_secao(self, frame, titulo, modo):
        ctk.CTkLabel(frame, text=titulo, font=("Arial", 22, "bold")).pack(pady=20)

        for i in range(4): 
            linha = ctk.CTkFrame(frame)
            linha.pack(pady=10, padx=20, fill="x")

            entry = ctk.CTkEntry(linha, placeholder_text=f"URL {i+1}")
            entry.pack(side="left", expand=True, fill="x", padx=(0,10))

            btn = ctk.CTkButton(
                linha,
                text="⬇️ Baixar",
                command=lambda e=entry, m=modo: self.iniciar_download(e.get(), m)
            )
            btn.pack(side="right")

    def iniciar_download(self, url, modo):
        if not url.strip():
            self.log("URL vazia!")
            return

        thread = threading.Thread(target=self.processar_download, args=(url, modo))
        thread.daemon = True
        thread.start()

        self.log("Iniciando download...")

    def processar_download(self, url, modo):
        ext = ".mp4" if modo == "video" else ".m4a"

        caminho = filedialog.asksaveasfilename(defaultextension=ext)

        if not caminho:
            self.log("Cancelado")
            return

        self.log(f"📁 FFMPEG caminho: {CAMINHO_FFMPEG}")
        self.log(f"📁 Existe? {os.path.exists(CAMINHO_FFMPEG)}")

        sucesso = baixar_arquivo(url, caminho, self.log, modo)

        if sucesso:
            salvar_historico(url, modo)
            self.log("Download finalizado!")

    def ver_historico(self):
        try:
            with open("historico_downloads.txt", "r", encoding="utf-8") as f:
                conteudo = f.read()
        except:
            conteudo = "Nenhum download ainda!"

        janela = ctk.CTkToplevel(self)
        janela.title("Histórico")
        janela.geometry("800x500")

        txt = ctk.CTkTextbox(janela)
        txt.pack(fill="both", expand=True, padx=20, pady=20)
        txt.insert("end", conteudo)

if __name__ == "__main__":
    app = App()
    app.mainloop()