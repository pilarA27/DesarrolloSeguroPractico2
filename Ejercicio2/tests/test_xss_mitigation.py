import sqlite3

import pytest

from app import app


@pytest.fixture
def client(tmp_path):
    # Se crea una base temporal con una pelicula y una funcion para cada caso.
    database_path = tmp_path / "test_cine2.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE peliculas (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            genero TEXT NOT NULL,
            director TEXT NOT NULL,
            descripcion TEXT
        );
        CREATE TABLE funciones (
            id INTEGER PRIMARY KEY,
            pelicula_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            asientos_totales INTEGER NOT NULL,
            asientos_ocupados INTEGER NOT NULL
        );
        INSERT INTO peliculas (id, nombre, genero, director, descripcion)
        VALUES (1, 'Pelicula de prueba', 'Drama', 'Directora', 'Descripcion inicial');
        INSERT INTO funciones
            (id, pelicula_id, fecha_hora, asientos_totales, asientos_ocupados)
        VALUES (1, 1, '2026-07-13 14:30:00', 100, 20);
        """
    )
    connection.commit()
    connection.close()

    # El cliente prueba Flask sin servidor externo; la configuracion se restaura al final.
    previous_database = app.config["DATABASE"]
    previous_testing = app.config["TESTING"]
    app.config.update(DATABASE=str(database_path), TESTING=True)
    try:
        yield app.test_client()
    finally:
        app.config.update(DATABASE=previous_database, TESTING=previous_testing)


# Cada prueba se repite con una etiqueta script y con un evento HTML.
@pytest.mark.parametrize(
    "payload",
    [
        "<script>alert('xss')</script>",
        '<img src=x onerror="alert(1)">',
    ],
)
def test_saved_description_is_rendered_as_text_in_search_results(client, payload):
    # Se guarda la entrada por el formulario real para cubrir el XSS almacenado.
    save_response = client.post(
        "/edit/1",
        data={
            "nombre": "Pelicula de prueba",
            "genero": "Drama",
            "director": "Directora",
            "descripcion": payload,
        },
    )

    assert save_response.status_code == 302

    # La busqueda debe mostrar entidades HTML, nunca las etiquetas activas.
    response = client.get("/", query_string={"buscar": "Pelicula"})

    assert response.status_code == 200
    assert payload.encode() not in response.data
    assert b"&lt;" in response.data
    assert b"&gt;" in response.data
    assert b"<script>" not in response.data
    assert b"<img" not in response.data


@pytest.mark.parametrize(
    "payload",
    [
        "<script>alert('xss')</script>",
        '<img src=x onerror="alert(1)">',
    ],
)
def test_saved_description_is_escaped_in_edit_preview(client, payload):
    # La vista de edicion tambien muestra la descripcion guardada y debe escaparla.
    client.post(
        "/edit/1",
        data={
            "nombre": "Pelicula de prueba",
            "genero": "Drama",
            "director": "Directora",
            "descripcion": payload,
        },
    )

    # Se revisa el HTML devuelto al volver a abrir la pelicula.
    response = client.get("/edit/1")

    assert response.status_code == 200
    assert payload.encode() not in response.data
    assert b"&lt;" in response.data
    assert b"&gt;" in response.data
