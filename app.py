from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario, Empresa, Tema, EstiloDeEscrita, TextosUsuarios, MetaAds, InstagramData, PostsInstagram,Ads
from newsapi import NewsApiClient
from forms import UsuarioForm, EmpresaForm, TemaForm, EstiloDeEscritaForm
from sqlalchemy.exc import IntegrityError
from openai import OpenAI
import time
import requests
import json
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from collections import Counter
from pytrends.request import TrendReq
import base64
from sqlalchemy import desc
import traceback


from scraping_instagram_social import consulta_api_e_salva_db
from scraping_meta_ads import atualizar_dados_meta_ads

load_dotenv()  # This is the new line


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Obter a URL do banco de dados do ambiente e ajustar se necessário
url = os.getenv("DATABASE_URL")
if url and url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

# Configurar a URI do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = url or 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def verify_password(self, password):
    if self.password_hash is None:
        return False
    return check_password_hash(self.password_hash, password)

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("dshau")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        print("USER: ", username)
        if user:
            print("DHSUASUDSU")
            print(f"Usuário: {username}, Senha fornecida: {password}")  # Debug
            print(f"Hash da senha armazenada: {user.password_hash}")  # Debug

            if user.verify_password(password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Senha incorreta.')
        else:
            flash('Usuário não encontrado.')

    return render_template('login.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


from flask import Flask, render_template
from pytrends.request import TrendReq


newsapi = NewsApiClient(api_key='4e6f6197a3b847c088f6d665828e4d9b')

# Rota para a página inicial acessível sem login
# Rota para a página de aterrissagem
@app.route('/')
def landing_page():
    return render_template('landing_page.html')


def scrape_trends24():
    url = "https://trends24.in/brazil/"
    trends_list = []
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        trends = soup.find_all('div', class_='trend-card')

        all_trends = []
        for trend in trends:
            trend_items = trend.find_all('a')
            for item in trend_items:
                all_trends.append(item.text.strip())

        trend_counts = Counter(all_trends)
        top_trends = trend_counts.most_common(10)  # Obtém as 10 principais tendências

        for trend, count in top_trends:
            trends_list.append({'name': trend, 'count': count})

    except requests.RequestException as e:
        print(f"Erro ao acessar a página: {e}")

    return trends_list

@app.route('/cadastrar/empresa', methods=['GET', 'POST'])
@login_required
def cadastrar_empresa():
    if not current_user.is_admin:
        abort(403)  # Forbidden
    if request.method == 'POST':
        empresa = Empresa(
            nome_contato=request.form.get('nome_contato'),
            email_contato=request.form.get('email_contato'),
            telefone_contato=request.form.get('telefone_contato'),
            endereco_empresa=request.form.get('endereco_empresa'),
            setor_atuacao=request.form.get('setor_atuacao'),
            tamanho_empresa=request.form.get('tamanho_empresa'),
            descricao_empresa=request.form.get('descricao_empresa'),
            objetivos_principais=request.form.get('objetivos_principais'),
            historico_interacoes=request.form.get('historico_interacoes')
        )
        db.session.add(empresa)
        db.session.commit()
        return redirect(url_for('listar_empresas'))
    return render_template('cadastrar_empresa.html')

@app.route('/atualizar/empresa/<int:id>', methods=['GET', 'POST'])
def atualizar_empresa(id):
    empresa = Empresa.query.get(id)
    empresas_instagram = Empresa.query.filter(Empresa.vincular_instagram != '').all()
    empresas_anuncio = Empresa.query.filter(Empresa.vincular_anuncio != '').all()

    if request.method == 'POST':
        print(request.form)
        empresa.nome_contato = request.form['nome_contato']
        empresa.email_contato = request.form['email_contato']
        empresa.telefone_contato = request.form['telefone_contato']
        empresa.endereco_empresa = request.form['endereco_empresa']
        empresa.setor_atuacao = request.form['setor_atuacao']
        empresa.tamanho_empresa = request.form['tamanho_empresa']
        empresa.descricao_empresa = request.form['descricao_empresa']
        empresa.objetivos_principais = request.form['objetivos_principais']
        empresa.historico_interacoes = request.form['historico_interacoes']
        empresa.vincular_instagram = request.form.get('vincular_instagram', '')
        empresa.vincular_anuncio = request.form.get('vincular_anuncio', '')
        db.session.commit()
        return redirect(url_for('listar_empresas'))
    
    return render_template('atualizar_empresa.html', empresa=empresa, empresas_instagram=empresas_instagram, empresas_anuncio=empresas_anuncio)

@app.route('/get_ads')
def get_ads():
    empresa_selecionada = request.args.get('empresa')
    anuncios = Ads.query.join(Empresa).filter(Empresa.nome_contato == empresa_selecionada).all()
    anuncios_dict = [anuncio.to_dict() for anuncio in anuncios]
    return jsonify(anuncios_dict)

@app.route('/get_empresas_id', methods=['GET'])
def get_empresas_id():
    empresa_name = request.args.get('name')
    print(empresa_name)
    empresa = Empresa.query.filter_by(nome_contato=empresa_name).first()
    print(empresa)
    if empresa:
        return jsonify({'id': empresa.id})
    else:
        return jsonify({'error': 'Empresa não encontrada'}), 404

@app.route('/empresas', methods=['GET'])
@login_required
def listar_empresas():
    if current_user.is_admin:
        empresas = Empresa.query.all()
    else:
        empresas = Empresa.query.filter_by(id=current_user.id_empresa).all()
    return render_template('listar_empresas.html', empresas=empresas)

def fetch_google_trends():
    pytrends = TrendReq(hl='pt-BR', tz=360)
    trends_list = []
    try:
        trends = pytrends.trending_searches(pn='brazil')
        for index, trend in enumerate(trends[0]):
            trends_list.append({'name': trend, 'index': index + 1})
    except Exception as e:
        print(f"Erro ao buscar tendências: {e}")

    return trends_list


# Rota para a home que requer login
@app.route('/home')
@login_required
def home():
    twitter_trends = scrape_trends24()
    google_trends = fetch_google_trends()
    return render_template('home.html', twitter_trends=twitter_trends, google_trends=google_trends)

@app.route('/verificar_post_existente', methods=['POST'])
def verificar_post_existente():
    data = request.get_json()
    id = data.get('id')
    if not id:
        return jsonify({'error': 'id não fornecido'}), 400

    post = PostsInstagram.query.filter_by(id=id).first()
    if post is None:
        return jsonify({'exists': False})
    else:
        return jsonify({'exists': True})

@app.route('/verificar_anuncio_existente', methods=['POST'])
def verificar_anuncio_existente():
    data = request.get_json()
    id = data.get('id')
    cpm = data.get('cpm')
    ctr = data.get('ctr')
    cpc = data.get('cpc')

    if not id:
        return jsonify({'error': 'ID não fornecido'}), 400
    if cpm is None or ctr is None or cpc is None:
        return jsonify({'error': 'CPM, CTR ou CPC não fornecido'}), 400

    anuncio = Ads.query.filter_by(id=id, cpm=cpm, ctr=ctr, cpc=cpc).first()
    if anuncio is None:
        return jsonify({'exists': False})
    else:
        return jsonify({'exists': True})



@app.route('/api/analise_posts')
def api_analise_posts():
    empresa = request.args.get('empresa')
    analise = analise_post_instagram(empresa)
    print(analise)
    return jsonify(analise)

@app.route('/listar/posts', methods=['GET'])
def listar_posts():
    empresas = Empresa.query.filter(Empresa.vincular_instagram.isnot(None)).all()
    posts = PostsInstagram.query.filter(PostsInstagram.timestamp.isnot(None)).all()
    return render_template('listar_posts.html', posts=posts, empresas=empresas)

@app.route('/api/salvar_analise', methods=['POST'])
def salvar_analise():
    try:
        if request.method == 'POST':
            analise = AnaliseInstagram(
                id=request.form.get('id'),
                nome_empresa=request.form.get('nome_empresa'),
                data_criacao=request.form.get('data_criacao'),
                analise=request.form.get('analise'),
            )
            db.session.add(analise)
            db.session.commit()
            return jsonify({'message': 'Análise salva com sucesso!'}), 200  # Adicione essa linha
            
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Falha ao salvar análise!'}), 500


@app.route('/api/posts', methods=['GET'])
def api_posts():
    empresa_selecionada = request.args.get('empresa')
    if empresa_selecionada:
        posts = PostsInstagram.query.filter(PostsInstagram.nome_empresa == empresa_selecionada).order_by(desc(PostsInstagram.timestamp)).all()
    else:
        posts = PostsInstagram.query.order_by(desc(PostsInstagram.timestamp)).all()

    posts = [post.to_dict() for post in posts]  # Convert each post to a dictionary
    return jsonify(posts)

@app.route('/admin/usuarios', methods=['GET', 'POST'])
@login_required
def admin_usuarios():
    if not current_user.is_admin:  # Verifica se o usuário é administrador
        flash('Acesso negado. Apenas administradores.', 'danger')
        return redirect(url_for('index'))  # Redireciona se não for administrador

    form = UsuarioForm()
    if form.validate_on_submit():
        # Verifica se está criando um novo usuário ou atualizando um existente
        if form.user_id.data:
            usuario = Usuario.query.get_or_404(form.user_id.data)
            usuario.username = form.username.data
            usuario.nome = form.username.data  # Atribui o valor de username a nome
            usuario.id_empresa = form.id_empresa.data
            # Atualiza a senha se um novo valor foi fornecido
            if form.new_password.data:
                usuario.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
        else:
            hashed_password = generate_password_hash(form.password.data)
            empresa = Empresa.query.first()
            newUser = Usuario(
                nome=form.username.data,
                sobrenome=form.username.data,
                email=form.username.data,
                celular='99999999',
                status='Ativo',
                username=form.username.data,
                password=form.password.data,
                id_empresa=form.id_empresa.data,
                is_admin=True
            )
            print(newUser)
            db.session.add(newUser)
            db.session.commit()
           
        # Redireciona para a mesma página para limpar o formulário ou realizar mais operações
        return redirect(url_for('admin_usuarios'))

    usuarios = Usuario.query.all()
    return render_template('admin_usuarios.html', form=form, usuarios=usuarios)


@app.route('/admin/empresas', methods=['GET', 'POST'])
@login_required
def admin_empresas():
    if not current_user.is_admin:  # Adiciona esta linha para verificar se é admin
        flash('Acesso negado. Apenas administradores.', 'danger')
        return redirect(url_for('index'))  # Redireciona se não for admin
    form = EmpresaForm()
    if form.validate_on_submit():
        empresa = Empresa(nome=form.nome.data)
        db.session.add(empresa)
        db.session.commit()
        flash('Empresa criada com sucesso!', 'success')
        return redirect(url_for('admin_empresas'))
    empresas = Empresa.query.all()
    return render_template('admin_empresas.html', form=form, empresas=empresas)



@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    # Verifica se o usuário atual tem o username 'admin'
    if current_user.username != 'admin':
        flash('Acesso negado. Apenas o administrador pode editar usuários.', 'danger')
        return redirect(url_for('admin_usuarios'))

    usuario = Usuario.query.get_or_404(id)

    # Evita que o usuário 'admin' seja editado por alguém que não seja ele mesmo
    if usuario.username == 'admin' and current_user.username != 'admin':
        flash('Não é possível editar o usuário administrador.', 'danger')
        return redirect(url_for('admin_usuarios'))

    form = UsuarioForm(obj=usuario)

    if form.validate_on_submit():
        usuario.username = form.username.data
        usuario.id_empresa = form.id_empresa.data

        # Atualiza a senha se um novo valor foi fornecido e não é vazio
        if form.new_password.data:
            usuario.password_hash = generate_password_hash(form.new_password.data)

        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('admin_usuarios'))

    return render_template('editar_usuario.html', form=form, usuario=usuario)


@app.route('/excluir_usuario/<int:id>', methods=['POST'])
@login_required
def excluir_usuario(id):
    # Verifica se o usuário atual tem o username 'admin'
    if current_user.username != 'admin':
        flash('Acesso negado. Apenas o administrador pode excluir usuários.', 'danger')
        return redirect(url_for('admin_usuarios'))

    usuario = Usuario.query.get_or_404(id)
    # Evita que o usuário 'admin' seja excluído
    if usuario.username == 'admin':
        flash('Não é possível excluir o usuário administrador.', 'danger')
        return redirect(url_for('admin_usuarios'))

    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin_usuarios'))



@app.route('/editar_empresa/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    form = EmpresaForm(obj=empresa)
    if form.validate_on_submit():
        empresa.nome_contato = form.nome.data
        db.session.commit()
        flash('Empresa atualizada com sucesso!', 'success')
        return redirect(url_for('admin_empresas'))
    # Note que 'empresa=empresa' está sendo passado para o contexto do template.
    return render_template('editar_empresa.html', form=form, empresa=empresa)




@app.route('/deletar_empresa/<int:id>', methods=['POST'])
@login_required
def deletar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if empresa.usuarios:  # Substitua 'usuarios' pelo nome real da relação no seu modelo
        flash(
            'Não é possível excluir uma empresa que possui usuários vinculados. Desvincule os usuários antes de excluir.',
            'danger')
        return redirect(url_for('admin_empresas'))

    try:
        db.session.delete(empresa)
        db.session.commit()
        flash('Empresa excluída com sucesso!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Não é possível excluir esta empresa porque ela tem usuários vinculados.', 'danger')

    return redirect(url_for('admin_empresas'))


@app.route('/admin/temas', methods=['GET', 'POST'])
@login_required
def admin_temas():
    form = TemaForm()
    if form.validate_on_submit():
        # Conta quantos temas a empresa do usuário atual já possui
        count = Tema.query.filter_by(id_empresa=current_user.id_empresa).count()

        # Verifica se a empresa já tem 3 temas
        if count >= 3:
            flash('A quantidade máxima de temas para cada empresa é 3.', 'danger')
            return redirect(url_for('admin_temas'))

        # Se tiver menos de 3 temas, permite a criação de um novo
        novo_tema = Tema(nome=form.nome.data, usuario_id=current_user.id, id_empresa=current_user.id_empresa)
        db.session.add(novo_tema)
        db.session.commit()
        flash('Tema criado com sucesso!', 'success')
        return redirect(url_for('admin_temas'))

    temas = Tema.query.filter_by(id_empresa=current_user.id_empresa).all()
    return render_template('admin_temas.html', form=form, temas=temas)


@app.route('/editar_tema/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_tema(id):
    tema = Tema.query.get_or_404(id)
    form = TemaForm(obj=tema)

    if form.validate_on_submit():
        tema.nome = form.nome.data
        # Se houver mais campos para atualizar, faça isso aqui
        db.session.commit()
        flash('Tema atualizado com sucesso!', 'success')
        return redirect(url_for('admin_temas'))

    return render_template('editar_tema.html', form=form)


@app.route('/excluir_tema/<int:id>', methods=['POST'])
@login_required
def excluir_tema(id):
    tema = Tema.query.get_or_404(id)
    db.session.delete(tema)
    db.session.commit()
    flash('Tema excluído com sucesso!', 'success')
    return redirect(url_for('admin_temas'))

@app.route('/admin/estilos_de_escrita', methods=['GET', 'POST'])
@login_required
def admin_estilos_de_escrita():
    form = EstiloDeEscritaForm()
    if form.validate_on_submit():
        # Verifica se a empresa do usuário já possui um estilo de escrita
        existe_estilo = EstiloDeEscrita.query.filter_by(id_empresa=current_user.id_empresa).first()
        if existe_estilo:
            flash('Cada empresa pode ter apenas um estilo de escrita.', 'danger')
        else:
            novo_estilo = EstiloDeEscrita(estilo=form.estilo.data, usuario_id=current_user.id, id_empresa=current_user.id_empresa)
            db.session.add(novo_estilo)
            db.session.commit()
            flash('Estilo de escrita criado com sucesso!', 'success')
        return redirect(url_for('admin_estilos_de_escrita'))

    estilos = EstiloDeEscrita.query.filter_by(id_empresa=current_user.id_empresa).all()
    return render_template('admin_estilos_de_escrita.html', form=form, estilos=estilos)

@app.route('/editar_estilo/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_estilo(id):
    estilo = EstiloDeEscrita.query.get_or_404(id)
    form = EstiloDeEscritaForm(obj=estilo)
    if form.validate_on_submit():
        estilo.estilo = form.estilo.data
        db.session.commit()
        flash('Estilo de escrita atualizado com sucesso!', 'success')
        return redirect(url_for('admin_estilos_de_escrita'))
    # Certifique-se de passar o objeto 'estilo' para o template
    return render_template('editar_estilo.html', form=form, estilo=estilo)


@app.route('/excluir_estilo/<int:id>', methods=['POST'])
@login_required
def excluir_estilo(id):
    estilo = EstiloDeEscrita.query.get_or_404(id)
    db.session.delete(estilo)
    db.session.commit()
    flash('Estilo de escrita excluído com sucesso!', 'success')
    return redirect(url_for('admin_estilos_de_escrita'))

###############################################################################################




openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("A chave API do OpenAI não foi configurada corretamente.")


# -------------- Parte 01 ---------------------------------------------------------------------------------------


# Leia os temas de uma planilha do Excel
#df_temas = pd.read_excel('temas.xlsx')

@app.route('/rodar/')
@login_required
def rodar():
    # Use sua chave da Google Custom Search API
    api_key_google = os.getenv('API_KEY_GOOGLE')
    # Use seu Custom Search Engine ID
    cse_id = os.getenv('CSE_ID')

    id = current_user.id

    tema = Tema.query.filter_by(usuario_id=id).first()
    tema_nome = tema.nome if tema else 'Não definido'
    tema = tema_nome

    # Busca o estilo de escrita associado ao usuário
    estilo_de_escrita = EstiloDeEscrita.query.filter_by(usuario_id=id).first()
    estilo = estilo_de_escrita.estilo if estilo_de_escrita else 'Não definido'
    estilo_de_escrita = estilo

    print(id)
    print(tema)
    print(estilo_de_escrita)
    flash('As notícias estão sendo geradas e você será notificado quando estiverem prontas.', 'info')

    if tema != 'Não definido' and estilo_de_escrita != 'Não definido':

        df_temas = pd.DataFrame({'Coluna': [tema]})
        # Converte a coluna de temas em uma lista
        temas = df_temas.iloc[:, 0].tolist()
        # Lista para armazenar os resultados
        resultados = []
        # Loop através dos temas
        for tema in temas:
            url = f"https://www.googleapis.com/customsearch/v1?q={tema} Brasil&cx={cse_id}&key={api_key_google}&num=3&lr=lang_pt"

            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    print(f'Notícias do Google para o tema: {tema}')
                    for noticia in data['items']:
                        resultados.append({'Tema': tema, 'Notícia': noticia['title'], 'Fonte': 'Google'})
                else:
                    print(f'Sem notícias para o tema: {tema}')
            else:
                print(f"Erro na API para o tema {tema}. Código de status: {response.status_code}")
                print(response.json())

            time.sleep(10)

        # Converte a lista de resultados em um DataFrame
        df = pd.DataFrame(resultados)

        # Now, use the if statement to test if 'df' is not null
        if df is not None and not df.empty:

            # ------------- Parte 02 --------------------------------------------------------------------------------------------------------
            def perguntar_gpt(pergunta, messages):
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + openai_api_key
                }

                # Adiciona a pergunta atual
                messages.append({"role": "user", "content": pergunta})

                data = {
                    "model": "gpt-4",
                    "messages": messages
                }

                backoff_time = 1  # Começamos com um tempo de espera de 1 segundo
                while True:
                    try:
                        response = requests.post(url, headers=headers, data=json.dumps(data))
                        response.raise_for_status()

                        # Adiciona a resposta do modelo à lista de mensagens
                        resp_content = response.json()['choices'][0]['message']['content']
                        messages.append({"role": "assistant", "content": resp_content})

                        # Interpreta a resposta como um objeto JSON
                        resp_json = json.loads(resp_content)

                        return resp_json, messages
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code in (429, 520, 502, 503):  # Limite de requisições atingido ou erro de servidor
                            print(f"Erro {e.response.status_code} atingido. Aguardando antes de tentar novamente...")
                            time.sleep(backoff_time)  # Aguarda antes de tentar novamente
                            backoff_time *= 2  # Aumenta o tempo de espera
                        else:
                            raise


            # Inicializa a lista de mensagens para o GPT-4
            messages = []

            # Inicializa a lista de resultados
            resultados = []

            # Loop através das notícias
            for i, row in df.iterrows():
                tema = row['Tema']
                noticia = row['Notícia']

                # Prepara a pergunta para o GPT-4
                pergunta = f'quais o termos de buscas ideias para achar noticias sobre esse tema: {noticia}\n\nPor favor, responda em formato JSON com as chaves "termo1", "termo2" e "termo3".'

                # Chama a função perguntar_gpt
                termos_busca, messages = perguntar_gpt(pergunta, messages)

                # Adiciona o resultado à lista de resultados
                resultados.append(
                    {'Tema': tema, 'Notícia': noticia, 'Termo 1': termos_busca['termo1'], 'Termo 2': termos_busca['termo2'],
                     'Termo 3': termos_busca['termo3']})

            # Converte a lista de resultados em um DataFrame
            df_termos_busca = pd.DataFrame(resultados)

            # ------------- Fim Parte 02 ----------------------------------------------------------------------------------------------------

            # ------------- Parte 03 --------------------------------------------------------------------------------------------------------
            def get_links_from_google(term, api_key, cse_id):
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "q": term,
                    "key": api_key,
                    "cx": cse_id,
                    "num": 3  # Contagem define o número de resultados por busca
                }

                links = []

                try:
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    search_results = response.json()

                    for result in search_results.get("items", []):
                        links.append(result["link"])

                except Exception as e:
                    print(f"Erro ao buscar termo '{term}': {e}")

                return links

            # Use sua chave da Google Custom Search API
            api_key_google = os.getenv('API_KEY_GOOGLE')
            # Use seu Custom Search Engine ID
            cse_id = os.getenv('CSE_ID')

            # Adiciona as novas colunas para os termos de busca
            for i in range(1, 4):
                col_name = f'Termo {i}'
                df_termos_busca[f'Link {col_name} 1'] = None
                df_termos_busca[f'Link {col_name} 2'] = None
                df_termos_busca[f'Link {col_name} 3'] = None

                for index, row in df_termos_busca.iterrows():
                    term = row[col_name]
                    links = get_links_from_google(term, api_key_google, cse_id)

                    # Adiciona os links às novas colunas
                    for j, link in enumerate(links):
                        df_termos_busca.at[index, f'Link {col_name} {j + 1}'] = link

            # ------------- Fim Parte 03 ----------------------------------------------------------------------------------------------------

            # ------------- Parte 04 --------------------------------------------------------------------------------------------------------
            def get_text_from_url(url):
                try:
                    print(f"Buscando texto do URL: {url}")

                    # Faz a solicitação com um tempo limite
                    response = requests.get(url, timeout=10)

                    # Se a resposta não for bem-sucedida, retorne None
                    if response.status_code != 200:
                        print(f"Não foi possível obter dados de {url}. Status code: {response.status_code}")
                        return None

                    # Analisa o HTML com BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Extrai o texto do corpo principal da página
                    paragraphs = soup.find_all('p')
                    text = ' '.join(p.get_text() for p in paragraphs)

                    # Pausa de 1 segundo para evitar muitas requisições rápidas
                    time.sleep(1)

                    return text
                except Exception as e:
                    print(f"Erro ao processar o URL {url}. Erro: {e}")
                    return None


            # Imprime os nomes das colunas para verificação
            print(df_termos_busca.columns)

            # Processa os links
            columns_mapping = {
                'Texto Link Termo 1 1': 'Link Termo 1 1',
                'Texto Link Termo 1 2': 'Link Termo 1 2',
                'Texto Link Termo 1 3': 'Link Termo 1 3',
                'Texto Link Termo 2 1': 'Link Termo 2 1',
                'Texto Link Termo 2 2': 'Link Termo 2 2',
                'Texto Link Termo 2 3': 'Link Termo 2 3',
                'Texto Link Termo 3 1': 'Link Termo 3 1',
                'Texto Link Termo 3 2': 'Link Termo 3 2',
                'Texto Link Termo 3 3': 'Link Termo 3 3'
            }

            for new_col, old_col in columns_mapping.items():
                df_termos_busca[new_col] = df_termos_busca[old_col].apply(get_text_from_url)

            # ------------- Fim Parte 04 ----------------------------------------------------------------------------------------------------

            # ------------- Parte 05 --------------------------------------------------------------------------------------------------------
            def perguntar_gpt(pergunta, messages):
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + os.getenv('OPENAI_API_KEY')
                }
                messages.append({"role": "user", "content": pergunta})
                data = {
                    "model": "gpt-4",
                    "messages": messages
                }
                backoff_time = 1
                while True:
                    try:
                        response = requests.post(url, headers=headers, data=json.dumps(data))
                        response.raise_for_status()
                        messages.append({"role": "assistant", "content": response.json()['choices'][0]['message']['content']})
                        return response.json()['choices'][0]['message']['content'], messages
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code in (429, 520, 502, 503):
                            print(f"Erro {e.response.status_code} atingido. Aguardando antes de tentar novamente...")
                            time.sleep(backoff_time)
                            backoff_time *= 2
                        else:
                            raise


            # Imprimir colunas para verificação
            print("Colunas no DataFrame:")
            print(df_termos_busca.columns)

            # Iterar por cada linha e cada coluna de texto relevante
            for index, row in df_termos_busca.iterrows():
                for termo_num in range(1, 4):
                    for versao_num in range(1, 4):
                        col_name = f'Texto Link Termo {termo_num} {versao_num}'
                        new_col_name = f'Factos Relevantes Termo {termo_num} {versao_num}'

                        try:
                            texto = str(row[col_name])
                        except KeyError:
                            print(f"Coluna {col_name} não encontrada. Continuando...")
                            continue

                        if not texto or texto.lower() == 'nan':
                            continue

                        texto = texto[:2048]
                        pergunta = f"{texto}\n\nQuais são os fatos mais importantes dessa notícia?"

                        print(f"Enviando a seguinte pergunta para o GPT-4: {pergunta}")

                        resposta, messages = perguntar_gpt(pergunta, [{"role": "system",
                                                                       "content": "Você é um assistente de escrita e precisa extrair os fatos mais importantes dessa notícia. Como data de acontecimento, principais personagens envolvidos e sitações. Alem de locais de acontecimentos."}])

                        print(f"Resposta do GPT-4: {resposta}")

                        df_termos_busca.at[index, new_col_name] = resposta

            # ------------- Fim Parte 05 ----------------------------------------------------------------------------------------------------

            # ------------- Parte 06 --------------------------------------------------------------------------------------------------------

            # Inicialize uma nova coluna para armazenar os fatos relevantes consolidados
            df_termos_busca['Fatos Relevantes Consolidados'] = ''

            # Lista das colunas que você quer consolidar (atualizada com base nas suas colunas existentes)
            colunas_para_consolidar = [
                "Factos Relevantes Termo 1 1",
                "Factos Relevantes Termo 1 2",
                "Factos Relevantes Termo 1 3",
                "Factos Relevantes Termo 2 1",
                "Factos Relevantes Termo 2 3",
                "Factos Relevantes Termo 3 1",
                "Factos Relevantes Termo 3 2",
                "Factos Relevantes Termo 3 3"
            ]

            # Para cada linha no DataFrame
            for index, row in df_termos_busca.iterrows():
                fatos_relevantes = []

                for col in colunas_para_consolidar:
                    # Verifique se a coluna existe no DataFrame
                    if col in df_termos_busca.columns:
                        factos_relevantes_termo = str(row[col])

                        if factos_relevantes_termo and factos_relevantes_termo.lower() != 'nan':
                            fatos_relevantes.append(factos_relevantes_termo)
                    else:
                        print(f"Aviso: A coluna '{col}' não foi encontrada no DataFrame.")

                # Concatene os fatos relevantes em uma única string e adicione à nova coluna
                df_termos_busca.at[index, 'Fatos Relevantes Consolidados'] = '---'.join(fatos_relevantes)

            # ------------- Fim Parte 06 ----------------------------------------------------------------------------------------------------
            api_key_google = os.getenv('API_KEY_GOOGLE')
            if not api_key_google:
                raise ValueError("A chave API do Google não foi configurada corretamente.")

            # ------------- Parte 07 --------------------------------------------------------------------------------------------------------
            def perguntar_gpt(pergunta, messages):
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + os.getenv('OPENAI_API_KEY')
                }

                # Adiciona a pergunta atual
                messages.append({"role": "user", "content": pergunta})

                # Os dados agora precisam incluir o modelo 'gpt-4-1106-preview'
                data = {
                    "model": "gpt-4-1106-preview",
                    "messages": messages,
                }

                backoff_time = 1  # Começamos com um tempo de espera de 1 segundo
                while True:
                    try:
                        response = requests.post(url, headers=headers,
                                                 json=data)  # Note que aqui usamos 'json=data' em vez de 'data=json.dumps(data)'
                        response.raise_for_status()

                        # Adiciona a resposta do modelo à lista de mensagens
                        messages.append({"role": "assistant", "content": response.json()['choices'][0]['message']['content']})

                        return response.json()['choices'][0]['message']['content'], messages
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code in (429, 520, 502, 503):  # Limite de requisições atingido ou erro de servidor
                            print(f"Erro {e.response.status_code} atingido. Aguardando antes de tentar novamente...")
                            time.sleep(backoff_time)  # Aguarda antes de tentar novamente
                            backoff_time *= 2  # Aumenta o tempo de espera
                        else:
                            raise

            # Carregue o arquivo de estilo de escrita
            # with open("../../testinho2/projeto_gorwth/estilo_escrita.txt", "r", encoding='utf-8') as file:
            # estilo_escrita = file.read()

            articles = []

            # Para cada tendência e fato importante no DataFrame
            for index, row in df_termos_busca.iterrows():
                trend = row['Tema']
                fact = row['Fatos Relevantes Consolidados']

                # Construa uma prompt com a tendência e os fatos importantes
                prompt = f"Estilo de Escrita:\n{estilo_de_escrita}\n\nTendência: {trend}\nFatos importantes: {fact}\n\nCom base nas informações acima e no estilo de escrita fornecido, crie 1 artigos completos que estejam alinhados com as tendências atuais, o estilo de escrita e os fatos importantes. User apenas as referencias listadas. Não user informações fora desse contexto. Cada artigo deve ser um texto completo e detalhado, desenvolvido a partir do título e dos fatos gerados, e deve abordar o tópico de maneira aprofundada e informativa, usando apenas as referências, datas e eventos presentes nos fatos fornecidos. Além disso, cada artigo deve incluir pelo menos uma citação de uma autoridade, especialista ou organização."

                print(f"Enviando a seguinte pergunta para o GPT-4: {prompt}")

                # Faça uma solicitação para a API GPT-4 para expandir a prompt em uma matéria
                response, messages = perguntar_gpt(prompt, [{"role": "system",
                                                             "content": "Você é um assistente de escrita e precisa escrever uma matéria completa baseada nas informações fornecidas."}])

                print(f"Resposta do GPT-4: {response}")

                # Adicione o texto gerado à lista de artigos
                articles.append([trend, response])

            # Converta a lista de artigos em um DataFrame
            articles_df = pd.DataFrame(articles, columns=['Tendência', 'Matéria Gerada'])

            for index, row in articles_df.iterrows():
                artigo = row['Matéria Gerada']

                # Crie um prompt para o GPT-4 gerar ideias de imagem baseadas no artigo
                prompt_imagem = f"Por favor, crie 3 prompts de imagem criativos que se relacionem com o seguinte artigo: {artigo}"
                print(prompt_imagem)
                # Envie o prompt para o GPT-4 e receba as ideias de imagem
                resposta_imagem, _ = perguntar_gpt(prompt_imagem, [
                    {"role": "system", "content": "Você é um assistente criativo e precisa sugerir ideias de imagem."}])

                # Adicione as ideias de imagem ao DataFrame
                articles_df.at[index, 'Prompts de Imagem'] = resposta_imagem
                print(articles_df)
                print(f"Prompts de imagem para o artigo {index}: {resposta_imagem}")
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                raise ValueError("A chave API do OpenAI não foi configurada corretamente no .env.")

            client = OpenAI(api_key=openai_api_key)

            def gerar_e_salvar_imagem(client, prompt):
                print(f"Gerando imagem para o prompt: {prompt}")
                # Gere a imagem usando o DALL-E 3
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                image_url = response.data[0].url

                # Baixe a imagem
                r = requests.get(image_url)
                if r.status_code == 200:
                    print("Imagem obtida com sucesso.")
                    # Retorna o conteúdo binário da imagem
                    return r.content
                else:
                    print(f"Falha ao baixar a imagem do URL: {image_url}")
                    return None

            for index, row in articles_df.iterrows():
                print(f"Processando imagens para o artigo {index}")
                prompts_imagem = row['Prompts de Imagem'].split(
                    '\n')  # Supondo que cada prompt esteja separado por uma nova linha

                imagens_binarias = []
                for i, prompt in enumerate(prompts_imagem):
                    if len(prompt) > 0:
                        dados_imagem = gerar_e_salvar_imagem(client, prompt)
                        if dados_imagem:
                            imagens_binarias.append(dados_imagem)
                            print(f"Imagem {i} gerada para o artigo {index}")

                # Armazenar os dados binários das imagens no DataFrame
                if len(imagens_binarias) > 0:
                    articles_df.at[index, 'Imagens Geradas0'] = imagens_binarias[0] if len(
                        imagens_binarias) > 0 else None
                    articles_df.at[index, 'Imagens Geradas1'] = imagens_binarias[1] if len(
                        imagens_binarias) > 1 else None
                    articles_df.at[index, 'Imagens Geradas2'] = imagens_binarias[2] if len(
                        imagens_binarias) > 2 else None

            # Cria uma instância de TextosUsuarios
            for index, row in articles_df.iterrows():
                novo_texto_usuario = TextosUsuarios(
                    id_usuario=id,
                    texto=row['Matéria Gerada'],
                    imagens0=row['Imagens Geradas0'],
                    imagens1=row['Imagens Geradas1'],
                    imagens2=row['Imagens Geradas2']
                )
                db.session.add(novo_texto_usuario)
                print(f"Artigo {index} adicionado à sessão do banco de dados.")

            db.session.commit()
            print("Commit realizado no banco de dados.")

            # ------------- Fim Parte 07 ----------------------------------------------------------------------------------------------------

            print(
                "Todas as matérias geradas foram salvas com sucesso no arquivo 'noticias_termos_buscas_links_textos_fatos_relevante_consolidadora_artigos.xlsx'.")

            print(
                "As informações importantes foram consolidadas e salvas com sucesso no arquivo 'noticias_termos_buscas_links_textos_fatos_relevante_consolidadora.xlsx'.")

            print(
                "Todas as informações importantes foram salvas com sucesso no arquivo 'noticias_termos_buscas_links_textos_fatos_relevante.xlsx'.")

            # Depois que as notícias forem geradas e salvas no banco de dados
            flash('Notícias prontas!', 'success')

            # Redireciona para a página inicial ou de status após iniciar o processo
            return redirect(url_for('home'))

        else:
            print("DataFrame (Df) esta vazio.")

        # --------------------- Fim parte 01 --------------------------------------------------------------------------

    else:
        print("Tema ou estilo de escrita nao definidos.")

    return redirect(url_for('home'))
