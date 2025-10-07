# Project
Project management tool. Should contain all the features we need to deploy reliable projects with focus on simplicity.

This software manages project, which are directories with a file named `projectfile` defined, as well as project's modules, defined in directories with a file named `modulefile`. These files contain Yelets Scripting Language code aimed on providing customizable project development services, such as building, code generation, dependency management.


## Commands
Commands are organized in the 2 groups:
1. local to a project: execution of the functions from the `projectfile`: `execute` and `execute-all`
2. universal: helper commands, such as `init`, `status`, `template`, `push`, `module`

### `project init`
Creates a new project using template:
```
project make {project_id} {template:optional}
```

Will create a sub-directory in current working directory named as project name says. Inside, the files will be generated according to a predefined template. Templates are managed by united engine and organized under command `project template ...`, see below.


### `project execute {function_name} {...args}`
Calls specified function of your `projectfile`.

Every executable function can access current args by calling the `args()` function, which returns a dictionary looking like this:
```yelets
{
    positional: [
        "my_directory_1",
        "my_directory_2",
    ],
    keyword: {
        force: null,
        organizer: "advanced",
        limit: 100,
    },
}
```

### `project execute-all {function_name} {...args}`
Executes a function for every project in the stack. The same arguments are passed for each function.


### `project module add {dependency_name} {version: optional, defaults "latest"} {output_directory: optional, default to the original dependency name}`
Adds a dependency to a project.


### `project module install`
Installs/Refreshes all project-specified dependencies. Every dependency is a directory, containing correct `modulefile`.


### `project module upload {module_directory}`
Uploads a dependency to a server, specified in project's `user.cfg`. Dependency version must be unique for a chosen domain and module name, and must not be lower than the latest version of this dependency name for the given domain uploaded. Also, the upload will be blocked if attempted to upload newest version from one, that is lower than the latest uploaded one.

Module file of a dependency may look as follows (`id` and `version` must be defined):
```yelets
id = "python.my_module"
version = "0.4.9"
```

The installed or uploaded dependencies receive a generated file called `modulehash`, which contain a combined hash of the module's contents. If an user changes any module, further `project module install` and `project module upload` calls affecting the module will be rejected until all the unconsistencies are fixed. The changed module can be re-uploaded by calling `project module update -force`.


### `project module install {dependency_directory} [-force]`
Updates a single module, if called in their's directory. This logic is similar that is called for each project's dependency by `project dependency install`. Flag `-force` ensures that full update is made in case of hash-unconsistencies.


### `project status`
Displays information about the current project.


### `project commit`
Commits changes to version control.


### `project push`
Pushes changes to version control.


### `project update`
Updates changes from version control.


### `project template`
Makes use of a templates inside a project.