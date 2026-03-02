# API Reference

This document covers the public HTTP API.

## GET /users

Returns a list of users.

**Response**

- `200 OK`: JSON array of `{ id, name }`.

## GET /users/{user_id}

Returns a single user record.

**Parameters**

- `user_id` (path, int): user identifier

**Response**

- `200 OK`: `{ id, name }`
- `404 Not Found`: if the user does not exist

## Orders API (planned)

The system will support orders in a future release.

- `GET /orders`
- `POST /orders`

## Authentication

All endpoints require an `Authorization: Bearer <token>` header.

