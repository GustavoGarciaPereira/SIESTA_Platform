"""Template tags auxiliares para formulários."""
from django import template

register = template.Library()


@register.simple_tag
def section_has_errors(form, *field_names):
    """Retorna True se qualquer campo informado tiver erros de validação."""
    return any(form[name].errors for name in field_names)
