# Project
Project management tool. Should contain all the features we need to deploy reliable projects with focus on simplicity.

This software manages project, which are directories with a file named `projectfile` defined, as well as project's modules, defined in directories with a file named `modulefile`. These files contain Yelets Scripting Language code aimed on providing customizable project development services, such as building, code generation, dependency management.

## `project create`
Creates a new project using template:
```
project create {project_name} {template:optional}
```

Will create a sub-directory in current working directory named as project name says. Inside, the files will be generated according to a predefined template. Templates are managed by united engine and organized under command `project template ...`, see below.


## `project execute {function_name} {...args}`
Calls specified function of your `projectfile`. Most common one is `build` function, which, for Python projects, may look as follows:
```yelets
name = "my_project"

build = fn () {
    buildInfo("build.py")
    // collects codes from the master's project root-placed `code.txt` and transforms them into an appropriate format, based on the target file's extension
    buildCode("code.py")

    // includes all python module directories with depth 1, as well as python-must files, such as `requirements.txt` and `main.py`
    buildIncludePython()
}
```

Build function is not just a pattern, it is called during `project build` invocation for each project in the stack. Note that functions `info`, `code`, `include`, `include_python_modules` are part of the build stack and injected by the project software. Each of these functions rely on working with a directory `.build`, placed in the project directory.

Every executable function can access current args by calling the `args()` function, which returns a dictionary looking like this:
```yelets
{
    positional: [
        "my_directory_1",
        "my_directory_2",
    ],
    keyword: {
        "-force": null,
        "-organizer": "advanced",
        "-limit": 100,
    },
}
```

## `project build {version} {-debug: optional, defaults to False}`
Builds this project and all sub-projects recursively, calling `project execute build` for each one of them, and organizing the results. Each build call creates a `.build` directory in the according project locations. Further `project deploy` calls may collect them for project/projects running elsewhere.

Arguments `version` and `debug` are specified for all projects to be built.


## `project deploy`
Calls deploy function for a project, collecting all built subprojects (from the according directories called `build`), and providing an *argument* `deploy`, which contains a dictionary with keys as project names and values as project build directory path.

Typical deploy function, that deploys built python project to remote server's `alex@192.168.0.10:/home/alex/app/my_project` directory:
```yelets
ssh = @import("ssh")
file = @import("file")
tar = @import("tar")
time = @import("time")

name = "my_project"

...

deploy = fn () {
    // helper function that makes a tar file with compression at the `.deploy/deploy.tar.xz`, compression algorithm is based on the target file extension. The tar contains all project builds sorted by in directories.
    deployCollectTar(".deploy/deploy.tar.xz")

    ssh_host = ssh.createHost("user", "192.168.0.10")
    ssh_host.execute("sudo systemctl stop my_project")
    ssh_host.execute(f"mkdir /home/alex/.app/my_project")
    ssh_host.execute(f"cp /home/alex/.app/my_project /home/alex/.backup/my_project_{time.stamp()}")

    ssh_host.copyTo("/home/alex/.app/my_project/deploy.tar.xz", ".deploy/deploy.tar.xz")
    ssh_host.execute("tar -xf /home/alex/.app/my_project/deploy.tar.xz -C /home/alex/.app/my_project/")

    ssh_host.execute("sudo systemctl start my_project")
}
```

Calling `project execute deploy` won't have the necessary effect - the required arguments and setup managed by the project software won't take place, which most probably will result in errors.


## `project dependency add {dependency_name} {version: optional, defaults "latest"} {output_directory: optional, default to the original dependency name}`
Adds a dependency to a project.


## `project dependency install`
Installs all project-specified dependencies. Every dependency is a directory, containing correct `modulefile`.


## `project dependency upload {dependency_directory}`
Uploads a dependency to the server. Dependency version must be unique for a chosen domain and module name, and must not be lower than the latest version of this dependency name for the given domain uploaded.

Module file of a dependency may look as follows (`domain`, `name` and `version` must be defined):
```yelets
domain = "python"
name = "my_module"
version = "0.4.9"
```

The installed or uploaded dependencies receive a generated file called `modulehash`, which contain a combined hash of the module's contents. If an user changes any module, further `project dependency install` and `project dependency upload` calls affecting the module will be rejected until all unconsistencies are fixed. The changed module can be re-uploaded by calling `project dependency update -force`.

## `project dependency update {dependency_directory} [-force]`
Updates a single dependency, if called in their's directory. This logic is similar that is called for each project's dependency by `project dependency install`. Flag `-force` ensures that full update is made in case of hash-unconsistencies.


