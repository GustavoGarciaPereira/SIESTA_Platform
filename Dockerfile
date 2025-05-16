# Usar imagem base do Python
FROM python:3.10-slim

# Configurar diretório de trabalho no container
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq-dev gcc --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copiar os arquivos do projeto
COPY . .

# Instalar dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1

# Coletar arquivos estáticos durante o build (ainda recomendado)
RUN python manage.py collectstatic --noinput

# Criar superusuário (pode ser mantido aqui se as variáveis forem passadas no build,
# ou movido para o entrypoint se depender de variáveis de runtime e o DB estiver pronto)
# Se movido, certifique-se que migrate rodou antes.
# Para simplificar, pode ser melhor criar o superusuário manualmente ou via um comando customizado após o deploy.
# RUN DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=1234 python manage.py createsuperuser --noinput

# Copiar o script de entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expor a porta
EXPOSE 8000

# Definir o entrypoint
ENTRYPOINT ["/entrypoint.sh"]
