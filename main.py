import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Ganti dengan Token bot kamu
TOKEN = 'YOUR_BOT_TOKEN'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Halo! Selamat datang di Video to Sticker Bot.**\n\n"
        "Caranya sangat mudah:\n"
        "1. Kirimkan video pendek (maksimal 3 detik).\n"
        "2. Bot akan memproses dan mengirimkan stiker bergerak.\n\n"
        "⚠️ *Pastikan video tidak lebih dari 3 detik ya!*"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_file = await update.message.video.get_file()
    
    # Cek durasi (optional, tapi disarankan)
    if update.message.video.duration > 3:
        await update.message.reply_text("❌ Video terlalu panjang! Maksimal durasi adalah 3 detik.")
        return

    status_msg = await update.message.reply_text("⏳ Sedang memproses video menjadi stiker...")
    
    input_path = f"{video_file.file_id}.mp4"
    output_path = f"{video_file.file_id}.webm"

    await video_file.download_to_drive(input_path)

    # Perintah FFmpeg untuk konversi ke format WebM Telegram
    # -vf: resize ke 512x512 (menjaga aspek rasio), -an: hapus audio
    command = [
        'ffmpeg', '-i', input_path,
        '-vf', "scale='if(gt(iw,ih),512,-1)':'if(gt(iw,ih),-1,512)'",
        '-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0',
        '-t', '00:00:03', '-an', '-f', 'webm', output_path
    ]

    try:
        subprocess.run(command, check=True)
        # Kirim sebagai dokumen dengan mime_type video/webm agar terbaca sebagai stiker
        await update.message.reply_document(
            document=open(output_path, 'rb'),
            filename="sticker.webm",
            caption="✅ Ini stiker bergerakmu! Klik dan 'Add to Favorites'."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan saat konversi.")
    finally:
        # Hapus file sampah
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        await status_msg.delete()

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
        
