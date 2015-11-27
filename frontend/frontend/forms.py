from django import forms


class IndexForm(forms.Form):
    url = forms.CharField(max_length=2000, widget=forms.TextInput(attrs={'class': 'input-xxlarge', 'placeholder': 'http://'}))
