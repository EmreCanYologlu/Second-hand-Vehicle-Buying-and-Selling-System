-- Create `User` table
CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    account_status ENUM('active', 'inactive', 'banned') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create `Admin` table
CREATE TABLE Admin (
    permission_level INT NOT NULL CHECK(permission_level BETWEEN 1 AND 5),
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Create `Vehicle` table
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
    engine_size INT,
    drivetrain VARCHAR(50),
    color VARCHAR(50),
    guarantee BOOLEAN,
    vehicle_condition ENUM('new', 'used', 'heavily damaged', 'damaged', 'no damage') NOT NULL DEFAULT 'used',
    plate VARCHAR(20)
);

-- Create `VehicleAd` table
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

-- Create `Car` table
CREATE TABLE Car (
    car_id INT AUTO_INCREMENT PRIMARY KEY,
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

-- Create `Motorcycle` table
CREATE TABLE Motorcycle (
    motorcycle_id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('sport', 'cruiser', 'touring', 'enduro', 'scooter', 'dirt') NOT NULL,
    abs BOOLEAN DEFAULT FALSE,
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Create `Van` table
CREATE TABLE Van (
    van_id INT AUTO_INCREMENT PRIMARY KEY,
    cargo_capacity INT NOT NULL,
    cargo_length INT,
    cargo_width INT,
    cargo_height INT,
    max_payload INT,
    seating_config VARCHAR(50),
    sliding_doors BOOLEAN,
    removable_seats BOOLEAN,
    roof_height DECIMAL(10, 2) CHECK(roof_height > 0),
    van_type VARCHAR(50),
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Create `Photo` table
CREATE TABLE Photo (
    p_id INT AUTO_INCREMENT PRIMARY KEY,
    height INT,
    width INT,
    content VARCHAR(255) NOT NULL,
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Create `AdminAction` table
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

-- Create `Rating` table
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

-- Create `SearchPreference` table
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
    vehicle_condition ENUM('new', 'used', 'heavily damaged', 'damaged', 'no damage'),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Create `ExpertReport` table
CREATE TABLE ExpertReport (
    w_id INT AUTO_INCREMENT PRIMARY KEY,
    content LONGBLOB NOT NULL,
    vehicle_id INT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- Create `InterestedIn` table
CREATE TABLE InterestedIn (
    user_id INT NOT NULL,
    ad_id INT NOT NULL,
    PRIMARY KEY (user_id, ad_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ad_id) REFERENCES VehicleAd(ad_id) ON DELETE CASCADE
);

-- Create `Bid` table
CREATE TABLE Bid (
    bid_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL CHECK(amount > 0),
    status VARCHAR(50),
    counter_bid DECIMAL(10, 2) CHECK(counter_bid > 0),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    buyer_id INT NOT NULL,
    ad_id INT NOT NULL,
    FOREIGN KEY (buyer_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ad_id) REFERENCES VehicleAd(ad_id) ON DELETE CASCADE
);

-- Create `Message` table
CREATE TABLE Message (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    FOREIGN KEY (sender_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Create `Notification` table
CREATE TABLE Notification (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Create `ActionNotif` table
CREATE TABLE ActionNotif (
    notification_id INT NOT NULL,
    action_id INT NOT NULL,
    PRIMARY KEY (notification_id, action_id),
    FOREIGN KEY (notification_id) REFERENCES Notification(notification_id) ON DELETE CASCADE,
    FOREIGN KEY (action_id) REFERENCES AdminAction(action_id) ON DELETE CASCADE
);

-- Create `BidNotif` table
CREATE TABLE BidNotif (
    notification_id INT NOT NULL,
    bid_id INT NOT NULL,
    PRIMARY KEY (notification_id, bid_id),
    FOREIGN KEY (notification_id) REFERENCES Notification(notification_id) ON DELETE CASCADE,
    FOREIGN KEY (bid_id) REFERENCES Bid(bid_id) ON DELETE CASCADE
);

-- Create `MessageNotif` table
CREATE TABLE MessageNotif (
    notification_id INT NOT NULL,
    message_id INT NOT NULL,
    PRIMARY KEY (notification_id, message_id),
    FOREIGN KEY (notification_id) REFERENCES Notification(notification_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES Message(message_id) ON DELETE CASCADE
);

-- Create `Transaction` table
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

-- Create `Wallet` table
CREATE TABLE Wallet (
    w_id INT AUTO_INCREMENT PRIMARY KEY,
    funds DECIMAL(10, 2) NOT NULL CHECK(funds >= 0),
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_vehicle_condition ON Vehicle(vehicle_condition);
CREATE INDEX idx_vehicle_type ON Vehicle(vehicle_id);
CREATE INDEX idx_motorcycle_type ON Motorcycle(type);
CREATE INDEX idx_van_capacity ON Van(cargo_capacity);
CREATE INDEX idx_vehicle_brand ON Vehicle(brand);
CREATE INDEX idx_vehicle_year ON Vehicle(year);
CREATE INDEX idx_ad_status ON VehicleAd(status);
CREATE INDEX idx_ad_price ON VehicleAd(price);
CREATE INDEX idx_ad_created ON VehicleAd(created_at);