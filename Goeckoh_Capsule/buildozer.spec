[app]
title = Goeckoh
package.name = goeckoh
package.domain = org.exocortex
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,onnx,txt
version = 1.0.0

requirements = python3,kivy,numpy,sounddevice,sherpa-onnx,jnius,plyer,requests

android.permissions = RECORD_AUDIO,INTERNET,BODY_SENSORS,WRITE_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity

[buildozer]
log_level = 2
warn_on_root = 1
