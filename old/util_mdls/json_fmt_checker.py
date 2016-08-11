import json

def is_json(file_path):
    try: 
        json_object = json.loads(file_path)
    except ValueError, e:
        print e
        return False
    return True
