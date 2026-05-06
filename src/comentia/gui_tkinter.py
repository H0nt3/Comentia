#!/usr/bin/env python3
"""Interfaz gráfica con tkinter para Comentia."""

import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import time
from pathlib import Path
from .core import (extraer_id_noticia, descargar_comentarios,
                   exportar_comentarios, generar_estadisticas_txt)


class SelectorDirectorio:
    """Selector gráfico de directorio."""

    def __init__(self, root):
        self.root = root
        self.ruta_seleccionada = None

    def mostrar(self, callback):
        """Muestra la ventana de selección."""
        self.ventana = tk.Toplevel(self.root)
        self.ventana.title("Comentia - Seleccionar directorio")
        self.ventana.geometry("500x360")
        self.ventana.resizable(False, False)
        self.ventana.configure(bg='#2b2b2b')
        self.ventana.transient(self.root)
        self.ventana.grab_set()

        # Centrar
        self.ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (320 // 2)
        self.ventana.geometry(f"+{x}+{y}")

        # Título
        titulo = tk.Label(self.ventana, text="📝 Comentia",
                         font=('Arial', 18, 'bold'), bg='#2b2b2b', fg='white')
        titulo.pack(pady=(20, 5))

        subtitulo = tk.Label(self.ventana, text="Extractor de comentarios de Marca.com",
                            font=('Arial', 10), bg='#2b2b2b', fg='#888')
        subtitulo.pack(pady=(0, 20))

        # Botones
        btn_frame = tk.Frame(self.ventana, bg='#2b2b2b')
        btn_frame.pack(pady=8)
        btn_seleccionar = tk.Button(btn_frame, text="📁 Seleccionar carpeta",
                                   command=self._seleccionar, width=30, height=2,
                                   bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
        btn_seleccionar.pack()

        btn_frame2 = tk.Frame(self.ventana, bg='#2b2b2b')
        btn_frame2.pack(pady=8)
        btn_actual = tk.Button(btn_frame2, text="💾 Carpeta actual",
                              command=lambda: self._usar_actual(callback), width=30, height=2,
                              bg='#2196F3', fg='white', font=('Arial', 10))
        btn_actual.pack()

        btn_frame3 = tk.Frame(self.ventana, bg='#2b2b2b')
        btn_frame3.pack(pady=8)
        btn_escritorio = tk.Button(btn_frame3, text="🖥️ Escritorio (carpeta Comentia)",
                                  command=lambda: self._usar_escritorio(callback), width=30, height=2,
                                  bg='#FF9800', fg='white', font=('Arial', 10))
        btn_escritorio.pack()

        btn_frame4 = tk.Frame(self.ventana, bg='#2b2b2b')
        btn_frame4.pack(pady=8)
        btn_cancelar = tk.Button(btn_frame4, text="❌ Cancelar",
                                command=self._cancelar, width=30, height=2,
                                bg='#f44336', fg='white', font=('Arial', 10))
        btn_cancelar.pack()

    def _seleccionar(self):
        directorio = filedialog.askdirectory(title="Selecciona dónde guardar")
        if directorio:
            self.ruta_seleccionada = Path(directorio)
            self.ventana.destroy()

    def _usar_actual(self, callback):
        self.ruta_seleccionada = Path.cwd()
        self.ventana.destroy()
        callback(self.ruta_seleccionada)

    def _usar_escritorio(self, callback):
        import os
        if os.name == 'nt':
            escritorio = Path.home() / "Desktop"
        else:
            escritorio = Path.home() / "Desktop"
            if not escritorio.exists():
                escritorio = Path.home() / "Escritorio"
        self.ruta_seleccionada = escritorio / "Comentia_comentarios"
        self.ventana.destroy()
        callback(self.ruta_seleccionada)

    def _cancelar(self):
        self.ruta_seleccionada = None
        self.ventana.destroy()


class AplicacionComentia:
    """Aplicación principal con tkinter."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Comentia - Extractor de comentarios")
        self.root.geometry("650x550")
        self.root.resizable(False, False)
        self.root.configure(bg='#2b2b2b')
        self.directorio = None
        self._setup_ui()
        self.root.mainloop()

    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.root.winfo_screenheight() // 2) - (550 // 2)
        self.root.geometry(f"+{x}+{y}")

        # Título
        titulo = tk.Label(self.root, text="📝 Comentia",
                         font=('Arial', 24, 'bold'), bg='#2b2b2b', fg='white')
        titulo.pack(pady=(20, 5))

        subtitulo = tk.Label(self.root, text="Extractor de comentarios de Marca.com",
                            font=('Arial', 10), bg='#2b2b2b', fg='#888')
        subtitulo.pack(pady=(0, 20))

        # Marco de directorio
        frame_dir = tk.LabelFrame(self.root, text="📁 Directorio de destino",
                                  bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        frame_dir.pack(fill='x', padx=20, pady=10)

        self.label_dir = tk.Label(frame_dir, text="Ninguna carpeta seleccionada",
                                 bg='#3c3c3c', fg='white', anchor='w',
                                 padx=10, pady=8, font=('Arial', 9))
        self.label_dir.pack(side='left', fill='x', expand=True, padx=10, pady=10)

        btn_dir = tk.Button(frame_dir, text="Seleccionar", command=self._seleccionar_directorio,
                           bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'), padx=15)
        btn_dir.pack(side='right', padx=10, pady=10)

        # Marco de URL
        frame_url = tk.LabelFrame(self.root, text="🔗 URL de la noticia",
                                  bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        frame_url.pack(fill='x', padx=20, pady=10)

        self.entry_url = tk.Entry(frame_url, font=('Arial', 11), bg='#3c3c3c',
                                 fg='white', insertbackground='white')
        self.entry_url.pack(fill='x', padx=10, pady=10)
        self.entry_url.insert(0, "https://www.marca.com/...")

        # Botón extraer
        self.btn_extraer = tk.Button(self.root, text="🚀 Extraer comentarios",
                                    command=self._iniciar_extraccion,
                                    bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'),
                                    height=2, state='disabled')
        self.btn_extraer.pack(fill='x', padx=20, pady=10)

        # Barra de progreso
        self.progress = tk.ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill='x', padx=20, pady=5)
        self.progress.pack_forget()

        # Área de log
        frame_log = tk.LabelFrame(self.root, text="📄 Progreso",
                                  bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        frame_log.pack(fill='both', expand=True, padx=20, pady=10)

        self.log_text = tk.Text(frame_log, height=12, bg='#1e1e1e', fg='#d4d4d4',
                               font=('Courier', 9), wrap='word')
        scrollbar = tk.Scrollbar(frame_log, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

        # Estado
        self.status_label = tk.Label(self.root, text="✅ Listo",
                                    bg='#2b2b2b', fg='#4CAF50', font=('Arial', 9))
        self.status_label.pack(pady=(0, 15))

    def _seleccionar_directorio(self):
        selector = SelectorDirectorio(self.root)
        selector.mostrar(self._actualizar_directorio)

    def _actualizar_directorio(self, directorio):
        self.directorio = directorio
        self.label_dir.config(text=str(directorio))
        self.btn_extraer.config(state='normal')
        self._log("✅ Carpeta seleccionada: " + str(directorio))

    def _log(self, mensaje):
        self.log_text.insert('end', mensaje + '\n')
        self.log_text.see('end')
        self.root.update_idletasks()

    def _iniciar_extraccion(self):
        url = self.entry_url.get().strip()
        if not url or url == "https://www.marca.com/...":
            messagebox.showerror("Error", "Introduce una URL válida")
            return

        noticia_id = extraer_id_noticia(url)
        if not noticia_id:
            messagebox.showerror("Error", "No se pudo extraer el ID de la noticia")
            return

        self.btn_extraer.config(state='disabled')
        self.progress.pack(fill='x', padx=20, pady=5)
        self.progress['value'] = 0
        self.status_label.config(text="⏳ Extrayendo comentarios...", fg='#FF9800')
        self._log(f"✅ ID detectado: {noticia_id}")

        # Ejecutar en segundo plano (simulado, aquí iría un hilo)
        self.root.after(100, lambda: self._ejecutar_extraccion(noticia_id, url))

    def _ejecutar_extraccion(self, noticia_id, url_original):
        subdir = self.directorio / f"noticia_{noticia_id}"
        subdir.mkdir(exist_ok=True)

        tiempo_inicio = time.time()
        comentarios_dict, total_esperado, errores = descargar_comentarios(noticia_id)
        tiempo_ejecucion = time.time() - tiempo_inicio

        exportar_comentarios(comentarios_dict, noticia_id, subdir, url_original)
        generar_estadisticas_txt(noticia_id, url_original, comentarios_dict,
                                total_esperado, tiempo_ejecucion, subdir, errores)

        exito = len(comentarios_dict) >= total_esperado * 0.95 if total_esperado > 0 else len(comentarios_dict) > 0
        if exito:
            self.status_label.config(text=f"✅ ¡Éxito! {len(comentarios_dict)}/{total_esperado} comentarios", fg='#4CAF50')
            messagebox.showinfo("Completado", f"✅ Extracción finalizada\n\n{len(comentarios_dict)} comentarios guardados\n📁 {subdir}")
        else:
            self.status_label.config(text=f"⚠️ {len(comentarios_dict)}/{total_esperado} comentarios", fg='#f44336')
            messagebox.showwarning("Errores", f"⚠️ Extracción con errores\n\n{len(comentarios_dict)}/{total_esperado} comentarios")

        self.btn_extraer.config(state='normal')
        self.progress.pack_forget()


def main_gui():
    """Función principal para iniciar la GUI."""
    AplicacionComentia()


if __name__ == "__main__":
    main_gui()