###############################################################################################


# Função para codificar em base64
def b64encode_filter(data):
    if isinstance(data, bytes):
        return base64.b64encode(data).decode()  # Decodifica para string após a codificação
    # Se 'data' não for do tipo 'bytes', você pode lidar de outra maneira ou levantar um erro.
    raise TypeError("O dado fornecido não é do tipo 'bytes'")


# Registrar o filtro com Jinja2
app.jinja_env.filters['b64encode'] = b64encode_filter



@app.route('/materias')
@login_required
def materias():
    textos = TextosUsuarios.query.filter_by(id_usuario=current_user.id).all()
    return render_template('materias.html', textos=textos)

@app.route('/delete_texto/<int:texto_id>', methods=['POST'])
@login_required
def delete_texto(texto_id):
    texto = TextosUsuarios.query.get_or_404(texto_id)
    if texto.usuario != current_user:
        flash('Você não tem permissão para excluir este texto.', 'danger')
        return redirect(url_for('materias'))
    db.session.delete(texto)
    db.session.commit()
    flash('O texto foi excluído com sucesso.', 'success')
    return redirect(url_for('materias'))


@app.route('/texto_completo/<int:texto_id>')
@login_required
def texto_completo(texto_id):
    texto = TextosUsuarios.query.get_or_404(texto_id)
    if texto.id_usuario != current_user.id:
        flash('Você não tem permissão para visualizar este texto.', 'warning')
        return redirect(url_for('materias'))
    return render_template('texto_completo.html', texto=texto)

