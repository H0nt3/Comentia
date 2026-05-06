# 📝 Comentia

<div align="center">

![Versión](https://img.shields.io/badge/versión-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![Licencia](https://img.shields.io/badge/licencia-MIT-orange)
![Plataformas](https://img.shields.io/badge/plataforma-Windows%20%7C%20Linux%20%7C%20Mac-grey)

**Extrae todos los comentarios de cualquier noticia de Marca.com de forma sencilla y rápida**

</div>

---

## 📌 Tabla de contenidos
  * 📖 [¿Qué es Comentia?](#-qué-es-comentia)
  * ✨ [Características principales](#-características-principales)
  * 📋 [Requisitos previos](#-requisitos-previos)
  * 🚀 [Instalación](#-instalación)
  * 🧑‍💻 [Guía de Uso](#-guía-de-uso)
  * 📂 [Salida y archivos generados](#-salida-y-archivos-generados)
  * 📊 [Estadísticas](#-estadísticas)
  * 🛠️ [Estructura JSON](#-estructura-json)
  * ❓ [Preguntas Frecuentes (FAQ)](#-preguntas-frecuentes-faq)
  * 🐛 [Solución de problemas](#-solución-de-problemas)
  * 🤝 [Contribuir](#-contribuir)
  * 📄 [Licencia](#-licencia)
  * ⭐ [Soporte y Créditos](#-soporte-y-créditos)

---
<a name="qué-es-comentia"></a>
### 📖 ¿Qué es Comentia?

**Comentia** es una herramienta diseñada para fácil de usar que te permite **extraer, guardar y analizar comentarios** de cualquier noticia de **Marca.com** en tu ordenador y de forma automatizada. Solo necesitas **pegar la URL de la noticia** y Comentia se encarga del resto.

Ideal para:

* 📊 análisis de datos
* 🧠 estudios de comportamiento
* 💾 archivado de debates

---
<a name="características-principales"></a>
### ✨ Características principales

| Característica                     | Descripción                                                                 |
| ---------------------------------- | --------------------------------------------------------------------------- |
| 🚀 **Sencillo**                    | Solo necesitas la URL de la noticia                                         |
| 💾 **Extracción completa**         | Descarga **todos** los comentarios, incluso los que están en varias páginas |
| 📁 **Organización**                | Selección de carpeta mediante una interfaz gráfica                          |
| 📊 **Estadísticas**                | Genera un informe automático con datos y metricas interesantes              |
| 🔄 **Sin duplicados**              | Detecta y evita comentarios repetidos automáticamente                       |
| 🛡️ **Robusto**                     | Sistema de reintentos automático ante errores de conexión                   |
| 🎨 **Interfaz moderna**            | GUI con Qt5 + versión clásica (tkinter)                                     |
| ⚡ **Modo CLI**                     | Uso desde terminal para automatización                                      |
| 📦 **Multiplataforma**             | Compatible con Windows, macOS y Linux                                       |
| 💾 **Configuración persistente**   | Recuerda tu última carpeta y URLs                                           |

---
<a name="requisitos-previos"></a>
### 📋 Requisitos previos

* **Python 3.9 o superior** ([Descargar Python](https://www.python.org/downloads/)) *(solo para versión desde código fuente)*
* Conexión a internet
* Espacio en disco: ~10 MB

---
<a name="instalación"></a>
### 🚀 Instalación

#### 🔧 Desde el código fuente

```bash
# Clonar el repositorio
git clone https://github.com/H0nt3/Comentia.git
cd Comentia

# Instalar dependencias
pip install -r requirements.txt
```
#### ▶️ Ejecutar

``` bash
# Ejecutar (GUI moderna - recomendado)
python qt_app/main.py

# GUI clásica
python -m comentia

# Modo consola
python -m comentia --cli
```

#### 📦 Ejecutable independiente

Descarga el ejecutable según tu S.O. desde **Releases**:

| Sistema Operativo | Archivo                  |
| ----------------- | ------------------------ |
| Windows           | Comentia-windows.exe     |
| macOS             | Comentia-macoss.app      |
| Linux             | Comentia-linux           |

---
<a name="guía-de-uso"></a>
### 🧑‍💻 Guía de Uso

#### Extracción simple

  **1.** Ejecuta Comentia (doble-clic en el ejecutable o `python qt_app/main.py`) 
  
  **2.** Selecciona la carpeta dónde deseas guardar los archivos que se van a generar.

  **3.** Busca la noticia en Marca.com, selecciona la URL y copiala.

  **4.** Pega la URL de la noticia.

  **5.** Haz clic en **"Extraer Comentarios"**.

  **6.** Espera a que termine (verás el proceso en tiempo real)
  
  **7.** Los archivos generados estarán en la carpeta que seleccionaste. 
  
  **8.** Si todo fué correcto, cierra Comentia.

  Ejemplo de URL de Marca.com
  ```
  https://www.marca.com/futbol/real-madrid/2026/02/09/noticia-ejemplo.html

  ```

#### Extracción por lotes (multiples URL's)

  **1.** Crea un archivo de texto plano (*.txt) con una URL por linea:
  
  ```text
  https://www.marca.com/futbol/real-madrid/2026/02/09/noticia-ejemplo.html
  https://www.marca.com/futbol/real-madrid/2026/03/12/noticia-ejemplo.html
  https://www.marca.com/futbol/real-madrid/2025/012/28/noticia-ejemplo.html
  ```
  
  **2.** En Comentia, ve a la pestaña **"Extracción por lotes"**.

  **3.** Selecciona el archivo con las URLs.

  **4.** Haz clic en **"Extraer todas las URLs**".

  **5.** Espera a que procese todas las noticias.

 ---
<a name="salida-y-archivos-generados"></a>
### 📂 Salida y archivos generados

En la carpeta que seleccionaste, apareceran estos archivos:
```
noticia_123456789/
├── comentarios_123456789_completo.json       # Aqui se guardan todos los comentarios y los metadatos (formato completo)
├── comentarios_123456789_simplificado.json   # Versión simplificada del archivo anterior (solo texto, sin metadatos)
└── comentarios_123456789_estadisticas.txt    # Informe de estadisticas
```

---
<a name="estadísticas"></a>
### 📊 Estadísticas

Incluye automáticamente:

  * 📈 Total de comentarios esperados y obtenidos 
  * 👥 Top 10 de usuarios más activos
  * 📝 Longitud promedio de los comentarios
  * 🔤 Palabras más frecuentes
  * 🗓️ Actividad por fechas
  * ✅ Ratio de éxito de extracción
  * 🚨 Lista de errores (si los hubo)
---
<a name="estructura-json"></a>
### 🛠️ Estructura JSON

#### Ejemplo de JSON Completo

```json
{
  "metadata": {
    "noticia_id": "4405498",
    "url_noticia": "https://...",
    "total_comentarios": 57,
    "fecha_exportacion": "2026-05-06 12:30:45"
  },
  "comentarios": [
    {
      "id": "86882964",
      "order": 1,
      "user": "usuario123",
      "body": "Texto del comentario...",
      "date": "09/02/2026",
      "time": "08:31",
      "references": []
    }
  ]
}
```

#### Simplificado

```json
[
  {
    "usuario": "X",
    "comentario": "...",
    "fecha": "..."
  }
]
```

---
<a name="preguntas-frecuentes-faq"></a>
### ❓ Preguntas Frecuentes (FAQ)
<details> <summary><b>¿Puedo extraer comentarios de cualquier noticia?</b></summary> 
  Sí, cualquier noticia de Marca.com que tenga sección de comentarios activa funciona perfectamente.</details>

<details> <summary><b>¿Cuánto tiempo tarda el proceso?</b></summary>
  Depende del número de comentarios. Para 1000 comentarios, aproximadamente 30-60 segundos.
</details>

<details> <summary><b>¿Es legal extraer estos comentarios?</b></summary>
  Sí, estás extrayendo datos públicos que ya están disponibles en la web. Recomendamos usarlo de forma ética y respetuosa, sin sobrecargar los servidores.
</details>

<details> <summary><b>¿Puedo usar los comentarios para análisis de datos?</b></summary>
  ¡Claro! Los archivos JSON son perfectos para análisis con Python, Pandas, Excel o cualquier herramienta de datos.
</details>

<details><summary><b>¿Qué hago si el programa no arranca en Linux?</b></summary>
  Asegúrate de tener instalado `python3-tk` y `python3-pyqt5`: 

```bash
  sudo apt install python3-tk python3-pyqt5
``` 
</details>

---
<a name="solución-de-problemas"></a>
### 🐛 Solución de problemas

| Problema                                         | Solución                      |
| ------------------------------------------------ | -------------------------------------------------------|
| `ModuleNotFoundError: No module named PyQt5`     | Ejecuta en la terminal `pip install PyQt5`             |
| La ventana de tkinter no se abre en Linux        | Ejecuta en la terminal `sudo apt install python3-tk`   |
| La ventana no se abre en linux                   | Ejecuta en la terminal `sudo apt install python3-pyqt5 |
| Error de conexión                                | Revisar internet                                       |
| No se encuentra el ID de la noticia              | Asegurate que has introducido la URL corrrecta         |
| Permission denied en Linux                       | Ejecuta en la terminal `chmod +x Comentia_Linux` antes de ejecutar     |


---
<a name="contribuir"></a>
### 🤝 Contribuir

Sientete libre de contribuir y mejorar **Comentia** de la manera que consideres oportuno.

---
<a name="licencia"></a>
### 📄 Licencia

MIT License - Libre para su uso personal y comercial
© 2026

---
<a name="soporte-y-créditos"></a>
### ⭐ Soporte y Créditos

Si este proyecto te resulta útil:

<div align="center">

⭐ Dale una estrella en GitHub
🐛 Reporta bugs
💡 Propón mejoras

Desarrollado por Grupo 40 - Equipo EVO Madrid con ❤️

</div>