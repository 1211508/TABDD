CREATE TABLE orders (
    orderCode      INTEGER PRIMARY KEY,
    orderDate      DATE,
    totalAmount    NUMBER(10, 2),
    status         VARCHAR2(10),
    SystemUserCode   INTEGER,
    deliveryAddress VARCHAR2(100)
);
drop table orders

INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1001, TO_DATE('2024-01-01', 'YYYY-MM-DD'), 250, 'completed', 501, '123 Main St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1002, TO_DATE('2024-01-03', 'YYYY-MM-DD'), 300, 'completed', 502, '456 Elm St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1003, TO_DATE('2024-01-05', 'YYYY-MM-DD'), 150, 'pending', 503, '789 Oak St, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1004, TO_DATE('2024-01-07', 'YYYY-MM-DD'), 400, 'completed', 504, '321 Maple St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1005, TO_DATE('2024-01-09', 'YYYY-MM-DD'), 500, 'canceled', 505, '654 Pine St, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1006, TO_DATE('2024-01-11', 'YYYY-MM-DD'), 600, 'completed', 506, '987 Cedar St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1007, TO_DATE('2024-01-13', 'YYYY-MM-DD'), 700, 'pending', 507, '432 Birch St, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1008, TO_DATE('2024-01-15', 'YYYY-MM-DD'), 800, 'completed', 508, '876 Willow St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1009, TO_DATE('2024-01-17', 'YYYY-MM-DD'), 900, 'canceled', 509, '210 Chestnut St, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1010, TO_DATE('2024-01-19', 'YYYY-MM-DD'), 1000, 'completed', 510, '135 Redwood St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1011, TO_DATE('2024-01-21', 'YYYY-MM-DD'), 1100, 'pending', 511, '246 Cypress St, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1012, TO_DATE('2024-01-23', 'YYYY-MM-DD'), 1200, 'completed', 512, '357 Sycamore St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1013, TO_DATE('2024-01-25', 'YYYY-MM-DD'), 1300, 'canceled', 513, '468 Walnut St, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1014, TO_DATE('2024-01-27', 'YYYY-MM-DD'), 1400, 'completed', 514, '579 Fir St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1015, TO_DATE('2024-01-29', 'YYYY-MM-DD'), 1500, 'pending', 515, '680 Beech St, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1016, TO_DATE('2024-01-31', 'YYYY-MM-DD'), 1600, 'completed', 516, '791 Spruce St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1017, TO_DATE('2024-02-02', 'YYYY-MM-DD'), 1700, 'canceled', 517, '902 Hickory St, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1018, TO_DATE('2024-02-04', 'YYYY-MM-DD'), 1800, 'completed', 518, '123 Palm St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1019, TO_DATE('2024-02-06', 'YYYY-MM-DD'), 1900, 'pending', 519, '234 Magnolia St, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1020, TO_DATE('2024-02-08', 'YYYY-MM-DD'), 2000, 'completed', 520, '345 Poplar St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1021, TO_DATE('2024-02-10', 'YYYY-MM-DD'), 2100, 'completed', 521, '456 Evergreen Terrace, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1022, TO_DATE('2024-02-12', 'YYYY-MM-DD'), 2200, 'pending', 522, '789 Baker St, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1023, TO_DATE('2024-02-14', 'YYYY-MM-DD'), 2300, 'canceled', 523, '321 Elm St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1024, TO_DATE('2024-02-16', 'YYYY-MM-DD'), 2400, 'completed', 524, '654 Maple Ave, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1025, TO_DATE('2024-02-18', 'YYYY-MM-DD'), 2500, 'pending', 525, '987 Cedar Ln, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1026, TO_DATE('2024-02-20', 'YYYY-MM-DD'), 2600, 'completed', 526, '123 Oak St, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1027, TO_DATE('2024-02-22', 'YYYY-MM-DD'), 2700, 'canceled', 527, '456 Pine St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1028, TO_DATE('2024-02-24', 'YYYY-MM-DD'), 2800, 'completed', 528, '789 Redwood Dr, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1029, TO_DATE('2024-02-26', 'YYYY-MM-DD'), 2900, 'pending', 529, '321 Birch Ave, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1030, TO_DATE('2024-02-28', 'YYYY-MM-DD'), 3000, 'completed', 530, '654 Walnut St, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1031, TO_DATE('2024-03-01', 'YYYY-MM-DD'), 3100, 'canceled', 531, '987 Magnolia Rd, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1032, TO_DATE('2024-03-03', 'YYYY-MM-DD'), 3200, 'completed', 532, '123 Sycamore Ln, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1033, TO_DATE('2024-03-05', 'YYYY-MM-DD'), 3300, 'pending', 533, '456 Cypress Dr, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1034, TO_DATE('2024-03-07', 'YYYY-MM-DD'), 3400, 'completed', 534, '789 Spruce St, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1035, TO_DATE('2024-03-09', 'YYYY-MM-DD'), 3500, 'canceled', 535, '321 Palm Ave, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1036, TO_DATE('2024-03-11', 'YYYY-MM-DD'), 3600, 'completed', 536, '654 Chestnut Rd, Shelbyville');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1037, TO_DATE('2024-03-13', 'YYYY-MM-DD'), 3700, 'pending', 537, '987 Hickory St, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1038, TO_DATE('2024-03-15', 'YYYY-MM-DD'), 3800, 'completed', 538, '123 Fir Ln, Capital City');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1039, TO_DATE('2024-03-17', 'YYYY-MM-DD'), 3900, 'canceled', 539, '456 Willow Dr, Springfield');
INSERT INTO orders (orderCode, orderDate, totalAmount, status, SystemUserCode, deliveryAddress) VALUES (1040, TO_DATE('2024-03-19', 'YYYY-MM-DD'), 4000, 'completed', 540, '789 Redwood Ave, Shelbyville');
