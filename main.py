import os
import subprocess
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Setup log agar kita bisa pantau bot di Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Kita pakai nama BOT_TOKEN sesuai permintaanmu
TOKEN = os.getenv("BOT_TOKEN")

# Fungsi saat kamu klik /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = (
        "👋 **Halo! Aku Bot Stiker Video.**\n\n"
        "Kirimkan video MP4 pendek (maks 3 detik),\n"
        "aku akan mengubahnya jadi stiker .webm otomatis!"
    )
    await update.message.reply_text(teks, parse_mode='Markdown')

# Fungsi saat kamu kirim video
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document
    if not video: return

    pesan_tunggu = await update.message.reply_text("⏳ Lagi proses konversi, sabar ya...")
    
    # Download file video ke server
    nama_input = f"input_{video.file_id}.mp4"
    nama_output = f"output_{video.file_id}.webm"
    file_telegram = await context.bot.get_file(video.file_id)
    await file_telegram.download_to_drive(nama_input)

    try:
        # Proses merubah video jadi stiker (FFmpeg)
        # Aturan: 512x512 piksel, tanpa suara, durasi 3 detik
        perintah = [
            'ffmpeg', '-i', nama_input,
            '-vf', "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color=#00000000",
            '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
            '-r', '30', '-t', '3', '-an', '-f', 'webm', '-y', nama_output
        ]
        subprocess.run(perintah, check=True)

        # Kirim hasilnya kembali ke Telegram
        with open(nama_output, 'rb') as f:
            await update.message.reply_document(document=f, filename="sticker.webm")
        
        await pesan_tunggu.delete()

    except Exception as e:
        await pesan_tunggu.edit_text(f"❌ Aduh, ada error: {e}")
    finally:
        # Hapus sampah file di server
        if os.path.exists(nama_input): os.remove(nama_input)
        if os.path.exists(nama_output): os.remove(nama_output)

if __name__ == '__main__':
    # Menjalankan bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    print("Bot sudah nyala...")
    app.run_polling()
