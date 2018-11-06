# Conan Premake5 generator
A conan generator for the premake5 tool. 

# Using this module 
To use this conan generator first you need to clone or download it and create a package localy.
```
cd {path_to_this_repo_localy}
conan create . premake-generator/0.2@dandielo/stable
```

After that just add to your projects `conanfile.txt` the following lines:
```
[generators]
premake-generator/0.2@dandielo/stable
```

This will create a file named `conna.lua` when issuing the `conan install .` command.
In premake you just require the generated file to start using conan libraries in premake5 generated projects.
```lua
require "conan"
-- ...
```

# How to use libraries with this generator
The general idea behind this generator is to serve all available conan libraries independently.
That means you dont have a single `conan_libdirs` option to be used in a premake5 project or workspace but you get a `conan` function which can be seen like the `links` property of premake5.

The `conan` function takes a table of libraries to be `imported` in the given scope for example:
```
require "conan"

-- Every workspace will use includedirs, libdirs and libs from zlib.
conan { "zlib" }

workspace "MyWorkspace" 
  -- Every project in 'MyWorkspace' will use additionaly the `lua` package.
  conan { "lua" }
  
  -- Project JSON will also use `rapidjson` package.
  project "JSON"
    conan { "rapidjson" }
```

Note: The `conan` function clears filters and resets to the project scope always. 
```
project "TestProject" 
  filter "Debug"
    symbols "On"
    
    -- The filter will be ignored here
    conan { "lua" }
    -- We are back in the project scope, not the 'filter:Debug' scope!
```

## Debug and Release libraries 
The option to use `debug` instead `release` library versions is to set a `conan-debug` tag for the given configurations.

```
require "conan"

filter "Debug or SomeOtherConfigName"
  tags { "conan-debug" }
```
