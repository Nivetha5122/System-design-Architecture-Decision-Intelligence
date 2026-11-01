package com.vit.archds.dto;
import jakarta.validation.constraints.*;
public final class AuthDtos { private AuthDtos(){}
 public record Register(@NotBlank @Size(max=100) String name,@NotBlank @Email String email,@NotBlank @Size(min=8,max=100) String password){}
 public record Login(@NotBlank @Email String email,@NotBlank String password){}
 public record AuthResponse(String token,Long userId,String name,String email,String role){}
}
