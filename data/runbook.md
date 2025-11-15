# Production Incident Runbook & Technical Docs

This document contains post-mortems and technical information for diagnosing production alerts.

---

## Incident: Bank XYZ API Outage
**Date:** January 15, 2024
**Symptom:** A massive spike in payment failures.
**Root Cause:** The external payment provider 'Bank XYZ' had a complete API outage.
**Error Logs:** During the incident, logs showed thousands of messages like "Connection Timeout: Upstream service 'Bank XYZ' not responding."
**Solution:** The team temporarily disabled Bank XYZ as a payment option in the checkout flow and rerouted traffic to other providers.

---

## Incident: Cart Service DB-Pool Exhaustion
**Date:** March 2, 2024
**Symptom:** Users reported being unable to add items to their cart. High 500 error rate on checkout.
**Root Cause:** The 'cart-service' had a misconfiguration that exhausted its entire database connection pool.
**Error Logs:** Logs showed many "Database Error: Failed to write payment record."
**Solution:** The connection pool size for the cart service was increased and a memory leak in the service was patched.

---

## Technical Spec: Cart Service Authentication
**Service:** cart-service
**Contact:** @team-checkout
**Info:** The cart service handles all checkout and payment logic. It authenticates with other internal services using a rotating API key.
**Common Error:** If you see "Invalid API Key: 'cart-service' auth failed," it means a deployment likely pushed an expired or incorrect key.
**Solution:** The on-call engineer must immediately roll back the 'cart-service' deployment or rotate the API key in the credentials manager.