# pacientes/views.py
"""
Views para o sistema de pacientes

Este módulo implementa todas as views necessárias para o gerenciamento
completo de pacientes no sistema médico da Guiné-Bissau.

Autor: Sistema Médico IA Guiné-Bissau
Data: 2025
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
#from django.contrib.auth import get_user_model
#from django.core.exceptions import ValidationError
#from django.db import transaction
from datetime import  date
#from decimal import Decimal

from .models import Paciente, HistoricoFamiliar, DoencaFamiliar
from .serializers import (
    PacienteCadastroSerializer,
    PacientePerfilCompletoSerializer,
    PacienteResumoSerializer,
    PacienteCompletoSerializer,
    HistoricoFamiliarSerializer,
    DoencaFamiliarSerializer
)
from pacientes.permissions import IsPacienteOrAdmin


from usuarios.permissions import IsAdminUser


class PacientePagination(PageNumberPagination):
    """Paginação customizada para pacientes"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PacienteCadastroView(APIView):
    """
    View para cadastro de novos pacientes
    
    POST /api/pacientes/cadastro/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Cadastra um novo paciente no sistema"""
        serializer = PacienteCadastroSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                paciente = serializer.save()
                
                # Dados de resposta
                response_data = {
                    'success': True,
                    'message': 'Paciente cadastrado com sucesso!',
                    'data': {
                        'id': paciente.id,
                        'numero_utente': paciente.numero_utente,
                        'nome_completo': paciente.nome_completo,
                        'email': paciente.user.email,
                        'user_id': paciente.user.id,
                        'porcentagem_preenchimento': paciente.porcentagem_preenchimento,
                        'perfil_completo': paciente.perfil_completo
                    }
                }
                
                return Response(response_data, {
                    "mensagem": "Paciente cadastrado com sucesso",
                }, status=status.HTTP_201_CREATED , )
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': 'Erro interno do servidor',
                    'errors': [str(e)]
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Dados inválidos',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PacientePerfilView(APIView):
    """
    View para gerenciar perfil do paciente
    
    GET /api/pacientes/perfil/ - Visualizar perfil próprio
    PUT /api/pacientes/perfil/ - Atualizar perfil completo
    PATCH /api/pacientes/perfil/ - Atualização parcial
    """
    permission_classes = [IsAuthenticated, IsPacienteOrAdmin]
    
    def get(self, request):
        """Retorna dados completos do perfil do paciente logado"""
        try:
            paciente = request.user.paciente
            serializer = PacientePerfilCompletoSerializer(paciente)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Paciente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Perfil de paciente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request):
        """Atualização completa do perfil"""
        try:
            paciente = request.user.paciente
            serializer = PacientePerfilCompletoSerializer(
                paciente, 
                data=request.data,
                partial=False
            )
            
            if serializer.is_valid():
                serializer.save()
                
                return Response({
                    'success': True,
                    'message': 'Perfil atualizado com sucesso!',
                    'data': serializer.data
                })
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Paciente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Perfil de paciente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request):
        """Atualização parcial do perfil"""
        try:
            paciente = request.user.paciente
            serializer = PacientePerfilCompletoSerializer(
                paciente, 
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                
                return Response({
                    'success': True,
                    'message': 'Perfil atualizado parcialmente!',
                    'data': serializer.data
                })
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Paciente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Perfil de paciente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class PacienteListView(APIView):
    """
    View para listar pacientes (apenas para Administrador)
    
    GET /api/pacientes/ - Lista todos os pacientes
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = PacientePagination
    
    def get(self, request):
        """Lista pacientes com filtros e paginação"""
        queryset = Paciente.objects.select_related(
            'user', 'regiao', 'cidade', 'tabanca_bairro'
        ).all()
        
        # Filtros opcionais
        search = request.query_params.get('search', '')
        regiao_id = request.query_params.get('regiao', '')
        cidade_id = request.query_params.get('cidade', '')
        genero = request.query_params.get('genero', '')
        idade_min = request.query_params.get('idade_min', '')
        idade_max = request.query_params.get('idade_max', '')
        perfil_completo = request.query_params.get('perfil_completo', '')
        
        # Aplicar filtros
        if search:
            queryset = queryset.filter(
                Q(nome_completo__icontains=search) |
                Q(numero_utente__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        if regiao_id:
            queryset = queryset.filter(regiao_id=regiao_id)
        
        if cidade_id:
            queryset = queryset.filter(cidade_id=cidade_id)
        
        if genero:
            queryset = queryset.filter(genero=genero)
        
        if perfil_completo:
            is_complete = perfil_completo.lower() == 'true'
            queryset = queryset.filter(perfil_completo=is_complete)
        
        # Filtro por idade
        if idade_min or idade_max:
            hoje = date.today()
            
            if idade_min:
                try:
                    idade_min = int(idade_min)
                    data_max = date(hoje.year - idade_min, hoje.month, hoje.day)
                    queryset = queryset.filter(data_nascimento__lte=data_max)
                except ValueError:
                    pass
            
            if idade_max:
                try:
                    idade_max = int(idade_max)
                    data_min = date(hoje.year - idade_max - 1, hoje.month, hoje.day)
                    queryset = queryset.filter(data_nascimento__gte=data_min)
                except ValueError:
                    pass
        
        # Ordenação
        ordering = request.query_params.get('ordering', '-created_at')
        valid_orderings = [
            'nome_completo', '-nome_completo',
            'data_nascimento', '-data_nascimento',
            'created_at', '-created_at',
            'numero_utente', '-numero_utente'
        ]
        
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        
        # Paginação
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = PacienteResumoSerializer(page, many=True)
            return paginator.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = PacienteResumoSerializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })


class PacienteDetailView(APIView):
    """
    View para visualizar detalhes de um paciente específico
    
    GET /api/pacientes/{id}/ - Detalhes do paciente
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request, pk):
        """Retorna dados completos de um paciente específico"""
        paciente = get_object_or_404(
            Paciente.objects.select_related(
                'user', 'regiao', 'cidade', 'tabanca_bairro', 'historico_familiar'
            ).prefetch_related('doencas_familiares'),
            pk=pk
        )
        
        serializer = PacienteCompletoSerializer(paciente)
        
        return Response({
            'success': True,
            'data': serializer.data
        })


