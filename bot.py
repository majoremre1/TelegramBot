import os
import yt_dlp
import moviepy as mp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from moviepy import AudioFileClip, VideoFileClip


# Download the video using yt-dlp
def download_video(url: str, download_path: str):
    ydl_opts = {
        'format': 'best',
        'outtmpl': download_path,  # Save file to this location
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

from moviepy import VideoFileClip
import numpy as np

def process_video(input_path, output_path):
    # Load the video clip
    video = VideoFileClip(input_path)
    
    # Get the audio from the video
    audio = video.audio
    
    # Convert the audio to a numpy array
    audio_array = audio.to_soundarray(fps=22000)
    
    # Reduce volume by scaling the audio samples (e.g., reducing by 2%)
    audio_array = audio_array * 0.98  # 2% reduction in volume
    
    # Convert the numpy array back to an AudioClip
    from moviepy.audio.AudioClip import AudioArrayClip
    new_audio = AudioArrayClip(audio_array, fps=audio.fps)
    
    # Set the new audio to the video using with_audio()
    video = video.with_audio(new_audio)
    
    # Write the output file
    video.write_videofile(output_path)




# Command handler to start the bot
async def start(update: Update, context):
    await update.message.reply_text("Schick mir einen Video-Link, und ich werde ihn herunterladen und verarbeiten!")


# Function to handle received links and process the video
async def handle_message(update: Update, context):
    url = update.message.text
    
    # Ensure URL is valid
    if not url.startswith('http'):
        await update.message.reply_text("Bitte schick mir eine gültige Video-URL!")
        return

    await update.message.reply_text("Video wird heruntergeladen...")

    # Download the video to a temporary path
    temp_input_path = "altes_video.mp4"
    download_video(url, temp_input_path)

    # Process the video (reduce volume, zoom)
    temp_output_path = "neues_video.mp4"
    process_video(temp_input_path, temp_output_path)

    # Send back the processed video
    await update.message.reply_video(video=open(temp_output_path, 'rb'))

    # Clean up the temporary files
    os.remove(temp_input_path)
    os.remove(temp_output_path)


# Function to start the bot
def main():
    # Telegram Bot Token
    bot_token = "8184390438:AAE93Z0N7sP2B6Vg3NJrUIDl2NXC9q8EB88"

    # Create the Application
    application = Application.builder().token(bot_token).build()

    # Add the handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
