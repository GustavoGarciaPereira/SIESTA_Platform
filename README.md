### Passo a Passo do Projeto

**1. Preparação do Ambiente (Semana 1-2)**
- Instalar Docker e Docker Compose
- Configurar imagem Docker do SIESTA (verificar se já existe uma oficial ou criar uma)
- Configurar ambiente Python virtual para o Django
- Criar projeto Django básico (`django-admin startproject`)
- Estudar formato de arquivos XYZ e FDF (checar documentação do SIESTA)

**2. Conversor XYZ para FDF (Semana 3-4)**
- Desenvolver script Python para conversão:
  - Ler arquivo XYZ (usar pandas/numpy para manipulação)
  - Mapear dados para formato FDF
  - Validar estrutura do arquivo gerado
  - Criar testes unitários para a conversão
- Integrar o conversor ao Django como módulo/app

**3. Integração com SIESTA/Docker (Semana 5-6)**
- Configurar comunicação Django-Docker:
  - Usar SDK Docker para Python
  - Criar serviço para executar containers sob demanda
- Desenvolver sistema de filas para processamento
- Implementar monitoramento de execução:
  - Capturar logs do container
  - Verificar conclusão dos cálculos
  - Lidar com erros de execução

**4. Interface Web (Semana 7-8)**
- Criar views e templates Django para:
  - Upload de arquivos XYZ
  - Exibição de status de processamento
  - Visualização de resultados
- Implementar autenticação de usuários
- Desenvolver dashboard de monitoramento
- Adicionar download de resultados

**5. Testes e Otimização (Semana 9)**
- Testes de integração completa
- Otimizar performance:
  - Processamento assíncrono (Celery/RQ)
  - Caching de resultados
  - Gerenciamento de containers
- Testes de carga/stress
- Documentação do sistema

**6. Redação do TCC (Contínuo)**
- Estruturar documento:
  1. Introdução
  2. Revisão teórica
  3. Metodologia
  4. Implementação
  5. Resultados
  6. Conclusão
- Preparar materiais complementares:
  - Diagramas de arquitetura
  - Fluxogramas do sistema
  - Capturas de tela da interface

### Cronograma Sugerido (12 semanas)

| Semana | Atividades-Chave |
|--------|------------------|
| 1      | Configuração inicial do ambiente, estudos dos formatos de arquivo |
| 2      | Dockerização do SIESTA, projeto Django base |
| 3      | Desenvolvimento do conversor XYZ-FDF |
| 4      | Testes do conversor, integração inicial com Django |
| 5      | Comunicação Django-Docker, sistema de filas |
| 6      | Integração completa com SIESTA, tratamento de erros |
| 7      | Desenvolvimento da interface web (front-end) |
| 8      | Sistema de autenticação, dashboard de resultados |
| 9      | Testes de integração, otimizações de performance |
| 10     | Redação do TCC (capítulos 1-3) |
| 11     | Redação do TCC (capítulos 4-6), ajustes finais |
| 12     | Revisão final, preparação da apresentação |

### Ferramentas Recomendadas:
1. **Django**: Para gestão web do projeto
2. **Docker SDK for Python**: Para controle de containers
3. **Celery**: Para tarefas assíncronas (se necessário)
4. **Plotly/D3.js**: Para visualização de resultados
5. **Git**: Para controle de versão
6. **Sphinx**: Para documentação técnica

### Pontos Críticos para Atenção:
1. Comunicação entre Django e Docker (evitar chamadas síncronas)
2. Formatação exata dos arquivos FDF (checar requirements do SIESTA)
3. Gestão de recursos computacionais (limite de containers simultâneos)
4. Segurança no upload de arquivos
5. Persistência de dados entre execuções de containers

### Dicas Extras:
- Comece a escrever o TCC desde a primeira semana
- Mantenha um repositório Git organizado
- Use issues e milestones para controle
- Documente TODAS as decisões técnicas
- Faça testes intermediários com usuários reais
- Mantenha comunicação constante com seu orientador

Quer que detalhe mais alguma parte específica do projeto?
