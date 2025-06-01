CREATE TABLE records (
    moment TEXT  PRIMARY KEY -- YYYY/MM/DD HH:MM:SS
    ,activity TEXT REFERENCES activity (activity)
    ,comment TEXT
);

CREATE TABLE activity (
    activity TEXT PRIMARY KEY
);


CREATE TRIGGER add_activity BEFORE INSERT ON records
    WHEN NOT EXISTS (SELECT TRUE from activity where activity.activity = new.activity)
    BEGIN INSERT INTO activity VALUES(new.activity); END;
