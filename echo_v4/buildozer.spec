[app]
# (str) Title of your application
title = Echo V4

# (str) Package name
package.name = echov4

# (str) Package domain (needed for android/ios packaging)
package.domain = org.goeckoh.echo

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let buildozer find them)
source.include_exts = py,png,jpg,jpeg,gif,json,kv,ttf,otf,db,npz,txt,md,onnx,gz,bz2

# (str) Application versioning
version = 0.4

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
# Neds to include python3, kivy, and all other dependencies.
# For Android, `pyaudio` needs a special recipe. We use `python-for-android`'s
# pyaudio recipe. `jnius` and `pyobjus` are included by default when targeting android/ios.
requirements = python3,kivy,kivymd,numpy,scipy,pyaudio,torch,torchaudio,sympy,opencv,psutil

# (str) Presplash background color (for new android AAB)
#android.presplash_color = #FFFFFF

# (str) Presplash animation using Lottie format.
# Not used in this spec.
#android.presplash_lottie = "assets/presplash.json"

# (str) Orientation (all | portrait | landscape)
orientation = portrait

# (list) Permissions
android.permissions = RECORD_AUDIO, INTERNET, MODIFY_AUDIO_SETTINGS

# (int) Android API to use
android.api = 31

# (int) Minimum API required
android.minapi = 26

# (int) Android SDK version to use
android.sdk = 24

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android NDK path. If not set, buildozer will download it.
#android.ndk_path =

# (str) Android SDK path. If not set, buildozer will download it.
#android.sdk_path =

# (str) Android build tools version.
#android.build_tools_version = 31.0.0

[buildozer]
# (int) Log level (0 = error, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
