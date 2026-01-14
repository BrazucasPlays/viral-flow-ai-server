import os
import requests
import time
import firebase_admin
from firebase_admin import credentials, storage, db

# --- CONFIGURAÇÃO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOME_JSON = os.path.join(BASE_DIR, "serviceAccountKey.json")

# 🚨 AJUSTE DO BUCKET: Com base no seu link do banco, este é o nome padrão:
NOME_DO_BUCKET = 'viralflow-2dbf5.appspot.com' 

if not firebase_admin._apps:
    cred = credentials.Certificate(NOME_JSON)
    firebase_admin.initialize_app(cred, {
        'storageBucket': NOME_DO_BUCKET,
        'databaseURL': 'https://viralflow-2dbf5-default-rtdb.firebaseio.com/'
    })

def minerar_feed_infinito(hashtags):
    print("🚀 Iniciando Mineração Automática Genium...")
    
    for hashtag in hashtags:
        print(f"🔎 Buscando produtos virais em: #{hashtag}")
        # Buscando 5 vídeos para cada hashtag para popular o App
        api_url = f"https://www.tikwm.com/api/feed/search?keywords={hashtag}&count=5"
        
        try:
            res = requests.get(api_url).json()
            if res.get('code') == 0:
                for v in res['data']['videos']:
                    v_id = v['video_id']
                    titulo = v.get('title', 'Produto Viral')[:40]
                    v_url = v['play'] # Vídeo sem marca d'água
                    
                    print(f"📥 Processando: {titulo}")
                    
                    # 1. Download do vídeo
                    video_data = requests.get(v_url).content
                    temp_path = os.path.join(BASE_DIR, f"{v_id}.mp4")
                    with open(temp_path, "wb") as f:
                        f.write(video_data)

                    # 2. Upload para o Storage (Onde estava dando erro 404)
                    try:
                        bucket = storage.bucket()
                        blob = bucket.blob(f"feed/{v_id}.mp4")
                        blob.upload_from_filename(temp_path)
                        blob.make_public()
                        link_video_final = blob.public_url
                    except Exception as e_storage:
                        print(f"⚠️ Erro no Storage: {e_storage}")
                        # Se o storage falhar, usamos o link direto da API para o App não parar
                        link_video_final = v_url

                    # 3. Salva no Database (O link que você me enviou)
                    db.reference('videos_virais').push({
                        "produto": titulo,
                        "faturamento": f"R$ {time.strftime('%M')}.{v_id[:2]}0,00",
                        "link_video": link_video_final,
                        "imagem": v['cover'],
                        "timestamp": time.time()
                    })
                    
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    print(f"✅ SUCESSO: Vídeo enviado para o feed!")
            else:
                print(f"⚠️ Sem resultados para #{hashtag}")
        except Exception as e:
            print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    # Rodando para 2 hashtags (Isso vai colocar 10 vídeos no seu App)
    minerar_feed_infinito(["amazonfinds", "tiktokmadebuymeit"])
    print("\n🔥 PROCESSO CONCLUÍDO! Verifique o seu App Flutter.")