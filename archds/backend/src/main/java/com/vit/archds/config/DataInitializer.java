package com.vit.archds.config;

import com.vit.archds.entity.Role;
import com.vit.archds.entity.User;
import com.vit.archds.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.jdbc.core.JdbcTemplate;

@Configuration
public class DataInitializer {
    @Bean
    CommandLineRunner demo(UserRepository users, PasswordEncoder encoder, JdbcTemplate jdbc) {
        return args -> {
            try { jdbc.update("update users set role='REVIEWER' where role='USER'"); } catch (Exception ignored) { }
            createIfMissing(users, encoder, "ARCHDS Administrator", "admin@archds.local", "Admin@12345", Role.ADMIN);
            createIfMissing(users, encoder, "ARCHDS Architect", "architect@archds.local", "Architect@12345", Role.ARCHITECT);
            createIfMissing(users, encoder, "ARCHDS Reviewer", "reviewer@archds.local", "Reviewer@12345", Role.REVIEWER);
        };
    }

    private void createIfMissing(UserRepository users, PasswordEncoder encoder, String name, String email, String password, Role role) {
        if (!users.existsByEmail(email)) {
            users.save(new User(name, email, encoder.encode(password), role));
        }
    }
}
