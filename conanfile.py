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
    def __init__(self, deps_cpp_info):
        self.includedirs = deps_cpp_info.include_paths
        self.libdirs = deps_cpp_info.lib_paths
        self.links = deps_cpp_info.libs

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

    def build_property(self, name, values, paths=False):
        lines = []
        if values:
            lines.append(name + "{")
            for value in values:
                if paths:
                    value = normpath(value).replace("\\", "/")
                lines.append('    "%s",' % value)
            lines.append("}")
        return lines

    def build_conan_module(self, deps):

        lines = []
        lines += self.build_property("includedirs", deps.includedirs, True)
        lines += self.build_property("libdirs", deps.libdirs, True)
        lines += self.build_property("links", deps.links)

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
    name = "PremakeGen"
    version = "0.1"
    url = "https://gitlab.dandielo.net/dandielo/premake5-conan"
    license = "MIT"
