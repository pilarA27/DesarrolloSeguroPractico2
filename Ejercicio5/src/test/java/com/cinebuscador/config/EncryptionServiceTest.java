package com.cinebuscador.config;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class EncryptionServiceTest {

    @Test
    void encryptStoresOneWayBcryptHashInsteadOfPlaintext() {
        // Se invoca el servicio directamente, sin iniciar Spring ni una base de datos.
        String password = "Password123!";

        String storedHash = EncryptionService.encrypt(password);

        // El formato BCrypt distingue el hash de la contrasena en texto plano.
        assertNotEquals(password, storedHash);
        assertTrue(storedHash.matches("^\\$2[aby]\\$\\d{2}\\$.{53}$"));
    }

    @Test
    void encryptUsesUniqueSaltForEachHash() {
        // La misma contrasena debe producir hashes distintos por la sal aleatoria.
        String password = "Password123!";

        String firstHash = EncryptionService.encrypt(password);
        String secondHash = EncryptionService.encrypt(password);

        // Ambos hashes deben seguir validando la contrasena original.
        assertNotEquals(firstHash, secondHash);
        assertTrue(EncryptionService.matches(password, firstHash));
        assertTrue(EncryptionService.matches(password, secondHash));
    }

    @Test
    void matchesRejectsIncorrectPassword() {
        // Un hash valido no debe aceptar una contrasena diferente.
        String storedHash = EncryptionService.encrypt("Password123!");

        assertFalse(EncryptionService.matches("IncorrectPassword!", storedHash));
    }
}
