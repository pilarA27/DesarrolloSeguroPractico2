import os
import re
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

import pytest


# Docker configura la URL interna; fuera del contenedor se puede indicar APP_BASE_URL.
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
BOUNDARY = "pytest-integration-boundary"


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    # Conserva el 302 del POST para poder comprobar la redireccion del servidor.
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


HTTP_CLIENT = urllib.request.build_opener(_NoRedirectHandler)


def _request(path, method="GET", data=None, headers=None):
    # Se consulta la aplicacion real y se conservan tambien las respuestas de error HTTP.
    request = urllib.request.Request(
        f"{APP_BASE_URL}{path}", data=data, headers=headers or {}, method=method
    )
    try:
        with HTTP_CLIENT.open(request, timeout=10) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as response:
        return response.code, response.headers, response.read()


def _multipart_upload(filename, content, content_type):
    # Construye el mismo campo multipart que envia el formulario de afiches.
    body = (
        f"--{BOUNDARY}\r\n"
        f'Content-Disposition: form-data; name="afiche"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + content + f"\r\n--{BOUNDARY}--\r\n".encode()
    headers = {"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"}
    return _request("/upload/1", method="POST", data=body, headers=headers)


def _png_chunk(chunk_type, data):
    # Cada bloque PNG incluye longitud y checksum para que la imagen sea valida.
    chunk = chunk_type + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk))


def _valid_png():
    # Genera una imagen RGB de un pixel en memoria, sin archivos auxiliares.
    image_header = struct.pack(">2I5B", 1, 1, 8, 2, 0, 0, 0)
    image_data = zlib.compress(b"\x00\x00\x00\x00")
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", image_header)
        + _png_chunk(b"IDAT", image_data)
        + _png_chunk(b"IEND", b"")
    )


@pytest.fixture(scope="session", autouse=True)
def wait_for_application():
    # Compose puede iniciar pytest antes de que Spring Boot este listo.
    deadline = time.monotonic() + 90
    last_error = None
    while time.monotonic() < deadline:
        try:
            status, _, _ = _request("/")
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
        f"Último error: {last_error}. Iniciá Ejercicio3 con Docker Compose."
    )


def test_upload_form_limits_file_picker_to_images():
    # Solo comprueba la restriccion del selector; esto no valida el contenido en el servidor.
    status, _, body = _request("/upload/1")

    assert status == 200
    assert b'type="file"' in body
    assert b'accept="image/png,image/jpeg"' in body


# Se intenta eludir el selector con HTML, un MIME falso y un SVG.
@pytest.mark.parametrize(
    ("filename", "content_type", "content"),
    [
        ("payload.html", "text/html", b"<html><script>alert(1)</script></html>"),
        ("payload.png", "image/png", b"<html><script>alert(1)</script></html>"),
        ("payload.svg", "image/svg+xml", b"<svg xmlns='http://www.w3.org/2000/svg'/>"),
    ],
)
def test_upload_rejects_non_raster_images(filename, content_type, content):
    # La mitigacion del servidor deberia rechazar la carga y no publicar el archivo.
    status, _, _ = _multipart_upload(filename, content, content_type)

    assert status == 400
    assert _request(f"/uploads/{urllib.parse.quote(filename)}")[0] == 404


def test_valid_png_is_saved_with_server_generated_name_and_served_as_image():
    # El contenido es PNG, aunque el cliente declare un nombre y MIME HTML.
    image = _valid_png()
    status, headers, _ = _multipart_upload("poster.html", "text/html", image)

    assert status == 302
    assert headers.get("Location") == "/"

    # La busqueda permite obtener el nombre con el que se guardo el afiche.
    search = urllib.parse.urlencode({"buscar": "Inception"})
    search_status, _, page = _request(f"/?{search}")

    assert search_status == 200
    match = re.search(rb'<img[^>]+src="(/uploads/[^"]+)"', page)
    assert match is not None
    image_path = match.group(1).decode()
    assert re.fullmatch(r"/uploads/[0-9a-f-]{36}\.png", image_path)

    # Se comprueban los bytes recuperados y las cabeceras de entrega segura.
    image_status, image_headers, served_image = _request(image_path)

    assert image_status == 200
    assert image_headers.get_content_type() == "image/png"
    assert image_headers.get("X-Content-Type-Options") == "nosniff"
    assert served_image == image
