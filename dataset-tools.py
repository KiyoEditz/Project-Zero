import tkinter as tk
from tkinter import ttk, messagebox
import json
import argilla as rg
import os

# Konfigurasi Default
API_URL = "http://localhost:6900"
API_KEY = "FjMn6IAgKw6nKAzEYhgHlZBHCUc8p4osPJBjJSgBPllzpoE230cJiVto3KcPBLhVnTXBQiYkzDwReUW6E7h0C4Ej5i7yg4iKDwNZV0aDvDs"
WORKSPACE = "elaina_workspace"
DATASET_NAME = "Elaina-Finetuning"
AUTOSAVE_FILE = "elaina_session_autosave.json" # File untuk menyimpan sesi

SYSTEM_PROMPT = (
    "You are Elaina, the Ashen Witch. You are 18 years old. "
    "You have ash-gray hair and azure blue eyes. You absolutely love money and Croissants, "
    "but you deeply despise mushrooms. You are generally polite, but can be quite arrogant, "
    "greedy when it comes to money, tsundere, and somewhat cold towards men. "
    "IMPORTANT: Always use roleplay actions or facial expressions enclosed in asterisks "
    "(e.g., *smiles arrogantly* or *crosses my arms*) to describe your actions. "
    "Maintain your persona and occasionally use your catchphrase 'Sou, Watashi desu' (Yes, that is me)."
)

class ElainaDatasetCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Elaina ChatML Dataset Creator - Session Persistence")
        self.geometry("900x600")
        self.configure(bg="#4c6b8c")

        # Inisialisasi State
        self.conversations = []
        self.current_index = 0
        
        # Muat sesi sebelumnya jika ada
        self.load_session()

        self.setup_ui()
        self.refresh_preview()

        # Binding untuk menyimpan saat aplikasi ditutup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_new_conversation(self):
        return [{"role": "system", "content": SYSTEM_PROMPT}]

    def load_session(self):
        """Memuat data dari file JSON autosave jika tersedia."""
        if os.path.exists(AUTOSAVE_FILE):
            try:
                with open(AUTOSAVE_FILE, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f) # Baca sebagai JSON utuh
                    
                    if loaded_data:
                        # Ekstrak kembali hanya bagian "messages" agar sesuai dengan logika memori aplikasi
                        self.conversations = [item["messages"] for item in loaded_data]
                        self.current_index = len(self.conversations) - 1
                        print(f"🔄 Sesi berhasil dimuat: {len(self.conversations)} percakapan.")
                        return
            except Exception as e:
                print(f"⚠️ Gagal memuat sesi: {e}")
        
        self.conversations = [self.create_new_conversation()]
        self.current_index = 0

    def save_session(self):
        """Menyimpan progres ke file JSON dengan format rapi (indent=4) dan metadata."""
        try:
            data_to_save = []
            for i, conv in enumerate(self.conversations):
                # Simpan jika ada dialog, atau jika ini satu-satunya baris
                if len(conv) > 1 or len(self.conversations) == 1:
                    data_to_save.append({
                        "messages": conv,
                        "metadata": {"urutan": i + 1}
                    })

            with open(AUTOSAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            print("💾 Sesi berhasil disimpan secara otomatis (JSON Format Rapi).")
        except Exception as e:
            print(f"⚠️ Gagal menyimpan sesi: {e}")

    def on_closing(self):
        """Prosedur saat jendela ditutup."""
        self.save_session()
        self.destroy()

    def setup_ui(self):
        # 1. Preview Frame
        self.preview_frame = tk.Frame(self, bg="#cccccc", padx=10, pady=10)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 10))

        self.preview_text = tk.Text(
            self.preview_frame, wrap=tk.WORD, font=("Arial", 12),
            bg="#cccccc", bd=0, highlightthickness=0, state=tk.DISABLED
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        self.preview_text.tag_configure("system", foreground="#555555", font=("Arial", 10, "italic"), justify="center", spacing3=10)
        self.preview_text.tag_configure("user", background="#6aa877", foreground="white", justify="right", lmargin1=150, rmargin=10, spacing1=5, spacing3=5)
        self.preview_text.tag_configure("assistant", background="#6aa877", foreground="white", justify="left", lmargin1=10, rmargin=150, spacing1=5, spacing3=5)

        # 2. Toolbar Frame (Perbaikan padx/pady di sini)
        self.toolbar_frame = tk.Frame(self, bg="#4c6b8c")
        self.toolbar_frame.pack(fill=tk.X, padx=20, pady=5)

        self.btn_export = tk.Button(self.toolbar_frame, text="Export JSONL", bg="#ffa500", fg="black", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.export_jsonl)
        self.btn_export.pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_status = tk.Label(self.toolbar_frame, text="Row: 1/1", bg="#4c6b8c", fg="white", font=("Arial", 11, "bold"))
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        self.btn_prev = tk.Button(self.toolbar_frame, text="◄ Prev", bg="#8a2be2", fg="white", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.prev_conversation)
        self.btn_prev.pack(side=tk.LEFT, padx=5)
        
        self.btn_next = tk.Button(self.toolbar_frame, text="Next ►", bg="#8a2be2", fg="white", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.next_conversation)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        self.btn_upload = tk.Button(self.toolbar_frame, text="Upload Argilla", bg="#ff69b4", fg="black", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.upload_to_argilla)
        self.btn_upload.pack(side=tk.LEFT, padx=20)

        self.btn_add = tk.Button(self.toolbar_frame, text="Enter ↵", bg="#4169e1", fg="white", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.add_dialog)
        self.btn_add.pack(side=tk.RIGHT, padx=(5, 0))

        self.agent_var = tk.StringVar(value="user")
        self.dropdown_agent = ttk.Combobox(self.toolbar_frame, textvariable=self.agent_var, values=["user", "assistant", "system"], state="readonly", width=10, font=("Arial", 11))
        self.dropdown_agent.pack(side=tk.RIGHT, padx=5)

        # 3. Input Frame
        self.input_frame = tk.Frame(self, bg="black", padx=10, pady=10)
        self.input_frame.pack(fill=tk.X, padx=20, pady=(10, 20))

        self.entry_dialog = tk.Entry(self.input_frame, bg="black", fg="white", font=("Arial", 12), bd=0, insertbackground="white")
        self.entry_dialog.pack(fill=tk.X, ipady=15)
        self.entry_dialog.bind("<Return>", lambda event: self.add_dialog())

    def refresh_preview(self):
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)

        if not self.conversations:
            return

        current_conv = self.conversations[self.current_index]
        for msg in current_conv:
            role = msg["role"]
            content = msg["content"]
            display_text = f" {role.upper()}: {content} \n\n"
            self.preview_text.insert(tk.END, display_text, role)

        self.preview_text.config(state=tk.DISABLED)
        self.preview_text.see(tk.END)
        self.lbl_status.config(text=f"Row: {self.current_index + 1}/{len(self.conversations)}")

    def add_dialog(self):
        raw_text = self.entry_dialog.get()
        if not raw_text.strip(): return
            
        role = self.agent_var.get()
        formatted_text = raw_text.replace("\\n", "\n")
        
        self.conversations[self.current_index].append({"role": role, "content": formatted_text})
        self.entry_dialog.delete(0, tk.END)
        self.refresh_preview()
        
        if role == "user": self.agent_var.set("assistant")
        elif role == "assistant": self.agent_var.set("user")
        
        # Simpan sesi setiap ada perubahan
        self.save_session()

    def prev_conversation(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.refresh_preview()

    def next_conversation(self):
        if self.current_index == len(self.conversations) - 1:
            self.conversations.append(self.create_new_conversation())
        
        self.current_index += 1
        self.agent_var.set("user")
        self.refresh_preview()
        self.save_session()

    def export_jsonl(self):
        try:
            filename = "elaina_exported_dataset.jsonl"
            with open(filename, "w", encoding="utf-8") as f:
                for conv in self.conversations:
                    if len(conv) > 1: 
                        f.write(json.dumps({"messages": conv}, ensure_ascii=False) + "\n")
            messagebox.showinfo("Export Berhasil", f"Dataset disimpan di:\n{os.path.abspath(filename)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def upload_to_argilla(self):
        # Logika upload tetap sama dengan sebelumnya
        if not messagebox.askyesno("Konfirmasi", "Upload ke Argilla?"): return
        try:
            client = rg.Argilla(api_url=API_URL, api_key=API_KEY)
            existing_dataset = client.datasets(name=DATASET_NAME, workspace=WORKSPACE)
            if existing_dataset: existing_dataset.delete()

            settings = rg.Settings(
                fields=[rg.ChatField(name="messages", title="Elaina Roleplay Logs")],
                questions=[
                    rg.LabelQuestion(name="quality", title="Accuracy?", labels=["Perfect", "Acceptable", "Bad"]),
                    rg.TextQuestion(name="correction", title="Correction?", required=False, use_markdown=True)
                ]
            )
            dataset = rg.Dataset(name=DATASET_NAME, workspace=WORKSPACE, settings=settings)
            dataset.create()

            valid_records = [{"messages": c} for c in self.conversations if len(c) > 1]
            if valid_records:
                dataset.records.log(valid_records)
                messagebox.showinfo("Sukses", "Data terunggah ke Argilla.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = ElainaDatasetCreator()
    app.mainloop()