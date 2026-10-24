import os
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

import pytest


# Permite probar por HTTP tanto la URL interna de Docker como una instancia local.
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8080").rstrip("/")


class _PageParser(HTMLParser):
    # Extrae el mensaje producido por el controlador, no solo el input que refleja la consulta.
    def __init__(self):
        super().__init__()
        self.messages = []
        self.text = []
        self._inside_message = False

    def handle_starttag(self, tag, attrs):
        if tag == "p" and "mensaje" in dict(attrs).get("class", "").split():
            self._inside_message = True

    def handle_endtag(self, tag):
        if tag == "p" and self._inside_message:
            self.messages.append("".join(self.text).strip())
            self.text.clear()
            self._inside_message = False

    def handle_data(self, data):
        if self._inside_message:
            self.text.append(data)


def _get(path):
    # Se mantienen los codigos HTTP de error para que las aserciones puedan detectarlos.
    request = urllib.request.Request(f"{APP_BASE_URL}{path}")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as response:
        return response.code, response.read()


def _search(value):
    # Codifica signos y espacios para enviar la expresion sin alterarla.
    return _get("/?" + urllib.parse.urlencode({"buscar": value}))


@pytest.fixture(scope="session", autouse=True)
def wait_for_application():
    # Espera el arranque de Spring Boot; si no responde, las pruebas fallan explicitamente.
    deadline = time.monotonic() + 90
    last_error = None

    while time.monotonic() < deadline:
        try:
            status, _ = _get("/")
            if status == 200:
                return
            pytest.fail(
                f"La aplicación respondió HTTP {status} en {APP_BASE_URL}; "
                "se esperaba HTTP 200 en la ruta principal."
            )
        except (OSError, urllib.error.URLError) as exception:
            last_error = str(exception)
        time.sleep(2)

    pytest.fail(
        f"La aplicación no respondió en {APP_BASE_URL} dentro de 90 segundos. "
        f"Último error: {last_error}. Iniciá Ejercicio4 antes de ejecutar pytest."
    )


# Expresiones benignas que detectan evaluacion SpEL sin ejecutar comandos del sistema.
@pytest.mark.parametrize(
    "expression",
    [
        "1 + 1",
        "T(java.lang.Math).sqrt(144)",
    ],
)
def test_spel_like_search_input_is_returned_as_literal_text(expression):
    # El mensaje debe conservar la expresion completa, no su resultado calculado.
    status, body = _search(expression)
    parser = _PageParser()
    parser.feed(body.decode("utf-8"))

    assert status == 200
    assert parser.messages == [f"Resultados buscando por: {expression}"]


def test_regular_search_still_returns_matching_screenings():
    # Control positivo: una busqueda normal debe seguir generando una respuesta correcta.
    status, body = _search("Inception")
    parser = _PageParser()
    parser.feed(body.decode("utf-8"))

    assert status == 200
    assert parser.messages == ["Resultados buscando por: Inception"]
    assert b"Inception" in body
