from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import BIGINT
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from base64 import b64decode
from base64 import b64decode, b64encode


db = SQLAlchemy()




class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_contato = db.Column(db.String(80))
    email_contato = db.Column(db.String(120))
    telefone_contato = db.Column(db.String(20))
    endereco_empresa = db.Column(db.String(200))
    setor_atuacao = db.Column(db.String(200))
    tamanho_empresa = db.Column(db.String(200))
    descricao_empresa = db.Column(db.Text)
    objetivos_principais = db.Column(db.Text)
    historico_interacoes = db.Column(db.Text)
    vincular_instagram = db.Column(db.String(200))
    vincular_anuncio = db.Column(db.String(200))

    def __repr__(self):
        return f'<Empresa {self.nome_contato}>'

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    sobrenome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    celular = db.Column(db.String(20), nullable=False)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='usuarios')
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    cargo = db.Column(db.String(80))
    status = db.Column(db.String(20))
    sprint = db.Column(db.String(200))  # Novo campo
    dayling_1 = db.Column(db.String(200))  # Novo campo
    dayling_2 = db.Column(db.String(200))  # Novo campo
    dayling_3 = db.Column(db.String(200))  # Novo campo
    dayling_4 = db.Column(db.String(200))  # Novo campo
    dayling_5 = db.Column(db.String(200))  # Novo campo
    sprint = db.Column(db.String(200))
    dayling_1 = db.Column(db.String(200))
    dayling_2 = db.Column(db.String(200))
    dayling_3 = db.Column(db.String(200))
    dayling_4 = db.Column(db.String(200))
    dayling_5 = db.Column(db.String(200))
    password_hash = db.Column(db.String(300))
    is_admin = db.Column(db.Boolean, default=False)
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'sobrenome': self.sobrenome,
            'email': self.email,
        }
    @property
    def password(self):
        raise AttributeError('password: campo de leitura apenas')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)






class Tema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)

    usuario = db.relationship('Usuario', back_populates='temas')
    empresa = db.relationship('Empresa', back_populates='temas')

    def __repr__(self):
        return f'<Tema {self.nome}>'

# Adicione a nova relação em Usuario e Empresa
Usuario.temas = db.relationship('Tema', back_populates='usuario')
Empresa.temas = db.relationship('Tema', back_populates='empresa')


class EstiloDeEscrita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estilo = db.Column(db.Text, nullable=False)  # Campo de texto ilimitado para o estilo de escrita
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False, unique=True)

    usuario = db.relationship('Usuario', backref='estilo_de_escrita')
    empresa = db.relationship('Empresa', backref='estilo_de_escrita', uselist=False)

    def __repr__(self):
        return f'<EstiloDeEscrita {self.estilo[:30]}>...'  # Exibe os primeiros 30 caracteres do estilo


class TextosUsuarios(db.Model):
    __tablename__ = 'textos_usuarios'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    ##imagens0 = db.Column(db.Text, nullable=False)
    ##imagens1 = db.Column(db.Text, nullable=False)
    ##imagens2 = db.Column(db.Text, nullable=False)
    imagens0 = db.Column(db.LargeBinary, nullable=True)  # Alterado de db.Text para db.LargeBinary
    imagens1 = db.Column(db.LargeBinary, nullable=True)  # Alterado de db.Text para db.LargeBinary
    imagens2 = db.Column(db.LargeBinary, nullable=True)  # Alterado de db.Text para db.LargeBinary
    usuario = db.relationship('Usuario', backref='textos_usuarios')


    def __repr__(self):
        return f'<TextosUsuarios {self.texto[:50]}>...'  # Exibe os primeiros 50 caracteres do texto



class MetaAds(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)  # Data da informação
    adcampaign_name = db.Column(db.String(100), nullable=False)  # Nome da campanha
    adset_name = db.Column(db.String(100), nullable=False)  # Nome do conjunto de anúncios
    ad_name = db.Column(db.String(100), nullable=False)  # Nome do anúncio
    profile = db.Column(db.String(100), nullable=False)  # Perfil
    reach = db.Column(db.Integer, nullable=False)  # Alcance
    frequency = db.Column(db.Float, nullable=False)  # Frequência
    impressions = db.Column(db.Integer, nullable=False)  # Impressões
    cost = db.Column(db.Float, nullable=False)  # Custo
    cpm = db.Column(db.Float, nullable=False)  # CPM
    action_link_click = db.Column(db.Integer, nullable=False)  # Cliques no link
    clicks = db.Column(db.Integer, nullable=False)  # Cliques
    ctr = db.Column(db.Float, nullable=False)  # CTR
    cplc = db.Column(db.Float, nullable=False)  # CPLC
    cpc = db.Column(db.Float, nullable=False)  # CPC
    action_subscribe = db.Column(db.Integer, nullable=False)  # Ações de inscrição

    def __repr__(self):
        return f'<MetaAds {self.adcampaign_name}>'




