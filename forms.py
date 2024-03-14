from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, SelectField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional
from models import Empresa  # Certifique-se de que esta importação está correta de acordo com a estrutura do seu projeto
from werkzeug.security import check_password_hash


csrf = CSRFProtect()

class EmpresaForm(FlaskForm):
    empresa_id = HiddenField('ID da Empresa')  # Adicionado para edição
    nome = StringField('Nome', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Salvar Empresa')

    # Esta função inicializa o campo empresa_id para edição
    def __init__(self, *args, **kwargs):
        super(EmpresaForm, self).__init__(*args, **kwargs)
        if 'obj' in kwargs:
            self.empresa_id.data = kwargs['obj'].id

class UsuarioForm(FlaskForm):
    user_id = HiddenField('ID do Usuário')  # Campo oculto para o ID do usuário
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=2, max=20)])
    # Para a criação de um novo usuário, utilizaremos os campos 'password' e 'confirm_password'.
    password = PasswordField('Senha', validators=[Optional(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirme a Senha', validators=[EqualTo('password', message='As senhas não correspondem.'), Optional()])
    # Campo para a atualização da senha, sem necessidade da senha atual.
    new_password = PasswordField('Nova Senha', validators=[Optional(), Length(min=6, max=20)])
    confirm_new_password = PasswordField('Confirme a Nova Senha', validators=[EqualTo('new_password', message='As senhas não correspondem.'), Optional()])
    empresa_id = SelectField('Empresa', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Cadastrar/Atualizar Usuário')

    def __init__(self, *args, **kwargs):
        super(UsuarioForm, self).__init__(*args, **kwargs)
        # Inicializa as escolhas de empresa_id a partir do banco de dados.
        self.empresa_id.choices = [(empresa.id, empresa.nome_contato) for empresa in Empresa.query.all()]


class TemaForm(FlaskForm):
    tema_id = HiddenField('ID')
    nome = StringField('Nome do Tema', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class EstiloDeEscritaForm(FlaskForm):
    estilo_id = HiddenField('ID do Estilo de Escrita')
    estilo = TextAreaField('Estilo de Escrita', validators=[DataRequired()])
    submit = SubmitField('Salvar Estilo de Escrita')
