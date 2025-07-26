import os
import argparse
import asyncio
from pyrogram import Client
from dotenv import load_dotenv
from asyncio import Semaphore
# --- Diseñado para ser mas rapido en grupos publicos ---
# --- Cargar entorno (.env) ---
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
output_folder = os.getenv("OUTPUT_FOLDER", "downloads")
session_name = os.getenv("SESSION_NAME", "session")

# --- Argumentos CLI ---
parser = argparse.ArgumentParser(description="Descarga media de Telegram (photo, video, document)")
parser.add_argument("--limit", type=int, default=10000, help="Cantidad máxima de mensajes a procesar")
parser.add_argument("--concurrent", type=int, default=6, help="Descargas simultáneas (default 6)")
parser.add_argument("--media-types", nargs='+', choices=['photo', 'video', 'document'], default=['photo', 'video', 'document'], help="Tipos de media a descargar")
args = parser.parse_args()

# --- Setup inicial ---
os.makedirs(output_folder, exist_ok=True)
semaphore = Semaphore(args.concurrent)
app = Client(session_name, api_id=api_id, api_hash=api_hash)

# --- Función de descarga según tipo ---
async def download_media(msg):
    mt = None
    filename = None

    if msg.photo and 'photo' in args.media_types:
        mt = 'photo'
        filename = os.path.join(output_folder, f"{msg.message_id}.jpg")
    elif msg.video and 'video' in args.media_types:
        mt = 'video'
        ext = os.path.splitext(msg.video.file_name or "")[1] or ".mp4"
        filename = os.path.join(output_folder, f"{msg.message_id}{ext}")
    elif msg.document and 'document' in args.media_types:
        mt = 'document'
        ext = os.path.splitext(msg.document.file_name or "")[1] or ".bin"
        filename = os.path.join(output_folder, f"{msg.message_id}{ext}")

    if not mt or not filename:
        return  # Tipo no solicitado o no válido

    if not os.path.exists(filename):
        async with semaphore:
            try:
                await msg.download(file_name=filename)
                print(f"✔ {filename}")
            except Exception as e:
                print(f"✖ Error {msg.message_id}: {e}")

# --- Selección de chat interactiva ---
async def select_chat():
    print("\n📜 Listando tus chats...")
    chats = []
    async with app:
        async for dialog in app.get_dialogs():
            name = dialog.chat.title or getattr(dialog.chat, "first_name", "Sin nombre")
            chats.append((name, dialog.chat.id))
    for i, (name, cid) in enumerate(chats):
        print(f"{i}: {name} (ID: {cid})")
    while True:
        idx = input("\n❓ Número de chat: ").strip()
        if idx.isdigit() and int(idx) < len(chats):
            return chats[int(idx)][1]
        print("❌ Selección inválida.")

# --- Lógica principal ---
async def main():
    async with app:
        chat_id = await select_chat()
        tasks = []
        async for msg in app.get_chat_history(chat_id, limit=args.limit):
            if msg.photo or msg.video or msg.document:
                tasks.append(download_media(msg))
        await asyncio.gather(*tasks)
        print("✅ Descarga completada.")

if __name__ == "__main__":
    asyncio.run(main())
