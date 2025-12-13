PRAGMA foreign_keys = ON;

CREATE TABLE label(
    name VARCHAR2(20),
    PRIMARY KEY(name)
);

CREATE TABLE patient(
    id INTEGER,
    name VARCHAR2(20),
    PRIMARY KEY(id)
);

CREATE TABLE annotation(
    set_name INTEGER,
    path_url VARCHAR2(40),
    label VARCHAR2(20),
    patient_id INTEGER,
    desc VARCHAR(40),

    CONSTRAINT fk FOREIGN KEY (label)
        REFERENCES label(name),
    CONSTRAINT fk2 FOREIGN KEY (patient_id)
        REFERENCES patient(id),
    PRIMARY KEY(set_name, path_url)
);