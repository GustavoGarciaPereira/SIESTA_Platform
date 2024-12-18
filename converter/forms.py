# converter/forms.py

from django import forms

class UploadFileForm(forms.Form):
    xyz_file = forms.FileField(label='Selecione o arquivo Heparin.xyz', 
                               help_text='Apenas arquivos com extensão .xyz são permitidos.')

    def clean_xyz_file(self):
        file = self.cleaned_data.get('xyz_file', False)
        if file:
            if not file.name.endswith('.xyz'):
                raise forms.ValidationError("Apenas arquivos .xyz são permitidos.")
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("O arquivo é muito grande. O tamanho máximo é de 5MB.")
        return file
