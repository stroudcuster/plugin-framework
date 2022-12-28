.. plugin-framework documentation master file, created by
   sphinx-quickstart on Tue Dec 27 14:23:32 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to plugin-framework's documentation!
============================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   LICENSE
   api

================
Plugin Framework
================
The intent of this project is to provide an interface between primary Python applications and plugins that extend the functionality
of the primary application.  It addresses these issues that arise when attempting in implement an ability to accept
plugin extension in an application:

+ How to integrate the primary application and the plugin package without resorting to automated or user run post-install scripts
+ How to make the plugin packages entry points known the primary application
+ In the case of desktop GUI applications, how to integrate access to the plugin functionality into the GUI menu structure

The central piece of this framework is a hierarchy of classes that contains the following information about the plugin package:

+ Descriptive information; name, description, author, email address, version
+ A menu/menu item hierarchy that provides the information necessary to build a GUI menu structure and establish the entry points for the various plugin features

Instances of this class hierarchy (PluginSpec/PluginMenu/PluginMenuItem) are serialized to JSON format files which are discovered and
digested by the primary application. In this framework, the primary application is referred to as the plugin host and the extension package as the plugin source.
The codebase consists of three packages;

+ plugin_common which contains the object model, JSON encode/decode function and some utilities that are employed in the process of dynamically integrating the plugin host and source.
+ plugin_source which provides entry points that implement the source side of the discovery process
+ plugin_host which provides discovery  plugin_source package entry points and installation and update of the PluginSpec JSON files

The discovery process uses the importlib_metadata library functions to discovery the plugin entry points declared in the plugin package's
pyproject.toml file.  See the example file in the project's root directory.  Entry points specified in this way can not accept any arguments,
which makes that unsuitable for implementing the plugin's core functionality, but does not prevent them from providing information about the plugin
packages functionality.  Currently the following entry points are provided by the plugin_source.interface.

+ get_help_docs_uri - returns a uri pointing to the plugin package's HTML format help documentation
+ get_version - returns the current plugin package version, drawn from the project's pyproject.toml file
+ get_plugin_spec - returns the PluginSpec/PluginMenu/PluginMenuItem hierarchy for the plugin package.

On the plugin host side of things, the installation of a discovered plugin is implemented by serializing the PluginSpec hierarchy
to a JSON file and saving it in a directory known the host application.  Each time the host application is started,
the plugin_host/discovery model repeats the discovery process, and retrieves the help doc uri and version for each package
discovered.  It then retrieves the PluginSpec objects for each plugin that is not currently installed, or has a more recent
version than the installed plugin.  At this point you can allow the user to select which plugins should be installed, updated
or removed from the installed list.  The module also provides methods to carry out these actions.

Each PluginMenu object specifies a menu title and a module path that will provide the functionality for the menu's items.
Each PluginMenuItem object specifies a menu item title and a function entry point within the module specified in the parent
PluginMenu.  In the current state of the framework, these function cannot be bound functions, as I could find no simple
way to provide the host application access to objects instantiated by the plugin source package.  If necessary, an entry
point that returns the required object or class could be added to the plugin_source.interface module.  It is up to the
host application to establish on or more interfaces to be applied to the menu item entry points.  There is currently
no provision in the PluginSpec hierarchy for specifying this sort of information, but a de facto standard to be implemented
by menu item entry points could be established by the host application authors.

I have a related project called Plugin Manager that provides a tree-structured GUI to allow developers to create, maintain
and serialize PluginSpec objects.

The plugin_host.discovery module provides a create_menus method that invokes a corresponding method in each of the menus
declared for each installed plugin.  These methods accept two callback routines; one to create a GUI menu object and one
to attach a GUI menu item to a parent menu.  This dependency injection allows the framework to be easily adapted to
different GUI frameworks.

This framework is still very much a work in progress.  I developed it so that I could add plugin capability to my
Biometrics Tracker application.  One of the advantage of implementing ancillary functions as plugin is that this
can reduce the number of dependencies in the host application, as opposed to implementing all of the functionality
directly in the host application.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
