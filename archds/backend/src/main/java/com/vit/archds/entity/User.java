package com.vit.archds.entity;
import jakarta.persistence.*; import org.springframework.security.core.*; import org.springframework.security.core.authority.SimpleGrantedAuthority; import org.springframework.security.core.userdetails.UserDetails; import java.time.Instant; import java.util.*;
@Entity @Table(name="users", uniqueConstraints=@UniqueConstraint(name="uk_users_email",columnNames="email"))
public class User implements UserDetails {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id; @Column(nullable=false) private String name; @Column(nullable=false) private String email; @Column(nullable=false) private String passwordHash; @Enumerated(EnumType.STRING) @Column(nullable=false) private Role role=Role.REVIEWER; @Column(nullable=false,updatable=false) private Instant createdAt=Instant.now(); @Column(nullable=false) private Instant updatedAt=Instant.now();
 public User(){} public User(String n,String e,String p,Role r){name=n;email=e.toLowerCase();passwordHash=p;role=r;createdAt=Instant.now();updatedAt=Instant.now();} public Long getId(){return id;} public String getName(){return name;} public String getEmail(){return email;} public String getPasswordHash(){return passwordHash;} public Role getRole(){return role;} public Instant getCreatedAt(){return createdAt;} public Instant getUpdatedAt(){return updatedAt;} public void setName(String v){name=v;updatedAt=Instant.now();} public void setPasswordHash(String v){passwordHash=v;updatedAt=Instant.now();}
 @PrePersist void prePersist(){if(createdAt==null)createdAt=Instant.now();if(updatedAt==null)updatedAt=Instant.now();}
 @PreUpdate void preUpdate(){updatedAt=Instant.now();}
 @Override public Collection<? extends GrantedAuthority> getAuthorities(){return List.of(new SimpleGrantedAuthority("ROLE_"+role.name()));} @Override public String getPassword(){return passwordHash;} @Override public String getUsername(){return email;}
}
