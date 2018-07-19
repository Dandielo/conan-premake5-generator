from conans.model import Generator
from conans import ConanFile

class PremakeDeps(object):
    def __init__(self, deps_cpp_info):
        pass

class Premake(Generator):
    def __init__(self):
        print(self.deps_build_info)
        pass

    @property
    def filename(self):
        return "conan.lua"

    @property
    def content(self):
        pass

class Premake5GeneratorPackage(ConanFile):
    name = "PremakeGen"
    version = "0.1"
    url = "https://gitlab.dandielo.net/dandielo/premake5-conan"
