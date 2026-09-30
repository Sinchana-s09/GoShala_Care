-- ========================================================
-- GoShala Care - MySQL Database Schema
-- Compatible with MySQL 8.0+ (InnoDB, UTF8MB4)
-- ========================================================

CREATE DATABASE IF NOT EXISTS `goshala_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `goshala_db`;

-- Disable foreign key checks during schema creation
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Users Table
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(60) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('farmer', 'vet', 'admin') NOT NULL DEFAULT 'farmer',
    `full_name` VARCHAR(100) NOT NULL,
    `phone` VARCHAR(20) DEFAULT NULL,
    `location` VARCHAR(150) DEFAULT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_role` (`role`),
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Cows Table
DROP TABLE IF EXISTS `cows`;
CREATE TABLE `cows` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farmer_id` INT NOT NULL,
    `tag_id` VARCHAR(50) NOT NULL,
    `name` VARCHAR(100) DEFAULT NULL,
    `breed` VARCHAR(80) NOT NULL DEFAULT 'Indigenous / Gir',
    `date_of_birth` DATE DEFAULT NULL,
    `lactation_stage` ENUM('Early', 'Mid', 'Late', 'Dry', 'Heifer', 'Calf') NOT NULL DEFAULT 'Mid',
    `photo_url` VARCHAR(255) DEFAULT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_farmer_tag` (`farmer_id`, `tag_id`),
    CONSTRAINT `fk_cows_farmer` FOREIGN KEY (`farmer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Diseases Reference Library
DROP TABLE IF EXISTS `diseases`;
CREATE TABLE `diseases` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(120) NOT NULL UNIQUE,
    `scientific_name` VARCHAR(150) DEFAULT NULL,
    `urgency_level` ENUM('Low', 'Moderate', 'High') NOT NULL DEFAULT 'Moderate',
    `description` TEXT NOT NULL,
    `key_indicators` TEXT,
    `prevention_guidance` TEXT NOT NULL,
    `first_aid` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Symptoms Master List
DROP TABLE IF EXISTS `symptoms`;
CREATE TABLE `symptoms` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `code` VARCHAR(50) NOT NULL UNIQUE,
    `display_name` VARCHAR(120) NOT NULL,
    `category` VARCHAR(50) NOT NULL DEFAULT 'General',
    `severity_weight` FLOAT NOT NULL DEFAULT 1.0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Disease to Symptom Mapping (Backs the Explainable Rule Engine)
DROP TABLE IF EXISTS `disease_symptoms`;
CREATE TABLE `disease_symptoms` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `disease_id` INT NOT NULL,
    `symptom_code` VARCHAR(50) NOT NULL,
    `is_primary` BOOLEAN NOT NULL DEFAULT TRUE,
    `weight` FLOAT NOT NULL DEFAULT 1.0,
    CONSTRAINT `fk_ds_disease` FOREIGN KEY (`disease_id`) REFERENCES `diseases` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uk_disease_symptom` (`disease_id`, `symptom_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Daily Vitals & Symptoms Logs
DROP TABLE IF EXISTS `vitals_logs`;
CREATE TABLE `vitals_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `cow_id` INT NOT NULL,
    `farmer_id` INT NOT NULL,
    `log_date` DATE NOT NULL,
    `temperature` DECIMAL(4, 2) NOT NULL, -- in °C e.g., 38.60
    `feed_intake` ENUM('normal', 'reduced', 'none') NOT NULL DEFAULT 'normal',
    `water_intake` ENUM('normal', 'reduced', 'none') NOT NULL DEFAULT 'normal',
    `milk_yield` DECIMAL(5, 2) NOT NULL DEFAULT 0.00, -- in Litres
    `symptoms_json` JSON DEFAULT NULL, -- Array of selected symptom codes
    `other_symptoms` VARCHAR(255) DEFAULT NULL,
    `calculated_risk` ENUM('Low', 'Moderate', 'High') NOT NULL DEFAULT 'Low',
    `risk_score` FLOAT NOT NULL DEFAULT 0.0,
    `explanation` TEXT DEFAULT NULL,
    `feed_quantity_kg` FLOAT DEFAULT 15.0,
    `water_intake_litres` FLOAT DEFAULT 50.0,
    `walking_distance_km` FLOAT DEFAULT 4.0,
    `rumination_time_hrs` FLOAT DEFAULT 7.5,
    `resting_hours` FLOAT DEFAULT 10.0,
    `heart_rate_bpm` FLOAT DEFAULT 65.0,
    `respiratory_rate` FLOAT DEFAULT 26.0,
    `predicted_disease` VARCHAR(100) DEFAULT NULL,
    `comparison_data_json` TEXT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `chk_vitals_temp` CHECK (`temperature` >= 32.0 AND `temperature` <= 45.0),
    CONSTRAINT `chk_vitals_milk` CHECK (`milk_yield` >= 0.0),
    CONSTRAINT `fk_vitals_cow` FOREIGN KEY (`cow_id`) REFERENCES `cows` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_vitals_farmer` FOREIGN KEY (`farmer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    INDEX `idx_vitals_cow_date` (`cow_id`, `log_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Photo Scans Table
DROP TABLE IF EXISTS `photo_scans`;
CREATE TABLE `photo_scans` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `cow_id` INT NOT NULL,
    `farmer_id` INT NOT NULL,
    `image_path` VARCHAR(255) NOT NULL,
    `body_part` ENUM('skin', 'udder', 'hooves', 'general') NOT NULL DEFAULT 'general',
    `predicted_label` VARCHAR(100) NOT NULL,
    `confidence` FLOAT NOT NULL,
    `detected_risk` ENUM('Low', 'Moderate', 'High') NOT NULL DEFAULT 'Low',
    `notes` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_photos_cow` FOREIGN KEY (`cow_id`) REFERENCES `cows` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_photos_farmer` FOREIGN KEY (`farmer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Case Reports (Vet Queue)
DROP TABLE IF EXISTS `cases`;
CREATE TABLE `cases` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `case_number` VARCHAR(30) NOT NULL UNIQUE,
    `cow_id` INT NOT NULL,
    `farmer_id` INT NOT NULL,
    `source` ENUM('vitals', 'photo', 'combined') NOT NULL,
    `vitals_log_id` INT DEFAULT NULL,
    `photo_scan_id` INT DEFAULT NULL,
    `suspected_disease` VARCHAR(120) DEFAULT NULL,
    `urgency` ENUM('Low', 'Moderate', 'High') NOT NULL DEFAULT 'Moderate',
    `status` ENUM('pending', 'in_review', 'resolved', 'closed') NOT NULL DEFAULT 'pending',
    `rule_explanation` TEXT,
    `ml_prediction_summary` TEXT,
    `assigned_vet_id` INT DEFAULT NULL,
    `vet_notes` TEXT DEFAULT NULL,
    `vet_recommendation` TEXT DEFAULT NULL,
    `reviewed_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_cases_cow` FOREIGN KEY (`cow_id`) REFERENCES `cows` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cases_farmer` FOREIGN KEY (`farmer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cases_vitals` FOREIGN KEY (`vitals_log_id`) REFERENCES `vitals_logs` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_cases_photo` FOREIGN KEY (`photo_scan_id`) REFERENCES `photo_scans` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_cases_vet` FOREIGN KEY (`assigned_vet_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    INDEX `idx_cases_urgency_status` (`urgency`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Vet Directory & Clinic Directory (Shown on Interactive Map)
DROP TABLE IF EXISTS `vet_directory`;
CREATE TABLE `vet_directory` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT DEFAULT NULL,
    `name` VARCHAR(120) NOT NULL,
    `clinic_name` VARCHAR(150) NOT NULL,
    `specialty` VARCHAR(100) NOT NULL DEFAULT 'Bovine Medicine & Surgery',
    `phone` VARCHAR(30) NOT NULL,
    `email` VARCHAR(120) DEFAULT NULL,
    `address` VARCHAR(255) NOT NULL,
    `latitude` DECIMAL(10, 7) NOT NULL,
    `longitude` DECIMAL(10, 7) NOT NULL,
    `emergency_available` BOOLEAN NOT NULL DEFAULT TRUE,
    `operating_hours` VARCHAR(100) DEFAULT '8:00 AM - 8:00 PM',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_vd_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- ========================================================
-- Seed Data: Core Cattle Symptoms
-- ========================================================
INSERT INTO `symptoms` (`code`, `display_name`, `category`, `severity_weight`) VALUES
('fever', 'High Fever (>39.5°C)', 'Systemic', 1.8),
('milk_drop', 'Sudden Sharp Milk Drop (>30%)', 'Production', 1.6),
('mouth_blisters', 'Drooling / Mouth Blisters & Erosions', 'Oral/Head', 2.0),
('skin_lumps', 'Skin Lumps, Nodules or Scabs', 'Dermatological', 1.9),
('limping', 'Limping / Hoof Sores / Foot Lesions', 'Locomotive', 1.5),
('not_eating', 'Not Eating / No Cudding / Off Feed', 'Digestive', 1.7),
('swollen_udder', 'Hot, Hard or Swollen Udder / Clots in Milk', 'Mammary', 2.0),
('bloat', 'Swollen Left Belly / Severe Bloat', 'Digestive', 2.0),
('downer_cow', 'Unable to Stand / Downer Cow After Calving', 'Metabolic', 2.0),
('abortion', 'Abortion / Retained Placenta / Discharge', 'Reproductive', 1.8),
('leg_swelling', 'Crackling Leg/Shoulder Swelling (Crepitus)', 'Musculoskeletal', 2.0),
('breathing_difficulty', 'Rapid Grunting Breathing / Froth from Nostrils', 'Respiratory', 1.9),
('sweet_breath', 'Sweet Acetone Smell in Breath or Milk', 'Metabolic', 1.5),
('tremor_cold_ears', 'Muscle Tremors, Staggering, Cold Ears', 'Metabolic', 1.8);

-- ========================================================
-- Seed Data: Core Cattle Diseases & Knowledge Base
-- ========================================================
INSERT INTO `diseases` (`name`, `scientific_name`, `urgency_level`, `description`, `key_indicators`, `prevention_guidance`, `first_aid`) VALUES
('Mastitis', 'Bovine Mastitis (Streptococcus / Staph aureus)', 'High', 
'Inflammation of the mammary gland caused by bacterial infection through teat canals. Causes severe economic loss and milk spoilage.', 
'Hot, hard, painful swollen udder, watery or clotted milk, abrupt reduction in milk yield, fever.', 
'Dip teats in antiseptic iodine post-milking, maintain clean dry bedding, disinfect milking equipment, practice good hand hygiene.', 
'Isolate affected quarter, milk out gently, apply cold compress if acute inflammation, administer vet-prescribed intramammary antibiotics.'),

('Foot-and-Mouth Disease (FMD)', 'Aphthovirus', 'High', 
'Highly contagious viral disease affecting cloven-hoofed animals. Rapidly spreads through aerosol, direct contact, and contaminated feed.', 
'Excessive frothy salivation, blister-like vesicles on tongue, lips, and interdigital clefts of hooves, severe lameness, high fever.', 
'Strict biosecurity, mandatory 6-month vaccination, quarantine new stock for 21 days, disinfect farm gate with 4% sodium carbonate.', 
'Isolate cow immediately. Wash mouth with 1% potassium permanganate or mild alum solution, treat foot lesions with antiseptic fly-repellent paste. Contact veterinary authority.'),

('Lumpy Skin Disease (LSD)', 'Capripoxvirus', 'High', 
'Vector-borne viral disease characterized by firm round skin nodules, enlarged lymph nodes, and edema.', 
'Round, raised cutaneous nodules (2-5 cm) all over body, fever, watery eye discharge, swelling in dewlap and limbs.', 
'Annual homologous goat pox / LSD vaccine, control biting flies, ticks, and mosquitoes using neem/permethrin repellents.', 
'Isolate animal in vector-proof enclosure. Clean open nodules with antiseptic solution (povidone-iodine), provide soft palatable feed and fresh water.'),

('Milk Fever (Hypocalcemia)', 'Parturient Paresis', 'High', 
'Acute metabolic disorder occurring around calving due to sudden calcium demand for colostrum production.', 
'Unable to stand (downer cow), S-shaped curve of neck, muscle tremors, cold ears and extremities, dilated pupils.', 
'Feed low-calcium diet during dry period to prime parathyroid hormone, provide oral calcium gel immediately before and after calving.', 
'Do NOT drench liquid medications (high aspiration risk). Keep cow propped in sternal position with straw bales. Vet must urgently administer IV Calcium Borogluconate slowly.'),

('Bloat (Tympanites)', 'Ruminal Tympany', 'High', 
'Excessive gas accumulation in rumen, either frothy (due to lush legumes) or free gas (esophageal obstruction). Can cause fatal asphyxiation.', 
'Distended left flank drum-tight, grunting, kicking at belly, labored mouth breathing, restlessness.', 
'Avoid sudden turnout onto lush wet clover/alfalfa pastures; feed dry hay before grazing green fodder.', 
'For urgent relief, keep head elevated. Administer antifoaming agents (vegetable oil 500ml or dimethicone). In extreme life-threatening distress, veterinary emergency trocharization of left paralumbar fossa.'),

('Ketosis (Acetonemia)', 'Bovine Ketosis', 'Moderate', 
'Metabolic state of severe negative energy balance in high-yielding dairy cows during early lactation.', 
'Rapid loss of body condition, sweet acetone odor in breath/urine/milk, sudden drop in milk, partial anorexia (refusing grain but eating straw).', 
'Balanced transition diet with adequate non-fiber carbohydrates, avoid overconditioning before calving, feed propylene glycol or niacin.', 
'Administer oral propylene glycol (250-400ml twice daily), intravenous dextrose 50%, and corticosteroids under vet supervision.'),

('Brucellosis', 'Brucella abortus', 'High', 
'Bacterial zoonotic disease causing reproductive failure, contagious abortion, and infertility. Poses high human transmission risk (undulant fever).', 
'Late-term abortion (between 5th and 8th months), retained placenta, uterine infection, testicular swelling in bulls.', 
'Vaccinate female calves at 4-8 months with Strain 19 or RB51. Never drink unpasteurized milk. Test and screen all new breeding stock.', 
'Burn or deeply bury aborted fetus and placenta with quicklime. Disinfect area thoroughly with bleaching powder. Wear gloves. Consult veterinary authority.'),

('Black Quarter (BQ)', 'Clostridium chauvoei', 'High', 
'Acute bacterial soil-borne infection characterized by severe toxemia and gas-filled muscular necrosis, especially in young cattle (6-24 months).', 
'Crepitant (crackling sound on touch) swelling over hip, shoulder or chest, high fever, acute lameness, depression, dark dry skin over swelling.', 
'Annual vaccination before monsoon onset. Do not graze on newly excavated pastures.', 
'Extremely urgent veterinary intervention required. High doses of crystalline penicillin if detected early; drain and oxygenate local wound tissue.');

-- ========================================================
-- Seed Data: Disease-Symptom Mappings for Rule Engine
-- ========================================================
-- Mastitis
INSERT INTO `disease_symptoms` (`disease_id`, `symptom_code`, `is_primary`, `weight`) VALUES
(1, 'swollen_udder', 1, 2.5),
(1, 'milk_drop', 1, 2.0),
(1, 'fever', 0, 1.2);

-- FMD
INSERT INTO `disease_symptoms` (`disease_id`, `symptom_code`, `is_primary`, `weight`) VALUES
(2, 'mouth_blisters', 1, 3.0),
(2, 'limping', 1, 2.2),
(2, 'fever', 1, 1.8),
(2, 'not_eating', 0, 1.5);

-- LSD
INSERT INTO `disease_symptoms` (`disease_id`, `symptom_code`, `is_primary`, `weight`) VALUES
(3, 'skin_lumps', 1, 3.5),
(3, 'fever', 1, 1.8),
(3, 'milk_drop', 0, 1.3);

-- Milk Fever
INSERT INTO `disease_symptoms` (`disease_id`, `symptom_code`, `is_primary`, `weight`) VALUES
(4, 'downer_cow', 1, 3.5),
(4, 'tremor_cold_ears', 1, 2.5),
(4, 'not_eating', 0, 1.2);

-- Bloat
INSERT INTO `disease_symptoms` (`disease_id`, `symptom_code`, `is_primary`, `weight`) VALUES
(5, 'bloat', 1, 3.5),
(5, 'breathing_difficulty', 1, 2.0),
(5, 'not_eating', 0, 1.5);

-- Ketosis
INSERT INTO `disease_symptoms` (`disease_id`, `symptom_code`, `is_primary`, `weight`) VALUES
(6, 'sweet_breath', 1, 3.0),
(6, 'milk_drop', 1, 2.0),
(6, 'not_eating', 0, 1.6);

-- Brucellosis
INSERT INTO `disease_symptoms` (`disease_id`, `symptom_code`, `is_primary`, `weight`) VALUES
(7, 'abortion', 1, 3.5),
(7, 'fever', 0, 1.2);

-- Black Quarter
INSERT INTO `disease_symptoms` (`disease_id`, `symptom_code`, `is_primary`, `weight`) VALUES
(8, 'leg_swelling', 1, 3.5),
(8, 'limping', 1, 2.0),
(8, 'fever', 1, 1.8);

-- ========================================================
-- Seed Data: Sample Vet Clinics (For Interactive Map)
-- Coordinates near Anand / Gujarat (India's Dairy Capital) & surroundings
-- ========================================================
INSERT INTO `vet_directory` (`name`, `clinic_name`, `specialty`, `phone`, `email`, `address`, `latitude`, `longitude`, `emergency_available`, `operating_hours`) VALUES
('Dr. Ramesh Patel, MVSc', 'Kamdhenu Bovine Care & Research Center', 'Bovine Surgery & Udder Health', '+91 98250 12345', 'dr.ramesh@kamdhenuvet.in', 'Near Dairy Circle, Anand, Gujarat 388001', 22.5645, 72.9289, 1, '24/7 Emergency Service'),
('Dr. Sunita Sharma, Ph.D', 'Pashu Seva Kendra Veterinary Hospital', 'Epidemiology & Infectious Diseases', '+91 98765 43210', 'sunita.sharma@pashuseva.org', 'Station Road, Nadiad, Gujarat 387001', 22.6916, 72.8634, 1, '8:00 AM - 9:00 PM'),
('Dr. Arvind Joshi, MVSc', 'Amul Zone Mobile Cattle Dispensary', 'Reproductive Care & Nutrition', '+91 94270 56789', 'arvind.joshi@amulcare.in', 'Mogri Crossing, Vidyanagar, Gujarat 388120', 22.5510, 72.9150, 0, '9:00 AM - 6:00 PM'),
('Dr. Meera Kulkarni, BVSc', 'Surabhi Livestock Emergency Clinic', 'Metabolic Disorders & Calf Care', '+91 91234 56780', 'meera.vet@surabhicattle.com', 'Borsad Highway, Anand Rural, Gujarat 388540', 22.5200, 72.9000, 1, '24/7 On-Call Support');
