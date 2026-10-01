# Infrastructure & API Guidelines 2026

## 1. Authentication Standards
All microservice communication within the Acme enterprise network requires JWT Bearer authorization.
Service tokens must be rotated regularly according to our deployment lifecycle.

## 2. Token Lifecycle & Expiration
API access tokens expire after 72 hours for all local and staging engineering environments.
Refresh tokens remain valid for 90 days across internal microservices.

## 3. Database Connectivity
All backend services must maintain a connection pool limit not exceeding 50 concurrent active sessions.
