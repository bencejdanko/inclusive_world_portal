"""
Forms for the Discovery Survey - simplified single-section form.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import DiscoverySurvey


class DiscoverySurveyForm(forms.ModelForm):
    """Discovery Questions - More About You"""
    
    # Learning style checkboxes stored as JSON - matching the provided options
    learning_visual = forms.BooleanField(
        label="Visual (Ex: PowerPoint presentations, pictures projected onto a screen, story maps, diagram, chart, graphic organizers, highlighters, color-coding)", 
        required=False
    )
    learning_auditory = forms.BooleanField(
        label="Auditory (Ex: Turn and talk, class discussions, have students repeat what you've said, use songs, chants, summarize to recap the lesson)", 
        required=False
    )
    learning_reading_writing = forms.BooleanField(
        label="Reading/Writing (Ex: Use handouts, books, dictionaries, and other texts, have students take notes, make lists, write sight words)", 
        required=False
    )
    learning_kinesthetic = forms.BooleanField(
        label="Kinesthetic (Ex: Role-play, science experiments, STEM activities, sorting objects/pictures, building words, play-doh, finger-tracing, magnetic letters, body-spelling, use real-life examples)", 
        required=False
    )
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'people_closest_to_you',
            'great_things_about_you',
            'things_like_to_do',
            'things_want_to_learn',
            'what_makes_you_happy',
            'what_makes_you_sad',
            'learned_at_school_liked',
            'learned_at_school_disliked',
            'prior_jobs',
            'iep_working',
            'iep_not_working',
            'supportive_devices',
            'working_environment_preferences',
            'form_helper',
        ]
        widgets = {
            'people_closest_to_you': forms.Textarea(attrs={'rows': 4, 'placeholder': 'At home, at school, friends... Who do you turn to when you need help?'}),
            'great_things_about_you': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What great things do people say about you?'}),
            'things_like_to_do': forms.Textarea(attrs={'rows': 5, 'placeholder': 'What do you like to do at home, outside, and just for fun? Who do you like doing them with? Why?'}),
            'things_want_to_learn': forms.Textarea(attrs={'rows': 5, 'placeholder': 'What new things would you like to learn? With whom? Why?'}),
            'what_makes_you_happy': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What makes you happy? How do you communicate feeling happy?'}),
            'what_makes_you_sad': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What makes you sad/mad/frustrated? How do you communicate that?'}),
            'learned_at_school_liked': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What did you like? Why?'}),
            'learned_at_school_disliked': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What didn\'t you like? Why? Could it have been presented differently?'}),
            'prior_jobs': forms.Textarea(attrs={'rows': 3, 'placeholder': 'List any jobs you have had...'}),
            'iep_working': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List 3 ways your IEP is working for you...'}),
            'iep_not_working': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List 3 ways your IEP isn\'t working... How can Inclusive World support you?'}),
            'supportive_devices': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Tablets, computers, communication devices, etc.'}),
            'working_environment_preferences': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Please share your environmental sensitivity...'}),
            'form_helper': forms.TextInput(attrs={'placeholder': 'Name of person who helped you...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load learning style from JSON if exists
        if self.instance and self.instance.pk and self.instance.learning_style:
            learn_style = self.instance.learning_style
            if isinstance(learn_style, dict):
                self.fields['learning_visual'].initial = learn_style.get('visual', False)
                self.fields['learning_auditory'].initial = learn_style.get('auditory', False)
                self.fields['learning_reading_writing'].initial = learn_style.get('reading_writing', False)
                self.fields['learning_kinesthetic'].initial = learn_style.get('kinesthetic', False)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save learning style as JSON
        styles = []
        if self.cleaned_data.get('learning_visual'):
            styles.append('Visual')
        if self.cleaned_data.get('learning_auditory'):
            styles.append('Auditory')
        if self.cleaned_data.get('learning_reading_writing'):
            styles.append('Reading/Writing')
        if self.cleaned_data.get('learning_kinesthetic'):
            styles.append('Kinesthetic')
        
        instance.learning_style = {
            'visual': self.cleaned_data.get('learning_visual', False),
            'auditory': self.cleaned_data.get('learning_auditory', False),
            'reading_writing': self.cleaned_data.get('learning_reading_writing', False),
            'kinesthetic': self.cleaned_data.get('learning_kinesthetic', False),
            'summary': ', '.join(styles),
        }
        if commit:
            instance.save()
        return instance

