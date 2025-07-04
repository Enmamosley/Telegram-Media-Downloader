# Descargador de Álbumes de Telegram

## Descripción
Este proyecto es una herramienta de línea de comandos escrita en Python que permite descargar álbumes y medios de chats de Telegram. Organiza los archivos descargados en carpetas basadas en los mensajes o sus captions, con soporte para filtrado por tipo de medio y fechas. Utiliza la biblioteca **Telethon** para interactuar con la API de Telegram y **tqdm** para mostrar una barra de progreso.

## Características
- Descarga fotos, videos, GIFs, audios, stickers y documentos de chats de Telegram.
- Organiza los medios en carpetas basadas en el caption del mensaje o la fecha.
- Soporta filtrado por tipo de medio y rango de fechas.
- Evita descargas duplicadas mediante un archivo de historial (`seen.json`).
- Manejo de concurrencia para descargas más rápidas con un límite de 5 descargas simultáneas.
- Registro detallado de las operaciones en la consola.
- Interfaz interactiva para seleccionar chats si no se especifica un ID.

## Requisitos
- Python 3.8 o superior.
- Bibliotecas de Python:
  - `telethon`
  - `tqdm`
- Credenciales de API de Telegram (`api_id` y `api_hash`). Obtén las tuyas en [my.telegram.org](https://my.telegram.org).

## Instalación
1. Clona el repositorio:
   ```bash
   git clone https://github.com/enmamosley/Telegram-Media-Downloader.git
   cd tu_repositorio
   ```
2. Instala las dependencias:
   ```bash
   pip install telethon tqdm
   ```
3. Configura tus credenciales de API en el código:
   - Edita las variables `api_id` y `api_hash` en el archivo principal con tus credenciales de Telegram.

## ✅ Obtener API ID y Hash

Para usar la API de Telegram necesitas tus propias credenciales:

1. Ve a [https://my.telegram.org](https://my.telegram.org)
2. Inicia sesión con tu número de teléfono.
3. Crea una nueva aplicación.
4. Obtén tu API ID y API Hash.
5. Guarda esos datos para configurarlos en los scripts.

---

## ✅ Archivos del proyecto

```bash
.
├── init_session.py       # Primer paso: inicializar y guardar tus chats
├── download_media.py     # Segundo paso: descargar mensajes y medios
└── README.md             # Documentación del proyecto
```

---

## ✅ Configuración

En ambos scripts encontrarás estas variables al inicio:

```python
api_id = TU_API_ID
api_hash = 'TU_API_HASH'
session_name = 'mysession'
```

✏️ Debes reemplazarlas con tus datos reales.

Por ejemplo:

```python
api_id = 123456
api_hash = 'abcdef1234567890abcdef1234567890'
```

---

## ✅ Uso recomendado

⚡ **¿Por qué hay dos scripts?**

Usar Telethon por primera vez requiere guardar tu sesión (archivo `.session`) para que los chats y canales estén disponibles localmente. Por eso recomendamos este flujo:

### 1️⃣ Inicializar sesión

✅ Este paso se hace solo la primera vez (o si borras el archivo de sesión).

```bash
python init_session.py
```

✔️ **Qué hace:**

- Inicia sesión en tu cuenta (te pedirá el código de Telegram si es la primera vez).
- Recorre todos tus chats, grupos y canales.
- Los guarda en la sesión (`mysession.session`) para usarlos después.

✅ **Ventajas:**

- Evita errores como «entidad no encontrada».
- Reduce consultas futuras a la API de Telegram.

### 2️⃣ Descargar contenidos

✅ Una vez tengas la sesión creada, puedes usar el segundo script:
1. Ejecuta el script:
   ```bash
   python script.py
   ```
2. Si no especificas un `--chat-id`, el script mostrará una lista de tus chats de Telegram y te pedirá que selecciones uno ingresando su número.

### Opciones de línea de comandos
```bash
python script.py --chat-id <ID> --limit <N> --min-date <YYYY-MM-DD> --max-date <YYYY-MM-DD> --media-types <tipo1 tipo2 ...> --reverse
```
- `--chat-id`: ID del chat a procesar.
- `--limit`: Número máximo de mensajes a procesar.
- `--min-date`: Fecha mínima para los mensajes (formato `YYYY-MM-DD`).
- `--max-date`: Fecha máxima para los mensajes (formato `YYYY-MM-DD`).
- `--media-types`: Tipos de medios a descargar (p.ej., `photo video document`).
- `--reverse`: Procesa los mensajes en orden ascendente (del más antiguo al más reciente).

### Ejemplo
Descargar fotos y videos de un chat específico, limitando a mensajes de 2023:
```bash
python script.py --chat-id 123456789 --limit 1000 --min-date 2023-01-01 --max-date 2023-12-31 --media-types photo video
```

## Estructura de Archivos
- Los archivos se guardan en la carpeta `downloads/`.
- Cada álbum se organiza en una subcarpeta nombrada según el caption del mensaje o la fecha.
- Los captions se guardan en un archivo `text.txt` dentro de la carpeta correspondiente.
- El archivo `seen.json` registra los IDs de los álbumes procesados para evitar duplicados.

## Notas
- Asegúrate de tener una conexión estable a internet.
- Los archivos existentes no se volverán a descargar.
- Si usas macOS, el script ajusta automáticamente la política de bucle de eventos para compatibilidad.
- Los errores durante la descarga se registran en la consola sin interrumpir el proceso.

## Contribuciones
¡Las contribuciones son bienvenidas! Por favor, abre un *issue* o envía un *pull request* con mejoras o correcciones.

## Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