class InstagramData(db.Model):
    __tablename__ = 'instagram_data'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(BIGINT, nullable=False)
    data_source = db.Column(db.String(120))
    instagram_id = db.Column(db.String(120), unique=True, nullable=False)
    media_caption = db.Column(db.Text)
    media_id = db.Column(db.String(120), unique=True, nullable=False)
    media_permalink = db.Column(db.String(255))
    media_shortcode = db.Column(db.String(120))
    video_thumbnail_url = db.Column(db.String(255))
    media_type = db.Column(db.String(50))
    media_url = db.Column(db.String(255))
    name = db.Column(db.String(120))
    media_created = db.Column(db.DateTime)
    today = db.Column(db.Date)
    username = db.Column(db.String(120))
    website = db.Column(db.String(255))
    carousel_album_engagement = db.Column(db.Integer)
    carousel_album_impressions = db.Column(db.Integer)
    carousel_album_reach = db.Column(db.Integer)
    carousel_album_saved = db.Column(db.Integer)
    comments_count = db.Column(db.Integer)
    engagement = db.Column(db.Integer)
    media_impressions = db.Column(db.Integer)
    like_count = db.Column(db.Integer)
    media_reach = db.Column(db.Integer)
    unique_saves = db.Column(db.Integer)
    story_exits = db.Column(db.Integer)
    story_impressions = db.Column(db.Integer)
    story_reach = db.Column(db.Integer)
    story_replies = db.Column(db.Integer)
    taps_back = db.Column(db.Integer)
    taps_forward = db.Column(db.Integer)
    video_views = db.Column(db.Integer)

    def __repr__(self):
        return f'<InstagramData {self.media_id}>'

class PostsInstagram(db.Model):
    id = db.Column(db.String, primary_key=True)
    id_empresa = db.Column(db.String(64), index=True)
    timestamp = db.Column(db.String(64))
    caption = db.Column(db.String(64))
    like_count = db.Column(db.Integer)
    comments_count = db.Column(db.Integer)  
    reach = db.Column(db.Integer)
    percentage = db.Column(db.Float)
    media_product_type = db.Column(db.String(64))
    plays = db.Column(db.Integer)
    saved = db.Column(db.Integer)
    nome_empresa = db.Column(db.String(64))

    def to_dict(self):
        return {
            'id': self.id,  # incluir o id no dicionário
            'id_empresa': self.id_empresa,
            'timestamp': self.timestamp,
            'caption': self.caption,
            'like_count': self.like_count,
            'comments_count': self.comments_count,
            'reach': self.reach,
            'percentage': self.percentage,
            'media_product_type': self.media_product_type,
            'plays': self.plays,
            'saved': self.saved,
            'nome_empresa': self.nome_empresa,
        }

class analise_anuncios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='respostas')
    valor = db.Column(db.Float)
    impressoes = db.Column(db.Integer)
    landing = db.Column(db.Integer)
    cpm = db.Column(db.Float)
    ctr = db.Column(db.Float)
    cpc = db.Column(db.Float)   

class Ads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    timestamp = db.Column(db.String(64))
    nome_grupo = db.Column(db.String(200))
    nome_campanha = db.Column(db.String(200))
    nome_anuncio = db.Column(db.String(200))
    empresa = db.relationship('Empresa', backref='ads')
    valor = db.Column(db.Float)
    impressoes = db.Column(db.Integer)
    landing = db.Column(db.Integer)
    cpm = db.Column(db.Float)
    ctr = db.Column(db.Float)
    cpc = db.Column(db.Float)
    nome_empresa = db.Column(db.String(64))

    def to_dict(self):  
        return {
            'id': self.id,
            'id_empresa': self.id_empresa,
            'timestamp': self.timestamp,
            'nome_grupo': self.nome_grupo,
            'nome_campanha': self.nome_campanha,
            'nome_anuncio': self.nome_anuncio,
            'empresa': self.empresa.id if self.empresa else None,  # Aqui está a mudança
            'valor': self.valor,
            'impressoes': self.impressoes,
            'landing': self.landing,
            'cpm': self.cpm,
            'ctr': self.ctr,
            'cpc': self.cpc,
            'nome_empresa': self.nome_empresa,
        }