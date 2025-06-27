Project management tool. Should contain all the features we need to deploy reliable projects with focus on simplicity.

== Create ==
Create a new project using template.

@todo implement

== Build ==
Order of commands: build.info -> build.replacements -> build.command -> build.includes.

We traverse the whole project, searching for sub-projects - directories with a `project.cfg` inside. Each project is built separately, using the information from the `project.cfg`. The output is stored in directory `build`, with sub-directories according to project names.

For project configuration section `[build]`, this program looks at `command`, for the command to execute in the source directory of the project, and an optional `include` field, which specified which directories to include to the final build. For example, for a Python project, a `project.cfg` may look like this:
%cfg
[main]
name = "my_python_project"

[build]
command = ""
include = "res,src"
%

This layout is used, because Python is an interpreted language, so it needs source scripts to be present in the final build. The resulting tree will look like this:
%tree
build/
  my_python_project/
    res/
      ...
    src/
      ...
    BUILD
%

Builder always create a `BUILD` file for the each project, containing build information in the following format:
%
{version_number: int16}
{build_date_milliseconds: int64}
%

All versioning is done using integer numbers. For all projects, build version is the same - it is specified during calling this program.

For `build.include`, glob paths are not supported for now. Also gitignore is not considered - include directories are copied as they are.

== Dependency ==
@todo implement

== Install ==
Installs current project and it's subprojects using installation directives. Installation is a process of moving the build to the target location, either local or remote, setting up the environment for the invocation, and, optionally, setting up a background service to run.

@todo implement
