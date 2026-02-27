from constance import config
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class ConfigView(APIView):
    """
    API endpoint that returns the current Constance configuration.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Retrieve all configuration values from django-constance
        config_values = {
            key: getattr(config, key)
            for key in dir(config)
            if not key.startswith("_") and not callable(getattr(config, key))
        }
        return Response(config_values, status=status.HTTP_200_OK)
