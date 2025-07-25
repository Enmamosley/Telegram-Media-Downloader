import os
import re
import json
import argparse
import logging
import asyncio
import sys
import datetime
import mimetypes
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
from tqdm.asyncio import tqdm
from dotenv import load_dotenv

# --- Configuración y utilidades ---

load_dotenv()
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
session_name = os.getenv('SESSION_NAME', 'mysession')
output_folder = os.getenv('OUTPUT_FOLDER', 'downloads')
seen_file = os.path.join(output_folder, 'seen.json')

if sys.platform == 'darwin':
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def clean_filename(name: str) -> str:
    name = name.strip().replace("\n", " ").replace(".", "_")
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:50] or "sin_texto"

def ensure_unique_folder(path: str) -> str:
    base, ext = os.path.splitext(path)
    i, unique = 1, path
    while os.path.exists(unique):
        unique = f"{base}_{i}{ext}"
        i += 1
    return unique

def get_media_type(msg):
    if msg.photo: return 'photo'
    if getattr(msg, 'video', None): return 'video'
    if getattr(msg, 'animation', None): return 'gif'
    if getattr(msg, 'voice', None): return 'voice'
    if getattr(msg, 'sticker', None): return 'sticker'
    if msg.document: return 'document'
    return None

def resolve_output_folder(msg, caption, grouped, base_output, structure="flat"):
    if structure == "flat":
        if grouped:
            if caption:
                folder = ensure_unique_folder(os.path.join(base_output, clean_filename(caption)))
            else:
                folder = os.path.join(base_output, "NC")
        else:
            folder = base_output
    elif structure == "monthly":
        ym = msg.date.strftime("%Y-%m")
        if grouped:
            if caption:
                folder = ensure_unique_folder(os.path.join(base_output, ym, "captions", clean_filename(caption)))
            else:
                folder = os.path.join(base_output, ym, "NC")
        else:
            folder = os.path.join(base_output, ym, "individual")
    else:
        raise ValueError(f"Estructura no reconocida: {structure}")
    os.makedirs(folder, exist_ok=True)
    return folder

def resolve_filename(msg, caption, ext, structure="flat", grouped=False):
    if structure == "flat" and not grouped:
        if caption:
            name = f"{clean_filename(caption)}_{msg.id}{ext}"
        else:
            name = f"{msg.id}{ext}"
    else:
        name = f"{msg.id}{ext}"
    return name

def get_file_extension(msg):
    # Documentos
    if msg.document:
        # 1. Usa filename si existe
        for attr in msg.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                ext = os.path.splitext(attr.file_name)[1]
                if ext:
                    return ext
        # 2. Usa mime_type si existe
        mime_type = getattr(msg.document, 'mime_type', None)
        if mime_type:
            ext = mimetypes.guess_extension(mime_type)
            if ext:
                return ext
        return ".bin"
    # Fotos
    if msg.photo:
        return ".jpg"
    # Videos
    if getattr(msg, 'video', None):
        return ".mp4"
    # Animaciones (GIF)
    if getattr(msg, 'animation', None):
        return ".gif"
    # Voz
    if getattr(msg, 'voice', None):
        return ".ogg"
    # Stickers
    if getattr(msg, 'sticker', None):
        return ".webp"
    return ".bin"

# --- Manejo de historial (seen.json) con protección concurrente ---

seen_lock = asyncio.Lock()

def load_seen():
    if os.path.exists(seen_file):
        try:
            with open(seen_file, encoding='utf-8') as f:
                return set(json.load(f))
        except Exception:
            logging.warning("No se pudo leer seen.json, se reinicia historial.")
    return set()

async def save_seen_async(seen):
    async with seen_lock:
        os.makedirs(output_folder, exist_ok=True)
        with open(seen_file, 'w', encoding='utf-8') as f:
            json.dump(list(seen), f, ensure_ascii=False, indent=2)

def get_seen_ids(msg):
    ids = {msg.id}
    if getattr(msg, 'grouped_id', None):
        ids.add(msg.grouped_id)
    return ids

# --- Descarga de media ---

async def download_media(m, folder, fname, semaphore, attempt_limit=4):
    async with semaphore:
        for attempt in range(1, attempt_limit+1):
            try:
                path = os.path.join(folder, fname)
                if os.path.exists(path):
                    logging.info(f"  ⏭ {fname} ya existe")
                    return
                downloaded = await m.download_media(file=path)
                logging.info(f"  ✔ mensaje {m.id} -> {os.path.basename(downloaded)}")
                return
            except Exception as e:
                logging.error(f"  ✖ fallo mensaje {m.id}: {e} (intento {attempt})")
                await asyncio.sleep(2 ** (attempt-1))
        logging.error(f"  ❌ No se pudo descargar {m.id} tras varios intentos.")

def save_caption_text(folder, caption):
    path = os.path.join(folder, "text.txt")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(caption)
        logging.info(f"  📝 caption guardado en {path}")
    except Exception as e:
        logging.error(f"  ✖ error al guardar caption: {e}")

# --- Argumentos CLI ---

