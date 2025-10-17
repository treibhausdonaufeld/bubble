from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from bubble.users.models import Profile, User

from .serializers import ProfileSerializer, UserSerializer


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.exclude(is_superuser=True).exclude(username="AnonymousUser")

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class ProfileViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for retrieving user profiles.
    Read-only access to profile information.
    """

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's profile."""
        return Profile.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Get the current user's profile."""
        profile = request.user.profile
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
