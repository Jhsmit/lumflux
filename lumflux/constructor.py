from __future__ import annotations

import collections
from typing import Any, Optional, Type

from lumflux.controllers import ControlPanel
from lumflux.support import gen_subclasses
from lumflux.main_controllers import MainController
from lumflux.opts import OptsBase
from lumflux.sources import *
from lumflux.tools import supported_tools
from lumflux.transforms import *
from lumflux.views import View
from lumflux.cache import Cache

element_count = 0


class AppConstructor(param.Parameterized):

    errors = param.Selector(
        default='raise',
        objects=['raise', 'warn', 'ignore'],
        doc="Set error handling behaviour"
    )

    sources = param.Dict(
        default={},
        doc="Dictionary with resolved Source objects",
    )

    transforms = param.Dict(
        default={},
        doc="Dictionary with resolved Transform objects",
    )

    opts = param.Dict(
        default={},
        doc="Dictionary with resolved Opts objects",
    )

    tools = param.Dict(
        default={},
        doc="Dictionary with resolved Tools objects",
    )

    views = param.Dict(
        default={},
        doc="Dictionary with resolved Tools objects"
    )

    loggers = param.Dict(
        default={},
        doc="Dictionary with resolved Logger objects"
    )

    ctrl_class = param.ClassSelector(
        class_=MainController,
        instantiate=False,
        doc="Type of main controller to use for the application"
    )

    cache = param.ClassSelector(
        default=Cache(),
        class_=Cache,
        doc="Type of Cache object to use for the application"
    )

    def __init__(self, **params):
        super().__init__(**params)
        self.classes = self.find_classes(duplicates=self.errors)

    def parse(self, app_spec: dict, **kwargs) -> MainController:
        self._parse_sections(app_spec)
        for name, dic in app_spec.get("modules", {}).items():
            self._parse_sections(dic)

        if isinstance(app_spec["controllers"], list):
            control_panel_spec = {_type: {"type": _type} for _type in app_spec["controllers"]}
        else:
            control_panel_spec = app_spec["controllers"]

        control_panels: list[tuple[Type[ControlPanel]], dict] = []
        for name, spec in control_panel_spec.items():
            spec["name"] = name
            klass = self._resolve_class(spec.pop("type"), "controller")
            control_panels.append((klass, spec))


        main_ctrl_spec = app_spec["main_controller"]
        main_ctrl_class = self._resolve_class(main_ctrl_spec.pop("type"), "main")
        ctrl = main_ctrl_class(
            control_panels,
            sources=self.sources,
            transforms=self.transforms,
            opts=self.opts,
            views=self.views,
            loggers=self.loggers,
            **kwargs,
            **main_ctrl_spec,
        )

        return ctrl

    @staticmethod
    def find_classes(duplicates: Optional[str] = 'raise') -> dict[str, dict[str: Any]]:  # Todo base class for everything
        """Returns a nested dict with implementations of all lumflux element types

        # todo define nomenclature ('types'?
        Keys in the dict are the main types ('main', 'transform', 'source', etc), values
        are subdicts of {_type: cls}

        """
        base_classes = {
            "main": MainController,
            "transform": Transform,
            "source": Source,
            "view": View,
            "opt": OptsBase,
            "controller": ControlPanel,
        }
        classes = {}
        for key, base_cls in base_classes.items():
            all_classes = list(
                [cls for cls in gen_subclasses(base_cls) if getattr(cls, "_type", None)]
            )
            all_classes.append(base_cls)

            class_dict = {}
            for cls in all_classes:
                if cls._type in class_dict:
                    message = \
                        f"Multiple implementations of {cls._type!r} found with the same type:"\
                        f"current: {cls}, existing: {class_dict[cls._type]}"
                    if duplicates == 'raise':
                        raise ValueError(message)
                    elif duplicates == 'warn':
                        warnings.warn(message)
                    elif duplicates == 'ignore':
                        pass
                    else:
                        raise ValueError(f"Invalid value for 'duplicates': {duplicates}")
                class_dict[cls._type] = cls

            classes[key] = class_dict

        classes["tool"] = supported_tools

        return classes

    def _parse_sections(self, app_spec: dict):
        sections = ["sources", "transforms", "tools", "opts", "views"]
        for section in sections:
            element = section[:-1]
            element_dict = getattr(self, element + "s")

            d = app_spec.get(section, {})
            for name, spec in d.items():
                if name in element_dict:
                    raise ValueError(
                        f"The element {element!r} with name {name!r} already exists"
                    )
                # todo move to classmethod on object which checks spec/kwargs  (also prevents logger from needing a source)
                if "type" not in spec:
                    raise KeyError(
                        f"The field 'type' is not specified for {section[:-1]} {name!r}"
                    )
                # _type = spec.pop('type')
                if section in ["transforms", "views"] and "source" not in spec:
                    # raise KeyError(f"The field 'source' is not specified for {section[:-1]} {name!r}")
                    print(
                        f"The field 'source' is not specified for {section[:-1]} {name!r}"
                    )
                obj = self.create_element(name, element, **spec)
                element_dict[name] = obj

    def create_element(self, name: str, element: str, **spec):
        """

        :param name:
        :param element: eiter source, filter, opt, view, tool
        :param spec:
        :return:
        """
        global element_count

        _type = spec.pop("type")
        kwargs = self._resolve_kwargs(**spec)
        class_ = self._resolve_class(_type, element)
        if element == "transform":
            kwargs["_cache"] = self.cache
        obj = class_(name=name, **kwargs)
        element_count += 1

        return obj
        #

    def _resolve_class(self, _type, cls):
        return self.classes[cls][_type]

    def _resolve_kwargs(self, **kwargs):
        global element_count

        resolved = {}
        for k, v in kwargs.items():
            if k == "source":
                # temporary:
                if v is None:
                    resolved[k] = v
                else:
                    # obj = self.sources.get(v) or self.transforms.get(
                    #     v
                    # )  # can be none in case of logging

                    if v in self.sources:
                        obj = self.sources[v]
                    elif v in self.transforms:
                        obj = self.transforms[v]
                    else:
                        obj = None


                    resolved[k] = obj
            elif k == "sources":
                # v should be a dict: src_type (view spec): src_name
                sources = {}
                for src_type, src in v.items():
                    obj = self.sources.get(src) or self.transforms.get(src)
                    sources[src_type] = obj
                # obj = {src_type: self.sources[src] for src_type, src in v.items()}
                resolved[k] = sources
            elif k == "opts":
                v = (
                    [v] if isinstance(v, (str, dict)) else v
                )  # allow single opt by str/dict (needs testing)
                opts = []
                for vi in v:
                    if isinstance(vi, dict):  # in situ opt declaration
                        if len(vi) != 1:
                            raise ValueError("Opts ")
                        name = next(iter(vi))  # get the first key
                        obj = self.create_element(
                            f"{name}_{element_count:05d}", "opt", **vi[name]
                        )  # should these in situ opts be added to global opts? probably not or they should have nested names
                        opts.append(obj)
                    else:
                        opts.append(self.opts[vi])

                resolved[k] = opts  # [self.opts[vi] for vi in v]
            elif k == "views":
                v = [v] if isinstance(v, str) else v  # allow single view by str
                resolved[k] = [self.views[vi] for vi in v]
            elif k == "tools":
                v = [v] if isinstance(v, str) else v  # allow single tool by str
                resolved[k] = [self.tools[vi] for vi in v]
            elif (
                k == "dependencies"
            ):  # dependencies are opts/transforms/controllers? (anything with .updated event)
                all_objects = []
                for type_, obj_list in v.items():
                    for obj in obj_list:
                        all_objects.append(getattr(self, type_)[obj])
                resolved[k] = all_objects
            elif k == "logger":
                resolved[k] = self.loggers[v]
            elif k == "tooltips":
                # workaround for pyyaml not reading tuples directly
                resolved[k] = [tuple(item) for item in v]

            else:
                resolved[k] = v

        return resolved
