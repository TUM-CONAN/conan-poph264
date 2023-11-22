#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from conan import ConanFile
from conan.tools.apple import XcodeDeps, XcodeToolchain, XcodeBuild
from conan.tools.microsoft import MSBuildDeps, MSBuildToolchain, MSBuild, vs_layout
from conan.tools.scm import Git
from conan.tools.files import load, update_conandata, copy, collect_libs, replace_in_file, get
from conan.tools.layout import basic_layout
import os


class poph264Conan(ConanFile):

    name = "poph264"
    _version = "1.9.2"
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
        "shared": True,
        "fPIC": False
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
        elif self.settings.os == "Windows" or self.settings.os == "WindowsStore":
            tc = MSBuildToolchain(self)
            tc.generate()

            deps = MSBuildDeps(self)
            deps.generate()
        else:
            raise ValueError("OS not yet supported")

    def layout(self):
        if self.settings.os == "Macos" or self.settings.os == "iOS":
            basic_layout(self, src_folder="source_folder")
        elif self.settings.os == "Windows" or self.settings.os == "WindowsStore":
            vs_layout(self)

    def build(self):
        if self.settings.os == "Macos" or self.settings.os == "iOS":
            xcodebuild = XcodeBuild(self)
            xcodebuild.build(os.path.join(self.source_folder, "PopH264.xcodeproj"), target="PopH264_Universal")
        elif self.settings.os == "Windows":
            msbuild = MSBuild(self)
            if not self.options.shared:
                msbuild.build_type = "Static"  # @todo: this is always debug win ~20mb ?
            msbuild.build(os.path.join(self.source_folder, "PopH264.visualstudio", "PopH264.sln"), targets=["PopH264"])
        elif self.settings.os == "WindowsStore":
            msbuild = MSBuild(self)
            if self.settings.arch == "armv8":
                msbuild.platform = '"ARM64 Uwp"'
            msbuild.build(os.path.join(self.source_folder, "PopH264.visualstudio", "PopH264.sln"), targets=["PopH264_Uwp"])
        else:
            raise ValueError("OS not yet supported")

    def package(self):
        if self.settings.os == "Macos" or self.settings.os == "iOS":
            base_path = os.path.join(self.source_folder, "build", str(self.settings.build_type), "PopH264.xcframework")
            copy(self, "PopH264.h", os.path.join(self.source_folder, "Source"), os.path.join(self.package_folder, "include"), keep_path=False)
            copy(self, "*", base_path, os.path.join(self.package_folder, "lib", "PopH264.xcframework"))
        elif self.settings.os == "Windows":
            base_path = os.path.join(self.source_folder, "PopH264.visualstudio", "x64", str(self.settings.build_type))
            copy(self, "PopH264.h", base_path, os.path.join(self.package_folder, "include"))
            copy(self, "*.dll", base_path, os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", base_path, os.path.join(self.package_folder, "lib"))
        elif self.settings.os == "WindowsStore":
            base_path = os.path.join(self.source_folder, "PopH264.visualstudio", "ARM64", str(self.settings.build_type), "PopH264.Uwp")
            copy(self, "PopH264.h", base_path, os.path.join(self.package_folder, "include"))
            copy(self, "*.dll", base_path, os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", base_path, os.path.join(self.package_folder, "lib"))
        else:
            raise ValueError("OS not yet supported")

    def package_info(self):
        self.cpp_info.name = "PopH264"
        if self.settings.os == "Macos" or self.settings.os == "iOS":
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
        elif self.settings.os == "Windows":
            self.cpp_info.components["Api"].includedirs = [os.path.join(self.package_folder, "include")]
            self.cpp_info.components["Api"].libs = ["PopH264"]
        elif self.settings.os == "WindowsStore":
            self.cpp_info.components["Api"].includedirs = [os.path.join(self.package_folder, "include")]
            self.cpp_info.components["Api"].libs = ["PopH264.Uwp"]
        else:
            self.cpp_info.libs = collect_libs(self)