@app.route('/documentacao')
def documentacao():
    return render_template('documentacao.html')

@app.route('/')
def index():
    # Supondo que você tenha uma forma de verificar se o usuário é admin
    # Isso pode ser parte do objeto 'user' se estiver usando algo como Flask-Login
    is_admin = session.get('is_admin', False)
    return render_template('base.html', is_admin=is_admin)

@app.route('/analise_posts', methods=['GET', 'POST'])
def analise_posts():
    try:
        if request.method == 'POST':
            posts = PostsInstagram(
                id=request.form.get('id'),
                id_empresa=request.form.get('id_empresa'),
                timestamp=request.form.get('timestamp'),
                caption=request.form.get('caption'),
                like_count=request.form.get('like_count'),
                comments_count=request.form.get('comments_count'),
                reach=request.form.get('reach'),
                percentage=request.form.get('percentage'),
                media_product_type=request.form.get('media_product_type'),
                plays=request.form.get('plays'),
                saved=request.form.get('saved'),
                nome_empresa=request.form.get('nome_empresa')
            )
            db.session.add(posts)
            db.session.commit()
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 201
        

    empresas = Empresa.query.filter(
            (Empresa.vincular_instagram.isnot(None) & (Empresa.vincular_instagram != ''))
        ).all()
    return render_template('analise_posts.html', empresas=empresas)

