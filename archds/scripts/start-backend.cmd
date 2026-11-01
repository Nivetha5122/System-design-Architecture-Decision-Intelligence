@echo off
setlocal
cd /d "%~dp0..\backend"
echo [ARCHDS] Starting Spring Boot with local PostgreSQL...
echo [ARCHDS] JDBC: jdbc:postgresql://localhost:5432/archds
mvn -Dspring-boot.run.profiles=postgres spring-boot:run
endlocal
