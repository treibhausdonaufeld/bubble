from rest_framework import serializers

from bubble.users.models import Profile, User


class ProfileSerializer(serializers.ModelSerializer[Profile]):
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "username",
            "name",
            "email",
            "phone",
            "bio",
            "profile_image",
        ]


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["uuid", "username", "name", "email"]
