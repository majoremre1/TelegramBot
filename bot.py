import os
import subprocess
import yt_dlp
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from moviepy import VideoFileClip
import numpy as np

# Funktion zur Entfernung von Metadaten mit ffmpeg
def remove_metadata(input_video_path, output_video_path):
    command = [
        'ffmpeg', '-i', input_video_path,
        '-map_metadata', '-1', '-c:v', 'copy', '-c:a', 'copy',
        output_video_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Funktion zur Überprüfung der Videogröße vor dem Download
def check_video_size(url: str):
    ydl_opts = {'format': 'best', 'quiet': True, 'noplaylist': True, 'simulate': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_size = info_dict.get('filesize', None)
        return video_size / (1024 * 1024) if video_size else None

# Funktion zum Download eines Videos mit yt-dlp
def download_video(url: str, download_path: str):
    ydl_opts = {
        'format': 'best',  # Fordert das beste verfügbare Format an
        'outtmpl': download_path, 
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# Funktion zur Videobearbeitung (Lautstärke senken, leicht zoomen)
def process_video(input_path, output_path):
    video = VideoFileClip(input_path)
    audio = video.audio
    audio_array = audio.to_soundarray(fps=43278) * 0.98  # 2% leiser
    from moviepy.audio.AudioClip import AudioArrayClip
    new_audio = AudioArrayClip(audio_array, fps=audio.fps)
    video = video.with_audio(new_audio).resized(1.01)  # 1% Zoom
    video.write_videofile(output_path)

# Start-Befehl
async def start(update: Update, context):
    await update.message.reply_text("Schick mir einen Video-Link, und ich werde ihn herunterladen und verarbeiten!")

# Nachrichtenhandler für Video-Links
async def handle_message(update: Update, context):
    url = update.message.text
    if not url.startswith('http'):
        await update.message.reply_text("Bitte schick mir eine gültige Video-URL!")
        return

    check_msg = await update.message.reply_text("📡 Video wird überprüft...")

    # Videogröße prüfen
    video_size_mb = check_video_size(url)
    if video_size_mb is not None and video_size_mb > 100:
        await check_msg.delete()
        await update.message.reply_text(f"❌ Das Video ist {video_size_mb:.2f} MB groß. Maximal erlaubt: 100 MB.")
        return

    await check_msg.delete()
    await update.message.reply_text("⬇️ Video wird heruntergeladen...")

    # Eindeutige Datei-IDs erzeugen
    unique_id = str(uuid.uuid4())[:8]
    temp_input_path = f"altes_{unique_id}.mp4"
    temp_output_path = f"neues_{unique_id}.mp4"

    try:
        # Video herunterladen und verarbeiten
        download_video(url, temp_input_path)
        process_video(temp_input_path, temp_output_path)

        if os.path.exists(temp_output_path):
            await update.message.reply_video(video=open(temp_output_path, 'rb'))
        else:
            await update.message.reply_text("⚠️ Fehler: Die bearbeitete Datei wurde nicht gefunden.")

    except Exception as e:
        await update.message.reply_text(f"❌ Fehler: {e}")

    finally:
        # Temporäre Dateien löschen
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

# Hauptfunktion zum Starten des Bots
def main():
    bot_token = "8184390438:AAE93Z0N7sP2B6Vg3NJrUIDl2NXC9q8EB88"  # Dein Bot-Token als String
    application = Application.builder().token(bot_token).build()

    # Befehle registrieren
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Webhook anstelle von Polling verwenden
    application.run_webhook(
        listen="0.0.0.0",  # IP-Adresse des Servers
        port=8443,  # Port für Webhooks
        url_path=bot_token,  # Dies sollte der Bot-Token sein
        webhook_url=f"https://telegrambot-s9wx.onrender.com/{bot_token}"  # Korrekte Webhook-URL mit Token als String
    )

if __name__ == "__main__":
    main()

