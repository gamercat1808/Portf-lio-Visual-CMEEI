from flask import Flask, render_template, request, redirect, url_for, flash
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'chave_secreta'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Banco de imagens
def init_image_db():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with sqlite3.connect('imagens.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS imagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                caminho TEXT
            )
        ''')


# Página inicial
@app.route('/')
def index():
    with sqlite3.connect('imagens.db') as conn:
        imagens = conn.execute('SELECT id, nome, caminho FROM imagens').fetchall()
    return render_template('index.html', imagens=imagens)


# Página de formulário para renomear
@app.route('/rename/<int:imagem_id>')
def rename_page(imagem_id):
    with sqlite3.connect('imagens.db') as conn:
        imagem = conn.execute('SELECT id, nome FROM imagens WHERE id=?', (imagem_id,)).fetchone()

    if imagem:
        return render_template('rename.html', imagem=imagem)
    else:
        flash('Imagem não encontrada.')
        return redirect(url_for('index'))


# Processo de renomear
@app.route('/rename/<int:imagem_id>', methods=['POST'])
def rename(imagem_id):
    novo_nome = request.form['novo_nome'].strip()

    if not (novo_nome.endswith('.png') or novo_nome.endswith('.jpg') or novo_nome.endswith('.jpeg') or novo_nome.endswith('.gif')):
        novo_nome += '.png'

    with sqlite3.connect('imagens.db') as conn:
        imagem = conn.execute('SELECT caminho FROM imagens WHERE id=?', (imagem_id,)).fetchone()

        if imagem:
            caminho_antigo = imagem[0]
            novo_caminho = os.path.join(UPLOAD_FOLDER, novo_nome)

            if not os.path.exists(caminho_antigo):
                flash('Arquivo original não encontrado.')
                return redirect(url_for('index'))

            if os.path.exists(novo_caminho):
                flash('Já existe uma imagem com esse nome.')
                return redirect(url_for('index'))

            os.rename(caminho_antigo, novo_caminho)

            conn.execute('UPDATE imagens SET nome=?, caminho=? WHERE id=?', (novo_nome, novo_caminho, imagem_id))
            conn.commit()

            flash('Imagem renomeada com sucesso!')
        else:
            flash('Imagem não encontrada.')

    return redirect(url_for('index'))


# Upload de imagem
@app.route('/upload', methods=['POST'])
def upload():
    imagem = request.files['imagem']
    if imagem and imagem.filename:
        caminho = os.path.join(UPLOAD_FOLDER, imagem.filename)
        imagem.save(caminho)

        with sqlite3.connect('imagens.db') as conn:
            conn.execute('INSERT INTO imagens (nome, caminho) VALUES (?, ?)', (imagem.filename, caminho))
            conn.commit()

        flash('Imagem enviada com sucesso!')
    else:
        flash('Nenhum arquivo selecionado.')

    return redirect(url_for('index'))


# Deletar imagem
@app.route('/delete/<int:imagem_id>')
def delete(imagem_id):
    with sqlite3.connect('imagens.db') as conn:
        imagem = conn.execute('SELECT caminho FROM imagens WHERE id=?', (imagem_id,)).fetchone()

        if imagem:
            caminho = imagem[0]
            if os.path.exists(caminho):
                os.remove(caminho)

            conn.execute('DELETE FROM imagens WHERE id=?', (imagem_id,))
            conn.commit()

            flash('Imagem deletada com sucesso!')
        else:
            flash('Imagem não encontrada.')

    return redirect(url_for('index'))


# Inicializa o banco e executa
if __name__ == '__main__':
    init_image_db()
    app.run(debug=True)
