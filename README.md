# 📝 Comentia

<div align="center">

![Versión](https://img.shields.io/badge/versión-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![Licencia](https://img.shields.io/badge/licencia-MIT-orange)
![Plataforma](https://img.shields.io/badge/plataforma-Windows%20%7C%20Linux%20%7C%20Mac-grey)

**Extrae todos los comentarios de cualquier noticia de Marca.com de forma sencilla y rápida**

[Español](#español) | [English](#english)

</div>

---

<a name="español"></a>

## 🇪🇸 Español

### 📖 ¿Qué es Comentia?

**Comentia** es una herramienta fácil de usar que te permite **descargar y guardar todos los comentarios** de cualquier noticia de **Marca.com** en tu ordenador.

¿Alguna vez has querido guardar los comentarios de una noticia polémica para leerlos más tarde? ¿O analizar los patrones de comportamiento de los usuarios? **Comentia** hace esto posible con solo **pegar la URL de la noticia**.

---

### ✨ Características principales

| Característica           | Descripción                                                                 |
| ------------------------ | --------------------------------------------------------------------------- |
| 🚀 **Sencillo**          | Solo necesitas la URL de la noticia                                         |
| 💾 **Guarda todo**       | Descarga **todos** los comentarios, incluso los que están en varias páginas |
| 📁 **Organización**      | Elige dónde guardar los archivos (con ventana gráfica)                      |
| 📊 **Estadísticas**      | Genera un informe completo con datos interesantes                           |
| 🔄 **Sin duplicados**    | Detecta y evita comentarios repetidos automáticamente                       |
| 🛡️ **Robusto**          | Reintenta automáticamente si hay errores de conexión                        |
| 🎨 **Interfaz amigable** | Versión gráfica (tkinter) y versión de consola                              |
| 📦 **Multiplataforma**   | Funciona en Windows, macOS y Linux                                          |

---

### 📋 Requisitos previos

* **Python 3.9 o superior** ([Descargar Python](https://www.python.org/downloads/)) *(solo para versión desde código fuente)*
* Conexión a internet
* Espacio en disco: ~10 MB

---

### 🚀 Instalación y uso

#### Opción 1: Desde el código fuente

```bash
# Clonar el repositorio
git clone https://github.com/tuusuario/comentia.git
cd comentia

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar (versión gráfica)
python -m comentia

# O versión de consola
python -m comentia --cli
```

#### Opción 2: Ejecutable independiente

Descarga el ejecutable desde **Releases**:

| Sistema Operativo | Archivo      | Ejecución    |
| ----------------- | ------------ | ------------ |
| Windows           | Comentia.exe | Doble click  |
| macOS             | Comentia.app | Doble click  |
| Linux             | Comentia     | `./Comentia` |

---

### 📖 Guía paso a paso

#### Paso 1: Obtener la URL

```
https://www.marca.com/futbol/real-madrid/2026/02/09/noticia-ejemplo.html
```

#### Paso 2: Ejecutar Comentia

```bash
python -m comentia
```

#### Paso 3: Seleccionar carpeta

* 📁 Seleccionar carpeta
* 💾 Carpeta actual
* 🖥️ Escritorio

#### Paso 4: Pegar la URL

```
📝 URL o ID de la noticia: https://www.marca.com/...
```

#### Paso 5: Esperar

```
⬇️ Descargando comentarios...
--------------------------------------------------
📄 Página 1... (Total esperado: 840 comentarios)
📄 Página 2... +25 | Total: 50/840 | █░░░░░░░░░░░░░░░░░░░ 6.0%
...
```

#### Paso 6: Archivos generados

```
noticia_123456789/
├── comentarios_123456789.json
├── comentarios_123456789_texto.json
└── comentarios_123456789_estadisticas.txt
```

---

### 📊 Estadísticas

```
COMENTIA - ESTADÍSTICAS DE COMENTARIOS

Total esperado: 840
Total obtenido: 838
Éxito: 99.76%
```

---

### 🛠️ Estructura JSON

#### Completo

```json
{
  "metadata": {
    "noticia_id": "4405498",
    "url_noticia": "https://...",
    "total_comentarios": 838
  },
  "comentarios": []
}
```

#### Simplificado

```json
[
  {
    "usuario": "Xenon2",
    "comentario": "..."
  }
]
```

---

### 📄 Licencia

MIT License

---

### 🙏 Créditos

Desarrollado con ❤️ para la comunidad de Marca.com

<div align="center">

⭐ Si Comentia te ha sido útil, ¡dale una estrella! ⭐

</div>

---

<a name="english"></a>

## 🇬🇧 English

### 📖 What is Comentia?

Comentia is an easy-to-use tool that lets you download and save all comments from any Marca.com article.

---

### ✨ Features

| Feature           | Description          |
| ----------------- | -------------------- |
| 🚀 Simple         | Just paste the URL   |
| 💾 Save all       | Downloads everything |
| 📊 Stats          | Generates reports    |
| 📦 Cross-platform | Works everywhere     |

---

### 📋 Requirements

* Python 3.9+
* Internet connection
* ~10MB disk space

---

### 🚀 Installation

```bash
git clone https://github.com/yourusername/comentia.git
cd comentia
pip install -r requirements.txt
python -m comentia
```

---

### 📄 License

MIT License

---

### 🙏 Credits

Developed with ❤️ for the Marca.com community

<div align="center">

⭐ Give it a star on GitHub ⭐

</div>

---

Si quieres, puedo darte una versión **más profesional (tipo proyecto top de GitHub)** con badges extra, TOC automático y screenshots.
