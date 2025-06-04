ARQUITETURA DO SISTEMA SUGERIDAR POR MIM É O SEGUINTE:
- Eu sugiro e vou dar mais informaçoes e voce vai implementar outros para que possamos ter um sistema mais completo e eficiente.

1. Estrutura de Usuários

ADMINISTRADOR
├── Dashboard Analytics (gráficos, estatísticas)
├── Gestão de Usuários
├── Configuração de IA
├── Logs e Auditoria
├── Backup/Manutenção
└── Moderação de Consultas
...

PACIENTE
├── Dashboard Pessoal de Saúde
├── Agendamento de Consultas
├── Histórico Médico
├── Notificações Inteligentes
└── Relatórios (PDF)
....

2. Fluxo de Consulta Detalhado sugerida:

    1. Paciente → Login → Dashboard
    2. "Nova Consulta" → Seleção de Especialidade
    3. Formulário Pré-Consulta:
    - Sintomas principais
    - Histórico relevante
    - Medicamentos atuais
    - Alergias
    4. Matching com Chatbot Especialista
    5. Consulta Interativa (IA)
    6. Geração de Relatório
    7. Armazenamento no Perfil
    8. Notificações de Follow-up



MODELAGEM DE DADOS (Estrutura Expandida) Sugerida:
Modelos Principais:
   # Modelo Usuario (Custom User)
- id, email, password, is_active, is_admin
- created_at, updated_at
- phone_number, preferred_language

# Modelo Paciente
- user (OneToOne)
- numero_utente (auto-gerado)
- nome_completo, data_nascimento
- genero, endereco, cidade
- contato_emergencia
- condicoes_cronicas[]
- alergias[]
- peso, altura, tipo_sanguineo

# Modelo Especialidade
- nome (Cardiologia, Pediatria, etc.)
- descricao
- prompt_base_ia
- configuracoes_especificas

# Modelo Consulta
- paciente, especialidade
- sintomas_relatados
- conversa_completa (JSON)
- diagnostico_preliminar
- recomendacoes
- medicamentos_sugeridos
- urgencia_nivel
- status (concluida, pendente)
- created_at

# Modelo IA_Config
- especialidade
- modelo_usado (llama3-70b, etc.)
- prompt_system
- parametros_fine_tuning
- versao, ativo

# Modelo Notificacao
- paciente, tipo
- titulo, mensagem
- enviada_em, lida
- agendada_para

# Modelo RelatorioSaude
- paciente
- periodo (semanal, mensal)
- metricas_saude
- sugestoes_ia
- gerado_em

obs: como eu disse devemos expandir o modelo de paciente para incluir mais informações. nao apenas modelo de paciente , todos modelos que temos e que podem ser expandidos.

FUNCIONALIDADES DETALHADAS
🏥 Dashboard do Paciente

Resumo de Saúde: Últimas consultas, medicamentos ativos
Próximos Lembretes: Consultas, medicamentos
Gráficos Pessoais: Evolução de peso, pressão arterial
Sugestões Semanais: Baseadas no perfil e histórico
Zona de Emergência: Botão direto para consulta urgente
Zona de perigo: para apagar a conta .

🤖 Sistema de IA Especializada
Especialidades Sugeridas:

Clínica Geral - Triagem inicial
Pediatria - Saúde infantil
Cardiologia - Problemas cardíacos
Ginecologia - Saúde da mulher
Nutrição - Orientação alimentar
Medicina Tropical - Doenças locais (malária, etc.)


Paciente Input → Pré-processamento → 
Análise de Sintomas → Consulta Especializada → 
Geração de Resposta → Validação → 
Armazenamento → Follow-up

Dashboard Administrativo

Analytics em Tempo Real:

Consultas por especialidade (gráfico pizza)
Evolução mensal de usuários (gráfico linha)
Distribuição geográfica (mapa)
Taxa de satisfação,

Gestão de IA: Ajustar prompts, treinar modelos
Moderação: Revisar consultas sensíveis
Relatórios: Exportar dados para autoridades de saúde

STACK TECNOLÓGICA DETALHADA

Backend (API REST)

     Django REST Framework
    ├── Authentication: JWT + Custom User
    ├── Database: PostgreSQL (prod) / SQLite (dev)
    ├── AI Integration: LangChain + Groq
    ├── File Storage: AWS S3 ou local
    ├── Email: Django Email Backend
    ├── Notifications: Celery + Redis
    └── API Documentation: DRF Spectacular


