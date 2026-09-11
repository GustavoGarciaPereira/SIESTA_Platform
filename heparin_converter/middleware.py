"""Middlewares do projeto."""

from django.conf import settings


class DefaultLanguageMiddleware:
    """Mantém pt-BR como idioma padrão até o usuário escolher outro.

    Sem isso, o LocaleMiddleware negocia o idioma a partir do Accept-Language
    do navegador, o que fazia usuários com navegador em inglês verem páginas
    parcialmente traduzidas. A escolha explícita no seletor grava o cookie e
    passa a ser respeitada.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME):
            request.META['HTTP_ACCEPT_LANGUAGE'] = settings.LANGUAGE_CODE
        return self.get_response(request)