parser = argparse.ArgumentParser(description="Descarga álbumes de Telegram")
parser.add_argument('--chat-id', type=int, help="ID del chat a procesar")
parser.add_argument('--limit', type=int, help="Límite de mensajes a procesar")
parser.add_argument('--min-date', type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d'), help="Fecha mínima YYYY-MM-DD")
parser.add_argument('--max-date', type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d'), help="Fecha máxima YYYY-MM-DD")
parser.add_argument('--media-types', nargs='+', choices=['photo','video','gif','voice','sticker','document'], help="Tipos de media a descargar")
parser.add_argument('--reverse', action='store_true', help="Orden ascendente de mensajes")
parser.add_argument('--caption-only', action='store_true', help="Solo guardar captions (no descarga media)")
parser.add_argument('--skip-seen', action='store_true', help="Procesar todo sin saltar mensajes vistos en seen.json")
parser.add_argument('--structure', choices=['monthly'], default=None, help="Si se indica, usa estructura mensual (por año/mes); por defecto es plana/simple.")
parser.add_argument('--download-text', action='store_true', help="Descargar mensajes de solo texto (sin media)")
parser.add_argument('--concurrent', type=int, default=6,
    help="Cantidad de descargas simultáneas (default: 6, máximo recomendado: 15)")
args = parser.parse_args()

structure = args.structure or 'flat'

client = TelegramClient(session_name, api_id, api_hash)

# --- Lógica principal ---

async def main():
    await client.start()
    logging.info("Conectado con éxito.")

    # Selección de chat
    if args.chat_id:
        target = await client.get_entity(args.chat_id)
    else:
        dialogs = []
        async for d in client.iter_dialogs(limit=50):
            name = getattr(d.entity, 'title', getattr(d.entity, 'first_name', ''))
            dialogs.append((name, d.entity))
        print("\n📜 Tus chats disponibles:")
        for i, (name, ent) in enumerate(dialogs):
            print(f"{i}: {name} (ID: {ent.id})")
        sel = int(input("\n❓ Número de chat: ").strip())
        if sel < 0 or sel >= len(dialogs):
            logging.error("Selección inválida.")
            return
        target = dialogs[sel][1]
        logging.info(f"Chat seleccionado: {dialogs[sel][0]}")

    os.makedirs(output_folder, exist_ok=True)
    seen = load_seen()
    semaphore = asyncio.Semaphore(args.concurrent)

    logging.info(f"Descargando mensajes de: {getattr(target, 'title', getattr(target, 'first_name', ''))}...")
    msgs = client.iter_messages(target, limit=args.limit, reverse=args.reverse)

    async for msg in tqdm(msgs, desc="Procesando mensajes", unit="msg"):
        try:
            if args.min_date and msg.date.date() < args.min_date.date(): continue
            if args.max_date and msg.date.date() > args.max_date.date(): continue
            if not msg.media and not msg.text: continue

            seen_ids = get_seen_ids(msg)
            if not args.skip_seen and seen_ids & seen: continue

            is_grouped = bool(getattr(msg, 'grouped_id', None))
            caption = msg.text.strip() if msg.text else ""

            # -- Individuales: todos van a la raíz (flat) o carpeta mensual (monthly)
            if not is_grouped and (msg.photo or getattr(msg, 'video', None) or msg.document):
                folder = resolve_output_folder(msg, caption, False, output_folder, structure)
                ext = get_file_extension(msg)
                fname = resolve_filename(msg, caption, ext, structure, False)
                await download_media(msg, folder, fname, semaphore)
                seen.update(seen_ids)
                await save_seen_async(seen)
                continue

            # -- Texto suelto individual (sin media), solo si se pidió
            if args.download_text and not is_grouped and msg.text and not msg.media:
                folder = resolve_output_folder(msg, "", False, output_folder, structure)
                fname = f"text_{msg.id}.txt"
                path = os.path.join(folder, fname)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(msg.text)
                logging.info(f"  📝 texto suelto guardado en {path}")
                seen.update(seen_ids)
                await save_seen_async(seen)
                continue

            # -- ÁLBUM/GRUPO (grouped)
            if is_grouped:
                # Buscar todos los mensajes del grupo (álbum)
                group_id = msg.grouped_id
                album_msgs = []
                search_ids = set()
                range_size = 40
                for _ in range(3):
                    min_id = max(1, msg.id - range_size)
                    max_id = msg.id + range_size
                    async for m in client.iter_messages(target, reverse=True, min_id=min_id, max_id=max_id):
                        if getattr(m, 'grouped_id', None) == group_id and m.id not in search_ids:
                            search_ids.add(m.id)
                            album_msgs.append(m)
                    if len(album_msgs) >= 10: break
                    range_size *= 2
                # Busca caption grupal
                group_caption = next((m.text for m in album_msgs if m.text), "").strip()
                folder = resolve_output_folder(msg, group_caption, True, output_folder, structure)
                # Descarga todos los archivos
                tasks = []
                for m in album_msgs:
                    mt = get_media_type(m)
                    if args.media_types and mt not in args.media_types:
                        continue
                    ext = get_file_extension(m)
                    fname = resolve_filename(m, "", ext, structure, True)
                    tasks.append(download_media(m, folder, fname, semaphore))
                await asyncio.gather(*tasks)
                # Guarda el caption grupal como text.txt si existe
                if group_caption:
                    save_caption_text(folder, group_caption)
                seen.update(seen_ids)
                await save_seen_async(seen)
                continue

        except Exception as e:
            logging.error(f"Error procesando álbum {getattr(msg, 'grouped_id', msg.id)}: {e}")

    logging.info("✅ Proceso completado. Archivos en '%s'", output_folder)

if __name__ == "__main__":
    asyncio.run(main())