LangChain
    ├── Chain Types: ConversationChain, QAChain
    ├── Memory: ConversationBufferMemory
    ├── Prompts: Especializados por área médica
    └── Groq Integration: Llama3-70B-8192

    Processamento de Linguagem
    ├── Detecção de Idioma (PT/Crioulo)
    ├── Tradução Automática
    ├── Análise de Sentimento
    └── Extração de Entidades Médicas


obs:
Para criar estatísticas epidemiológicas robustas e auxiliar o Ministério da Saúde, precisamos de uma coleta de dados muito mais abrangente. Vou expandir o modelo de dados com foco em análises geográficas e de saúde pública.

nesse caso sugiro seguinte:

EXPANSÃO DO MODELO DE DADOS PARA ESTATÍSTICAS EPIDEMIOLÓGICAS
    🗺️ Estrutura Geográfica da Guiné-Bissau
                # Modelo Regiao
                - nome (Bissau, Bafatá, Biombo, Bolama, etc.)
                - codigo_regiao
                - populacao_estimada
                - coordenadas_gps
                - caracteristicas_climaticas

                # Modelo Cidade/Sector
                - regiao (ForeignKey)
                - nome
                - codigo_postal
                - populacao
                - tipo (urbana/rural)
                - distancia_hospital_mais_proximo

                # Modelo Tabanca/Bairro
                - cidade (ForeignKey)
                - nome
                - coordenadas_gps
                - infraestrutura_saude (enum: nenhuma, basica, completa)
                - acesso_agua_potavel (boolean)
                - acesso_eletricidade (boolean)

Dados Demográficos e Socioeconômicos Expandidos

        # Modelo Paciente (EXPANDIDO)
    class Paciente(models.Model):
        # Dados Básicos
        user = models.OneToOneField(User)
        numero_utente = models.CharField(unique=True)
        nome_completo = models.CharField(max_length=200)
        data_nascimento = models.DateField()
        genero = models.CharField(choices=GENERO_CHOICES)
        
        # Localização Detalhada
        regiao = models.ForeignKey(Regiao)
        cidade = models.ForeignKey(Cidade)
        tabanca_bairro = models.ForeignKey(Tabanca)
        endereco_completo = models.TextField()
        
        # Dados Socioeconômicos
        profissao = models.CharField()
        nivel_escolaridade = models.CharField(choices=ESCOLARIDADE_CHOICES)
        renda_familiar_mensal = models.CharField(choices=RENDA_CHOICES)
        numero_pessoas_casa = models.IntegerField()
        tipo_habitacao = models.CharField(choices=HABITACAO_CHOICES)
        
        # Acesso a Serviços
        tem_agua_potavel = models.BooleanField()
        tem_saneamento_basico = models.BooleanField()
        tem_energia_eletrica = models.BooleanField()
        meio_transporte_principal = models.CharField()
        
        # Dados Físicos e Saúde
        peso = models.FloatField()
        altura = models.FloatField()
        tipo_sanguineo = models.CharField()
        pressao_habitual = models.CharField()
        
        # Hábitos de Vida
        fuma = models.BooleanField()
        consome_alcool = models.CharField(choices=ALCOOL_CHOICES)
        pratica_exercicio = models.CharField(choices=EXERCICIO_CHOICES)
        dieta_principal = models.CharField(choices=DIETA_CHOICES)
        
        # Contatos
        telefone_principal = models.CharField()
        telefone_emergencia = models.CharField()
        contato_emergencia_nome = models.CharField()
        contato_emergencia_parentesco = models.CharField()

Histórico Familiar Detalhado:
# Modelo HistoricoFamiliar
class HistoricoFamiliar(models.Model):
    paciente = models.ForeignKey(Paciente)
    
    # Pais
    pai_vivo = models.BooleanField()
    pai_idade_morte = models.IntegerField(null=True)
    pai_causa_morte = models.CharField(null=True)
    pai_doencas_cronicas = models.JSONField(default=list)
    
    mae_viva = models.BooleanField()
    mae_idade_morte = models.IntegerField(null=True)
    mae_causa_morte = models.CharField(null=True)
    mae_doencas_cronicas = models.JSONField(default=list)
    
    # Irmãos
    numero_irmaos = models.IntegerField()
    irmaos_doencas_hereditarias = models.JSONField(default=list)
    
    # Histórico Geral
    historico_cancer_familia = models.BooleanField()
    historico_diabetes_familia = models.BooleanField()
    historico_hipertensao_familia = models.BooleanField()
    historico_cardiopatias_familia = models.BooleanField()
    historico_doencas_mentais_familia = models.BooleanField()
    historico_malaria_recorrente = models.BooleanField()
    
    # Doenças Específicas da Região
    historico_esquistossomose = models.BooleanField()
    historico_oncocercose = models.BooleanField()
    historico_tuberculose = models.BooleanField()

