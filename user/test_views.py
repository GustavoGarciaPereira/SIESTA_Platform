"""
Testes para as views do aplicativo user.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from .models import UserProfile


class UserViewsTests(TestCase):
    """Testes para as views do aplicativo user."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_home_view(self):
        """Testa a view da página inicial."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_home_view_unauthenticated(self):
        """Testa a página inicial para usuários não autenticados."""
        self.client.logout()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_about_view(self):
        """Testa a view da página sobre."""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')
        # Verifica se o contexto contém team_members
        self.assertIn('team_members', response.context)

    def test_contact_view(self):
        """Testa a view da página de contato."""
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact.html')

    def test_contact_submit_view_post(self):
        """Testa o envio do formulário de contato."""
        response = self.client.post(reverse('contact_submit'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Test message content'
        })

        # Deve redirecionar de volta para a página de contato
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contact'))

        # Verifica se a mensagem de sucesso foi adicionada
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any('sucesso' in str(message) for message in messages_list))

    def test_contact_submit_view_get(self):
        """Testa acesso GET ao endpoint de envio de contato."""
        response = self.client.get(reverse('contact_submit'))

        # Deve redirecionar com mensagem de erro
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contact'))

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any('inválido' in str(message).lower() for message in messages_list))

    def test_signup_view_get(self):
        """Testa acesso GET à página de cadastro."""
        self.client.logout()  # Usuário não deve estar logado para cadastro
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/signup.html')
        self.assertContains(response, 'form')

    def test_signup_view_post_valid(self):
        """Testa cadastro com dados válidos."""
        self.client.logout()
        initial_user_count = User.objects.count()

        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })

        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

        # Deve ter criado um novo usuário
        self.assertEqual(User.objects.count(), initial_user_count + 1)

        # Verifica se o usuário foi criado
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.email, 'newuser@example.com')

    def test_signup_view_post_invalid(self):
        """Testa cadastro com dados inválidos."""
        self.client.logout()
        initial_user_count = User.objects.count()

        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'invalid-email',  # Email inválido
            'password1': 'pass',
            'password2': 'pass',  # Senha muito simples
        })

        # Deve permanecer na página de cadastro com erros
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/signup.html')

        # Não deve criar novo usuário
        self.assertEqual(User.objects.count(), initial_user_count)

        # Deve conter erros no formulário
        self.assertContains(response, 'bi-exclamation-circle', status_code=200)


class UserProfileTests(TestCase):
    """Testes para o modelo UserProfile."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_create_user_profile(self):
        """Testa criação de UserProfile."""
        profile = UserProfile.objects.create(
            user=self.user,
            institution='Test University',
            research_area='Computational Chemistry',
            email_verified=True
        )

        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(profile.institution, 'Test University')
        self.assertEqual(profile.research_area, 'Computational Chemistry')
        self.assertTrue(profile.email_verified)

    def test_user_profile_auto_fields(self):
        """Testa campos automáticos do UserProfile."""
        profile = UserProfile.objects.create(
            user=self.user,
            institution='Test'
        )

        # created_at deve ser definido
        self.assertIsNotNone(profile.created_at)

        # updated_at deve ser definido
        self.assertIsNotNone(profile.updated_at)

        # email_verified deve ser False por padrão
        self.assertFalse(profile.email_verified)

    def test_user_profile_str(self):
        """Testa a representação em string do UserProfile."""
        profile = UserProfile.objects.create(
            user=self.user,
            institution='Test University'
        )

        expected_str = f"Profile of {self.user.username}"
        self.assertEqual(str(profile), expected_str)

    def test_user_profile_one_to_one(self):
        """Testa relação OneToOne entre User e UserProfile."""
        profile = UserProfile.objects.create(user=self.user)

        # Deve ser acessível de ambas as direções
        self.assertEqual(self.user.profile, profile)
        self.assertEqual(profile.user, self.user)


class AuthenticationFlowTests(TestCase):
    """Testes para o fluxo de autenticação."""

    def test_login_view(self):
        """Testa a view de login."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/login.html')

    def test_login_valid_credentials(self):
        """Testa login com credenciais válidas."""
        user = User.objects.create_user(
            username='loginuser',
            password='testpass123'
        )

        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'testpass123'
        })

        # Deve redirecionar para home após login bem-sucedido
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_login_invalid_credentials(self):
        """Testa login com credenciais inválidas."""
        response = self.client.post(reverse('login'), {
            'username': 'nonexistent',
            'password': 'wrongpass'
        })

        # Deve permanecer na página de login
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/login.html')
        self.assertContains(response, 'Erro', status_code=200)

    def test_logout_view(self):
        """Testa a view de logout."""
        user = User.objects.create_user(
            username='logoutuser',
            password='testpass123'
        )
        self.client.login(username='logoutuser', password='testpass123')

        response = self.client.get(reverse('logout'))

        # Deve redirecionar para home após logout
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

        # Usuário não deve mais estar autenticado
        self.assertNotIn('_auth_user_id', self.client.session)


class PasswordResetTests(TestCase):
    """Testes para as views de redefinição de senha."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_password_reset_view_get(self):
        """Testa acesso GET à página de redefinição de senha."""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/password_reset_form.html')
        self.assertContains(response, 'form')

    def test_password_reset_view_post_valid_email(self):
        """Testa envio de formulário de redefinição com email válido."""
        response = self.client.post(reverse('password_reset'), {
            'email': 'test@example.com'
        })

        # Deve redirecionar para password_reset_done
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_reset_done'))

    def test_password_reset_view_post_invalid_email(self):
        """Testa envio de formulário de redefinição com email inválido."""
        response = self.client.post(reverse('password_reset'), {
            'email': 'nonexistent@example.com'
        })

        # Mesmo com email inválido, ainda redireciona para password_reset_done
        # (por segurança, não revela se o email existe ou não)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('password_reset_done'))

    def test_password_reset_done_view(self):
        """Testa a página de confirmação de envio de email."""
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/password_reset_done.html')
        self.assertContains(response, 'e-mail')

    def test_password_reset_confirm_view_get_invalid_token(self):
        """Testa acesso à página de confirmação com token inválido."""
        # Usa um uidb64 e token inválidos
        response = self.client.get(reverse('password_reset_confirm', kwargs={
            'uidb64': 'MQ',
            'token': 'abc123-invalid-token'
        }))

        # Deve mostrar página de erro ou formulário inválido
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/password_reset_confirm.html')
        # Pode conter mensagem de erro sobre link inválido
        self.assertContains(response, 'form')

    def test_password_reset_complete_view(self):
        """Testa a página de conclusão de redefinição de senha."""
        response = self.client.get(reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'converter/password_reset_complete.html')
        self.assertContains(response, 'sucesso', status_code=200)


