from django.urls import path

from user.views import UserView, ProfilePictureView

urlpatterns = [
    path("api/user/", UserView.as_view(), name="user"),
    path("api/user/profile_picture/", ProfilePictureView.as_view(), name="profile_picture"),
]
