from collections import OrderedDict
from contextlib import contextmanager
import requests
import xmltodict


VULKAN_PLATEFORM_URL = ('http://raw.githubusercontent.com/KhronosGroup/'
                        'Vulkan-Docs/1.0/src/vulkan/vk_platform.h')
VULKAN_H_URL = ('http://raw.githubusercontent.com/KhronosGroup/'
                'Vulkan-Docs/1.0/src/vulkan/vulkan.h')
VK_XML_URL = ('http://raw.githubusercontent.com/KhronosGroup/'
              'Vulkan-Docs/1.0/src/spec/vk.xml')
OUT_FILE = 'vulkanmodule.c'

define_header = '''
#include <Python.h>
#include <dlfcn.h>

#define VK_NO_PROTOTYPES

#if defined(ANDROID) || defined (__ANDROID__)
  #define VK_USE_PLATFORM_ANDROID_KHR 1
#elif defined(_WIN32)
  #define VK_USE_PLATFORM_WIN32_KHR 1
#elif defined(__linux__)
  #define VK_USE_PLATFORM_XLIB_KHR 1
#endif

#ifdef __unix__

#define LOAD_SDK() dlopen("libvulkan.so", RTLD_NOW);

#elif defined(_WIN32) || defined(WIN32)

#define LOAD_SDK() LoadLibrary("vulkan-1.dll");
#define dlsym GetProcAddress

#endif
'''


def download_files():
    print("Download files")
    urls = (VULKAN_PLATEFORM_URL, VULKAN_H_URL, VK_XML_URL)
    return [requests.get(url).text for url in urls]


def clean_vulkan_h(vulkan_h):
    cleaned = ""
    for line in vulkan_h.splitlines(True):
        if '#include "vk_platform.h"' not in line:
            cleaned += line

    return cleaned


