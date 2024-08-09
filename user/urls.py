from django.urls import path

from user.views import UserView, ProfilePictureView

urlpatterns = [
    path("", UserView.as_view(), name="user"),
    path("profile_picture/", ProfilePictureView.as_view(), name="profile_picture"),
]
