from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para leitura de dados do usuário (uso em /auth/me/)."""
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)
    time_display = serializers.CharField(source='get_time_display', read_only=True)
    can_edit = serializers.BooleanField(read_only=True)
    has_full_access = serializers.BooleanField(read_only=True)
    can_manage_users = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email',
            'papel', 'papel_display',
            'time', 'time_display',
            'avatar_url',
            'can_edit', 'has_full_access', 'can_manage_users',
            'is_superuser',
            'first_name', 'last_name',
        ]
        read_only_fields = [
            'id', 'papel', 'papel_display',
            'time', 'time_display',
            'can_edit', 'has_full_access', 'can_manage_users',
            'is_superuser',
        ]


class UsuarioGestaoSerializer(serializers.ModelSerializer):
    """
    Serializer para CRUD de usuários pelo painel (admin/superuser).

    Validações:
      - `password` obrigatório no create, opcional no update.
      - Admin (não-super) só pode mexer em usuários do próprio time.
      - Todo usuário (não-super) tem que ter `time`.
    """
    password = serializers.CharField(
        write_only=True, required=False,
        validators=[validate_password], style={'input_type': 'password'},
    )
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)
    time_display = serializers.CharField(source='get_time_display', read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'papel', 'papel_display',
            'time', 'time_display',
            'is_active', 'is_superuser',
            'avatar_url',
            'password',
        ]
        read_only_fields = ['id', 'papel', 'papel_display', 'time_display', 'is_superuser']

    def _requester(self):
        request = self.context.get('request')
        return getattr(request, 'user', None) if request else None

    def validate(self, attrs):
        requester = self._requester()
        if requester is None or not requester.is_authenticated:
            raise serializers.ValidationError('Sem usuário no contexto.')

        time_alvo = attrs.get('time', getattr(self.instance, 'time', None))

        # Admin (não-super) só gerencia usuários do próprio time.
        if not requester.is_superuser:
            if not requester.time:
                raise serializers.ValidationError(
                    'Você precisa ter um time atribuído para gerenciar usuários.'
                )
            if time_alvo != requester.time:
                raise serializers.ValidationError({
                    'time': f'Você só pode gerenciar usuários do time "{requester.get_time_display()}".'
                })

        # Todo usuário não-superuser precisa de time
        # (superuser pode ter time=None — ele tem acesso transversal)
        alvo_eh_super = getattr(self.instance, 'is_superuser', False)
        if not alvo_eh_super and not time_alvo:
            raise serializers.ValidationError({
                'time': 'Time é obrigatório.'
            })

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'Senha é obrigatória na criação.'})
        # Todo usuário criado pelo painel é admin do time
        validated_data['papel'] = 'admin'
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegistroSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'As senhas não coincidem.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = Usuario.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login (compatível com SimpleJWT)."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AtualizarUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para atualização de perfil do usuário."""

    class Meta:
        model = Usuario
        fields = ['email', 'first_name', 'last_name', 'avatar_url']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class MudarSenhaSerializer(serializers.Serializer):
    """Serializer para mudança de senha."""
    password_actual = serializers.CharField(write_only=True)
    password_new = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate_password_actual(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value

    def validate(self, attrs):
        if attrs['password_new'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'As senhas não coincidem.'})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['password_new'])
        user.save()
        return user