# Modelo DoencasFamiliares (relacionamento many-to-many)
class DoencaFamiliar(models.Model):
    paciente = models.ForeignKey(Paciente)
    doenca = models.CharField()
    parentesco = models.CharField() # pai, mãe, irmão, avô, etc.
    idade_diagnostico = models.IntegerField(null=True)
    observacoes = models.TextField()


 Histórico Médico Pessoal Expandido

 # Modelo HistoricoMedico
class HistoricoMedico(models.Model):
    paciente = models.ForeignKey(Paciente)
    
    # Doenças Tropicais Comuns
    historico_malaria = models.JSONField(default=list) # [{"ano": 2023, "gravidade": "leve"}]
    historico_dengue = models.BooleanField()
    historico_febre_amarela = models.BooleanField()
    historico_colera = models.BooleanField()
    
    # Doenças Respiratórias
    historico_tuberculose = models.BooleanField()
    historico_pneumonia = models.IntegerField(default=0) # quantas vezes
    historico_asma = models.BooleanField()
    
    # Doenças Crônicas
    diabetes = models.CharField(choices=DIABETES_CHOICES)
    hipertensao = models.BooleanField()
    cardiopatias = models.JSONField(default=list)
    
    # Saúde da Mulher
    historico_gravidez = models.JSONField(default=list) # para mulheres
    uso_contraceptivos = models.CharField(null=True)
    
    # Vacinação
    vacinas_completas = models.JSONField(default=list)
    vacina_covid = models.CharField(choices=COVID_VACINA_CHOICES)
    
    # Cirurgias
    cirurgias_realizadas = models.JSONField(default=list)
    
    # Medicamentos Atuais
    medicamentos_continuos = models.JSONField(default=list)
    alergias_medicamentos = models.JSONField(default=list)


# 📈 Modelos para Analytics e Estatísticas
# Modelo EstatisticaRegional
class EstatisticaRegional(models.Model):
    regiao = models.ForeignKey(Regiao)
    mes_ano = models.DateField()
    
    # Dados Demográficos
    total_usuarios_registrados = models.IntegerField()
    total_consultas_realizadas = models.IntegerField()
    
    # Top 10 Doenças Reportadas
    doencas_mais_comuns = models.JSONField() # {"malaria": 150, "hipertensao": 89}
    
    # Indicadores de Saúde
    casos_malaria_mes = models.IntegerField()
    casos_diabetes_novos = models.IntegerField()
    casos_hipertensao_novos = models.IntegerField()
    
    # Demografia das Consultas
    consultas_por_faixa_etaria = models.JSONField()
    consultas_por_genero = models.JSONField()
    consultas_por_especialidade = models.JSONField()

# Modelo RelatorioEpidemiologico
class RelatorioEpidemiologico(models.Model):
    titulo = models.CharField()
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()
    
    # Dados Agregados
    regioes_incluidas = models.JSONField()
    total_pacientes_analisados = models.IntegerField()
    
    # Principais Descobertas
    principais_indicadores = models.JSONField()
    doencas_emergentes = models.JSONField()
    areas_risco = models.JSONField()
    recomendacoes = models.TextField()
    
    # Metadados
    gerado_por = models.ForeignKey(User)
    gerado_em = models.DateTimeField(auto_now_add=True)
    arquivo_pdf = models.FileField()


Incentivos para Completar Dados:

Gamificação: Pontos por completar seções
Relatórios Personalizados: Mais dados = relatórios mais precisos
Prioridade: Perfis completos têm preferência em consultas
Lembretes Inteligentes: Notificações para atualizar dados

📋 RELATÓRIOS PARA O MINISTÉRIO DA SAÚDE
Relatórios Automáticos:

