Create DATABASE FLeetManagement;

Use FLeetManagement;

-- VEHICLES TABLE
CREATE TABLE Vehicles (
    VehicleID INT PRIMARY KEY AUTO_INCREMENT,
    Manufacturer VARCHAR(100) NOT NULL,
    ModelYear INT CHECK (ModelYear >= 1900),
    GrossWeight DECIMAL(10,2) CHECK (GrossWeight > 0)
);

-- FACILITIES TABLE
CREATE TABLE Facilities (
    FacilityID INT PRIMARY KEY AUTO_INCREMENT,
    FacilityName VARCHAR(150) NOT NULL,
    Address VARCHAR(255),
    Latitude DECIMAL(9,6),
    Longitude DECIMAL(9,6),
    CONSTRAINT chk_latitude CHECK (Latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_longitude CHECK (Longitude BETWEEN -180 AND 180)
);

-- SHIPMENTS TABLE
CREATE TABLE Shipments (
    ShipmentID INT PRIMARY KEY AUTO_INCREMENT,
    VehicleID INT NOT NULL,
    SourceFacilityID INT NOT NULL,
    ReceiverFacilityID INT NOT NULL,
    ShipmentDate DATE NOT NULL,
    
    FOREIGN KEY (VehicleID)
        REFERENCES Vehicles(VehicleID)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (SourceFacilityID)
        REFERENCES Facilities(FacilityID)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (ReceiverFacilityID)
        REFERENCES Facilities(FacilityID)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- OPTIONAL: Trigger to prevent self-shipment
DELIMITER //
CREATE TRIGGER trg_check_facilities
BEFORE INSERT ON Shipments
FOR EACH ROW
BEGIN
    IF NEW.SourceFacilityID = NEW.ReceiverFacilityID THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Source and receiver facilities cannot be the same.';
    END IF;
END//
DELIMITER ;

