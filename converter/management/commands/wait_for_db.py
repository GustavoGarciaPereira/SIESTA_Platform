"""Comando de gerenciamento para aguardar o banco de dados ficar disponível."""

import time

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Aguarda o banco de dados aceitar conexões (usado no entrypoint do Docker)."""

    help = 'Aguarda o banco de dados ficar disponível antes de continuar.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retries', type=int, default=10,
            help='Número de tentativas (padrão: 10).',
        )
        parser.add_argument(
            '--delay', type=float, default=2.0,
            help='Intervalo entre tentativas em segundos (padrão: 2).',
        )

    def handle(self, *args, **options):
        retries = options['retries']
        delay = options['delay']

        for attempt in range(1, retries + 1):
            try:
                connections['default'].ensure_connection()
            except OperationalError:
                self.stdout.write(
                    f'Banco indisponível, tentativa {attempt}/{retries}...'
                )
                time.sleep(delay)
            except ImproperlyConfigured as exc:
                raise SystemExit(
                    f'Configuração de banco inválida: {exc}\n'
                    'Defina DB_ENGINE/DB_* , DATABASE_URL ou PGHOST/PGDATABASE/... '
                    'no ambiente do serviço.'
                )
            else:
                self.stdout.write(self.style.SUCCESS('Banco de dados pronto.'))
                return

        raise SystemExit('Não foi possível conectar ao banco de dados.')
