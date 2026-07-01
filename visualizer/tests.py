"""Testes do app visualizer."""

import io

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import OutFile


def _make_out_file(content=None):
    """Cria um arquivo .out simulado em BytesIO."""
    if content is None:
        content = """\
siesta: Atomic coordinates (Ang):
   1  O    4.4700    5.4820   -3.9220
   2  C    6.5430    4.5380   -4.7680
siesta: Mulliken populations:
Species: O  #1  Q = -0.4321
Species: C  #2  Q =  0.2512
"""
    return io.BytesIO(content.encode("utf-8"))


class OutFileModelTests(TestCase):
    """Testes do modelo OutFile."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_out_file(self):
        out = OutFile.objects.create(
            user=self.user,
            file=None,
            system_name="TestSystem",
            atom_count=136,
        )
        self.assertEqual(OutFile.objects.count(), 1)
        self.assertEqual(out.system_name, "TestSystem")
        self.assertEqual(out.atom_count, 136)
        self.assertEqual(out.user.username, "testuser")

    def test_str_representation(self):
        out = OutFile.objects.create(
            user=self.user,
            file=None,
            system_name="MyMolecule",
            atom_count=42,
        )
        self.assertIn("MyMolecule", str(out))
        self.assertIn("42", str(out))


class UploadViewTests(TestCase):
    """Testes da view de upload."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_upload_view_get(self):
        response = self.client.get(reverse("visualizer:upload_out"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizer/upload.html")
        self.assertContains(response, "form")

    def test_upload_view_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("visualizer:upload_out"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_upload_valid_out_file(self):
        f = _make_out_file()
        f.name = "test.out"
        response = self.client.post(
            reverse("visualizer:upload_out"),
            {"file": f, "system_name": "TestMolecule"},
        )
        # Should redirect to visualize page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OutFile.objects.count(), 1)
        out = OutFile.objects.first()
        self.assertEqual(out.user, self.user)
        self.assertEqual(out.system_name, "TestMolecule")
        self.assertEqual(out.atom_count, 2)
        self.assertIn(str(out.id), response.url)

    def test_upload_invalid_extension(self):
        f = io.BytesIO(b"not valid")
        f.name = "test.pdf"
        response = self.client.post(
            reverse("visualizer:upload_out"),
            {"file": f, "system_name": "Test"},
        )
        self.assertEqual(response.status_code, 200)  # Stays on page
        self.assertEqual(OutFile.objects.count(), 0)
        self.assertContains(response, "Apenas arquivos .out ou .txt")

    def test_upload_file_too_large(self):
        f = io.BytesIO(b"x" * (11 * 1024 * 1024))  # 11 MB
        f.name = "large.out"
        response = self.client.post(
            reverse("visualizer:upload_out"),
            {"file": f, "system_name": "Large"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OutFile.objects.count(), 0)
        self.assertContains(response, "10 MB")


class VisualizeViewTests(TestCase):
    """Testes da view de visualização 3D."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="other", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.out_file = OutFile.objects.create(
            user=self.user,
            system_name="TestSystem",
            atom_count=10,
        )

    def test_visualize_view_owner(self):
        response = self.client.get(
            reverse("visualizer:visualize", args=[self.out_file.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visualizer/visualize.html")
        self.assertContains(response, "canvas3d")

    def test_visualize_view_other_user(self):
        other_out = OutFile.objects.create(
            user=self.other_user,
            system_name="OtherSystem",
            atom_count=5,
        )
        response = self.client.get(
            reverse("visualizer:visualize", args=[other_out.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_visualize_view_unauthenticated(self):
        self.client.logout()
        response = self.client.get(
            reverse("visualizer:visualize", args=[self.out_file.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_visualize_view_nonexistent(self):
        response = self.client.get(
            reverse("visualizer:visualize", args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_api_content_view_owner(self):
        # Create an OutFile with actual file content
        f = _make_out_file()
        f.name = "test.out"
        self.client.post(
            reverse("visualizer:upload_out"),
            {"file": f, "system_name": "API"},
        )
        out = OutFile.objects.first()
        response = self.client.get(
            reverse("visualizer:out_content", args=[out.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Atomic coordinates", response.content.decode())

    def test_api_content_view_other_user(self):
        other_out = OutFile.objects.create(
            user=self.other_user,
            system_name="Other",
            atom_count=1,
        )
        response = self.client.get(
            reverse("visualizer:out_content", args=[other_out.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_api_atoms_json_view(self):
        f = _make_out_file()
        f.name = "test.out"
        self.client.post(
            reverse("visualizer:upload_out"),
            {"file": f, "system_name": "Atoms"},
        )
        out = OutFile.objects.first()
        response = self.client.get(
            reverse("visualizer:out_atoms", args=[out.id])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("atoms", data)
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["atoms"][0]["sym"], "O")


class ParserHelperTests(TestCase):
    """Testes das funções auxiliares de parse."""

    def test_extract_system_label(self):
        from .views import _extract_system_label
        content = "System label: MyMolecule\nother stuff"
        self.assertEqual(_extract_system_label(content), "MyMolecule")

    def test_extract_system_label_not_found(self):
        from .views import _extract_system_label
        self.assertEqual(_extract_system_label("no label here"), "")

    def test_count_atoms(self):
        from .views import _count_atoms
        content = """\
siesta: Atomic coordinates (Ang):
   1  O    0.0  0.0  0.0
   2  H    1.0  0.0  0.0
   3  H    0.0  1.0  0.0
siesta: end
"""
        self.assertEqual(_count_atoms(content), 3)

    def test_count_atoms_none(self):
        from .views import _count_atoms
        self.assertEqual(_count_atoms("no atoms"), 0)

    def test_parse_atoms_python(self):
        from .views import _parse_atoms_python
        content = """\
siesta: Atomic coordinates (Ang):
   1  O    4.4700    5.4820   -3.9220
   2  C    6.5430    4.5380   -4.7680
siesta: Mulliken populations:
Species: O  #1  Q = -0.4321
Species: C  #2  Q =  0.2512
"""
        atoms = _parse_atoms_python(content)
        self.assertEqual(len(atoms), 2)
        self.assertEqual(atoms[0]["sym"], "O")
        self.assertAlmostEqual(atoms[0]["q"], -0.4321)
        self.assertEqual(atoms[1]["sym"], "C")
        self.assertAlmostEqual(atoms[1]["q"], 0.2512)