class Generator():
    def __init__(self):
        f0, f1, f2 = download_files()
        self.vulkan_plateform = f0
        self.vulkan_h = clean_vulkan_h(f1)
        self.vk_xml = xmltodict.parse(f2)
        self.fextensions = self.get_functions_in_extensions()
        self.sextensions = self.get_structs_in_extensions()

    def get_functions_in_extensions(self):
        names = []
        for extension in self.vk_xml['registry']['extensions']['extension']:
            if 'command' not in extension['require']:
                continue
            if type(extension['require']['command']) is not list:
                extension['require']['command'] = [
                    extension['require']['command']]

            for command in extension['require']['command']:
                names.append(command['@name'])
        return names

    def get_structs_in_extensions(self):
        names = []
        for extension in self.vk_xml['registry']['extensions']['extension']:
            if 'type' not in extension['require']:
                continue
            if type(extension['require']['type']) is not list:
                extension['require']['type'] = [
                    extension['require']['type']]

            for struct in extension['require']['type']:
                names.append(struct['@name'])
        return names

    def main(self):
        with open(OUT_FILE, 'w') as vulkanmodule_file:
            self.out = vulkanmodule_file
            self.add_header()
            self.add_vk_plateform()
            self.add_vk_h()
            self.add_functions_definition()
            self.add_initsdk()
            self.add_pyobject()
            self.add_pymethod()
            self.add_pymodule()
            self.add_pyinit()
        self.out = None

    def add_header(self):
        header = define_header
        header += '\n'
        self.out.write(header)

    def add_vk_plateform(self):
        self.out.write("// BEGIN VULKAN PLATEFORM\n")
        self.out.write(self.vulkan_plateform)
        self.out.write("// END VULKAN PLATEFORM\n")

    def add_vk_h(self):
        self.out.write("// BEGIN VULKAN H\n")
        self.out.write(self.vulkan_h)
        self.out.write("// END VULKAN H\n")

    def add_pyinit(self):
        self.out.write("\n\nPyMODINIT_FUNC PyInit_vulkan(void) {\n")
        self.create_module()
        self.add_constants()
        self.add_object_in_init()
        self.out.write("return module;\n}\n")

    def add_object_in_init(self):
        structs = [s for s in self.vk_xml['registry']['types']['type']
                   if s.get('@category', None) == 'struct']

        for struct in structs:
            with self.check_struct_extension(struct):
                self.out.write('''
                    if (PyType_Ready(&Py{0}Type) < 0)
                        return NULL;
                    Py_INCREF(&Py{0}Type);
                    PyModule_AddObject(module, "{0}", (PyObject *)&Py{0}Type);
                '''.format(struct['@name']))

    def add_pyobject(self):
        def add_struct(s):
            definition = '''
                typedef struct {{ PyObject_HEAD {0} *base; }}
                Py{0};
                '''
            self.out.write(definition.format(s['@name']))

        def add_del(s):
            definition = '''
                static void Py{0}_del(Py{0}* self) {{
                    Py_TYPE(self)->tp_free((PyObject*)self); }}
                '''
            self.out.write(definition.format(s['@name']))

        def add_new(s):
            definition = '''
                static PyObject *
                Py{0}_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
                {{
                    Py{0} *self;
                    self = (Py{0} *)type->tp_alloc(type, 0);
                    if (self != NULL) {{
                        self->base = malloc(sizeof({0}));
                        if (self->base == NULL) {{
                            PyErr_SetString(PyExc_MemoryError,
                                "Cannot allocate memory for {0}");
                            return NULL;
                        }}
                    }}

                    return (PyObject *)self;
                }}
                '''
            self.out.write(definition.format(s['@name']))

        def add_setters(s):
            def add_setter(member):
                definition = '''
                static int Py{0}_set{1}(Py{0} *self, PyObject *value,
                                        void *closure) {{
                    if (value == NULL) {{
                        PyErr_SetString(PyExc_TypeError, "Error with {1}");
                        return -1;
                    }}
                '''

                if member['type'] == "uint32_t" and '#text' not in member:
                    definition += '''
                        uint32_t val = (uint32_t) PyLong_AsLong(value);
                        '''
                else:
                    return

                definition += '''
                    (self->base)->{1} = val;
                    return 0;
                }}
                '''
                self.out.write(definition.format(s['@name'], member['name']))

            def add_getter(member):
                definition = '''
                static PyObject * Py{0}_get{1}(Py{0} *self, void *closure){{
                '''

                if member['type'] == "uint32_t" and '#text' not in member:
                    definition += '''
                        PyObject* value = PyLong_FromLong(
                            (long) (self->base)->{1});
                    '''
                else:
                    return

                definition += '''
                    Py_INCREF(value);
                    return value;
                }}
                '''
                self.out.write(definition.format(s['@name'], member['name']))

            def add_getter_setter(s):
                self.out.write('''
                    static PyGetSetDef {}_getsetters[] = {{
                    '''.format(s['@name']))

                for member in s['member']:
                    if member['type'] != "uint32_t" or '#text' in member:
                        continue
                    self.out.write('''
                        {{ "{1}", (getter)Py{0}_get{1},
                           (setter)Py{0}_set{1}, "", NULL}},
                    '''.format(s['@name'], member['name']))

                self.out.write('{NULL}};\n')

            for member in s['member']:
                add_setter(member)
                add_getter(member)
            add_getter_setter(s)

        def add_type(s):
            self.out.write('''
                static PyTypeObject Py{0}Type = {{
                    PyVarObject_HEAD_INIT(NULL, 0)
                    "vulkan.{0}", sizeof(Py{0}), 0,
                    (destructor)Py{0}_del,
                    0,0,0,0,0,0,0,0,0,0,0,0,0,0,Py_TPFLAGS_DEFAULT,
                    "{0} object",0,0,0,0,0,0,0,0,
                    {0}_getsetters,0,0,0,0,0,0,0,Py{0}_new,}};
            '''.format(s['@name']))

        structs = [s for s in self.vk_xml['registry']['types']['type']
                   if s.get('@category', None) == 'struct']

        for struct in structs:
            with self.check_struct_extension(struct):
                for fun in (add_struct, add_del, add_new, add_setters,
                            add_type):
                    fun(struct)

    @contextmanager
    def check_struct_extension(self, struct):
        mapping = {'VkAndroidSurfaceCreateInfoKHR':
                   'VK_USE_PLATFORM_ANDROID_KHR',
                   'VkMirSurfaceCreateInfoKHR':
                   'VK_USE_PLATFORM_MIR_KHR',
                   'VkWaylandSurfaceCreateInfoKHR':
                   'VK_USE_PLATFORM_WAYLAND_KHR',
                   'VkWin32SurfaceCreateInfoKHR':
                   'VK_USE_PLATFORM_WIN32_KHR',
                   'VkXcbSurfaceCreateInfoKHR':
                   'VK_USE_PLATFORM_XCB_KHR',
                   'VkXlibSurfaceCreateInfoKHR':
                   'VK_USE_PLATFORM_XLIB_KHR',
                   'VkRect3D': 'hackdefine'}
        try:
            if struct['@name'] in mapping:
                self.out.write('\n#ifdef {}\n'
                               .format(mapping[struct['@name']]))
            yield
        finally:
            if struct['@name'] in mapping:
                self.out.write('\n#endif\n')

    def add_pymodule(self):
        name = '"vulkan"'
        doc = '"Vulkan module"'
        self.out.write('''
            static struct PyModuleDef vulkanmodule = {{
                PyModuleDef_HEAD_INIT, {}, {}, -1, VulkanMethods}};
            '''.format(name, doc))

    def create_module(self):
        self.out.write('''
            PyObject* module;
            module = PyModule_Create(&vulkanmodule);
            if (module == NULL) return NULL;
        ''')

    def add_functions_definition(self):
        result = []
        commands = [c['proto']['name']
                    for c in self.vk_xml['registry']['commands']['command']]
        commands = [c for c in commands if c not in self.fextensions]

        for command in commands:
            name = command
            name_pfn = 'PFN_{}'.format(name)
            result.append('static {} {};'.format(name_pfn, name))

        self.out.write('\n')
        self.out.write('\n'.join(result))
        self.out.write('\n')

    def add_constants(self):
        result = []

        def add_result(name, value):
            result.append('PyModule_AddIntConstant(module, "{}", {})'.format(
                name, value))

        # List enums
        for enum in self.vk_xml['registry']['enums']:
            name = ""
            value = ""

            # List constant in enum
            if type(enum['enum']) is not list:
                enum['enum'] = [enum['enum']]

            for constant in enum['enum']:
                if '@bitpos' in constant:
                    value = str(int(constant['@bitpos']) + 1).zfill(8)
                    constant['@value'] = '0x{}'.format(value)
                name = constant["@name"]
                value = constant["@value"]
                add_result(name, value)

        text = '\n\n'
        text += ';\n'.join(result)
        text += ';\n'
        self.out.write(text)

    def add_initsdk(self):
        functions = []
        commands = [c['proto']['name']
                    for c in self.vk_xml['registry']['commands']['command']]
        commands = [c for c in commands if c not in self.fextensions]
        for command in commands:
            name = command
            name_pfn = 'PFN_{}'.format(name)
            functions.append('''
                             {0} = ({1})dlsym(vk_sdk, "{0}");
                             if( {0} == NULL ) {{
                                 PyErr_SetString(PyExc_ImportError,
                                                 "Can't load {0} in sdk");
                                 return NULL;
                             }}
                             '''
                             .format(name, name_pfn))

        self.out.write('''
            static PyObject * load_sdk(PyObject *self, PyObject *args) {
                void* vk_sdk = LOAD_SDK();
                if (vk_sdk == NULL) {
                    PyErr_SetString(PyExc_ImportError,
                                    "Can't find vulkan sdk");
                    return NULL;
                }

                '''+'\n'.join(functions)+'''

                Py_INCREF(Py_None);
                return Py_None;
            }
        ''')

    def add_pymethod(self):
        functions = []
        functions.append({'name': '"load_sdk"',
                          'value': 'load_sdk',
                          'arg': 'METH_NOARGS',
                          'doc': '"Load SDK"'})

        self.out.write('\nstatic PyMethodDef VulkanMethods[] = {\n')

        for fun in functions:
            self.out.write('{{{}, {}, {}, {}}},\n'.format(
                fun['name'], fun['value'], fun['arg'], fun['doc']))

        self.out.write('\n{NULL, NULL, 0, NULL} };\n')


if __name__ == '__main__':
    generator = Generator()
    generator.main()
