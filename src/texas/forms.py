from django import forms

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from texas.models import *

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=20, label='Username',
                               widget=forms.TextInput(attrs={'class': 'grumblr-input-text',
                                                             'placeholder': 'Username'}))
    first_name = forms.CharField(max_length=20, label='First name',
                                 widget=forms.TextInput(attrs={'class': 'grumblr-input-text',
                                                               'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=20, label='Last name',
                                widget=forms.TextInput(attrs={'class': 'grumblr-input-text',
                                                              'placeholder': 'Last name'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'grumblr-input-password',
                                                                           'placeholder': 'Email'}))
    password1 = forms.CharField(max_length=30,
                                label='Password',
                                widget=forms.PasswordInput(attrs={'class': 'grumblr-input-password',
                                                                  'placeholder': 'Create a password'}))
    password2 = forms.CharField(max_length=30,
                                label='Confirm password',
                                widget=forms.PasswordInput(attrs={'class': 'grumblr-input-password',
                                                                  'placeholder': 'Confirm your password'}))

    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super(RegistrationForm, self).clean()

        # Confirms that the two password fields match
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        # Generally return the cleaned data we got from our parent.
        return cleaned_data

    # Customizes form validation for the username field.
    def clean_username(self):
        # Confirms that the username is not already present in the
        # User model database.
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")

        # Generally return the cleaned data we got from the cleaned_data
        # dictionary
        return username

class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(max_length=30, label='Type your new password',
                                widget=forms.PasswordInput())
    password2 = forms.CharField(max_length=30, label='Type your new password one more time',
                                widget=forms.PasswordInput())
    def clean_password(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super(ResetPasswordForm, self).clean()

        # Confirms that the two password fields match
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        # Generally return the cleaned data we got from our parent.
        return cleaned_data


BIRTH_YEAR_CHOICES = tuple(x for x in range(2017, 1917, -1))


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = (  'dob', 'profile_photo_src')
        widgets = {
            'profile_photo_src': forms.FileInput(attrs={'class':'form-control'}),
            'dob': forms.SelectDateWidget(
                years=BIRTH_YEAR_CHOICES,
                attrs={'class': 'form-control'}
            )
            # attrs={),
        }


class EditUser(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'firstname', 'required': 'true'}),
            'last_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'lastname', 'required': 'true'}),
            'email': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Email Address', 'required': 'true'}),
        }

class ChangePasswordForm(forms.Form):
    newpassword1 = forms.CharField(max_length=200,
                                   label='NewPassword',
                                   widget=forms.TextInput(
                                       attrs={'type': 'password', 'class': 'form-control',
                                              'placeholder': 'New Password',
                                              'required': 'true'}))
    newpassword2 = forms.CharField(max_length=200,
                                   label='NewPassword',
                                   widget=forms.TextInput(
                                       attrs={'type': 'password', 'class': 'form-control',
                                              'placeholder': 'Confirm New Password',
                                              'required': 'true'}))

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        password1 = cleaned_data.get('newpassword1')
        password2 = cleaned_data.get('newpassword2')
        # user = authenticate(username=username, password=password)
        # if user is None:
        #     raise forms.ValidationError("invalid username or password.")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("new passwords did not match.")
        # if password == password1:
        #     raise forms.ValidationError("new password should be different")
        return cleaned_data

class EmailPassword(forms.Form):
    email = forms.EmailField(max_length=50, label='Email Address',
                             widget=forms.TextInput(
                                 attrs={'type': 'email', 'class': 'form-control', 'placeholder': 'Email Address',
                                        'required': 'true'}))

    def clean(self):
        cleaned_data = super(EmailPassword, self).clean()
        email = cleaned_data.get('email')
        if not User.objects.filter(email__exact=email):
            raise forms.ValidationError("invalid email.")
        return cleaned_data


class JoinRoomForm(forms.Form):
    room_number = forms.CharField(max_length=50, label='The room number',
                               widget=forms.TextInput(attrs={'class': 'grumblr-input-text',
                                                             'placeholder': 'RoomNumber'}))

    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username', None)
        super(JoinRoomForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(JoinRoomForm, self).clean()
        game_no = self.cleaned_data.get('room_number')
        if not Game.objects.filter(game_no=game_no):
            raise forms.ValidationError("The room number does not exist.")
        # before add user into game room, check if he/she has sufficient balance
        game = Game.objects.get(game_no=game_no)
        if not game.players.filter(username=self.username) and \
                        game.player_num == game.players.count():
            raise forms.ValidationError("The room is full.")

        return cleaned_data