from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate

from .serializers import (
    UsuarioSerializer,
    UsuarioGestaoSerializer,
    RegistroSerializer,
    LoginSerializer,
    AtualizarUsuarioSerializer,
    MudarSenhaSerializer,
)
from .permissions import CanManageUsers

Usuario = get_user_model()


class RegistroView(generics.CreateAPIView):
    """Registra um novo usuário."""
    queryset = Usuario.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegistroSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Gera tokens JWT
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UsuarioSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Autentica usuário e retorna tokens JWT."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Credenciais inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Usuário desativado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UsuarioSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class LogoutView(APIView):
    """Invalida o refresh token do usuário."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logout realizado com sucesso.'})
        except Exception:
            return Response({'message': 'Logout realizado.'})


class MeView(generics.RetrieveUpdateAPIView):
    """Retorna ou atualiza dados do usuário autenticado."""
    permission_classes = [IsAuthenticated]
    serializer_class = UsuarioSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = AtualizarUsuarioSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UsuarioSerializer(instance).data)


class MudarSenhaView(APIView):
    """Altera a senha do usuário autenticado."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MudarSenhaSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Senha alterada com sucesso.'})


class UsuariosViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuários acessível pelo painel.

    - Superuser vê/mexe em todos.
    - Admin do painel vê/mexe só em admins do próprio time.

    O `UsuarioGestaoSerializer` aplica as validações de papel + time;
    o `CanManageUsers` controla quem entra na view e em quais objetos.
    """
    serializer_class = UsuarioGestaoSerializer
    permission_classes = [IsAuthenticated, CanManageUsers]

    def get_queryset(self):
        u = self.request.user
        qs = Usuario.objects.all().order_by('-date_joined')
        if u.is_superuser:
            return qs
        # Admin do painel: só seu time + esconde superusers
        return qs.filter(time=u.time).exclude(is_superuser=True)

    def perform_create(self, serializer):
        u = self.request.user
        # Admin (não-super): força time = time dele (defesa em profundidade,
        # já validado no serializer também)
        if not u.is_superuser:
            serializer.save(time=u.time)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        u = self.request.user
        if instance.pk == u.pk:
            raise PermissionDenied('Você não pode deletar a si mesmo.')
        if instance.is_superuser and not u.is_superuser:
            raise PermissionDenied('Não é possível deletar um superuser.')
        instance.delete()