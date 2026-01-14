import os
import requests
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Tenta importar moviepy com suporte a novas versões
try:
    from moviepy.editor import VideoFileClip, vfx
except ImportError:
    from moviepy import VideoFileClip, vfx

app = Flask(__name__)
CORS(app)

# Configuração de Pastas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "downloads")
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


def limpar_arquivos_antigos():
    """Remove vídeos com mais de 1 hora para não lotar a VPS"""
    while True:
        now = time.time()
        for f in os.listdir(OUTPUT_FOLDER):
            f_path = os.path.join(OUTPUT_FOLDER, f)
            if os.stat(f_path).st_mtime < now - 3600:
                os.remove(f_path)
                print(f"🗑️ Vídeo antigo removido: {f}")
        time.sleep(1800)  # Roda a cada 30 min


# Inicia a limpeza em segundo plano
threading.Thread(target=limpar_arquivos_antigos, daemon=True).start()


@app.route('/recriar', methods=['POST'])
def recriar():
    try:
        dados = request.json
        url_video = dados.get('link_video')
        produto = dados.get('produto', 'Produto')

        print(f"🎬 Recriando anúncio para: {produto}")

        temp_input = os.path.join(BASE_DIR, f"temp_{int(time.time())}.mp4")
        nome_saida = f"anuncio_{int(time.time())}.mp4"
        caminho_saida = os.path.join(OUTPUT_FOLDER, nome_saida)

        # 1. Download
        r = requests.get(url_video)
        with open(temp_input, 'wb') as f:
            f.write(r.content)

        # 2. Edição IA (Torna o vídeo único)
        clip = VideoFileClip(temp_input)
        # Espelha + Leve zoom + Ajuste de cor
        video_unico = (clip.fx(vfx.mirror_x)
                           .fx(vfx.colorx, 1.1)
                       # Pequeno zoom para mudar pixels
                           .resize(height=clip.h * 1.05))

        video_unico.write_videofile(
            caminho_saida, codec="libx264", audio_codec="aac", fps=24)

        clip.close()
        video_unico.close()
        os.remove(temp_input)

        # O link agora será dinâmico
        return jsonify({
            "success": True,
            "video_url": f"/baixar/{nome_saida}",
            "copy": f"🚀 {produto} - Exclusivo Genium IA.\nGaranta o seu agora! 🛒"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/baixar/<filename>')
def baixar(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)


if __name__ == "__main__":
    # Porta padrão para VPS ou Nuvem
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
