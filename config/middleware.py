import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class LogoutOn404Middleware:
    """
    Si una ruta NO existe (404), desloguea y redirige a login,
    PERO solo para navegaciones normales (HTML) y fuera del admin.
    Evita afectar: admin, static/media, favicon, robots, assets, requests AJAX/JSON.
    """

    EXCLUDE_PREFIXES = ("/admin/", "/static/", "/media/")
    EXCLUDE_PATHS = ("/favicon.ico", "/robots.txt", "/sitemap.xml")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code != 404:
            return response

        path = request.path

        # 1) Excluir admin/static/media y archivos típicos
        if path.startswith(self.EXCLUDE_PREFIXES) or path in self.EXCLUDE_PATHS:
            return response

        # 2) Si parece request de recurso (css/js/png/etc), no hagas logout
        #    (esto evita que te desconecte por assets 404)
        lowered = path.lower()
        if lowered.endswith((
            ".css", ".js", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
            ".woff", ".woff2", ".ttf", ".eot", ".webp"
        )):
            return response

        # 3) Si es AJAX / API / JSON, no redirijas (rompe el admin y fetch)
        accept = (request.headers.get("Accept") or "").lower()
        xrw = (request.headers.get("X-Requested-With") or "").lower()
        if "application/json" in accept or xrw == "xmlhttprequest":
            return response

        # 4) Solo actuar cuando el navegador espera HTML
        if "text/html" not in accept and "*/*" not in accept:
            return response

        # 5) Evitar loop si ya está en login
        login_path = reverse("login")
        if path == login_path:
            return response

        logout(request)
        return redirect(login_path)


class IdleTimeoutMiddleware:
    """
    Desloguea al usuario si no ha hecho requests por X segundos.
    Aplica solo a usuarios autenticados.
    """

    EXCLUDE_PREFIXES = ("/admin/", "/static/", "/media/")
    EXCLUDE_PATHS = ("/login/", "/favicon.ico")

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, "SESSION_IDLE_TIMEOUT", 900)

    def __call__(self, request):
        path = request.path

        # excluir rutas críticas
        if path.startswith(self.EXCLUDE_PREFIXES) or path in self.EXCLUDE_PATHS:
            return self.get_response(request)

        if not request.user.is_authenticated:
            return self.get_response(request)

        now = int(time.time())
        last_activity = request.session.get("last_activity")

        if last_activity:
            if now - last_activity > self.timeout:
                logout(request)
                request.session.flush()
                return redirect(reverse("login"))

        # actualizar actividad SOLO en requests HTML reales
        accept = (request.headers.get("Accept") or "").lower()
        if "text/html" in accept or "*/*" in accept:
            request.session["last_activity"] = now

        return self.get_response(request)
