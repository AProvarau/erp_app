CREATE TABLE clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    client_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (role_id) REFERENCES roles (role_id),
    FOREIGN KEY (client_id) REFERENCES clients (client_id)
);

CREATE TABLE invitations (
    invitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    role_id INTEGER NOT NULL,
    client_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (datetime('now', '+1 day')),
    used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (role_id) REFERENCES roles (role_id),
    FOREIGN KEY (client_id) REFERENCES clients (client_id)
);

CREATE TABLE password_reset_tokens (
    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (datetime('now', '+1 hour')),
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE gateways (
    gateway_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE terminals (
    terminal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE export_contracts (
    export_contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL UNIQUE,
    date DATE NOT NULL,
    client_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (client_id),
    FOREIGN KEY (created_by) REFERENCES users (user_id)
);

CREATE TABLE general_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    gateway_id INTEGER NOT NULL,
    terminal_id INTEGER NOT NULL,
    vehicle TEXT,
    invoice_number TEXT NOT NULL,
    export_contract_id INTEGER NOT NULL,
    delivery_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (client_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (gateway_id) REFERENCES gateways (gateway_id),
    FOREIGN KEY (terminal_id) REFERENCES terminals (terminal_id),
    FOREIGN KEY (export_contract_id) REFERENCES export_contracts (export_contract_id)
);