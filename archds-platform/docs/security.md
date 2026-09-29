# Security

- BCrypt password hashing (cost 12)
- Stateless JWT authentication with configurable expiry
- USER and ADMIN roles
- Protected project/job/audit APIs
- CORS allow-list from environment
- Bean Validation on API inputs
- JPA repositories for parameterized persistence
- No passwords or JWTs logged by the application
- JWT secret supplied by environment variable
- Generic production error responses without stack traces
- Session token stored in browser sessionStorage and cleared on logout/401
