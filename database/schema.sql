-- Update `User` table
CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    account_status ENUM('active', 'inactive', 'banned') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Update `Admin` table
CREATE TABLE Admin (
    permission_level INT NOT NULL CHECK(permission_level BETWEEN 1 AND 5),
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Update `Vehicle` table
CREATE TABLE Vehicle (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    brand VARCHAR(50),
    series VARCHAR(50),
    model VARCHAR(50),
    year INT,
    fuel_type VARCHAR(50),
    km INT,
    HP INT,
    cc INT,
    drivetrain VARCHAR(50),
    color VARCHAR(50),
    guarantee BOOLEAN,
    vehicle_type ENUM('car', 'motorcycle', 'van') NOT NULL,
    car_condition ENUM('heavily damaged', 'damaged', 'no damage'),
    plate VARCHAR(20)
);

-- Update `VehicleAd` table
CREATE TABLE VehicleAd (
    ad_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100),
    description TEXT,
    price INT NOT NULL CHECK(price > 0),
    status ENUM('available', 'sold') NOT NULL DEFAULT 'available',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vehicle_id INT NOT NULL,
    seller_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Update `AdminAction` table
CREATE TABLE AdminAction (
    action_id INT AUTO_INCREMENT PRIMARY KEY,
    action_type VARCHAR(100),
    details TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    admin_id INT NOT NULL,
    ad_id INT,
    user_id INT,
    FOREIGN KEY (admin_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ad_id) REFERENCES VehicleAd(ad_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Update `Rating` table
CREATE TABLE Rating (
    rating_id INT AUTO_INCREMENT PRIMARY KEY,
    score INT NOT NULL CHECK(score BETWEEN 1 AND 5),
    comment TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    ad_id INT NOT NULL,
    FOREIGN KEY (buyer_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ad_id) REFERENCES VehicleAd(ad_id) ON DELETE CASCADE
);

-- Update `SearchPreference` table
CREATE TABLE SearchPreference (
    sp_id INT AUTO_INCREMENT PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,
    series VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    fuel_type VARCHAR(50) NOT NULL,
    km INT NOT NULL,
    HP INT NOT NULL,
    cc INT NOT NULL,
    drivetrain VARCHAR(50) NOT NULL,
    color VARCHAR(50) NOT NULL,
    guarantee BOOLEAN NOT NULL,
    car_condition ENUM('heavily damaged', 'damaged', 'no damage'),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Update `ExpertReport` table
CREATE TABLE ExpertReport (
    w_id INT AUTO_INCREMENT PRIMARY KEY,
    content VARCHAR(255) NOT NULL,
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Update `Photo` table
CREATE TABLE Photo (
    p_id INT AUTO_INCREMENT PRIMARY KEY,
    height INT,
    width INT,
    content VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Update `Car` table
CREATE TABLE Car (
    body_style VARCHAR(50),
    door_count INT CHECK(door_count > 0),
    infotainment_screen BOOLEAN,
    ac BOOLEAN,
    emission_standard VARCHAR(50),
    airbags_count INT CHECK(airbags_count > 0),
    lane_assist BOOLEAN,
    abs BOOLEAN,
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Update `Bike` table
CREATE TABLE Bike (
    bike_type VARCHAR(50),
    frame_material VARCHAR(50),
    saddle_height DECIMAL(10, 2) CHECK(saddle_height > 0),
    handlebar_type VARCHAR(50),
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Update `Van` table
CREATE TABLE Van (
    seating_config VARCHAR(50),
    sliding_doors BOOLEAN,
    cargo_volume DECIMAL(10, 2) CHECK(cargo_volume > 0),
    removable_seats BOOLEAN,
    roof_height DECIMAL(10, 2) CHECK(roof_height > 0),
    van_type VARCHAR(50),
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Update `InterestedIn` table
CREATE TABLE InterestedIn (
    user_id INT NOT NULL,
    ad_id INT NOT NULL,
    PRIMARY KEY (user_id, ad_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ad_id) REFERENCES VehicleAd(ad_id) ON DELETE CASCADE
);

-- Update `Bid` table
CREATE TABLE Bid (
    bid_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL CHECK(amount > 0),
    status ENUM('waiting', 'rejected', 'approved') NOT NULL DEFAULT 'waiting', -- Updated to ENUM
    counter_bid DECIMAL(10, 2) CHECK(counter_bid > 0),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    buyer_id INT NOT NULL,
    ad_id INT NOT NULL,
    FOREIGN KEY (buyer_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ad_id) REFERENCES VehicleAd(ad_id) ON DELETE CASCADE
);


-- Update `Message` table
CREATE TABLE Message (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    status ENUM('sent', 'delivered', 'read') NOT NULL DEFAULT 'sent',
    FOREIGN KEY (sender_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Update `Notification` table
CREATE TABLE Notification (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Update `ActionNotif` table
CREATE TABLE ActionNotif (
    notification_id INT NOT NULL,
    action_id INT NOT NULL,
    PRIMARY KEY (notification_id, action_id),
    FOREIGN KEY (notification_id) REFERENCES Notification(notification_id) ON DELETE CASCADE,
    FOREIGN KEY (action_id) REFERENCES AdminAction(action_id) ON DELETE CASCADE
);

-- Update `BidNotif` table
CREATE TABLE BidNotif (
    notification_id INT NOT NULL,
    bid_id INT NOT NULL,
    PRIMARY KEY (notification_id, bid_id),
    FOREIGN KEY (notification_id) REFERENCES Notification(notification_id) ON DELETE CASCADE,
    FOREIGN KEY (bid_id) REFERENCES Bid(bid_id) ON DELETE CASCADE
);

-- Update `MessageNotif` table
CREATE TABLE MessageNotif (
    notification_id INT NOT NULL,
    message_id INT NOT NULL,
    PRIMARY KEY (notification_id, message_id),
    FOREIGN KEY (notification_id) REFERENCES Notification(notification_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES Message(message_id) ON DELETE CASCADE
);

-- Update `Transaction` table
CREATE TABLE Transaction (
    t_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL CHECK(amount > 0),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    ad_id INT NOT NULL,
    FOREIGN KEY (buyer_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ad_id) REFERENCES VehicleAd(ad_id) ON DELETE CASCADE
);

-- Update `Wallet` table
CREATE TABLE Wallet (
    w_id INT AUTO_INCREMENT PRIMARY KEY,
    funds DECIMAL(10, 2) NOT NULL CHECK(funds >= 0),
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Add trigger for cascading deletes on `VehicleAd`
DELIMITER //
CREATE TRIGGER delete_related_records_after_vehiclead_delete
AFTER DELETE ON VehicleAd
FOR EACH ROW
BEGIN
    DELETE FROM Photo WHERE vehicle_id = OLD.vehicle_id;
    DELETE FROM Vehicle WHERE vehicle_id = OLD.vehicle_id;
END;//
DELIMITER ;
