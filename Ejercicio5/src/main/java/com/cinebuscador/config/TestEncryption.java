package com.cinebuscador.config;

/*
public class TestEncryption {

    public static void main(String[] args) {

        String password = "Password123";

        String encrypted = EncryptionService.encrypt(password);
        String decrypted = EncryptionService.decrypt(encrypted);

        System.out.println("Contraseña original: " + password);
        System.out.println("Ciphertext: " + encrypted);
        System.out.println("Contraseña descifrada: " + decrypted);
        System.out.println("Clave: " + EncryptionService.getStaticKey());
    }
}
*/

public class TestEncryption {

    public static void main(String[] args) {

        String password = "Password123";

        String encrypted = EncryptionService.encrypt(password);
        boolean matches = EncryptionService.matches(password, encrypted);

        System.out.println("Contraseña original: " + password);
        System.out.println("Hash almacenado: " + encrypted);
        System.out.println("Coincide con la original: " + matches);
    }
}
