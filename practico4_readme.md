# Práctico 4

## Ejercicio 1: Mitigación de SQL

Las pruebas del Ejercicio 1 comprueban la búsqueda y la mitigación de SQL injection.

### Ejecución

Antes de ejecutar los ejercicios dockerizados, abrir Docker Desktop y esperar a que el motor esté activo. Se puede comprobar con `docker info`.

Desde la raíz del repositorio, instalar las dependencias y ejecutar:

```bash
python -m pip install -r Ejercicio1/requirements.txt
python -m pytest Ejercicio1
```

## Ejercicio 2: Mitigación de Cross Site Scripting

Las pruebas pytest verifican que las descripciones guardadas con etiquetas `<script>` e `<img>` se muestren como texto escapado en los resultados y en la vista de edición, evitando su interpretación como HTML activo.

### Ejecución
```bash
python -m pip install -r Ejercicio2/requirements.txt
python -m pytest Ejercicio2
```

## Ejercicio 3: integración de subida de afiches

Estas pruebas HTTP comprueban que se rechacen archivos que no sean imágenes raster PNG/JPEG, que se conserve la selección de imágenes en el formulario y que una imagen válida se guarde con nombre generado por el servidor y se entregue con tipo seguro. La validación del servidor complementa el atributo `accept` del navegador, que por sí solo no bloquea archivos no permitidos.


### Ejecución
Desde la carpeta `Ejercicio3`, ejecutar la aplicación y las pruebas en Compose:

```bash
docker compose --profile test run --build --rm integration-tests
docker compose down
```

Mientras esté iniciada, la aplicación está disponible en `http://localhost:8083`. El contenedor de pruebas espera a que responda y devuelve el resultado de pytest.

## Ejercicio 4: integración de mitigación SSTI/RCE

Las pruebas HTTP de pytest verifican que expresiones que antes se evaluaban como SpEL se muestren literalmente y que la búsqueda normal siga funcionando. No ejecutan comandos ni acciones en el sistema.

### Ejecución
Desde la carpeta `Ejercicio4`, iniciar la aplicación y ejecutar el runner de pruebas:

```bash
docker compose up --build -d
docker build -t ejercicio4-integration-tests -f tests/Dockerfile tests
docker run --rm --network ejercicio4_default -e APP_BASE_URL=http://cinebuscador4:8080 ejercicio4-integration-tests
docker compose down
```

Mientras esté iniciada, la aplicación está disponible en `http://localhost:8084`. El runner usa la red interna de Compose y espera a que responda la aplicación.

## Ejercicio 5: pruebas unitarias de almacenamiento seguro

Las pruebas JUnit verifican que las contraseñas se almacenen como hashes BCrypt con sal y que solo la contraseña correcta valide el hash.

### Ejecución
Desde la carpeta `Ejercicio5`, con Docker Desktop abierto, ejecutar en **Git Bash (Windows)**:

```bash
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W):/app" -w /app maven:3.9.11-eclipse-temurin-17-noble mvn test
```

El contenedor incluye Maven y Java 17, por lo que no es necesario instalarlos localmente. La primera ejecución descarga la imagen y las dependencias. `MSYS_NO_PATHCONV=1` evita que Git Bash transforme las rutas internas del contenedor. Al finalizar, el contenedor se elimina y los reportes quedan en `Ejercicio5/target/surefire-reports`.

Si las pruebas pasan, Maven muestra `BUILD SUCCESS` junto con el resumen de JUnit.
