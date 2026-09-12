package com.cinebuscador.config;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

public class EncryptionService {

    private static final PasswordEncoder PASSWORD_ENCODER = new BCryptPasswordEncoder();

    public static String encrypt(String plaintext) {
        return PASSWORD_ENCODER.encode(plaintext);
    }

    public static boolean matches(String plaintext, String storedHash) {
        return PASSWORD_ENCODER.matches(plaintext, storedHash);
    }
}
