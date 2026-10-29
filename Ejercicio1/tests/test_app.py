import sqlite3

import pytest

from app import app, buscar_funciones


@pytest.fixture
def client(tmp_path):
    # Cada prueba usa su propia base; no se toca cine.db.
    database_path = tmp_path / "test_cine.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE peliculas (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL
        );
        CREATE TABLE funciones (
            id INTEGER PRIMARY KEY,
            pelicula_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            asientos_totales INTEGER NOT NULL,
            asientos_ocupados INTEGER NOT NULL
        );
        """
    )
    # Los datos permiten distinguir coincidencias, orden y asientos disponibles.
    connection.executemany(
        "INSERT INTO peliculas (id, nombre) VALUES (?, ?)",
        [(1, "Dune: Alfa"), (2, "Dune: Zeta"), (3, "Oppenheimer")],
    )
    connection.executemany(
        """
        INSERT INTO funciones
            (pelicula_id, fecha_hora, asientos_totales, asientos_ocupados)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1, "2026-07-13 14:30:00", 100, 80),
            (1, "2026-07-14 18:00:00", 100, 50),
            (2, "2026-07-15 21:00:00", 120, 100),
            (3, "2026-07-16 19:00:00", 100, 60),
        ],
    )
    connection.commit()
    connection.close()

    # Flask usa la base temporal durante la prueba y recupera su configuracion al terminar.
    previous_database = app.config["DATABASE"]
    previous_testing = app.config["TESTING"]
    app.config.update(DATABASE=str(database_path), TESTING=True)
    try:
        yield app.test_client()
    finally:
        app.config.update(DATABASE=previous_database, TESTING=previous_testing)


def test_search_returns_matching_screenings_and_available_seats(client):
    # Control positivo: la mitigacion debe conservar las busquedas normales.
    response = client.get("/", query_string={"buscar": "Dune"})

    assert response.status_code == 200
    assert b"Dune: Alfa" in response.data
    assert b"Dune: Zeta" in response.data
    assert b"Oppenheimer" not in response.data
    assert b"20" in response.data


def test_search_treats_apostrophe_as_literal_text(client):
    # Una comilla debe buscarse como dato, sin alterar ni romper la consulta SQL.
    response = client.get("/", query_string={"buscar": "Dune'"})

    assert response.status_code == 200
    assert b"No se encontraron funciones" in response.data


def test_search_accepts_allowlisted_date_sorting(client):
    # Se comprueba el orden completo al usar una columna y direccion permitidas.
    with app.app_context():
        results = buscar_funciones("Dune", sort_by="fecha_hora", sort_dir="DESC")

    assert [row["fecha_hora"] for row in results] == [
        "2026-07-15 21:00:00",
        "2026-07-14 18:00:00",
        "2026-07-13 14:30:00",
    ]


def test_search_falls_back_to_safe_sort_values(client):
    # Los fragmentos SQL no permitidos deben reemplazarse por nombre y ASC.
    with app.app_context():
        results = buscar_funciones(
            "Dune", sort_by="nombre DESC", sort_dir="DESC, nombre"
        )

    assert [row["pelicula"] for row in results] == [
        "Dune: Alfa",
        "Dune: Alfa",
        "Dune: Zeta",
    ]
