-- ============================================
-- Clínica Azul Dashboard — Schema (demo / reconstruction)
-- Anonymized structure — no real patient data.
-- ============================================

CREATE TABLE IF NOT EXISTS staff (
    staff_id      INT PRIMARY KEY AUTO_INCREMENT,
    full_name     VARCHAR(120) NOT NULL,
    role          VARCHAR(60)  NOT NULL,        -- e.g. 'Odontólogo', 'Higienista', 'Recepción'
    weekly_hours  INT          NOT NULL DEFAULT 40
);

CREATE TABLE IF NOT EXISTS patients (
    patient_id    INT PRIMARY KEY AUTO_INCREMENT,
    patient_code  VARCHAR(20)  NOT NULL UNIQUE, -- anonymized reference (e.g. 'PAT-0001')
    age_range     VARCHAR(10)  NOT NULL,        -- e.g. '18-30' — no birthdate stored
    created_at    DATE         NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id   INT PRIMARY KEY AUTO_INCREMENT,
    patient_id       INT NOT NULL,
    staff_id         INT NOT NULL,
    scheduled_at     DATETIME NOT NULL,
    service_type     VARCHAR(80) NOT NULL,      -- e.g. 'Limpieza', 'Revisión', 'Tratamiento'
    status           ENUM('scheduled', 'attended', 'no_show', 'cancelled') NOT NULL DEFAULT 'scheduled',
    reminder_sent_at DATETIME NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
);

CREATE TABLE IF NOT EXISTS satisfaction_surveys (
    survey_id       INT PRIMARY KEY AUTO_INCREMENT,
    appointment_id  INT NOT NULL,
    score           TINYINT NOT NULL,           -- 1-5
    comment         TEXT NULL,
    sentiment       ENUM('positive', 'neutral', 'negative') NULL,
    sentiment_score DECIMAL(4,3) NULL,          -- -1.0 to 1.0, filled by the n8n sentiment workflow
    submitted_at    DATETIME NOT NULL,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- ============================================
-- Seed data (synthetic, for local demo only)
-- ============================================

INSERT INTO staff (full_name, role, weekly_hours) VALUES
    ('Dra. Laura Méndez', 'Odontóloga', 40),
    ('Dr. Marc Soler', 'Odontólogo', 32),
    ('Anna Puig', 'Higienista', 36),
    ('Jordi Vidal', 'Recepción', 40);

INSERT INTO patients (patient_code, age_range, created_at) VALUES
    ('PAT-0001', '18-30', '2025-09-01'),
    ('PAT-0002', '31-45', '2025-09-03'),
    ('PAT-0003', '46-60', '2025-09-10'),
    ('PAT-0004', '18-30', '2025-10-02'),
    ('PAT-0005', '61+',   '2025-10-15'),
    ('PAT-0006', '31-45', '2025-11-01'),
    ('PAT-0007', '46-60', '2025-11-20'),
    ('PAT-0008', '18-30', '2025-12-05');

INSERT INTO appointments (patient_id, staff_id, scheduled_at, service_type, status, reminder_sent_at) VALUES
    (1, 1, '2026-05-04 09:00:00', 'Revisión',    'attended',   '2026-05-03 09:00:00'),
    (2, 1, '2026-05-04 10:00:00', 'Limpieza',    'attended',   '2026-05-03 10:00:00'),
    (3, 2, '2026-05-05 11:00:00', 'Tratamiento', 'no_show',    '2026-05-04 11:00:00'),
    (4, 3, '2026-05-05 12:00:00', 'Limpieza',    'attended',   '2026-05-04 12:00:00'),
    (5, 1, '2026-05-06 09:30:00', 'Revisión',    'attended',   '2026-05-05 09:30:00'),
    (6, 2, '2026-05-06 16:00:00', 'Tratamiento', 'cancelled',  NULL),
    (7, 3, '2026-05-07 10:00:00', 'Limpieza',    'attended',   '2026-05-06 10:00:00'),
    (8, 1, '2026-05-07 17:00:00', 'Revisión',    'no_show',    '2026-05-06 17:00:00'),
    (1, 2, '2026-05-11 09:00:00', 'Tratamiento', 'attended',   '2026-05-10 09:00:00'),
    (2, 3, '2026-05-11 11:00:00', 'Limpieza',    'attended',   '2026-05-10 11:00:00'),
    (3, 1, '2026-05-12 15:00:00', 'Revisión',    'attended',   '2026-05-11 15:00:00'),
    (4, 2, '2026-05-13 09:00:00', 'Tratamiento', 'no_show',    '2026-05-12 09:00:00');

INSERT INTO satisfaction_surveys (appointment_id, score, comment, sentiment, sentiment_score, submitted_at) VALUES
    (1, 5, 'Muy buena atención, la doctora explicó todo con calma.', 'positive', 0.870, '2026-05-04 12:00:00'),
    (2, 4, 'Todo bien, aunque tuve que esperar unos 15 minutos.',     'neutral',  0.120, '2026-05-04 13:00:00'),
    (4, 5, 'Excelente trato del personal, muy profesional.',          'positive', 0.910, '2026-05-05 14:00:00'),
    (5, 2, 'La consulta fue muy rápida, sentí que no me explicaron bien el tratamiento.', 'negative', -0.520, '2026-05-06 11:00:00'),
    (7, 4, 'Buena experiencia en general, instalaciones limpias.',    'positive', 0.640, '2026-05-07 12:00:00'),
    (9, 3, 'Atención correcta, nada destacable.',                      'neutral',  0.050, '2026-05-11 12:00:00'),
    (10,5, 'Encantada, la higienista fue muy amable y cuidadosa.',    'positive', 0.880, '2026-05-11 13:00:00'),
    (11,2, 'Esperé bastante y el trato fue algo frío.',               'negative', -0.430, '2026-05-12 17:00:00');