@app.route('/deletar_anuncios', methods=['DELETE'])
def deletar_anuncios():
    try:
        Ads.query.delete()  # Substitua Ads pelo nome do seu modelo de anúncios
        db.session.commit()
        return jsonify({'message': 'Todos os anúncios foram deletados com sucesso'}), 200
    except Exception as e:
        print("Erro ao deletar anúncios: ", e)
        return jsonify({'error': 'Erro ao deletar anúncios'}), 500


@app.route('/salvar_anuncios', methods=['GET', 'POST'])
def salvar_anuncios():
    try:
        if request.method == 'POST':
            anuncios = Ads(
                id=request.form.get('id'),
                id_empresa=request.form.get('id_empresa'),
                timestamp=request.form.get('timestamp'),
                nome_grupo=request.form.get('nome_grupo'),
                nome_campanha=request.form.get('nome_campanha'),
                nome_anuncio=request.form.get('nome_anuncio'),
                valor=request.form.get('valor'),
                impressoes=request.form.get('impressoes'),
                landing=request.form.get('landing'),
                cpm=request.form.get('cpm'),
                ctr=request.form.get('ctr'),
                cpc=request.form.get('cpc'),
                nome_empresa=request.form.get('nome_empresa'),
            )
            db.session.add(anuncios)
            db.session.commit()
            return jsonify({'message': 'Anúncio inserido com sucesso'}), 200  # Altere para retornar uma resposta JSON
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 500