class PacienteHistoricoFamiliarView(APIView):
    """
    View para gerenciar histórico familiar do paciente
    
    GET /api/pacientes/historico-familiar/ - Visualizar histórico
    POST /api/pacientes/historico-familiar/ - Criar histórico
    PUT /api/pacientes/historico-familiar/ - Atualizar histórico
    """
    permission_classes = [IsAuthenticated, IsPacienteOrAdmin]
    
    def get(self, request):
        """Retorna histórico familiar do paciente logado"""
        try:
            paciente = request.user.paciente
            historico, created = HistoricoFamiliar.objects.get_or_create(
                paciente=paciente
            )
            
            serializer = HistoricoFamiliarSerializer(historico)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'created': created
            })
            
        except Paciente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Perfil de paciente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request):
        """Cria ou atualiza histórico familiar"""
        try:
            paciente = request.user.paciente
            historico, created = HistoricoFamiliar.objects.get_or_create(
                paciente=paciente
            )
            
            serializer = HistoricoFamiliarSerializer(
                historico, 
                data=request.data,
                partial=not created
            )
            
            if serializer.is_valid():
                serializer.save()
                
                message = 'Histórico familiar criado!' if created else 'Histórico familiar atualizado!'
                
                return Response({
                    'success': True,
                    'message': message,
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'message': 'Dados inválidos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Paciente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Perfil de paciente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request):
        """Atualiza histórico familiar completo"""
        return self.post(request)


class PacienteDoencasFamiliaresView(APIView):
    """
    View para gerenciar doenças familiares específicas
    
    GET /api/pacientes/doencas-familiares/ - Lista doenças familiares
    POST /api/pacientes/doencas-familiares/ - Adiciona doença familiar
    """
    permission_classes = [IsAuthenticated, IsPacienteOrAdmin]
    
    def get(self, request):
        """Lista doenças familiares do paciente"""
        try:
            paciente = request.user.paciente
            doencas = DoencaFamiliar.objects.filter(paciente=paciente)
            
            serializer = DoencaFamiliarSerializer(doencas, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': doencas.count()
            })
            
        except Paciente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Perfil de paciente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request):
        """Adiciona nova doença familiar"""
        try:
            paciente = request.user.paciente
            
            # Pode receber uma doença ou lista de doenças
            data = request.data
            if isinstance(data, list):
                # Múltiplas doenças
                doencas_criadas = []
                
                for doenca_data in data:
                    doenca_data['paciente'] = paciente.id
                    serializer = DoencaFamiliarSerializer(data=doenca_data)
                    
                    if serializer.is_valid():
                        doenca = serializer.save(paciente=paciente)
                        doencas_criadas.append(serializer.data)
                    else:
                        return Response({
                            'success': False,
                            'message': 'Dados inválidos em uma das doenças',
                            'errors': serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'success': True,
                    'message': f'{len(doencas_criadas)} doenças familiares adicionadas!',
                    'data': doencas_criadas
                }, status=status.HTTP_201_CREATED)
            
            else:
                # Doença única
                serializer = DoencaFamiliarSerializer(data=data)
                
                if serializer.is_valid():
                    doenca = serializer.save(paciente=paciente)
                    
                    # Aqui é crucial verificar se a doença já existe para o paciente   serializer.data
                    return Response({
                        'success': True,
                        'message': 'Doença familiar adicionada!',
                        'data': doenca
                    }, status=status.HTTP_201_CREATED, )
                
                return Response({
                    'success': False,
                    'message': 'Dados inválidos',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Paciente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Perfil de paciente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class DoencaFamiliarDetailView(APIView):
    """
    View para gerenciar doença familiar específica
    
    GET /api/pacientes/doencas-familiares/{id}/ - Detalhes da doença
    PUT /api/pacientes/doencas-familiares/{id}/ - Atualizar doença
    DELETE /api/pacientes/doencas-familiares/{id}/ - Remover doença
    """
    permission_classes = [IsAuthenticated, IsPacienteOrAdmin]
    
    def get_object(self, request, pk):
        """Busca doença familiar do paciente logado"""
        try:
            paciente = request.user.paciente
            return DoencaFamiliar.objects.get(pk=pk, paciente=paciente)
        except (DoencaFamiliar.DoesNotExist, Paciente.DoesNotExist):
            return None
    
    def get(self, request, pk):
        """Retorna detalhes da doença familiar"""
        doenca = self.get_object(request, pk)
        if not doenca:
            return Response({
                'success': False,
                'message': 'Doença familiar não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DoencaFamiliarSerializer(doenca)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """Atualiza doença familiar"""
        doenca = self.get_object(request, pk)
        if not doenca:
            return Response({
                'success': False,
                'message': 'Doença familiar não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DoencaFamiliarSerializer(doenca, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'success': True,
                'message': 'Doença familiar atualizada!',
                'data': serializer.data
            })
        
        return Response({
            'success': False,
            'message': 'Dados inválidos',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Remove doença familiar"""
        doenca = self.get_object(request, pk)
        if not doenca:
            return Response({
                'success': False,
                'message': 'Doença familiar não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        doenca_nome = doenca.doenca
        doenca.delete()
        
        return Response({
            'success': True,
            'message': f'Doença "{doenca_nome}" removida do histórico familiar!'
        })


class PacienteEstatisticasView(APIView):
    """
    View para estatísticas gerais dos pacientes
    
    GET /api/pacientes/estatisticas/ - Estatísticas gerais
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Retorna estatísticas gerais dos pacientes"""
        
        # Contadores básicos
        total_pacientes = Paciente.objects.count()
        perfis_completos = Paciente.objects.filter(perfil_completo=True).count()
        cadastros_hoje = Paciente.objects.filter(
            created_at__date=date.today()
        ).count()
        
        # Distribuição por gênero
        distribuicao_genero = Paciente.objects.values('genero').annotate(
            total=Count('id')
        ).order_by('genero')
        
        # Distribuição por região
        distribuicao_regiao = Paciente.objects.select_related('regiao').values(
            'regiao__nome'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        # Distribuição por faixa etária
        hoje = date.today()
        faixas_etarias = {
            '0-17': 0,
            '18-29': 0,
            '30-49': 0,
            '50-64': 0,
            '65+': 0
        }
        
        for paciente in Paciente.objects.only('data_nascimento'):
            idade = hoje.year - paciente.data_nascimento.year
            if idade < 18:
                faixas_etarias['0-17'] += 1
            elif idade < 30:
                faixas_etarias['18-29'] += 1
            elif idade < 50:
                faixas_etarias['30-49'] += 1
            elif idade < 65:
                faixas_etarias['50-64'] += 1
            else:
                faixas_etarias['65+'] += 1
        
        # Média de preenchimento de perfil
        from django.db.models import Avg
        media_preenchimento = Paciente.objects.aggregate(
            media=Avg('porcentagem_preenchimento')
        )['media'] or 0
        
        return Response({
            'success': True,
            'data': {
                'resumo': {
                    'total_pacientes': total_pacientes,
                    'perfis_completos': perfis_completos,
                    'percentual_completos': round(
                        (perfis_completos / total_pacientes * 100) if total_pacientes > 0 else 0, 2
                    ),
                    'cadastros_hoje': cadastros_hoje,
                    'media_preenchimento': round(media_preenchimento, 2)
                },
                'distribuicao_genero': list(distribuicao_genero),
                'distribuicao_regiao': list(distribuicao_regiao),
                'faixas_etarias': faixas_etarias
            }
        })


class PacienteBuscarView(APIView):
    """
    View para busca avançada de pacientes
    
    GET /api/pacientes/buscar/ - Busca avançada
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Busca avançada de pacientes"""
        
        # Parâmetros de busca
        query = request.query_params.get('q', '').strip()
        
        if not query or len(query) < 2:
            return Response({
                'success': False,
                'message': 'Termo de busca deve ter pelo menos 2 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Busca em múltiplos campos
        pacientes = Paciente.objects.select_related(
            'user', 'regiao', 'cidade'
        ).filter(
            Q(nome_completo__icontains=query) |
            Q(numero_utente__icontains=query) |
            Q(user__email__icontains=query) |
            Q(telefone_principal__icontains=query) |
            Q(cidade__nome__icontains=query) |
            Q(regiao__nome__icontains=query)
        )[:50]  # Limitar resultados
        
        serializer = PacienteResumoSerializer(pacientes, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(serializer.data),
            'query': query
        })