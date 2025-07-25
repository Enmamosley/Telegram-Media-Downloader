# Descargador de Álbumes y Medios de Telegram

## Descripción

Herramienta de línea de comandos en Python para descargar álbumes y medios de chats de Telegram, organizando los archivos descargados en carpetas simples (estructura plana por defecto) o mensuales (con `--structure monthly` si lo prefieres). Permite filtrar por tipo de medio y fechas, evita duplicados y soporta descargas concurrentes configurables. Utiliza **Telethon** para interactuar con la API de Telegram y **tqdm** para barra de progreso.

## Características

- Descarga fotos, videos, GIFs, audios, stickers y documentos de chats de Telegram.
- Organización de archivos en estructura plana (**flat**, por defecto) o mensual (`--structure monthly`).
- Extensiones de archivo correctas (evita `.bin` salvo casos excepcionales).
- Filtros por tipo de medio y rango de fechas.
- Evita descargas duplicadas mediante un archivo de historial (`seen.json`).
- Manejo de concurrencia configurable con `--concurrent` (por defecto 5; recomendado 4-8).
- Descarga mensajes de solo texto si se indica con `--download-text`.
- Registro detallado de las operaciones en la consola.
- Interfaz interactiva para seleccionar chats si no se especifica un ID.

---

## Estructura del proyecto

```bash
telegram-album-downloader/
├── .env.example
├── requirements.txt
├── init_session.py
├── download_media.py
└── downloads/           # Carpeta de salida
```

---

## Requisitos

- **Python 3.8+**
- **Credenciales de Telegram:** Consigue tu `api_id` y `api_hash` desde [my.telegram.org](https://my.telegram.org).
- **Entorno virtual** (recomendado).
- **Dependencias**:
  ```
  telethon>=1.30.0
  tqdm>=4.64.0
  python-dotenv>=0.21.0
  ```

---

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/enmamosley/Telegram-Media-Downloader.git
   cd telegram-media-downloader
   ```
2. Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Windows CMD:
   .\.venv\Scripts\activate.bat
   # Unix/macOS:
   source .venv/bin/activate
   ```
3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura tus credenciales:
   ```bash
   cp .env.example .env
   # Edita .env con tus datos reales
   ```

---

## Configuración de entorno

Ejemplo `.env.example`:

```dotenv
TELEGRAM_API_ID=1234567
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=mysession
OUTPUT_FOLDER=downloads
```

---

## Scripts

### 1️⃣ `init_session.py`

*Ejecuta sólo la primera vez para guardar tu sesión:*

```bash
python init_session.py
```

Ingresa tu número de teléfono con código de país y el código de verificación recibido. La sesión queda guardada para futuros usos.

---

### 2️⃣ `download_media.py`

*Descarga medios de un chat específico o seleccionando uno de tus chats:*

```bash
python download_media.py --chat-id <ID> [opciones]
```

Si omites `--chat-id`, podrás elegir el chat de manera interactiva.

#### Opciones principales

| Opción                    | Descripción                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------- |
| `--chat-id <ID>`          | ID del chat a procesar                                                                 |
| `--limit <N>`             | Límite de mensajes a procesar                                                          |
| `--min-date <YYYY-MM-DD>` | Solo mensajes desde esta fecha                                                         |
| `--max-date <YYYY-MM-DD>` | Solo mensajes hasta esta fecha                                                         |
| `--media-types <tipos>`   | Lista de tipos (`photo`, `video`, `gif`, `voice`, `sticker`, `document`)               |
| `--reverse`               | Orden ascendente (antiguo a reciente)                                                  |
| `--download-text`         | Descargar mensajes de solo texto (sin media)                                           |
| `--structure monthly`     | Organiza los archivos en carpetas por año/mes (por defecto es estructura plana/simple) |
| `--skip-seen`             | Procesa todo, sin saltar mensajes ya vistos                                            |
| `--concurrent <N>`        | Número de descargas simultáneas (default: 5, recomendado 4-8)                          |

---

#### Ejemplo de uso

Solo fotos y videos del 2024, con 8 hilos de descarga simultáneas:

```bash
python download_media.py --chat-id 123456789 --media-types photo video --min-date 2024-01-01 --max-date 2024-12-31 --concurrent 8
```

Solo descarga mensajes de texto (sin media), en estructura mensual:

```bash
python download_media.py --structure monthly --download-text
```

---

#### Organización de archivos

**Por defecto (estructura plana/simple):**

```
downloads/
  Mi_Caption_12345.jpg    # Individual con caption
  12346.jpg               # Individual sin caption
  NC/                     # Álbumes sin caption
    33456.jpg
  Mi_Album/
    5551.jpg
    5552.mp4
    text.txt              # Caption grupal
```

**Con **--structure monthly**:**

```
downloads/
  2024-07/
    individual/
      Mi_Caption_12345.jpg
      12346.jpg
    NC/
      33456.jpg
    captions/
      Mi_Album/
        5551.jpg
        5552.mp4
        text.txt
```

- **Individuales:** en la raíz (o en carpeta `individual/` si usas `monthly`).
- **Álbumes con caption:** en carpeta por caption, junto a su `text.txt`.
- **Álbumes sin caption:** en carpeta `NC/`.

---

## Notas y recomendaciones de rendimiento

- **Concurrencia:** Usa el argumento `--concurrent` para ajustar el número de descargas simultáneas (recomendado entre 4 y 8). Más alto no necesariamente acelera la descarga, y puede ser más lento por límites de Telegram, tu red o disco.
- **Historial (**``**):** Evita descargar dos veces el mismo mensaje/álbum.
- **Extensiones seguras:** El script elige la extensión correcta; `.bin` solo si no hay información suficiente.
- **Barra de progreso:** Usa `tqdm` para feedback visual.
- **Chats privados/canales:** Algunos pueden ser inaccesibles por permisos; el script solo avisa y sigue.
- **No descarga mensajes de solo texto a menos que se pida explícitamente (**``**).**
- **Compatible con macOS y otros sistemas.**
- **Archivos existentes no se sobrescriben.**
- **Una imagen o video no comprimida y enviada como archivo, "foto.png" se trata como un documento.**

---

## Contribuciones

¡Bienvenidas! Abre un issue o PR con mejoras o sugerencias.

## Licencia

MIT. Consulta `LICENSE` para más detalles.

