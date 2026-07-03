[app]
title = Goeckoh
package.name = goeckoh
package.domain = org.goeckoh
source.dir = src
version = 0.1
requirements = python3,kivy,numpy,scipy,sherpa-onnx,plyer,sounddevice

# Assets and models
source.include_exts = py,txt,kv,png,jpg,onnx
android.permissions = RECORD_AUDIO,INTERNET,MODIFY_AUDIO_SETTINGS
android.minapi = 26
android.sdk = 31
orientation = portrait

[buildozer]
log_level = 1