Relatório Epidemiológico Mensal

Top 10 doenças por região
Comparação com mês anterior
Alertas de surtos potenciais


Relatório Demográfico Trimestral

Distribuição etária dos usuários
Padrões de acesso por região
Indicadores socioeconômicos


Relatório de Saúde Pública Anual

Tendências de longo prazo
Eficácia de campanhas de saúde
Recomendações de políticas públicas


# Alertas Automáticos:
# Sistema de Alertas Epidemiológicos
if casos_malaria_regiao > media_historica * 2:
    enviar_alerta_ministerio("Possível surto de malária em {regiao}")

if consultas_diabetes_mes > threshold_diabetes:
    enviar_alerta_ministerio("Aumento significativo de diabetes em {regiao}")


obes final : essas foram a minha ideia, agora estou esperando a sua magica, sempre mais sempre segue as minhas ideias e implemente as suas , nao esqueça de boas praticas de desenvolvimento e de testes unitários, e de documentação, e de segurança,


- a pasta core é onde está o settings.py ou seja é o diretorio de projeto django 
- o resto dos arquivos que tem o arquivo models.py  sao apps de projeto.

-o diretorio usuario é onde será implementada modelo de usuario personalisado
   esse diretorio tem um arquivo chamada managers.py que é onde será implementado o manager de usuario




====================DOCUMENTO PARA IA JURIDICO =================================



# Plano Completo: IA Jurídica para Guiné-Bissau
## "Assistente Jurídico Digital GB"

---

## 1. VISÃO GERAL DO PROJETO

### Objetivo Principal
Criar uma inteligência artificial que funcione como um advogado digital, democratizando o acesso à justiça na Guiné-Bissau, desde educação jurídica básica até assistência em processos complexos.

### Público-Alvo
- **Cidadãos comuns** (sem conhecimento jurídico)
- **Pessoas com processos em andamento**
- **Advogados** (como ferramenta de apoio)
- **Estudantes de Direito**

---

## 2. FUNCIONALIDADES PRINCIPAIS

### 2.1 Para Cidadãos Comuns
- **Consultor Jurídico Virtual**: Diagnóstico inicial de problemas
- **Educação Legal**: Explicação de direitos em linguagem simples
- **Simulador de Situações**: "E se..." scenarios jurídicos
- **Calculadora de Direitos**: Pensões, indenizações, prazos
- **Prevenção Legal**: Como evitar problemas jurídicos

### 2.2 Para Processos em Andamento
- **Análise de Caso**: Questionário inteligente para coleta de informações
- **Estratégia Legal**: Identificação dos melhores argumentos
- **Gerador de Documentos**: Petições, recursos, contestações
- **Timeline do Processo**: Explicação de etapas e prazos
- **Acompanhamento**: Lembretes e próximos passos

### 2.3 Para Advogados
- **Pesquisa Jurisprudencial**: Busca inteligente de precedentes
- **Revisão de Peças**: Análise e sugestões de melhoria
- **Biblioteca Jurídica**: Acesso rápido a leis e códigos
- **Modelos Personalizados**: Templates adaptados por área
- **Análise de Probabilidade**: Chances de sucesso do caso

---

## 3. ARQUITETURA TÉCNICA

### 3.1 Componentes Principais
```
Frontend (Interface do Usuário)
├── Web App (React/Vue.js)
├── Mobile App (React Native/Flutter)
└── WhatsApp Bot (integração)

Backend (Lógica de Negócio)
├── API Gateway
├── Serviço de Processamento de Linguagem Natural
├── Base de Conhecimento Jurídico
├── Sistema de Geração de Documentos
└── Sistema de Notificações

Base de Dados
├── Legislação da Guiné-Bissau
├── Jurisprudência
├── Modelos de Documentos
├── Histórico de Consultas
└── Perfis de Usuários
```

### 3.2 Tecnologias Recomendadas

**Para IA/NLP:**
- **Primeira Fase**: API do Claude ou GPT-4 (prototipagem rápida)
- **Segunda Fase**: Fine-tuning de modelo local (Llama 3 ou Mixtral)
- **Processamento**: Python + FastAPI
- **Embeddings**: Para busca semântica na base jurídica

**Para Frontend:**
- **Web**: React.js + TypeScript
- **Mobile**: React Native ou Flutter
- **WhatsApp**: API do WhatsApp Business

