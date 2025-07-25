import os
from dotenv import load_dotenv
import asyncio
import sys
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError

# ————— Cargar variables de entorno —————
load_dotenv()
api_id       = int(os.getenv('TELEGRAM_API_ID'))
api_hash     = os.getenv('TELEGRAM_API_HASH')
session_name = os.getenv('SESSION_NAME', 'mysession')

# ————— MacOS fix —————
if sys.platform == 'darwin':
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

client = TelegramClient(session_name, api_id, api_hash)

async def main():
    await client.start()
    print("✅ Sesión iniciada correctamente.\n")
    print("🔎 Escaneando TODOS tus chats, grupos y canales...\n")

    count = 0
    bad    = []  # Para guardar los diálogos privados o sin acceso

    async for dialog in client.iter_dialogs(limit=None):
        ent  = dialog.entity
        name = getattr(ent, 'title', getattr(ent, 'first_name', ''))

        try:
            # Intentamos obtener la entidad completa
            await client.get_entity(ent.id)
            print(f"- Guardando: {name} (ID: {ent.id})")
            count += 1

        except ChannelPrivateError:
            # Si es privado o no tienes permiso
            print(f"- ⚠️  Saltando {name!r} (ID: {ent.id}): privado o sin acceso")
            bad.append((ent.id, name))
            continue

    print(f"\n✅ Guardados {count} entities en la sesión.")
    if bad:
        print("\n🔒 Estos canales/grupos no pudiste acceder:")
        for cid, cname in bad:
            print(f"  • {cname!r} (ID: {cid})")

    print("\n✅ ¡Ya puedes correr el descargador sin problemas!")

if __name__ == '__main__':
    asyncio.run(main())
