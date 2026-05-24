from django import forms


class ManualPurchaseForm(forms.Form):
    number1 = forms.IntegerField(min_value=1, max_value=45, label="번호 1")
    number2 = forms.IntegerField(min_value=1, max_value=45, label="번호 2")
    number3 = forms.IntegerField(min_value=1, max_value=45, label="번호 3")
    number4 = forms.IntegerField(min_value=1, max_value=45, label="번호 4")
    number5 = forms.IntegerField(min_value=1, max_value=45, label="번호 5")
    number6 = forms.IntegerField(min_value=1, max_value=45, label="번호 6")

    def clean(self):
        cleaned_data = super().clean()

        numbers = [
            cleaned_data.get("number1"),
            cleaned_data.get("number2"),
            cleaned_data.get("number3"),
            cleaned_data.get("number4"),
            cleaned_data.get("number5"),
            cleaned_data.get("number6"),
        ]

        if None in numbers:
            return cleaned_data

        if len(set(numbers)) != 6:
            raise forms.ValidationError("로또 번호는 중복될 수 없습니다.")

        return cleaned_data

    def get_numbers(self):
        return [
            self.cleaned_data["number1"],
            self.cleaned_data["number2"],
            self.cleaned_data["number3"],
            self.cleaned_data["number4"],
            self.cleaned_data["number5"],
            self.cleaned_data["number6"],
        ]