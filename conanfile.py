from conans.model import Generator
from conans import ConanFile
from cStringIO import StringIO
from posixpath import normpath

conan_lua_function = """
local conan_modules = { }
function conan(modules)
    for _, v in ipairs(modules) do
        v = v:lower()
        assert(conan_modules[v], ("The given module '%s' couldn't be found, have you added it to your conanfile.txt?"):format(v))
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
        self.bindirs = get_unique('bin_paths')
        self.links = get_unique('libs')
        self.defines = get_unique('defines')

        if base == None:
            if hasattr(source, 'debug'):
                self.debug = PremakeDeps(source.debug, base=source)
            if hasattr(source, 'release'):
                self.release = PremakeDeps(source.release, base=source)

    def has_cpp_info(self):
        return (self.includedirs
            or self.libdirs
            or self.defines
            or self.links
            or self.bindirs
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

    def build_commands_property(self, dirs_from, to, command, files="*", stage="", IndentLevel=0):
        indent_prop = ''.join(["    "] * IndentLevel)
        indent_prop_arg = ''.join(["    "] * (IndentLevel + 1))
        lines = []

        if command not in ["copy"]:
            return lines

        # make sure we end the ratget dir with a slash
        to = normpath(to) + "/"

        if dirs_from:
            lines.append("%s%scommands{" % (indent_prop, stage))
            for dir_from in dirs_from:
                dir_from = normpath(dir_from).replace("\\", "/")
                # For the 'copy' command
                if command == "copy":
                    lines.append('%s\'{COPY} "%s/%s" "%s"\',' % (indent_prop_arg, dir_from, files, to))
            lines.append("%s}" % indent_prop)

        return lines


    def build_property_group(self, deps, filter=None):

        indentation = 0
        if filter != None:
            indentation = 1

        lines = []
        lines += self.build_property("includedirs", deps.includedirs, True, IndentLevel=indentation)
        lines += self.build_property("libdirs", deps.libdirs, True, IndentLevel=indentation)
        lines += self.build_property("links", deps.links, False, IndentLevel=indentation)
        lines += self.build_property("defines", deps.defines, False, IndentLevel=indentation)
        lines += self.build_commands_property(deps.bindirs, "%{cfg.targetdir}", "copy", files="*.dll", stage="postbuild", IndentLevel=indentation)

        if lines and filter != None:
            lines.insert(0, 'filter { "tags:%s" }' % '", "'.join(filter))
            lines.append('filter { "*" }')

        return lines



    def build_conan_module(self, deps):

        lines = []
        lines += self.build_property_group(deps)
        if deps.debug:
            lines += self.build_property_group(deps.debug, [ "conan-debug" ])
        if deps.release:
            lines += self.build_property_group(deps.release, [ "not conan-debug" ])

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
    version = "0.2"
    license = "MIT"
    url = "https://gitlab.dandielo.net/dandielo/premake5-conan"
    description = "Premake5 generator for the conan package manager."

    def package(self):
        pass
