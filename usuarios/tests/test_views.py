from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Usuario

User = get_user_model()


class BaseTestCase(APITestCase):
    """
    Classe base com criação de usuários e método auxiliar de autenticação
    usada por todos os testes.
    """

    def setUp(self):
        self.client = APIClient()

        # Cria um usuário com tipo 'paciente'
        self.usuario_paciente = Usuario.objects.create_user(
            email='paciente@teste.com',
            password='senha123456',
            telefone='+244900000001',
            is_paciente=True
        )

        # Cria um usuário com tipo 'moderador'
        self.usuario_moderador = Usuario.objects.create_user(
            email='moderador@teste.com',
            password='senha123456',
            telefone='+244900000002',
            is_moderador=True
        )

        # Cria um usuário com tipo 'admin'
        self.usuario_admin = Usuario.objects.create_user(
            email='admin@teste.com',
            password='senha123456',
            telefone='+244900000003',
            is_admin=True,
            is_staff=True
        )

    def autenticar_como(self, usuario):
        """
        Gera um token de acesso JWT para o usuário fornecido
        e adiciona ao cabeçalho Authorization para autenticação nas requisições.
        """
        refresh = RefreshToken.for_user(usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')


class LoginViewTestCase(BaseTestCase):
    """
    Testes para login de usuários
    """

    def test_login_sucesso(self):
        # Testa login com credenciais corretas
        url = reverse('usuarios:login')
        data = {
            'email': 'paciente@teste.com',
            'password': 'senha123456'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_falha(self):
        # Testa login com senha incorreta
        url = reverse('usuarios:login')
        data = {
            'email': 'paciente@teste.com',
            'password': 'senha_errada'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PerfilUsuarioViewTestCase(BaseTestCase):
    """
    Testes para visualização e atualização do perfil do usuário autenticado
    """

    def test_visualizar_perfil(self):
        self.autenticar_como(self.usuario_paciente)
        url = reverse('usuarios:perfil_usuario')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.usuario_paciente.email)

    def test_atualizar_perfil(self):
        self.autenticar_como(self.usuario_paciente)
        url = reverse('usuarios:perfil_usuario')
        data = {
            'telefone': '+2459000001'
        }

        response = self.client.put(url, data, format='json')

        # 👇 Debug: imprime o erro real do serializer
        print("Erros da resposta:", response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['telefone'], '+2459000001')


class GerenciarUsuariosViewTestCase(BaseTestCase):
    """
    Testes para o endpoint de listagem de usuários por administradores
    """

    def test_listar_usuarios_admin(self):
        self.autenticar_como(self.usuario_admin)
        url = reverse('usuarios:gerenciar_usuarios')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_acesso_negado_para_nao_admin(self):
        self.autenticar_como(self.usuario_paciente)
        url = reverse('usuarios:gerenciar_usuarios')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
