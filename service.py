from time import sleep
from jnius import autoclass
from android.config import ACTIVITY_CLASS_NAME  # noqa: F401 - kept for clarity

PythonService = autoclass("org.kivy.android.PythonService")
service = PythonService.mService

Context = autoclass("android.content.Context")
Build_VERSION = autoclass("android.os.Build$VERSION")
NotificationManager = autoclass("android.app.NotificationManager")
NotificationChannel = autoclass("android.app.NotificationChannel")
NotificationBuilder = autoclass("android.app.Notification$Builder")
PowerManager = autoclass("android.os.PowerManager")
ServiceInfo = autoclass("android.content.pm.ServiceInfo")

CHANNEL_ID = "echo_exocortex_channel"
NOTIF_ID = 1001


def _ensure_channel(nm):
    if Build_VERSION.SDK_INT >= 26:
        importance = NotificationManager.IMPORTANCE_LOW
        channel = NotificationChannel(CHANNEL_ID, "Echo V4.0 Listener", importance)
        nm.createNotificationChannel(channel)


def _build_notification():
    nm = service.getSystemService(Context.NOTIFICATION_SERVICE)
    _ensure_channel(nm)

    if Build_VERSION.SDK_INT >= 26:
        builder = NotificationBuilder(service, CHANNEL_ID)
    else:
        builder = NotificationBuilder(service)

    notif = (
        builder.setContentTitle("Echo V4.0")
        .setContentText("Exocortex is listening...")
        .setSmallIcon(service.getApplicationInfo().icon)
        .setOngoing(True)
        .build()
    )
    return notif


def _start_foreground():
    notif = _build_notification()

    # API 29+ supports service type; required on Android 14 for mic
    if Build_VERSION.SDK_INT >= 29:
        service.startForeground(
            NOTIF_ID,
            notif,
            ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE,
        )
    else:
        service.startForeground(NOTIF_ID, notif)


def _acquire_wakelock():
    pm = service.getSystemService(Context.POWER_SERVICE)
    wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "EchoV4:MicLock")
    wl.acquire()
    return wl


if __name__ == "__main__":
    _start_foreground()
    wakelock = _acquire_wakelock()

    # Keep service alive; insert lightweight supervision here if desired
    while True:
        sleep(1)