@app.route('/listar_anuncios', methods=['GET', 'POST'])
def listar_anuncios():
    try:
        if request.method == 'POST':
            anuncios = Ads(
                id_empresa=request.form.get('id_empresa'),
                timestamp=request.form.get('timestamp'),
                nome_grupo=request.form.get('nome_grupo'),
                nome_campanha=request.form.get('nome_campanha'),
                nome_anuncio=request.form.get('nome_anuncio'),
                valor=request.form.get('valor'),
                impressoes=request.form.get('impressoes'),
                landing=request.form.get('landing'),
                cpm=request.form.get('cpm'),
                ctr=request.form.get('ctr'),
                cpc=request.form.get('cpc'),
                nome_empresa=request.form.get('nome_empresa'),
            )
            db.session.add(anuncios)
            db.session.commit()
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 500

    # Consulta todas as empresas, mas processa para remover duplicatas posteriormente
    empresaNomes = Empresa.query.filter(
        Empresa.vincular_anuncio.isnot(None) & (Empresa.vincular_anuncio != '')
    ).all()
    
    ads = Ads.query.filter(Ads.timestamp.isnot(None)).all()


    # Utiliza um conjunto para garantir a unicidade dos nomes
    empresas_unicas = {empresa.vincular_anuncio for empresa in empresaNomes}

    return render_template('listar_anuncios.html', ads = ads)

