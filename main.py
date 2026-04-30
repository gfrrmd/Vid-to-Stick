import os
import logging
import subprocess
from telegram import Update, ReplyParameters
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup Logging agar kamu bisa cek error di Railway Logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ambil Token dari Environment Variable
TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Instruksi saat pengguna mengetik /start"""
    user_name = update.effective_user.first_name
    instructions = (
        f"Halo {user_name}! 👋\n\n"
        "Saya adalah Bot Pembuat Stiker Bergerak.\n"
        "**Cara Penggunaan:**\n"
        "1. Kirimkan video pendek ke saya.\n"
        "2. Durasi video wajib **maksimal 3 detik**.\n"
        "3. Saya akan otomatis mengirimkan stiker .webm untukmu.\n\n"
        "Silakan kirim videonya sekarang!"
    )
    await update.message.reply_text(instructions, parse_mode='Markdown')

async def convert_to_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fungsi utama merubah video menjadi stiker"""
    video = update.message.video or update.message.document
    
    # Validasi jika yang dikirim bukan video
    if not video or (hasattr(video, 'mime_type') and 'video' not in video.mime_type):
        await update.message.reply_text("❌ Mohon kirimkan file dalam format video.")
        return

    # Validasi durasi (Maksimal 3 detik sesuai aturan Telegram)
    if video.duration and video.duration > 3:
        await update.message.reply_text("❌ Video terlalu panjang! Maksimal durasi adalah 3 detik.")
        return

    status_msg = await update.message.reply_text("⏳ Sedang memproses... Tunggu sebentar ya.")
    
    file = await video.get_file()
    input_file = f"input_{file.file_id}.mp4"
    output_file = f"sticker_{file.file_id}.webm"

    try:
        # Download file dari Telegram
        await file.download_to_drive(input_file)

        # Proses Konversi menggunakan FFmpeg
        # Spesifikasi: 512px, No Audio, VP9 Codec, durasi 3s
        process = subprocess.run([
            'ffmpeg', '-i', input_file,
            '-vf', "scale='if(gt(iw,ih),512,-1)':'if(gt(iw,ih),-1,512)',fps=30",
            '-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0',
            '-t', '3', '-an', '-f', 'webm', output_file
        ], capture_output=True, text=True)

        if process.returncode != 0:
            raise Exception(f"FFmpeg Error: {process.stderr}")

        # Kirim hasil sebagai stiker (Document dengan format webm)
        await update.message.reply_document(
            document=open(output_file, 'rb'),
            filename="sticker.webm",
            caption="✅ Selesai! Klik file di atas lalu pilih 'Add to Favorites'."
        )

        except Exception as e:
        logger.error(f"Error: {e}")
        # Ubah baris ini agar kamu tahu error spesifiknya apa
        await update.message.reply_text(f"❌ Detail Error: {str(e)}")

    
    finally:
        # Bersihkan file sementara
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)
        await status_msg.delete()

def main():
    if not TOKEN:
        print("❌ Error: Variabel TELEGRAM_TOKEN belum diisi di Railway!")
        return

    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    # Menerima video baik dikirim sebagai video biasa atau dokumen
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, convert_to_sticker))

    print("Bot sedang berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