class ProfileViewTests(TestCase):
    """Testes para a view de perfil do usuário."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_profile_view_get(self):
        """Testa acesso GET à página de perfil."""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/profile.html')
        self.assertContains(response, 'form')

    def test_profile_view_get_unauthenticated(self):
        """Testa acesso à página de perfil sem autenticação."""
        self.client.logout()
        response = self.client.get(reverse('profile'))

        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_view_post_valid(self):
        """Testa atualização de perfil com dados válidos."""
        # Primeiro cria um perfil para o usuário
        from .models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=self.user)

        response = self.client.post(reverse('profile'), {
            'institution': 'Test University',
            'research_area': 'Computational Chemistry',
            'email_verified': True
        })

        # Deve redirecionar de volta para o perfil
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile'))

        # Verifica se o perfil foi atualizado
        profile.refresh_from_db()
        self.assertEqual(profile.institution, 'Test University')
        self.assertEqual(profile.research_area, 'Computational Chemistry')

    def test_profile_view_post_with_profile_picture(self):
        """Testa atualização de perfil com foto (simulado)."""
        # Este teste simula upload de arquivo
        # Em testes reais, precisaríamos de um arquivo mock
        response = self.client.post(reverse('profile'), {
            'institution': 'Another University',
            'research_area': 'Materials Science'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile'))

    def test_profile_auto_creation(self):
        """Testa criação automática de perfil ao acessar a view."""
        # Primeiro deleta qualquer perfil existente
        from .models import UserProfile
        UserProfile.objects.filter(user=self.user).delete()

        # Acessa a view - deve criar perfil automaticamente
        response = self.client.get(reverse('profile'))

        # Verifica se o perfil foi criado
        profile_exists = UserProfile.objects.filter(user=self.user).exists()
        self.assertTrue(profile_exists)


class UserFormsTests(TestCase):
    """Testes para os formulários do aplicativo user."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='existinguser',
            password='testpass123',
            email='existing@example.com'
        )

    def test_user_creation_form_valid(self):
        """Testa UserCreationForm com dados válidos."""
        from .forms import UserCreationForm

        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }

        form = UserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Verifica se o usuário pode ser salvo
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')

    def test_user_creation_form_duplicate_username(self):
        """Testa UserCreationForm com nome de usuário duplicado."""
        from .forms import UserCreationForm

        form_data = {
            'username': 'existinguser',  # Já existe
            'email': 'different@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }

        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_user_creation_form_duplicate_email(self):
        """Testa UserCreationForm com email duplicado."""
        from .forms import UserCreationForm

        form_data = {
            'username': 'differentuser',
            'email': 'existing@example.com',  # Já existe
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }

        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_user_creation_form_password_mismatch(self):
        """Testa UserCreationForm com senhas diferentes."""
        from .forms import UserCreationForm

        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass456!'  # Diferente
        }

        form = UserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_user_profile_form_valid(self):
        """Testa UserProfileForm com dados válidos."""
        from .forms import UserProfileForm
        from .models import UserProfile

        # Cria um perfil para testar
        profile = UserProfile.objects.create(user=self.user)

        form_data = {
            'institution': 'Test University',
            'research_area': 'Computational Chemistry'
        }

        form = UserProfileForm(data=form_data, instance=profile)
        self.assertTrue(form.is_valid())

        # Salva o formulário
        saved_profile = form.save()
        self.assertEqual(saved_profile.institution, 'Test University')
        self.assertEqual(saved_profile.research_area, 'Computational Chemistry')

    def test_user_profile_form_empty(self):
        """Testa UserProfileForm com campos vazios (deve ser válido)."""
        from .forms import UserProfileForm
        from .models import UserProfile

        profile = UserProfile.objects.create(user=self.user)

        form_data = {
            'institution': '',
            'research_area': ''
        }

        form = UserProfileForm(data=form_data, instance=profile)
        self.assertTrue(form.is_valid())  # Campos são opcionais

    def test_user_profile_form_with_file(self):
        """Testa UserProfileForm com upload de arquivo (simulado)."""
        from .forms import UserProfileForm
        from .models import UserProfile

        profile = UserProfile.objects.create(user=self.user)

        # Em um teste real, precisaríamos de um mock de arquivo
        # Por enquanto, testamos sem arquivo
        form_data = {
            'institution': 'Test University',
            'research_area': 'Materials Science'
        }

        form = UserProfileForm(data=form_data, instance=profile)
        self.assertTrue(form.is_valid())