import sqlite3
import csv
import os
from bs4 import BeautifulSoup

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

            # Insertar o actualizar el post en la base de datos
            cursor.execute('''
                INSERT OR REPLACE INTO posts (guid, title, pubDate, link, author, thumbnail, description, content, categories)
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