GAME_NAME = "RpgMap"
def get_msg(module_name, game_name):
    text = "Could not load "+module_name+". Module "+module_name+\
            " is needed to run "+game_name+".\n\nTry running 'pip install "+\
            module_name+"' in a console to install this dependency."
    return text

def check_gui(module_name):
    try:
        __import__(module_name)
    except ImportError:
        text = get_msg(module_name, GAME_NAME)
        print(text)
        import thorpy
        ap = thorpy.Application((800,600))
        thorpy.launch_blocking_alert("Missing module", text)
        ap.quit()
        exit()

def check_console(module_name):
    try:
        __import__(module_name)
    except ImportError:
        text = get_msg(module_name, GAME_NAME)
        print(text)
        exit()
