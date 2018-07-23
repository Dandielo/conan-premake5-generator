from conans.model import Generator
from conans import ConanFile
from cStringIO import StringIO
from posixpath import normpath

conan_lua_function = """
local conan_modules = { }
function conan(modules)
    for _, v in ipairs(modules) do
        v = v:lower()
        assert(conan_modules[v], "The given module couldn't be found, have you added it to your conanfile.txt?")
        conan_modules[v]()
    end
end
"""

conan_lua_module = """
conan_modules[('{name}'):lower()] = function()
    {funcs}
end
"""


class PremakeDeps(object):
    def __init__(self, source, base=None):
        def get_unique(name):
            attrib = getattr(source, name, [])
            attrib_base = getattr(base, name, [])

            if base == None:
                return attrib

            if type(attrib) != list:
                return attrib

            return [item for item in attrib if item not in attrib_base]

        self.includedirs = get_unique('include_paths')
        self.libdirs = get_unique('lib_paths')
        self.links = get_unique('libs')

        if base == None:
            if hasattr(source, 'debug'):
                self.debug = PremakeDeps(source.debug, base=source)
            if hasattr(source, 'release'):
                self.release = PremakeDeps(source.release, base=source)

    def has_cpp_info(self):
        return (self.includedirs
            or self.libdirs
            or self.links
        )


class PremakeModule(object):
    def __init__(self, name):
        self.name = name
        self.lines = []

    def append(self, str, indent = False):
        if indent:
            self.lines.append("    %s" % str)
        else:
            self.lines.append("%s" % str)

    def build_property(self, name, values, paths=False, IndentLevel=0):
        indent_prop = ''.join(["    "] * IndentLevel)
        indent_prop_arg = ''.join(["    "] * (IndentLevel + 1))
        lines = []

        if values:
            lines.append("%s%s{" % (indent_prop, name))
            for value in values:
                if paths:
                    value = normpath(value).replace("\\", "/")
                lines.append('%s"%s",' % (indent_prop_arg, value))
            lines.append("%s}" % indent_prop)

        return lines

    def build_property_group(self, deps, filter=None):

        indentation = 0
        if filter != None:
            indentation = 1

        lines = []
        lines += self.build_property("includedirs", deps.includedirs, True, IndentLevel=indentation)
        lines += self.build_property("libdirs", deps.libdirs, True, IndentLevel=indentation)
        lines += self.build_property("links", deps.links)

        if lines and filter != None:
            lines.insert(0, 'filter { "%s" }' % '", "'.join(filter))
            lines.append('filter { "*" }')

        return lines



    def build_conan_module(self, deps):

        lines = []
        lines += self.build_property_group(deps)
        if deps.debug:
            lines += self.build_property_group(deps.debug, [ "Debug" ])
        if deps.release:
            lines += self.build_property_group(deps.release, [ "Release" ])

        if lines:
            funcs = "\n    ".join(lines)
            self.append(conan_lua_module.format(name=self.name, funcs=funcs))
            return True

        return False

    def build(self, deps):
        if self.build_conan_module(deps):
            return '\n'.join(self.lines)
        return ''


class premake(Generator):
    @property
    def filename(self):
        return "conan.lua"

    @property
    def content(self):
        sections = ["# Generated Conan file"]
        sections.append(conan_lua_function)

        # if self.conanfile.name and self.conanfile.version:
        #     deps = PremakeDeps(self.deps_build_info)
        #     module = PremakeModule(self.conanfile.name, self.conanfile.version)
        #     module.build(deps)

        for dep_name, dep_cpp_info in self.deps_build_info.dependencies:
            deps = PremakeDeps(dep_cpp_info)
            if deps.has_cpp_info():
                module = PremakeModule(dep_name)
                sections.append(module.build(deps))

        return "\n".join(sections)

class Premake5GeneratorPackage(ConanFile):
    name = "premake-generator"
    version = "0.1"
    license = "MIT"
    url = "https://gitlab.dandielo.net/dandielo/premake5-conan"
    description = "Premake5 generator for the conan package manager."

    def package(self):
        pass
