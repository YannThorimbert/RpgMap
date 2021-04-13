import pickle, os
import thorpy
from PyWorld2D.mapobjects.objects import MapObject

def ask_save(me):
    choice = thorpy.launch_binary_choice("Do you want to save this map ?")
    default_fn = me.get_fn().replace(".map","")
    if choice:
        fn = thorpy.get_user_text("Filename", default_fn, size=(me.W//2,40))
        fn += ".map"
        to_file(me, fn)
    thorpy.functions.quit_menu_func()


def get_saved_files_button(root):
    files = [fn for fn in os.listdir(root) if fn.endswith(".map")]
    ddl = thorpy.DropDownListLauncher.make("Choose a file to load", "", files)
    def unlaunch():
        ddl.default_unlaunch()
        thorpy.functions.quit_menu_func()
    ddl.unlaunch_func = unlaunch
    return ddl


def ask_load():
    pass
################################################################################

def obj_to_file(obj, f):
    for attr in obj.get_saved_attributes():
        value = getattr(obj, attr)
        pickle.dump(value, f)

def file_to_obj(f, obj):
    for attr in obj.get_saved_attributes():
        value = pickle.load(f)
        setattr(obj, attr, value)

def to_file(me, fn):
    print("Saving map to", fn)
    tmp_name = me.map_initializer.name
    me.map_initializer.name = fn.replace("_", " ")
    with open(fn, "wb") as f:
        obj_to_file(me.map_initializer, f) #store map properties
        #save modified cells
        print("dumping", len(me.modified_cells), "modified cells")
        pickle.dump(len(me.modified_cells), f) #len(modified cells)
        for x,y in me.modified_cells:
            cell = me.lm.cells[x][y]
            pickle.dump((x,y),f)
            pickle.dump(cell.name,f) #cell name
        #save modified objects
        print("dumping", len(me.dynamic_objects), "dynamic objects")
        pickle.dump(len(me.dynamic_objects), f) #len(dynamic_objects)
        for obj in me.dynamic_objects:
            pickle.dump(obj.get_cell_coord(), f) #coord
            obj_to_file(obj, f) #dyn obj
    me.map_initializer.name = tmp_name



def from_file_base(f):
    """Load map properties and re-generate the map"""
    from editor.mapbuilding import MapInitializer
    print("Loading map")
    mi = MapInitializer("")
    file_to_obj(f, mi)
    me = mi.configure_map_editor()
    return me

def from_file_cells(f, me):
    """Load cells and their logical content (names, properties, etc.)"""
    print("Loading cells")
    n = pickle.load(f) #len(modified cells)
    for i in range(n):
        x,y = pickle.load(f) #coord
        name = pickle.load(f) #name
        #
        me.lm.cells[x][y].set_name(name)

def from_file_units(f, me):
    """Load units and their logical content (names, properties, etc.)"""
    print("Loading units")
    n = pickle.load(f) #len(dynamic_objects)
    for i in range(n):
        coord = pickle.load(f) #coord
        a = {}
        for attr_name in MapObject.get_saved_attributes():
            a[attr_name] = pickle.load(f)
        #
        print("*** Loading unit", a["name"])
        print(a)
        obj = MapObject(me, fns=a["fns"], name=a["name"], factor=a["factor"],
                        relpos=a["relpos"], build=a["build"], new_type=a["new_type"])
        obj.set_frame_refresh_type(obj._refresh_frame_type)
        obj_added = me.add_unit(coord, obj, a["quantity"])
