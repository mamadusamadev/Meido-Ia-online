# Meido IA Online

## Descrição do Projeto
Sistema médico para a Guiné-Bissau que oferece cadastro geográfico completo (regiões, cidades e tabancas), gerenciamento de pacientes e usuários, além de rotas protegidas utilizando Django REST Framework. O objetivo é disponibilizar uma API segura e extensível para aplicações de saúde baseadas em inteligência artificial.

## Funcionalidades Principais
- Autenticação e autorização via JWT
- CRUD de usuários com diferentes níveis de permissão
- Registro e gerenciamento de pacientes
- Cadastro de regiões, cidades e tabancas
- Endpoints protegidos para consultas médicas

## Tecnologias Utilizadas
- Python 3
- Django 5
- Django REST Framework
- Simple JWT
- Django Jazzmin (admin)
- SQLite (por padrão, facilmente adaptável para PostgreSQL)

## Instalação e Configuração
1. Clone o repositório:
   ```bash
   git clone <URL-do-repositorio>
   cd Meido-Ia-online
   ```
2. Crie e ative um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure suas variáveis de ambiente criando um arquivo `.env` (exemplo):
   ```env
   SECRET_KEY=sua-secret-key
   DEBUG=True
   EMAIL_HOST_USER=seu-email@example.com
   EMAIL_HOST_PASSWORD=sua-senha
   ```
5. Aplique as migrações do banco de dados:
   ```bash
   python manage.py migrate
   ```
6. Inicie o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```
A API estará disponível em `http://localhost:8000/`.

## Como Contribuir
1. Faça um fork deste repositório e crie sua branch:
   ```bash
   git checkout -b minha-feature
   ```
2. Implemente sua alteração e adicione testes, se necessário.
3. Rode os testes locais com:
   ```bash
   python manage.py test
   ```
4. Envie seus commits e abra um Pull Request descrevendo suas mudanças.

## Estrutura do Projeto
```
core/        # configurações do projeto Django
usuarios/    # app de autenticação e perfis
pacientes/   # gerenciamento de pacientes
geografia/   # regiões, cidades e tabancas
consultas/   # módulos de consultas médicas
ia/          # integrações de inteligência artificial
static/      # arquivos estáticos
templates/   # templates HTML
manage.py    # utilitário de linha de comando do Django
requirements.txt  # dependências Python
```

## Endpoints da API
| Endpoint | Método | Descrição |
|----------|-------|-----------|
| `/api/usuarios/auth/login/` | POST | Gera tokens JWT para autenticação |
| `/api/usuarios/auth/registro/` | POST | Cria novo usuário |
| `/api/usuarios/perfil/` | GET/PUT | Visualiza ou atualiza dados do usuário |
| `/api/pacientes/cadastro/` | POST | Cadastro de paciente |
| `/api/pacientes/` | GET | Lista pacientes (admin) |
| `/api/geografia/regioes/` | GET/POST | Consulta ou cria regiões |
| `/api/geografia/regioes/<id>/` | GET/PUT/DELETE | Detalhes de uma região |
| `/api/geografia/cidades/` | GET/POST | CRUD de cidades |
| `/api/geografia/tabancas/` | GET/POST | CRUD de tabancas |

Os demais endpoints podem ser consultados no código de cada aplicativo.

## Licença
Ainda não há uma licença definida para este projeto. Entre em contato com os mantenedores caso deseje utilizá-lo em outros contextos.

## Contato
Para dúvidas ou sugestões abra uma issue ou envie um e-mail para [mamadusamadev@gmail.com](mailto:mamadusamadev@gmail.com).

*Esta documentação está em português, podendo ser traduzida livremente para inglês.*
