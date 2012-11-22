from annoying.decorators import render_to

@render_to('room/main.html')
def room(request, id):
    return {}