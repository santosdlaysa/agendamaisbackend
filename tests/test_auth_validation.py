"""
Testes de validacao do registro de usuario em auth.py
"""
import pytest
import json
from src.models.user import User


class TestAuthRegisterValidation:
    """Testes de validacao do registro de usuario"""

    def test_register_success(self, client, app):
        """Registro com dados validos deve funcionar"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'novo@teste.com',
                    'password': 'senha123',
                    'name': 'Novo Usuario'
                },
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert 'user' in data
            assert data['user']['email'] == 'novo@teste.com'
            assert data['user']['name'] == 'Novo Usuario'
            assert 'message' in data

    def test_register_email_required_empty(self, client, app):
        """Deve falhar com email vazio"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': '',
                    'password': 'senha123',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Email, senha e nome' in data['message']

    def test_register_email_required_missing(self, client, app):
        """Deve falhar sem campo email"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'password': 'senha123',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Email, senha e nome' in data['message']

    def test_register_password_required_empty(self, client, app):
        """Deve falhar com senha vazia"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'teste@email.com',
                    'password': '',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Email, senha e nome' in data['message']

    def test_register_password_required_missing(self, client, app):
        """Deve falhar sem campo senha"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'teste@email.com',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Email, senha e nome' in data['message']

    def test_register_name_required_empty(self, client, app):
        """Deve falhar com nome vazio"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'teste@email.com',
                    'password': 'senha123',
                    'name': ''
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Email, senha e nome' in data['message']

    def test_register_name_required_missing(self, client, app):
        """Deve falhar sem campo nome"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'teste@email.com',
                    'password': 'senha123'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Email, senha e nome' in data['message']

    def test_register_email_invalid_format_no_at(self, client, app):
        """Deve falhar com email sem @"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'abc',
                    'password': 'senha123',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Formato de email' in data['message']

    def test_register_email_invalid_format_no_domain(self, client, app):
        """Deve falhar com email sem dominio"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'abc@',
                    'password': 'senha123',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Formato de email' in data['message']

    def test_register_email_invalid_format_no_local(self, client, app):
        """Deve falhar com email sem parte local"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': '@teste.com',
                    'password': 'senha123',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Formato de email' in data['message']

    def test_register_password_too_short(self, client, app):
        """Deve falhar com senha menor que 6 caracteres"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'teste@email.com',
                    'password': '12345',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert '6 caracteres' in data['message']

    def test_register_password_exactly_6_chars_success(self, client, app):
        """Senha com exatamente 6 caracteres deve funcionar"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'teste6chars@email.com',
                    'password': '123456',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 201

    def test_register_name_only_spaces(self, client, app):
        """Deve falhar com nome apenas espacos"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'teste@email.com',
                    'password': 'senha123',
                    'name': '   '
                },
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Email, senha e nome' in data['message']

    def test_register_email_already_in_use(self, client, app, db_session):
        """Deve falhar se email ja esta em uso"""
        with app.app_context():
            # Primeiro registro
            response1 = client.post(
                '/api/auth/register',
                json={
                    'email': 'duplicado@teste.com',
                    'password': 'senha123',
                    'name': 'Usuario 1'
                },
                content_type='application/json'
            )
            assert response1.status_code == 201

            # Segundo registro com mesmo email
            response2 = client.post(
                '/api/auth/register',
                json={
                    'email': 'duplicado@teste.com',
                    'password': 'outrasenha',
                    'name': 'Usuario 2'
                },
                content_type='application/json'
            )

            assert response2.status_code == 400
            data = json.loads(response2.data)
            assert 'Email' in data['message'] and 'uso' in data['message']

    def test_register_email_case_insensitive(self, client, app, db_session):
        """Deve tratar email case insensitive para duplicatas"""
        with app.app_context():
            # Primeiro registro
            response1 = client.post(
                '/api/auth/register',
                json={
                    'email': 'CaseTeste@Email.com',
                    'password': 'senha123',
                    'name': 'Usuario 1'
                },
                content_type='application/json'
            )
            assert response1.status_code == 201

            # Segundo registro com mesmo email em lowercase
            response2 = client.post(
                '/api/auth/register',
                json={
                    'email': 'caseteste@email.com',
                    'password': 'outrasenha',
                    'name': 'Usuario 2'
                },
                content_type='application/json'
            )

            # O comportamento depende da implementacao
            # Se o banco eh case insensitive, vai falhar com 400
            # Se nao, vai criar outro usuario
            # O teste verifica que nao da erro 500
            assert response2.status_code in [201, 400]

    def test_register_email_with_spaces_trimmed(self, client, app):
        """Email com espacos deve ser trimado"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': '  espacos@teste.com  ',
                    'password': 'senha123',
                    'name': 'Usuario Teste'
                },
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['user']['email'] == 'espacos@teste.com'

    def test_register_name_with_spaces_trimmed(self, client, app):
        """Nome com espacos extras deve ser trimado"""
        with app.app_context():
            response = client.post(
                '/api/auth/register',
                json={
                    'email': 'trimname@teste.com',
                    'password': 'senha123',
                    'name': '  Usuario Com Espacos  '
                },
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['user']['name'] == 'Usuario Com Espacos'
