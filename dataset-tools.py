import tkinter as tk
from tkinter import ttk, messagebox
import json
import argilla as rg
import os

# Konfigurasi Default (Berdasarkan script asli)
API_URL = "http://localhost:6900"
API_KEY = "FjMn6IAgKw6nKAzEYhgHlZBHCUc8p4osPJBjJSgBPllzpoE230cJiVto3KcPBLhVnTXBQiYkzDwReUW6E7h0C4Ej5i7yg4iKDwNZV0aDvDs"
WORKSPACE = "elaina_workspace"
DATASET_NAME = "Elaina-Finetuning"

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
        self.title("Elaina ChatML Dataset Creator")
        self.geometry("900x600")
        self.configure(bg="#4c6b8c") # Warna background biru-abu sesuai sketsa

        # State Penyimpanan Dataset
        # Percakapan selalu diawali dengan system prompt
        self.conversations = [self.create_new_conversation()]
        self.current_index = 0

        self.setup_ui()
        self.refresh_preview()

    def create_new_conversation(self):
        """Membuat template row percakapan baru dengan system prompt bawaan."""
        return [{"role": "system", "content": SYSTEM_PROMPT}]

    def setup_ui(self):
        # ==========================================
        # 1. Bagian Atas: Preview Percakapan (Gray)
        # ==========================================
        self.preview_frame = tk.Frame(self, bg="#cccccc", padx=10, pady=10)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 10))

        # Menggunakan Text widget agar mudah di-scroll dan format warnanya
        self.preview_text = tk.Text(
            self.preview_frame, wrap=tk.WORD, font=("Arial", 12),
            bg="#cccccc", bd=0, highlightthickness=0, state=tk.DISABLED
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Tag untuk format chat bubble text
        self.preview_text.tag_configure("system", foreground="#555555", font=("Arial", 10, "italic"), justify="center", spacing3=10)
        self.preview_text.tag_configure("user", background="#6aa877", foreground="white", justify="right", lmargin1=150, rmargin=10, spacing1=5, spacing3=5)
        self.preview_text.tag_configure("assistant", background="#6aa877", foreground="white", justify="left", lmargin1=10, rmargin=150, spacing1=5, spacing3=5)

        # ==========================================
        # 2. Bagian Tengah: Toolbar Tombol (Quick Task)
        # ==========================================
        self.toolbar_frame = tk.Frame(self, bg="#4c6b8c")
        self.toolbar_frame.pack(fill=tk.X, padx=20, pady=5)

       # Tombol Orange (Export JSONL)
        self.btn_export = tk.Button(self.toolbar_frame, text="Export JSONL", bg="#ffa500", fg="black", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.export_jsonl)
        self.btn_export.pack(side=tk.LEFT, padx=(0, 20))

        # Status Label (Menunjukkan Row Percakapan ke-berapa)
        self.lbl_status = tk.Label(self.toolbar_frame, text="Row: 1/1", bg="#4c6b8c", fg="white", font=("Arial", 11, "bold"))
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # Tombol Ungu (Previous & Next)
        self.btn_prev = tk.Button(self.toolbar_frame, text="◄ Prev", bg="#8a2be2", fg="white", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.prev_conversation)
        self.btn_prev.pack(side=tk.LEFT, padx=5)
        
        self.btn_next = tk.Button(self.toolbar_frame, text="Next ►", bg="#8a2be2", fg="white", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.next_conversation)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        # Tombol Pink (Upload Argilla)
        self.btn_upload = tk.Button(self.toolbar_frame, text="Upload Argilla", bg="#ff69b4", fg="black", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.upload_to_argilla)
        self.btn_upload.pack(side=tk.LEFT, padx=20)

        # Tombol Biru (Add Dialog) & Selector Agent
        self.btn_add = tk.Button(self.toolbar_frame, text="Enter ↵", bg="#4169e1", fg="white", font=("Arial", 11, "bold"), bd=0, padx=10, pady=5, command=self.add_dialog)
        self.btn_add.pack(side=tk.RIGHT, padx=(5, 0))

        self.agent_var = tk.StringVar(value="user")
        self.dropdown_agent = ttk.Combobox(self.toolbar_frame, textvariable=self.agent_var, values=["user", "assistant", "system"], state="readonly", width=10, font=("Arial", 11))
        self.dropdown_agent.pack(side=tk.RIGHT, padx=5)

        # ==========================================
        # 3. Bagian Bawah: Input Teks Raw (Black)
        # ==========================================
        self.input_frame = tk.Frame(self, bg="black", padx=10, pady=10)
        self.input_frame.pack(fill=tk.X, padx=20, pady=(10, 20))

        # Menggunakan Entry agar tidak bisa multiline menggunakan tombol Enter, namun font tetap seragam
        self.entry_dialog = tk.Entry(self.input_frame, bg="black", fg="white", font=("Arial", 12), bd=0, insertbackground="white")
        self.entry_dialog.pack(fill=tk.X, ipady=15)
        
        # Binding tombol Enter di keyboard agar langsung submit dialog
        self.entry_dialog.bind("<Return>", lambda event: self.add_dialog())

    # --- FUNGSI LOGIKA ---

    def refresh_preview(self):
        """Memperbarui tampilan layar preview berdasarkan row percakapan saat ini."""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)

        current_conv = self.conversations[self.current_index]
        
        for msg in current_conv:
            role = msg["role"]
            content = msg["content"]
            
            # Format tampilan agar lebih rapih di mata
            if role == "system":
                display_text = f"[SYSTEM PROMPT]\n{content}\n\n"
            elif role == "user":
                display_text = f" User: {content} \n\n"
            else:
                display_text = f" Elaina: {content} \n\n"
            
            self.preview_text.insert(tk.END, display_text, role)

        self.preview_text.config(state=tk.DISABLED)
        self.preview_text.see(tk.END) # Auto scroll ke bawah
        self.lbl_status.config(text=f"Row: {self.current_index + 1}/{len(self.conversations)}")

    def add_dialog(self):
        """Menambahkan raw text ke dalam percakapan saat ini dan merender newline."""
        raw_text = self.entry_dialog.get()
        if not raw_text.strip():
            return
            
        role = self.agent_var.get()
        # Mengubah karakter literal '\n' yang diketik user menjadi newline betulan (\n)
        formatted_text = raw_text.replace("\\n", "\n")
        
        self.conversations[self.current_index].append({
            "role": role,
            "content": formatted_text
        })
        
        self.entry_dialog.delete(0, tk.END)
        self.refresh_preview()
        
        # Ganti role otomatis setelah user input agar lebih efisien (ping-pong)
        if role == "user":
            self.agent_var.set("assistant")
        elif role == "assistant":
            self.agent_var.set("user")

    def prev_conversation(self):
        """Mundur ke row percakapan sebelumnya."""
        if self.current_index > 0:
            self.current_index -= 1
            self.refresh_preview()

    def next_conversation(self):
        """Maju ke row percakapan berikutnya. Buat baru jika belum ada."""
        if self.current_index == len(self.conversations) - 1:
            # Otomatis membuat template baru dengan system prompt
            self.conversations.append(self.create_new_conversation())
        
        self.current_index += 1
        self.agent_var.set("user") # Reset role selector
        self.refresh_preview()

    def export_jsonl(self):
        """Menulis dataset yang ada di memori ke dalam file JSONL yang rapi."""
        try:
            filename = "elaina_exported_dataset.jsonl"
            with open(filename, "w", encoding="utf-8") as f:
                for conv in self.conversations:
                    # Filter percakapan yang hanya berisi system prompt tanpa dialog lain
                    if len(conv) > 1: 
                        json_line = json.dumps({"messages": conv}, ensure_ascii=False)
                        f.write(json_line + "\n")
            
            messagebox.showinfo("Export Berhasil", f"Dataset berhasil disimpan ke:\n{os.path.abspath(filename)}")
        except Exception as e:
            messagebox.showerror("Error Export", f"Gagal mengekspor file:\n{str(e)}")

    def upload_to_argilla(self):
        """Mengunggah dataset ke Argilla sesuai dengan script asli Anda."""
        if not messagebox.askyesno("Konfirmasi Upload", "Apakah Anda yakin ingin menghapus dataset lama di Argilla dan mengupload dataset ini?"):
            return

        try:
            # 1. Connect to Argilla
            client = rg.Argilla(api_url=API_URL, api_key=API_KEY)
            
            # 2. Hapus Dataset Lama
            existing_dataset = client.datasets(name=DATASET_NAME, workspace=WORKSPACE)
            if existing_dataset:
                existing_dataset.delete()

            # 3. Setting Dataset
            settings = rg.Settings(
                fields=[
                    rg.ChatField(name="messages", title="Elaina Roleplay Logs")
                ],
                questions=[
                    rg.LabelQuestion(
                        name="quality", 
                        title="How accurate is Elaina's characterization?", 
                        labels=["Perfect (In-Character)", "Acceptable", "Bad (Out-of-Character)"]
                    ),
                    rg.TextQuestion(
                        name="correction",
                        title="Write dialogue/narration corrections here (Optional):",
                        required=False,
                        use_markdown=True
                    )
                ]
            )

            # 4. Buat Dataset Baru
            dataset = rg.Dataset(name=DATASET_NAME, workspace=WORKSPACE, settings=settings)
            dataset.create()

            # 5. Format Data & Upload
            valid_records = []
            for conv in self.conversations:
                # Hanya upload percakapan yang punya interaksi (lebih dari sekadar system prompt)
                if len(conv) > 1:
                    valid_records.append({"messages": conv})

            if valid_records:
                dataset.records.log(valid_records)
                messagebox.showinfo("Upload Berhasil", f"✅ Dataset bahasa Inggris '{DATASET_NAME}' berhasil diupload!\nTotal baris percakapan: {len(valid_records)}")
            else:
                messagebox.showwarning("Dataset Kosong", "Tidak ada dialog yang dimasukkan. Hanya ada system prompt.")

        except Exception as e:
            messagebox.showerror("Argilla Connection Error", f"Terjadi kesalahan saat mengunggah ke sistem Argilla:\n\n{str(e)}\n\nPastikan server lokal argilla berjalan di {API_URL}.")

if __name__ == "__main__":
    app = ElainaDatasetCreator()
    app.mainloop()