@app.route('/relatorio')
def relatorio():
    empresa_selecionada = request.args.get('empresa')
    if empresa_selecionada:
        anuncios = Ads.query.join(Empresa).filter(Empresa.vincular_anuncio == empresa_selecionada).all()
        anuncios_dict = [anuncio.to_dict() for anuncio in anuncios]
    else:
        anuncios_dict = []
    
    empresaNomes = Empresa.query.filter(
            (Empresa.vincular_anuncio.isnot(None) & (Empresa.vincular_anuncio != ''))
        ).all()

    return render_template('relatorio.html', anuncios=anuncios_dict, empresas=empresaNomes)


@app.route('/relatorio_posts')
def relatorio_posts():
    empresa_selecionada = request.args.get('empresa')
    if empresa_selecionada:
        anuncios = PostsInstagram.query.join(Empresa).filter(Empresa.vincular_instagram == empresa_selecionada).all()
        anuncios_dict = [anuncio.to_dict() for anuncio in anuncios]
    else:
        anuncios_dict = []
    
    empresaNomes = Empresa.query.filter(
            (Empresa.vincular_instagram.isnot(None) & (Empresa.vincular_instagram != ''))
        ).all()

    return render_template('relatorio_posts.html', anuncios=anuncios_dict, empresas=empresaNomes)

