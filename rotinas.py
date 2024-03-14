from app import app
from models import db, Usuario, Empresa
from werkzeug.security import generate_password_hash

with app.app_context():
    # Drop all existing tables
    db.drop_all()
    db.create_all()

    db.create_all()

    if not Empresa.query.first():
        nova_empresa = Empresa(nome_contato='Empresa Exemplo')
        db.session.add(nova_empresa)
        db.session.commit()

    if not Usuario.query.filter_by(username='admin').first():
        empresa = Empresa.query.first()
        admin = Usuario(
            nome='Admin',
            sobrenome='User',
            email='admin@example.com',
            celular='99999999',
            cargo='Administrador',
            status='Ativo',
            username='admin',
            password='Omega801',
            id_empresa=empresa.id,
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()