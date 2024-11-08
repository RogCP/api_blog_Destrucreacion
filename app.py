import sqlite3
from flask import Flask, jsonify, request
import requests
from urllib.parse import unquote
import csv
import os
from bs4 import BeautifulSoup

app = Flask(__name__)
FEED_URL = 'https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fdestrucreacion.substack.com%2Ffeed'

# Función para crear la tabla de publicaciones
def create_table():
    conn = sqlite3.connect('baseblogDestrucreacion.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            guid TEXT PRIMARY KEY,
            title TEXT,
            pubDate TEXT,
            link TEXT,
            author TEXT,
            thumbnail TEXT,
            description TEXT,
            content TEXT,
            categories TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Función para guardar publicaciones obtenidas del feed en la base de datos
def save_posts_to_db(posts):
    conn = sqlite3.connect('baseblogDestrucreacion.db')
    cursor = conn.cursor()
    for post in posts:
        # Verificar si el GUID ya existe
        cursor.execute('SELECT 1 FROM posts WHERE guid = ?', (post.get('guid'),))
        exists = cursor.fetchone()

        # Solo insertar si el GUID no existe
        if not exists:
            cursor.execute('''
                INSERT INTO posts (guid, title, pubDate, link, author, thumbnail, description, content, categories)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post.get('guid'),
                post.get('title'),
                post.get('pubDate'),
                post.get('link'),
                post.get('author'),
                post.get('thumbnail'),
                post.get('description'),
                post.get('content'),
                ','.join(post.get('categories', []))
            ))

    conn.commit()
    conn.close()

# Función para importar publicaciones desde el CSV y los archivos HTML
def import_published_posts():
    # Conectar a la base de datos
    conn = sqlite3.connect('baseblogDestrucreacion.db')
    cursor = conn.cursor()

    # Asegurar que la tabla de posts existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            guid TEXT PRIMARY KEY,
            title TEXT,
            pubDate TEXT,
            link TEXT,
            author TEXT,
            thumbnail TEXT,
            description TEXT,
            content TEXT,
            categories TEXT
        )
    ''')
    conn.commit()

    # Ruta a la carpeta con los archivos HTML
    html_folder = 'posts_html'

    # Leer el archivo CSV y filtrar solo los posts publicados
    with open('posts_metadata.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Verificar si el post está publicado
            if row['is_published'].lower() == 'true':
                post_id = row['post_id']
                pub_date = row['post_date']
                title = row['title']
                subtitle = row['subtitle']  # Usaremos `subtitle` como `description`
                link = row['link']  # Usa el link como GUID y link

                # Construir la ruta del archivo HTML correspondiente
                html_file_path = os.path.join(html_folder, f'{post_id}.html')

                # Leer el contenido del archivo HTML si existe
                content = ""
                if os.path.exists(html_file_path):
                    with open(html_file_path, 'r') as html_file:
                        soup = BeautifulSoup(html_file, 'html.parser')
                        content = soup.get_text()  # Extrae solo el texto del HTML

                # Verificar si el GUID ya existe
                cursor.execute('SELECT 1 FROM posts WHERE guid = ?', (link,))
                exists = cursor.fetchone()

                # Solo insertar si el GUID no existe
                if not exists:
                    # Insertar el post en la base de datos
                    cursor.execute('''
                        INSERT INTO posts (guid, title, pubDate, link, author, thumbnail, description, content, categories)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        link,                # guid es el link
                        title,               # título del post
                        pub_date,            # fecha de publicación
                        link,                # link del post
                        "Rogerio Canales",   # autor
                        "",                  # thumbnail (vacío)
                        subtitle,            # description usando el subtitle
                        content,             # contenido del HTML
                        ""                   # categories (vacío)
                    ))

                    print(f"Publicación '{title}' agregada a la base de datos.")

    # Guardar y cerrar la conexión
    conn.commit()
    conn.close()

    print("Importación completada.")

# Llamadas a funciones de inicialización
create_table()
import_published_posts()

# Rutas de Flask
@app.route('/posts', methods=['GET'])
def get_posts():
    response = requests.get(FEED_URL)
    if response.status_code == 200:
        data = response.json()
        posts = data.get('items', [])
        save_posts_to_db(posts)  # Guarda las publicaciones en la base de datos
        return jsonify(posts)
    else:
        return jsonify({'error': 'No se pudo obtener el feed'}), 500

@app.route('/all_posts', methods=['GET'])
def get_all_posts():
    conn = sqlite3.connect('baseblogDestrucreacion.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts')
    rows = cursor.fetchall()
    conn.close()

    posts = []
    for row in rows:
        posts.append({
            'guid': row[0],
            'title': row[1],
            'pubDate': row[2],
            'link': row[3],
            'author': row[4],
            'thumbnail': row[5],
            'description': row[6],
            'content': row[7],
            'categories': row[8].split(',')
        })

    return jsonify(posts)

@app.route('/posts/<path:post_id>', methods=['GET'])
def get_post(post_id):
    conn = sqlite3.connect('baseblogDestrucreacion.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE guid = ?', (post_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        post = {
            'guid': row[0],
            'title': row[1],
            'pubDate': row[2],
            'link': row[3],
            'author': row[4],
            'thumbnail': row[5],
            'description': row[6],
            'content': row[7],
            'categories': row[8].split(',')
        }
        return jsonify(post)
    else:
        return jsonify({'error': 'Publicación no encontrada'}), 404

if __name__ == '__main__':
    app.run(debug=True)
