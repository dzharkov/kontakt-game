from app.forms import EmptyForm

def empty_form_context_processor(request):
    return { 'empty_form' : EmptyForm() }