**Para Backend:**
- **API**: Node.js/Express ou Python/FastAPI
- **Base de Dados**: PostgreSQL + Vector Database (Pinecone/Weaviate)
- **Cloud**: AWS, Google Cloud ou Azure

---

## 4. BASE DE CONHECIMENTO JURÍDICO

### 4.1 Fontes de Dados Identificadas
- **Legis-PALOP+TL**: Base de dados principal
- **Códigos Específicos**: Civil, Penal, Processo Civil/Penal
- **Constituição da Guiné-Bissau**
- **Jurisprudência dos Tribunais Superiores**
- **Doutrina Jurídica em Português**

### 4.2 Estruturação dos Dados
```
Hierarquia Legal:
├── Constituição
├── Códigos (Civil, Penal, etc.)
├── Leis Ordinárias
├── Decretos
├── Regulamentos
└── Jurisprudência
    ├── Supremo Tribunal
    ├── Tribunais de Recurso
    └── Tribunais de 1ª Instância
```

### 4.3 Processamento
- **Digitalização**: OCR para documentos físicos
- **Estruturação**: Extração de artigos, parágrafos, incisos
- **Indexação**: Criação de embeddings para busca semântica
- **Versionamento**: Controle de versões das leis

---

## 5. INTERFACE DO USUÁRIO

### 5.1 Fluxo Principal
```
1. Boas-vindas → Seleção de Idioma (Português/Crioulo)
2. Tipo de Usuário → Cidadão/Advogado/Estudante
3. Categoria do Problema → Civil/Penal/Trabalhista/etc.
4. Coleta de Informações → Questionário inteligente
5. Análise → Processamento pela IA
6. Resultados → Orientações + Documentos + Próximos passos
7. Acompanhamento → Lembretes e updates
```

### 5.2 Recursos de Acessibilidade
- **Suporte a Crioulo**: Tradução automática
- **Interface Simples**: Design intuitivo para baixa literacia digital
- **Áudio**: Leitura de textos (text-to-speech)
- **Offline**: Funcionalidades básicas sem internet
- **WhatsApp**: Canal familiar para muitos usuários

---

## 6. ÁREAS JURÍDICAS PRIORITÁRIAS

### Fase 1 (MVP)
- **Direito de Família**: Divórcio, pensão alimentar, guarda
- **Direito Trabalhista**: Salários, demissões, acidentes
- **Direito Civil**: Contratos, propriedade, vizinhança
- **Direito Penal**: Crimes comuns, autodefesa

### Fase 2 (Expansão)
- **Direito Administrativo**: Documentos, licenças
- **Direito Comercial**: Empresas, contratos comerciais
- **Direito Imobiliário**: Compra/venda, registros
- **Direito Ambiental**: Recursos naturais, poluição

---

## 7. PLANO DE DESENVOLVIMENTO

### Fase 1: MVP (3-4 meses)
**Mês 1-2:**
- Coleta e estruturação da base jurídica
- Desenvolvimento da API básica
- Interface web simples
- Integração com Claude/GPT-4

**Mês 3-4:**
- Testes com usuários reais
- Refinamento dos prompts de IA
- Sistema de geração de documentos básicos
- Implementação do bot WhatsApp

### Fase 2: Expansão (3-4 meses)
- App mobile
- Fine-tuning de modelo próprio
- Mais áreas jurídicas
- Sistema de acompanhamento de processos
- Melhorias baseadas em feedback

### Fase 3: Consolidação (2-3 meses)
- Parcerias com tribunais/ordem dos advogados
- Sistema de métricas e analytics
- Funcionalidades avançadas para advogados
- Expansão para outros países PALOP

---

## 8. MONETIZAÇÃO E SUSTENTABILIDADE

### Modelos de Receita
- **Freemium**: Consultas básicas gratuitas, avançadas pagas
- **Assinaturas**: Planos para advogados e escritórios
- **Parcerias**: Tribunais, ONG's, governo
- **Doações**: Organizações internacionais de direitos humanos

### Custos Estimados (Mensais)
- **APIs de IA**: $200-500 (dependendo do volume)
- **Hosting/Cloud**: $100-300
- **Desenvolvimento**: $2000-5000 (equipe)
- **Total Inicial**: ~$3000-6000/mês

---

## 9. EQUIPE NECESSÁRIA

