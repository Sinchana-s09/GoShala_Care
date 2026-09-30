-- ============================================================
-- GoShala Care -- Early Detection and Management of Cow Diseases
-- MySQL database schema
-- ============================================================

DROP DATABASE IF EXISTS goshala_care;
CREATE DATABASE goshala_care
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE goshala_care;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. users -- farmers, vets and admins (one login table, role column)
CREATE TABLE users (
  user_id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name           VARCHAR(100)  NOT NULL,
  email          VARCHAR(150)  NOT NULL,
  password_hash  VARCHAR(255)  NOT NULL,
  role           ENUM('farmer','vet','admin') NOT NULL DEFAULT 'farmer',
  phone          VARCHAR(20),
  village        VARCHAR(100),
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                 ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uq_users_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE INDEX idx_users_role ON users(role);

-- 2. cows -- each cow belongs to exactly one farmer (user)
CREATE TABLE cows (
  cow_id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         INT UNSIGNED NOT NULL,
  tag             VARCHAR(30)  NOT NULL,
  breed           VARCHAR(60),
  age_years       DECIMAL(4,1) CHECK (age_years >= 0),
  last_vaccinated DATE,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cows_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT uq_cows_owner_tag UNIQUE (user_id, tag)
) ENGINE=InnoDB;

CREATE INDEX idx_cows_user ON cows(user_id);

-- 3. daily_logs -- one row per cow per day: vitals + intake
CREATE TABLE daily_logs (
  log_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  cow_id          INT UNSIGNED NOT NULL,
  log_date        DATE NOT NULL,
  temperature_c   DECIMAL(4,1)  CHECK (temperature_c BETWEEN 30 AND 45),
  feed_intake_kg  DECIMAL(5,1)  CHECK (feed_intake_kg >= 0),
  water_intake_l  DECIMAL(5,1)  CHECK (water_intake_l >= 0),
  milk_yield_l    DECIMAL(5,1)  CHECK (milk_yield_l   >= 0),
  feed_status     ENUM('normal','reduced','none') NOT NULL DEFAULT 'normal',
  water_status    ENUM('normal','reduced','none') NOT NULL DEFAULT 'normal',
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_logs_cow
    FOREIGN KEY (cow_id) REFERENCES cows(cow_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT uq_logs_cow_date UNIQUE (cow_id, log_date)
) ENGINE=InnoDB;

CREATE INDEX idx_logs_cow_date ON daily_logs(cow_id, log_date);

-- 4. symptoms -- master lookup list (normalized, not free text)
CREATE TABLE symptoms (
  symptom_id   SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code         VARCHAR(20)  NOT NULL,
  label        VARCHAR(120) NOT NULL,
  CONSTRAINT uq_symptoms_code UNIQUE (code)
) ENGINE=InnoDB;

-- 5. daily_log_symptoms -- which symptoms were ticked on a given log
--    (many-to-many between daily_logs and symptoms)
CREATE TABLE daily_log_symptoms (
  log_id      BIGINT UNSIGNED   NOT NULL,
  symptom_id  SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (log_id, symptom_id),
  CONSTRAINT fk_dls_log
    FOREIGN KEY (log_id) REFERENCES daily_logs(log_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_dls_symptom
    FOREIGN KEY (symptom_id) REFERENCES symptoms(symptom_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 6. diseases -- reference library
CREATE TABLE diseases (
  disease_id   SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(120) NOT NULL,
  description  TEXT,
  prevention   TEXT,
  urgency      TINYINT UNSIGNED NOT NULL CHECK (urgency BETWEEN 1 AND 3),
  CONSTRAINT uq_diseases_name UNIQUE (name)
) ENGINE=InnoDB;

-- 7. disease_symptoms -- which symptoms indicate which disease
--    (many-to-many between diseases and symptoms)
CREATE TABLE disease_symptoms (
  disease_id  SMALLINT UNSIGNED NOT NULL,
  symptom_id  SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (disease_id, symptom_id),
  CONSTRAINT fk_ds_disease
    FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ds_symptom
    FOREIGN KEY (symptom_id) REFERENCES symptoms(symptom_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 8. vets -- directory entries shown on the map (added by admin)
CREATE TABLE vets (
  vet_id      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(120) NOT NULL,
  specialty   VARCHAR(120),
  phone       VARCHAR(20),
  address     VARCHAR(255),
  latitude    DECIMAL(9,6),
  longitude   DECIMAL(9,6),
  added_by    INT UNSIGNED,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_vets_admin
    FOREIGN KEY (added_by) REFERENCES users(user_id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 9. reports -- the case queue: every symptom check / photo scan
--    result that reaches Moderate/High urgency, for vet review
CREATE TABLE reports (
  report_id    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id      INT UNSIGNED NOT NULL,
  cow_id       INT UNSIGNED,
  log_id       BIGINT UNSIGNED,
  source       ENUM('vitals','symptoms','photo') NOT NULL,
  result       VARCHAR(255) NOT NULL,
  urgency      TINYINT UNSIGNED NOT NULL CHECK (urgency BETWEEN 1 AND 3),
  status       ENUM('pending','reviewed') NOT NULL DEFAULT 'pending',
  vet_note     TEXT,
  reviewed_by  INT UNSIGNED,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at  DATETIME NULL,
  CONSTRAINT fk_reports_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_reports_cow
    FOREIGN KEY (cow_id) REFERENCES cows(cow_id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_reports_log
    FOREIGN KEY (log_id) REFERENCES daily_logs(log_id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_reports_reviewer
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_reports_status_urgency ON reports(status, urgency DESC, created_at DESC);
CREATE INDEX idx_reports_user ON reports(user_id);

SET FOREIGN_KEY_CHECKS = 1;