@app.route('/api/anuncios')
def api_anuncios():
    empresa_selecionada = request.args.get('empresa')
    if empresa_selecionada:
        # Filtra os anúncios pela empresa usando o campo vincular_anuncio
        anuncios = Ads.query.join(Empresa).filter(Empresa.vincular_anuncio == empresa_selecionada).all()
    else:
        anuncios = Ads.query.all()

    anuncios_data = [anuncio.to_dict() for anuncio in anuncios]
    return jsonify(anuncios_data)

@app.route('/anuncios', methods=['GET', 'POST'])
def analise_anuncios():
    try:
        if request.method == 'POST':
            anuncios = analise_anuncios(
                id=request.form.get('id'),
                id_empresa=request.form.get('id_empresa'),
                valor=request.form.get('valor'),
                impressoes=request.form.get('impressoes'),
                landing=request.form.get('landing'),
                cpm=request.form.get('cpm'),
                ctr=request.form.get('ctr'),
                cpc=request.form.get('cpc')
            )
            db.session.add(anuncios)
            db.session.commit()
    except Exception as e:
        print("Exceção ocorreu: ", e)
        traceback.print_exc()
        return jsonify({'message': 'Dados inseridos com falha!'}), 201
        

    empresaNomes = Empresa.query.filter(
            (Empresa.vincular_anuncio.isnot(None) & (Empresa.vincular_anuncio != ''))
        ).all()
        
    return render_template('anuncios.html', empresas=empresaNomes)


