CREATE TABLE albaranes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    numero VARCHAR(20),
    empresa VARCHAR(255),
    fecha VARCHAR(50),
    tiporec VARCHAR(10),
    alias VARCHAR(100),
    proveedor VARCHAR(100),
    tiposer VARCHAR(10),
    hora VARCHAR(20),
    hora_aeropuerto VARCHAR(20),
    letrero VARCHAR(100),
    ttoo VARCHAR(100),
    agencia VARCHAR(100),
    excursion VARCHAR(100),
    guia VARCHAR(100),
    aeropuerto VARCHAR(100),
    vuelo VARCHAR(100),
    observacion VARCHAR(255),
    referencia VARCHAR(100),
    observacion_chofer VARCHAR(255)
);

CREATE TABLE zonas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    albaran_id INT FOREIGN KEY REFERENCES albaranes(id),
    orden INT,
    zona_inicio VARCHAR(100),
    zona_fin VARCHAR(100),
    hora VARCHAR(20),
    personas INT,
    adultos INT,
    ninos INT,
    bicis INT,
    bebes INT,
    ninosb INT,
    invitados INT
);

CREATE TABLE hoteles (
    id INT IDENTITY(1,1) PRIMARY KEY,
    zona_id INT FOREIGN KEY REFERENCES zonas(id),
    orden INT,
    establecimiento VARCHAR(255),
    habitacion VARCHAR(100),
    hora VARCHAR(20),
    personas INT,
    adultos INT,
    ninos INT,
    bebes INT,
    bicis INT,
    agencia VARCHAR(100),
    lugar_recogida VARCHAR(255),
    observacion VARCHAR(255)
);