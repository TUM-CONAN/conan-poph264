#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from conan import ConanFile
from conan.tools.apple import XcodeDeps, XcodeToolchain, XcodeBuild
from conan.tools.scm import Git
from conan.tools.files import load, update_conandata, copy, collect_libs, replace_in_file, get
from conan.tools.layout import basic_layout
import os


class poph264Conan(ConanFile):

    name = "poph264"
    _version = "1.9.0"
    revision = ""
    version = _version+revision

    license = "Apache-2.0"
    homepage = "http://poph264.com"
    url = "https://github.com/TUM-CONAN/conan-poph264"
    description = "Low-level, minimal H264 decoder & encoder library for windows, hololens/uwp, ios/tvos/macos, linux, android/quest/magic leap. CAPI for use with c#, unreal, swift"
    topics = ("Media", "Codec")

    settings = "os", "compiler", "build_type", "arch"
    options = {
         "shared": [True, False],
         "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    def export(self):
        update_conandata(self, {"sources": {
            "commit": "v{}".format(self._version),
            "url": "https://github.com/NewChromantics/PopH264.git"
            }}
            )

    def source(self):
        git = Git(self)
        sources = self.conan_data["sources"]
        git.clone(url=sources["url"], target=self.source_folder, args=["--recursive", ])
        git.checkout(commit=sources["commit"])

    def generate(self):
        if self.settings.os == "Macos" or self.settings.os == "iOS":
            tc = XcodeToolchain(self)
            tc.generate()

            deps = XcodeDeps(self)
            deps.generate()
        else:
            raise ValueError("OS not yet supported")

    def layout(self):
        basic_layout(self, src_folder="source_folder")

    def build(self):
        if self.settings.os == "Macos" or self.settings.os == "iOS":
            xcodebuild = XcodeBuild(self)
            xcodebuild.build(os.path.join(self.source_folder, "PopH264.xcodeproj"), target="PopH264_Universal")
        else:
            raise ValueError("OS not yet supported")

    def package(self):
        copy(self, "PopH264.h", os.path.join(self.source_folder, "source"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Macos" or self.settings.os == "iOS":
            copy(self, "*", os.path.join(self.source_folder, "build", str(self.settings.build_type), "PopH264.xcframework"), os.path.join(self.package_folder, "lib", "PopH264.xcframework"))
        else:
            raise ValueError("OS not yet supported")

    def package_info(self):
        if self.settings.os == "Macos" or self.settings.os == "iOS":
            self.cpp_info.name = "PopH264"
            platform = None
            arch_folder = None
            if self.settings.os == "Macos":
                arch_folder = "macos-arm64_x86_64"
                platform = "Osx"
            elif self.settings.os == "iOS":
                arch_folder = "ios-arm64"
                platform = "Ios"

            framework_path = os.path.join(self.package_folder, "lib", "PopH264.xcframework", arch_folder)
            self.cpp_info.components["Api"].names["cmake_find_package"] = platform
            self.cpp_info.components["Api"].frameworkdirs = [framework_path]
            self.cpp_info.components["Api"].frameworks = ["PopH264_{0}".format(platform)]
        else:
            self.cpp_info.libs = collect_libs(self)