@app.route('/atualizar-meta-ads')
def atualizar_meta_ads():
    try:
        atualizar_dados_meta_ads()  # Chama a função de scraping e atualização do banco
        flash('Dados de Meta Ads atualizados com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar dados: {e}', 'danger')

    return redirect(url_for('home'))  # Substitua 'home' pelo nome da rota desejada


@app.route('/meta-ads-campanhas')
@login_required  # Adicione isso se você quiser que apenas usuários logados possam acessar esta página
def meta_ads_campanhas():
    # Busca todos os registros de MetaAds
    todos_meta_ads = MetaAds.query.all()
    return render_template('meta_ads_campanhas.html', todos_meta_ads=todos_meta_ads)


@app.route('/atualizar_instagram_social')
def atualizar_instagram_social():
    try:
        consulta_api_e_salva_db()
        flash('Dados do Instagram atualizados com sucesso!', 'success')
    except Exception as e:
        # Em caso de erro, envie uma mensagem para a interface do usuário
        flash(f'Erro ao atualizar os dados do Instagram: {e}', 'danger')

    # Redireciona para a página principal ou alguma página de confirmação
    return redirect(url_for('home'))  # Substitua 'index' pelo endpoint da página para a qual deseja redirecionar


@app.route('/instagram_social')
def instagram_social():
    # Buscar todos os dados do Instagram no banco de dados
    dados_instagram = InstagramData.query.all()

    # Renderizar um template HTML passando os dados do Instagram
    return render_template('instagram_social.html', dados=dados_instagram)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)