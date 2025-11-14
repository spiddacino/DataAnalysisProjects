-- Create schema
CREATE DATABASE IF NOT EXISTS fleetmanagement;
USE fleetmanagement;

-- =====================================================
-- 1. Vehicles
-- =====================================================
DROP TABLE IF EXISTS Vehicles;
CREATE TABLE Vehicles (
    VehicleID INT PRIMARY KEY,
    Manufacturer VARCHAR(100) NOT NULL,
    ModelYear INT NOT NULL,
    GrossWeight DECIMAL(10,2) NOT NULL
);

-- =====================================================
-- 2. Facilities
-- =====================================================
DROP TABLE IF EXISTS Facilities;
CREATE TABLE Facilities (
    FacilityID INT PRIMARY KEY,
    FacilityName VARCHAR(255) NOT NULL,
    Address VARCHAR(500),
    City VARCHAR(150),
    Region VARCHAR(150),
    Country VARCHAR(150),
    Latitude DECIMAL(10,6),
    Longitude DECIMAL(10,6)
);

-- =====================================================
-- 3. Shipments
-- =====================================================
DROP TABLE IF EXISTS Shipments;
CREATE TABLE Shipments (
    ShipmentID BIGINT PRIMARY KEY,

    VehicleID INT NOT NULL,
    SourceFacilityID INT NOT NULL,
    ReceiverFacilityID INT NOT NULL,

    ShipmentDateTime DATETIME NOT NULL,
    PickupTime DATETIME NOT NULL,
    DeliveryTime DATETIME NULL,

    Status VARCHAR(50) NOT NULL,
    Cost DECIMAL(12,2) NOT NULL,
    TransitTimeDays DECIMAL(10,2) NOT NULL,
    DistanceKm DECIMAL(12,3) NOT NULL,

    RouteType VARCHAR(50),
    RouteKey VARCHAR(100),

    CONSTRAINT fk_ship_vehicle
        FOREIGN KEY (VehicleID) REFERENCES Vehicles(VehicleID)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_ship_source
        FOREIGN KEY (SourceFacilityID) REFERENCES Facilities(FacilityID)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_ship_receiver
        FOREIGN KEY (ReceiverFacilityID) REFERENCES Facilities(FacilityID)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- =====================================================
-- Enforce Business Rule with Triggers
-- SourceFacilityID <> ReceiverFacilityID
-- =====================================================

DROP TRIGGER IF EXISTS trg_shipments_before_insert;
DELIMITER $$
CREATE TRIGGER trg_shipments_before_insert
BEFORE INSERT ON Shipments
FOR EACH ROW
BEGIN
    IF NEW.SourceFacilityID = NEW.ReceiverFacilityID THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'SourceFacilityID and ReceiverFacilityID must be different.';
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_shipments_before_update;
DELIMITER $$
CREATE TRIGGER trg_shipments_before_update
BEFORE UPDATE ON Shipments
FOR EACH ROW
BEGIN
    IF NEW.SourceFacilityID = NEW.ReceiverFacilityID THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'SourceFacilityID and ReceiverFacilityID must be different.';
    END IF;
END$$
DELIMITER ;


-- Optional indexing for analytics
CREATE INDEX idx_ship_vehicle ON Shipments(VehicleID);
CREATE INDEX idx_ship_status ON Shipments(Status);
CREATE INDEX idx_ship_routekey ON Shipments(RouteKey);
CREATE INDEX idx_ship_sourcedest ON Shipments(SourceFacilityID, ReceiverFacilityID);
CREATE INDEX idx_ship_datetime ON Shipments(ShipmentDateTime);