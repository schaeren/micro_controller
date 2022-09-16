import json

class Settings_Base:
    '''Base class for settings / configuration class.
    
    Maps a JSON configuration file to Python object. 
    The object's class must be derived from this class.
    '''
    def __init__(self) -> None:
        # Override this list in derived class if necessary: get_settings_as_text() will hide values of fields 
        # whose name contain one of these strings.
        self._password_fields = ['password', 'pwd']
    
    def load(self, module_name, settings_file_paths, json_path = ''):
        '''Load JSON file and map to instamce of class derived from this class.
        
        module_name : Name of the module to which the settings belong (used for error messages only).
        settings_file_path : String or list of strings with paths of files to load.
        json_path : Path of JSON node where mapping starts (default = root node(s)).
        '''
        # Allow single path as string or several paths as list of strings.
        if not isinstance(settings_file_paths, list):
            settings_file_paths = [settings_file_paths]
        for settings_file_path in settings_file_paths:
            try:
                with open(settings_file_path) as settings_file:
                    json_deserialized = json.load(settings_file)
                    branch = self._get_branch_or_leave(json_deserialized, json_path)
                    if branch:
                        self._load(module_name, branch, self, settings_file_path)
            except Exception as e:
                print(f'Error while reading {settings_file_path}: {e}')
                raise

    def get_settings_as_text(self, intro_text, prefix = '', obj = None):
        '''Returns all public attributes and their values (of derived class object) as formatted text.'''
        text = []
        if obj is None:
            obj = self
        if intro_text:
            text.append(intro_text)
        # Loop through all member variables except those starting with '_'.
        keys = sorted(obj.__dict__.keys())
        for key in [k for k in keys if k[0] != '_']:
            value = getattr(obj, key)
            if type(value) in [str, int, bool, list]:
                # For password fields: Return only stars (*). 
                for pwd in self._password_fields:
                    if pwd.lower() in key.lower():
                        value = '*' * len(value)
                text.append(f'  {prefix}{key} = {value}')
            else:
                prefix += key + '.'
                text.append(self.get_settings_as_text('', prefix, value))
        return '\n'.join(text)

    def _load(self, module_name : str, json_deserialized : object, obj : object, settings_file_path : str):
        '''Load JSON file and deserialize it to derived class object attributes.
        
        Method is called recursively for nested JSON nodes/objects.
        '''
        for key in json_deserialized:
            value = json_deserialized[key]

            if hasattr(obj, key):
                if type(value) in [str, int, bool, list]:
                    setattr(obj, key, value)
                elif type(value) is dict:
                    child_obj = getattr(obj, key)
                    if type(child_obj) is dict:
                        setattr(obj, key, value)
                    else:
                        # child_obj is instance of a (settings) class -> recursion
                        self._load(module_name, value, child_obj, settings_file_path)
                elif value == None:
                    pass
                else:
                    print(f"ERROR while loading settings from file {settings_file_path}: Key: '{key}', data type {type(value)} is not supported.")
            else:
                print(f"WARNING: Unknown setting for module '{module_name}' in {settings_file_path}: '{key}' : '{value}'")

    def _get_branch_or_leave(self, json_deserialized, path):
        '''Get JSON node/object with given path.
        
        Path is a concatenation of the node/object names, e.g. 'root_node.parent_node.node'.
        '''
        if not path:
            return json_deserialized
        p = path.split('.')
        j = json_deserialized
        for i in range(len(p)):
            if p[i] in j:
                j = j[p[i]]
            else:
                return None
        return j
