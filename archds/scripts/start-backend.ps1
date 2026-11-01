Set-Location "$PSScriptRoot/../backend"
Write-Host "[ARCHDS] Starting Spring Boot with local PostgreSQL..."
Write-Host "[ARCHDS] JDBC: jdbc:postgresql://localhost:5432/archds"
mvn -Dspring-boot.run.profiles=postgres spring-boot:run
