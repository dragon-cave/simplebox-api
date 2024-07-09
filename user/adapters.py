from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=False):
        super().save_user(request, user, form, commit)
        data = form.cleaned_data
        user.full_name = data.get('full_name')
        user.username = data.get('username')
        user.email = data.get('email')
        user.save()
        return user
