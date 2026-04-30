import os
import logging
import subprocess
import shutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. Ambil Token dari Environment Variable
TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fungsi /start dengan instruksi interaktif"""
    text = (
        "🎬 **Bot Video ke Stiker Bergerak**\n\n"
        "Kirimkan video pendek (maksimal 3 detik) dan saya akan "
        "mengubahnya menjadi stiker WebM yang siap kamu simpan!\n\n"
        "**Ketentuan:**\n"
        "• Durasi video: 1 - 3 detik\n"
        "• Format: Video atau Video Note"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memproses video yang dikirim pengguna"""
    # Deteksi video dari pesan biasa atau dokumen
    video = update.message.video or update.message.document or update.message.video_note
    
    # Cek apakah itu benar-benar video
    if update.message.document and not update.message.document.mime_type.startswith('video/'):
        return

    # Validasi Durasi
    if video.duration and video.duration > 3.5: # Toleransi sedikit
        await update.message.reply_text("❌ Video kepanjangan! Maksimal 3 detik saja.")
        return

    # Cek apakah FFmpeg tersedia di server
    if not shutil.which('ffmpeg'):
        await update.message.reply_text("❌ Sistem error: FFmpeg tidak ditemukan di server Railway.")
        return

    status_msg = await update.message.reply_text("⏳ Sedang memproses... Tunggu ya!")
    
    file = await video.get_file()
    input_path = f"in_{file.file_id}.mp4"
    output_path = f"out_{file.file_id}.webm"

    try:
        await file.download_to_drive(input_path)

        # Proses Konversi dengan FFmpeg
        # Spesifikasi Telegram: VP9, No Audio, 512px, <256KB
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', "scale='if(gt(iw,ih),512,-1)':'if(gt(iw,ih),-1,512)',fps=30",
            '-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0',
            '-t', '3', '-an', '-f', 'webm', output_path
        ]
        
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode != 0:
            logger.error(f"FFmpeg Error: {process.stderr}")
            raise Exception("Gagal mengonversi video.")

        # Kirim hasil sebagai stiker (Document dengan mime-type webm)
        await update.message.reply_document(
            document=open(output_path, 'rb'),
            filename="sticker.webm",
            caption="✅ Berhasil! Klik file lalu simpan ke favorit."
        )

    except Exception as e:
        logger.error(f"General Error: {e}")
        await update.message.reply_text(f"❌ Terjadi kesalahan teknis.")
    
    finally:
        # Hapus file sementara agar storage server tidak penuh
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        await status_msg.delete()

def main():
    if not TOKEN:
        print("❌ Masukkan TELEGRAM_TOKEN di Variables Railway!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO | filters.VIDEO_NOTE, handle_video))

    print("Bot Berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()
        
