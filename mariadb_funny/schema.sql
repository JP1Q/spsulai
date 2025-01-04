CREATE DATABASE IF NOT EXISTS school_db;
USE school_db;

-- Nejprve vytvoříme tabulku "ucitele" (musí být před "trida" kvůli foreign key)
CREATE TABLE ucitele (
    id_ucitele INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    heslo VARCHAR(255) NOT NULL
);

-- Nyní vytvoříme "trida", která odkazuje na "ucitele"
CREATE TABLE trida (
    id_tridy INT PRIMARY KEY AUTO_INCREMENT,
    nazev VARCHAR(255),
    pristup BOOLEAN,
    tridni_ucitel INT,
    FOREIGN KEY (tridni_ucitel) REFERENCES ucitele(id_ucitele)
);

-- Vytvoříme další tabulky, zatím žádné závislosti neporušujeme
CREATE TABLE model (
    id_modelu INT PRIMARY KEY AUTO_INCREMENT,
    nazev_modelu VARCHAR(255),
    rychlost INT
);

-- Tabulka "api_klic" s odkazem na "model"
CREATE TABLE api_klic (
    id_klice INT PRIMARY KEY AUTO_INCREMENT,
    cas_vytvoreni DATETIME,
    cas_vyprseni DATETIME,
    nazev_klice VARCHAR(255),
    model INT,
    FOREIGN KEY (model) REFERENCES model(id_modelu)
);

-- Tabulka "studenti" s odkazy na "trida" a "api_klic"
CREATE TABLE studenti (
    id_student INT PRIMARY KEY AUTO_INCREMENT,
    trida INT,
    email VARCHAR(255) NOT NULL,
    heslo VARCHAR(255) NOT NULL,
    api_klic INT,
    aktivni BOOLEAN,
    FOREIGN KEY (trida) REFERENCES trida(id_tridy),
    FOREIGN KEY (api_klic) REFERENCES api_klic(id_klice)
);

-- Spojovací tabulka "spoj_klic_model" pro "api_klic" a "model"
CREATE TABLE spoj_klic_model (
    api_klic INT,
    model INT,
    PRIMARY KEY (api_klic, model),
    FOREIGN KEY (api_klic) REFERENCES api_klic(id_klice),
    FOREIGN KEY (model) REFERENCES model(id_modelu)
);
