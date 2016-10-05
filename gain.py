# -*- coding: utf-8 -*-
# @author zig(remember1637@gmail.com)

import sys
import types
import marshal
import requests
try:
    import czipfile as zipfile
except ImportError:
    import zipfile
try:
    import cStringIO.StringIO as StringIO
except ImportError:
    try:
        import StringIO.StringIO as StringIO
    except ImportError:
        from io import BytesIO as StringIO

__we_are_debuging__ = False

# the module's identifier, use it to hotfix
__i_am_pygain_module__ = "__i_am_pygain_module__"


class __Importer__(object):
    def __init__(self):
        self.__i_am_pygain_importer__ = "__i_am_pygain_importer__"
        self.__specs__ = {}
        self.__packs__ = {}

        self.aliases = {}

    def find_spec(self, name, fullpath, mod=None):
        """

        :param name:
        :param fullpath: package path, None when top-level
        :param mod: passed when reload
        :return:
        """
        class Spec(object):
            def __init__(self, name, loader):
                # __xxx__ assign to module
                self.name = name  # __name__ A string for the fully-qualified name of the module.
                self.loader = loader  # __loader__ The loader to use for loading. For namespace packages this should be set to None.
                self.origin = None  # __file__ Name of the place from which the module is loaded,
                                    # e.g. “builtin” for built-in modules and the filename for modules loaded from source.
                                    # Normally “origin” should be set, but it may be None (the default) which indicates it is unspecified.
                self.submodule_search_locations = None  # __path__ List of strings for where to find submodules, if a package (None otherwise).
                self.cached = None  # __cached__ String for where the compiled module should be stored (or None).
                self.has_location = True  # Boolean indicating whether or not the module’s “origin” attribute refers to a loadable location.
                # for python 2.7
                self.load_module = loader.load_module
        # check whether the module's name starts with a alias
        for alias in self.aliases:
            if name.startswith(alias):
                if __we_are_debuging__:
                    print("|-got spec for name:", name, "fullpath:", fullpath)
                spec = Spec(name, self)
                self.__specs__[name] = spec
                return spec
        else:
            return None

    def find_module(self, name, fullpath):
        """
        deprecated from 3.4, use find_spec instead
        :param name:
        :param fullpath: package path, None when top-level
        :return:
        """
        return self.find_spec(name, fullpath)

    def create_module(self, spec):
        if __we_are_debuging__:
            print("|-create module for spec:", spec)
        module = types.ModuleType(spec.name)
        # init module attributes
        module.__name__ = spec.name
        module.__loader__ = getattr(spec, "loader", None)
        module.__package__ = getattr(spec, "parent", None)
        module.__spec__ = spec
        module.__path__ = spec.submodule_search_locations
        module.__file__ = spec.origin
        module.__cached__ = spec.cached
        if __we_are_debuging__:
            print("|-created module:", module)
        return module

    def exec_module(self, module):
        if __we_are_debuging__:
            print("|-exec module for module:", module)
        spec = module.__spec__
        name = spec.name

        # parent module
        nameparts = name.split(".")
        aliasctx = self.aliases[nameparts[0]]
        if len(nameparts) > 1:
            pname = ".".join(nameparts[:-1])
            pmodule = sys.modules[pname]
            purl = pmodule.__path__[0]
        else:  # this must be a alias package
            purl = aliasctx["baseurl"]
        urlhead = purl + "/" + nameparts[-1]
        if __we_are_debuging__:
            print("|-", name, "'s urlhead:", urlhead)

        # # import alias.a
        suffixes = aliasctx["suffixes"]
        # do i have a parent container(zip)?
        # # import alias.a.b
        for namei in range(1, len(nameparts)):
            packname = ".".join(nameparts[0:namei])  # container's name  ## alias
            if packname in self.__packs__:  # this is my parent container
                pack = self.__packs__[packname]
                # search in this container
                for suffix in suffixes:
                    path = "/".join(nameparts[namei:]) + "." + suffix  ## b.zip; b.py
                    # # (/a.zip exists, b.zip/b.py...)
                    contentfile = self._fetch_file_from_pack(path, pack["zip"], pack["kwargs"])
                    if contentfile is not None:
                        # zip pack, eval __init__
                        if suffix == "zip":  # # /b.zip, execute a.zip/b.zip/__init__.py
                            zippack = {"zip": zipfile.ZipFile(contentfile), "kwargs": aliasctx["kwargs"]}
                            self.__packs__[name] = zippack
                            for initsuffix in suffixes:
                                if initsuffix != "zip":
                                    initpath = "__init__." + initsuffix
                                    initcontentfile = self._fetch_file_from_pack(initpath, zippack["zip"], zippack["kwargs"])
                                    if initcontentfile is not None:
                                        # a package
                                        module.__file__ = urlhead + "." + suffix
                                        module.__path__ = [urlhead + "." + suffix]
                                        self._exec_module(initcontentfile.read(), module)
                                        sys.modules[name] = module
                                        return module
                        else:
                            # just a module
                            module.__file__ = urlhead + "." + suffix
                            delattr(module, "__path__")
                            self._exec_module(contentfile.read(), module)
                            sys.modules[name] = module
                            return module
                # # (/a.zip/b/__init__.py), b is a directory
                else:  # try __init__
                    for initsuffix in suffixes:
                        if initsuffix != "zip":
                            initpath = "/".join(nameparts[namei:]) + "/__init__." + initsuffix  ## b/__init__.py
                            initcontentfile = self._fetch_file_from_pack(initpath, pack["zip"], pack["kwargs"])
                            if initcontentfile is not None:
                                # a package
                                module.__file__ = urlhead + "/__init__." + initsuffix
                                module.__path__ = [urlhead]
                                self._exec_module(initcontentfile.read(), module)
                                sys.modules[name] = module
                                return module

        # search in remote
        # # import alias
        for suffix in suffixes:
            url = urlhead + "." + suffix
            content = self._fetch_file_from_remote(url, aliasctx.get("kwargs", {}))
            if content is not None:
                # zip pack, eval __init__
                if suffix == "zip":  ## /a.zip, execute a.zip/__init__.py
                    zippack = {"zip": zipfile.ZipFile(StringIO(content)), "kwargs": aliasctx["kwargs"]}
                    self.__packs__[name] = zippack
                    for initsuffix in suffixes:
                        if initsuffix != "zip":
                            initpath = "__init__." + initsuffix
                            initcontentfile = self._fetch_file_from_pack(initpath, zippack["zip"], zippack["kwargs"])
                            if initcontentfile is not None:
                                # a package
                                module.__file__ = urlhead + "." + suffix + "/__init__." + initsuffix
                                module.__path__ = [urlhead + "." + suffix]
                                self._exec_module(initcontentfile.read(), module)
                                sys.modules[name] = module
                                return module
                else:  # just a module
                    module.__file__ = url
                    delattr(module, "__path__")
                    self._exec_module(content, module)
                    sys.modules[name] = module
                    return module
        # # import alias.b
        # # remote /a.zip
        # #        /b/__init__.py
        # try __init__
        for initsuffix in suffixes:
            if initsuffix != "zip":
                initurl = urlhead + "/__init__." + initsuffix
                initcontent = self._fetch_file_from_remote(initurl, aliasctx.get("kwargs", {}))
                if initcontent is not None:
                    # a package
                    module.__file__ = initurl
                    module.__path__ = [urlhead]
                    self._exec_module(initcontent, module)
                    sys.modules[name] = module
                    return module

        raise ImportError

    def load_module(self, name):
        """
        deprecated from 3.4, use create_module&exec_module instead
        :param name:
        :return:
        """
        if __we_are_debuging__:
            print("|-load module for name:", name)
        ret = self.exec_module(self.create_module(self.__specs__[name]))
        del self.__specs__[name]
        return ret

    def _exec_module(self, content, module):
        # we support exec py/pyjet
        if module.__file__.endswith("pyjet"):
            co = marshal.loads(content)
        elif module.__file__.endswith("py"):
            co = compile(content, module.__file__, "exec")
        else:
            raise ValueError("unsupported module filename suffix:", module.__file__)
        exec(co, module.__dict__)

    def _fetch_file_from_pack(self, path, packfile, packctx):
        zippw = packctx.get("zippw", None)
        if __we_are_debuging__:
            print("|-fetch file from pack, path:", path, "zippw:", zippw)
        try:
            return packfile.open(path, "r", zippw.encode() if zippw else None)
        except KeyError:
            return None
        except TypeError:
            try:
                return packfile.open(path, "r", zippw)
            except KeyError:
                return None

    def _fetch_file_from_remote(self, url, kwargs):
        if __we_are_debuging__:
            print("|-fetch file from remote url:", url)
        trytimes = kwargs.get("__trytimes__", 1)
        httpheaders = kwargs.get("httpheaders", None)
        try:
            r = requests.get(url, headers=httpheaders)
            if r.status_code == 200:
                return r.content
            else:
                if __we_are_debuging__:
                    print("|-get ", url, " failed,ec:", r.status_code)
        except (TypeError, TimeoutError) as e:
            if trytimes < 5:
                kwargs["__trytimes__"] = trytimes + 1
                return self._fetch_file_from_remote(url, kwargs)
            else:
                raise e
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

__importer__ = __Importer__()


def gain(alias, baseurl, suffixes, **kwargs):
    """
    :param alias: the import instruction's package name
    :param baseurl: the alias's base url
    :param suffixes: supported suffixed
    :param kwargs: keyword arguments
                    zip package password: zippw(password)
                    http headers: httpheaders
    :return: None
    """
    if __we_are_debuging__ is True:
        print("gain - alias:", alias, "|baseurl:", baseurl, "|suffixes:", suffixes, "|kwargs:", kwargs)
    aliases = __importer__.aliases
    if alias in aliases:
        return None
    aliases[alias] = {
        "baseurl": baseurl, "suffixes": suffixes, "kwargs": kwargs
    }

# hotfix
for module in sys.modules:
    if hasattr(module, __i_am_pygain_module__):
        module.gain = gain
for importer in sys.meta_path:
    if hasattr(importer, __importer__.__i_am_pygain_importer__):
        importer.find_spec = __importer__.find_spec
        break
else:  # first time load
    sys.meta_path.append(__importer__)
