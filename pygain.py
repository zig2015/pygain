# -*- coding: utf-8 -*-
# @author zig(shawhen2012@hotmail.com)

import sys
import types
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
                print("got spec for name:", name, "fullpath:", fullpath)
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
        print("create module for spec:", spec)
        module = types.ModuleType(spec.name)
        # init module attributes
        module.__name__ = spec.name
        module.__loader__ = getattr(spec, "loader", None)
        module.__package__ = getattr(spec, "parent", None)
        module.__spec__ = spec
        module.__path__ = spec.submodule_search_locations
        module.__file__ = spec.origin
        module.__cached__ = spec.cached
        print("created module:", module)
        return module

    def exec_module(self, module):
        print("exec module for module:", module)
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
        print(name, "'s urlhead:", urlhead)

        ## import alias.a
        suffixes = aliasctx["suffixes"]
        # do i have a parent container(zip)?
        ## import alias.a.b
        for namei in range(1, len(nameparts)):
            packname = ".".join(nameparts[0:namei])  # container's name  ## alias
            if packname in self.__packs__:  # this is my parent container
                pack = self.__packs__[packname]
                # search in this container
                for suffix in suffixes:
                    path = "/".join(nameparts[namei:]) + "." + suffix  ## b.zip; b.py
                    ## (/a.zip exists, b.zip/b.py...)
                    contentfile = self._fetch_file_from_pack(path, pack["zip"], pack["kwargs"])
                    if contentfile is not None:
                        # zip pack, eval __init__
                        if suffix == "zip":  ## /b.zip, execute a.zip/b.zip/__init__.py
                            zippack = {"zip": zipfile.ZipFile(contentfile), "kwargs": aliasctx["kwargs"]}
                            self.__packs__[name] = zippack
                            for initsuffix in suffixes:
                                if initsuffix != "zip":
                                    initpath = "__init__." + initsuffix
                                    initcontentfile = self._fetch_file_from_pack(initpath, zippack["zip"], zippack["kwargs"])
                                    # a package
                                    module.__file__ = urlhead + "." + suffix
                                    module.__path__ = [urlhead + "." + suffix]
                                    exec(initcontentfile.read(), module.__dict__)
                                    sys.modules[name] = module
                                    return module
                        else:
                            # just a module
                            module.__file__ = urlhead + "." + suffix
                            delattr(module, "__path__")
                            exec(contentfile.read(), module.__dict__)
                            sys.modules[name] = module
                            return module
                ## (/a.zip/b/__init__.py), b is a directory
                else:  # try __init__
                    for initsuffix in suffixes:
                        if initsuffix != "zip":
                            initpath = "/".join(nameparts[namei:]) + "/__init__." + initsuffix  ## b/__init__.py
                            initcontentfile = self._fetch_file_from_pack(initpath, pack["zip"], pack["kwargs"])
                            if initcontentfile is not None:
                                # a package
                                module.__file__ = urlhead + "/__init__." + initsuffix
                                module.__path__ = [urlhead]
                                exec(initcontentfile.read(), module.__dict__)
                                sys.modules[name] = module
                                return module

        # search in remote
        ## import alias
        for suffix in suffixes:
            url = urlhead + "." + suffix
            content = self._fetch_file_from_remote(url)
            if content is not None:
                # zip pack, eval __init__
                if suffix == "zip":  ## /a.zip, execute a.zip/__init__.py
                    zippack = {"zip": zipfile.ZipFile(StringIO(content)), "kwargs": aliasctx["kwargs"]}
                    self.__packs__[name] = zippack
                    for initsuffix in suffixes:
                        if initsuffix != "zip":
                            initpath = "__init__." + initsuffix
                            initcontentfile = self._fetch_file_from_pack(initpath, zippack["zip"], zippack["kwargs"])
                            # a package
                            module.__file__ = urlhead + "." + suffix + "/__init__." + initsuffix
                            module.__path__ = [urlhead + "." + suffix]
                            exec(initcontentfile.read(), module.__dict__)
                            sys.modules[name] = module
                            return module
                else:  # just a module
                    module.__file__ = url
                    delattr(module, "__path__")
                    exec(content, module.__dict__)
                    sys.modules[name] = module
                    return module
        ## import alias.b
        ## remote /a.zip
        ##        /b/__init__.py
        # try __init__
        for initsuffix in suffixes:
            if initsuffix != "zip":
                initurl = urlhead + "/__init__." + initsuffix
                initcontent = self._fetch_file_from_remote(initurl)
                if initcontent is not None:
                    # a package
                    module.__file__ = initurl
                    module.__path__ = [urlhead]
                    exec(initcontent, module.__dict__)
                    sys.modules[name] = module
                    return module

        raise ImportError

    def load_module(self, name):
        """
        deprecated from 3.4, use create_module&exec_module instead
        :param name:
        :return:
        """
        print("load module for name:", name)
        ret = self.exec_module(self.create_module(self.__specs__[name]))
        del self.__specs__[name]
        return ret

    def _fetch_file_from_pack(self, path, packfile, packctx):
        try:
            return packfile.open(path, "r", packctx.get("zippw", None))
        except KeyError:
            return None
        except TypeError:
            try:
                return packfile.open(path, "r", packctx.get("zippw", None).encode())
            except KeyError:
                return None

    def _fetch_file_from_remote(self, url):
        print("fetch file from remote url:", url)
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return r.content
            else:
                print("get ", url, " failed,ec:", r.status_code)
        except Exception as e:
            import traceback
            traceback.print_exc()

__importer__ = __Importer__()


def gain(alias, baseurl, suffixes, **kwargs):
    """
    // zh-cn
    :param alias: 用于import时的别名
    :param baseurl: 别名引入的基址url
    :param suffixes: 支持的后缀模式
    :param kwargs: 附加参数,比如zip解压密码等...
                    zip: zippw(password)
    :return: None
    // en-us
    """
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
else: # first time load
    sys.meta_path.append(__importer__)
