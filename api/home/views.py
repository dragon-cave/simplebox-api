from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class Home(APIView):
    def get(self, request):
        try:
            return Response({"message:": "Hello World"})
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