### Essencial (MVP)
- **1 Desenvolvedor Full-Stack** (você + 1)
- **1 Especialista em IA/NLP**
- **1 Jurista da Guiné-Bissau**
- **1 Designer UX/UI**

### Expansão
- **Desenvolvedores Mobile**
- **Especialista em Dados**
- **Marketing/Vendas**
- **Suporte ao Cliente**

---

## 10. RISCOS E MITIGAÇÕES

### Riscos Técnicos
- **Qualidade da IA**: Testes extensivos + feedback loop
- **Dados insuficientes**: Parcerias com universidades/tribunais
- **Escalabilidade**: Arquitetura cloud-native

### Riscos Jurídicos
- **Responsabilidade legal**: Disclaimers claros + supervisão humana
- **Regulamentação**: Diálogo com Ordem dos Advogados
- **Ética**: Comitê consultivo com juristas

### Riscos de Mercado
- **Aceitação**: Programas de educação + parcerias locais
- **Competição**: Foco na especialização local
- **Sustentabilidade**: Diversificação de fontes de receita

---

## 11. MÉTRICAS DE SUCESSO

### KPIs Principais
- **Usuários ativos mensais**
- **Satisfação do usuário** (NPS)
- **Casos resolvidos com sucesso**
- **Tempo médio de resposta**
- **Taxa de adoção por advogados**

### Impacto Social
- **Aumento no acesso à justiça**
- **Redução de custos legais**
- **Melhoria na educação jurídica**
- **Eficiência do sistema judicial**

---

## 12. ROADMAP DETALHADO

### Q1 2025: Fundação
- [ ] Constituição da equipe
- [ ] Coleta da base jurídica
- [ ] Desenvolvimento da API base
- [ ] Prototipo web funcional

### Q2 2025: MVP
- [ ] Teste com 100 usuários beta
- [ ] WhatsApp bot
- [ ] Documentos básicos
- [ ] Parcerias iniciais

### Q3 2025: Lançamento
- [ ] Lançamento público
- [ ] App mobile
- [ ] Marketing e divulgação
- [ ] Coleta de feedback

### Q4 2025: Crescimento
- [ ] 1.000+ usuários ativos
- [ ] Modelo de negócio validado
- [ ] Expansão de funcionalidades
- [ ] Planejamento internacional

---

## PRÓXIMOS PASSOS IMEDIATOS

1. **Validar o conceito**: Entrevistas com potenciais usuários
2. **Formar equipe mínima**: Recrutar desenvolvedor + jurista
3. **Coletar dados jurídicos**: Baixar base do Legis-PALOP
4. **Criar protótipo**: Interface simples + integração IA
5. **Testar com usuários reais**: Validar utilidade e usabilidade

---
==================================================================

Recomendação: Modelo Híbrido
Acesso Sem Cadastro (Consultas Básicas)

Perguntas simples sobre direitos
Explicações de leis em linguagem simples
Calculadoras básicas (prazos, valores)
Orientações gerais

Vantagens:

Maior acessibilidade
Sem barreiras de entrada
Pessoas com pouca educação digital podem usar
Privacidade total para consultas sensíveis

Com Cadastro (Funcionalidades Avançadas)

Acompanhamento de processos específicos
Geração de documentos personalizados
Histórico de consultas
Lembretes de prazos
Consultas mais complexas

Estratégia Recomendada:
Nível 1: Anônimo (Sem Cadastro)
✅ Consultas básicas
✅ Educação jurídica
✅ Explicação de leis
✅ Calculadoras simples
❌ Histórico
❌ Documentos personalizados
Nível 2: Cadastro Simples (Só email/telefone)
✅ Tudo do Nível 1 +
✅ Histórico de consultas
✅ Lembretes por email/SMS
✅ Documentos básicos
❌ Acompanhamento de processos
Nível 3: Perfil Completo
✅ Tudo anterior +
✅ Documentos jurídicos completos
✅ Acompanhamento de processos
✅ Consultas ilimitadas
✅ Suporte prioritário
Para WhatsApp:

Funciona naturalmente sem cadastro
Número do telefone já identifica o usuário
Pode salvar histórico automaticamente
Mais familiar para usuários locais

Campos Mínimos para Cadastro:

Nome completo
Telefone/WhatsApp
Email (opcional)
Localização (cidade/região)
Tipo de usuário (cidadão/advogado/estudante)