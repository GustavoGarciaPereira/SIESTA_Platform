"""Views do app visualizer — upload, visualização 3D e API de conteúdo."""

from __future__ import annotations

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from .forms import OutFileForm
from .models import OutFile

logger = logging.getLogger(__name__)


@login_required
def upload_out(request):
    """View para upload de arquivo .out do SIESTA."""
    if request.method == "POST":
        form = OutFileForm(request.POST, request.FILES)
        if form.is_valid():
            out_file = form.save(commit=False)
            out_file.user = request.user

            # Tenta extrair system_name e atom_count do conteúdo
            content = request.FILES["file"].read().decode("utf-8", errors="replace")
            request.FILES["file"].seek(0)

            out_file.system_name = form.cleaned_data.get("system_name") or _extract_system_label(content)
            out_file.atom_count = _count_atoms(content)
            out_file.save()

            logger.info(
                "OutFile uploaded: id=%s user=%s atoms=%s",
                out_file.id, request.user.username, out_file.atom_count,
            )
            return redirect(reverse("visualizer:visualize", args=[out_file.id]))
    else:
        form = OutFileForm()

    return render(request, "visualizer/upload.html", {"form": form})


@login_required
def visualize_out(request, out_id):
    """View principal — renderiza o visualizador 3D com Three.js + WASM."""
    out_file = get_object_or_404(OutFile, id=out_id, user=request.user)
    return render(request, "visualizer/visualize.html", {
        "out_file": out_file,
        "api_url": reverse("visualizer:out_content", args=[out_file.id]),
    })


@login_required
def out_content(request, out_id):
    """API interna: retorna o conteúdo do arquivo .out como texto."""
    out_file = get_object_or_404(OutFile, id=out_id, user=request.user)

    try:
        with out_file.file.open("r") as f:
            content = f.read()
        return HttpResponse(content, content_type="text/plain; charset=utf-8")
    except Exception as e:
        logger.error("Failed to read OutFile %s: %s", out_id, e)
        raise Http404("Arquivo não encontrado ou corrompido.")


@login_required
def out_atoms_json(request, out_id):
    """API: retorna os átomos parseados como JSON (usando o parser WASM no backend).

    Fallback: se o WASM não estiver disponível, faz parse básico em Python.
    """
    out_file = get_object_or_404(OutFile, id=out_id, user=request.user)

    try:
        with out_file.file.open("r") as f:
            content = f.read()

        atoms = _parse_atoms_python(content)
        return JsonResponse({"atoms": atoms, "count": len(atoms)})
    except Exception as e:
        logger.error("Failed to parse OutFile %s: %s", out_id, e)
        return JsonResponse({"error": str(e)}, status=400)


# ─── Helper functions ─────────────────────────────────────────────────────────

def _extract_system_label(content: str) -> str:
    """Extrai SystemLabel do conteúdo do .out."""
    for line in content.splitlines():
        if "System label" in line or "SystemLabel" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                return parts[-1].strip()
    return ""


def _count_atoms(content: str) -> int:
    """Conta átomos na seção Atomic coordinates do .out."""
    count = 0
    in_block = False
    for line in content.splitlines():
        if "Atomic coordinates (Ang)" in line:
            in_block = True
            continue
        if in_block:
            t = line.strip()
            if not t or t.startswith("siesta:"):
                break
            count += 1
    return count


def _parse_atoms_python(content: str) -> list[dict]:
    """Parse básico em Python (fallback quando WASM não disponível)."""
    atoms = []
    in_coords = False

    for line in content.splitlines():
        if "Atomic coordinates (Ang)" in line:
            in_coords = True
            continue
        if in_coords:
            t = line.strip()
            if not t or t.startswith("siesta:"):
                break
            parts = t.split()
            if len(parts) >= 5:
                atoms.append({
                    "sym": parts[1],
                    "x": float(parts[2]),
                    "y": float(parts[3]),
                    "z": float(parts[4]),
                    "q": 0.0,
                })

    # Extract Mulliken charges
    mulliken = []
    in_mull = False
    for line in content.splitlines():
        if "Mulliken populations" in line:
            in_mull = True
            continue
        if in_mull:
            t = line.strip()
            if not t or t.startswith("siesta:"):
                break
            if "Q =" in t:
                try:
                    q = float(t.split("Q =")[-1].strip())
                    mulliken.append(q)
                except ValueError:
                    pass

    if len(mulliken) == len(atoms):
        for i, a in enumerate(atoms):
            a["q"] = mulliken[i]

    return atoms
