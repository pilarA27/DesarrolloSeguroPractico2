package com.cinebuscador.config;

import org.springframework.stereotype.Component;


@Component
public class SpelEvaluator {


    public String evaluate(String expression) {
        if (expression == null || expression.isBlank()) {
            return "";
        }
        return expression;
    }
}
